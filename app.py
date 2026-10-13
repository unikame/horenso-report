"""報連相AI 管理画面（Streamlit）

起動： streamlit run app.py
"""
import streamlit as st

from horenso import config, data, sheets

st.set_page_config(page_title="報連相AI 管理画面", page_icon=":material/dashboard:", layout="wide")

pages = [
    st.Page("views/home.py", title="ホーム", icon=":material/home:", default=True),
    st.Page("views/reports.py", title="レポート履歴", icon=":material/history:"),
    st.Page("views/risks.py", title="リスク", icon=":material/warning:"),
    st.Page("views/todos.py", title="TODO", icon=":material/checklist:"),
    st.Page("views/survey.py", title="アンケート", icon=":material/insights:"),
]
pg = st.navigation(pages, position="top")

with st.sidebar:
    st.markdown("### 報連相AI 管理画面")
    if st.button("最新を読み込む", icon=":material/refresh:", width="stretch"):
        sheets.reload_all()
        st.rerun()
    st.caption(f"読み込んだ内容は {int(config.get('CACHE_TTL')) // 60}分ごとに自動で更新されます。")
    st.markdown(
        f"- [管理台帳](https://docs.google.com/spreadsheets/d/{config.get('LEDGER_ID')}/edit)\n"
        f"- [アンケート回答管理表](https://docs.google.com/spreadsheets/d/{config.get('SURVEY_ID')}/edit)"
    )
    email = sheets.service_account_email()
    if email:
        st.caption(f"読み込みに使うアカウント：{email}")

data.reset_errors()
pg.run()
