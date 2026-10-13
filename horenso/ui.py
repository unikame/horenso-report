"""画面の部品と色。

色の決まり
- 報告・連絡・相談は固定色（青・橙・緑）。並び順で色を変えない
- 点数 1〜5 は「低い点＝赤系、3点＝灰、高い点＝青系」
- 状態の色は意味で固定（未対応＝赤、確認中・期限切れ＝橙、完了＝緑）。色だけに頼らず文字も必ず添える
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from . import ledger, sheets

ITEM_COLORS = {"報告": "#2a78d6", "連絡": "#eb6834", "相談": "#1baf7a"}
LEVEL_COLORS = {1: "#c43b3b", 2: "#ef9f9a", 3: "#c9c8c2", 4: "#86b6ef", 5: "#2a78d6"}
ACCENT = "#1f395f"
RED, ORANGE, GREEN, BLUE, GRAY = "#c43b3b", "#c97a12", "#1e8a3c", "#1f5fa8", "#768194"

CSS = """
<style>
/* 本文の幅と余白 */
.block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1320px; }
/* 見出しまわり */
h1 { letter-spacing: .01em; }
.hr-eyebrow { font-size: .72rem; letter-spacing: .12em; color: #768194; margin-bottom: .1rem; }
.hr-sub { color: #768194; font-size: .85rem; margin-top: -.35rem; }
.hr-stamp { text-align: right; color: #768194; font-size: .78rem; line-height: 1.5; }
/* 数字のカード：ラベルを小さく控えめに */
[data-testid="stMetricLabel"] p { font-size: .78rem; letter-spacing: .03em; opacity: .78; }
[data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
/* 折りたたみの見出し */
[data-testid="stExpander"] summary p { font-weight: 500; }
/* 左メニューのブランド */
.hr-brand { font-weight: 600; font-size: 1.02rem; letter-spacing: .02em; margin: .2rem 0 .1rem; }
.hr-brand-sub { font-size: .75rem; opacity: .7; margin-bottom: .6rem; }
/* 一覧の1行 */
.hr-row { display: grid; grid-template-columns: auto 1fr auto; gap: .2rem .75rem; padding: .55rem 0; border-top: 1px solid rgba(128,140,160,.22); align-items: start; }
.hr-row:first-child { border-top: 0; }
.hr-row .main { min-width: 0; overflow-wrap: anywhere; }
.hr-row .meta { font-size: .78rem; color: #768194; }
.hr-row .side { text-align: right; font-size: .78rem; color: #768194; white-space: nowrap; }
.hr-tag { display: inline-block; font-size: .72rem; font-weight: 600; padding: .05rem .5rem; border-radius: 999px; white-space: nowrap; }
.hr-empty { color: #768194; font-size: .85rem; padding: .4rem 0; }
</style>
"""


def inject_css():
    st.html(CSS)


def page_header(title: str, subtitle: str = "", eyebrow: str = ""):
    if eyebrow:
        st.html(f'<div class="hr-eyebrow">{eyebrow}</div>')
    st.title(title, anchor=False)
    if subtitle:
        st.html(f'<div class="hr-sub">{subtitle}</div>')


def stamp_text() -> str:
    t = sheets.loaded_at()
    return f":material/schedule: 最終読み込み {t.month}/{t.day} {t:%H:%M}" if t else ""


def kpi(label: str, value: str, note: str = "", tone: str = "gray", help: str | None = None, delta: str | None = None):
    """高さをそろえた数字のカード。note は下に添える短い状態表示。"""
    with st.container(border=True, height=136):
        st.metric(label, value, delta=delta, help=help)
        if note:
            st.badge(note, color=tone)


def section_title(title: str, page: str | None = None, link: str = "すべて見る", note: str = ""):
    left, right = st.columns([3, 1], vertical_alignment="center")
    with left:
        st.subheader(title, anchor=False)
        if note:
            st.caption(note)
    if page:
        with right:
            st.page_link(page, label=link, icon=":material/arrow_forward:")


def tag(text: str, color: str) -> str:
    return f'<span class="hr-tag" style="color:{color};background:{color}1f">{text}</span>'


def rows_html(rows: list[tuple[str, str, str, str]], empty: str) -> str:
    """(左の札, 本文, 補足, 右の表示) の並び。本文・補足は呼び出し側でエスケープ済みにする。"""
    if not rows:
        return f'<div class="hr-empty">{empty}</div>'
    return "".join(f'<div class="hr-row"><div>{a}</div><div class="main">{b}<div class="meta">{c}</div></div><div class="side">{d}</div></div>' for a, b, c, d in rows)


def esc(s) -> str:
    import html
    return html.escape(str(s if s is not None else ""))


# ---- 表の色分け（文字色だけを変えるので、明るい／暗い表示のどちらでも読める） ----
STATE_COLORS = {"未対応": RED, "確認中": ORANGE, "対応中": BLUE, "要確認": ORANGE, "完了": GREEN, "対応済み": GREEN, "対応不要": GRAY,
                "▲ 高": RED, "高": RED, "中": ORANGE, "低": GRAY, "期限切れ": RED}


def color_text(v):
    c = STATE_COLORS.get(str(v))
    return f"color: {c}; font-weight: 600" if c else ""


def styled(df: pd.DataFrame, cols: list[str]):
    return df.style.map(color_text, subset=[c for c in cols if c in df.columns])


# ---- レポート ----
def send_badge(s: str):
    if "送信済み" in s:
        st.badge("送信済み", icon=":material/check:", color="green")
    elif "失敗" in s:
        st.badge("送信失敗", icon=":material/error:", color="red")
    elif "やりとりなし" in s:
        st.badge("やりとりなし", color="gray")
    else:
        st.badge(s or "–", color="gray")


SECTION_ICONS = {"報告": ":material/campaign:", "連絡": ":material/forward_to_inbox:", "相談": ":material/forum:",
                 "決定事項": ":material/gavel:", "TODO": ":material/task_alt:", "未解決事項": ":material/help:", "リスク": ":material/warning:"}


def report_body(sections: dict):
    items = [(name, sections.get(name, [])) for _, name in ledger.SECTIONS if sections.get(name)]
    if not items:
        st.caption("対象期間のやりとりはありませんでした。")
        return
    cols = st.columns(2, gap="large")
    for i, (name, lines) in enumerate(items):
        with cols[i % 2]:
            head = f":red[**{name}**]" if name == "リスク" else f"**{name}**"
            st.markdown(f"{SECTION_ICONS.get(name, '')} {head}　:gray[{len(lines)}件]")
            st.markdown("\n".join("- " + l.replace("\n", " ") for l in lines))


def report_title(r) -> str:
    counts = []
    for name, word in (("決定事項", "決定"), ("TODO", "TODO"), ("未解決事項", "未解決"), ("リスク", "リスク")):
        n = len(r["sections"].get(name, []))
        if n:
            counts.append(f"{word} {n}")
    status = " :red[送信失敗]" if "失敗" in r["status"] else (" :gray[やりとりなし]" if "やりとりなし" in r["status"] else "")
    return (f"**{ledger.period_label(r['date'], r['dow'])}**　{r['space']}　:gray[メッセージ {r['count']}件"
            + ("・" + "・".join(counts) if counts else "") + "]" + status)


def fmt(v, d=2):
    return "–" if v is None or v != v else f"{v:.{d}f}"
