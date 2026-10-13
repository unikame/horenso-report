"""報連相チェック（Googleフォーム）の解析と集計。Streamlit に依存しない純粋な関数だけを置く。

集計のルール
- 回答は「回答日の直前の金曜日（金曜当日を含む）」の配信週にまとめる
- 同じ人が同じ週に複数回答したら、新しい回答を使う（氏名の空白は無視して同一人物とみなす）
- 月ごとの集計は、配信週（金曜）が属する月でまとめる
"""
from __future__ import annotations

import datetime as dt
import re

import pandas as pd

ITEMS = [("r", "報告", "【報告】"), ("c", "連絡", "【連絡】"), ("s", "相談", "【相談】")]
ITEM_NAMES = {k: n for k, n, _ in ITEMS}
LEVELS = {5: "10割できた", 4: "9割できた", 3: "8〜9割できた", 2: "5〜8割できた", 1: "5割未満"}


def _stamp(s):
    m = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?", str(s))
    if not m:
        return None
    y, mo, d, h, mi, se = (int(x) if x else 0 for x in m.groups())
    return dt.datetime(y, mo, d, h, mi, se)


def friday_of(d: dt.datetime) -> str:
    back = (d.weekday() - 4) % 7          # 月=0 … 金=4
    return (d.date() - dt.timedelta(days=back)).isoformat()


def _score(v):
    m = re.match(r"\s*([1-5])", str(v or ""))
    return int(m.group(1)) if m else None


def short_header(h: str) -> str:
    h = re.sub(r"^\s*\d+\.\s*", "", str(h))
    return re.sub(r"\s*[（(][^）)]*[）)]\s*$", "", h).strip()


def parse(values) -> tuple[pd.DataFrame, list[tuple[str, str]]]:
    """回答の表 → (1回答1行の DataFrame, 自由記述の列 [(列名, 表示名)])"""
    cols = ["at", "week", "month", "name", "key", "dept", "r", "c", "s", "total"]
    if not values:
        return pd.DataFrame(columns=cols), []
    head = [str(h) for h in values[0]]
    idx = {"name": None, "dept": None}
    for i, h in enumerate(head):
        if idx["name"] is None and re.search(r"氏名|名前", h):
            idx["name"] = i
        elif idx["dept"] is None and re.search(r"部署|所属", h):
            idx["dept"] = i
        for k, _, mark in ITEMS:
            if mark in h:
                idx[k] = i
    last_score = max([idx.get(k, 0) or 0 for k, _, _ in ITEMS] + [0])
    free = [(f"free{i}", short_header(h)) for i, h in enumerate(head) if i > last_score and h.strip()]

    recs = {}
    for r in values[1:]:
        r = list(r) + [""] * (len(head) - len(r))
        at = _stamp(r[0])
        if not at:
            continue
        name = str(r[idx["name"]] if idx["name"] is not None else "").strip() or "（氏名なし）"
        rec = {"at": at, "week": friday_of(at), "name": name, "key": re.sub(r"\s+", "", name),
               "dept": str(r[idx["dept"]] if idx["dept"] is not None else "").strip() or "未記入"}
        rec["month"] = rec["week"][:7]
        scores = {k: _score(r[idx[k]]) if idx.get(k) is not None else None for k, _, _ in ITEMS}
        if any(v is None for v in scores.values()):
            continue
        rec.update(scores)
        rec["total"] = sum(scores.values())
        for i, (col, _) in enumerate(free):
            j = int(col[4:])
            rec[col] = str(r[j]).strip()
        k = (rec["week"], rec["key"])
        if k not in recs or recs[k]["at"] < at:
            recs[k] = rec
    df = pd.DataFrame(list(recs.values()))
    if df.empty:
        return pd.DataFrame(columns=cols + [c for c, _ in free]), free
    return df.sort_values("at").reset_index(drop=True), free


