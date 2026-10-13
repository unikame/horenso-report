import streamlit as st

from horenso import data, ui

ui.page_header("レポート履歴", "毎朝送られた日次レポートを、月・スペースごとに見返します。", eyebrow="REPORTS")
reports = data.reports()
if reports is None:
    st.stop()
if reports.empty:
    st.info("レポートはまだありません。")
    st.stop()

months = sorted(reports["date"].str[:7].unique(), reverse=True)
with st.container(border=True):
    c1, c2, c3 = st.columns([1, 1, 2], vertical_alignment="bottom")
    month = c1.selectbox("月", ["すべて"] + months, index=1, format_func=lambda m: m if m == "すべて" else f"{int(m[:4])}年{int(m[5:])}月")
    space = c2.selectbox("スペース", ["すべて"] + sorted(reports["space"].unique()))
    keyword = c3.text_input("キーワード", placeholder="例：納期、見積、シャッフルデスク")

view = reports
if month != "すべて":
    view = view[view["date"].str[:7] == month]
if space != "すべて":
    view = view[view["space"] == space]
if keyword.strip():
    kw = keyword.strip()
    view = view[view["sections"].map(lambda s: any(kw in l for ls in s.values() for l in ls))]

n_risk = int(view["sections"].map(lambda s: len(s.get("リスク", []))).sum())
n_dec = int(view["sections"].map(lambda s: len(s.get("決定事項", []))).sum())
fail = int(view["status"].str.contains("失敗").sum())
k1, k2, k3, k4 = st.columns(4)
with k1:
    ui.kpi("レポート", f"{len(view)}件", f"送信失敗 {fail}件" if fail else "すべて送信済み", "red" if fail else "green")
with k2:
    ui.kpi("メッセージ", f"{int(view['count'].sum())}件", "要約したチャットの数")
with k3:
    ui.kpi("決定事項", f"{n_dec}件")
with k4:
    ui.kpi("リスクの記載", f"{n_risk}件", "リスク一覧で対応状況を確認" if n_risk else "", "orange" if n_risk else "gray")

st.caption(f"{len(view)}件・新しい順")
if view.empty:
    st.info("この条件のレポートはありません。")
for i, (_, r) in enumerate(view.iterrows()):
    with st.expander(ui.report_title(r), expanded=(i == 0)):
        ui.send_badge(r["status"])
        ui.report_body(r["sections"])
