import altair as alt
import pandas as pd
import streamlit as st

from horenso import data, survey as sv, ui

ui.page_header("報連相チェック", "毎週金曜に配信するセルフチェック（報告・連絡・相談 各5点）の集計です。", eyebrow="SURVEY")

res = data.survey_all()
if res is None:
    st.stop()
df, free, target, goal = res
if df.empty:
    st.info("回答がまだありません。フォームに回答が入ると、ここに集計が表示されます。")
    st.stop()

ITEMS = [(k, n) for k, n, _ in sv.ITEMS]
NAMES = [n for _, n in ITEMS]
COLOR = alt.Scale(domain=NAMES, range=[ui.ITEM_COLORS[n] for n in NAMES])

# ---- 期間の選択 ----
with st.container(border=True):
    c1, c2, c3 = st.columns([1.2, 2, 3], vertical_alignment="bottom")
    with c1:
        unit_label = st.segmented_control("集計単位", ["週ごと", "月ごと"], default="週ごと", required=True, key="unit")
    unit = "week" if unit_label == "週ごと" else "month"
    ps = sv.periods(df, unit)

    def period_name(p):
        if unit == "week":
            return p.replace("-", "/") + "（金）" + ("　最新" if p == ps[0] else "")
        return f"{sv.label(p, 'month')}（配信 {sv.rows_in(df, 'month', p)['week'].nunique()}回）" + ("　最新" if p == ps[0] else "")

    with c2:
        p = st.selectbox("配信週（金曜）" if unit == "week" else "月", ps, format_func=period_name, key="period_" + unit)
    with c3:
        st.caption(":material/lock: 委員会内での分析用です。本人への共有や評価には使用しません。")

pp = sv.prev_period(ps, p)
rows = sv.rows_in(df, unit, p)
cur, prev = sv.stats(rows), (sv.stats(sv.rows_in(df, unit, pp)) if pp else None)
word = "前週比" if unit == "week" else "前月比"
d0 = 0 if unit == "week" else 1

# ---- 数字のカード ----
rate = sv.rate_of(df, unit, p, target)
prate = sv.rate_of(df, unit, pp, target) if pp else None
k1, k2, k3, k4 = st.columns(4)
with k1:
    ui.kpi("回答者数" if unit == "week" else "回答した人（実人数）", f"{cur['people']}人" + (f" / {int(target)}" if target else ""),
           "" if unit == "week" else f"延べ {cur['n']}件",
           delta=(f"{cur['people'] - prev['people']:+d}人" if prev and unit == "week" else None))
with k2:
    ok = rate is not None and goal is not None and rate >= goal
    ui.kpi("回答率" if unit == "week" else "回答率（各週の平均）", f"{rate:.0%}" if rate is not None else "–",
           (f"目標{goal:.0%}達成" if ok else f"目標{goal:.0%}に未達") if (rate is not None and goal is not None) else "",
           "green" if ok else "orange", delta=(f"{(rate - prate) * 100:+.0f}pt" if rate is not None and prate is not None else None),
           help=None if target else "「分析」タブの対象人数が未設定です")
with k3:
    ui.kpi("合計平均（15点満点）", ui.fmt(cur["total"]), delta=(f"{cur['total'] - prev['total']:+.2f}" if prev else None))
with k4:
    w = sv.weakest(cur)
    ui.kpi("いちばん弱い項目", f"{w[0]} {w[1]:.2f}" if w else "なし", "次の施策のテーマ候補" if w else "全項目が満点", "blue" if w else "green")

tab1, tab2, tab3, tab4 = st.tabs([":material/bar_chart: 概要", ":material/show_chart: 推移", ":material/groups: 部署・個人", ":material/chat: 自由記述"])

