import textwrap
from plotly.subplots import make_subplots
import math
import plotly.graph_objects as go
from urllib.parse import quote
from utils.charts import CARD_BG, make_chart_pretty, render_chart_card, HOVER_BG
import streamlit as st
import pandas as pd
from utils.metrics import calculate_teacher_retention_metrics
import plotly.express as px
from utils.charts import (
    style_figure,
    beautify_pie_chart,
    beautify_bar_chart,
    fix_pie,
    show_chart,
)
from utils.preprocess import preprocess_teacher, split_national_and_school, normalize_school_col, classify

COLOR_PRIMARY = "#3B5998"
COLOR_SECOND = "#7BCFA6"
COLOR_WARN = "#FF9900"
COLOR_DANGER = "#B36D61"
COLOR_NEUTRAL = "#7F8EA3"

TEXT_COLOR = "#EAF1FF"
SUB_TEXT_COLOR = "#A9B8D4"
# 页面状态初始化

def render_rank_card(
    df: pd.DataFrame,
    name_col: str,
    value_col: str,
    title: str,
    value_suffix: str = "",
    sub_col: str = None,
    sub_fmt: str = None,
    sort_ascending: bool = False,
    top_n: int = 10,
    key_prefix: str = "rank_card",
    height: int = None
):
    st.markdown(f"#### {title}")

    if df.empty or name_col not in df.columns or value_col not in df.columns:
        st.info("暂无可展示数据。")
        return

    show_df = df[[name_col, value_col] + ([sub_col] if sub_col and sub_col in df.columns else [])].copy()
    show_df[value_col] = pd.to_numeric(show_df[value_col], errors="coerce")
    show_df = show_df.dropna(subset=[name_col, value_col])

    if show_df.empty:
        st.info("暂无可展示数据。")
        return

    show_df = show_df.sort_values(value_col, ascending=sort_ascending).head(top_n).reset_index(drop=True)

    rank_colors = ["#F59E0B", "#9CA3AF", "#CD7C3A"]

    rows_html = ""
    for i, row in show_df.iterrows():
        rank = i + 1
        badge_bg = rank_colors[rank - 1] if rank <= 3 else "#374151"
        divider = "" if i == len(show_df) - 1 else "border-bottom: 1px solid rgba(255,255,255,0.07);"

        main_val = row[value_col]
        if pd.isna(main_val):
            main_text = "-"
        else:
            if value_suffix == "%":
                main_text = f"{main_val:.1f}%"
            else:
                main_text = f"{int(main_val):,}" if float(main_val).is_integer() else f"{main_val:,.1f}"

        sub_text = ""
        if sub_col and sub_col in show_df.columns:
            sub_val = row[sub_col]
            if pd.notna(sub_val):
                if sub_fmt == "%":
                    sub_text = f"{sub_col}：{sub_val:.1f}%"
                else:
                    sub_text = f"{sub_col}：{sub_val:,.0f}"

        rows_html += f"""<div class="rank-board-row" style="display:flex;align-items:center;justify-content:space-between;padding:8px 10px;{divider}">
<div style="display:flex;align-items:center;gap:10px;min-width:0;flex:1.8;">
<div style="width:26px;height:26px;border-radius:7px;background:{badge_bg};color:white;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">{rank}</div>
<div style="min-width:0;">
<div style="font-size:14px;font-weight:600;color:white;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{row[name_col]}</div>
<div style="font-size:10px;color:#8FA3BF;margin-top:1px;line-height:1.2;">{sub_text}</div>
</div>
</div>
<div style="text-align:right;flex:1;">
<div style="font-size:15px;font-weight:700;color:#7BCFA6;line-height:1.2;">{main_text}</div>
</div>
</div>"""

    height_style = f"height:{height}px;" if height else ""

    full_html = f"""<div class="rank-board-card" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:16px 20px;{height_style}overflow:auto;">{rows_html}
</div>"""
    st.markdown(full_html, unsafe_allow_html=True)

def build_school_entry_df(school_cur_df: pd.DataFrame) -> pd.DataFrame:
    df = school_cur_df.copy()

    use_cols = ["学校", "参与率", "参与后完成率", "任务总数"]
    for col in use_cols:
        if col not in df.columns:
            df[col] = None

    df = df[use_cols].copy()
    df["参与率"] = pd.to_numeric(df["参与率"], errors="coerce")
    df["参与后完成率"] = pd.to_numeric(df["参与后完成率"], errors="coerce")
    df["任务总数"] = pd.to_numeric(df["任务总数"], errors="coerce")

    df = df.dropna(subset=["学校", "参与率", "参与后完成率"]).copy()

    if df.empty:
        return df

    x_mid = df["参与率"].median()
    y_mid = df["参与后完成率"].median()

    def get_quadrant(row):
        x = row["参与率"]
        y = row["参与后完成率"]
        if x >= x_mid and y >= y_mid:
            return "高参与·高完成"
        elif x >= x_mid and y < y_mid:
            return "高参与·低完成"
        elif x < x_mid and y >= y_mid:
            return "低参与·高完成"
        else:
            return "低参与·低完成"

    def get_rate_level(rate):
        if pd.isna(rate):
            return "缺失"
        elif rate >= 50:
            return "≥50%"
        elif rate >= 30:
            return "30-49%"
        elif rate >= 10:
            return "10-29%"
        else:
            return "<10%"

    df["分组"] = df.apply(get_quadrant, axis=1)
    df["参与率档位"] = df["参与率"].apply(get_rate_level)

    group_order = ["高参与·高完成", "高参与·低完成", "低参与·高完成", "低参与·低完成"]
    df["分组"] = pd.Categorical(df["分组"], categories=group_order, ordered=True)

    df = df.sort_values(
        ["分组", "参与率", "参与后完成率", "任务总数"],
        ascending=[True, False, False, False]
    ).reset_index(drop=True)

    return df

