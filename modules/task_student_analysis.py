import pandas as pd
import streamlit as st
import plotly.express as px
import html
import plotly.graph_objects as go

from utils.charts import style_figure, beautify_bar_chart, fix_pie, show_chart, TEXT_COLOR, CARD_BG, SUB_TEXT_COLOR, \
    HOVER_BG, render_chart_card, make_chart_pretty

COLOR_PRIMARY = "#3B5998"
COLOR_SECOND = "#7BCFA6"
COLOR_WARN = "#FF9900"
COLOR_DANGER = "#B36D61"
COLOR_NEUTRAL = "#7F8EA3"

def _format_big_num(v):
    if pd.isna(v):
        return "-"
    v = float(v)
    if v >= 10000:
        return f"{v / 10000:.1f}万"
    if v.is_integer():
        return f"{int(v):,}"
    return f"{v:,.1f}"


def _safe_change(cur, last):
    cur = pd.to_numeric(cur, errors="coerce")
    last = pd.to_numeric(last, errors="coerce")
    if pd.isna(cur) or pd.isna(last) or last == 0:
        return None
    return (cur - last) / last * 100

def _build_accuracy_band(val):
    if pd.isna(val):
        return "缺失"
    elif val >= 90:
        return "优秀（90-100）"
    elif val >= 70:
        return "良好（70-89）"
    elif val >= 50:
        return "一般（50-69）"
    else:
        return "较差（0-49）"

def build_task_type_board_data(
    df_task_cur: pd.DataFrame,
    df_task_last: pd.DataFrame,
    df_teacher_cur: pd.DataFrame,
    df_teacher_last: pd.DataFrame
):
    # ===== 当前期 =====
    cur_df = build_task_subject_df(df_task_cur, df_teacher_cur).copy()
    last_df = build_task_subject_df(df_task_last, df_teacher_last).copy()

    # ===== 学科归一 =====
    def normalize_subject(subject):
        if pd.isna(subject):
            return "其他"
        s = str(subject).strip().lower()
        if "语文" in s:
            return "语文"
        elif "数学" in s:
            return "数学"
        elif "英语" in s:
            return "英语"
        else:
            return "其他"

    for df in [cur_df, last_df]:
        df["科目"] = df["科目"].apply(normalize_subject)
        df["任务类型"] = df["任务类型"].fillna("未知").astype(str).str.strip()

    # ===== 当前：任务条数（关键！！）=====
    cur_summary = (
        cur_df.groupby(["科目", "任务类型"])
        .size()
        .reset_index(name="当前值")
    )

    # ===== 上期 =====
    last_summary = (
        last_df.groupby(["科目", "任务类型"])
        .size()
        .reset_index(name="上期值")
    )

    # ===== 合并 =====
    board_df = cur_summary.merge(
        last_summary,
        on=["科目", "任务类型"],
        how="left"
    )

    # ===== 环比 =====
    def safe_change(cur, last):
        if pd.isna(last) or last == 0:
            return None
        return (cur - last) / last * 100

    board_df["环比变化"] = board_df.apply(
        lambda row: safe_change(row["当前值"], row["上期值"]),
        axis=1
    )

    # ===== 重命名 =====
    board_df = board_df.rename(columns={
        "科目": "分组",
        "任务类型": "指标名"
    })

    # ===== 学科顺序 =====
    subject_order = ["英语", "语文", "数学", "其他"]
    board_df["分组"] = pd.Categorical(board_df["分组"], categories=subject_order, ordered=True)

    # ===== 每组取>100 =====
    threshold = 100
    board_df = board_df[board_df["当前值"] >= threshold]
    board_df = (
        board_df.sort_values(["分组", "当前值"], ascending=[True, False])
        .reset_index(drop=True)
    )

    # ===== 顶部总览 =====
    cur_total = len(cur_df)
    last_total = len(last_df)

    total_change = None
    if last_total != 0:
        total_change = (cur_total - last_total) / last_total * 100

    def format_big(v):
        if v >= 10000:
            return f"{v/10000:.1f}万"
        return f"{v:,}"

    summary = {
        "left_label": "上周任务总量",
        "left_value": format_big(last_total),
        "right_label": "本周任务总量",
        "right_value": format_big(cur_total),
        "change_text": "-" if total_change is None else f"{total_change:+.1f}%"
    }

    return board_df, summary

