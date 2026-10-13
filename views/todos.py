import streamlit as st

from horenso import config, data

st.title("TODO一覧")
todos = data.todos()
if todos is None:
    st.stop()

c1, c2, c3 = st.columns(3)
state = c1.selectbox("状態", ["未完了", "すべて"])
who = c2.selectbox("担当", ["すべて"] + sorted(todos["who"].unique()))
space = c3.selectbox("スペース", ["すべて"] + sorted(todos["space"].unique()))

view = todos
if state != "すべて":
    view = view[view["open"]]
if who != "すべて":
    view = view[view["who"] == who]
if space != "すべて":
    view = view[view["space"] == space]

st.caption(f"{len(view)}件。期限切れが先、次に経過日数の長い順。期限が日付で書かれていないものは、期限切れの判定から外しています。")
st.dataframe(
    view[["overdue", "who", "what", "due", "state", "memo", "days", "date", "space"]],
    hide_index=True, width="stretch",
    column_config={
        "overdue": st.column_config.CheckboxColumn("期限切れ", width="small"),
        "who": st.column_config.TextColumn("担当", width="small"),
        "what": st.column_config.TextColumn("内容", width="large"),
        "due": st.column_config.TextColumn("期限", width="small"),
        "state": st.column_config.TextColumn("状態", width="small"),
        "memo": st.column_config.TextColumn("対応メモ"),
        "days": st.column_config.NumberColumn("経過", format="%d日", width="small"),
        "date": st.column_config.TextColumn("発生日", width="small"),
        "space": st.column_config.TextColumn("スペース"),
    },
)
st.caption(f"状態・対応メモは [管理台帳の「TODO」タブ](https://docs.google.com/spreadsheets/d/{config.get('LEDGER_ID')}/edit#gid=20) で更新してください。")
