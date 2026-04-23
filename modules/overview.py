import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import textwrap
from utils.preprocess import preprocess, preprocess_teacher
from utils.charts import style_figure, CARD_BG, TEXT_COLOR, SUB_TEXT_COLOR, GRID_COLOR, render_chart_card
from utils.charts import show_chart
from utils.metrics import calculate_teacher_retention_metrics

COLOR_PRIMARY = "#3B5998"
COLOR_SECOND = "#7BCFA6"
COLOR_WARN = "#FF9900"
COLOR_DANGER = "#B36D61"
COLOR_NEUTRAL = "#7F8EA3"

CARD_HEIGHT = 360  # 四个卡片统一高度，改这一个数字即可


def metric_block(label, cur, last=None, is_percent=False, show_delta=True):
    cur = 0 if pd.isna(cur) else cur
    last = 0 if pd.isna(last) else last

    if not show_delta:
        if is_percent:
            st.metric(label, f"{cur:.1f}%")
        else:
            st.metric(label, f"{int(cur):,}")
        return

    delta = cur - last

    if is_percent:
        st.metric(label, f"{cur:.1f}%", f"{delta:+.1f}%")
    else:
        st.metric(label, f"{int(cur):,}", f"{int(delta):+}")


def to_num(val):
    if pd.isna(val):
        return 0
    return pd.to_numeric(str(val).replace("%", "").replace(",", ""), errors="coerce")


def _safe_pct(numerator, denominator):
    return numerator / denominator * 100 if denominator else 0


def _deep_card(title, subtitle, body_html, card_bg, height=None):
    """统一渲染深度分析卡片，固定高度，内容区滚动。"""
    h = height or CARD_HEIGHT
    s_outer = f"background:{card_bg};border:1px solid #E5EAF3;border-radius:16px;padding:16px 18px;height:{h}px;box-sizing:border-box;display:flex;flex-direction:column;overflow:hidden;"
    s_title = "font-size:15px;font-weight:700;color:#16324F;margin-bottom:6px;flex-shrink:0;"
    s_sub = "font-size:11px;color:#6B7A90;margin-bottom:12px;flex-shrink:0;"
    s_body = "flex:1;min-height:0;overflow-y:auto;padding-right:4px;"
    return (
        f'<div style="{s_outer}">'
        f'<div style="{s_title}">{title}</div>'
        f'<div style="{s_sub}">{subtitle}</div>'
        f'<div style="{s_body}">{body_html}</div>'
        '</div>'
    )