def render_task_type_metric_board(
    df: pd.DataFrame,
    summary: dict,
    cols_per_row: int = 5,
    card_height: int = 68
):
    st.caption("仅展示任务条数 ≥ 100 的任务类型")

    if df is None or df.empty:
        st.info("暂无数据")
        return

    plot_df = df.copy()
    plot_df["分组"] = plot_df["分组"].astype(str).str.strip().replace("nan", "其他")
    plot_df["指标名"] = plot_df["指标名"].fillna("未知").astype(str).str.strip()
    plot_df["当前值"] = pd.to_numeric(plot_df["当前值"], errors="coerce")
    plot_df["环比变化"] = pd.to_numeric(plot_df["环比变化"], errors="coerce")

    # 顶部总览卡
    left_label = html.escape(str(summary.get("left_label", "上期")))
    left_value = html.escape(str(summary.get("left_value", "-")))
    right_label = html.escape(str(summary.get("right_label", "本期")))
    right_value = html.escape(str(summary.get("right_value", "-")))
    change_text = html.escape(str(summary.get("change_text", "-")))

    change_color = "#4ADE80" if str(change_text).startswith("+") else "#F87171"

    summary_html = f"""
<div class="custom-analytic-card metric-summary-card" style="background:linear-gradient(90deg, rgba(226,236,248,0.90) 0%, rgba(240,245,252,0.95) 100%);border:1px solid #D6E2F0;border-radius:12px;padding:10px 16px;margin-bottom:12px;">
<div style="display:flex;justify-content:center;align-items:center;gap:28px;">
<div style="text-align:center;">
<div style="font-size:11px;color:#8FA3BF;font-weight:600;">{left_label}</div>
<div style="font-size:15px;color:#16324F;font-weight:800;line-height:1.3;">{left_value}</div>
</div>

<div style="display:flex;align-items:center;gap:10px;">
<div style="font-size:12px;color:#8FA3BF;">→</div>
<div style="font-size:11px;color:{change_color};background:#FFFFFF;border:1px solid #D7E1EE;padding:2px 8px;border-radius:999px;font-weight:700;">
{change_text}
</div>
</div>

<div style="text-align:center;"><div style="font-size:11px;color:#8FA3BF;font-weight:600;">{right_label}</div>
<div style="font-size:18px;color:#16324F;font-weight:800;line-height:1.3;">{right_value}</div>
</div>
</div>
</div>
"""
    st.markdown(summary_html, unsafe_allow_html=True)

    group_order = plot_df["分组"].drop_duplicates().tolist()

    group_colors = {
        "英语": "#60A5FA",
        "语文": "#84CC16",
        "数学": "#F97316",
        "其他": "#A78BFA",
        "未知": "#7F8EA3"
    }

    def get_card_style(change_val):
        # 默认蓝色卡
        style = {
            "bg": "linear-gradient(180deg, #F8FBFF 0%, #EEF4FB 100%)",
            "border": "#D7E1EE",
            "title": "#60A5FA",
            "value": "#16324F",
            "change": "#6B7A90",
        }

        if pd.isna(change_val):
            return style
        elif change_val >= 20:
            return {
                "bg": "linear-gradient(180deg, #FFF5F2 0%, #FCE9E3 100%)",
                "border": "#F0C7B8",
                "title": "#F97316",
                "value": "#16324F",
                "change": "#4ADE80",
            }
        elif change_val > 0:
            return {
                "bg": "linear-gradient(180deg, #F8FBFF 0%, #EAF3FF 100%)",
                "border": "#C9DCF3",
                "title": "#60A5FA",
                "value": "#16324F",
                "change": "#4ADE80",
            }
        else:
            return {
                "bg": "linear-gradient(180deg, #F7F9FC 0%, #EDF2F7 100%)",
                "border": "#D8E0EA",
                "title": "#93C5FD",
                "value": "#16324F",
                "change": "#F87171",
            }

    def format_change(v):
        if pd.isna(v):
            return "-"
        return f"{v:+.1f}%"

    sections_html = []
    for group_idx, group_name in enumerate(group_order):
        sub = plot_df[plot_df["分组"] == group_name].copy()
        if sub.empty:
            continue

        marker_color = group_colors.get(group_name, "#60A5FA")
        cards_html = []

        for card_idx, (_, row) in enumerate(sub.iterrows()):
            name = html.escape(str(row["指标名"]))
            value = row["当前值"]
            change_val = row["环比变化"]
            style = get_card_style(change_val)

            if pd.isna(value):
                value_text = "-"
            else:
                value_text = _format_big_num(value)

            change_text = format_change(change_val)
            delay = 0.05 * ((card_idx % cols_per_row) + 1)

            cards_html.append(
                f"""
<div class="metric-board-card" style="height:{card_height}px;border-radius:10px;background:{style['bg']};border:1px solid {style['border']};padding:8px 10px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;text-align:center;animation-delay:{delay:.2f}s;">
  <div style="font-size:10px;color:{style['title']};font-weight:700;line-height:1.2;margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;">{name}</div>
  <div style="font-size:15px;color:{style['value']};font-weight:800;line-height:1.2;margin-bottom:2px;">{value_text}</div>
  <div style="font-size:10px;color:{style['change']};font-weight:700;line-height:1.2;">{change_text}</div>
</div>
"""
            )

        sections_html.append(
            f"""
<div style="margin:12px 0 8px 0;display:flex;align-items:center;gap:6px;">
  <span style="width:8px;height:8px;border-radius:2px;background:{marker_color};display:inline-block;"></span>
  <span style="color:#16324F;font-size:13px;font-weight:700;">{html.escape(str(group_name))}</span>
</div>
<div style="display:grid;grid-template-columns:repeat({cols_per_row}, minmax(0, 1fr));gap:10px 12px;">
  {''.join(cards_html)}
</div>
"""
        )

    st.markdown("".join(sections_html), unsafe_allow_html=True)

def _safe_pct(numerator, denominator):
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")
    return (numerator / denominator * 100).fillna(0)


def _build_task_summary(df_task_cur, df_task_type_cur):
    """
    优先使用学校文件第2个sheet（学校×任务类型统计）
    若没有，再回退到任务明细表
    返回：
    task_summary: 任务类型汇总表
    task_data_source: 数据来源说明
    """
    task_summary = None
    task_data_source = ""

    # 方案A：优先使用学校文件第2个sheet
    if df_task_type_cur is not None and not df_task_type_cur.empty and "任务类型" in df_task_type_cur.columns:
        tmp = df_task_type_cur.copy()
        tmp["任务类型"] = tmp["任务类型"].fillna("未知").astype(str).str.strip()

        for col in ["任务总数", "接收任务学生数", "打开任务学生数", "完成任务学生数", "发布任务老师数"]:
            if col in tmp.columns:
                tmp[col] = pd.to_numeric(tmp[col], errors="coerce").fillna(0)
            else:
                tmp[col] = 0

        task_summary = (
            tmp.groupby("任务类型", as_index=False)
            .agg({
                "任务总数": "sum",
                "接收任务学生数": "sum",
                "打开任务学生数": "sum",
                "完成任务学生数": "sum",
                "发布任务老师数": "sum"
            })
            .rename(columns={"任务总数": "任务数"})
        )

        task_summary["参与率"] = _safe_pct(task_summary["打开任务学生数"], task_summary["接收任务学生数"])
        task_summary["参与后完成率"] = _safe_pct(task_summary["完成任务学生数"], task_summary["打开任务学生数"])
        task_summary["收到后完成率"] = _safe_pct(task_summary["完成任务学生数"], task_summary["接收任务学生数"])

        task_data_source = "学校数据文件第2个sheet（任务类型统计）"

    # 方案B：回退到任务明细
    if task_summary is None:
        task_cur = df_task_cur.copy()

        if "任务类型" not in task_cur.columns:
            return None, "无可用任务类型数据"

        task_cur["任务类型"] = task_cur["任务类型"].fillna("未知").astype(str).str.strip()

        for col in ["接收任务学生数", "打开任务学生数", "完成任务学生数"]:
            if col in task_cur.columns:
                task_cur[col] = pd.to_numeric(task_cur[col], errors="coerce").fillna(0)
            else:
                task_cur[col] = 0

        if "任务名称" not in task_cur.columns:
            task_cur["任务名称"] = ""

        if "老师邮箱" not in task_cur.columns:
            task_cur["老师邮箱"] = ""

        task_summary = (
            task_cur.groupby("任务类型", as_index=False)
            .agg({
                "任务名称": "count",
                "接收任务学生数": "sum",
                "打开任务学生数": "sum",
                "完成任务学生数": "sum",
                "老师邮箱": pd.Series.nunique
            })
            .rename(columns={
                "任务名称": "任务数",
                "老师邮箱": "发布任务老师数"
            })
        )

        task_summary["参与率"] = _safe_pct(task_summary["打开任务学生数"], task_summary["接收任务学生数"])
        task_summary["参与后完成率"] = _safe_pct(task_summary["完成任务学生数"], task_summary["打开任务学生数"])
        task_summary["收到后完成率"] = _safe_pct(task_summary["完成任务学生数"], task_summary["接收任务学生数"])

        task_data_source = "任务明细表聚合计算"

    return task_summary, task_data_source


