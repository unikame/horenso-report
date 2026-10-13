import altair as alt
import pandas as pd
import streamlit as st

from horenso import data, survey as sv, ui

st.title("アンケート（報連相チェック）")
st.caption(":material/lock: 委員会内での分析用です。本人への共有や評価には使用しません。")

res = data.survey_all()
if res is None:
    st.stop()
df, free, target, goal = res
if df.empty:
    st.info("回答がまだありません。フォームに回答が入ると、ここに集計が表示されます。")
    st.stop()

ITEMS = [(k, n) for k, n, _ in sv.ITEMS]
COLOR = alt.Scale(domain=[n for _, n in ITEMS], range=[ui.ITEM_COLORS[n] for _, n in ITEMS])

# ---- 期間の選択 ----
c1, c2, _ = st.columns([1, 2, 2])
with c1:
    unit_label = st.segmented_control("集計単位", ["週ごと", "月ごと"], default="週ごと", required=True, key="unit")
unit = "week" if unit_label == "週ごと" else "month"
ps = sv.periods(df, unit)


def period_name(p):
    if unit == "week":
        return p.replace("-", "/") + "（金）"
    return f"{sv.label(p, 'month')}（配信 {sv.rows_in(df, 'month', p)['week'].nunique()}回）"


with c2:
    p = st.selectbox("配信週（金曜）" if unit == "week" else "月", ps, format_func=lambda x: period_name(x) + ("　最新" if x == ps[0] else ""), key="period_" + unit)
pp = sv.prev_period(ps, p)
rows = sv.rows_in(df, unit, p)
cur, prev = sv.stats(rows), sv.stats(sv.rows_in(df, unit, pp)) if pp else None
word = "前週比" if unit == "week" else "前月比"
d0 = 0 if unit == "week" else 1

# ---- サマリー ----
k1, k2, k3, k4 = st.columns(4)
rate = sv.rate_of(df, unit, p, target)
prate = sv.rate_of(df, unit, pp, target) if pp else None
with k1:
    st.metric("回答者数" if unit == "week" else "回答した人（実人数）",
              f"{cur['people']}人" + (f" / {int(target)}人" if target else ""),
              delta=(f"{cur['people'] - prev['people']:+d}人" if prev and unit == "week" else None), border=True,
              help=None if unit == "week" else f"延べ {cur['n']}件")
with k2:
    st.metric("回答率" if unit == "week" else "回答率（各週の平均）", f"{rate:.0%}" if rate is not None else "–",
              delta=(f"{(rate - prate) * 100:+.0f}pt" if rate is not None and prate is not None else None), border=True,
              help=None if target else "「分析」タブの対象人数が未設定です")
    if rate is not None and goal is not None:
        st.badge(f"目標{goal:.0%}達成" if rate >= goal else f"目標{goal:.0%}に未達",
                 icon=":material/check:" if rate >= goal else ":material/warning:", color="green" if rate >= goal else "orange")
with k3:
    st.metric("合計平均（15点満点）", ui.fmt(cur["total"]),
              delta=(f"{cur['total'] - prev['total']:+.2f}" if prev else None), border=True)
with k4:
    w = sv.weakest(cur)
    st.metric("いちばん弱い項目", f"{w[0]} {w[1]:.2f}点" if w else "なし（全項目満点）", border=True,
              help="次の施策・掲示板発信のテーマ候補")

