"""報連相チェック集計（Streamlit）

Googleフォームの回答（スプレッドシート）を読み込み、集計画面を表示する。
画面そのものは horenso/dashboard.html（週・月の切り替え、個人の記録などはブラウザ側で動く）。

起動： streamlit run app.py
"""
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from horenso import config, sheets

st.set_page_config(page_title="報連相チェック集計", page_icon=":material/insights:", layout="wide", initial_sidebar_state="collapsed")

# Streamlit 標準の飾り（上部のバー・余白・サイドバー）を消して、集計画面だけを全面に出す
st.html("""<style>
header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], #MainMenu, footer { display: none !important; }
.block-container, [data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: none !important; }
[data-testid="stMainBlockContainer"] > div { gap: 0 !important; }
iframe { display: block; border: 0; }
</style>""")

# 「最新を読み込む」から ?reload=1 付きで開かれたら、読み込み済みの内容を捨てて読み直す
if st.query_params.get("reload"):
    sheets.reload_all()
    st.query_params.clear()

try:
    values = sheets.load("survey")
except sheets.SheetError as e:
    with st.container(border=True):
        st.error(str(e), icon=":material/error:")
    st.stop()
try:
    settings = sheets.load("settings")             # 対象人数・回答率の目標（なくても動く）
except sheets.SheetError:
    settings = []

t = sheets.loaded_at()
loaded = f"{t.month}/{t.day} {t:%H:%M}" if t else ""


def js(obj) -> str:
    """<script> の中に安全に埋め込める JSON にする。"""
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


page = (Path(__file__).parent / "horenso" / "dashboard.html").read_text(encoding="utf-8")
page = (page.replace("__VALUES__", js(values))
            .replace("__SETTINGS__", js(settings))
            .replace("__LOADED__", js(loaded))
            .replace("__SHEET_URL__", f"https://docs.google.com/spreadsheets/d/{config.get('SURVEY_ID')}/edit"))

# 高さは画面の中から自動で合わせる（最初は大きめに取っておく）
components.html(page, height=2400, scrolling=False)