def render_top_rank_card(title, items):
    st.markdown(f"#### {title}")

    if not items:
        st.info("暂无数据")
        return

    rank_colors = [COLOR_WARN, COLOR_NEUTRAL, "#CD7C3A"]

    rows_html = ""
    for i, (name, value_text, sub_text) in enumerate(items):
        rank = i + 1
        badge_bg = rank_colors[i] if i < 3 else "#374151"
        divider = "" if i == len(items) - 1 else "border-bottom: 1px solid #E5EAF3;"

        rows_html += f"""
    <div class="rank-board-row" style="display:flex;align-items:center;padding:10px 10px;{divider}">
    <!-- 左侧 -->
    <div style="display:flex;align-items:center;gap:10px;flex:1.5;">
    <div style="width:22px;height:22px;border-radius:6px;background:{badge_bg};color:white;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">{rank}
    </div>
    <div style="min-width:0;">
    <div style="font-size:13px;font-weight:600;color:#16324F;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}
    </div>
    <div style="font-size:9px;color:#6B7A90;margin-top:1px;">{sub_text}
    </div>
    </div>
    </div>
    <!-- 右侧数值 -->
    <div style="flex:0.8;text-align:right;">
    <div style="font-size:13px;font-weight:700;color:{COLOR_SECOND};line-height:1.2;">{value_text}
    </div>
    </div>
    </div>
    """

    full_html = f"""
    <div class="rank-board-card" style="background:#FFFFFF;border:1px solid #E5EAF3;border-radius:14px;padding:10px 14px;height:267px;overflow:auto;">
    {rows_html}
    </div>
    """
    st.markdown(full_html, unsafe_allow_html=True)


def build_task_subject_df(df_task: pd.DataFrame, df_teacher: pd.DataFrame) -> pd.DataFrame:
    task_df = df_task.copy()
    teacher_df = df_teacher.copy()

    # ===== 1. 清洗任务表 =====
    if "老师邮箱" in task_df.columns:
        task_df["老师邮箱"] = task_df["老师邮箱"].astype(str).str.strip().str.lower()
    if "老师姓名" in task_df.columns:
        task_df["老师姓名"] = task_df["老师姓名"].astype(str).str.strip()
    if "任务类型" in task_df.columns:
        task_df["任务类型"] = task_df["任务类型"].fillna("未知").astype(str).str.strip()
    else:
        task_df["任务类型"] = "未知"

    # ===== 2. 清洗老师表 =====
    if "老师邮箱" in teacher_df.columns:
        teacher_df["老师邮箱"] = teacher_df["老师邮箱"].astype(str).str.strip().str.lower()
    if "老师姓名" in teacher_df.columns:
        teacher_df["老师姓名"] = teacher_df["老师姓名"].astype(str).str.strip()

    if "科目" in teacher_df.columns:
        teacher_df["科目"] = teacher_df["科目"].fillna("未知").astype(str).str.strip()
    else:
        teacher_df["科目"] = "未知"

    if "学校" not in teacher_df.columns:
        for candidate in ["学校名称", "校区", "校区名称"]:
            if candidate in teacher_df.columns:
                teacher_df = teacher_df.rename(columns={candidate: "学校"})
                break

    if "学校" in teacher_df.columns:
        teacher_df["学校"] = teacher_df["学校"].fillna("未知").astype(str).str.strip()
    else:
        teacher_df["学校"] = "未知"

    # ===== 3. 只保留老师维表必要字段 =====
    teacher_cols = [c for c in ["老师邮箱", "老师姓名", "学校", "科目"] if c in teacher_df.columns]
    teacher_dim = teacher_df[teacher_cols].copy()

    # 去重，防止 merge 后行数膨胀
    if "老师邮箱" in teacher_dim.columns and teacher_dim["老师邮箱"].notna().any():
        teacher_dim = teacher_dim.drop_duplicates(subset=["老师邮箱"], keep="first")
    elif "老师姓名" in teacher_dim.columns:
        teacher_dim = teacher_dim.drop_duplicates(subset=["老师姓名"], keep="first")

    # ===== 4. 优先邮箱关联，其次姓名关联 =====
    if (
        "老师邮箱" in task_df.columns
        and "老师邮箱" in teacher_dim.columns
        and task_df["老师邮箱"].notna().any()
    ):
        merged = task_df.merge(
            teacher_dim,
            on="老师邮箱",
            how="left",
            suffixes=("", "_teacher")
        )

        if "老师姓名_teacher" in merged.columns:
            if "老师姓名" in merged.columns:
                merged["老师姓名"] = merged["老师姓名"].fillna(merged["老师姓名_teacher"])
            else:
                merged["老师姓名"] = merged["老师姓名_teacher"]
            merged = merged.drop(columns=["老师姓名_teacher"])

    elif "老师姓名" in task_df.columns and "老师姓名" in teacher_dim.columns:
        merged = task_df.merge(
            teacher_dim,
            on="老师姓名",
            how="left",
            suffixes=("", "_teacher")
        )
    else:
        merged = task_df.copy()
        merged["学校"] = "未知"
        merged["科目"] = "未知"

    # ===== 5. 缺失兜底 =====
    if "学校" not in merged.columns:
        merged["学校"] = "未知"
    else:
        merged["学校"] = merged["学校"].fillna("未知")

    if "科目" not in merged.columns:
        merged["科目"] = "未知"
    else:
        merged["科目"] = merged["科目"].fillna("未知")

    return merged

