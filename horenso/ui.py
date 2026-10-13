"""画面の部品と色。色はグラフの役割ごとに固定する（項目の色は並び順で変えない）。"""
from __future__ import annotations

import streamlit as st

from . import ledger

ITEM_COLORS = {"報告": "#2a78d6", "連絡": "#eb6834", "相談": "#1baf7a"}
# 点数 1〜5 の分布：低い点は赤系、3点は灰、高い点は青系（中央が灰の発散配色）
LEVEL_COLORS = {1: "#c43b3b", 2: "#ef9f9a", 3: "#c9c8c2", 4: "#86b6ef", 5: "#2a78d6"}
ACCENT = "#1f395f"


def level_badge(level: str):
    color = {"高": "red", "中": "orange", "低": "gray"}.get(level, "gray")
    st.badge(("▲ " if level == "高" else "") + (level or "–"), color=color)


def risk_state_badge(s: str):
    st.badge(s, color={"未対応": "red", "確認中": "orange", "対応済み": "green"}.get(s, "gray"))


def todo_state_badge(s: str):
    st.badge(s, color={"未対応": "orange", "対応中": "blue", "完了": "green", "要確認": "orange"}.get(s, "gray"))


def send_badge(s: str):
    if "送信済み" in s:
        st.badge("送信済み", icon=":material/check:", color="green")
    elif "失敗" in s:
        st.badge("送信失敗", icon=":material/error:", color="red")
    elif "やりとりなし" in s:
        st.badge("やりとりなし", color="gray")
    else:
        st.badge(s or "–", color="gray")


def report_body(sections: dict):
    items = [(name, sections.get(name, [])) for _, name in ledger.SECTIONS if sections.get(name)]
    if not items:
        st.caption("対象期間のやりとりはありませんでした。")
        return
    cols = st.columns(2)
    for i, (name, lines) in enumerate(items):
        with cols[i % 2]:
            st.markdown(f"**{':red[' + name + ']' if name == 'リスク' else name}**　:gray[{len(lines)}]")
            st.markdown("\n".join("- " + l.replace("\n", " ") for l in lines))


def report_title(r) -> str:
    counts = []
    for name, word in (("決定事項", "決定"), ("TODO", "TODO"), ("未解決事項", "未解決"), ("リスク", "リスク")):
        n = len(r["sections"].get(name, []))
        if n:
            counts.append(f"{word} {n}")
    status = "送信失敗" if "失敗" in r["status"] else ("やりとりなし" if "やりとりなし" in r["status"] else "")
    return (f"{ledger.period_label(r['date'], r['dow'])}　{r['space']}　｜　メッセージ {r['count']}件"
            + ("　" + "・".join(counts) if counts else "") + (f"　［{status}］" if status else ""))


def fmt(v, d=2):
    return "–" if v is None else f"{v:.{d}f}"