def parse_settings(values) -> tuple[float | None, float | None]:
    """「分析」タブから（対象人数, 回答率の目標）を読む。見つからなければ None。"""
    target = goal = None
    for r in values or []:
        lab = str(r[0]) if r else ""
        val = str(r[1]) if len(r) > 1 else ""
        if "対象人数" in lab:
            n = re.sub(r"[^\d.]", "", val)
            target = float(n) if n else None
        if "回答率の目標" in lab:
            n = re.sub(r"[^\d.]", "", val)
            if n:
                g = float(n)
                goal = g / 100 if ("%" in val or g > 1) else g
    return target, goal


# ---- 集計 ----
def period_col(unit: str) -> str:
    return "week" if unit == "week" else "month"


def periods(df: pd.DataFrame, unit: str) -> list[str]:
    return sorted(df[period_col(unit)].unique().tolist(), reverse=True) if len(df) else []


def rows_in(df: pd.DataFrame, unit: str, p: str) -> pd.DataFrame:
    return df[df[period_col(unit)] == p]


def stats(rows: pd.DataFrame) -> dict:
    if rows.empty:
        return {"n": 0, "people": 0, "r": None, "c": None, "s": None, "total": None}
    return {"n": len(rows), "people": rows["key"].nunique(), "r": rows["r"].mean(), "c": rows["c"].mean(),
            "s": rows["s"].mean(), "total": rows["total"].mean()}


def rate_of(df: pd.DataFrame, unit: str, p: str, target: float | None):
    """週＝回答者/対象人数、月＝その月の各配信週の回答率の平均"""
    if not target:
        return None
    rows = rows_in(df, unit, p)
    if rows.empty:
        return None
    per_week = rows.groupby("week")["key"].nunique() / target
    return float(per_week.mean())


def prev_period(ps: list[str], p: str):
    i = ps.index(p) if p in ps else -1
    return ps[i + 1] if 0 <= i < len(ps) - 1 else None


def per_person(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame(columns=["key", "name", "dept", "r", "c", "s", "total", "n"])
    g = rows.sort_values("at").groupby("key")
    out = g.agg(name=("name", "last"), dept=("dept", "last"), r=("r", "mean"), c=("c", "mean"), s=("s", "mean"),
                total=("total", "mean"), n=("total", "size")).reset_index()
    return out


def follow_list(df: pd.DataFrame, unit: str, p: str, ps: list[str]) -> pd.DataFrame:
    """声をかけたい人：2点以下の項目／合計9点以下／前の期間から3点以上低下"""
    cur = per_person(rows_in(df, unit, p))
    pp = prev_period(ps, p)
    prev = per_person(rows_in(df, unit, pp)).set_index("key") if pp else pd.DataFrame()
    reasons = []
    word = "前週" if unit == "week" else "前月"
    for _, x in cur.iterrows():
        why = [f"{ITEM_NAMES[k]} {x[k]:.{0 if unit == 'week' else 1}f}点" for k, _, _ in ITEMS if x[k] <= 2]
        if x["total"] <= 9:
            why.append(f"合計 {x['total']:.{0 if unit == 'week' else 1}f}点")
        if len(prev) and x["key"] in prev.index and prev.loc[x["key"], "total"] - x["total"] >= 3:
            why.append(f"{word}から −{prev.loc[x['key'], 'total'] - x['total']:.{0 if unit == 'week' else 1}f}点")
        reasons.append("／".join(why))
    cur["why"] = reasons
    return cur[cur["why"] != ""].sort_values("total").reset_index(drop=True)


def weakest(st: dict):
    vals = {k: st[k] for k, _, _ in ITEMS if st[k] is not None}
    if not vals or all(v == 5 for v in vals.values()):
        return None
    k = min(vals, key=vals.get)
    return ITEM_NAMES[k], vals[k]


def label(p: str, unit: str) -> str:
    y, m, *d = p.split("-")
    return f"{int(m)}/{int(d[0])}週" if unit == "week" else f"{int(y)}年{int(m)}月"