def render_ai_agent_panel(
    df_school_cur,
    df_school_last,
    school_count_cur,
    task_total_cur,
    task_total_last,
    active_teacher_cur,
    active_teacher_last,
    participation_cur,
    participation_last,
    completion_cur,
    completion_last,
    teacher_retention_cur,
    retention_data,
    df_teacher_cur=None,
    df_teacher_last=None,
    df_task_cur=None,
    df_task_last=None,
    df_task_30d=None,
):
    perspective_key = "overview_ai_summary_perspective"
    detail_key = "overview_ai_summary_show_detail"
    if perspective_key not in st.session_state:
        st.session_state[perspective_key] = "overall"
    if detail_key not in st.session_state:
        st.session_state[detail_key] = False

    receive_cur = open_cur = finish_cur = 0
    receive_last = open_last = finish_last = 0

    if df_task_cur is not None and not df_task_cur.empty:
        receive_cur = pd.to_numeric(df_task_cur.get("接收任务学生数", 0), errors="coerce").fillna(0).sum()
        open_cur = pd.to_numeric(df_task_cur.get("打开任务学生数", 0), errors="coerce").fillna(0).sum()
        finish_cur = pd.to_numeric(df_task_cur.get("完成任务学生数", 0), errors="coerce").fillna(0).sum()

    if df_task_last is not None and not df_task_last.empty:
        receive_last = pd.to_numeric(df_task_last.get("接收任务学生数", 0), errors="coerce").fillna(0).sum()
        open_last = pd.to_numeric(df_task_last.get("打开任务学生数", 0), errors="coerce").fillna(0).sum()
        finish_last = pd.to_numeric(df_task_last.get("完成任务学生数", 0), errors="coerce").fillna(0).sum()

    task_delta = task_total_cur - task_total_last
    teacher_delta = active_teacher_cur - active_teacher_last
    participation_delta = participation_cur - participation_last
    completion_delta = completion_cur - completion_last
    open_rate_cur = _safe_pct(open_cur, receive_cur)
    open_rate_last = _safe_pct(open_last, receive_last)
    finish_after_open_cur = _safe_pct(finish_cur, open_cur)
    finish_after_open_last = _safe_pct(finish_last, open_last)
    open_rate_delta = open_rate_cur - open_rate_last
    finish_after_open_delta = finish_after_open_cur - finish_after_open_last

    school_cur_p = preprocess(df_school_cur.copy())
    school_cur_only = school_cur_p[school_cur_p["学校"] != "全国"].copy()
    school_distribution_text = "学校分层数据不足，暂时无法判断整体结构。"
    school_focus_text = "当前缺少足够的学校分布信号。"

    if not school_cur_only.empty and {"参与率", "参与后完成率"}.issubset(school_cur_only.columns):
        school_cur_only["参与率"] = pd.to_numeric(school_cur_only["参与率"], errors="coerce")
        school_cur_only["参与后完成率"] = pd.to_numeric(school_cur_only["参与后完成率"], errors="coerce")
        school_cur_only = school_cur_only.dropna(subset=["参与率", "参与后完成率"]).copy()
        if not school_cur_only.empty:
            x_mid = school_cur_only["参与率"].median()
            y_mid = school_cur_only["参与后完成率"].median()

            def classify_school(row):
                if row["参与率"] >= x_mid and row["参与后完成率"] >= y_mid:
                    return "高参与·高完成"
                if row["参与率"] >= x_mid and row["参与后完成率"] < y_mid:
                    return "高参与·低完成"
                if row["参与率"] < x_mid and row["参与后完成率"] >= y_mid:
                    return "低参与·高完成"
                return "低参与·低完成"

            school_cur_only["象限"] = school_cur_only.apply(classify_school, axis=1)
            quad_counts = school_cur_only["象限"].value_counts()
            high_low = int(quad_counts.get("高参与·低完成", 0))
            low_high = int(quad_counts.get("低参与·高完成", 0))
            low_low = int(quad_counts.get("低参与·低完成", 0))

            if (high_low + low_low) > 0:
                school_distribution_text = '学校层面的分化依然明显，问题主要集中在【高参与低完成】和【低参与低完成】两类。'
            else:
                school_distribution_text = '学校层面的分布相对健康，异常象限占比不高。'

            if high_low >= low_low and high_low > 0:
                school_focus_text = '优先看【高参与但低完成】的学校，这类学校说明触达已完成，短板在完成承接。'
            elif low_low > 0:
                school_focus_text = '优先看【低参与低完成】的学校，这类学校往往同时存在触达和完成两端问题。'
            elif low_high > 0:
                school_focus_text = '有一部分学校属于【低参与高完成】，说明任务本身不差，主要问题在前链路触达。'

    task_type_structure_text = "近30天任务类型数据不足，暂时无法判断结构集中度。"
    task_type_risk_text = "当前暂未识别出明确的任务类型短板。"
    task_type_chain_reason = "当前没有足够的任务类型链路数据来判断具体掉点。"
    weakest_task_name = None
    task_type_summary = pd.DataFrame()

    if df_task_30d is not None and not df_task_30d.empty and "任务类型" in df_task_30d.columns:
        task_type_df = df_task_30d.copy()
        task_type_df["任务类型"] = task_type_df["任务类型"].fillna("未知").astype(str).str.strip()
        for col in ["接收任务学生数", "打开任务学生数", "完成任务学生数"]:
            if col in task_type_df.columns:
                task_type_df[col] = pd.to_numeric(task_type_df[col], errors="coerce").fillna(0)
            else:
                task_type_df[col] = 0

        task_type_summary = (
            task_type_df.groupby("任务类型", as_index=False)
            .agg(
                任务数=("任务类型", "size"),
                接收任务学生数=("接收任务学生数", "sum"),
                打开任务学生数=("打开任务学生数", "sum"),
                完成任务学生数=("完成任务学生数", "sum"),
            )
        )
        task_type_summary["参与率"] = task_type_summary.apply(
            lambda row: _safe_pct(row["打开任务学生数"], row["接收任务学生数"]), axis=1
        )
        task_type_summary["参与后完成率"] = task_type_summary.apply(
            lambda row: _safe_pct(row["完成任务学生数"], row["打开任务学生数"]), axis=1
        )
        task_type_summary["未打开流失"] = task_type_summary["接收任务学生数"] - task_type_summary["打开任务学生数"]
        task_type_summary["打开后未完成流失"] = task_type_summary["打开任务学生数"] - task_type_summary["完成任务学生数"]
        task_type_summary = task_type_summary.sort_values(["任务数", "参与率"], ascending=[False, False]).reset_index(drop=True)

        if not task_type_summary.empty:
            top_task = task_type_summary.iloc[0]
            top_share = top_task["任务数"] / task_type_summary["任务数"].sum() * 100 if task_type_summary["任务数"].sum() > 0 else 0
            task_type_structure_text = (
                f'任务结构明显被【{top_task["任务类型"]}】拉动，头部任务类型对整体表现影响很大。'
                if top_share >= 30 else
                '任务结构相对分散，整体表现不是由单一任务类型决定。'
            )

            risk_pool = task_type_summary[task_type_summary["任务数"] >= 3].sort_values("参与后完成率", ascending=True)
            if not risk_pool.empty:
                weakest_task = risk_pool.iloc[0]
                weakest_task_name = weakest_task["任务类型"]
                task_type_risk_text = f'从任务类型看，【{weakest_task_name}】更像当前短板。'
                if weakest_task["未打开流失"] >= weakest_task["打开后未完成流失"]:
                    task_type_chain_reason = (
                        f'说明任务类型【{weakest_task_name}】在收到任务到打开任务这段损失更大，'
                        f'未打开流失高于打开后未完成流失，问题更偏前链路触达。'
                    )
                else:
                    task_type_chain_reason = (
                        f'说明任务类型【{weakest_task_name}】在打开后的损失更大，'
                        f'打开后未完成流失高于未打开流失，问题更偏完成承接。'
                    )

    headline_parts = []
    if participation_delta >= 2 and completion_delta >= 2:
        headline_parts.append("参与率和完成率双双提升，本周整体信号积极")
    elif participation_delta <= -2 and completion_delta <= -2:
        headline_parts.append("参与率和完成率同步下滑，本周需要重点关注")
    else:
        headline_parts.append("参与率与完成率走势分化，需分别定位原因")

    if open_rate_delta <= -2:
        headline_parts.append("打开率明显下滑，前链路触达是当前主要漏点")
    elif finish_after_open_delta <= -2:
        headline_parts.append("打开后完成率下滑，任务承接环节需要重点跟进")
    else:
        headline_parts.append("打开率和完成率整体平稳，主链路无明显断层")

    if retention_data["lost"] > retention_data["new"]:
        headline_parts.append("老师流失大于新增，需关注高价值流失老师")
    elif teacher_delta > 0:
        headline_parts.append("活跃老师数量增加，老师侧扩张态势良好")

    # ---------- 整体视角文案 ----------
    overall_chain = (
        "打开率下滑是本周主要漏点，学生收到任务后没有打开，前链路触达效果变弱。"
        if open_rate_delta <= -2 else
        "打开后完成率下滑是主要漏点，学生打开了任务但没完成，承接环节需要重点关注。"
        if finish_after_open_delta <= -2 else
        "本周整体漏斗没有明显断层，打开率和完成率都在正常区间。"
    )
    overall_left = [
        f"<b>学校分布：</b>{school_distribution_text}",
        f"<b>链路诊断：</b>{overall_chain}",
        f"<b>任务结构：</b>{task_type_structure_text}",
    ]
    overall_right = [
        f"<b>优先学校：</b>{school_focus_text}",
        f"<b>老师侧：</b>{'上周有老师流失且新增不够补充，建议优先联系高价值流失老师。' if retention_data['lost'] > retention_data['new'] else '老师活跃面稳定，当前重点是扩大高活跃学校的覆盖。'}",
        f"<b>任务侧：</b>{task_type_risk_text}",
    ]

    # ---------- 任务类型视角文案 ----------
    tasktype_chain = task_type_chain_reason
    tasktype_left = [
        f"<b>结构集中度：</b>{task_type_structure_text}",
        f"<b>链路诊断：</b>{tasktype_chain}",
        f"<b>健康度最高：</b>{'参与率和完成率综合最优的任务类型，可作为推广模板。' if not task_type_summary.empty else '暂无数据。'}",
    ]
    tasktype_right = [
        f"<b>短板类型：</b>{task_type_risk_text}",
        f"<b>建议动作：</b>{'针对低健康度任务类型，重点排查是打开率低还是完成率低，分别对应触达和内容两个方向。' if not task_type_summary.empty else '暂无数据。'}",
        f"<b>老师联动：</b>优先找低健康度任务类型发布量最高的老师沟通，了解一线反馈。",
    ]

    is_task_view = st.session_state[perspective_key] == "task_type"
    left_items = tasktype_left if is_task_view else overall_left
    right_items = tasktype_right if is_task_view else overall_right
    title_suffix = "任务类型视角" if is_task_view else "整体视角"

    left_html = "".join([f"<li>{item}</li>" for item in left_items])
    right_html = "".join([f"<li>{item}</li>" for item in right_items])

    st.markdown(f'''<div class="custom-analytic-card ai-summary-card">
<div class="ai-summary-top">
<div class="ai-summary-title">本周分析摘要</div>
</div>
<div class="ai-summary-headline">{'；'.join(headline_parts)}。</div>
<div class="ai-summary-grid">
<div class="ai-summary-col">
<div class="ai-summary-col-title ai-summary-col-title-good">亮点与判断</div>
<ul>{left_html}</ul>
</div>
<div class="ai-summary-col">
<div class="ai-summary-col-title ai-summary-col-title-warn">重点跟进</div>
<ul>{right_html}</ul>
</div>
</div>
</div>''', unsafe_allow_html=True)

    action_left, action_mid, action_right = st.columns([1.1, 1.1, 4.8])
    with action_left:
        if st.button("深度分析", key="overview_ai_deep_btn", use_container_width=True):
            st.session_state[detail_key] = not st.session_state[detail_key]
            st.rerun()
    with action_mid:
        if st.button("换个角度", key="overview_ai_switch_btn", use_container_width=True):
            st.session_state[perspective_key] = "task_type" if st.session_state[perspective_key] == "overall" else "overall"
            st.rerun()

    if st.session_state[detail_key]:
        render_overview_deep_analysis_panel_v2(
            card_bg=CARD_BG,
            task_type_summary=task_type_summary,
            school_cur_only=school_cur_only,
            df_teacher_cur=df_teacher_cur,
            df_teacher_last=df_teacher_last,
            task_type_chain_reason=task_type_chain_reason,
            task_type_structure_text=task_type_structure_text,
            teacher_retention_cur=teacher_retention_cur,
            retention_data=retention_data,
            teacher_delta=teacher_delta,
            open_rate_cur=open_rate_cur,
            open_rate_delta=open_rate_delta,
            finish_after_open_cur=finish_after_open_cur,
            finish_after_open_delta=finish_after_open_delta,
            participation_cur=participation_cur,
            participation_delta=participation_delta,
            completion_cur=completion_cur,
            completion_delta=completion_delta,
            school_focus_text=school_focus_text,
            weakest_task_name=weakest_task_name,
        )