# ---- 項目別の平均・分布 ----
a, b = st.columns(2)
with a:
    with st.container(border=True):
        st.subheader("項目別の平均")
        avg = pd.DataFrame([{"項目": n, "平均": cur[k], "前": (prev[k] if prev else None)} for k, n in ITEMS])
        avg["表示"] = avg.apply(lambda r: f"{r['平均']:.2f}" + (f"（{word} {r['平均'] - r['前']:+.2f}）" if pd.notna(r["前"]) else ""), axis=1)
        base = alt.Chart(avg).encode(y=alt.Y("項目:N", sort=[n for _, n in ITEMS], title=None, scale=alt.Scale(paddingInner=0.45)))
        bars = base.mark_bar(cornerRadiusEnd=4).encode(
            x=alt.X("平均:Q", scale=alt.Scale(domain=[0, 5]), axis=alt.Axis(values=[0, 1, 2, 3, 4, 5], title="5点満点")),
            color=alt.Color("項目:N", scale=COLOR, legend=None),
            tooltip=[alt.Tooltip("項目:N"), alt.Tooltip("平均:Q", format=".2f")])
        text = base.mark_text(align="left", dx=6).encode(x="平均:Q", text="表示:N")
        st.altair_chart((bars + text).properties(height=alt.Step(34)), width="stretch")
with b:
    with st.container(border=True):
        st.subheader("点数の分布")
        dist = []
        for k, n in ITEMS:
            for lv in range(1, 6):
                cnt = int((rows[k] == lv).sum())
                if cnt:
                    dist.append({"項目": n, "点数": lv, "点数名": f"{lv}点 {sv.LEVELS[lv]}", "件数": cnt})
        dd = pd.DataFrame(dist)
        chart = alt.Chart(dd).mark_bar().encode(
            y=alt.Y("項目:N", sort=[n for _, n in ITEMS], title=None, scale=alt.Scale(paddingInner=0.35)),
            x=alt.X("sum(件数):Q", stack="normalize", axis=alt.Axis(format="%", title="人数" if unit == "week" else "延べ件数（割合）")),
            color=alt.Color("点数名:N", scale=alt.Scale(domain=[f"{lv}点 {sv.LEVELS[lv]}" for lv in range(1, 6)],
                                                       range=[ui.LEVEL_COLORS[lv] for lv in range(1, 6)]),
                            legend=alt.Legend(orient="bottom", title=None, columns=3)),
            order=alt.Order("点数:Q"),
            tooltip=["項目:N", "点数名:N", "件数:Q"])
        st.altair_chart(chart.properties(height=alt.Step(34)), width="stretch")

# ---- 推移 ----
with st.container(border=True):
    st.subheader("推移")
    trend = []
    for q in sorted(ps):
        s = sv.stats(sv.rows_in(df, unit, q))
        for k, n in ITEMS:
            trend.append({"期間": sv.label(q, unit), "順": q, "項目": n, "平均": s[k], "件数": s["n"]})
    td = pd.DataFrame(trend)
    if len(ps) < 2:
        st.caption(f"2{'週' if unit == 'week' else 'か月'}分以上たまると、線で推移が見られます。")
    order = [sv.label(q, unit) for q in sorted(ps)]
    line = alt.Chart(td).encode(
        x=alt.X("期間:N", sort=order, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("平均:Q", scale=alt.Scale(domain=[1, 5]), title="平均（5点満点）"),
        color=alt.Color("項目:N", scale=COLOR, legend=alt.Legend(orient="top", title=None)),
        tooltip=["期間:N", "項目:N", alt.Tooltip("平均:Q", format=".2f"), "件数:Q"])
    st.altair_chart((line.mark_line(strokeWidth=2) + line.mark_point(filled=True, size=60)).properties(height=240), width="stretch")
    if target:
        rd = pd.DataFrame([{"期間": sv.label(q, unit), "回答率": sv.rate_of(df, unit, q, target)} for q in sorted(ps)])
        rc = alt.Chart(rd).encode(x=alt.X("期間:N", sort=order, title=None, axis=alt.Axis(labelAngle=0)),
                                  y=alt.Y("回答率:Q", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format="%"), title="回答率"),
                                  tooltip=["期間:N", alt.Tooltip("回答率:Q", format=".0%")])
        layers = rc.mark_line(color=ui.ACCENT, strokeWidth=2) + rc.mark_point(color=ui.ACCENT, filled=True, size=50)
        if goal is not None:
            layers += alt.Chart(pd.DataFrame({"目標": [goal]})).mark_rule(strokeDash=[4, 4], color="#768194").encode(y="目標:Q")
        st.altair_chart(layers.properties(height=130), width="stretch")
    with st.expander("表で見る"):
        tbl = []
        for q in sorted(ps, reverse=True):
            s = sv.stats(sv.rows_in(df, unit, q))
            r_ = sv.rate_of(df, unit, q, target)
            tbl.append({"期間": sv.label(q, unit), "回答者": s["people"], "回答率": r_, "報告": s["r"], "連絡": s["c"], "相談": s["s"], "合計": s["total"]})
        st.dataframe(pd.DataFrame(tbl), hide_index=True, width="stretch", column_config={
            "回答率": st.column_config.NumberColumn(format="percent"),
            **{c: st.column_config.NumberColumn(format="%.2f") for c in ("報告", "連絡", "相談", "合計")}})

