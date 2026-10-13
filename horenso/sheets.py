"""Google スプレッドシートの読み込み（読み取り専用）。

認証は次のどちらか。
- secrets.toml の [gcp_service_account] にサービスアカウントの鍵（Streamlit Community Cloud など）
- 実行環境の既定の認証情報（Cloud Run に割り当てたサービスアカウントなど。鍵ファイル不要）
どちらの場合も、そのサービスアカウントのメールアドレスを、管理台帳とアンケートのスプレッドシートに「閲覧者」で共有しておく。
"""
from __future__ import annotations

import gspread
import streamlit as st

from . import config

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


class SheetError(Exception):
    """画面に出すための、わかりやすい読み込みエラー。"""


@st.cache_resource(show_spinner=False)
def _client():
    if "gcp_service_account" in st.secrets:
        from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=SCOPES)
    else:
        import google.auth
        creds, _ = google.auth.default(scopes=SCOPES)
    return gspread.authorize(creds), getattr(creds, "service_account_email", "")


def service_account_email() -> str:
    try:
        return _client()[1] or ""
    except Exception:
        return ""


def _ttl() -> int:
    try:
        return int(config.get("CACHE_TTL"))
    except ValueError:
        return 600


@st.cache_data(ttl=_ttl(), show_spinner="スプレッドシートを読み込んでいます…")
def load_values(sheet_id: str, tab: str) -> list[list[str]]:
    """タブ全体を、画面に表示されている書式どおりの文字列で返す。"""
    try:
        gc, email = _client()
    except Exception as e:  # 認証情報がない・壊れている
        raise SheetError("Google の認証情報が見つかりません。README の「認証の準備」を確認してください。（" + type(e).__name__ + "）") from e
    try:
        return gc.open_by_key(sheet_id).worksheet(tab).get_values()
    except gspread.exceptions.WorksheetNotFound as e:
        raise SheetError("スプレッドシートに「" + tab + "」タブが見つかりません。タブ名が変わっていないか確認してください。") from e
    except gspread.exceptions.SpreadsheetNotFound as e:
        raise SheetError("スプレッドシートが見つからないか、共有されていません。" + (email + " を閲覧者として共有してください。" if email else "")) from e
    except gspread.exceptions.APIError as e:
        code = getattr(getattr(e, "response", None), "status_code", None)
        if code == 403:
            raise SheetError("スプレッドシートを読む権限がありません。" + (email + " を閲覧者として共有してください。" if email else "")) from e
        if code == 429:
            raise SheetError("Google の読み込み回数の上限に達しました。1分ほど待ってから再読み込みしてください。") from e
        raise SheetError("スプレッドシートを読み込めませんでした（" + str(code) + "）。") from e


def load(kind: str) -> list[list[str]]:
    """kind: reports / todos / risks / survey / settings"""
    sheet = config.get("LEDGER_ID") if kind in ("reports", "todos", "risks") else config.get("SURVEY_ID")
    return load_values(sheet, config.TABS[kind])


def reload_all():
    load_values.clear()
