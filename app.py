import streamlit as st
import pandas as pd
from io import BytesIO
from utils.charts import inject_chart_css

from utils.preprocess import (
    preprocess_task,
    preprocess_student,
    preprocess_teacher,
    get_analysis_periods,
    filter_by_date,
    build_teacher_dimension,
    attach_teacher_dimension,
    build_teacher_snapshot_from_task,
    build_school_snapshot_from_task,
    build_task_type_snapshot_from_task,
)
from modules.task_student_analysis import render_task_student_analysis
from modules.overview import render_overview
from modules.detail_analysis import render_detail_analysis
from modules.school_detail import render_school_detail_page

st.set_page_config(page_title="数据看板系统", layout="wide")

st.markdown("""
<style>

/* ========== 整体基础 ========== */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.stApp {
    background: #F7F9FC;
}

.chart-card {
    background: #FFFFFF;
    border: 1px solid rgba(59, 89, 152, 0.12);
    border-radius: 20px;
    padding: 14px 16px 8px 16px;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
    margin-bottom: 14px;
}

.ai-summary-card {
    margin: 8px 0 18px 0;
    padding: 16px 20px 16px 20px;
    border-radius: 20px;
    border: 1px solid rgba(59, 89, 152, 0.15);
    background: #FFFFFF;
    box-shadow: 0 16px 34px rgba(0, 0, 0, 0.06);
}

.ai-summary-title {
    color: #16324F;
    font-size: 15px;
    font-weight: 700;
    line-height: 1.3;
}

.ai-summary-toggle {
    color: #6B7A90;
    font-size: 11px;
    line-height: 1;
    margin-top: 2px;
}

.ai-summary-headline {
    color: #425466;
    font-size: 12.5px;
    line-height: 1.65;
    margin: 8px 0 12px 0;
    padding: 8px 12px;
    border-radius: 10px;
    background: rgba(0,0,0,0.02);
    border: 1px solid rgba(0,0,0,0.06);
}

.ai-summary-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
}

.ai-summary-col-title {
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 6px;
}

.ai-summary-col-title-good {
    color: #2D9E6B;
}

.ai-summary-col-title-warn {
    color: #D97706;
}

.ai-summary-col ul {
    list-style: none;
    margin: 0;
    padding: 0;
    color: #16324F;
    font-size: 12.5px;
}

.ai-summary-col li {
    padding: 5px 0;
    border-bottom: 1px solid rgba(0,0,0,0.05);
    line-height: 1.6;
}

.ai-summary-col li:last-child {
    border-bottom: none;
}

@media (max-width: 900px) {
    .ai-summary-grid {
        grid-template-columns: 1fr;
    }
}

/* ========== 干掉 Streamlit 顶部 ========== */
header[data-testid="stHeader"] {
    height: 0rem !important;
    min-height: 0rem !important;
    background: transparent !important;
}

.stAppHeader {
    background: transparent !important;
}

/* ========== 主容器 ========== */
.block-container {
    padding-top: 0.6rem !important;
    padding-bottom: 1.2rem !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    max-width: 100% !important;
}

/* ========== 标题 ========== */
h1, h2, h3 {
    color: #16324F !important;
    font-weight: 700 !important;
    line-height: 1.25 !important;
    margin-bottom: 0.5rem !important;
}

h1 { font-size: 24px !important; }
h2 { font-size: 20px !important; }
h3 { font-size: 17px !important; }
h4 { font-size: 15px !important; color: #16324F !important; }

p {
    color: #16324F;
    font-size: 13px !important;
}

label {
    color: #16324F;
    font-size: 13px !important;
}

[data-testid="stCaptionContainer"] {
    color: #6B7A90 !important;
    font-size: 12px !important;
}

/* ========== 顶部导航 ========== */
.top-nav-wrap {
    position: sticky;
    top: 0;
    z-index: 999;
    background: rgba(247, 249, 252, 0.95);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid rgba(0,0,0,0.08);
    padding: 8px 0 12px 0;
    margin: 0 0 0.8rem 0;
}

.top-nav-title {
    font-size: 24px !important;
    font-weight: 600 !important;
    color: #16324F !important;
    line-height: 1.1 !important;
    margin: 0 !important;
}

/* ========== 按钮 ========== */
div[data-testid="stButton"] > button {
    height: 38px !important;
    min-height: 38px !important;
    border-radius: 10px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    border: 1px solid rgba(0,0,0,0.10) !important;
    background: rgba(0,0,0,0.02) !important;
    color: #16324F !important;
}

div[data-testid="stButton"] > button:hover {
    border: 1px solid rgba(59, 89, 152, 0.35) !important;
    background: rgba(59, 89, 152, 0.05) !important;
}

div[data-testid="stButton"] > button[kind="primary"] {
    background: rgba(59, 89, 152, 0.12) !important;
    border: 1px solid rgba(59, 89, 152, 0.40) !important;
    color: #16324F !important;
}

/* ===== selectbox ===== */
div[data-baseweb="select"] > div {
    min-height: 38px !important;
    height: 38px !important;
    border-radius: 10px !important;
    background: #FFFFFF !important;
    border: 1px solid rgba(0,0,0,0.10) !important;
}

div[data-baseweb="select"] * {
    font-size: 12px !important;
}

div[data-baseweb="select"] div[role="combobox"] {
    font-size: 12px !important;
    color: #16324F !important;
    line-height: 1.2 !important;
}

div[data-baseweb="select"] input {
    font-size: 12px !important;
    color: #16324F !important;
}

div[data-baseweb="select"] input::placeholder {
    font-size: 12px !important;
    color: #6B7A90 !important;
}

div[role="listbox"] * {
    font-size: 12px !important;
}

div[data-baseweb="select"] svg {
    width: 18px !important;
    height: 18px !important;
}

/* ========== KPI 卡片 ========== */
div[data-testid="stMetric"] {
    border: 1px solid rgba(0,0,0,0.06) !important;
    border-radius: 14px !important;
    background: #FFFFFF !important;
    padding: 14px 16px !important;
    transition: transform 0.24s cubic-bezier(0.22, 1, 0.36, 1),
                box-shadow 0.24s ease,
                border-color 0.24s ease !important;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-4px);
    border-color: rgba(59, 89, 152, 0.20) !important;
    background: #FFFFFF !important;
    box-shadow: 0 14px 30px rgba(15, 23, 42, 0.08) !important;
}

div[data-testid="stMetric"] label[data-testid="stMetricLabel"] {
    font-size: 12px !important;
    color: #6B7A90 !important;
}

div[data-testid="stMetric"] div[data-testid="stMetricValue"],
div[data-testid="stMetric"] div[data-testid="stMetricValue"] * {
    font-size: 26px !important;
    font-weight: 200 !important;
    color: #16324F !important;
    line-height: 1.1 !important;
}

/* ========== 分割线 ========== */
hr {
    border: none !important;
    border-top: 1px solid rgba(0,0,0,0.08) !important;
    margin: 1rem 0 !important;
}

/* ========== 列间距 ========== */
[data-testid="column"] {
    padding-left: 4px !important;
    padding-right: 4px !important;
}

/* ========== 表格 ========== */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(0,0,0,0.06) !important;
    border-radius: 12px !important;
}

</style>
""", unsafe_allow_html=True)


