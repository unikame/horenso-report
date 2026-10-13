"""報連相AI 管理画面（Streamlit）

起動： streamlit run app.py
"""
import streamlit as st

from horenso import config, data, sheets, ui

st.set_page_config(page_title="報連相AI 管理画面", page_icon=":material/dashboard:", layout="wide")
ui.inject_css()
st.logo("assets/logo.svg", icon_image="assets/mark.svg", size="large")

pg = st.navigation({
    "概要": [
        st.Page("views/home.py", title="ホーム", icon=":material/space_dashboard:", default=True),
    ],
    "報連相レポート": [
        st.Page("views/reports.py", title="レポート履歴", icon=":material/history:"),
        st.Page("views/risks.py", title="リスク", icon=":material/warning:"),
        st.Page("views/todos.py", title="TODO", icon=":material/task_alt:"),
    ],
    "報連相チェック": [
        st.Page("views/survey.py", title="アンケート", icon=":material/insights:"),
    ],
}, position="sidebar", expanded=True)

with st.sidebar:
    if st.button("最新を読み込む", icon=":material/refresh:", width="stretch", type="secondary"):
        sheets.reload_all()
        st.rerun()
    stamp = st.empty()
    st.caption(f"データは {int(config.get('CACHE_TTL')) // 60}分ごとに自動で更新されます。")
    st.markdown(
        f":material/table_chart: [管理台帳](https://docs.google.com/spreadsheets/d/{config.get('LEDGER_ID')}/edit)  \n"
        f":material/table_chart: [アンケート回答管理表](https://docs.google.com/spreadsheets/d/{config.get('SURVEY_ID')}/edit)"
    )

data.reset_errors()
pg.run()
stamp.caption(ui.stamp_text())           # 画面を描いたあとで、読み込んだ時刻を表示する