def render_task_student_analysis(
    df_task_cur: pd.DataFrame,
    df_task_last: pd.DataFrame,
    df_student_cur: pd.DataFrame,
    df_student_last: pd.DataFrame,
    df_teacher_cur: pd.DataFrame,
    df_teacher_last: pd.DataFrame,
    df_task_type_cur: pd.DataFrame = None,
    df_task_type_last: pd.DataFrame = None,
    df_task_30d=None
):

    # ===============================
    # 一、任务类型汇总表
    # ===============================
    TASK_CHARTS = [
        "任务类型占比",
        "任务量/参与率/完成率 TOP5",
        "学生覆盖率",
        "任务渗透率",
        "掉链子分析",
        "任务类型效果象限图",
        "任务类型活跃数据看板",
        "学员任务状态分布",
        "正确率分布",
        "做题数分布",
    ]
    if "task_selected_charts" not in st.session_state:
        st.session_state.task_selected_charts = TASK_CHARTS
    selected = st.multiselect(
        "选择展示的分析模块",
        TASK_CHARTS,
        default=st.session_state.task_selected_charts,
        key="task_chart_selector"
    )
    st.session_state.task_selected_charts = selected    

    task_subject_df = build_task_subject_df(df_task_cur, df_teacher_cur)
    task_summary, task_data_source = _build_task_summary(df_task_cur, df_task_type_cur)
    # ===== 总老师数（保留备用）=====
    if "老师邮箱" in df_teacher_cur.columns:
        total_teacher_cnt = df_teacher_cur["老师邮箱"].nunique()
    elif "老师姓名" in df_teacher_cur.columns:
        total_teacher_cnt = df_teacher_cur["老师姓名"].nunique()
    else:
        total_teacher_cnt = len(df_teacher_cur)
    # ===== 近30天各工具老师池 =====
    if df_task_30d is not None and not df_task_30d.empty and "任务类型" in df_task_30d.columns:
        id_col = "老师邮箱" if "老师邮箱" in df_task_30d.columns else "老师姓名"
        pool_df = (
            df_task_30d.groupby("任务类型")[id_col]
            .nunique()
            .reset_index()
            .rename(columns={id_col: "老师池"})
        )
        task_summary = task_summary.merge(pool_df, on="任务类型", how="left")
        task_summary["老师池"] = task_summary["老师池"].fillna(1).astype(int)
    else:
        task_summary["老师池"] = task_summary["发布任务老师数"].clip(lower=1).astype(int)

    # ===== 渗透率 = 本周使用老师数 / 近30天老师池 =====
    task_summary["渗透率"] = (
            task_summary["发布任务老师数"] / task_summary["老师池"] * 100
    ).clip(upper=100)

    # ↓ 在这里加上这两行
    task_summary["使用老师数"] = task_summary["发布任务老师数"].astype(int)
    task_summary["老师总数"] = task_summary["老师池"]
    if task_summary is None or task_summary.empty:
        st.warning("当前没有可用于展示的任务类型数据。")
        return

    task_summary = task_summary.copy()
    task_summary["任务类型"] = task_summary["任务类型"].fillna("未知").astype(str).str.strip()

    for col in ["任务数", "接收任务学生数", "打开任务学生数", "完成任务学生数", "发布任务老师数",
                "参与率", "参与后完成率", "收到后完成率"]:
        if col not in task_summary.columns:
            task_summary[col] = 0
        task_summary[col] = pd.to_numeric(task_summary[col], errors="coerce").fillna(0)

    # 学生覆盖率：用任务类型的接收学生数 / 全部任务类型接收学生数
    total_receive = task_summary["接收任务学生数"].sum()
    if total_receive > 0:
        task_summary["学生覆盖率"] = task_summary["接收任务学生数"] / total_receive * 100
    else:
        task_summary["学生覆盖率"] = 0

    # 为防止图太挤，默认只展示前12个任务类型
    task_summary = task_summary.sort_values("任务数", ascending=False)
    plot_summary = task_summary.head(12).copy()

    TASK_SOLID_COLORS = [
        "#3B5998", "#7BCFA6", "#FF9900", "#B36D61", "#7F8EA3",
        "#5B79B8", "#4DAF8A", "#FFB84D", "#D08B80", "#9DAEC3",
        "#2A4070", "#6ABFA0"
    ]
    plot_summary_sorted = plot_summary.sort_values("任务数", ascending=False).reset_index(drop=True)
    task_color_map = {
        row["任务类型"]: TASK_SOLID_COLORS[i % len(TASK_SOLID_COLORS)]
        for i, (_, row) in enumerate(plot_summary_sorted.iterrows())
    }
    # ===============================
    # 二、任务结构总览
    # ===============================
    st.markdown("""
        <hr style="
            height:0px;
            border:none;
            background-color:#EAF1FF;
            margin:0 0;
        ">
    """, unsafe_allow_html=True)

    st.markdown("### 📦任务层分析")
    if "任务类型占比" in selected or "任务量/参与率/完成率 TOP5" in selected:
        top_left, top_right = st.columns([1, 1], gap="large")
    TASK_COLORS = [
        "#6366F1", "#3B82F6", "#06B6D4", "#10B981",
        "#84CC16", "#F59E0B", "#F97316", "#EF4444",
        "#EC4899", "#8B5CF6", "#14B8A6", "#F43F5E"
    ]
    with top_left:
        if "任务类型占比" in selected:
            pie_df = plot_summary[["任务类型", "任务数"]].copy()
            total = pie_df["任务数"].sum()
            pie_df["占比"] = pie_df["任务数"] / total * 100
            pie_df = pie_df.sort_values("占比", ascending=False).reset_index(drop=True)

            # 给每个任务类型分配固定颜色

            top3 = pie_df.head(3)
            top_text = "、".join([
                f"{row['任务类型']}（{row['占比']:.1f}%）"
                for _, row in top3.iterrows()
            ])
            long_tail_ratio = pie_df["占比"].iloc[3:].sum()

            st.markdown(f"""
<div style="margin:6px 0 14px 0;padding:10px 14px;background:#F8FBFF;border:1px solid #E5EAF3;border-radius:12px;font-size:13px;line-height:1.6;color:#16324F;">
当前任务结构以 <b style="color:#7BCFA6;">{top_text}</b> 为主导，
合计占比约 <b>{top3['占比'].sum():.1f}%</b>；
其余类型占比约 <b>{long_tail_ratio:.1f}%</b>，
整体较为{"集中" if top3['占比'].sum() > 60 else "分散"}。
</div>
""", unsafe_allow_html=True)


            fig_pie = px.pie(
                pie_df,
                names="任务类型",
                values="任务数",
                hole=0.55,
                color_discrete_map=task_color_map
            )
            fig_pie = fix_pie(fig_pie)
            fig_pie.update_layout(
                title=dict(
                    text="任务类型占比（Top12）",
                    font=dict(size=14, color="#16324F"),
                    x=0.01,
                    xanchor="left",
                    y=0.97,
                    yanchor="top"
                ),
                margin=dict(l=12, r=12, t=50, b=34)
            )
            show_chart(fig_pie, chart_type="pie")

    with top_right:
        if "任务量/参与率/完成率 TOP5" in selected:
            rank_tabs = st.tabs(["任务量最多", "参与率最高", "完成率最高"])

            with rank_tabs[0]:
                top_task_count = (
                    task_summary.sort_values(["任务数", "参与率"], ascending=[False, False])
                    .head(5)
                )
                items = [
                    (
                        row["任务类型"],
                        f"{int(row['任务数']):,}",
                        f"接收学生数：{int(row['接收任务学生数']):,}"
                    )
                    for _, row in top_task_count.iterrows()
                ]
                render_top_rank_card("任务量 TOP5", items)

            with rank_tabs[1]:
                top_participation = (
                    task_summary[task_summary["任务数"] >= 5]
                    .sort_values(["参与率", "任务数"], ascending=[False, False])
                    .head(5)
                )
                items = [
                    (
                        row["任务类型"],
                        f"{row['参与率']:.1f}%",
                        f"任务数：{int(row['任务数']):,}"
                    )
                    for _, row in top_participation.iterrows()
                ]
                render_top_rank_card("参与率 TOP5", items)

            with rank_tabs[2]:
                top_completion = (
                    task_summary[task_summary["任务数"] >= 5]
                    .sort_values(["参与后完成率", "任务数"], ascending=[False, False])
                    .head(5)
                )
                items = [
                    (
                        row["任务类型"],
                        f"{row['参与后完成率']:.1f}%",
                        f"任务数：{int(row['任务数']):,}"
                    )
                    for _, row in top_completion.iterrows()
                ]
                render_top_rank_card("参与后完成率 TOP5", items)

    st.markdown("---")
    if "学生覆盖率" in selected or "任务渗透率" in selected:
        cov_left, cov_right = st.columns(2, gap="large")

        with cov_left:
            if "学生覆盖率" in selected:
                cover_df = plot_summary[["任务类型", "学生覆盖率"]].copy()

                if cover_df.empty:
                    st.info("暂无学生覆盖率数据。")
                else:
                    cover_df["学生覆盖率"] = pd.to_numeric(cover_df["学生覆盖率"], errors="coerce").fillna(0)
                    cover_df = cover_df.sort_values("学生覆盖率", ascending=False).reset_index(drop=True)
                    max_val = max(cover_df["学生覆盖率"].max(), 1)

                    rows_html = ""
                    for i, row in cover_df.iterrows():
                        val = row["学生覆盖率"]
                        bar_width = val / max_val * 60
                        color = task_color_map.get(row["任务类型"], TASK_SOLID_COLORS[i % len(TASK_SOLID_COLORS)])

                        rows_html += f"""
<div class="task-penetration-row">
<div style="width:80px;text-align:right;font-size:13px;color:#16324F;flex-shrink:0;">{row['任务类型']}</div>
<div class="task-penetration-track">
<div class="task-penetration-fill" style="width:{bar_width:.1f}%;background:{color};animation-delay:{0.08 + i * 0.05:.2f}s;">
  <span style="font-size:12px;font-weight:700;color:white;white-space:nowrap;">{val:.1f}%</span>
</div>
</div>
</div>
"""

                    st.markdown(f"""
<div class="custom-analytic-card task-penetration-card" style="background:#FFFFFF;border:1px solid #E5EAF3;border-radius:16px;padding:16px 20px;max-height:380px;overflow-y:auto;">
<div style="font-size:14px;font-weight:700;color:#16324F;margin-bottom:12px;">学生覆盖率</div>
{rows_html}
</div>
""", unsafe_allow_html=True)
            with cov_right:
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
<div style="width:80px;text-align:right;font-size:13px;color:#16324F;flex-shrink:0;">{row['任务类型']}</div>
<div class="task-penetration-track">
<div class="task-penetration-fill" style="width:{bar_width:.1f}%;background:{color};animation-delay:{0.08 + i * 0.05:.2f}s;">
<span style="font-size:12px;font-weight:700;color:white;white-space:nowrap;">{val:.1f}%</span>
</div>
</div>
<div style="font-size:12px;color:#8FA3BF;white-space:nowrap;width:80px;">{count_text}</div>
</div>
"""

                    st.markdown(f"""
