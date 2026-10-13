"""動作確認（架空のデータで、画面が表示されるか・データが安全に埋め込まれるかを見る）

実行： python tests/test_app.py   （「すべてOK」と出れば成功）
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

L = {5: "5：10割できた", 4: "4：9割できた", 3: "3：8〜9割できた", 2: "2：5〜8割できた", 1: "1：5割未満"}
SURVEY = [["タイムスタンプ", "1. 氏名", "2. 部署", "3. 【報告】今週…", "4. 【連絡】今週…", "5. 【相談】今週…", "6. うまくいったこと", "7. 委員会への要望 (参考)"],
          ["2026/09/25 16:10:00", "社員 A", "営業部", L[3], L[4], L[5]],
          ["2026/10/02 16:00:00", "社員A", "営業部", L[4], L[4], L[5], "</script><b>テスト</b>"],
          ["2026/10/02 16:30:00", "社員B", "管理部", L[1], L[2], L[2], "", "要望"]]
SETTINGS = [["分析"], ["トライアル対象人数", "4", "人"], ["回答率の目標", "70%"]]


def test_app_renders():
    from streamlit.testing.v1 import AppTest
    import streamlit.components.v1 as components
    import horenso.sheets as sheets
    sheets.load = lambda kind: {"survey": SURVEY, "settings": SETTINGS}[kind]
    pages = []
    original = components.html
    components.html = lambda html, **kw: pages.append(html)
    try:
        at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=60).run()
    finally:
        components.html = original
    assert not at.exception, [e.message for e in at.exception]
    assert not at.error, [e.value for e in at.error]
    assert pages, "集計画面が表示されていません"
    page = pages[0]
    assert "__VALUES__" not in page and "__SETTINGS__" not in page
    assert "社員B" in page and "トライアル対象人数" in page
    assert "</script><b>" not in page                  # 回答の文字で画面のプログラムが壊れない


def test_sheet_error_shows_message():
    from streamlit.testing.v1 import AppTest
    import horenso.sheets as sheets

    def fail(kind):
        raise sheets.SheetError("「アンケート回答管理表」を読む権限がありません。")
    sheets.load = fail
    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=60).run()
    assert not at.exception
    assert any("権限がありません" in e.value for e in at.error)


if __name__ == "__main__":
    test_app_renders()
    test_sheet_error_shows_message()
    print("すべてOK")