def render_school_entry_wall(df: pd.DataFrame):

    st.markdown("### 🗺️ 学校入口总览（点击查看详情）")

    if df is None or df.empty:
        st.info("暂无学校数据")
        return

    if "school_search_keyword" not in st.session_state:
        st.session_state.school_search_keyword = ""

    group_order = ["高参与·高完成", "高参与·低完成", "低参与·高完成", "低参与·低完成"]

    group_title_map = {
        "高参与·高完成": '<span style="color:#7BCFA6;">高参与·高完成</span>',
        "高参与·低完成": '<span style="color:#78A8E0;">高参与·低完成</span>',
        "低参与·高完成": '<span style="color:#F2A541;">低参与·高完成</span>',
        "低参与·低完成": '<span style="color:#D99A86;">低参与·低完成</span>',
    }

    st.markdown("""
<style>
div[data-testid="stButton"] > button {
    padding: 4px 8px !important;
    font-size: 12px !important;
    border-radius: 8px !important;
    min-height: 34px !important;
    height: 34px !important;
    line-height: 1.1 !important;
}

div[data-testid="stButton"] > button[kind="secondary"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    color: #EAF1FF !important;
}

div[data-testid="stButton"] > button[kind="secondary"]:hover {
    border: 1px solid rgba(255,255,255,0.28) !important;
    background: rgba(255,255,255,0.05) !important;
}

div[data-testid="stButton"] > button[kind="primary"] {
    background: rgba(76,120,168,0.26) !important;
    border: 1px solid #78A8E0 !important;
    color: #EAF1FF !important;
    box-shadow: 0 0 0 1px rgba(120,168,224,0.18) inset !important;
}

.school-top-card {
    padding: 10px 14px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.03);
    margin-bottom: 12px;
}

.school-top-title {
    font-size: 13px;
    color: #8FA3BF;
    margin-bottom: 4px;
}

.school-top-name {
    font-size: 20px;
    font-weight: 700;
    color: #EAF1FF;
    margin-bottom: 4px;
}

.school-top-meta {
    font-size: 12px;
    color: #A9B8D4;
}
</style>
""", unsafe_allow_html=True)

    df = df.copy()
    if "参与率" in df.columns:
        df["参与率"] = pd.to_numeric(df["参与率"], errors="coerce")
    if "参与后完成率" in df.columns:
        df["参与后完成率"] = pd.to_numeric(df["参与后完成率"], errors="coerce")
    if "任务总数" in df.columns:
        df["任务总数"] = pd.to_numeric(df["任务总数"], errors="coerce")

    selected_school = st.session_state.get("selected_school")

    # ===== 学校分组按钮墙 =====
    for group in group_order:
        sub = df[df["分组"] == group].copy()
        if sub.empty:
            continue

        sub = sub.sort_values(
            by=["参与率", "参与后完成率", "任务总数"],
            ascending=[False, False, False]
        ).reset_index(drop=True)

        st.markdown(f"#### {group_title_map[group]}", unsafe_allow_html=True)

        cols_per_row = 10
        school_rows = [sub.iloc[i:i + cols_per_row] for i in range(0, len(sub), cols_per_row)]

        for row_df in school_rows:
            cols = st.columns(cols_per_row)

            for idx, (_, row) in enumerate(row_df.iterrows()):
                school = str(row.get("学校", "-"))

                rate = pd.to_numeric(row.get("参与率"), errors="coerce")
                finish = pd.to_numeric(row.get("参与后完成率"), errors="coerce")
                task_cnt = pd.to_numeric(row.get("任务总数"), errors="coerce")

                rate = 0.0 if pd.isna(rate) else rate
                finish = 0.0 if pd.isna(finish) else finish
                task_cnt = 0 if pd.isna(task_cnt) else int(task_cnt)

                help_text = (
                    f"学校：{school}\n"
                    f"参与率：{rate:.1f}%\n"
                    f"完成率：{finish:.1f}%\n"
                    f"任务数：{task_cnt}\n"
                    f"分组：{group}"
                )

                btn_type = "primary" if school == selected_school else "secondary"

                with cols[idx]:
                    if st.button(
                        school,
                        key=f"school_btn_{group}_{school}",
                        help=help_text,
                        use_container_width=True,
                        type=btn_type
                    ):
                        st.session_state.selected_school = school
                        st.session_state.top_nav_mode = "school"
                        st.rerun()

        st.markdown("")