# ---- 部署別・声をかけたい人 ----
a, b = st.columns(2)
with a:
    with st.container(border=True):
        st.subheader("部署別の平均")
        scope = st.segmented_control("集計期間", ["選択した期間", "全期間"], default="選択した期間", required=True, key="dept_scope")
        base_rows = rows if scope == "選択した期間" else df
        dept = base_rows.groupby("dept").agg(人数=("key", "nunique"), 報告=("r", "mean"), 連絡=("c", "mean"), 相談=("s", "mean"), 合計=("total", "mean")).reset_index().rename(columns={"dept": "部署"}).sort_values("合計")
        st.dataframe(dept, hide_index=True, width="stretch", column_config={
            **{c: st.column_config.ProgressColumn(c, min_value=0, max_value=5, format="%.2f") for c in ("報告", "連絡", "相談")},
            "合計": st.column_config.NumberColumn(format="%.1f")})
        if (dept["人数"] < 3).any():
            st.caption("回答者が3人未満の部署は個人の点数に近いため、扱いに注意してください。")
with b:
    with st.container(border=True):
        st.subheader("声をかけたい人")
        st.caption("2点以下の項目がある／合計9点以下／前の期間から3点以上下がった")
        fl = sv.follow_list(df, unit, p, ps)
        if fl.empty:
            st.caption("この期間に該当する人はいません。")
        first_free = free[0][0] if free else None
        for _, x in fl.iterrows():
            with st.container(border=True):
                st.markdown(f"**{x['name']}**　:gray[{x['dept']}]　報告{x['r']:.{d0}f}・連絡{x['c']:.{d0}f}・相談{x['s']:.{d0}f}（計{x['total']:.{d0}f}）")
                st.markdown(f":red[{x['why']}]")
                if first_free:
                    cm = [c for c in rows[rows["key"] == x["key"]].sort_values("at")[first_free] if c]
                    if cm:
                        st.caption(cm[-1])

# ---- 個人別 ----
with st.container(border=True):
    st.subheader("個人別")
    st.caption(("月内の平均。" if unit == "month" else "") + "合計の低い順。行を選ぶと、その人の記録を下に表示します。")
    pe = sv.per_person(rows)
    prevp = sv.per_person(sv.rows_in(df, unit, pp)).set_index("key")["total"] if pp else pd.Series(dtype=float)
    pe["差"] = pe.apply(lambda x: x["total"] - prevp[x["key"]] if x["key"] in prevp.index else None, axis=1)
    pe["回答"] = pe["key"].map(df.groupby("key").size()) if unit == "week" else pe["n"]
    pe = pe.sort_values(["total", "name"]).reset_index(drop=True)
    fmt = "%d" if unit == "week" else "%.1f"
    sel = st.dataframe(
        pe[["name", "dept", "r", "c", "s", "total", "差", "回答"]], hide_index=True, width="stretch",
        on_select="rerun", selection_mode="single-row", key="people_" + unit + p,
        column_config={"name": "氏名", "dept": "部署",
                       "r": st.column_config.NumberColumn("報告", format=fmt), "c": st.column_config.NumberColumn("連絡", format=fmt),
                       "s": st.column_config.NumberColumn("相談", format=fmt), "total": st.column_config.NumberColumn("合計", format=fmt),
                       "差": st.column_config.NumberColumn(word, format="%+.1f"),
                       "回答": st.column_config.NumberColumn("累計回答" if unit == "week" else "この月の回答", format="%d回")})
    picked = sel.selection.rows if sel and sel.selection else []

