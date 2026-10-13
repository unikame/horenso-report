import streamlit as st

from horenso import data, ledger, survey as sv, ui

ui.page_header("ホーム", "日次レポート・リスク・TODO・報連相チェックの状況をまとめて確認します。", eyebrow="OVERVIEW")

reports, todos, risks, svdata = data.reports(), data.todos(), data.risks(), data.survey_all()

# ---- 数字のカード ----
c1, c2, c3, c4 = st.columns(4)
with c1:
    if risks is not None:
        open_r = risks[risks["open"]]
        high = int((open_r["level"] == "高").sum())
        ui.kpi("対応が必要なリスク", f"{len(open_r)}件", f"高レベル {high}件" if high else "高レベルなし", "red" if high else "green")
with c2:
    if todos is not None:
        open_t = todos[todos["open"]]
        over = int(open_t["overdue"].sum())
        ui.kpi("未完了のTODO", f"{len(open_t)}件", f"期限切れ {over}件" if over else "期限切れなし", "red" if over else "green")
with c3:
    if reports is not None:
        sent = reports[~reports["status"].str.contains("やりとりなし")]
        fails = int(reports["status"].str.contains("失敗").sum())
        if len(sent):
            d = sent.iloc[0]["date"]
            ui.kpi("最新のレポート", f"{int(d[5:7])}/{int(d[8:10])}分", f"送信失敗 {fails}件" if fails else "すべて送信済み",
                   "red" if fails else "green", help=ledger.period_label(d, sent.iloc[0]["dow"]))
        else:
            ui.kpi("最新のレポート", "–", "記録なし")
with c4:
    if svdata is not None:
        df, _, target, goal = svdata
        if len(df):
            w = sv.periods(df, "week")[0]
            n = sv.rows_in(df, "week", w)["key"].nunique()
            rate = sv.rate_of(df, "week", w, target)
            ok = rate is not None and goal is not None and rate >= goal
            note = (f"目標{goal:.0%}達成" if ok else f"目標{goal:.0%}に未達") if (rate is not None and goal is not None) else f"{n}人回答"
            ui.kpi(f"チェック回答率（{sv.label(w, 'week')}）", f"{rate:.0%}" if rate is not None else f"{n}人", note, "green" if ok else "orange")

# ---- 最新のレポート ＋ 報連相チェック ----
left, right = st.columns([2, 1], gap="medium")
with left:
    with st.container(border=True):
        ui.section_title("最新のレポート", "views/reports.py", "履歴を見る", "スペースごとに、いちばん新しい日次レポート")
        if reports is not None:
            latest = reports.drop_duplicates("space")
            if latest.empty:
                st.caption("レポートはまだありません。")
            for i, (_, r) in enumerate(latest.iterrows()):
                with st.expander(ui.report_title(r), expanded=(i == 0)):
                    ui.report_body(r["sections"])
with right:
    with st.container(border=True):
        ui.section_title("報連相チェック", "views/survey.py", "詳しく見る")
        if svdata is not None and len(svdata[0]):
            df = svdata[0]
            w = sv.periods(df, "week")[0]
            s = sv.stats(sv.rows_in(df, "week", w))
            st.caption(f"{sv.label(w, 'week')}の平均（5点満点）")
            for k, name, _ in sv.ITEMS:
                st.progress(min(1.0, (s[k] or 0) / 5), text=f"{name}　**{ui.fmt(s[k])}**")
            weak = sv.weakest(s)
            if weak:
                st.caption(f"いちばん弱い項目は **{weak[0]}** です。")
            fl = sv.follow_list(df, "week", w, sv.periods(df, "week"))
            if len(fl):
                st.badge(f"声をかけたい人 {len(fl)}人", icon=":material/person_alert:", color="orange")
        elif svdata is not None:
            st.caption("回答はまだありません。")

# ---- リスク・TODO ----
left, right = st.columns(2, gap="medium")
with left:
    with st.container(border=True):
        ui.section_title("対応が必要なリスク", "views/risks.py", note="レベルの高い順・経過日数の長い順")
        if risks is not None:
            top = risks[risks["open"]].head(6)
            rows = [(ui.tag(("▲ " if r["level"] == "高" else "") + ui.esc(r["level"] or "–"), ui.STATE_COLORS.get(r["level"], ui.GRAY)),
                     ui.esc(r["what"]), f"{ui.esc(r['cat'])}・{ui.esc(r['space'])}・{ui.esc(r['date'])}",
                     ui.tag(ui.esc(r["state"]), ui.STATE_COLORS.get(r["state"], ui.GRAY)) + (f"<br>{int(r['days'])}日経過" if r["days"] == r["days"] else ""))
                    for _, r in top.iterrows()]
            st.html(ui.rows_html(rows, "対応が必要なリスクはありません。"))
with right:
    with st.container(border=True):
        ui.section_title("止まっているTODO", "views/todos.py", note="期限切れが先・経過日数の長い順")
        if todos is not None:
            top = todos[todos["open"]].head(6)
            rows = [(ui.tag(ui.esc(t["who"]), ui.BLUE), ui.esc(t["what"]),
                     ("期限 " + (f'<span style="color:{ui.RED};font-weight:600">{ui.esc(t["due"])}（期限切れ）</span>' if t["overdue"] else ui.esc(t["due"]))) + f"・{ui.esc(t['space'])}",
                     ui.tag(ui.esc(t["state"]), ui.STATE_COLORS.get(t["state"], ui.GRAY)) + (f"<br>{int(t['days'])}日経過" if t["days"] == t["days"] else ""))
                    for _, t in top.iterrows()]
            st.html(ui.rows_html(rows, "未完了のTODOはありません。"))