# ================= 页面状态 =================
default_session_keys = [
    "uploaded",
    "data_source",

    "teacher_file",
    "task_file",
    "student_file",

    "teacher_file_bytes",
    "task_file_bytes",
    "student_file_bytes",

    "analysis_anchor_date",
    "pending_anchor_date",
]

for key in default_session_keys:
    if key not in st.session_state:
        if key == "uploaded":
            st.session_state[key] = False
        elif key == "data_source":
            st.session_state[key] = "上传文件"
        elif key == "analysis_anchor_date":
            st.session_state[key] = pd.Timestamp.today().date()
        else:
            st.session_state[key] = None

# ================= 初始化session_state =================
if "page_mode" not in st.session_state:
    st.session_state.page_mode = "national"   # national / school_detail

if "selected_school" not in st.session_state:
    st.session_state.selected_school = None
if "top_nav_mode" not in st.session_state:
    st.session_state.top_nav_mode = "overview"   # overview / school / teacher

if "selected_school" not in st.session_state:
    st.session_state.selected_school = None

if "school_search_keyword" not in st.session_state:
    st.session_state.school_search_keyword = ""

# ================= 工具函数 =================
def load(file):
    """读取上传文件（单sheet或普通文件）"""
    if file is None:
        return None

    file.seek(0)

    if file.name.lower().endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)