# ---- 概要 ----
with tab1:
    a, b = st.columns(2, gap="medium")
    with a:
        with st.container(border=True):
            st.subheader("項目別の平均", anchor=False)
            st.caption(f"5点満点・{word}")
            avg = pd.DataFrame([{"項目": n, "平均": cur[k], "前": (prev[k] if prev else None)} for k, n in ITEMS])
            avg["表示"] = avg.apply(lambda r: f"{r['平均']:.2f}" + (f"（{r['平均'] - r['前']:+.2f}）" if pd.notna(r["前"]) else ""), axis=1)
            base = alt.Chart(avg).encode(y=alt.Y("項目:N", sort=NAMES, title=None, scale=alt.Scale(paddingInner=0.45)))
            bars = base.mark_bar(cornerRadiusEnd=4).encode(
                x=alt.X("平均:Q", scale=alt.Scale(domain=[0, 5]), axis=alt.Axis(values=[0, 1, 2, 3, 4, 5], title=None, grid=True)),
                color=alt.Color("項目:N", scale=COLOR, legend=None),
                tooltip=[alt.Tooltip("項目:N"), alt.Tooltip("平均:Q", format=".2f")])
            text = base.mark_text(align="left", dx=6, fontWeight=600, color=ui.GRAY).encode(x="平均:Q", text="表示:N")
            st.altair_chart((bars + text).properties(height=alt.Step(40)), width="stretch")
    with b:
        with st.container(border=True):
            st.subheader("点数の分布", anchor=False)
            st.caption("人数の割合" if unit == "week" else "延べ件数の割合（各週の回答の合計）")
            dist = [{"項目": n, "点数": lv, "点数名": f"{lv}点 {sv.LEVELS[lv]}", "件数": int((rows[k] == lv).sum())}
                    for k, n in ITEMS for lv in range(1, 6) if int((rows[k] == lv).sum())]
            chart = alt.Chart(pd.DataFrame(dist)).mark_bar().encode(
                y=alt.Y("項目:N", sort=NAMES, title=None, scale=alt.Scale(paddingInner=0.35)),
                x=alt.X("sum(件数):Q", stack="normalize", axis=alt.Axis(format="%", title=None)),
                color=alt.Color("点数名:N", scale=alt.Scale(domain=[f"{lv}点 {sv.LEVELS[lv]}" for lv in range(1, 6)],
                                                           range=[ui.LEVEL_COLORS[lv] for lv in range(1, 6)]),
                                legend=alt.Legend(orient="bottom", title=None, columns=3, labelLimit=160)),
                order=alt.Order("点数:Q"), tooltip=["項目:N", "点数名:N", "件数:Q"])
            st.altair_chart(chart.properties(height=alt.Step(40)), width="stretch")

    with st.container(border=True):
        st.subheader("声をかけたい人", anchor=False)
        st.caption("2点以下の項目がある／合計9点以下／前の期間から3点以上下がった人")
        fl = sv.follow_list(df, unit, p, ps)
        if fl.empty:
            st.success("この期間に該当する人はいません。", icon=":material/check_circle:")
        first_free = free[0][0] if free else None
        cols = st.columns(3)
        for i, (_, x) in enumerate(fl.iterrows()):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"**{x['name']}**　:gray[{x['dept']}]")
                    st.markdown(f":red[{x['why']}]")
                    st.caption(f"報告 {x['r']:.{d0}f}・連絡 {x['c']:.{d0}f}・相談 {x['s']:.{d0}f}（計 {x['total']:.{d0}f}）")
                    if first_free:
                        cm = [c for c in rows[rows["key"] == x["key"]].sort_values("at")[first_free] if c]
                        if cm:
                            st.caption("「" + cm[-1] + "」")