# ---- 個人の記録 ----
with st.container(border=True):
    st.subheader("個人の記録")
    everyone = sv.per_person(df).sort_values("name")
    names = everyone["key"].tolist()
    label_of = dict(zip(everyone["key"], everyone["name"] + "（" + everyone["dept"] + "）"))
    if picked:                                   # 表で行を選んだら、その人に切り替える
        k = pe.iloc[picked[0]]["key"]
        if st.session_state.get("last_pick") != k:
            st.session_state["last_pick"] = k
            st.session_state["person"] = k
    else:
        st.session_state["last_pick"] = None
    if st.session_state.get("person") not in names:
        st.session_state["person"] = pe.iloc[0]["key"] if len(pe) else names[0]
    who = st.selectbox("氏名", names, format_func=lambda k: label_of[k], key="person")
    mine = df[df["key"] == who].sort_values("at")
    first, last = mine.iloc[0], mine.iloc[-1]
    diff = int(last["total"] - first["total"])
    st.caption(f"回答 {len(mine)}回（{sv.label(first['week'], 'week')}〜{sv.label(last['week'], 'week')}）・合計 初回 {first['total']} → 最新 {last['total']}"
               + (f"（{diff:+d}点）" if len(mine) > 1 else ""))
    pl = mine.melt(id_vars=["week"], value_vars=[k for k, _ in ITEMS], var_name="k", value_name="点数")
    pl["項目"] = pl["k"].map(dict(ITEMS))
    pl["週"] = pl["week"].map(lambda w: sv.label(w, "week"))
    wk_order = [sv.label(w, "week") for w in mine["week"]]
    pc = alt.Chart(pl).encode(x=alt.X("週:N", sort=wk_order, title=None, axis=alt.Axis(labelAngle=0)),
                              y=alt.Y("点数:Q", scale=alt.Scale(domain=[1, 5]), axis=alt.Axis(values=[1, 2, 3, 4, 5])),
                              color=alt.Color("項目:N", scale=COLOR, legend=alt.Legend(orient="top", title=None)),
                              tooltip=["週:N", "項目:N", "点数:Q"])
    st.altair_chart((pc.mark_line(strokeWidth=2) + pc.mark_point(filled=True, size=60)).properties(height=200), width="stretch")
    hist = mine.sort_values("at", ascending=False)
    show = pd.DataFrame({"配信週": hist["week"], "報告": hist["r"], "連絡": hist["c"], "相談": hist["s"], "合計": hist["total"]})
    for col, lab in free:
        show[lab] = hist[col].values
    st.dataframe(show, hide_index=True, width="stretch")

# ---- 自由記述 ----
with st.container(border=True):
    st.subheader("自由記述")
    if not free:
        st.caption("自由記述の設問が見つかりません。")
    cols = st.columns(max(1, len(free)))
    for (col, lab), box in zip(free, cols):
        with box:
            items = rows[rows[col].fillna("") != ""].sort_values("at", ascending=False) if col in rows else rows.iloc[0:0]
            st.markdown(f"**{lab}**　:gray[{len(items)}件]")
            if items.empty:
                st.caption("記入はありません。")
            for _, r in items.iterrows():
                st.caption(f"{r['name']}・{r['dept']}" + ("" if unit == "week" else f"・{sv.label(r['week'], 'week')}"))
                st.text(r[col])
                st.divider()
