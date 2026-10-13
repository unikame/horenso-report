import streamlit as st

from horenso import data, ledger, survey as sv, ui

st.title("ホーム")

reports, todos, risks, svdata = data.reports(), data.todos(), data.risks(), data.survey_all()

c1, c2, c3, c4 = st.columns(4)
with c1:
    if risks is not None:
        open_r = risks[risks["open"]]
        high = int((open_r["level"] == "高").sum())
        st.metric("対応が必要なリスク", f"{len(open_r)}件", border=True)
        if high:
            st.badge(f"高 {high}件", icon=":material/warning:", color="red")
        else:
            st.badge("高レベルなし", icon=":material/check:", color="green")
with c2:
    if todos is not None:
        open_t = todos[todos["open"]]
        over = int(open_t["overdue"].sum())
        st.metric("未完了のTODO", f"{len(open_t)}件", border=True)
        if over:
            st.badge(f"期限切れ {over}件", icon=":material/schedule:", color="red")
        else:
            st.badge("期限切れなし", icon=":material/check:", color="green")
with c3:
    if reports is not None:
        sent = reports[~reports["status"].str.contains("やりとりなし")]
        fails = int(reports["status"].str.contains("失敗").sum())
        if len(sent):
            last = sent.iloc[0]
            d = last["date"]
            st.metric("最新のレポート", f"{int(d[5:7])}/{int(d[8:10])}分", border=True, help=ledger.period_label(d, last["dow"]))
            ui.send_badge(last["status"])
            if fails:
                st.badge(f"送信失敗 {fails}件", color="red")
        else:
            st.metric("最新のレポート", "–", border=True)
with c4:
    if svdata is not None:
        df, _, target, goal = svdata
        if len(df):
            w = sv.periods(df, "week")[0]
            n = sv.rows_in(df, "week", w)["key"].nunique()
            rate = sv.rate_of(df, "week", w, target)
            st.metric("アンケート回答率（最新週）", f"{rate:.0%}" if rate is not None else f"{n}人", border=True)
            st.caption(f"{sv.label(w, 'week')}・{n}人回答")
            if rate is not None and goal is not None:
                st.badge(f"目標{goal:.0%}達成" if rate >= goal else f"目標{goal:.0%}に未達", color="green" if rate >= goal else "orange")

st.subheader("最新のレポート")
if reports is not None:
    latest = reports.drop_duplicates("space")
    if latest.empty:
        st.caption("レポートはまだありません。")
    for i, (_, r) in enumerate(latest.iterrows()):
        with st.expander(ui.report_title(r), expanded=(i == 0)):
            ui.report_body(r["sections"])
    st.page_link("views/reports.py", label="レポート履歴を見る", icon=":material/history:")

left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.subheader("対応が必要なリスク")
        if risks is not None:
            top = risks[risks["open"]].head(5)
            if top.empty:
                st.caption("対応が必要なリスクはありません。")
            for _, r in top.iterrows():
                a, b = st.columns([1, 5])
                with a:
                    ui.level_badge(r["level"])
                with b:
                    st.markdown(r["what"])
                    st.caption(f"{r['cat']}・{r['space']}・{r['date']}・{r['state']}" + (f"・{int(r['days'])}日経過" if r["days"] == r["days"] else ""))
            st.page_link("views/risks.py", label="すべて見る", icon=":material/arrow_forward:")
with right:
    with st.container(border=True):
        st.subheader("止まっているTODO")
        if todos is not None:
            top = todos[todos["open"]].head(5)
            if top.empty:
                st.caption("未完了のTODOはありません。")
            for _, t in top.iterrows():
                a, b = st.columns([1, 5])
                with a:
                    st.badge(t["who"], color="gray")
                with b:
                    st.markdown(t["what"])
                    due = f":red[{t['due']}（期限切れ）]" if t["overdue"] else t["due"]
                    st.caption(f"期限 {due}・{t['state']}" + (f"・{int(t['days'])}日経過" if t["days"] == t["days"] else "") + f"・{t['space']}")
            st.page_link("views/todos.py", label="すべて見る", icon=":material/arrow_forward:")
