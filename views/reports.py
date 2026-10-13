import streamlit as st

from horenso import data, ui

st.title("レポート履歴")
reports = data.reports()
if reports is None:
    st.stop()
if reports.empty:
    st.info("レポートはまだありません。")
    st.stop()

months = sorted(reports["date"].str[:7].unique(), reverse=True)
c1, c2 = st.columns(2)
month = c1.selectbox("月", ["すべて"] + months, index=1, format_func=lambda m: m if m == "すべて" else f"{int(m[:4])}年{int(m[5:])}月")
space = c2.selectbox("スペース", ["すべて"] + sorted(reports["space"].unique()))

view = reports
if month != "すべて":
    view = view[view["date"].str[:7] == month]
if space != "すべて":
    view = view[view["space"] == space]

sent = int(view["status"].str.contains("送信済み").sum())
fail = int(view["status"].str.contains("失敗").sum())
st.caption(f"{len(view)}件（送信済み {sent}件" + (f"・送信失敗 {fail}件" if fail else "") + "）。新しい順。")

for i, (_, r) in enumerate(view.iterrows()):
    with st.expander(ui.report_title(r), expanded=(i == 0)):
        ui.send_badge(r["status"])
        ui.report_body(r["sections"])