# def load_school_with_task_type(file):
#     """
#     读取学校数据文件：
#     sheet1 = 学校总表
#     sheet2 = 任务类型统计表
#     """
#     if file is None:
#         return None, None
#
#     file.seek(0)
#
#     if file.name.lower().endswith(".csv"):
#         df_school = pd.read_csv(file)
#         df_task_type = None
#         return df_school, df_task_type
#
#     xls = pd.ExcelFile(file)
#
#     df_school = pd.read_excel(xls, sheet_name=0)
#
#     df_task_type = None
#     if len(xls.sheet_names) > 1:
#         df_task_type = pd.read_excel(xls, sheet_name=1)
#
#     return df_school, df_task_type


# def preprocess_teacher(df: pd.DataFrame) -> pd.DataFrame:
#     df = df.copy()
#
#     percent_cols = ["参与率", "参与后完成率", "收到后完成率"]
#     numeric_cols = ["发布任务总数", "接收任务学生数", "打开任务学生数", "完成任务学生数"]
#
#     for col in percent_cols:
#         if col in df.columns:
#             df[col] = df[col].astype(str).str.replace("%", "", regex=False).str.strip()
#             df[col] = pd.to_numeric(df[col], errors="coerce")
#
#     for col in numeric_cols:
#         if col in df.columns:
#             df[col] = df[col].astype(str).str.replace(",", "", regex=False).str.strip()
#             df[col] = pd.to_numeric(df[col], errors="coerce")
#
#     return df


def file_to_bytes(uploaded_file):
    if uploaded_file is None:
        return None
    uploaded_file.seek(0)
    return {
        "name": uploaded_file.name,
        "data": uploaded_file.read()
    }


@st.cache_data(show_spinner=False)
def load_table_from_bytes(file_dict):
    if file_dict is None:
        return None

    bio = BytesIO(file_dict["data"])
    filename = file_dict["name"]

    if filename.lower().endswith(".csv"):
        return pd.read_csv(bio)
    return pd.read_excel(bio)

@st.cache_data(show_spinner=False)
def load_table_selected_cols_from_bytes(file_dict, cols):
    if file_dict is None:
        return pd.DataFrame()

    bio = BytesIO(file_dict["data"])
    filename = file_dict["name"]

    try:
        if filename.lower().endswith(".csv"):
            return pd.read_csv(bio, usecols=lambda c: c in cols)
        return pd.read_excel(bio, usecols=lambda c: c in cols)
    except Exception:
        # 兜底：如果 usecols 因列名问题失败，退回全量读取
        bio.seek(0)
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(bio)
        else:
            df = pd.read_excel(bio)
        keep_cols = [c for c in cols if c in df.columns]
        return df[keep_cols]
    
@st.cache_data(show_spinner=False)
def get_teacher_df(file_bytes):
    return preprocess_teacher(load_table_from_bytes(file_bytes))


@st.cache_data(show_spinner=False)
def get_task_df(file_bytes):
    return preprocess_task(load_table_from_bytes(file_bytes))


