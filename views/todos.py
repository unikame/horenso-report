import streamlit as st

from horenso import config, data, ui

ui.page_header("TODO", "日次レポートから記録された依頼・作業と、その進み具合です。", eyebrow="TODO")
todos = data.todos()
if todos is None:
    st.stop()

open_t = todos[todos["open"]]
k1, k2, k3, k4 = st.columns(4)
with k1:
    ui.kpi("未完了", f"{len(open_t)}件", "未対応・対応中・要確認")
with k2:
    over = int(open_t["overdue"].sum())
    ui.kpi("期限切れ", f"{over}件", "担当者に確認" if over else "なし", "red" if over else "green")
with k3:
    nobody = int((open_t["who"] == "担当未定").sum())
    ui.kpi("担当未定", f"{nobody}件", "担当を決める" if nobody else "なし", "orange" if nobody else "green")
with k4:
    stale = int((open_t["days"] >= 7).sum())
    ui.kpi("7日以上経過", f"{stale}件", "止まっている可能性" if stale else "なし", "orange" if stale else "green")

with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    state = c1.segmented_control("状態", ["未完了", "すべて"], default="未完了", required=True)
    who = c2.selectbox("担当", ["すべて"] + sorted(todos["who"].unique()))
    space = c3.selectbox("スペース", ["すべて"] + sorted(todos["space"].unique()))

view = todos
if state != "すべて":
    view = view[view["open"]]
if who != "すべて":
    view = view[view["who"] == who]
if space != "すべて":
    view = view[view["space"] == space]

show = view.assign(flag=view["overdue"].map(lambda x: "期限切れ" if x else ""))[["flag", "who", "what", "due", "state", "memo", "days", "date", "space"]]
st.dataframe(
    ui.styled(show, ["flag", "state"]), hide_index=True, width="stretch",
    column_config={
        "flag": st.column_config.TextColumn("", width="small", pinned=True),
        "who": st.column_config.TextColumn("担当", width="small", pinned=True),
        "what": st.column_config.TextColumn("内容", width="large"),
        "due": st.column_config.TextColumn("期限", width="small"),
        "state": st.column_config.TextColumn("状態", width="small"),
        "memo": st.column_config.TextColumn("対応メモ"),
        "days": st.column_config.NumberColumn("経過", format="%d日", width="small"),
        "date": st.column_config.TextColumn("発生日", width="small"),
        "space": st.column_config.TextColumn("スペース"),
    },
)
st.caption(f"{len(view)}件。期限が日付で書かれていないものは、期限切れの判定から外しています。状態・対応メモは [管理台帳の「TODO」タブ](https://docs.google.com/spreadsheets/d/{config.get('LEDGER_ID')}/edit#gid=20) で更新してください。")