def render_detail_analysis(
    school_cur: pd.DataFrame,
    school_last: pd.DataFrame,
    teacher_cur: pd.DataFrame,
    teacher_last: pd.DataFrame,
    df_task_30d: pd.DataFrame = None
):
    # ========= 先做空数据/缺字段保护 =========
    if school_cur is None or school_cur.empty:
        st.info("当前分析窗口内暂无学校数据。")
        return

    if "学校" not in school_cur.columns:
        st.info("当前学校数据缺少【学校】字段，暂时无法展示学校/老师关联分析。")
        return
    # ========= 预处理 =========
    _, school_cur_df = split_national_and_school(school_cur)
    _, school_last_df = split_national_and_school(school_last)

    teacher_cur = preprocess_teacher(teacher_cur)
    teacher_last = preprocess_teacher(teacher_last)

    teacher_cur = normalize_school_col(teacher_cur)
    teacher_last = normalize_school_col(teacher_last)

    # ========= 学校入口 =========
    entry_df = build_school_entry_df(school_cur_df)
    render_school_entry_wall(entry_df)
    st.markdown("""
    <hr style="
        height:1px;
        border:none;
        background-color:#EAF1FF;
        margin:0 0;
    ">
    """, unsafe_allow_html=True)
    # =========================================================
    # 一、学校层分析
    # =========================================================
    st.markdown("### 🏫 学校层分析")
    school_left, school_right = st.columns([1, 1.2], gap="large")

    with school_left:
        st.markdown(
            """<div style="display:flex;flex-direction:column;justify-content:flex-start;;display:flex;flex-direction:column;justify-content:space-between;">""",
            unsafe_allow_html=True)

        active_teacher_df = (
            teacher_cur[teacher_cur["发布任务总数"] > 0]
            .groupby("学校")["老师姓名"]
            .nunique()
            .reset_index()
        )
        active_teacher_df.columns = ["学校", "活跃老师数"]

        teacher_count_col = "老师数量" if "老师数量" in school_cur_df.columns else "教师数量"

        school_teacher_df = school_cur_df[["学校", teacher_count_col]].copy()
        school_teacher_df = pd.merge(school_teacher_df, active_teacher_df, on="学校", how="left")
        school_teacher_df["活跃老师数"] = school_teacher_df["活跃老师数"].fillna(0)
        school_teacher_df["教师活跃率"] = (
                school_teacher_df["活跃老师数"] / school_teacher_df[teacher_count_col] * 100
        ).fillna(0)
        rank_mode = st.radio(
            "学校榜单视角",
            ["参与率TOP10", "任务规模TOP10", "教师活跃率TOP10"],
            horizontal=True,
            key="school_rank_mode"
        )

        if rank_mode == "参与率TOP10":
            render_rank_card(
                school_cur_df,
                name_col="学校",
                value_col="参与率",
                title="学校参与率 TOP10",
                value_suffix="%",
                sub_col="任务总数" if "任务总数" in school_cur_df.columns else None,
                sub_fmt=None,
                sort_ascending=False,
                top_n=10,
                key_prefix="school_participation"
            )
        elif rank_mode == "任务规模TOP10":
            render_rank_card(
                school_cur_df,
                name_col="学校",
                value_col="任务总数",
                title="学校任务规模 TOP10",
                value_suffix="",
                sub_col="参与率" if "参与率" in school_cur_df.columns else None,
                sub_fmt="%",
                sort_ascending=False,
                top_n=10,
                key_prefix="school_task"
            )
        else:
            render_rank_card(
                school_teacher_df,
                name_col="学校",
                value_col="教师活跃率",
                title="学校教师活跃率 TOP10",
                value_suffix="%",
                sub_col="活跃老师数",
                sub_fmt=None,
                sort_ascending=False,
                top_n=10,
                key_prefix="school_teacher_active"
            )

        st.markdown("""</div>""", unsafe_allow_html=True)

    with school_right:
        st.markdown("""<div style="display:flex;flex-direction:column;justify-content:flex-start;;display:flex;flex-direction:column;justify-content:flex-start;">""",
                    unsafe_allow_html=True)

        st.markdown("#### 学校参与率 × 完成率象限分布")

        scatter_df = school_cur_df[["学校", "参与率", "参与后完成率", "任务总数"]].copy()
        scatter_df["参与率"] = pd.to_numeric(scatter_df["参与率"], errors="coerce")
        scatter_df["参与后完成率"] = pd.to_numeric(scatter_df["参与后完成率"], errors="coerce")
        scatter_df["任务总数"] = pd.to_numeric(scatter_df["任务总数"], errors="coerce")
        scatter_df = scatter_df.dropna(subset=["学校", "参与率", "参与后完成率"]).copy()

        x_mid = scatter_df["参与率"].median()
        y_mid = scatter_df["参与后完成率"].median()

        def get_quadrant(x, y, x_mid, y_mid):
            if x >= x_mid and y >= y_mid:
                return "高参与·高完成"
            elif x >= x_mid and y < y_mid:
                return "高参与·低完成"
            elif x < x_mid and y >= y_mid:
                return "低参与·高完成"
            else:
                return "低参与·低完成"

        scatter_df["象限"] = scatter_df.apply(
            lambda r: get_quadrant(r["参与率"], r["参与后完成率"], x_mid, y_mid),
            axis=1
        )

        quad_summary = scatter_df["象限"].value_counts().reindex(
            ["高参与·高完成", "高参与·低完成", "低参与·高完成", "低参与·低完成"],
            fill_value=0
        )

        st.markdown(f"""<div class="custom-analytic-card" style="margin:6px 0 14px 0;padding:10px 14px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:12px;font-size:13px;line-height:1.7;color:#EAF1FF;">当前学校分布中，<span style="color:#7BCFA6;font-weight:700;">高参与·高完成</span>学校
    <span style="font-weight:700;">{quad_summary['高参与·高完成']}</span>所，
    <span style="color:#4C78A8;font-weight:700;">高参与·低完成</span>学校
    <span style="font-weight:700;">{quad_summary['高参与·低完成']}</span>所，
    <span style="color:#F2A541;font-weight:700;">低参与·高完成</span>学校
    <span style="font-weight:700;">{quad_summary['低参与·高完成']}</span>所，
    <span style="color:#C97A63;font-weight:700;">低参与·低完成</span>学校
    <span style="font-weight:700;">{quad_summary['低参与·低完成']}</span>所。整体看，优先关注“高参与但低完成”和“低参与低完成”学校的转化优化空间。
    </div>""", unsafe_allow_html=True)

        quadrant_order = ["高参与·高完成", "高参与·低完成", "低参与·高完成", "低参与·低完成"]
        subplot_map = {
            "高参与·高完成": (1, 1),
            "高参与·低完成": (1, 2),
            "低参与·高完成": (2, 1),
            "低参与·低完成": (2, 2),
        }
        quadrant_color_map = {
            "高参与·高完成": "#7BCFA6",
            "高参与·低完成": "#4C78A8",
            "低参与·高完成": "#F2A541",
            "低参与·低完成": "#C97A63",
        }
        quadrant_title_map = {
            "高参与·高完成": "高参与 · 高完成",
            "高参与·低完成": "高参与 · 低完成",
            "低参与·高完成": "低参与 · 高完成",
            "低参与·低完成": "低参与 · 低完成",
        }

        TOP_N = 12
        top_idx = scatter_df.nlargest(min(TOP_N, len(scatter_df)), "任务总数").index
        scatter_df["show_label"] = scatter_df.index.isin(top_idx)
        scatter_df["label_text"] = scatter_df["学校"].where(scatter_df["show_label"], "")

        task_vals = scatter_df["任务总数"].fillna(0)
        if task_vals.nunique() <= 1:
            scatter_df["bubble_size"] = 18
        else:
            norm = (task_vals - task_vals.min()) / (task_vals.max() - task_vals.min())
            scatter_df["bubble_size"] = 12 + norm.pow(0.6) * 16

        fig_b = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=[
                quadrant_title_map["高参与·高完成"],
                quadrant_title_map["高参与·低完成"],
                quadrant_title_map["低参与·高完成"],
                quadrant_title_map["低参与·低完成"],
            ],
            horizontal_spacing=0.06,
            vertical_spacing=0.12
        )

        panel_bg = {
            (1, 1): "rgba(123,207,166,0.05)",
            (1, 2): "rgba(76,120,168,0.05)",
            (2, 1): "rgba(242,165,65,0.05)",
            (2, 2): "rgba(201,122,99,0.05)",
        }

        fig_b.add_shape(type="rect", x0=0.00, x1=0.47, y0=0.56, y1=1.00, xref="paper", yref="paper",
                        line=dict(width=0), fillcolor=panel_bg[(1, 1)], layer="below")
        fig_b.add_shape(type="rect", x0=0.53, x1=1.00, y0=0.56, y1=1.00, xref="paper", yref="paper",
                        line=dict(width=0), fillcolor=panel_bg[(1, 2)], layer="below")
        fig_b.add_shape(type="rect", x0=0.00, x1=0.47, y0=0.00, y1=0.44, xref="paper", yref="paper",
                        line=dict(width=0), fillcolor=panel_bg[(2, 1)], layer="below")
        fig_b.add_shape(type="rect", x0=0.53, x1=1.00, y0=0.00, y1=0.44, xref="paper", yref="paper",
                        line=dict(width=0), fillcolor=panel_bg[(2, 2)], layer="below")

        for quad in quadrant_order:
            sub_df = scatter_df[scatter_df["象限"] == quad].copy()
            row, col = subplot_map[quad]

            if sub_df.empty:
                continue

            sub_df = sub_df.sort_values(
                by=["show_label", "任务总数", "参与率", "参与后完成率"],
                ascending=[False, False, False, False]
            ).reset_index(drop=True)

            n = len(sub_df)
            if n <= 4:
                n_cols = 2
            elif n <= 9:
                n_cols = 3
            elif n <= 16:
                n_cols = 4
            else:
                n_cols = 5

            n_rows = math.ceil(n / n_cols)
            xs, ys, text_pos = [], [], []

            for i in range(n):
                r = i // n_cols
                c = i % n_cols
                x = (c + 1) / (n_cols + 1)
                y = 1 - (r + 1) / (n_rows + 1)
                xs.append(x)
                ys.append(y)

                if c == 0:
                    pos = "middle right"
                elif c == n_cols - 1:
                    pos = "middle left"
                elif r % 2 == 0:
                    pos = "top center"
                else:
                    pos = "bottom center"
                text_pos.append(pos)

            sub_df["panel_x"] = xs
            sub_df["panel_y"] = ys
            sub_df["text_pos"] = text_pos

            df_plain = sub_df[~sub_df["show_label"]].copy()
            if not df_plain.empty:
                fig_b.add_trace(
                    go.Scatter(
                        x=df_plain["panel_x"],
                        y=df_plain["panel_y"],
                        mode="markers",
                        marker=dict(
                            size=df_plain["bubble_size"],
                            color=quadrant_color_map[quad],
                            opacity=0.72,
                            line=dict(width=1, color="rgba(255,255,255,0.25)")
                        ),
                        customdata=df_plain[["学校", "参与率", "参与后完成率", "任务总数", "象限"]].values,
                        hovertemplate=(
                            "<b>%{customdata[0]}</b><br>"
                            "参与率：%{customdata[1]:.1f}%<br>"
                            "参与后完成率：%{customdata[2]:.1f}%<br>"
                            "任务总数：%{customdata[3]:,.0f}<br>"
                            "象限：%{customdata[4]}<extra></extra>"
                        ),
                        showlegend=False
                    ),
                    row=row, col=col
                )

            df_label = sub_df[sub_df["show_label"]].copy()
            if not df_label.empty:
                fig_b.add_trace(
                    go.Scatter(
                        x=df_label["panel_x"],
                        y=df_label["panel_y"],
                        mode="markers+text",
                        text=df_label["label_text"],
                        textposition=df_label["text_pos"],
                        textfont=dict(size=10, color=TEXT_COLOR),
                        marker=dict(
                            size=df_label["bubble_size"] + 2,
                            color=quadrant_color_map[quad],
                            opacity=0.90,
                            line=dict(width=1.2, color="rgba(255,255,255,0.40)")
                        ),
                        customdata=df_label[["学校", "参与率", "参与后完成率", "任务总数", "象限"]].values,
                        hovertemplate=(
                            "<b>%{customdata[0]}</b><br>"
                            "参与率：%{customdata[1]:.1f}%<br>"
                            "参与后完成率：%{customdata[2]:.1f}%<br>"
                            "任务总数：%{customdata[3]:,.0f}<br>"
                            "象限：%{customdata[4]}<extra></extra>"
                        ),
                        showlegend=False
                    ),
                    row=row, col=col
                )

        for r in [1, 2]:
            for c in [1, 2]:
                fig_b.update_xaxes(row=r, col=c, showgrid=False, zeroline=False, showticklabels=False,
                                   ticks="", range=[0, 1], fixedrange=True, visible=False)
                fig_b.update_yaxes(row=r, col=c, showgrid=False, zeroline=False, showticklabels=False,
                                   ticks="", range=[0, 1], fixedrange=True, visible=False)

        for quad in quadrant_order:
            sub_df = scatter_df[scatter_df["象限"] == quad]
            row, col = subplot_map[quad]
            idx = (row - 1) * 2 + col
            xref = "x domain" if idx == 1 else f"x{idx} domain"
            yref = "y domain" if idx == 1 else f"y{idx} domain"

            fig_b.add_annotation(
                x=0.98, y=0.97, xref=xref, yref=yref,
                text=f"{len(sub_df)} 所学校",
                showarrow=False, xanchor="right", yanchor="top",
                font=dict(size=11, color=SUB_TEXT_COLOR)
            )

        for anno in fig_b.layout.annotations:
            if "所学校" not in str(anno.text):
                anno.font = dict(size=14, color=TEXT_COLOR)

        fig_b.update_layout(
            height=500,
            plot_bgcolor=CARD_BG,
            paper_bgcolor=CARD_BG,
            font=dict(color=TEXT_COLOR),
            margin=dict(l=20, r=20, t=45, b=20),
            hoverlabel=dict(bgcolor="rgba(15,23,42,0.96)", font=dict(color="white", size=10))
        )

        st.caption(
            f"象限划分口径：参与率中位数 {x_mid:.1f}%｜参与后完成率中位数 {y_mid:.1f}%｜仅展示任务总数 Top {min(TOP_N, len(scatter_df))} 学校名称"
        )
        st.plotly_chart(fig_b, use_container_width=True)

        st.markdown("""</div>""", unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================
    # =========================================================
    # 二、老师层分析
    # =========================================================

    if "科目" in teacher_cur.columns and "学校" in teacher_cur.columns:
        subject_df = teacher_cur.copy().dropna(subset=["科目"])

        left_col, right_col = st.columns(2, gap="large")

        # =========================
        # 左：总体分科目转化率排行
        # =========================
        school_cur_part = school_cur_df[["学校", "参与率", "参与后完成率"]].copy().rename(columns={
            "参与率": "本周参与率",
            "参与后完成率": "本周参与后完成率"
        })
        school_last_part = school_last_df[["学校", "参与率", "参与后完成率"]].copy().rename(columns={
            "参与率": "上周参与率",
            "参与后完成率": "上周参与后完成率"
        })

        for col in ["本周参与率", "本周参与后完成率"]:
            school_cur_part[col] = pd.to_numeric(school_cur_part[col], errors="coerce")

        for col in ["上周参与率", "上周参与后完成率"]:
            school_last_part[col] = pd.to_numeric(school_last_part[col], errors="coerce")

        school_change = pd.merge(school_cur_part, school_last_part, on="学校", how="inner")

        school_change["参与率变化"] = school_change["本周参与率"] - school_change["上周参与率"]
        school_change["参与后完成率变化"] = (
                school_change["本周参与后完成率"] - school_change["上周参与后完成率"]
        )

        with left_col:
            st.markdown("#### 分科目转化率排行（下滑看完整数据）")

            summary = (
                subject_df.groupby("科目", as_index=False)[
                    ["接收任务学生数", "打开任务学生数", "完成任务学生数"]
                ]
                .sum()
            )

            if summary.empty:
                st.info("当前没有可用于分析的科目数据。")
            else:
                summary["参与率"] = summary.apply(
                    lambda x: x["打开任务学生数"] / x["接收任务学生数"] * 100
                    if x["接收任务学生数"] else 0, axis=1
                )
                summary["参与后完成率"] = summary.apply(
                    lambda x: x["完成任务学生数"] / x["打开任务学生数"] * 100
                    if x["打开任务学生数"] else 0, axis=1
                )

                sort_by_left = st.radio(
                    "总体排序方式",
                    ["参与后完成率", "参与率"],
                    horizontal=True,
                    key="subject_rank_total"
                )

                summary = summary.sort_values(sort_by_left, ascending=False).reset_index(drop=True)

                rank_colors = ["#F59E0B", "#9CA3AF", "#CD7C3A"]

                rows_html = ""
                for i, row in summary.iterrows():
                    rate1 = row["参与率"]
                    rate2 = row["参与后完成率"]
                    rank = i + 1
                    badge_bg = rank_colors[rank - 1] if rank <= 3 else "#374151"
                    divider = "" if i == len(summary) - 1 else "border-bottom: 1px solid rgba(255,255,255,0.06);"

                    rows_html += f"""
<div class="rank-board-row" style="display:flex;align-items:center;padding:8px 10px;{divider}">
<div style="display:flex;align-items:center;gap:10px;flex:2;">
<div style="width:26px;height:26px;border-radius:7px;background:{badge_bg};color:white;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">{rank}</div>
<div style="font-size:14px;font-weight:600;color:white;line-height:1.2;">{row['科目']}</div>
</div>
<div style="flex:1;text-align:center;">
<div style="font-size:14px;font-weight:700;color:#60A5FA;line-height:1.2;">{rate1:.1f}%</div>
<div style="font-size:10px;color:#8FA3BF;margin-top:1px;">参与率</div>
</div>
<div style="flex:1;text-align:center;">
<div style="font-size:14px;font-weight:700;color:#34D399;line-height:1.2;">{rate2:.1f}%</div>
<div style="font-size:10px;color:#8FA3BF;margin-top:1px;">参与后完成率</div>
</div>
</div>
"""

                full_html = f"""
<div class="rank-board-card" style="
background:rgba(255,255,255,0.03);
border:1px solid rgba(255,255,255,0.08);
border-radius:14px;
padding:10px 14px;
height:325px;
overflow:auto;
">
                    {rows_html}
</div>
"""
                st.markdown(full_html, unsafe_allow_html=True)

        # =========================
        # 右侧：参与率 / 参与后完成率 切换
        # =========================
        with right_col:

            # ===== 切换按钮 =====
            if "rate_switch" not in st.session_state:
                st.session_state.rate_switch = "参与率"

            btn1, btn2 = st.columns(2)

            with btn1:
                if st.button(
                        "参与率变化",
                        use_container_width=True,
                        type="primary" if st.session_state.rate_switch == "参与率" else "secondary"
                ):
                    st.session_state.rate_switch = "参与率"
                    # 删掉 st.rerun()

            with btn2:
                if st.button(
                        "参与后完成率变化",
                        use_container_width=True,
                        type="primary" if st.session_state.rate_switch == "参与后完成率" else "secondary"
                ):
                    st.session_state.rate_switch = "参与后完成率"
                    # 删掉 st.rerun()

            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

            # =========================
            # 根据选择切换数据
            # =========================
            if st.session_state.rate_switch == "参与率":
                metric_col = "参与率变化"
                title = "参与率变化（按学校）Top/Bottom"
                text_fmt = "{:+.0f}%"
            else:
                metric_col = "参与后完成率变化"
                title = "参与后完成率变化（按学校）Top/Bottom"
                text_fmt = "{:+.1f}%"

            st.markdown(f"#### {title}")

            # =========================
            # 数据处理
            # =========================
            top_up = school_change.sort_values(metric_col, ascending=False).head(5)
            top_down = school_change.sort_values(metric_col, ascending=True).head(5)

            change_df = pd.concat([top_down, top_up], ignore_index=True)
            change_df = change_df.drop_duplicates(subset=["学校"])
            change_df = change_df.sort_values(metric_col, ascending=True)

            if change_df.empty:
                st.info("当前没有可用于分析的学校变化数据。")
            else:
                raw_max = change_df[metric_col].abs().max()
                max_val = max(raw_max * 1.15, 10)

                fig_d = go.Figure()

                # ===== 背景轨道 =====
                fig_d.add_trace(go.Bar(
                    x=[max_val] * len(change_df),
                    y=change_df["学校"],
                    orientation="h",
                    marker=dict(color="rgba(255,255,255,0.06)", line_width=0),
                    showlegend=False,
                    hoverinfo="skip"
                ))

                fig_d.add_trace(go.Bar(
                    x=[-max_val] * len(change_df),
                    y=change_df["学校"],
                    orientation="h",
                    marker=dict(color="rgba(255,255,255,0.06)", line_width=0),
                    showlegend=False,
                    hoverinfo="skip"
                ))

                # ===== 实际数据 =====
                for _, row in change_df.iterrows():
                    val = row[metric_col]
                    color = COLOR_SECOND if val >= 0 else COLOR_DANGER

                    fig_d.add_trace(go.Bar(
                        x=[val],
                        y=[row["学校"]],
                        orientation="h",
                        marker=dict(color=color, line_width=0),
                        text=text_fmt.format(val),
                        textposition="inside",
                        textfont=dict(color="#FFFFFF", size=11),
                        showlegend=False,
                        hovertemplate=f"{row['学校']}: {text_fmt.format(val)}<extra></extra>"
                    ))

                # ===== 样式 =====
                fig_d.update_layout(
                    barmode="overlay",
                    bargap=0.32,
                    plot_bgcolor=CARD_BG,
                    paper_bgcolor=CARD_BG,
                    font=dict(color=TEXT_COLOR, size=11),
                    height=330,
                    margin=dict(l=26, r=26, t=8, b=20),
                    xaxis=dict(
                        range=[-max_val * 1.05, max_val * 1.05],
                        showgrid=False,
                        zeroline=True,
                        zerolinecolor="rgba(255,255,255,0.18)",
                        zerolinewidth=1.2,
                        tickfont=dict(color=SUB_TEXT_COLOR, size=11),
                        showline=False
                    ),
                    yaxis=dict(
                        showgrid=False,
                        tickfont=dict(color=TEXT_COLOR, size=11),
                        categoryorder="array",
                        categoryarray=change_df["学校"].tolist(),
                        automargin=True
                    ),
                    hoverlabel=dict(
                        bgcolor=HOVER_BG,
                        font_color=TEXT_COLOR,
                        bordercolor=HOVER_BG
                    )
                )

                try:
                    fig_d.update_layout(barcornerradius=999)
                except Exception:
                    pass

                render_chart_card(fig_d)

    #     with right_col:
    #         st.markdown("#### 校区分科目排行")
    #
    #         school_options = sorted(subject_df["学校"].dropna().unique().tolist())
    #         selected_school_subject = st.selectbox(
    #             "选择校区",
    #             school_options,
    #             key="subject_rank_school"
    #         )
    #
    #         school_subject_df = subject_df[subject_df["学校"] == selected_school_subject].copy()
    #
    #         school_summary = (
    #             school_subject_df.groupby("科目", as_index=False)[
    #                 ["接收任务学生数", "打开任务学生数", "完成任务学生数"]
    #             ]
    #             .sum()
    #         )
    #
    #         if school_summary.empty:
    #             st.info("当前校区没有可用于分析的科目数据。")
    #         else:
    #             school_summary["参与率"] = school_summary.apply(
    #                 lambda x: x["打开任务学生数"] / x["接收任务学生数"] * 100
    #                 if x["接收任务学生数"] else 0, axis=1
    #             )
    #             school_summary["参与后完成率"] = school_summary.apply(
    #                 lambda x: x["完成任务学生数"] / x["打开任务学生数"] * 100
    #                 if x["打开任务学生数"] else 0, axis=1
    #             )
    #
    #             sort_by_right = st.radio(
    #                 "校区排序方式",
    #                 ["参与后完成率", "参与率"],
    #                 horizontal=True,
    #                 key="subject_rank_school_sort"
    #             )
    #
    #             school_summary = school_summary.sort_values(sort_by_right, ascending=False).reset_index(drop=True)
    #
    #             rank_colors = ["#F59E0B", "#9CA3AF", "#CD7C3A"]
    #
    #             rows_html_school = ""
    #             for i, row in school_summary.iterrows():
    #                 rate1 = row["参与率"]
    #                 rate2 = row["参与后完成率"]
    #                 rank = i + 1
    #                 badge_bg = rank_colors[rank - 1] if rank <= 3 else "#374151"
    #                 divider = "" if i == len(school_summary) - 1 else "border-bottom: 1px solid rgba(255,255,255,0.06);"
    #
    #                 rows_html_school += f"""<div style="display:flex;align-items:center;padding:8px 1px;{divider}">
    #             <div style="display:flex;align-items:center;gap:10px;flex:1.5;">
    #             <div style="width:22px;height:22px;border-radius:6px;background:{badge_bg};color:white;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">{rank}</div>
    #             <div style="font-size:13px;font-weight:600;color:white;line-height:1.2;">{row['科目']}</div>
    #             </div>
    #             <div style="flex:0.7;text-align:center;">
    #             <div style="font-size:13px;font-weight:700;color:#60A5FA;line-height:1.2;">{rate1:.1f}%</div>
    #             <div style="font-size:9px;color:#8FA3BF;margin-top:1px;">参与率</div>
    #             </div>
    #             <div style="flex:0.7;text-align:center;">
    #             <div style="font-size:13px;font-weight:700;color:#34D399;line-height:1.2;">{rate2:.1f}%</div>
    #             <div style="font-size:9px;color:#8FA3BF;margin-top:1px;">参与后完成率</div>
    #             </div>
    #             </div>"""
    #
    #             full_html_school = f"""
    #             <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:10px 14px;height:270px;overflow:auto;">
    #                 {rows_html_school}
    #             </div>
    #             """
    #             st.markdown(full_html_school, unsafe_allow_html=True)
    #
    # else:
    #     st.info("老师数据中未检测到【学校】或【科目】字段，暂时无法展示分科目转化率排行。")
    #
    # st.markdown("---")

        st.markdown("""
    <hr style="
    height:0px;
    border:none;
    background-color:#EAF1FF;
    margin:0 0;
    ">
    """, unsafe_allow_html=True)
        # ========= 第三层：老师留存 + 渗透 =========
        st.markdown("### 🧑‍🏫老师层分析")

        # ===== 渗透率计算：近7天去重活跃老师 / 近30天去重老师池 =====
        def _teacher_key(df: pd.DataFrame) -> pd.Series:
            if df is None or df.empty:
                return pd.Series(dtype="object")

            if "老师邮箱" in df.columns and df["老师邮箱"].notna().any():
                return df["老师邮箱"].astype(str).str.strip().str.lower()

            if "老师姓名" in df.columns:
                return df["老师姓名"].astype(str).str.strip()

            return pd.Series(["未知老师"] * len(df), index=df.index)

        # 本周活跃老师（近7天）
        cur_active_teacher_cnt = 0
        if teacher_cur is not None and not teacher_cur.empty:
            teacher_cur_tmp = preprocess_teacher(teacher_cur.copy())
            if "发布任务总数" in teacher_cur_tmp.columns:
                teacher_cur_tmp = teacher_cur_tmp[teacher_cur_tmp["发布任务总数"] > 0].copy()
            cur_active_teacher_cnt = _teacher_key(teacher_cur_tmp).nunique()

        # 上周活跃老师（上一周7天）
        last_active_teacher_cnt = 0
        if teacher_last is not None and not teacher_last.empty:
            teacher_last_tmp = preprocess_teacher(teacher_last.copy())
            if "发布任务总数" in teacher_last_tmp.columns:
                teacher_last_tmp = teacher_last_tmp[teacher_last_tmp["发布任务总数"] > 0].copy()
            last_active_teacher_cnt = _teacher_key(teacher_last_tmp).nunique()

        # 近30天老师池
        teacher_pool_30d = 0
        if df_task_30d is not None and not df_task_30d.empty:
            task_30d_tmp = df_task_30d.copy()
            teacher_pool_30d = _teacher_key(task_30d_tmp).nunique()

        teacher_penetration_cur = (
            cur_active_teacher_cnt / teacher_pool_30d * 100 if teacher_pool_30d else 0
        )
        teacher_penetration_last = (
            last_active_teacher_cnt / teacher_pool_30d * 100 if teacher_pool_30d else 0
        )
        penetration_delta = teacher_penetration_cur - teacher_penetration_last
        retention_data = calculate_teacher_retention_metrics(teacher_cur, teacher_last)
        # ===== 留存数据 =====
        retain = retention_data["retained"]
        new = retention_data["new"]
        lost = retention_data["lost"]
        cur_active = retention_data["cur_active"]
        last_active = retention_data["last_active"]
        retention_rate = retention_data["retention_rate"]

        retain_ratio = retain / cur_active * 100 if cur_active else 0
        new_ratio = new / cur_active * 100 if cur_active else 0
        lost_ratio_last = lost / last_active * 100 if last_active else 0

        left_ret, right_ret = st.columns(2, gap="large")

        # ================= 左：留存率 =================
        with left_ret:
            st.markdown("#### 老师留存率")

            st.markdown(f"""
    <div class="custom-analytic-card" style="height: 400px;overflow: hidden;display: flex;flex-direction: column;justify-content: space-between;background:#1A2335;border: 1px solid rgba(255,255,255,0.08);border-left: 4px solid {COLOR_SECOND};border-radius: 18px;padding: 16px 18px;"><div>
    <div style="font-size:13px;color:#A9B8D4;font-weight:600;">老师留存率</div>
    <div style="font-size:24px;font-weight:800;color:#F8FAFC;line-height:1.15;margin-top:3px;">
    {retention_rate:.1f}%
    </div>
    <div style="font-size:12px;color:#7F8EA3;margin-top:3px;">
    上周活跃老师中，本周仍然活跃的比例
    </div>
    </div>
    
    <div>
    <div style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
    <div style="font-size:13px;color:#A9B8D4;">留存老师</div>
    <div style="font-size:24px;font-weight:800;color:{COLOR_SECOND};">{retain}</div>
    <div style="font-size:12px;color:#7F8EA3;">占本周活跃老师 {retain_ratio:.1f}%</div>
    </div>
    
    <div style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
    <div style="font-size:13px;color:#A9B8D4;">新增老师</div>
    <div style="font-size:24px;font-weight:800;color:{COLOR_PRIMARY};">{new}</div>
    <div style="font-size:12px;color:#7F8EA3;">占本周活跃老师 {new_ratio:.1f}%</div>
    </div>
    
    <div style="padding:8px 0 0 0;">
    <div style="font-size:13px;color:#A9B8D4;">流失老师</div>
    <div style="font-size:24px;font-weight:800;color:{COLOR_DANGER};">{lost}</div>
    <div style="font-size:12px;color:#7F8EA3;">占上周活跃老师 {lost_ratio_last:.1f}%</div>
    </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

        # ================= 右：渗透率 =================
        with right_ret:
            st.markdown("#### 老师渗透率")

            delta_color = "#4ADE80" if penetration_delta >= 0 else "#F87171"

            st.markdown(f"""
    <div class="custom-analytic-card" style="height: 400px;overflow: hidden;display: flex;flex-direction: column;justify-content: space-between;background: #1A2335;border: 1px solid rgba(255,255,255,0.08);border-left: 4px solid {COLOR_WARN};border-radius: 18px;padding: 16px 18px;"><div>
    <div style="font-size:13px;color:#A9B8D4;font-weight:600;">近7天老师渗透率</div>
    <div style="display:flex;align-items:baseline;gap:10px;margin-top:3px;">
    <div style="font-size:24px;font-weight:800;color:#F8FAFC;line-height:1.15;">
    {teacher_penetration_cur:.1f}%
    </div>
    <div style="font-size:13px;font-weight:700;color:{delta_color};">
    {penetration_delta:+.1f}%
    </div>
    </div>
    <div style="font-size:12px;color:#7F8EA3;margin-top:3px;">
    近7天活跃老师 / 近30天老师池
    </div>
    </div>
    
    <div style="background: linear-gradient(90deg, rgba(255,190,60,0.10) 0%, rgba(255,190,60,0.06) 100%);border: 1px solid rgba(246,185,59,0.32);border-radius: 14px;padding: 12px 14px;margin: 8px 0;">
    <div style="font-size:13px;color:#A9B8D4;">覆盖情况</div>
    <div style="display:flex;align-items:baseline;gap:8px;margin-top:3px;">
    <div style="font-size:24px;font-weight:800;color:#F6B93B;">{cur_active_teacher_cnt:,}</div>
    <div style="font-size:13px;color:#A9B8D4;">/ {teacher_pool_30d:,}</div>
    </div>
    <div style="font-size:12px;color:#7F8EA3;margin-top:2px;">近7天活跃老师数 / 近30天去重老师池</div>
    </div>
    
    <div>
    <div style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
    <div style="font-size:13px;color:#A9B8D4;">近7天活跃老师</div>
    <div style="font-size:24px;font-weight:800;color:{COLOR_WARN};">{cur_active_teacher_cnt:,}</div>
    </div>
    
    <div style="padding:8px 0;">
    <div style="font-size:13px;color:#A9B8D4;">上一周活跃老师</div>
    <div style="font-size:24px;font-weight:800;color:{COLOR_PRIMARY};">{last_active_teacher_cnt:,}</div>
    </div>
    
    </div>
    </div>
    """, unsafe_allow_html=True)

        # ================= 底部一句结论 =================
        if teacher_penetration_cur >= 60 and retention_rate >= 60:
            conclusion = "老师覆盖和连续活跃都较好，当前工具已具备较强的使用广度与稳定性。"
        elif teacher_penetration_cur >= 60 and retention_rate < 60:
            conclusion = "老师覆盖较高，但留存偏弱，说明推广已经铺开，后续更应关注持续使用体验。"
        elif teacher_penetration_cur < 60 and retention_rate >= 60:
            conclusion = "老师留存表现较稳，但整体覆盖仍有限，说明现有使用老师认可度较高，可继续扩大触达。"
        else:
            conclusion = "当前老师覆盖和连续活跃均有提升空间，建议同时关注推广触达与产品使用粘性。"

        st.markdown(
    f"""
    <div class="custom-analytic-card" style="margin-top:14px;background: rgba(255,255,255,0.03);border: 1px solid rgba(255,255,255,0.07);border-radius: 14px;padding: 12px 16px;color: #D7E3FF;font-size: 13px;line-height: 1.7;">
    <b style="color:#EAF1FF;">结论：</b>{conclusion}
    </div>
    """,
    unsafe_allow_html=True
        )
