"""動作確認（架空のデータで、集計ロジックと各画面がエラーなく表示されるかを見る）

実行： python -m pytest tests/  または  python tests/test_app.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from horenso import ledger, survey as sv  # noqa: E402

L = {5: "5：10割できた", 4: "4：9割できた", 3: "3：8〜9割できた", 2: "2：5〜8割できた", 1: "1：5割未満"}
HEAD = ["タイムスタンプ", "1. 氏名", "2. 部署", "3. 【報告】今週…", "4. 【連絡】今週…", "5. 【相談】今週…",
        "6. 報連相でうまくいったことや、うまくできなかった場面があれば教えてください", "7. 委員会にしてほしいこと (参考にします)"]


def row(ts, name, dept, r, c, s, f6="", f7=""):
    return [ts, name, dept, L[r], L[c], L[s], f6, f7]


SURVEY = [HEAD,
          row("2026/09/25 16:10:00", "社員 A", "営業部", 3, 4, 5),
          row("2026/09/25 16:20:00", "社員B", "管理部", 5, 5, 5),
          row("2026/09/28 09:00:00", "社員C", "", 2, 2, 3, "相談が遅れた"),          # 月曜の回答 → 9/25週
          row("2026/10/02 16:00:00", "社員A", "営業部", 4, 4, 5),                   # 「社員 A」と同一人物
          row("2026/10/02 16:30:00", "社員B", "管理部", 1, 2, 2, "", "要望あり"),
          row("2026/10/02 17:00:00", "社員B", "管理部", 4, 4, 4),                   # 同じ週の再回答 → こちらを採用
          row("2026/10/09 16:00:00", "社員A", "営業部", 5, 5, 5, "うまくいった")]
SETTINGS = [["分析"], [], ["トライアル対象人数", "4", "人"], ["回答率の目標", "70%"]]
REPORTS = [["日付", "曜日", "スペース", "メッセージ数", "①報告", "②連絡", "③相談", "④決定事項", "⑤TODO", "⑥未解決事項", "⑦リスク", "送信内容", "送信状態", "記録日時", "レポートID", "データ形式", "AI出力（JSON）", "送信先"],
           ["2026-10-09", "金〜月（10/9（金）〜10/12（月））", "委員会", "8", "・報告1\n・報告2", "—", "・相談1", "—", "・Aさん：作業（2026-10-13）", "—", "—", "", "送信済み", "", "R1", "v1", "", "WEBHOOK_URL"],
           ["2026-10-06", "火", "委員会", "0", "—", "—", "—", "—", "—", "—", "—", "", "やりとりなし", "", "R2", "v1", ""],
           ["2026-10-07", "水", "営業", "3", "・報告", "—", "—", "・決定", "—", "—", "・【中・その他】リスク", "", "送信失敗：x", "", "R3", "v1", "", "WEBHOOK_SALES"]]
TODOS = [["TODO_ID", "発生日", "スペース", "担当", "内容", "期限", "状態", "対応メモ", "最終更新日", "更新者", "経過日数（未完了）", "レポートID"],
         ["T1", "2026-10-02", "委員会", "A", "返信する", "月曜日12時", "未対応", "", "", "", "11", ""],
         ["T2", "2026-10-07", "委員会", "B", "依頼する", "2026-10-07 19:00", "未対応", "", "", "", "6", ""],
         ["T3", "2026-10-08", "委員会", "C", "配信する", "2026-10-09", "完了", "済", "", "", "", ""]]
RISKS = [["リスクID", "発生日", "スペース", "レベル", "分類", "内容", "状態", "対応者", "対応メモ", "最終更新日", "経過日数（未対応）", "レポートID"],
         ["K1", "2026-10-07", "委員会", "中", "その他", "中リスク", "未対応", "", "", "", "6", ""],
         ["K2", "2026-10-08", "委員会", "高", "納期遅延", "高リスク", "確認中", "A", "", "", "5", ""],
         ["K3", "2026-10-01", "委員会", "低", "その他", "済リスク", "対応済み", "", "", "", "", ""]]
FIXTURES = {"reports": REPORTS, "todos": TODOS, "risks": RISKS, "survey": SURVEY, "settings": SETTINGS}


def test_survey_logic():
    df, free = sv.parse(SURVEY)
    assert len(free) == 2 and free[0][1].startswith("報連相でうまくいった")
    assert sorted(df["week"].unique()) == ["2026-09-25", "2026-10-02", "2026-10-09"]
    assert df[df["name"] == "社員C"]["week"].iloc[0] == "2026-09-25"
    b = df[(df["key"] == "社員B") & (df["week"] == "2026-10-02")]
    assert len(b) == 1 and b["total"].iloc[0] == 12                     # 同じ週の再回答は新しい方
    assert df[df["week"] == "2026-10-02"]["key"].nunique() == 2         # 「社員 A」と「社員A」は同じ人
    assert df[df["key"] == "社員C"]["dept"].iloc[0] == "未記入"
    target, goal = sv.parse_settings(SETTINGS)
    assert target == 4 and abs(goal - 0.7) < 1e-9
    assert sv.periods(df, "month") == ["2026-10", "2026-09"]
    assert abs(sv.rate_of(df, "week", "2026-10-02", target) - 0.5) < 1e-9
    assert abs(sv.rate_of(df, "month", "2026-10", target) - (0.5 + 0.25) / 2) < 1e-9   # 各週の回答率の平均
    ps = sv.periods(df, "week")
    fl = sv.follow_list(df, "week", "2026-09-25", ps)
    assert fl["name"].tolist() == ["社員C"]
    st = sv.stats(sv.rows_in(df, "week", "2026-10-09"))
    assert sv.weakest(st) is None                                     # 全項目満点


def test_ledger_logic():
    r = ledger.parse_reports(REPORTS)
    assert r["date"].tolist() == ["2026-10-09", "2026-10-07", "2026-10-06"]
    assert r.iloc[0]["sections"]["報告"] == ["報告1", "報告2"] and r.iloc[0]["sections"]["連絡"] == []
    assert ledger.period_label("2026-10-09", "金〜月（10/9（金）〜10/12（月））") == "10/9（金）〜10/12（月）"
    assert ledger.period_label("2026-10-06", "火") == "10/6（火）"
    t = ledger.parse_todos(TODOS, today="2026-10-13")
    assert t.iloc[0]["id"] == "T2" and bool(t.iloc[0]["overdue"])      # 期限切れが先頭
    assert not t[t["id"] == "T1"]["overdue"].iloc[0]                   # 日付でない期限は判定しない
    assert int(t["open"].sum()) == 2
    k = ledger.parse_risks(RISKS)
    assert k["id"].tolist()[0] == "K2" and int(k["open"].sum()) == 2


def test_pages_render():
    from streamlit.testing.v1 import AppTest
    import horenso.sheets as sheets
    sheets.load = lambda kind: FIXTURES[kind]
    sheets.service_account_email = lambda: ""
    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=60).run()      # ホーム
    pages = ["views/home.py", "views/reports.py", "views/risks.py", "views/todos.py", "views/survey.py"]
    for page in pages:
        if page != pages[0]:
            at.switch_page(page).run()
        assert not at.exception, (page, [e.message for e in at.exception])
        assert not at.error, (page, [e.value for e in at.error])
    at.segmented_control(key="unit").set_value("月ごと").run()           # 月ごとに切り替え
    assert not at.exception, [e.message for e in at.exception]
    assert any("2026年10月" in str(o) for o in at.selectbox(key="period_month").options)


if __name__ == "__main__":
    test_survey_logic(); test_ledger_logic(); test_pages_render()
    print("すべてOK")
