import streamlit as st

from horenso import config, data, ui

ui.page_header("リスク", "日次レポートから記録されたリスクと、その対応状況です。", eyebrow="RISKS")
risks = data.risks()
if risks is None:
    st.stop()

open_r = risks[risks["open"]]
k1, k2, k3, k4 = st.columns(4)
with k1:
    ui.kpi("対応が必要", f"{len(open_r)}件", "未対応・確認中")
with k2:
    high = int((open_r["level"] == "高").sum())
    ui.kpi("うち高レベル", f"{high}件", "すぐに確認" if high else "なし", "red" if high else "green")
with k3:
    untouched = int((open_r["state"] == "未対応").sum())
    ui.kpi("未対応のまま", f"{untouched}件", "対応者を決める" if untouched else "なし", "orange" if untouched else "green")
with k4:
    longest = open_r["days"].max()
    ui.kpi("最も長い経過", f"{int(longest)}日" if longest == longest else "–", "未対応の日数")

with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    state = c1.segmented_control("状態", ["対応が必要", "すべて"], default="対応が必要", required=True)
    level = c2.segmented_control("レベル", ["すべて", "高", "中", "低"], default="すべて", required=True)
    space = c3.selectbox("スペース", ["すべて"] + sorted(risks["space"].unique()))

view = risks
if state != "すべて":
    view = view[view["open"]]
if level != "すべて":
    view = view[view["level"] == level]
if space != "すべて":
    view = view[view["space"] == space]

show = view.assign(level=view["level"].map(lambda l: "▲ 高" if l == "高" else l))[["level", "cat", "what", "state", "owner", "memo", "days", "date", "space"]]
st.dataframe(
    ui.styled(show, ["level", "state"]), hide_index=True, width="stretch",
    column_config={
        "level": st.column_config.TextColumn("レベル", width="small", pinned=True),
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
st.caption(f"{len(view)}件。状態・対応者・対応メモは [管理台帳の「リスク」タブ](https://docs.google.com/spreadsheets/d/{config.get('LEDGER_ID')}/edit#gid=30) で更新してください。")
