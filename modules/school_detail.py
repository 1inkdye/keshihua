
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.charts import (
    style_figure,
    CARD_BG, HOVER_BG, TEXT_COLOR, SUB_TEXT_COLOR,
    COLOR_SECOND, COLOR_DANGER,
    render_chart_card
)
from utils.preprocess import preprocess_teacher, normalize_school_col
from utils.metrics import calculate_teacher_retention_metrics
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
def _teacher_key(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype="object")

    if "老师邮箱" in df.columns and df["老师邮箱"].notna().any():
        return df["老师邮箱"].astype(str).str.strip().str.lower()

    if "老师姓名" in df.columns:
        return df["老师姓名"].astype(str).str.strip()

    return pd.Series(["未知老师"] * len(df), index=df.index)
def render_school_detail_page(
    selected_school: str,
    school_cur: pd.DataFrame,
    school_last: pd.DataFrame,
    teacher_cur: pd.DataFrame,
    teacher_last: pd.DataFrame,
    task_cur: pd.DataFrame = None,
    task_30d: pd.DataFrame = None
):
    if teacher_cur is None or teacher_cur.empty:
        st.warning("当前分析窗口内暂无老师数据。")
        return
    if not selected_school:
        st.warning("未选择学校")
        return

    if st.button("← 返回整体看板", key="back_to_overview"):
        st.session_state.top_nav_mode = "overview"
        st.rerun()

    st.markdown("""
<style>
@keyframes customPanelReveal {
    0% { opacity: 0; transform: translateY(18px) scale(0.98); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes customBarFill {
    0% { width: 0; opacity: 0.35; }
    100% { opacity: 1; }
}

.custom-analytic-card {
    animation: customPanelReveal 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
    transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.28s cubic-bezier(0.22, 1, 0.36, 1), border-color 0.28s ease;
}

.custom-analytic-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 36px rgba(15, 23, 42, 0.26);
    border-color: rgba(123, 207, 166, 0.18) !important;
}

.task-penetration-row {
    display:flex;
    align-items:center;
    gap:12px;
    padding:8px 0;
    transition: transform 0.24s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.22s ease;
}

.task-penetration-row:hover {
    transform: translateX(4px);
}

.task-penetration-row:hover .task-penetration-track {
    background: #E3ECF6 !important;
}

.task-penetration-row:hover .task-penetration-fill {
    filter: brightness(1.08) saturate(1.08);
    box-shadow: 0 10px 20px rgba(15, 23, 42, 0.22);
}

.task-penetration-track {
    flex:1;
    position:relative;
    height:28px;
    background:#EDF3F9;
    border-radius:999px;
    overflow:hidden;
    transition: background 0.24s ease;
}

.task-penetration-fill {
    position:absolute;
    left:0;
    top:0;
    height:100%;
    border-radius:999px;
    display:flex;
    align-items:center;
    padding-left:10px;
    min-width:52px;
    animation: customBarFill 0.95s cubic-bezier(0.16, 0.84, 0.24, 1) both;
    transition: transform 0.24s cubic-bezier(0.22, 1, 0.36, 1), filter 0.24s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.24s ease;
    transform-origin: left center;
}

.task-type-summary-card {
    animation-delay: 0.06s;
}

.task-penetration-card {
    animation-delay: 0.12s;
}
</style>
""", unsafe_allow_html=True)

    st.markdown(f"## 📍 {selected_school} 详情")
    # =========================
    # 一、学校详情页 KPI
    # =========================
    school_cur = school_cur.copy() if school_cur is not None else pd.DataFrame()
    school_last = school_last.copy() if school_last is not None else pd.DataFrame()
    teacher_cur = teacher_cur.copy() if teacher_cur is not None else pd.DataFrame()
    teacher_last = teacher_last.copy() if teacher_last is not None else pd.DataFrame()
    task_cur = task_cur.copy() if task_cur is not None else pd.DataFrame()
    task_30d = task_30d.copy() if task_30d is not None else pd.DataFrame()

    # 当前学校：学校快照
    school_cur_one = pd.DataFrame()
    school_last_one = pd.DataFrame()

    if not school_cur.empty and "学校" in school_cur.columns:
        school_cur_one = school_cur[school_cur["学校"] == selected_school].copy()

    if not school_last.empty and "学校" in school_last.columns:
        school_last_one = school_last[school_last["学校"] == selected_school].copy()

    cur_row = school_cur_one.iloc[0] if not school_cur_one.empty else None
    last_row = school_last_one.iloc[0] if not school_last_one.empty else None

    # 1) 直接复用 school snapshot 里的学校级指标
    task_total_cur = to_num(cur_row["任务总数"]) if cur_row is not None and "任务总数" in cur_row else 0
    task_total_last = to_num(last_row["任务总数"]) if last_row is not None and "任务总数" in last_row else 0

    receive_students_cur = to_num(cur_row["接收任务学生数"]) if cur_row is not None and "接收任务学生数" in cur_row else 0
    receive_students_last = to_num(last_row["接收任务学生数"]) if last_row is not None and "接收任务学生数" in last_row else 0

    participation_cur = to_num(cur_row["参与率"]) if cur_row is not None and "参与率" in cur_row else 0
    participation_last = to_num(last_row["参与率"]) if last_row is not None and "参与率" in last_row else 0

    completion_cur = to_num(cur_row["参与后完成率"]) if cur_row is not None and "参与后完成率" in cur_row else 0
    completion_last = to_num(last_row["参与后完成率"]) if last_row is not None and "参与后完成率" in last_row else 0

    # 2) 老师渗透率：本周该校活跃老师 / 近30天该校老师池
    school_teacher_cur = pd.DataFrame()
    school_teacher_last = pd.DataFrame()
    school_task_cur = pd.DataFrame()
    school_task_30d = pd.DataFrame()

    if not teacher_cur.empty and "学校" in teacher_cur.columns:
        school_teacher_cur = teacher_cur[teacher_cur["学校"] == selected_school].copy()
    if not teacher_last.empty and "学校" in teacher_last.columns:
        school_teacher_last = teacher_last[teacher_last["学校"] == selected_school].copy()

    if not task_cur.empty and "学校" in task_cur.columns:
        school_task_cur = task_cur[task_cur["学校"] == selected_school].copy()
    if not task_30d.empty and "学校" in task_30d.columns:
        school_task_30d = task_30d[task_30d["学校"] == selected_school].copy()

    cur_active_teacher_cnt = 0
    if not school_teacher_cur.empty:
        tmp = preprocess_teacher(school_teacher_cur.copy())
        if "发布任务总数" in tmp.columns:
            tmp = tmp[tmp["发布任务总数"] > 0].copy()
        cur_active_teacher_cnt = _teacher_key(tmp).nunique()

    last_active_teacher_cnt = 0
    if not school_teacher_last.empty:
        tmp = preprocess_teacher(school_teacher_last.copy())
        if "发布任务总数" in tmp.columns:
            tmp = tmp[tmp["发布任务总数"] > 0].copy()
        last_active_teacher_cnt = _teacher_key(tmp).nunique()

    teacher_pool_30d = _teacher_key(school_task_30d).nunique() if not school_task_30d.empty else 0

    teacher_penetration_cur = cur_active_teacher_cnt / teacher_pool_30d * 100 if teacher_pool_30d > 0 else 0
    teacher_penetration_last = last_active_teacher_cnt / teacher_pool_30d * 100 if teacher_pool_30d > 0 else 0

    # 3) 老师留存率：只对当前学校调用
    teacher_retention_cur = 0
    if not school_teacher_cur.empty and not school_teacher_last.empty:
        retention_data = calculate_teacher_retention_metrics(
            school_teacher_cur,
            school_teacher_last
        )
        teacher_retention_cur = retention_data.get("retention_rate", 0)

    # KPI 展示：两行三列
    st.markdown("### 核心指标")
    kpi_row1 = st.columns(3)
    with kpi_row1[0]:
        metric_block("任务总数", task_total_cur, task_total_last)
    with kpi_row1[1]:
        st.metric(
            "老师渗透率",
            f"{teacher_penetration_cur:.1f}%",
            f"{teacher_penetration_cur - teacher_penetration_last:+.1f}%"
        )
    with kpi_row1[2]:
        metric_block("老师留存率", teacher_retention_cur, is_percent=True, show_delta=False)

    kpi_row2 = st.columns(3)
    with kpi_row2[0]:
        metric_block("接收任务学生数", receive_students_cur, receive_students_last)
    with kpi_row2[1]:
        metric_block("参与率", participation_cur, participation_last, is_percent=True)
    with kpi_row2[2]:
        metric_block("参与后完成率", completion_cur, completion_last, is_percent=True)

    st.markdown("---")

    # ===== 数据处理 =====
    if "学校" not in teacher_cur.columns:
        st.warning("当前老师数据缺少【学校】字段，无法展示学校详情。")
        return

    teacher_one_school = teacher_cur[teacher_cur["学校"] == selected_school].copy()

    if teacher_one_school.empty:
        st.warning(f"{selected_school} 暂无老师数据")
        return

    for col in ["发布任务总数", "参与率", "参与后完成率", "接收任务学生数", "完成任务学生数"]:
        if col in teacher_one_school.columns:
            teacher_one_school[col] = pd.to_numeric(teacher_one_school[col], errors="coerce")

    required_cols = ["老师姓名", "发布任务总数", "参与率", "参与后完成率"]
    teacher_one_school = teacher_one_school.dropna(
        subset=[c for c in required_cols if c in teacher_one_school.columns]
    ).copy()

    if teacher_one_school.empty:
        st.info("当前学校暂无可展示的老师数据。")
        return
    # ===== 数据处理 =====
    teacher_cur = teacher_cur.copy()
    teacher_last = teacher_last.copy()
    # teacher_cur = preprocess_teacher(teacher_cur)
    # teacher_cur = normalize_school_col(teacher_cur)
    # teacher_last = preprocess_teacher(teacher_last)
    # teacher_last = normalize_school_col(teacher_last)
    if "学校" not in teacher_cur.columns:
        st.warning("当前老师数据缺少【学校】字段，无法展示学校详情。")
        return
    teacher_one_school = teacher_cur[teacher_cur["学校"] == selected_school].copy()

    if teacher_one_school.empty:
        st.warning(f"{selected_school} 暂无老师数据")
        return

    for col in ["发布任务总数", "参与率", "参与后完成率", "接收任务学生数", "完成任务学生数"]:
        if col in teacher_one_school.columns:
            teacher_one_school[col] = pd.to_numeric(teacher_one_school[col], errors="coerce")

    required_cols = ["老师姓名", "发布任务总数", "参与率", "参与后完成率"]
    teacher_one_school = teacher_one_school.dropna(
        subset=[c for c in required_cols if c in teacher_one_school.columns]
    ).copy()

    if teacher_one_school.empty:
        st.info("当前学校暂无可展示的老师数据。")
        return

    def render_delta_inline(delta):
        if pd.notna(delta):
            arrow = "↑" if delta >= 0 else "↓"
            color = "#7BCFA6" if delta >= 0 else "#B36D61"
            return f"""
<span style='font-size:13px;color:{color};font-weight:600;'>
{arrow}{abs(delta):.1f}%
</span>
"""
        else:
            return "<span style='font-size:13px;color:#8FA3BF;'>-</span>"

    # =========================================================
    # 一、排行榜（左）+ 参与率变化（右）同行
    # =========================================================
    MIN_TASK = 5
    teacher_valid = teacher_one_school[teacher_one_school["发布任务总数"] >= MIN_TASK].copy()

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        if teacher_valid.empty:
            st.warning(f"该校区暂无任务量≥{MIN_TASK}的老师数据。")
        else:
            # ===== 本周统计 =====
            avg_part = teacher_valid["参与率"].mean()
            median_part = teacher_valid["参与率"].median()
            high_part = (teacher_valid["参与率"] >= 80).sum()
            low_part = (teacher_valid["参与率"] < 60).sum()

            avg_finish = teacher_valid["参与后完成率"].mean()
            median_finish = teacher_valid["参与后完成率"].median()
            high_finish = (teacher_valid["参与后完成率"] >= 80).sum()
            low_finish = (teacher_valid["参与后完成率"] < 60).sum()

            # ===== 上周同口径统计（任务量>=5）=====
            teacher_last_one_school = teacher_last[teacher_last["学校"] == selected_school].copy()
            for col in ["发布任务总数", "参与率", "参与后完成率"]:
                if col in teacher_last_one_school.columns:
                    teacher_last_one_school[col] = pd.to_numeric(teacher_last_one_school[col], errors="coerce")

            teacher_last_one_school = teacher_last_one_school[
                teacher_last_one_school["发布任务总数"] >= MIN_TASK
            ].copy()

            avg_part_last = teacher_last_one_school["参与率"].mean()
            avg_finish_last = teacher_last_one_school["参与后完成率"].mean()

            avg_part_delta = avg_part - avg_part_last if pd.notna(avg_part_last) else None
            avg_finish_delta = avg_finish - avg_finish_last if pd.notna(avg_finish_last) else None

            total_teachers = len(teacher_one_school)

            st.markdown("#### 校内老师排行")

            col_sort_label, col_sort_radio = st.columns([1, 4], vertical_alignment="center")
            with col_sort_label:
                st.markdown(
                    "<div style='font-size:14px;font-weight:600;color:#EAF1FF;'>排序方式</div>",
                    unsafe_allow_html=True
                )
            with col_sort_radio:
                sort_mode = st.radio(
                    "排序方式",
                    ["参与率", "完成率"],
                    horizontal=True,
                    key="teacher_rank_sort",
                    label_visibility="collapsed"
                )

            teacher_rank_df = teacher_valid.copy()

            # ===== 老师个人环比变化 =====
            teacher_cur_delta = teacher_cur[
                teacher_cur["学校"] == selected_school
            ][["老师姓名", "参与率", "参与后完成率"]].copy()
            teacher_cur_delta = teacher_cur_delta.rename(columns={
                "参与率": "本周参与率",
                "参与后完成率": "本周参与后完成率"
            })

            teacher_last_delta = teacher_last[
                teacher_last["学校"] == selected_school
            ][["老师姓名", "参与率", "参与后完成率"]].copy()
            teacher_last_delta = teacher_last_delta.rename(columns={
                "参与率": "上周参与率",
                "参与后完成率": "上周参与后完成率"
            })

            teacher_delta = pd.merge(
                teacher_cur_delta,
                teacher_last_delta,
                on="老师姓名",
                how="left"
            )

            teacher_delta["参与率变化"] = teacher_delta["本周参与率"] - teacher_delta["上周参与率"]
            teacher_delta["参与后完成率变化"] = teacher_delta["本周参与后完成率"] - teacher_delta["上周参与后完成率"]

            teacher_rank_df = teacher_rank_df.merge(
                teacher_delta[["老师姓名", "参与率变化", "参与后完成率变化"]],
                on="老师姓名",
                how="left"
            )

            if sort_mode == "参与率":
                teacher_rank_df = teacher_rank_df.sort_values(
                    ["参与率", "参与后完成率", "发布任务总数"],
                    ascending=[False, False, False]
                )
            else:
                teacher_rank_df = teacher_rank_df.sort_values(
                    ["参与后完成率", "参与率", "发布任务总数"],
                    ascending=[False, False, False]
                )

            top10_df = teacher_rank_df.head(10).reset_index(drop=True)
            n_rows = len(top10_df)

            # 左侧高度驱动右侧图高度
            left_total_height = 30 + n_rows * 60 + 24 + 12 + 112
            right_overhead = 40 + 35 + 37 + 30 + 19
            right_chart_height = max(180, int((left_total_height - right_overhead) / 2))

            rank_colors = ["#F59E0B", "#9CA3AF", "#CD7C3A"]

            rows_html = """
<div style="display:flex;align-items:center;justify-content:space-between;padding:2px 1px 4px 1px;border-bottom:1px solid rgba(255,255,255,0.10);margin-bottom:4px;">
<div style="flex:2.2;font-size:11px;color:#8FA3BF;font-weight:600;">老师(任务量≥5)</div>
<div style="flex:0.8;text-align:right;font-size:11px;color:#8FA3BF;font-weight:600;">学生参与率<span style="font-size:10px;font-weight:500;">（老师维度）</span></div>
<div style="flex:0.8;text-align:right;font-size:11px;color:#8FA3BF;font-weight:600;">学生完成率<span style="font-size:10px;font-weight:500;">（参与后）</span></div>
</div>
"""

            for i, row in top10_df.iterrows():
                rank = i + 1
                badge_bg = rank_colors[rank - 1] if rank <= 3 else "#374151"
                divider = "" if i == len(top10_df) - 1 else "border-bottom:1px solid rgba(255,255,255,0.06);"

                task_text = f"任务{int(row['发布任务总数'])}" if pd.notna(row.get("发布任务总数")) else "任务-"
                recv_text = f"接收{int(row['接收任务学生数'])}" if pd.notna(row.get("接收任务学生数")) else "接收-"
                finish_text = f"完成{int(row['完成任务学生数'])}" if pd.notna(row.get("完成任务学生数")) else "完成-"

                part_delta = row.get("参与率变化", None)
                finish_delta = row.get("参与后完成率变化", None)

                if pd.notna(part_delta):
                    part_arrow = "↑" if part_delta >= 0 else "↓"
                    part_color = "#7BCFA6" if part_delta >= 0 else "#B36D61"
                    part_delta_html = f"<div style='font-size:10px;color:{part_color};font-weight:600;margin-top:3px;line-height:1.1;'>{part_arrow}{abs(part_delta):.1f}%</div>"
                else:
                    part_delta_html = "<div style='font-size:10px;color:#8FA3BF;margin-top:3px;line-height:1.1;'>-</div>"

                if pd.notna(finish_delta):
                    finish_arrow = "↑" if finish_delta >= 0 else "↓"
                    finish_color = "#7BCFA6" if finish_delta >= 0 else "#B36D61"
                    finish_delta_html = f"<div style='font-size:10px;color:{finish_color};font-weight:600;margin-top:3px;line-height:1.1;'>{finish_arrow}{abs(finish_delta):.1f}%</div>"
                else:
                    finish_delta_html = "<div style='font-size:10px;color:#8FA3BF;margin-top:3px;line-height:1.1;'>-</div>"

                rows_html += f"""
<div class="rank-board-row" style="display:flex;align-items:center;justify-content:space-between;padding:10px 10px;{divider}">
<div style="display:flex;align-items:center;gap:10px;min-width:0;flex:2.2;">
<div style="width:26px;height:26px;border-radius:7px;background:{badge_bg};color:white;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
{rank}
</div>
<div style="min-width:0;">
<div style="font-size:14px;font-weight:600;color:#16324F;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:1.2;">
{row['老师姓名']}
</div>
<div style="font-size:10px;color:#8FA3BF;margin-top:2px;line-height:1.2;">
{task_text}｜{recv_text}｜{finish_text}
</div>
</div>
</div>

<div style="flex:0.8;text-align:right;">
<div style="font-size:16px;font-weight:700;color:#7BCFA6;line-height:1.1;">
{row['参与率']:.1f}%
</div>
{part_delta_html}
</div>

<div style="flex:0.8;text-align:right;">
<div style="font-size:16px;font-weight:700;color:#F2A541;line-height:1.1;">
{row['参与后完成率']:.1f}%
</div>
{finish_delta_html}
</div>
</div>
"""

            st.markdown(
                f"""<div class="rank-board-card" style="
background:#FFFFFF;
border:1px solid #E5EAF3;
border-radius:16px;
padding:12px 16px;
min-height:320px;
">
{rows_html}
</div>""",
                unsafe_allow_html=True
            )

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            st.markdown(
                f"""<div style="display:flex;gap:12px;flex-wrap:wrap;">
<div style="flex:1;min-width:120px;padding:12px 16px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:12px;">
<div style="font-size:11px;color:#8FA3BF;margin-bottom:4px;">学生参与率均值</div>
<div style="display:flex;align-items:baseline;gap:8px;">
<div style="font-size:22px;font-weight:700;color:#7BCFA6;">
{avg_part:.1f}%
</div>
{render_delta_inline(avg_part_delta)}
</div>
<div style="font-size:11px;color:#8FA3BF;margin-top:6px;">
中位数 {median_part:.1f}%　
<span style="color:#7BCFA6;">高参与 {high_part} 人</span>　
<span style="color:#B36D61;">低参与 {low_part} 人</span>
</div>
</div>

<div style="flex:1;min-width:120px;padding:12px 16px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:12px;">
<div style="font-size:11px;color:#8FA3BF;margin-bottom:4px;">学生完成率均值（参与后）</div>
<div style="display:flex;align-items:baseline;gap:8px;">
<div style="font-size:22px;font-weight:700;color:#F2A541;">
{avg_finish:.1f}%
</div>
{render_delta_inline(avg_finish_delta)}
</div>
<div style="font-size:11px;color:#8FA3BF;margin-top:6px;">
中位数 {median_finish:.1f}%　
<span style="color:#7BCFA6;">高完成 {high_finish} 人</span>　
<span style="color:#B36D61;">低完成 {low_finish} 人</span>
</div>
</div>

<div style="flex:1;min-width:120px;padding:12px 16px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:12px;">
<div style="font-size:11px;color:#8FA3BF;margin-bottom:4px;">结论</div>
<div style="font-size:12px;color:#16324F;line-height:1.7;margin-top:2px;">
共 <b>{total_teachers}</b> 位老师，有效样本（任务≥{MIN_TASK}）<b>{len(teacher_valid)}</b> 位。建议关注参与率高但完成率低的老师，优化任务质量与学生跟进链路。
</div>
</div>
</div>""",
                unsafe_allow_html=True
            )

    with col_right:
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        teacher_cur_part = teacher_cur[teacher_cur["学校"] == selected_school][["老师姓名", "参与率"]].copy()
        teacher_cur_part = teacher_cur_part.rename(columns={"参与率": "本周参与率"})
        teacher_last_part = teacher_last[teacher_last["学校"] == selected_school][["老师姓名", "参与率"]].copy()
        teacher_last_part = teacher_last_part.rename(columns={"参与率": "上周参与率"})

        teacher_change = pd.merge(teacher_cur_part, teacher_last_part, on="老师姓名", how="inner")
        teacher_change["参与率变化"] = teacher_change["本周参与率"] - teacher_change["上周参与率"]

        if teacher_change.empty:
            st.warning("该学校在两周老师数据中没有可对比记录。")
        else:
            teacher_up = teacher_change.sort_values("参与率变化", ascending=False).head(5)
            teacher_down = teacher_change.sort_values("参与率变化", ascending=True).head(5)
            teacher_change_show = pd.concat([teacher_down, teacher_up], ignore_index=True)
            teacher_change_show = teacher_change_show.drop_duplicates(subset=["老师姓名"])
            teacher_change_show = teacher_change_show.sort_values("参与率变化", ascending=True)

            raw_max = teacher_change_show["参与率变化"].abs().max()
            max_val = max(raw_max * 1.15, 10)

            fig_teacher_change = go.Figure()
            fig_teacher_change.add_trace(go.Bar(
                x=[max_val] * len(teacher_change_show),
                y=teacher_change_show["老师姓名"],
                orientation="h",
                marker=dict(color="rgba(0,0,0,0.06)", line_width=0),
                showlegend=False,
                hoverinfo="skip"
            ))
            fig_teacher_change.add_trace(go.Bar(
                x=[-max_val] * len(teacher_change_show),
                y=teacher_change_show["老师姓名"],
                orientation="h",
                marker=dict(color="rgba(0,0,0,0.06)", line_width=0),
                showlegend=False,
                hoverinfo="skip"
            ))

            for _, row in teacher_change_show.iterrows():
                color = COLOR_SECOND if row["参与率变化"] >= 0 else COLOR_DANGER
                fig_teacher_change.add_trace(go.Bar(
                    x=[row["参与率变化"]],
                    y=[row["老师姓名"]],
                    orientation="h",
                    marker=dict(color=color, line_width=0),
                    text=f"{row['参与率变化']:+.1f}%",
                    textposition="inside",
                    textfont=dict(color="#FFFFFF", size=11),
                    showlegend=False,
                    hovertemplate=f"{row['老师姓名']}: {row['参与率变化']:+.1f}%<extra></extra>"
                ))

            fig_teacher_change.update_layout(
                barmode="overlay",
                bargap=0.32,
                plot_bgcolor=CARD_BG,
                paper_bgcolor=CARD_BG,
                font=dict(color=TEXT_COLOR, size=11),
                height=right_chart_height,
                margin=dict(l=26, r=26, t=10, b=10),
                xaxis=dict(
                    range=[-max_val * 1.05, max_val * 1.05],
                    showgrid=False,
                    zeroline=True,
                    zerolinecolor="#D7E1EE",
                    zerolinewidth=1.2,
                    tickfont=dict(color=SUB_TEXT_COLOR, size=10),
                    showline=False
                ),
                yaxis=dict(
                    showgrid=False,
                    tickfont=dict(color=TEXT_COLOR, size=10),
                    categoryorder="array",
                    categoryarray=teacher_change_show["老师姓名"].tolist(),
                    automargin=True
                ),
                hoverlabel=dict(bgcolor=HOVER_BG, font_color=TEXT_COLOR, bordercolor=HOVER_BG)
            )

            try:
                fig_teacher_change.update_layout(barcornerradius=999)
            except Exception:
                pass

            render_chart_card(fig_teacher_change, title="参与率变化（按老师）Top/Bottom")

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        teacher_cur_part = teacher_cur[teacher_cur["学校"] == selected_school][["老师姓名", "参与后完成率"]].copy()
        teacher_cur_part = teacher_cur_part.rename(columns={"参与后完成率": "本周参与后完成率"})
        teacher_last_part = teacher_last[teacher_last["学校"] == selected_school][["老师姓名", "参与后完成率"]].copy()
        teacher_last_part = teacher_last_part.rename(columns={"参与后完成率": "上周参与后完成率"})

        teacher_change = pd.merge(teacher_cur_part, teacher_last_part, on="老师姓名", how="inner")
        teacher_change["参与后完成率变化"] = teacher_change["本周参与后完成率"] - teacher_change["上周参与后完成率"]

        if teacher_change.empty:
            st.warning("该学校在两周老师数据中没有可对比记录。")
        else:
            teacher_up = teacher_change.sort_values("参与后完成率变化", ascending=False).head(5)
            teacher_down = teacher_change.sort_values("参与后完成率变化", ascending=True).head(5)
            teacher_change_show = pd.concat([teacher_down, teacher_up], ignore_index=True)
            teacher_change_show = teacher_change_show.drop_duplicates(subset=["老师姓名"])
            teacher_change_show = teacher_change_show.sort_values("参与后完成率变化", ascending=True)

            raw_max = teacher_change_show["参与后完成率变化"].abs().max()
            max_val = max(raw_max * 1.15, 10)

            fig_teacher_finish_change = go.Figure()
            fig_teacher_finish_change.add_trace(go.Bar(
                x=[max_val] * len(teacher_change_show),
                y=teacher_change_show["老师姓名"],
                orientation="h",
                marker=dict(color="rgba(255,255,255,0.06)", line_width=0),
                showlegend=False,
                hoverinfo="skip"
            ))
            fig_teacher_finish_change.add_trace(go.Bar(
                x=[-max_val] * len(teacher_change_show),
                y=teacher_change_show["老师姓名"],
                orientation="h",
                marker=dict(color="rgba(255,255,255,0.06)", line_width=0),
                showlegend=False,
                hoverinfo="skip"
            ))

            for _, row in teacher_change_show.iterrows():
                color = COLOR_SECOND if row["参与后完成率变化"] >= 0 else COLOR_DANGER
                fig_teacher_finish_change.add_trace(go.Bar(
                    x=[row["参与后完成率变化"]],
                    y=[row["老师姓名"]],
                    orientation="h",
                    marker=dict(color=color, line_width=0),
                    text=f"{row['参与后完成率变化']:+.1f}%",
                    textposition="inside",
                    textfont=dict(color="#FFFFFF", size=11),
                    showlegend=False,
                    hovertemplate=f"{row['老师姓名']}: {row['参与后完成率变化']:+.1f}%<extra></extra>"
                ))

            fig_teacher_finish_change.update_layout(
                barmode="overlay",
                bargap=0.32,
                plot_bgcolor=CARD_BG,
                paper_bgcolor=CARD_BG,
                font=dict(color=TEXT_COLOR, size=11),
                height=right_chart_height,
                margin=dict(l=26, r=26, t=10, b=10),
                xaxis=dict(
                    range=[-max_val * 1.05, max_val * 1.05],
                    showgrid=False,
                    zeroline=True,
                    zerolinecolor="#D7E1EE",
                    zerolinewidth=1.2,
                    tickfont=dict(color=SUB_TEXT_COLOR, size=10),
                    showline=False
                ),
                yaxis=dict(
                    showgrid=False,
                    tickfont=dict(color=TEXT_COLOR, size=10),
                    categoryorder="array",
                    categoryarray=teacher_change_show["老师姓名"].tolist(),
                    automargin=True
                ),
                hoverlabel=dict(bgcolor=HOVER_BG, font_color=TEXT_COLOR, bordercolor=HOVER_BG)
            )

            try:
                fig_teacher_finish_change.update_layout(barcornerradius=999)
            except Exception:
                pass

            render_chart_card(fig_teacher_finish_change, title="参与后完成率变化（按老师）Top/Bottom")

    st.markdown("---")

    # =========================================================
    # 二、老师任务量 × 参与率分布（单校）
    # =========================================================
    st.markdown("### 📈 校内老师任务量 × 参与率分布")

    scatter_df = teacher_one_school.copy()

    required_cols = ["发布任务总数", "参与率"]
    missing_cols = [c for c in required_cols if c not in scatter_df.columns]
    if missing_cols:
        st.info(f"当前学校缺少字段：{', '.join(missing_cols)}，暂时无法展示。")
    else:
        teacher_name_col = None
        for col in ["老师姓名", "老师", "教师", "姓名"]:
            if col in scatter_df.columns:
                teacher_name_col = col
                break

        scatter_df["发布任务总数"] = pd.to_numeric(scatter_df["发布任务总数"], errors="coerce")
        scatter_df["参与率"] = pd.to_numeric(scatter_df["参与率"], errors="coerce")
        scatter_df = scatter_df.dropna(subset=["发布任务总数", "参与率"]).copy()

        if scatter_df.empty:
            st.info("暂无数据")
        else:
            filtered_df = scatter_df.copy()

            x_mid = filtered_df["发布任务总数"].median()
            y_mid = filtered_df["参与率"].median()

            def classify_teacher(row):
                if row["发布任务总数"] >= x_mid and row["参与率"] >= y_mid:
                    return "高效老师"
                elif row["发布任务总数"] < x_mid and row["参与率"] >= y_mid:
                    return "潜力老师"
                elif row["发布任务总数"] < x_mid and row["参与率"] < y_mid:
                    return "低活跃"
                else:
                    return "需跟进"

            filtered_df["象限类型"] = filtered_df.apply(classify_teacher, axis=1)

            quad_color_map = {
                "高效老师": "#5AD8A6",
                "潜力老师": "#F6BD60",
                "低活跃": "#8C9CB2",
                "需跟进": "#F08A8A"
            }

            quad_count = filtered_df["象限类型"].value_counts()
            total = len(filtered_df)
            high_ratio = quad_count.get("高效老师", 0) / total if total else 0
            follow_ratio = quad_count.get("需跟进", 0) / total if total else 0

            col_chart, col_text = st.columns([3.7, 1.3], gap="medium")

            # ================= 左：散点图 =================
            with col_chart:
                custom_cols = ["发布任务总数", "参与率", "象限类型"]
                if teacher_name_col:
                    custom_cols = [teacher_name_col] + custom_cols

                hovertemplate = ""
                idx = 0
                if teacher_name_col:
                    hovertemplate += f"<b>%{{customdata[{idx}]}}</b><br>"
                    idx += 1

                hovertemplate += (
                    f"发布任务数：%{{customdata[{idx}]:,.0f}}<br>"
                    f"参与率：%{{customdata[{idx + 1}]:.1f}}%<br>"
                    f"老师类型：%{{customdata[{idx + 2}]}}"
                    "<extra></extra>"
                )

                fig_scatter = px.scatter(
                    filtered_df,
                    x="发布任务总数",
                    y="参与率",
                    color="象限类型",
                    custom_data=custom_cols,
                    color_discrete_map=quad_color_map,
                    category_orders={"象限类型": ["高效老师", "潜力老师", "低活跃", "需跟进"]}
                )

                fig_scatter.update_traces(
                    marker=dict(
                        size=9,
                        opacity=0.82,
                        line=dict(width=0.8, color="rgba(255,255,255,0.18)")
                    ),
                    hovertemplate=hovertemplate
                )

                fig_scatter.add_vline(
                    x=x_mid,
                    line_width=1.2,
                    line_dash="dash",
                    line_color="rgba(22, 50, 79, 0.30)"
                )
                fig_scatter.add_hline(
                    y=y_mid,
                    line_width=1.2,
                    line_dash="dash",
                    line_color="rgba(22, 50, 79, 0.30)"
                )

                y_max = max(102, filtered_df["参与率"].max() + 3)
                x_min = min(0, filtered_df["发布任务总数"].min() - 0.5)
                x_max = filtered_df["发布任务总数"].max() + 1

                fig_scatter = style_figure(
                    fig_scatter,
                    x_title="发布任务总数",
                    y_title="参与率（%）",
                    legend_title="老师类型"
                )

                fig_scatter.update_layout(
                    height=290,
                    margin=dict(l=18, r=10, t=12, b=10),
                    showlegend=False
                )

                fig_scatter.update_yaxes(
                    range=[0, y_max],
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.05)",
                    zeroline=False
                )
                fig_scatter.update_xaxes(
                    range=[x_min, x_max],
                    showgrid=False,
                    zeroline=False
                )

                render_chart_card(fig_scatter)

            # ================= 右：说明栏 =================
            with col_text:
                st.markdown(f"""
<div style="height:300px;display:flex;flex-direction:column;justify-content:space-between;gap:12px;">

<div class="custom-analytic-card" style="
padding:12px 14px;
background:#F8FBFF;
border:1px solid #E5EAF3;
border-radius:12px;
color:#16324F;
font-size:13px;
line-height:1.7;
">
<div style="font-weight:700;margin-bottom:6px;">
当前校区：<span style="color:#60A5FA;">{selected_school}</span>
</div>
<div><span style="color:#5AD8A6;font-weight:700;">● 高效老师</span>：高任务量 + 高参与率</div>
<div><span style="color:#F6BD60;font-weight:700;">● 潜力老师</span>：低任务量 + 高参与率</div>
<div><span style="color:#8C9CB2;font-weight:700;">● 低活跃</span>：低任务量 + 低参与率</div>
<div><span style="color:#F08A8A;font-weight:700;">● 需跟进</span>：高任务量 + 低参与率</div>
</div>

<div class="custom-analytic-card" style="
padding:12px 14px;
background:linear-gradient(90deg, rgba(96,165,250,0.06), rgba(52,211,153,0.06));border:1px solid #E5EAF3;
border:1px solid rgba(255,255,255,0.08);
border-radius:12px;
color:#16324F;
font-size:13px;
line-height:1.75;
">
<div style="font-weight:700;margin-bottom:6px;">当前口径</div>
<div>任务量中位数 <b>{x_mid:.0f}</b>，参与率中位数 <b>{y_mid:.1f}%</b></div>
<div>
高效 <span style="color:#5AD8A6;font-weight:700;">{quad_count.get('高效老师', 0)}</span>，
潜力 <span style="color:#F6BD60;font-weight:700;">{quad_count.get('潜力老师', 0)}</span>，
低活跃 <span style="color:#8C9CB2;font-weight:700;">{quad_count.get('低活跃', 0)}</span>，
需跟进 <span style="color:#F08A8A;font-weight:700;">{quad_count.get('需跟进', 0)}</span>
</div>
<div>
高效占比 <span style="color:#5AD8A6;font-weight:700;">{high_ratio:.0%}</span>，
需跟进占比 <span style="color:#F08A8A;font-weight:700;">{follow_ratio:.0%}</span>
</div>
<div style="color:#6B7A90;margin-top:4px;">
建议优先关注需跟进人群，优化任务设计与完成链路。
</div>
</div>
</div>
""", unsafe_allow_html=True)
    st.markdown("---")

    # =========================================================
    # 三、校内分科目排行
    # =========================================================
    st.markdown("### 📚 校内分科目排行")

    if "科目" not in teacher_one_school.columns:
        st.info("当前老师数据缺少【科目】字段，暂时无法展示分科目排行。")
    else:
        school_subject_df = teacher_one_school.copy().dropna(subset=["科目"]).copy()

        if school_subject_df.empty:
            st.info("当前校区没有可用于分析的科目数据。")
        else:
            # ===== 聚合 =====
            school_summary = (
                school_subject_df.groupby("科目", as_index=False)[
                    ["接收任务学生数", "打开任务学生数", "完成任务学生数", "发布任务总数"]
                ]
                .sum()
            )

            school_summary["参与率"] = school_summary.apply(
                lambda x: x["打开任务学生数"] / x["接收任务学生数"] * 100
                if x["接收任务学生数"] else 0,
                axis=1
            )
            school_summary["参与后完成率"] = school_summary.apply(
                lambda x: x["完成任务学生数"] / x["打开任务学生数"] * 100
                if x["打开任务学生数"] else 0,
                axis=1
            )
            school_summary["收到后完成率"] = school_summary.apply(
                lambda x: x["完成任务学生数"] / x["接收任务学生数"] * 100
                if x["接收任务学生数"] else 0,
                axis=1
            )

            left_sub, right_sub = st.columns([1.15, 0.85], gap="large")

            # =========================
            # 左：排行卡片
            # =========================
            with left_sub:
                st.markdown("#### 分科目转化率排行")

                # 固定按参与率排序
                school_summary = school_summary.sort_values(
                    "参与率",
                    ascending=False
                ).reset_index(drop=True)

                rank_colors = ["#F59E0B", "#9CA3AF", "#CD7C3A"]

                rows_html_school = ""
                for i, row in school_summary.iterrows():
                    rate1 = row["参与率"]
                    rate2 = row["参与后完成率"]
                    task_cnt = row["发布任务总数"]
                    recv_cnt = row["接收任务学生数"]

                    rank = i + 1
                    badge_bg = rank_colors[rank - 1] if rank <= 3 else "#374151"
                    divider = "" if i == len(school_summary) - 1 else "border-bottom: 1px solid rgba(255,255,255,0.06);"

                    rows_html_school += f"""
<div class="rank-board-row" style="display:flex;align-items:center;padding:9px 10px;{divider}">
<div style="display:flex;align-items:center;gap:10px;flex:1.8;">
<div style="width:24px;height:24px;border-radius:6px;background:{badge_bg};color:white;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">{rank}</div>
<div>
<div style="font-size:13px;font-weight:600;color:#16324F;line-height:1.2;">{row['科目']}</div>
<div style="font-size:10px;color:#8FA3BF;margin-top:2px;line-height:1.2;">
    任务{task_cnt:.0f}｜接收{recv_cnt:.0f}
</div>
</div>
</div>

<div style="flex:0.8;text-align:center;">
<div style="font-size:13px;font-weight:700;color:#60A5FA;line-height:1.2;">{rate1:.1f}%</div>
<div style="font-size:9px;color:#8FA3BF;margin-top:1px;">参与率</div>
</div>

<div style="flex:0.8;text-align:center;">
<div style="font-size:13px;font-weight:700;color:#34D399;line-height:1.2;">{rate2:.1f}%</div>
<div style="font-size:9px;color:#8FA3BF;margin-top:1px;">参与后完成率</div>
</div>
</div>
"""

                full_html_school = f"""
<div class="rank-board-card" style="background:#F8FBFF;border:1px solid #E5EAF3;border-radius:14px;padding:10px 14px;min-height:260px;overflow:auto;">
    {rows_html_school}
</div>
"""
                st.markdown(full_html_school, unsafe_allow_html=True)

            # =========================
            # 右：摘要说明
            # =========================
            with right_sub:
                st.markdown("#### 科目表现摘要")

                top_subject = school_summary.iloc[0]["科目"]
                top_part = top_subject
                top_finish = school_summary.sort_values("参与后完成率", ascending=False).iloc[0]["科目"]

                avg_part = school_summary["参与率"].mean() if not school_summary.empty else 0
                avg_finish = school_summary["参与后完成率"].mean() if not school_summary.empty else 0

                st.markdown(f"""
<div style="display:flex;flex-direction:column;gap:12px;">

<div class="custom-analytic-card" style="padding:12px 14px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:12px;color:#16324F;font-size:13px;line-height:1.7;">
<div style="font-weight:700;margin-bottom:6px;">当前校区：<span style="color:#60A5FA;">{selected_school}</span></div>
<div>共覆盖 <b>{len(school_summary)}</b> 个科目。</div>
<div>平均参与率 <span style="color:#60A5FA;font-weight:700;">{avg_part:.1f}%</span></div>
<div>平均参与后完成率 <span style="color:#34D399;font-weight:700;">{avg_finish:.1f}%</span></div>
</div>

<div class="custom-analytic-card" style="padding:12px 14px;background:linear-gradient(90deg, rgba(96,165,250,0.06), rgba(52,211,153,0.06));border:1px solid #E5EAF3;border-radius:12px;color:#16324F;font-size:13px;line-height:1.75;">
<div style="font-weight:700;margin-bottom:6px;">关键观察</div>
<div>当前综合排序领先科目：<b>{top_subject}</b></div>
<div>参与率最高科目：<span style="color:#3B82F6;font-weight:700;">{top_part}</span></div>
<div>参与后完成率最高科目：<span style="color:#059669;font-weight:700;">{top_finish}</span></div>
<div style="color:#6B7A90;margin-top:4px;">可优先复用高表现科目的任务设计方式，再针对低表现科目优化触达与完成链路。</div>
</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📦 校内任务分析")

    if task_cur is None or task_cur.empty or task_30d is None or task_30d.empty:
        st.info("当前缺少任务数据，暂时无法展示任务渗透率和任务类型占比。")
    elif "学校" not in task_cur.columns or "学校" not in task_30d.columns:
        st.info("任务数据缺少【学校】字段，暂时无法展示校内任务分析。")
    else:
        school_task_cur = task_cur[task_cur["学校"] == selected_school].copy()
        school_task_30d = task_30d[task_30d["学校"] == selected_school].copy()

        if school_task_cur.empty or school_task_30d.empty:
            st.info(f"{selected_school} 当前没有可用于分析的任务数据。")
        else:
            for df in [school_task_cur, school_task_30d]:
                for col in ["接收任务学生数", "打开任务学生数", "完成任务学生数"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
                    else:
                        df[col] = 0

                if "任务类型" not in df.columns:
                    df["任务类型"] = "未分类"

                df["任务类型"] = df["任务类型"].fillna("未分类").astype(str).str.strip()

            # =========================
            # 老师主键
            # =========================
            def _teacher_key_series(df: pd.DataFrame) -> pd.Series:
                if "老师邮箱" in df.columns and df["老师邮箱"].notna().any():
                    return df["老师邮箱"].astype(str).str.strip().str.lower()
                if "老师姓名" in df.columns:
                    return df["老师姓名"].astype(str).str.strip()
                return pd.Series(["未知老师"] * len(df), index=df.index)

            school_task_cur["教师键"] = _teacher_key_series(school_task_cur)
            school_task_30d["教师键"] = _teacher_key_series(school_task_30d)

            # 当前校区近30天老师池
            teacher_pool_30d = school_task_30d["教师键"].nunique()

            # =========================
            # 任务类型汇总
            # =========================
            plot_summary = (
                school_task_cur.groupby("任务类型", as_index=False)
                .agg(
                    任务数=("任务类型", "count"),
                    接收任务学生数=("接收任务学生数", "sum"),
                    打开任务学生数=("打开任务学生数", "sum"),
                    完成任务学生数=("完成任务学生数", "sum"),
                    使用老师数=("教师键", "nunique")
                )
            )

            # 学生覆盖率（当前校区内按任务类型分布）
            total_receive = plot_summary["接收任务学生数"].sum()
            plot_summary["学生覆盖率"] = plot_summary["接收任务学生数"] / total_receive * 100 if total_receive > 0 else 0

            # 任务渗透率（近7天老师 / 近30天老师池）
            plot_summary["老师总数"] = teacher_pool_30d
            plot_summary["渗透率"] = plot_summary["使用老师数"] / teacher_pool_30d * 100 if teacher_pool_30d > 0 else 0

            # 参与率 / 完成率（可备用）
            plot_summary["参与率"] = plot_summary.apply(
                lambda x: x["打开任务学生数"] / x["接收任务学生数"] * 100 if x["接收任务学生数"] > 0 else 0,
                axis=1
            )
            plot_summary["参与后完成率"] = plot_summary.apply(
                lambda x: x["完成任务学生数"] / x["打开任务学生数"] * 100 if x["打开任务学生数"] > 0 else 0,
                axis=1
            )

            plot_summary = plot_summary.sort_values("任务数", ascending=False).reset_index(drop=True)

            # =========================
            # 配色
            # =========================
            TASK_SOLID_COLORS = [
                "#3B5998", "#7BCFA6", "#FF9900", "#B36D61", "#7F8EA3",
                "#5B79B8", "#4DAF8A", "#FFB84D", "#D08B80", "#9DAEC3",
                "#2A4070", "#6ABFA0"
            ]
            task_color_map = {
                task: TASK_SOLID_COLORS[i % len(TASK_SOLID_COLORS)]
                for i, task in enumerate(plot_summary["任务类型"].tolist())
            }

            # =========================
            # 第一行：占比 + 渗透率
            # =========================
            top_left, top_right = st.columns([1, 1], gap="large")

            with top_left:
                pie_df = plot_summary[["任务类型", "任务数"]].copy()
                total = pie_df["任务数"].sum()
                pie_df["占比"] = pie_df["任务数"] / total * 100 if total > 0 else 0
                pie_df = pie_df.sort_values("占比", ascending=False).reset_index(drop=True)

                top3 = pie_df.head(3)
                top_text = "、".join([
                    f"{row['任务类型']}（{row['占比']:.1f}%）"
                    for _, row in top3.iterrows()
                ]) if not top3.empty else "-"
                long_tail_ratio = pie_df["占比"].iloc[3:].sum() if len(pie_df) > 3 else 0

                st.markdown(f"""
<div class="custom-analytic-card task-type-summary-card" style="margin:6px 0 14px 0;padding:10px 14px;background:#F8FBFF;border:1px solid #E5EAF3;border-radius:12px;font-size:13px;line-height:1.6;color:#16324F;">
当前校区任务结构以 <b style="color:#7BCFA6;">{top_text}</b> 为主导，
Top3 合计占比约 <b>{top3['占比'].sum():.1f}%</b>；
其余类型占比约 <b>{long_tail_ratio:.1f}%</b>，
整体较为{"集中" if top3['占比'].sum() > 60 else "分散"}。
</div>
""", unsafe_allow_html=True)

                fig_pie = px.pie(
                    pie_df,
                    names="任务类型",
                    values="任务数",
                    hole=0.55,
                    color="任务类型",
                    color_discrete_map=task_color_map
                )
                fig_pie.update_layout(
                    plot_bgcolor=CARD_BG,
                    paper_bgcolor=CARD_BG,
                    font=dict(color=TEXT_COLOR),
                    height=320,
                    margin=dict(l=12, r=12, t=10, b=34),
                    legend=dict(
                        orientation="h",
                        y=-0.10,
                        x=0.5,
                        xanchor="center",
                        font=dict(size=10),
                        bgcolor="rgba(0,0,0,0)"
                    )
                )
                fig_pie.update_traces(
                    textposition="inside",
                    textinfo="percent",
                    marker=dict(line=dict(color="#FFFFFF", width=2))
                )
                render_chart_card(fig_pie, title="任务类型占比")

            with top_right:
                teacher_df = plot_summary[["任务类型", "渗透率", "使用老师数", "老师总数"]].copy()

                if teacher_df.empty:
                    st.info("暂无渗透率数据。")
                else:
                    teacher_df["渗透率"] = pd.to_numeric(teacher_df["渗透率"], errors="coerce").fillna(0)
                    teacher_df = teacher_df.sort_values("渗透率", ascending=False).reset_index(drop=True)
                    max_val = max(teacher_df["渗透率"].max(), 1)

                    rows_html = ""
                    for i, row in teacher_df.iterrows():
                        val = row["渗透率"]
                        bar_width = val / max_val * 60
                        color = task_color_map.get(row["任务类型"], TASK_SOLID_COLORS[i % len(TASK_SOLID_COLORS)])
                        count_text = f"{int(row['使用老师数'])}/{int(row['老师总数'])}"

                        rows_html += f"""
<div class="task-penetration-row">
<div style="width:88px;text-align:right;font-size:13px;color:#16324F;flex-shrink:0;">{row['任务类型']}</div>
<div class="task-penetration-track">
<div class="task-penetration-fill" style="width:{bar_width:.1f}%;background:{color};animation-delay:{0.08 + i * 0.05:.2f}s;">
<span style="font-size:12px;font-weight:700;color:white;white-space:nowrap;">{val:.1f}%</span>
</div>
</div>
<div style="font-size:12px;color:#8FA3BF;white-space:nowrap;width:80px;">{count_text}</div>
</div>
"""

                    st.markdown(f"""
<div class="custom-analytic-card task-penetration-card" style="background:#FFFFFF;border:1px solid #E5EAF3;border-radius:16px;padding:16px 20px;max-height:440px;overflow-y:auto;">
<div style="font-size:14px;font-weight:700;color:#16324F;margin-bottom:12px;">任务渗透率（近7天老师 / 近30天老师池）</div>
{rows_html}
</div>
""", unsafe_allow_html=True)
