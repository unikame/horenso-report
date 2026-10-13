"""画面から使うデータ取得。読み込みに失敗したら、その場所にエラーを出して None を返す。"""
from __future__ import annotations

import streamlit as st

from . import ledger, sheets, survey


def _values(kind: str, quiet: bool = False):
    try:
        return sheets.load(kind)
    except sheets.SheetError as e:
        if not quiet:
            st.error(f"{_LABEL[kind]}：{e}", icon=":material/error:")
        return None


_LABEL = {"reports": "レポート履歴", "todos": "TODO", "risks": "リスク", "survey": "アンケート", "settings": "アンケート設定"}


def reports():
    v = _values("reports")
    return None if v is None else ledger.parse_reports(v)


def todos():
    v = _values("todos")
    return None if v is None else ledger.parse_todos(v)


def risks():
    v = _values("risks")
    return None if v is None else ledger.parse_risks(v)


def survey_all():
    """(回答の DataFrame, 自由記述の列, 対象人数, 回答率の目標) または None"""
    v = _values("survey")
    if v is None:
        return None
    df, free = survey.parse(v)
    target, goal = survey.parse_settings(_values("settings", quiet=True) or [])
    return df, free, target, goal