@st.cache_data(show_spinner=False)
def get_student_df(file_bytes):
    STUDENT_COLS = [
        "发布时间", "完成时间",
        "老师邮箱", "老师姓名", "任务类型",
        "学员号", "学员任务状态",
        "正确率", "做题数"
    ]
    raw = load_table_selected_cols_from_bytes(file_bytes, STUDENT_COLS)
    return preprocess_student(raw)


@st.cache_data(show_spinner=False)
def load_all_data(
    teacher_file_bytes,
    task_file_bytes,
    student_file_bytes,
    analysis_anchor_date,
):
    # ================= 先初始化，避免局部变量未赋值 =================
    df_teacher_all = pd.DataFrame()
    teacher_dim = pd.DataFrame()

    df_task_all_raw = pd.DataFrame()
    df_task_all = pd.DataFrame()
    df_task_30d = pd.DataFrame()
    df_task_cur = pd.DataFrame()
    df_task_last = pd.DataFrame()

    df_student_all = pd.DataFrame()
    df_student_30d = pd.DataFrame()
    df_student_cur = pd.DataFrame()
    df_student_last = pd.DataFrame()

    df_teacher_cur = pd.DataFrame()
    df_teacher_last = pd.DataFrame()
    df_school_cur = pd.DataFrame()
    df_school_last = pd.DataFrame()
    df_task_type_cur = pd.DataFrame()
    df_task_type_last = pd.DataFrame()

    # ================= 周期 =================
    periods = get_analysis_periods(analysis_anchor_date)

    # ================= 原始数据 =================
    if teacher_file_bytes is not None:
        df_teacher_all = get_teacher_df(teacher_file_bytes)

    if task_file_bytes is not None:
        df_task_all_raw = get_task_df(task_file_bytes)

    if student_file_bytes is not None:
        df_student_all = get_student_df(student_file_bytes)
        # # 只保留实际存在的列
        # keep_cols = [c for c in STUDENT_COLS if c in raw_student.columns]
        # df_student_all = get_student_df(student_file_bytes)

    # ================= 老师维表 + 任务挂维 =================
    if not df_teacher_all.empty:
        teacher_dim = build_teacher_dimension(df_teacher_all)

    if not df_task_all_raw.empty:
        df_task_all = attach_teacher_dimension(df_task_all_raw, teacher_dim)


    # ================= 30天全集 =================
    if not df_task_all.empty:
        df_task_30d = filter_by_date(
            df_task_all,
            periods["rolling_30_start"],
            periods["rolling_30_end"]
        )

    if not df_student_all.empty:
        df_student_30d = filter_by_date(
            df_student_all,
            periods["rolling_30_start"],
            periods["rolling_30_end"]
        )

    # ================= 本周 / 上周任务 =================
    if not df_task_30d.empty:
        df_task_cur = filter_by_date(
            df_task_30d,
            periods["cur_start"],
            periods["cur_end"]
        )
        df_task_last = filter_by_date(
            df_task_30d,
            periods["last_start"],
            periods["last_end"]
        )

    # ================= 本周 / 上周学生 =================
    if not df_student_30d.empty:
        df_student_cur = filter_by_date(
            df_student_30d,
            periods["cur_start"],
            periods["cur_end"]
        )
        df_student_last = filter_by_date(
            df_student_30d,
            periods["last_start"],
            periods["last_end"]
        )

    # ================= 从任务反推老师 / 学校 / 任务类型 =================
    if not df_task_cur.empty:
        df_teacher_cur = build_teacher_snapshot_from_task(df_task_cur, teacher_dim)
        df_school_cur = build_school_snapshot_from_task(df_task_cur, teacher_dim)
        df_task_type_cur = build_task_type_snapshot_from_task(df_task_cur, teacher_dim)

    if not df_task_last.empty:
        df_teacher_last = build_teacher_snapshot_from_task(df_task_last, teacher_dim)
        df_school_last = build_school_snapshot_from_task(df_task_last, teacher_dim)
        df_task_type_last = build_task_type_snapshot_from_task(df_task_last, teacher_dim)

    return {
        "df_teacher_all": df_teacher_all,
        "teacher_dim": teacher_dim,

        "df_task_30d": df_task_30d,
        "df_student_30d": df_student_30d,

        "df_school_cur": df_school_cur,
        "df_school_last": df_school_last,
        "df_teacher_cur": df_teacher_cur,
        "df_teacher_last": df_teacher_last,
        "df_task_cur": df_task_cur,
        "df_task_last": df_task_last,
        "df_student_cur": df_student_cur,
        "df_student_last": df_student_last,
        "df_task_type_cur": df_task_type_cur,
        "df_task_type_last": df_task_type_last,

        "periods": periods,
    }


