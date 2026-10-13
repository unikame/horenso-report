import streamlit as st

from horenso import config, data

st.title("リスク一覧")
risks = data.risks()
if risks is None:
    st.stop()

c1, c2, c3 = st.columns(3)
state = c1.selectbox("状態", ["対応が必要なもの", "すべて"])
level = c2.selectbox("レベル", ["すべて", "高", "中", "低"])
space = c3.selectbox("スペース", ["すべて"] + sorted(risks["space"].unique()))

view = risks
if state != "すべて":
    view = view[view["open"]]
if level != "すべて":
    view = view[view["level"] == level]
if space != "すべて":
    view = view[view["space"] == space]

st.caption(f"{len(view)}件。レベルの高い順、同じレベルは経過日数の長い順。")
show = view.assign(level=view["level"].map(lambda l: "▲ 高" if l == "高" else l))
st.dataframe(
    show[["level", "cat", "what", "state", "owner", "memo", "days", "date", "space"]],
    hide_index=True, width="stretch",
    column_config={
        "level": st.column_config.TextColumn("レベル", width="small"),
        "cat": st.column_config.TextColumn("分類", width="small"),
        "what": st.column_config.TextColumn("内容", width="large"),
        "state": st.column_config.TextColumn("状態", width="small"),
        "owner": st.column_config.TextColumn("対応者", width="small"),
        "memo": st.column_config.TextColumn("対応メモ"),
        "days": st.column_config.NumberColumn("経過", format="%d日", width="small"),
        "date": st.column_config.TextColumn("発生日", width="small"),
        "space": st.column_config.TextColumn("スペース"),
    },
)
st.caption(f"状態・対応者・対応メモは [管理台帳の「リスク」タブ](https://docs.google.com/spreadsheets/d/{config.get('LEDGER_ID')}/edit#gid=30) で更新してください。")