<div class="custom-analytic-card task-penetration-card" style="background:#FFFFFF;border:1px solid #E5EAF3;border-radius:16px;padding:16px 20px;max-height:380px;overflow-y:auto;">
<div style="font-size:14px;font-weight:700;color:#16324F;margin-bottom:12px;">任务渗透率（近7天老师/近30天老师池）</div>
{rows_html}
</div>
""", unsafe_allow_html=True)
        st.markdown("---")

    # ===============================
    # 三、任务类型效果分析
    # ===============================
    if "掉链子分析" in selected or "任务类型效果象限图" in selected:
        effect_left, effect_right = st.columns([1, 1], gap="large")
    # =========================
    # 掉链子分析
    # =========================
    drop_summary = pd.DataFrame()
    fig_drop = None

    if "任务类型" in df_task_cur.columns:
        drop_df = df_task_cur.copy()
        drop_df["任务类型"] = drop_df["任务类型"].fillna("未知").astype(str).str.strip()

        for col in ["接收任务学生数", "打开任务学生数", "完成任务学生数"]:
            if col in drop_df.columns:
                drop_df[col] = pd.to_numeric(drop_df[col], errors="coerce").fillna(0)
            else:
                drop_df[col] = 0

        drop_summary = (
            drop_df.groupby("任务类型", as_index=False)
            .agg({
                "接收任务学生数": "sum",
                "打开任务学生数": "sum",
                "完成任务学生数": "sum"
            })
        )

        drop_summary["未打开流失"] = (
                drop_summary["接收任务学生数"] - drop_summary["打开任务学生数"]
        ).clip(lower=0)

        drop_summary["打开后未完成流失"] = (
                drop_summary["打开任务学生数"] - drop_summary["完成任务学生数"]
        ).clip(lower=0)

        drop_summary["总流失"] = (
                drop_summary["未打开流失"] + drop_summary["打开后未完成流失"]
        )

        drop_summary = (
            drop_summary.sort_values("总流失", ascending=False)
            .head(10)
            .sort_values("总流失", ascending=True)
            .reset_index(drop=True)
        )

        if not drop_summary.empty and drop_summary["总流失"].sum() > 0:
            fig_drop = go.Figure()

            fig_drop.add_trace(go.Bar(
                y=drop_summary["任务类型"],
                x=drop_summary["未打开流失"],
                name="未打开流失",
                orientation="h",
                marker=dict(color=COLOR_WARN, line=dict(width=0)),
                text=drop_summary["未打开流失"].apply(
                    lambda x: f"{int(x)}" if x >= drop_summary["总流失"].max() * 0.08 else ""
                ),
                textposition="inside",
                textfont=dict(color="#16324F", size=11),
                hovertemplate="任务类型：%{y}<br>未打开流失：%{x:,.0f} 人<extra></extra>"
            ))

            fig_drop.add_trace(go.Bar(
                y=drop_summary["任务类型"],
                x=drop_summary["打开后未完成流失"],
                name="打开后未完成流失",
                orientation="h",
                marker=dict(color=COLOR_DANGER, line=dict(width=0)),
                text=drop_summary["打开后未完成流失"].apply(
                    lambda x: f"{int(x)}" if x >= drop_summary["总流失"].max() * 0.08 else ""
                ),
                textposition="inside",
                textfont=dict(color="#FFFFFF", size=11),
                hovertemplate="任务类型：%{y}<br>打开后未完成流失：%{x:,.0f} 人<extra></extra>"
            ))

            fig_drop.add_trace(go.Scatter(
                y=drop_summary["任务类型"],
                x=drop_summary["总流失"] * 1.015,
                mode="text",
                text=drop_summary["总流失"].apply(lambda x: f"{int(x)}"),
                textfont=dict(color=TEXT_COLOR, size=11),
                textposition="middle right",
                showlegend=False,
                hoverinfo="skip"
            ))

            max_total = drop_summary["总流失"].max()

            fig_drop = make_chart_pretty(
                fig_drop,
                chart_type="hbar",
                height=320,
                x_title=None,
                y_title=None,
                legend_title=None,
                legend_top=True,
                margin=dict(l=20, r=36, t=40, b=18)
            )
            fig_drop.update_layout(title=dict(
                text="掉链子分析",
                font=dict(size=14, color="#16324F"),
                x=0.01, xanchor="left"
            ))

            fig_drop.update_layout(
                barmode="stack",
                bargap=0.34,
                bargroupgap=0.08,
                legend=dict(
                    title=None,
                    orientation="h",
                    yanchor="bottom",
                    y=1.03,
                    xanchor="right",
                    x=1,
                    font=dict(size=11),
                    bgcolor="rgba(0,0,0,0)"
                )
            )

            fig_drop.update_xaxes(
                range=[0, max_total * 1.15],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.06)",
                zeroline=False,
                tickfont=dict(color=SUB_TEXT_COLOR, size=11),
                separatethousands=True
            )

            fig_drop.update_yaxes(
                showgrid=False,
                tickfont=dict(color=TEXT_COLOR, size=12),
                automargin=True
            )

            try:
                fig_drop.update_traces(marker_line_width=0, cliponaxis=False)
                fig_drop.update_layout(barcornerradius=999)
            except Exception:
                pass
        with effect_left:
            if "掉链子分析" in selected:
                if fig_drop is None:
                    st.info("当前任务类型暂无明显流失数据。")
                else:
                    render_chart_card(fig_drop)

                    if not drop_summary.empty:
                        top_row = drop_summary.iloc[-1]  # 最大流失在最后一行
                        total_loss = int(drop_summary["总流失"].sum())

                        st.caption(
                            f"整体流失 {total_loss} 人，其中「{top_row['任务类型']}」流失最严重（{int(top_row['总流失'])} 人），主要集中在"
                            f"{'未打开环节' if top_row['未打开流失'] >= top_row['打开后未完成流失'] else '打开后未完成环节'}。"
                        )

        with effect_right:
            if "任务类型效果象限图" in selected:
                quad_df = task_summary.copy()
                quad_df = quad_df[quad_df["任务数"] >= 5].copy()

                if len(quad_df) < 2:
                    st.info("有效任务类型过少，暂时无法展示象限图。")
                else:
                    x_mid = quad_df["参与率"].median()
                    y_mid = quad_df["参与后完成率"].median()

                    def classify_quadrant(row):
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

                    quad_df["象限"] = quad_df.apply(classify_quadrant, axis=1)

                    fig_scatter = px.scatter(
                        quad_df,
                        x="参与率",
                        y="参与后完成率",
                        size="任务数",
                        color="象限",
                        color_discrete_map={
                            "高参与·高完成": COLOR_SECOND,
                            "高参与·低完成": COLOR_PRIMARY,
                            "低参与·高完成": COLOR_WARN,
                            "低参与·低完成": COLOR_DANGER
                        },
                        custom_data=["任务类型", "任务数"]  # ?关键
                    )
                    fig_scatter = style_figure(
                        fig_scatter,
                        x_title="参与率（%）",
                        y_title="参与后完成率（%）",
                        legend_title="象限",
                        height=300,
                        legend_top=False
                    )
                    fig_scatter.update_layout(
                        margin=dict(l=34, r=28, t=20, b=80),
                        title=dict(
                            text="任务类型效果象限图",
                            font=dict(size=14, color="#16324F"),
                            x=0.01,
                            xanchor="left",
                            y=0.97,
                            yanchor="top"
                        ),
                        legend=dict(
                            orientation="h",
                            y=-0.22,
                            x=0.5,
                            xanchor="center",
                            yanchor="top",
                            font=dict(size=11),
                            bgcolor="rgba(0,0,0,0)"
                        )
                    )
                    fig_scatter.update_traces(
                        hovertemplate=(
                            "任务类型：%{customdata[0]}<br>"
                            "参与率：%{x:.1f}%<br>"
                            "参与后完成率：%{y:.1f}%<br>"
                            "任务数：%{customdata[1]}<extra></extra>"
                        )
                    )

                    fig_scatter.add_vline(
                        x=x_mid,
                        line_width=1.2,
                        line_dash="dash",
                        line_color="rgba(22, 50, 79, 0.35)"
                    )
                    fig_scatter.add_hline(
                        y=y_mid,
                        line_width=1.2,
                        line_dash="dash",
                        line_color="rgba(22, 50, 79, 0.35)"
                    )
                    fig_scatter.update_xaxes(range=[0, 100])
                    fig_scatter.update_yaxes(range=[0, 100])

                    show_chart(fig_scatter, chart_type="scatter", height=320)
                    st.caption(f"划分口径：参与率中位数 {x_mid:.1f}%｜参与后完成率中位数 {y_mid:.1f}%")

    st.markdown("---")

    # ===============================
    # 四、任务类型活跃数据看板
    # ===============================
    if "任务类型活跃数据看板" in selected:
        st.markdown("#### 任务类型活跃数据看板")
        board_df, board_summary = build_task_type_board_data(
            df_task_cur=df_task_cur,
            df_task_last=df_task_last,
            df_teacher_cur=df_teacher_cur,
            df_teacher_last=df_teacher_last
        )

        render_task_type_metric_board(
            df=board_df,
            summary=board_summary,
            cols_per_row=6,
            card_height=84
        )

        st.markdown("""