def reset_upload_state():
    st.session_state.uploaded = False
    st.session_state.auto_aligned = False
    st.session_state.teacher_file = None
    st.session_state.task_file = None
    st.session_state.student_file = None

    st.session_state.teacher_file_bytes = None
    st.session_state.task_file_bytes = None
    st.session_state.student_file_bytes = None

    st.session_state.page_mode = "national"
    st.session_state.top_nav_mode = "overview"
    st.session_state.selected_school = None
    st.session_state.school_search_keyword = ""
    st.session_state.analysis_anchor_date = pd.Timestamp.today().date()

    load_all_data.clear()


# ================= 上传模式 =================
def render_upload_mode():
    st.markdown("## 📂 上传数据")
    st.markdown("""
    <div style="
    background:#EAF2FF;
    padding:16px 18px;
    border-radius:16px;
    font-size:13px;
    line-height:1.8;
    color:#16324F;
    white-space:normal;
    word-break:break-word;
    margin-bottom:12px;
    ">
    请上传近30天老师数据、任务数据、学生数据。系统会根据你选择的分析截止日期，自动切分：本周（上周五~本周四）和上周（上上周五~上周四），并生成近30天趋势。
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### 分析参数")

        def on_anchor_date_change():
            st.session_state.analysis_anchor_date = st.session_state.anchor_date_input

        analysis_anchor_date = st.date_input(
            "分析截止日期",
            value=st.session_state.analysis_anchor_date,
            key="anchor_date_input",
            on_change=on_anchor_date_change,
            help="系统会自动定位到最近一个已完成的周四，并生成本周/上周窗口"
        )

    with c2:
        periods = get_analysis_periods(st.session_state.get("anchor_date_input", st.session_state.analysis_anchor_date))
        st.markdown("### 口径预览")
        st.caption(
            f"本周：{periods['cur_start'].date()} ~ {periods['cur_end'].date()} ｜ "
            f"上周：{periods['last_start'].date()} ~ {periods['last_end'].date()} ｜ "
            f"近30天：{periods['rolling_30_start'].date()} ~ {periods['rolling_30_end'].date()}"
        )

    up1, up2, up3 = st.columns(3)

    with up1:
        st.markdown("### 老师数据")
        teacher_file = st.file_uploader("上传【近30天-老师数据】", key="teacher_month")

    with up2:
        st.markdown("### 任务数据")
        task_file = st.file_uploader("上传【近30天-任务数据】", key="task_month")

    with up3:
        st.markdown("### 学生数据（建议 CSV）")
        student_file = st.file_uploader("上传【近30天-学生数据】", key="student_month")

    ready = teacher_file is not None and task_file is not None and student_file is not None

    if ready:
        st.session_state.teacher_file = teacher_file
        st.session_state.task_file = task_file
        st.session_state.student_file = student_file

        st.session_state.teacher_file_bytes = file_to_bytes(teacher_file)
        st.session_state.task_file_bytes = file_to_bytes(task_file)
        st.session_state.student_file_bytes = file_to_bytes(student_file)

        # ===== 自动对齐分析日期（轻量 + 只执行一次）=====
        if "auto_aligned" not in st.session_state:
            raw_task = load_table_from_bytes(st.session_state.task_file_bytes)

            if raw_task is not None and "任务发布时间" in raw_task.columns:
                task_dates = pd.to_datetime(raw_task["任务发布时间"], errors="coerce")
                max_task_date = task_dates.max()

                if pd.notna(max_task_date):
                    st.session_state.analysis_anchor_date = max_task_date.date()

            st.session_state.auto_aligned = True

        st.session_state.uploaded = True
        st.session_state.page_mode = "national"
        st.session_state.top_nav_mode = "overview"
        st.session_state.selected_school = None
        st.session_state.school_search_keyword = ""

        load_all_data.clear()

        st.success("上传成功，正在进入可视化界面...")
        st.rerun()
    else:
        uploaded_count = sum([teacher_file is not None, task_file is not None, student_file is not None])
        if uploaded_count > 0:
            st.warning("请把 3 份近30天数据上传完整后进入看板。")


# ================= 接口模式 =================
def render_api_mode():
    st.markdown("## 🔌 接口拉取")
    st.info("该模式用于后续直接从业务系统拉取数据。当前版本先预留参数入口。")

    col1, col2 = st.columns(2)
    with col1:
        st.date_input("开始日期", key="api_start_date")
    with col2:
        st.date_input("结束日期", key="api_end_date")

    st.markdown("### 可选筛选")
    col3, col4 = st.columns(2)
    with col3:
        st.text_input("学校关键词（可选）", key="api_school_keyword")
    with col4:
        st.text_input("老师关键词（可选）", key="api_teacher_keyword")

    st.caption(
        "后续可在这里接入真实接口逻辑：根据时间范围与筛选条件，自动获取学校、老师、任务和学生数据。"
    )

    if st.button("获取并分析", use_container_width=True):
        st.warning("当前版本暂未接入真实接口，请先使用【上传文件】模式。")


# ================= 输入页 =================
def render_input_page():
    st.title("📊 作业任务数据看板")
    render_upload_mode()

# ================= 看板页 =================
def render_dashboard():
    try:
        inject_chart_css()
        with st.spinner("正在加载数据并构建看板，请稍候..."):
            data = load_all_data(
                st.session_state.teacher_file_bytes,
                st.session_state.task_file_bytes,
                st.session_state.student_file_bytes,
                st.session_state.analysis_anchor_date,  # 这个值只由上传时和on_change回调来修改
            )

            df_school_cur = data["df_school_cur"]
            df_school_last = data["df_school_last"]
            df_teacher_cur = data["df_teacher_cur"]
            df_teacher_last = data["df_teacher_last"]
            df_task_cur = data["df_task_cur"]
            df_task_last = data["df_task_last"]
            df_student_cur = data["df_student_cur"]
            df_student_last = data["df_student_last"]
            df_task_type_cur = data["df_task_type_cur"]
            df_task_type_last = data["df_task_type_last"]
            df_task_30d = data["df_task_30d"]
            periods = data["periods"]

            # st.caption(
            #     f"task_30d={len(df_task_30d)} | "
            #     f"task_cur={len(df_task_cur)} | task_last={len(df_task_last)} | "
            #     f"school_cur={len(df_school_cur)} | school_last={len(df_school_last)} | "
            #     f"teacher_cur={len(df_teacher_cur)} | teacher_last={len(df_teacher_last)}"
            # )
        # ================= 顶部导航栏 =================
        st.markdown('<div class="top-nav-wrap">', unsafe_allow_html=True)

        nav_left, nav_mid, nav_right = st.columns([2.2, 3.8, 2.8])

        with nav_left:
            st.markdown('<div class="top-nav-title">🏠 作业任务数据看板</div>', unsafe_allow_html=True)

        with nav_mid:
            nav1, nav2 = st.columns(2)

            with nav1:
                if st.button(
                        "整体看板",
                        key="top_nav_overview",
                        use_container_width=True,
                        type="primary" if st.session_state.top_nav_mode == "overview" else "secondary"
                ):
                    st.session_state.top_nav_mode = "overview"
                    st.rerun()

            with nav2:
                if st.button(
                        "学校报告",
                        key="top_nav_school",
                        use_container_width=True,
                        type="primary" if st.session_state.top_nav_mode == "school" else "secondary"
                ):
                    st.session_state.top_nav_mode = "school"
                    st.rerun()

        with nav_right:
            if "学校" in df_school_cur.columns:
                school_options = sorted(
                    df_school_cur[df_school_cur["学校"] != "全国"]["学校"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )
            else:
                school_options = []
            st.caption(
                f"本周：{periods['cur_start'].date()} ~ {periods['cur_end'].date()} ｜ "
                f"上周：{periods['last_start'].date()} ~ {periods['last_end'].date()} ｜ "
                f"月：{periods['rolling_30_start'].date()} ~ {periods['rolling_30_end'].date()}"
            )

            tool_left, tool_right = st.columns([5.0, 1.1], gap="small")

            with tool_left:
                selected_school = st.selectbox(
                    "搜索或选择学校",
                    options=[""] + school_options,
                    index=(school_options.index(st.session_state.selected_school) + 1)
                    if st.session_state.selected_school in school_options else 0,
                    key="top_school_selector"
                )

                if selected_school:
                    st.session_state.selected_school = selected_school

            with tool_right:
                st.write("")
                st.write("")
                if st.button("🔄 重置", key="reload_data_btn", use_container_width=True):
                    reset_upload_state()
                    st.rerun()

        # ================= 顶部导航分发 =================
        if st.session_state.top_nav_mode == "overview":
            if df_task_cur.empty and df_task_last.empty:
                st.warning("当前分析窗口内没有任务数据，请检查分析截止日期是否与上传数据时间匹配。")
                if st.button("返回重新上传", key="back_reupload_empty_task"):
                    reset_upload_state()
                    st.rerun()
                return

            section = st.radio(
                "查看内容",
                ["总览", "学校层与老师层分析", "任务层与学生层分析"],
                horizontal=True,
                key="overview_section"
            )

            if section == "总览":
                render_overview(
                    df_school_cur,
                    df_school_last,
                    df_teacher_cur,
                    df_teacher_last,
                    df_task_cur,
                    df_task_last,
                    df_task_30d
                )

            elif section == "学校层与老师层分析":
                render_detail_analysis(
                    df_school_cur,
                    df_school_last,
                    df_teacher_cur,
                    df_teacher_last,
                    df_task_30d
                )

            elif section == "任务层与学生层分析":
                render_task_student_analysis(
                    df_task_cur, df_task_last,
                    df_student_cur, df_student_last,
                    df_teacher_cur, df_teacher_last,
                    df_task_type_cur, df_task_type_last, df_task_30d
                )

        elif st.session_state.top_nav_mode == "school":
            st.markdown("## 🏫 学校报告")
            if not st.session_state.selected_school:
                st.info("请在顶部选择学校，或在学校入口总览中点击学校。")
            else:
                render_school_detail_page(
                    selected_school=st.session_state.selected_school,
                    school_cur=df_school_cur,
                    school_last=df_school_last,
                    teacher_cur=df_teacher_cur,
                    teacher_last=df_teacher_last,
                    task_cur=df_task_cur,
                    task_30d=df_task_30d
                )

        elif st.session_state.top_nav_mode == "teacher":
            st.markdown("## 👩‍🏫 老师画像")
            st.info("老师画像页面你后面再接。")

    except Exception as e:
        st.error(f"数据加载失败：{e}")
        st.warning("请检查上传文件格式、字段名是否正确。")
        if st.button("返回重新上传"):
            reset_upload_state()
            st.rerun()

# ================= 在页面分发前先消费待更新日期 =================
# if st.session_state.get("pending_anchor_date") is not None:
#     st.session_state.analysis_anchor_date = st.session_state.pending_anchor_date
#     st.session_state.pending_anchor_date = None

# ================= 主程序 =================
if not st.session_state.uploaded:
    render_input_page()
else:
    render_dashboard()