def render_overview_deep_analysis_panel_v2(
    card_bg,
    task_type_summary,
    school_cur_only,
    df_teacher_cur,
    df_teacher_last,
    task_type_chain_reason,
    task_type_structure_text,
    teacher_retention_cur,
    retention_data,
    teacher_delta,
    open_rate_cur,
    open_rate_delta,
    finish_after_open_cur,
    finish_after_open_delta,
    participation_cur,
    participation_delta,
    completion_cur,
    completion_delta,
    school_focus_text,
    weakest_task_name,
):
    def build_rows_html(df, name_col, score_col, meta_builder, score_color, suffix=""):
        if df is None or df.empty:
            return '<div style="color:#8FA3BF;font-size:13px;padding:8px 0;">暂无数据。</div>'
        rows = []
        for _, row in df.iterrows():
            rows.append(f"""
<div style="display:grid;grid-template-columns:minmax(0,1fr) 150px;gap:16px;align-items:center;padding:10px 0;border-bottom:1px solid #E5EAF3;">
  <div style="min-width:0;color:#16324F;font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{row[name_col]}</div>
  <div style="text-align:right;">
    <div style="color:{score_color};font-size:13px;font-weight:700;">{row[score_col]:.1f}{suffix}</div>
    <div style="color:#8FA3BF;font-size:11px;line-height:1.5;">{meta_builder(row)}</div>
  </div>
</div>
""")
        return "".join(rows)

    # ---------- 默认空内容 ----------
    top_task_html = '<div style="color:#8FA3BF;font-size:13px;padding:8px 0;">暂无可展示的任务类型数据。</div>'
    risk_task_html = '<div style="color:#8FA3BF;font-size:13px;padding:8px 0;">暂无可展示的风险任务类型。</div>'
    school_good_html = '<div style="color:#8FA3BF;font-size:13px;padding:8px 0;">暂无可展示的学校排行。</div>'
    school_risk_html = '<div style="color:#8FA3BF;font-size:13px;padding:8px 0;">暂无需要关注的学校数据。</div>'
    recall_teacher_html = '<div style="color:#8FA3BF;font-size:13px;padding:8px 0;">暂无可展示的召回名单。</div>'
    structure_signal_html = '<div style="color:#8FA3BF;font-size:13px;padding:8px 0;">暂无可展示的结构信号。</div>'

    # ---------- 任务类型健康度 ----------
    if task_type_summary is not None and not task_type_summary.empty:
        deep_task_df = task_type_summary.copy()
        deep_task_df["健康度"] = deep_task_df["参与率"] * 0.45 + deep_task_df["参与后完成率"] * 0.55
        healthy_df = deep_task_df.sort_values(["健康度", "任务数"], ascending=[False, False]).head(5)
        risk_df = deep_task_df.sort_values(["健康度", "任务数"], ascending=[True, False]).head(5)

        progress_rows = []
        for _, row in healthy_df.iterrows():
            progress_rows.append(f"""
<div style="padding-bottom:14px;">
  <div style="display:grid;grid-template-columns:minmax(0,1fr) 72px;gap:14px;align-items:center;">
    <div style="min-width:0;color:#16324F;font-size:13px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{row['任务类型']}</div>
    <div style="text-align:right;color:{COLOR_SECOND};font-size:13px;font-weight:700;">{row['健康度']:.1f}%</div>
  </div>
  <div style="height:8px;background:#E9EFF6;border-radius:999px;overflow:hidden;margin:8px 0 5px 0;">
    <div style="width:{max(min(row['健康度'], 100), 0):.1f}%;height:100%;background:{COLOR_SECOND};"></div>
  </div>
  <div style="display:flex;justify-content:space-between;gap:10px;color:#8FA3BF;font-size:11px;line-height:1.5;">
    <span>{int(row['任务数'])}个任务</span>
    <span>参与率 {row['参与率']:.1f}%</span>
    <span>完成率 {row['参与后完成率']:.1f}%</span>
  </div>
</div>
""")
        top_task_html = "".join(progress_rows)

        risk_task_html = build_rows_html(
            risk_df,
            "任务类型",
            "健康度",
            lambda row: f"未打开 {int(row['未打开流失'])}｜未完成 {int(row['打开后未完成流失'])}",
            COLOR_DANGER,
            "%"
        )

    # ---------- 学校健康度 ----------
    if school_cur_only is not None and not school_cur_only.empty:
        school_rank_df = school_cur_only.copy()
        school_rank_df["健康度"] = school_rank_df["参与率"] * 0.45 + school_rank_df["参与后完成率"] * 0.55
        good_school_df = school_rank_df.sort_values("健康度", ascending=False).head(8)
        risk_school_df = school_rank_df.sort_values("健康度", ascending=True).head(8)

        school_good_html = build_rows_html(
            good_school_df,
            "学校",
            "健康度",
            lambda row: f"参与率 {row['参与率']:.1f}%｜完成率 {row['参与后完成率']:.1f}%",
            COLOR_SECOND,
            "分"
        )
        school_risk_html = build_rows_html(
            risk_school_df,
            "学校",
            "健康度",
            lambda row: f"参与率 {row['参与率']:.1f}%｜完成率 {row['参与后完成率']:.1f}%",
            COLOR_DANGER,
            "分"
        )

    # ---------- 优先召回名单 ----------
    if df_teacher_last is not None and not df_teacher_last.empty:
        teacher_last_df = preprocess_teacher(df_teacher_last.copy())
        teacher_cur_df = (
            preprocess_teacher(df_teacher_cur.copy())
            if df_teacher_cur is not None and not df_teacher_cur.empty
            else pd.DataFrame()
        )

        cur_keys = set()
        if not teacher_cur_df.empty:
            if "老师邮箱" in teacher_cur_df.columns and teacher_cur_df["老师邮箱"].notna().any():
                cur_keys = set(teacher_cur_df["老师邮箱"].dropna().astype(str).str.strip().str.lower())
            elif "老师姓名" in teacher_cur_df.columns:
                cur_keys = set(teacher_cur_df["老师姓名"].dropna().astype(str).str.strip())

        if "发布任务总数" in teacher_last_df.columns:
            teacher_last_df = teacher_last_df[teacher_last_df["发布任务总数"] > 0].copy()

        if not teacher_last_df.empty:
            if "老师邮箱" in teacher_last_df.columns and teacher_last_df["老师邮箱"].notna().any():
                teacher_last_df["teacher_key"] = teacher_last_df["老师邮箱"].astype(str).str.strip().str.lower()
            else:
                teacher_last_df["teacher_key"] = teacher_last_df["老师姓名"].astype(str).str.strip()

            recall_df = teacher_last_df[~teacher_last_df["teacher_key"].isin(cur_keys)].copy()
            for col in ["发布任务总数", "接收任务学生数", "打开任务学生数", "完成任务学生数"]:
                if col in recall_df.columns:
                    recall_df[col] = pd.to_numeric(recall_df[col], errors="coerce").fillna(0)
                else:
                    recall_df[col] = 0

            if not recall_df.empty:
                recall_df["价值分"] = (
                    recall_df["发布任务总数"] * 12
                    + recall_df["接收任务学生数"] * 0.15
                    + recall_df["完成任务学生数"] * 0.25
                )
                q1 = recall_df["价值分"].quantile(0.33)
                q2 = recall_df["价值分"].quantile(0.66)
                recall_df["召回等级"] = recall_df["价值分"].apply(
                    lambda s: "易" if s >= q2 else ("中" if s >= q1 else "缓")
                )
                recall_df = recall_df.sort_values(["价值分", "发布任务总数"], ascending=[False, False]).head(10)

                rows = []
                for _, row in recall_df.iterrows():
                    school = row["学校"] if "学校" in row and pd.notna(row["学校"]) else "未知学校"
                    subject = row["科目"] if "科目" in row and pd.notna(row["科目"]) else "未知科目"
                    email = row["老师邮箱"] if "老师邮箱" in row and pd.notna(row["老师邮箱"]) else "-"
                    name = row["老师姓名"] if "老师姓名" in row and pd.notna(row["老师姓名"]) else "未知老师"
                    rows.append(f"""
<div title="老师：{name}｜邮箱：{email}｜上周任务数：{int(row['发布任务总数'])}"
     style="display:grid;grid-template-columns:minmax(0,1fr) 120px;gap:16px;align-items:center;padding:10px 0;border-bottom:1px solid #E5EAF3;">
  <div style="min-width:0;">
    <div style="color:#16324F;font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{school} · {subject}</div>
    <div style="color:#8FA3BF;font-size:11px;line-height:1.5;">{name}</div>
  </div>
  <div style="text-align:right;">
    <div style="color:{COLOR_WARN};font-size:13px;font-weight:700;">价值{row['价值分']:.1f} · {row['召回等级']}</div>
    <div style="color:#8FA3BF;font-size:11px;">hover查看邮箱</div>
  </div>
</div>
""")
                recall_teacher_html = "".join(rows)

    # ---------- 本周行动建议 ----------
    teacher_action = (
        "联系上周流失的高价值老师，了解停用原因，优先处理可挽回的流失。"
        if retention_data["lost"] > retention_data["new"] else
        "老师留存稳定，重点扩大高活跃学校的老师覆盖，推动更多老师发布任务。"
    )
    funnel_action = (
        "打开率偏低，建议检查任务推送通知是否正常，以及任务标题是否足够吸引学生点开。"
        if open_rate_delta <= -2 else
        "打开后完成率偏低，建议检查任务难度和时长设置，完成门槛过高会导致大量流失。"
        if finish_after_open_delta <= -2 else
        "漏斗整体健康，可以侧重扩大任务覆盖面，让更多学生接收到任务。"
    )
    school_action = school_focus_text
    task_action = (
        f"重点排查【{weakest_task_name}】类型的任务，{task_type_chain_reason}"
        if weakest_task_name else
        "当前任务类型数据不足，建议积累更多数据后再做类型层面的专项分析。"
    )

    def _action_row(icon, label, text, border=True):
        border_style = "border-bottom:1px solid #E5EAF3;" if border else ""
        return (
            f'<div style="padding:10px 0;{border_style}">'
            f'<div style="color:#16324F;font-size:13px;font-weight:600;margin-bottom:4px;">{icon} {label}</div>'
            f'<div style="color:#425466;font-size:12px;line-height:1.7;">{text}</div>'
            f'</div>'
        )

    structure_signal_html = "".join([
        _action_row("👨‍🏫", "老师侧行动", teacher_action),
        _action_row("📊", "漏斗优化", funnel_action),
        _action_row("🏫", "学校侧行动", school_action),
        _action_row("📋", "任务侧行动", task_action, border=False),
    ])

    # ---------- 深度分析摘要 ----------
    deep_summary_html = "".join([
        f"<li><b>任务链路：</b>{task_type_chain_reason}</li>",
        f"<li><b>任务结构：</b>{task_type_structure_text}</li>",
        "<li><b>本周重点：</b>低健康度任务类型、低健康度学校、高价值流失老师，三类对象建议本周逐一排查。</li>",
    ])

    _ds = (
        f'<div style="background:{card_bg};border:1px solid #E5EAF3;border-radius:16px;padding:14px 18px;margin:10px 0 14px 0;color:#425466;">'
        f'<div style="font-size:14px;font-weight:700;color:#60A5FA;margin-bottom:10px;">🔎 深度分析</div>'
        f'<ul style="margin:0;padding-left:18px;line-height:1.8;font-size:13px;">{deep_summary_html}</ul>'
        f'</div>'
    )
    st.markdown(_ds, unsafe_allow_html=True)

    # ===== 第一行：四个等高卡片，底部对齐 =====
    row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4, gap="large")

    with row1_col1:
        st.markdown(
            _deep_card("📊 任务类型健康度", "健康度 = 参与率45% + 完成率55%", top_task_html, card_bg),
            unsafe_allow_html=True,
        )

    with row1_col2:
        st.markdown(
            _deep_card("🚨 待关注任务类型", "优先看健康度低、流失更高的类型", risk_task_html, card_bg),
            unsafe_allow_html=True,
        )

    with row1_col3:
        st.markdown(
            _deep_card("🎯 优先召回名单", "建议优先联系高价值流失老师，hover查看邮箱", recall_teacher_html, card_bg),
            unsafe_allow_html=True,
        )

    with row1_col4:
        st.markdown(
            _deep_card("💡 本周行动建议", "基于数据诊断，当前最值得做的四件事", structure_signal_html, card_bg),
            unsafe_allow_html=True,
        )

    # ===== 第二行：两个等高卡片 =====
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    row2_col1, row2_col2 = st.columns(2, gap="large")

    with row2_col1:
        st.markdown(
            _deep_card("🏅 学校健康度排行", "按参与率与完成率综合计算", school_good_html, card_bg, height=320),
            unsafe_allow_html=True,
        )

    with row2_col2:
        st.markdown(
            _deep_card("⚠️ 需要关注学校", "优先处理综合健康度偏低的学校", school_risk_html, card_bg, height=320),
            unsafe_allow_html=True,
        )