<hr style="
height:0px;
border:none;
background-color:#EAF1FF;
margin:0 0;
">
""", unsafe_allow_html=True)

    # ===============================
    # 五、学生行为与学习质量（同一行）
    # ===============================

    student_cur = df_student_cur.copy()

    if "学员任务状态" in student_cur.columns:
        student_cur["学员任务状态"] = (
            student_cur["学员任务状态"]
            .fillna("未知")
            .astype(str)
            .str.strip()
            .replace("", "未知")
        )
    else:
        student_cur["学员任务状态"] = "未知"

    # =========================
    # 1. 学员任务状态分布
    # =========================
    status_df = student_cur["学员任务状态"].value_counts().reset_index()
    status_df.columns = ["学员任务状态", "人数"]

    fig_status = px.pie(
        status_df,
        names="学员任务状态",
        values="人数",
        hole=0.55
    )
    fig_status = fix_pie(fig_status)
    fig_status.update_layout(title=dict(
        text="学员任务状态",
        font=dict(size=14, color="#16324F"),
        x=0.01, xanchor="left", y=0.97, yanchor="top"
    ), margin=dict(l=12, r=12, t=50, b=34))



    # =========================
    # 2. 正确率分布
    # =========================
    acc_summary = pd.DataFrame()

    if "正确率" in student_cur.columns:
        acc_df = student_cur.copy()
        acc_df["正确率区间"] = acc_df["正确率"].apply(_build_accuracy_band)

        acc_summary = (
            acc_df["正确率区间"]
            .value_counts()
            .reindex(
                ["优秀（90-100）", "良好（70-89）", "一般（50-69）", "较差（0-49）", "缺失"],
                fill_value=0
            )
            .reset_index()
        )
        acc_summary.columns = ["正确率区间", "人数"]

    # =========================
    # 3. 做题数分布
    # =========================
    work_summary = pd.DataFrame()

    if "做题数" in student_cur.columns:
        work_df = student_cur.copy()
        work_df["做题数"] = pd.to_numeric(work_df["做题数"], errors="coerce").fillna(0)

        bins = [-1, 0, 5, 10, 20, 50, 999999]
        labels = ["0题", "1-5题", "6-10题", "11-20题", "21-50题", "50题以上"]
        work_df["做题数区间"] = pd.cut(work_df["做题数"], bins=bins, labels=labels)

        work_summary = (
            work_df["做题数区间"]
            .value_counts()
            .reindex(labels, fill_value=0)
            .reset_index()
        )
        work_summary.columns = ["做题数区间", "人数"]

    # =========================
    # 统一布局：四块放一行
    # =========================
    if "学员任务状态分布" in selected or "正确率分布" in selected or "做题数分布" in selected:
        st.markdown("### 👨‍🎓学生层分析")
        col1, col2, col3= st.columns(3, gap="small")

        with col1:
            if "学员任务状态分布" in selected:
                show_chart(
                    fig_status,
                    chart_type="pie"
                )

        with col2:
            if "正确率分布" in selected:
                if acc_summary.empty:
                    st.info("学生数据中缺少【正确率】字段，暂时无法展示正确率分布。")
                else:
                    acc_summary = acc_summary.copy()
                    acc_summary["人数"] = pd.to_numeric(acc_summary["人数"], errors="coerce").fillna(0)

                    # 固定顺序（很关键）
                    order = ["较差（0-49）", "一般（50-69）", "良好（70-89）", "优秀（90-100）"]
                    acc_summary["正确率区间"] = pd.Categorical(
                        acc_summary["正确率区间"],
                        categories=order,
                        ordered=True
                    )
                    acc_summary = acc_summary.sort_values("正确率区间").reset_index(drop=True)

                    max_val = max(acc_summary["人数"].max() * 1.15, 1)

                    fig_acc = go.Figure()

                    # =========================
                    # ① 背景轨道
                    # =========================
                    fig_acc.add_trace(go.Bar(
                        x=[max_val] * len(acc_summary),
                        y=acc_summary["正确率区间"],
                        orientation="h",
                        base=0,
                        marker=dict(color="rgba(255,255,255,0.07)", line_width=0),
                        showlegend=False,
                        hoverinfo="skip"
                    ))

                    # =========================
                    # ② 数据条
                    # =========================
                    for _, row in acc_summary.iterrows():
                        val = row["人数"]

                        color = COLOR_PRIMARY

                        fig_acc.add_trace(go.Bar(
                            x=[val],
                            y=[row["正确率区间"]],
                            orientation="h",
                            base=0,
                            marker=dict(color=color, line_width=0),
                            text=f"{int(val)}",
                            textposition="inside",
                            textfont=dict(color="#FFFFFF", size=11),
                            showlegend=False,
                            hovertemplate=f"{row['正确率区间']}: {int(val)}人<extra></extra>"
                        ))

                    fig_acc.update_layout(
                        barmode="overlay",
                        bargap=0.32,
                        plot_bgcolor=CARD_BG,
                        paper_bgcolor=CARD_BG,
                        font=dict(color=TEXT_COLOR, size=11),
                        height=280,
                        margin=dict(l=26, r=26, t=18, b=20),

                        xaxis=dict(
                            range=[0, max_val * 1.05],
                            showgrid=False,
                            zeroline=False,
                            tickfont=dict(color=SUB_TEXT_COLOR, size=11),
                            showline=False
                        ),

                        yaxis=dict(
                            showgrid=False,
                            tickfont=dict(color=TEXT_COLOR, size=11),
                            categoryorder="array",
                            categoryarray=acc_summary["正确率区间"].tolist(),
                            automargin=True
                        ),

                        hoverlabel=dict(
                            bgcolor=HOVER_BG,
                            font_color=TEXT_COLOR,
                            bordercolor=HOVER_BG
                        )
                    )

                    try:
                        fig_acc.update_layout(barcornerradius=999)
                    except Exception:
                        pass

                    fig_acc.update_layout(title=dict(
                        text="正确率分布",
                        font=dict(size=14, color="#16324F"),
                        x=0.01, xanchor="left"
                    ), margin=dict(l=26, r=26, t=50, b=20))
                    render_chart_card(fig_acc)

        with col3:
            if "做题数分布" in selected:
                if work_summary.empty:
                    st.info("学生数据中缺少【做题数】字段，暂时无法展示做题数分布。")
                else:
                    work_summary = work_summary.copy()
                    work_summary["人数"] = pd.to_numeric(work_summary["人数"], errors="coerce").fillna(0)

                    label_order = ["0题", "1-5题", "6-10题", "11-20题", "21-50题", "50题以上"]
                    work_summary["做题数区间"] = pd.Categorical(
                        work_summary["做题数区间"],
                        categories=label_order,
                        ordered=True
                    )
                    work_summary = work_summary.sort_values("做题数区间").reset_index(drop=True)

                    max_val = max(work_summary["人数"].max() * 1.15, 1)

                    fig_work = go.Figure()

                    # =========================
                    # ① 背景轨道（竖向）
                    # =========================
                    fig_work.add_trace(go.Bar(
                        x=work_summary["做题数区间"],
                        y=[max_val] * len(work_summary),
                        marker=dict(color="rgba(255,255,255,0.07)", line_width=0),
                        showlegend=False,
                        hoverinfo="skip"
                    ))

                    # =========================
                    # ② 实际数据柱
                    # =========================
                    fig_work.add_trace(go.Bar(
                        x=work_summary["做题数区间"],
                        y=work_summary["人数"],
                        marker=dict(color=COLOR_SECOND, line_width=0),
                        text=work_summary["人数"].apply(lambda x: f"{int(x)}"),
                        textposition="inside",
                        textfont=dict(color="#FFFFFF", size=11),
                        showlegend=False,
                        hovertemplate="%{x}: %{y}人<extra></extra>"
                    ))

                    fig_work.update_layout(
                        barmode="overlay",
                        bargap=0.35,
                        plot_bgcolor=CARD_BG,
                        paper_bgcolor=CARD_BG,
                        font=dict(color=TEXT_COLOR, size=11),
                        height=280,
                        margin=dict(l=20, r=20, t=18, b=20),

                        xaxis=dict(
                            showgrid=False,
                            tickfont=dict(color=TEXT_COLOR, size=11),
                            showline=False
                        ),

                        yaxis=dict(
                            range=[0, max_val * 1.05],
                            showgrid=False,
                            zeroline=False,
                            tickfont=dict(color=SUB_TEXT_COLOR, size=11)
                        ),

                        hoverlabel=dict(
                            bgcolor=HOVER_BG,
                            font_color=TEXT_COLOR,
                            bordercolor=HOVER_BG
                        )
                    )

                    try:
                        fig_work.update_layout(barcornerradius=999)
                    except Exception:
                        pass

                    fig_work.update_layout(title=dict(
                        text="做题数分布",
                        font=dict(size=14, color="#16324F"),
                        x=0.01, xanchor="left"
                    ), margin=dict(l=20, r=20, t=50, b=20))
                    render_chart_card(fig_work)