# ---- 推移 ----
with tab2:
    with st.container(border=True):
        st.subheader("報告・連絡・相談の平均", anchor=False)
        order = [sv.label(q, unit) for q in sorted(ps)]
        if len(ps) < 2:
            st.caption(f"2{'週' if unit == 'week' else 'か月'}分以上たまると、線で推移が見られます。")
        td = pd.DataFrame([{"期間": sv.label(q, unit), "項目": n, "平均": s[k], "件数": s["n"]}
                           for q in sorted(ps) for s in [sv.stats(sv.rows_in(df, unit, q))] for k, n in ITEMS])
        line = alt.Chart(td).encode(
            x=alt.X("期間:N", sort=order, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("平均:Q", scale=alt.Scale(domain=[1, 5]), title=None),
            color=alt.Color("項目:N", scale=COLOR, legend=alt.Legend(orient="top", title=None)),
            tooltip=["期間:N", "項目:N", alt.Tooltip("平均:Q", format=".2f"), "件数:Q"])
        st.altair_chart((line.mark_line(strokeWidth=2.5) + line.mark_point(filled=True, size=70)).properties(height=280), width="stretch")
    if target:
        with st.container(border=True):
            st.subheader("回答率", anchor=False)
            rd = pd.DataFrame([{"期間": sv.label(q, unit), "回答率": sv.rate_of(df, unit, q, target)} for q in sorted(ps)])
            rc = alt.Chart(rd).encode(x=alt.X("期間:N", sort=order, title=None, axis=alt.Axis(labelAngle=0)),
                                      y=alt.Y("回答率:Q", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format="%"), title=None),
                                      tooltip=["期間:N", alt.Tooltip("回答率:Q", format=".0%")])
            layers = rc.mark_area(color=ui.ACCENT, opacity=0.08) + rc.mark_line(color=ui.ACCENT, strokeWidth=2.5) + rc.mark_point(color=ui.ACCENT, filled=True, size=60)
            if goal is not None:
                layers += alt.Chart(pd.DataFrame({"目標": [goal]})).mark_rule(strokeDash=[4, 4], color=ui.GRAY).encode(y="目標:Q")
            st.altair_chart(layers.properties(height=160), width="stretch")
            if goal is not None:
                st.caption(f"点線は目標の {goal:.0%}")
    with st.expander("表で見る"):
        tbl = [{"期間": sv.label(q, unit), "回答者": s["people"], "回答率": sv.rate_of(df, unit, q, target),
                "報告": s["r"], "連絡": s["c"], "相談": s["s"], "合計": s["total"]}
               for q in sorted(ps, reverse=True) for s in [sv.stats(sv.rows_in(df, unit, q))]]
        st.dataframe(pd.DataFrame(tbl), hide_index=True, width="stretch", column_config={
            "回答率": st.column_config.NumberColumn(format="percent"),
            **{c: st.column_config.NumberColumn(format="%.2f") for c in ("報告", "連絡", "相談", "合計")}})