def render_overview(df_school_cur, df_school_last, df_teacher_cur, df_teacher_last, df_task_cur=None, df_task_last=None, df_task_30d=None):


    school_cur_p = preprocess(df_school_cur.copy())
    school_last_p = preprocess(df_school_last.copy())
    teacher_cur_p = preprocess_teacher(df_teacher_cur.copy())
    teacher_last_p = preprocess_teacher(df_teacher_last.copy())

    national_cur_df = school_cur_p[school_cur_p["学校"] == "全国"].copy()
    national_last_df = school_last_p[school_last_p["学校"] == "全国"].copy()

    school_cur_df = school_cur_p[school_cur_p["学校"] != "全国"].copy()
    school_last_df = school_last_p[school_last_p["学校"] != "全国"].copy()

    if national_cur_df.empty or national_last_df.empty:
        st.error("学校数据中未找到【全国】这一行，无法展示总览。")
        return

    national_cur = national_cur_df.iloc[0]
    national_last = national_last_df.iloc[0]

    school_count_cur = school_cur_df["学校"].nunique()
    school_count_last = school_last_df["学校"].nunique()

    active_teacher_cur = to_num(national_cur["发布任务老师数"])
    active_teacher_last = to_num(national_last["发布任务老师数"])

    task_total_cur = to_num(national_cur["任务总数"])
    task_total_last = to_num(national_last["任务总数"])

    receive_students_cur = to_num(national_cur["接收任务学生数"])
    receive_students_last = to_num(national_last["接收任务学生数"])

    participation_cur = to_num(national_cur["参与率"])
    participation_last = to_num(national_last["参与率"])

    completion_cur = to_num(national_cur["参与后完成率"])
    completion_last = to_num(national_last["参与后完成率"])

    def _teacher_key(df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty:
            return pd.Series(dtype="object")
        if "老师邮箱" in df.columns and df["老师邮箱"].notna().any():
            return df["老师邮箱"].astype(str).str.strip().str.lower()
        if "老师姓名" in df.columns:
            return df["老师姓名"].astype(str).str.strip()
        return pd.Series(["未知老师"] * len(df), index=df.index)

    cur_active_teacher_cnt = 0
    if df_teacher_cur is not None and not df_teacher_cur.empty:
        teacher_cur_tmp = preprocess_teacher(df_teacher_cur.copy())
        if "发布任务总数" in teacher_cur_tmp.columns:
            teacher_cur_tmp = teacher_cur_tmp[teacher_cur_tmp["发布任务总数"] > 0].copy()
        cur_active_teacher_cnt = _teacher_key(teacher_cur_tmp).nunique()

    last_active_teacher_cnt = 0
    if df_teacher_last is not None and not df_teacher_last.empty:
        teacher_last_tmp = preprocess_teacher(df_teacher_last.copy())
        if "发布任务总数" in teacher_last_tmp.columns:
            teacher_last_tmp = teacher_last_tmp[teacher_last_tmp["发布任务总数"] > 0].copy()
        last_active_teacher_cnt = _teacher_key(teacher_last_tmp).nunique()

    teacher_pool_30d = 0
    if df_task_30d is not None and not df_task_30d.empty:
        task_30d_tmp = df_task_30d.copy()
        teacher_pool_30d = _teacher_key(task_30d_tmp).nunique()

    teacher_penetration_cur = cur_active_teacher_cnt / teacher_pool_30d * 100 if teacher_pool_30d else 0
    teacher_penetration_last = last_active_teacher_cnt / teacher_pool_30d * 100 if teacher_pool_30d else 0

    retention_data = calculate_teacher_retention_metrics(df_teacher_cur, df_teacher_last)
    teacher_retention_cur = retention_data["retention_rate"]

    render_ai_agent_panel(
        df_school_cur=df_school_cur,
        df_school_last=df_school_last,
        school_count_cur=school_count_cur,
        task_total_cur=task_total_cur,
        task_total_last=task_total_last,
        active_teacher_cur=active_teacher_cur,
        active_teacher_last=active_teacher_last,
        participation_cur=participation_cur,
        participation_last=participation_last,
        completion_cur=completion_cur,
        completion_last=completion_last,
        teacher_retention_cur=teacher_retention_cur,
        retention_data=retention_data,
        df_teacher_cur=df_teacher_cur,
        df_teacher_last=df_teacher_last,
        df_task_cur=df_task_cur,
        df_task_last=df_task_last,
        df_task_30d=df_task_30d,
    )
    st.markdown("---")
    st.subheader("🌍 全局指标总览")
    st.markdown("### 核心指标（本周vs上周）")

    row1 = st.columns(4)
    with row1[0]:
        metric_block("学校数量", school_count_cur, school_count_last)
    with row1[1]:
        metric_block("活跃老师数", active_teacher_cur, active_teacher_last)
    with row1[2]:
        metric_block("任务总数", task_total_cur, task_total_last)
    with row1[3]:
        delta = teacher_penetration_cur - teacher_penetration_last
        st.metric("老师渗透率", f"{teacher_penetration_cur:.1f}%", f"{delta:+.1f}%")

    row2 = st.columns(4)
    with row2[0]:
        metric_block("老师留存率", teacher_retention_cur, is_percent=True, show_delta=False)
    with row2[1]:
        metric_block("接收任务学生数", receive_students_cur, receive_students_last)
    with row2[2]:
        metric_block("参与率", participation_cur, participation_last, is_percent=True)
    with row2[3]:
        metric_block("参与后完成率", completion_cur, completion_last, is_percent=True)

    st.markdown("---")
    st.markdown("### 趋势与漏斗")

    metric_options = ["任务总数", "活跃老师数", "参与率", "参与后完成率"]

    selected_metrics = st.multiselect(
        "选择展示的趋势指标",
        metric_options,
        default=["任务总数", "活跃老师数", "参与率"],
        key="overview_monthly_metrics"
    )

    left_col, right_col = st.columns([1.2, 1], gap="large")

    with left_col:
        if df_task_30d is None or df_task_30d.empty or "任务发布时间" not in df_task_30d.columns:
            st.info("暂无近30天任务数据，无法展示月趋势。")
        else:
            task_30d = df_task_30d.copy()
            task_30d["任务发布时间"] = pd.to_datetime(task_30d["任务发布时间"], errors="coerce")
            task_30d = task_30d.dropna(subset=["任务发布时间"]).copy()
            task_30d["日期"] = task_30d["任务发布时间"].dt.date

            for col in ["接收任务学生数", "打开任务学生数", "完成任务学生数"]:
                if col in task_30d.columns:
                    task_30d[col] = pd.to_numeric(task_30d[col], errors="coerce").fillna(0)
                else:
                    task_30d[col] = 0

            if "老师姓名" not in task_30d.columns:
                task_30d["老师姓名"] = None

            trend_df = (
                task_30d.groupby("日期", as_index=False)
                .agg(
                    任务总数=("任务发布时间", "count"),
                    活跃老师数=("老师姓名", lambda x: x.dropna().astype(str).str.strip().nunique()),
                    接收任务学生数=("接收任务学生数", "sum"),
                    打开任务学生数=("打开任务学生数", "sum"),
                    完成任务学生数=("完成任务学生数", "sum"),
                )
                .sort_values("日期")
            )

            trend_df["参与率"] = trend_df.apply(
                lambda x: x["打开任务学生数"] / x["接收任务学生数"] * 100 if x["接收任务学生数"] > 0 else 0,
                axis=1
            )
            trend_df["参与后完成率"] = trend_df.apply(
                lambda x: x["完成任务学生数"] / x["打开任务学生数"] * 100 if x["打开任务学生数"] > 0 else 0,
                axis=1
            )

            fig_trend = make_subplots(specs=[[{"secondary_y": True}]])

            color_map = {
                "任务总数": COLOR_PRIMARY,
                "活跃老师数": COLOR_WARN,
                "参与率": COLOR_SECOND,
                "参与后完成率": COLOR_DANGER,
            }

            count_metrics = [m for m in selected_metrics if m in ["任务总数", "活跃老师数"]]
            rate_metrics = [m for m in selected_metrics if m in ["参与率", "参与后完成率"]]

            for metric in count_metrics:
                fig_trend.add_trace(
                    go.Scatter(
                        x=trend_df["日期"],
                        y=trend_df[metric],
                        mode="lines+markers",
                        name=metric,
                        line=dict(width=2.5, color=color_map[metric]),
                        marker=dict(size=5, color=color_map[metric]),
                        hovertemplate="%{x}<br>" + metric + "：%{y:,.0f}<extra></extra>"
                    ),
                    secondary_y=False
                )

            for metric in rate_metrics:
                fig_trend.add_trace(
                    go.Scatter(
                        x=trend_df["日期"],
                        y=trend_df[metric],
                        mode="lines+markers",
                        name=metric,
                        line=dict(width=2.5, color=color_map[metric]),
                        marker=dict(size=5, color=color_map[metric]),
                        hovertemplate="%{x}<br>" + metric + "：%{y:.1f}%<extra></extra>"
                    ),
                    secondary_y=True
                )

            fig_trend.update_layout(
                plot_bgcolor=CARD_BG,
                paper_bgcolor=CARD_BG,
                font=dict(color=TEXT_COLOR),
                margin=dict(l=26, r=26, t=22, b=52),
                legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
                height=320,
                hovermode="x unified"
            )

            fig_trend.update_xaxes(
                title_text="",
                showgrid=False,
                tickfont=dict(color=SUB_TEXT_COLOR),
                title_font=dict(color=TEXT_COLOR)
            )
            fig_trend.update_yaxes(
                title_text="数量指标",
                secondary_y=False,
                showgrid=True,
                gridcolor=GRID_COLOR,
                zeroline=False,
                tickfont=dict(color=SUB_TEXT_COLOR),
                title_font=dict(color=TEXT_COLOR)
            )
            fig_trend.update_yaxes(
                title_text="比例指标（%）",
                secondary_y=True,
                showgrid=False,
                zeroline=False,
                range=[0, 100],
                tickfont=dict(color=SUB_TEXT_COLOR),
                title_font=dict(color=TEXT_COLOR)
            )

            render_chart_card(fig_trend, title="近30天趋势")

    with right_col:
        if df_task_30d is None or df_task_30d.empty:
            st.info("暂无近30天任务数据，无法展示漏斗分析。")
        else:
            task_30d = df_task_30d.copy()
            for col in ["接收任务学生数", "打开任务学生数", "完成任务学生数"]:
                if col in task_30d.columns:
                    task_30d[col] = pd.to_numeric(task_30d[col], errors="coerce").fillna(0)
                else:
                    task_30d[col] = 0

            task_7d = pd.DataFrame()
            if df_task_cur is not None and not df_task_cur.empty:
                task_7d = df_task_cur.copy()
                for col in ["接收任务学生数", "打开任务学生数", "完成任务学生数"]:
                    if col in task_7d.columns:
                        task_7d[col] = pd.to_numeric(task_7d[col], errors="coerce").fillna(0)
                    else:
                        task_7d[col] = 0

            def summarize_funnel(df):
                if df is None or df.empty:
                    return {"receive": 0, "open": 0, "finish": 0,
                            "open_rate": 0, "finish_after_open_rate": 0, "total_finish_rate": 0}
                total_receive = df["接收任务学生数"].sum()
                total_open = df["打开任务学生数"].sum()
                total_finish = df["完成任务学生数"].sum()
                return {
                    "receive": total_receive, "open": total_open, "finish": total_finish,
                    "open_rate": total_open / total_receive * 100 if total_receive > 0 else 0,
                    "finish_after_open_rate": total_finish / total_open * 100 if total_open > 0 else 0,
                    "total_finish_rate": total_finish / total_receive * 100 if total_receive > 0 else 0
                }

            week_stats = summarize_funnel(task_7d)
            month_stats = summarize_funnel(task_30d)

            def build_funnel_chart(stats, title):
                funnel_df = pd.DataFrame({
                    "阶段": ["接收", "打开", "完成"],
                    "人数": [stats["receive"], stats["open"], stats["finish"]]
                })
                fig = px.funnel(
                    funnel_df, x="人数", y="阶段", color="阶段",
                    category_orders={"阶段": ["接收", "打开", "完成"]},
                    color_discrete_map={"接收": "#6FAFE0", "打开": "#3B5998", "完成": "#7BCFA6"}
                )
                fig.update_traces(texttemplate="%{x:,.0f}", textposition="inside")
                fig.update_layout(
                    height=240, plot_bgcolor=CARD_BG, paper_bgcolor=CARD_BG,
                    font=dict(color=TEXT_COLOR), margin=dict(l=18, r=18, t=12, b=12),
                    showlegend=False
                )
                fig.update_xaxes(title_text="", showgrid=False, zeroline=False, tickfont=dict(color=SUB_TEXT_COLOR))
                fig.update_yaxes(title_text="", showgrid=False, zeroline=False, tickfont=dict(color=TEXT_COLOR))
                return fig

            funnel_left, funnel_right = st.columns(2, gap="small")
            with funnel_left:
                fig_week = build_funnel_chart(week_stats, "近7天漏斗")
                render_chart_card(fig_week, title="近7天漏斗")
            with funnel_right:
                fig_month = build_funnel_chart(month_stats, "近30天漏斗")
                render_chart_card(fig_month, title="近30天漏斗")

            if week_stats["total_finish_rate"] > month_stats["total_finish_rate"] + 2:
                conclusion = "近7天总完成率高于近30天平均水平，近期任务转化表现有所改善。"
            elif week_stats["total_finish_rate"] < month_stats["total_finish_rate"] - 2:
                conclusion = "近7天总完成率低于近30天平均水平，近期任务转化有所走弱，建议关注最新任务触达与完成情况。"
            else:
                conclusion = "近7天与近30天整体转化水平基本一致，近期表现相对稳定。"

            st.markdown(f'''<div style="margin-top:8px;background:#F8FBFF;border:1px solid #E5EAF3;border-radius:14px;padding:12px 14px;color:#425466;font-size:13px;line-height:1.6;">
<b style="color:#16324F;"></b>{conclusion}
</div>''', unsafe_allow_html=True)
