"""管理台帳（送信履歴・TODO・リスク）の解析。Streamlit に依存しない純粋な関数だけを置く。"""
from __future__ import annotations

import datetime as dt
import re

import pandas as pd

SECTIONS = [("①報告", "報告"), ("②連絡", "連絡"), ("③相談", "相談"), ("④決定事項", "決定事項"),
            ("⑤TODO", "TODO"), ("⑥未解決事項", "未解決事項"), ("⑦リスク", "リスク")]
TODO_DONE = {"完了", "対応不要"}
RISK_DONE = {"対応済み", "対応不要"}
LEVEL_RANK = {"高": 0, "中": 1, "低": 2}
JST = dt.timezone(dt.timedelta(hours=9))


def today_jst() -> str:
    """サーバーは UTC で動くことが多いので、日本時間の今日を使う。"""
    return dt.datetime.now(JST).date().isoformat()


def to_frame(values: list[list[str]]) -> pd.DataFrame:
    """1行目を見出しにした DataFrame。空行は捨てる。列が足りない行は空文字で埋める。"""
    if not values:
        return pd.DataFrame()
    head = [str(h).strip() for h in values[0]]
    rows = []
    for r in values[1:]:
        r = list(r) + [""] * (len(head) - len(r))
        if any(str(c).strip() for c in r):
            rows.append([str(c) for c in r[: len(head)]])
    return pd.DataFrame(rows, columns=head)


def lines(text: str) -> list[str]:
    out = []
    for s in str(text or "").split("\n"):
        s = re.sub(r"^[・\-\s]+", "", s).strip()
        if s and s not in ("—", "-"):
            out.append(s)
    return out


def _col(df: pd.DataFrame, pattern: str) -> pd.Series:
    for c in df.columns:
        if re.search(pattern, c):
            return df[c]
    return pd.Series([""] * len(df), index=df.index)


def _days(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.str.extract(r"(-?\d+)")[0], errors="coerce")


def parse_reports(values) -> pd.DataFrame:
    df = to_frame(values)
    if df.empty:
        return pd.DataFrame(columns=["date", "dow", "space", "count", "status", "dest", "sections"])
    out = pd.DataFrame({
        "date": df["日付"].str.strip(),
        "dow": df.get("曜日", ""),
        "space": df.get("スペース", ""),
        "count": pd.to_numeric(df.get("メッセージ数", 0), errors="coerce").fillna(0).astype(int),
        "status": df.get("送信状態", ""),
        "dest": df["送信先"] if "送信先" in df else "",
    })
    out["sections"] = [{name: lines(row.get(col, "")) for col, name in SECTIONS} for _, row in df.iterrows()]
    out = out[out["date"].str.match(r"^\d{4}-\d{2}-\d{2}")]
    return out.sort_values("date", ascending=False).reset_index(drop=True)


def period_label(date: str, dow: str) -> str:
    """送信履歴の「曜日」列（例：金〜日（10/2（金）〜10/4（日）））から見出しを作る。"""
    if "（" in str(dow) and "〜" in str(dow):
        return re.sub(r"^[^（]*（", "", dow)[:-1]
    d = dt.date.fromisoformat(date[:10])
    return f"{d.month}/{d.day}（{dow}）"


def _due_date(s: str):
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", str(s))
    return m.group(0) if m else None


def parse_todos(values, today: str | None = None) -> pd.DataFrame:
    today = today or today_jst()
    df = to_frame(values)
    cols = ["id", "date", "space", "who", "what", "due", "state", "memo", "days", "open", "overdue"]
    if df.empty or "内容" not in df:
        return pd.DataFrame(columns=cols)
    out = pd.DataFrame({
        "id": df.get("TODO_ID", ""), "date": df.get("発生日", ""), "space": df.get("スペース", ""),
        "who": df.get("担当", "").replace("", "担当未定"), "what": df["内容"], "due": df.get("期限", "").replace("", "未定"),
        "state": df.get("状態", "").replace("", "未対応"), "memo": df.get("対応メモ", ""),
        "days": _days(_col(df, r"^経過日数")),
    })
    out = out[out["what"].str.strip() != ""].copy()
    out["open"] = ~out["state"].isin(TODO_DONE)
    out["overdue"] = out.apply(lambda r: bool(r["open"] and _due_date(r["due"]) and _due_date(r["due"]) < today), axis=1)
    return out.sort_values(["overdue", "days"], ascending=[False, False], na_position="last").reset_index(drop=True)


def parse_risks(values) -> pd.DataFrame:
    df = to_frame(values)
    cols = ["id", "date", "space", "level", "cat", "what", "state", "owner", "memo", "days", "open", "rank"]
    if df.empty or "内容" not in df:
        return pd.DataFrame(columns=cols)
    out = pd.DataFrame({
        "id": df.get("リスクID", ""), "date": df.get("発生日", ""), "space": df.get("スペース", ""),
        "level": df.get("レベル", ""), "cat": df.get("分類", ""), "what": df["内容"],
        "state": df.get("状態", "").replace("", "未対応"), "owner": df.get("対応者", ""), "memo": df.get("対応メモ", ""),
        "days": _days(_col(df, r"^経過日数")),
    })
    out = out[out["what"].str.strip() != ""].copy()
    out["open"] = ~out["state"].isin(RISK_DONE)
    out["rank"] = out["level"].map(LEVEL_RANK).fillna(3).astype(int)
    return out.sort_values(["rank", "days"], ascending=[True, False], na_position="last").reset_index(drop=True)