# ---- 部署・個人 ----
with tab3:
    with st.container(border=True):
        h1, h2 = st.columns([3, 2], vertical_alignment="center")
        h1.subheader("部署別の平均", anchor=False)
        with h2:
            scope = st.segmented_control("集計期間", ["選択した期間", "全期間"], default="選択した期間", required=True, key="dept_scope", label_visibility="collapsed")
        base_rows = rows if scope == "選択した期間" else df
        dept = (base_rows.groupby("dept").agg(人数=("key", "nunique"), 報告=("r", "mean"), 連絡=("c", "mean"), 相談=("s", "mean"), 合計=("total", "mean"))
                .reset_index().rename(columns={"dept": "部署"}).sort_values("合計"))
        st.dataframe(dept, hide_index=True, width="stretch", column_config={
            **{c: st.column_config.ProgressColumn(c, min_value=0, max_value=5, format="%.2f", color=ui.ITEM_COLORS[c]) for c in ("報告", "連絡", "相談")},
            "人数": st.column_config.NumberColumn(format="%d人", width="small"),
            "合計": st.column_config.NumberColumn(format="%.1f", width="small")})
        if (dept["人数"] < 3).any():
            st.caption("回答者が3人未満の部署は個人の点数に近いため、扱いに注意してください。")

    with st.container(border=True):
        st.subheader("個人別", anchor=False)
        st.caption(("月内の平均。" if unit == "month" else "") + "合計の低い順。行を選ぶと、下に個人の記録を表示します。")
        pe = sv.per_person(rows)
        prevp = sv.per_person(sv.rows_in(df, unit, pp)).set_index("key")["total"] if pp else pd.Series(dtype=float)
        pe["差"] = pe.apply(lambda x: x["total"] - prevp[x["key"]] if x["key"] in prevp.index else None, axis=1)
        pe["回答"] = pe["key"].map(df.groupby("key").size()) if unit == "week" else pe["n"]
        pe = pe.sort_values(["total", "name"]).reset_index(drop=True)
        fmt = "%d" if unit == "week" else "%.1f"
        low = lambda v: f"color: {ui.RED}; font-weight: 600" if isinstance(v, (int, float)) and v <= 2 else ""
        table = pe[["name", "dept", "r", "c", "s", "total", "差", "回答"]]
        sel = st.dataframe(
            table.style.map(low, subset=["r", "c", "s"]), hide_index=True, width="stretch",
            on_select="rerun", selection_mode="single-row", key="people_" + unit + p,
            column_config={"name": st.column_config.TextColumn("氏名", pinned=True), "dept": "部署",
                           "r": st.column_config.NumberColumn("報告", format=fmt), "c": st.column_config.NumberColumn("連絡", format=fmt),
                           "s": st.column_config.NumberColumn("相談", format=fmt), "total": st.column_config.NumberColumn("合計", format=fmt),
                           "差": st.column_config.NumberColumn(word, format="%+.1f"),
                           "回答": st.column_config.NumberColumn("累計回答" if unit == "week" else "この月の回答", format="%d回")})
        picked = sel.selection.rows if sel and sel.selection else []

    with st.container(border=True):
        st.subheader("個人の記録", anchor=False)
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
        m1, m2, m3 = st.columns(3)
        m1.metric("回答回数", f"{len(mine)}回", help=f"{sv.label(first['week'], 'week')}〜{sv.label(last['week'], 'week')}")
        m2.metric("最新の合計", f"{last['total']}点", delta=(f"{int(last['total'] - first['total']):+d}（初回比）" if len(mine) > 1 else None))
        lw = sv.weakest({"r": last["r"], "c": last["c"], "s": last["s"]})
        m3.metric("今の課題", lw[0] if lw else "なし")
        pl = mine.melt(id_vars=["week"], value_vars=[k for k, _ in ITEMS], var_name="k", value_name="点数")
        pl["項目"] = pl["k"].map(dict(ITEMS))
        pl["週"] = pl["week"].map(lambda w_: sv.label(w_, "week"))
        wk_order = [sv.label(w_, "week") for w_ in mine["week"]]
        pc = alt.Chart(pl).encode(x=alt.X("週:N", sort=wk_order, title=None, axis=alt.Axis(labelAngle=0)),
                                  y=alt.Y("点数:Q", scale=alt.Scale(domain=[1, 5]), axis=alt.Axis(values=[1, 2, 3, 4, 5]), title=None),
                                  color=alt.Color("項目:N", scale=COLOR, legend=alt.Legend(orient="top", title=None)),
                                  tooltip=["週:N", "項目:N", "点数:Q"])
        st.altair_chart((pc.mark_line(strokeWidth=2.5) + pc.mark_point(filled=True, size=70)).properties(height=220), width="stretch")
        hist = mine.sort_values("at", ascending=False)
        show = pd.DataFrame({"配信週": hist["week"], "報告": hist["r"], "連絡": hist["c"], "相談": hist["s"], "合計": hist["total"]})
        for col, lab in free:
            show[lab] = hist[col].values
        st.dataframe(show.style.map(low, subset=["報告", "連絡", "相談"]), hide_index=True, width="stretch")

# ---- 自由記述 ----
with tab4:
    if not free:
        st.caption("自由記述の設問が見つかりません。")
    cols = st.columns(max(1, len(free)), gap="medium")
    for (col, lab), box in zip(free, cols):
        with box:
            with st.container(border=True):
                items = rows[rows[col].fillna("") != ""].sort_values("at", ascending=False) if col in rows else rows.iloc[0:0]
                st.subheader(lab, anchor=False)
                st.caption(f"{len(items)}件")
                if items.empty:
                    st.caption("記入はありません。")
                for _, r in items.iterrows():
                    with st.container(border=True):
                        st.caption(f"{r['name']}・{r['dept']}" + ("" if unit == "week" else f"・{sv.label(r['week'], 'week')}"))
                        st.markdown(r[col].replace("\n", "  \n"))
