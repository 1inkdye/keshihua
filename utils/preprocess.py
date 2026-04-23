import pandas as pd


# =========================
# 基础清洗工具
# =========================
def _to_num_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False).str.replace("%", "", regex=False).str.strip(),
        errors="coerce"
    )


def _clean_text_col(df: pd.DataFrame, col: str, lower: bool = False) -> pd.DataFrame:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        if lower:
            df[col] = df[col].str.lower()
        df.loc[df[col].isin(["nan", "None", "NaT"]), col] = pd.NA
    return df


def _normalize_date_col(df: pd.DataFrame, candidates) -> pd.DataFrame:
    for col in candidates:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df["日期"] = df[col].dt.normalize()
            return df
    if "日期" not in df.columns:
        df["日期"] = pd.NaT
    return df


# =========================
# 原有基础预处理
# =========================
def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()

    df = df.copy()

    percent_cols = ["发布任务老师占比", "参与率", "参与后完成率", "收到后完成率"]
    numeric_cols = [
        "教师数量", "老师数量", "任务总数", "发布任务老师数",
        "接收任务学生数", "打开任务学生数", "完成任务学生数"
    ]

    for col in percent_cols:
        if col in df.columns:
            df[col] = _to_num_series(df[col])

    for col in numeric_cols:
        if col in df.columns:
            df[col] = _to_num_series(df[col])

    df = normalize_school_col(df)
    df = _normalize_date_col(df, ["日期", "数据日期", "统计日期"])

    return df


def split_national_and_school(df: pd.DataFrame):
    df = normalize_school_col(df)
    national_df = df[df["学校"] == "全国"].copy() if "学校" in df.columns else pd.DataFrame()
    school_df = df[df["学校"] != "全国"].copy() if "学校" in df.columns else pd.DataFrame()
    return national_df, school_df


def get_national_row(national_df: pd.DataFrame):
    if not national_df.empty:
        return national_df.iloc[0]
    return None


def safe_metric_value(row, col):
    if row is None or col not in row or pd.isna(row[col]):
        return 0
    return row[col]


def classify(rate):
    if pd.isna(rate):
        return "缺失"
    elif rate >= 80:
        return "优秀（80%-100%）"
    elif rate >= 60:
        return "良好（60%-79.9%）"
    elif rate >= 40:
        return "一般（40%-59.9%）"
    else:
        return "较差（0%-39.9%）"


# =========================
# 学校文件第二sheet：任务类型统计
# =========================
def preprocess_task_type(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()

    df = df.copy()

    percent_cols = ["发布任务老师占比", "参与率", "参与后完成率", "收到后完成率"]
    numeric_cols = [
        "任务总数", "发布任务老师数",
        "接收任务学生数", "打开任务学生数", "完成任务学生数"
    ]

    for col in percent_cols:
        if col in df.columns:
            df[col] = _to_num_series(df[col])

    for col in numeric_cols:
        if col in df.columns:
            df[col] = _to_num_series(df[col])

    df = normalize_school_col(df)

    if "任务类型" in df.columns:
        df["任务类型"] = df["任务类型"].astype(str).str.strip()

    return df


# =========================
# 任务数据预处理
# =========================
def preprocess_task(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()

    df = df.copy()

    percent_cols = ["参与率", "参与后完成率", "收到后完成率"]
    numeric_cols = ["接收任务学生数", "打开任务学生数", "完成任务学生数"]

    for col in percent_cols:
        if col in df.columns:
            df[col] = _to_num_series(df[col])

    for col in numeric_cols:
        if col in df.columns:
            df[col] = _to_num_series(df[col])

    if "任务发布时间" in df.columns:
        df["任务发布时间"] = pd.to_datetime(df["任务发布时间"], errors="coerce")
        df["日期"] = df["任务发布时间"].dt.normalize()
        df["发布日期"] = df["任务发布时间"].dt.date
        df["发布小时"] = df["任务发布时间"].dt.hour
        df["发布星期"] = df["任务发布时间"].dt.day_name().map({
            "Monday": "周一",
            "Tuesday": "周二",
            "Wednesday": "周三",
            "Thursday": "周四",
            "Friday": "周五",
            "Saturday": "周六",
            "Sunday": "周日"
        })
    else:
        df = _normalize_date_col(df, ["日期", "发布时间"])

    df = _clean_text_col(df, "老师邮箱", lower=True)
    df = _clean_text_col(df, "老师姓名")
    df = _clean_text_col(df, "任务类型")
    df = _clean_text_col(df, "任务名称")
    df = normalize_school_col(df)

    return df


# =========================
# 学生数据预处理
# =========================
def preprocess_student(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()

    df = df.copy()

    percent_cols = ["正确率"]
    numeric_cols = ["做题数"]

    for col in percent_cols:
        if col in df.columns:
            df[col] = _to_num_series(df[col])

    for col in numeric_cols:
        if col in df.columns:
            df[col] = _to_num_series(df[col])

    if "发布时间" in df.columns:
        df["发布时间"] = pd.to_datetime(df["发布时间"], errors="coerce")
    if "完成时间" in df.columns:
        df["完成时间"] = pd.to_datetime(df["完成时间"], errors="coerce")

    if "发布时间" in df.columns:
        df["日期"] = df["发布时间"].dt.normalize()
    elif "完成时间" in df.columns:
        df["日期"] = df["完成时间"].dt.normalize()
    else:
        df["日期"] = pd.NaT

    df = _clean_text_col(df, "老师邮箱", lower=True)
    df = _clean_text_col(df, "老师姓名")
    df = _clean_text_col(df, "任务类型")
    df = _clean_text_col(df, "任务名称")
    df = _clean_text_col(df, "主任务名称")
    df = _clean_text_col(df, "学生姓名")
    df = _clean_text_col(df, "学员号")
    df = _clean_text_col(df, "学员任务状态")
    df = normalize_school_col(df)

    if "老师评语" in df.columns:
        df["老师评语"] = df["老师评语"].astype(str).replace("nan", "")
        df["有评语"] = df["老师评语"].str.strip() != ""
    else:
        df["有评语"] = False

    if "老师评星" in df.columns:
        df["老师评星"] = pd.to_numeric(df["老师评星"], errors="coerce")
        df["有评星"] = df["老师评星"].notna()
    else:
        df["有评星"] = False

    return df


# =========================
# 老师维表预处理
# =========================
def preprocess_teacher(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()

    df = df.copy()

    percent_cols = ["参与率", "参与后完成率", "收到后完成率"]
    numeric_cols = ["发布任务总数", "接收任务学生数", "打开任务学生数", "完成任务学生数"]

    for col in percent_cols:
        if col in df.columns:
            df[col] = _to_num_series(df[col])

    for col in numeric_cols:
        if col in df.columns:
            df[col] = _to_num_series(df[col])

    df = _clean_text_col(df, "老师邮箱", lower=True)
    df = _clean_text_col(df, "老师姓名")
    df = _clean_text_col(df, "科目")
    df = normalize_school_col(df)
    df = _normalize_date_col(df, ["日期", "数据日期", "统计日期"])

    return df


def normalize_school_col(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()

    df = df.copy()
    if "学校" not in df.columns:
        for candidate in ["学校名称", "校区", "校区名称"]:
            if candidate in df.columns:
                df = df.rename(columns={candidate: "学校"})
                break

    if "学校" in df.columns:
        df["学校"] = df["学校"].astype(str).str.strip()
        df.loc[df["学校"].isin(["nan", "None", "NaT"]), "学校"] = pd.NA

    return df


# =========================
# 新增：周期切片
# =========================
def get_analysis_periods(anchor_date):
    import pandas as pd
    anchor = pd.Timestamp(anchor_date)

    # 找最近的周四（包含anchor_date当天，如果anchor本身是周四也算）
    # weekday(): 周一=0 ... 周四=3 ... 周五=4
    days_since_thursday = (anchor.weekday() - 3) % 7
    cur_end = anchor - pd.Timedelta(days=days_since_thursday)

    # 本周：cur_end往前6天到cur_end
    cur_start = cur_end - pd.Timedelta(days=6)

    # 上周
    last_end = cur_start - pd.Timedelta(days=1)
    last_start = last_end - pd.Timedelta(days=6)

    # 近30天
    rolling_30_end = cur_end
    rolling_30_start = cur_end - pd.Timedelta(days=29)

    return {
        "cur_start": cur_start,
        "cur_end": cur_end,
        "last_start": last_start,
        "last_end": last_end,
        "rolling_30_start": rolling_30_start,
        "rolling_30_end": rolling_30_end,
    }


def filter_by_date(df: pd.DataFrame, start_date, end_date, date_col: str = "日期") -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()
    if date_col not in out.columns:
        return out.iloc[0:0].copy()

    out[date_col] = pd.to_datetime(out[date_col], errors="coerce").dt.normalize()
    start_date = pd.to_datetime(start_date).normalize()
    end_date = pd.to_datetime(end_date).normalize()

    return out[(out[date_col] >= start_date) & (out[date_col] <= end_date)].copy()


# =========================
# 新增：任务表 + 老师维表 => 反推老师 / 学校 / 任务类型
# =========================
def build_teacher_dimension(df_teacher: pd.DataFrame) -> pd.DataFrame:
    df_teacher = preprocess_teacher(df_teacher)

    if df_teacher.empty:
        return pd.DataFrame(columns=["老师邮箱", "老师姓名", "学校", "科目"])

    use_cols = [c for c in ["老师邮箱", "老师姓名", "学校", "科目"] if c in df_teacher.columns]
    dim = df_teacher[use_cols].copy()

    # 先按邮箱去重
    if "老师邮箱" in dim.columns and dim["老师邮箱"].notna().any():
        dim = dim.sort_values(
            by=[c for c in ["学校", "科目", "老师姓名"] if c in dim.columns],
            na_position="last"
        ).drop_duplicates(subset=["老师邮箱"], keep="first")

    # 补一份按姓名去重的备用映射
    dim_name = dim.copy()
    if "老师姓名" in dim_name.columns:
        dim_name = dim_name.drop_duplicates(subset=["老师姓名"], keep="first")

    return dim_name.reset_index(drop=True)


def attach_teacher_dimension(df_task: pd.DataFrame, df_teacher_dim: pd.DataFrame) -> pd.DataFrame:
    df_task = preprocess_task(df_task)
    df_teacher_dim = build_teacher_dimension(df_teacher_dim)

    if df_task.empty:
        return df_task

    out = df_task.copy()

    # 先按邮箱并学校/科目
    if not df_teacher_dim.empty and "老师邮箱" in out.columns and "老师邮箱" in df_teacher_dim.columns:
        email_dim_cols = [c for c in ["老师邮箱", "学校", "科目"] if c in df_teacher_dim.columns]
        email_dim = df_teacher_dim[email_dim_cols].drop_duplicates("老师邮箱")
        out = out.merge(email_dim, on="老师邮箱", how="left", suffixes=("", "_dim"))

        for col in ["学校", "科目"]:
            dim_col = f"{col}_dim"
            if dim_col in out.columns:
                if col not in out.columns:
                    out[col] = out[dim_col]
                else:
                    out[col] = out[col].fillna(out[dim_col])
                out = out.drop(columns=[dim_col])

    # 再按姓名兜底
    if not df_teacher_dim.empty and "老师姓名" in out.columns and "老师姓名" in df_teacher_dim.columns:
        name_dim_cols = [c for c in ["老师姓名", "学校", "科目"] if c in df_teacher_dim.columns]
        name_dim = df_teacher_dim[name_dim_cols].drop_duplicates("老师姓名")
        out = out.merge(name_dim, on="老师姓名", how="left", suffixes=("", "_name"))

        for col in ["学校", "科目"]:
            name_col = f"{col}_name"
            if name_col in out.columns:
                if col not in out.columns:
                    out[col] = out[name_col]
                else:
                    out[col] = out[col].fillna(out[name_col])
                out = out.drop(columns=[name_col])

    out = normalize_school_col(out)
    return out


def _teacher_key_series(df: pd.DataFrame) -> pd.Series:
    if "老师邮箱" in df.columns and df["老师邮箱"].notna().any():
        return df["老师邮箱"].astype(str)
    if "老师姓名" in df.columns:
        return df["老师姓名"].astype(str)
    return pd.Series(["未知老师"] * len(df), index=df.index)


def build_teacher_snapshot_from_task(df_task: pd.DataFrame, df_teacher_dim: pd.DataFrame = None) -> pd.DataFrame:
    task = attach_teacher_dimension(df_task, df_teacher_dim)

    if task.empty:
        return pd.DataFrame(columns=[
            "老师姓名", "老师邮箱", "学校", "科目",
            "发布任务总数", "接收任务学生数", "打开任务学生数", "完成任务学生数",
            "参与率", "参与后完成率", "收到后完成率"
        ])

    task["教师键"] = _teacher_key_series(task)

    group_cols = [c for c in ["教师键", "老师姓名", "老师邮箱", "学校", "科目"] if c in task.columns]
    agg_df = (
        task.groupby(group_cols, dropna=False, as_index=False)
        .agg(
            发布任务总数=("任务发布时间" if "任务发布时间" in task.columns else "教师键", "count"),
            接收任务学生数=("接收任务学生数", "sum"),
            打开任务学生数=("打开任务学生数", "sum"),
            完成任务学生数=("完成任务学生数", "sum"),
        )
    )

    agg_df["参与率"] = agg_df.apply(
        lambda x: x["打开任务学生数"] / x["接收任务学生数"] * 100 if x["接收任务学生数"] > 0 else 0,
        axis=1
    )
    agg_df["参与后完成率"] = agg_df.apply(
        lambda x: x["完成任务学生数"] / x["打开任务学生数"] * 100 if x["打开任务学生数"] > 0 else 0,
        axis=1
    )
    agg_df["收到后完成率"] = agg_df.apply(
        lambda x: x["完成任务学生数"] / x["接收任务学生数"] * 100 if x["接收任务学生数"] > 0 else 0,
        axis=1
    )

    if "教师键" in agg_df.columns:
        agg_df = agg_df.drop(columns=["教师键"])

    return agg_df.sort_values(["发布任务总数", "接收任务学生数"], ascending=False).reset_index(drop=True)


def build_school_snapshot_from_task(df_task: pd.DataFrame, df_teacher_dim: pd.DataFrame = None) -> pd.DataFrame:
    task = attach_teacher_dimension(df_task, df_teacher_dim)
    teacher_dim = build_teacher_dimension(df_teacher_dim)

    if task.empty:
        return pd.DataFrame(columns=[
            "学校", "老师数量", "教师数量", "任务总数", "发布任务老师数", "发布任务老师占比",
            "接收任务学生数", "打开任务学生数", "完成任务学生数",
            "参与率", "参与后完成率", "收到后完成率"
        ])

    task = task[task["学校"].notna()].copy()
    if task.empty:
        return pd.DataFrame(columns=[
            "学校", "老师数量", "教师数量", "任务总数", "发布任务老师数", "发布任务老师占比",
            "接收任务学生数", "打开任务学生数", "完成任务学生数",
            "参与率", "参与后完成率", "收到后完成率"
        ])

    task["教师键"] = _teacher_key_series(task)

    school_df = (
        task.groupby("学校", as_index=False)
        .agg(
            任务总数=("任务发布时间" if "任务发布时间" in task.columns else "教师键", "count"),
            发布任务老师数=("教师键", "nunique"),
            接收任务学生数=("接收任务学生数", "sum"),
            打开任务学生数=("打开任务学生数", "sum"),
            完成任务学生数=("完成任务学生数", "sum"),
        )
    )

    if not teacher_dim.empty and "学校" in teacher_dim.columns:
        teacher_dim["教师键"] = _teacher_key_series(teacher_dim)
        teacher_cnt = (
            teacher_dim.dropna(subset=["学校"])
            .groupby("学校", as_index=False)["教师键"]
            .nunique()
            .rename(columns={"教师键": "老师数量"})
        )
        school_df = school_df.merge(teacher_cnt, on="学校", how="left")
    else:
        school_df["老师数量"] = school_df["发布任务老师数"]

    school_df["老师数量"] = school_df["老师数量"].fillna(school_df["发布任务老师数"])
    school_df["教师数量"] = school_df["老师数量"]

    school_df["发布任务老师占比"] = school_df.apply(
        lambda x: x["发布任务老师数"] / x["老师数量"] * 100 if x["老师数量"] > 0 else 0,
        axis=1
    )
    school_df["参与率"] = school_df.apply(
        lambda x: x["打开任务学生数"] / x["接收任务学生数"] * 100 if x["接收任务学生数"] > 0 else 0,
        axis=1
    )
    school_df["参与后完成率"] = school_df.apply(
        lambda x: x["完成任务学生数"] / x["打开任务学生数"] * 100 if x["打开任务学生数"] > 0 else 0,
        axis=1
    )
    school_df["收到后完成率"] = school_df.apply(
        lambda x: x["完成任务学生数"] / x["接收任务学生数"] * 100 if x["接收任务学生数"] > 0 else 0,
        axis=1
    )

    # 全国行
    national = pd.DataFrame([{
        "学校": "全国",
        "老师数量": school_df["老师数量"].sum() if "老师数量" in school_df.columns else school_df["发布任务老师数"].sum(),
        "教师数量": school_df["教师数量"].sum() if "教师数量" in school_df.columns else school_df["发布任务老师数"].sum(),
        "任务总数": school_df["任务总数"].sum(),
        "发布任务老师数": school_df["发布任务老师数"].sum(),
        "接收任务学生数": school_df["接收任务学生数"].sum(),
        "打开任务学生数": school_df["打开任务学生数"].sum(),
        "完成任务学生数": school_df["完成任务学生数"].sum(),
    }])

    national["发布任务老师占比"] = national.apply(
        lambda x: x["发布任务老师数"] / x["老师数量"] * 100 if x["老师数量"] > 0 else 0, axis=1
    )
    national["参与率"] = national.apply(
        lambda x: x["打开任务学生数"] / x["接收任务学生数"] * 100 if x["接收任务学生数"] > 0 else 0, axis=1
    )
    national["参与后完成率"] = national.apply(
        lambda x: x["完成任务学生数"] / x["打开任务学生数"] * 100 if x["打开任务学生数"] > 0 else 0, axis=1
    )
    national["收到后完成率"] = national.apply(
        lambda x: x["完成任务学生数"] / x["接收任务学生数"] * 100 if x["接收任务学生数"] > 0 else 0, axis=1
    )

    out = pd.concat([national, school_df], ignore_index=True)
    return out.reset_index(drop=True)


def build_task_type_snapshot_from_task(df_task: pd.DataFrame, df_teacher_dim: pd.DataFrame = None) -> pd.DataFrame:
    task = attach_teacher_dimension(df_task, df_teacher_dim)

    if task.empty:
        return pd.DataFrame(columns=[
            "任务类型", "任务总数", "发布任务老师数", "发布任务老师占比",
            "接收任务学生数", "打开任务学生数", "完成任务学生数",
            "参与率", "参与后完成率", "收到后完成率"
        ])

    if "任务类型" not in task.columns:
        task["任务类型"] = "未分类"

    task["任务类型"] = task["任务类型"].fillna("未分类")
    task["教师键"] = _teacher_key_series(task)

    total_teacher_pool = task["教师键"].nunique()

    out = (
        task.groupby("任务类型", as_index=False)
        .agg(
            任务总数=("任务发布时间" if "任务发布时间" in task.columns else "教师键", "count"),
            发布任务老师数=("教师键", "nunique"),
            接收任务学生数=("接收任务学生数", "sum"),
            打开任务学生数=("打开任务学生数", "sum"),
            完成任务学生数=("完成任务学生数", "sum"),
        )
    )

    out["发布任务老师占比"] = out.apply(
        lambda x: x["发布任务老师数"] / total_teacher_pool * 100 if total_teacher_pool > 0 else 0,
        axis=1
    )
    out["参与率"] = out.apply(
        lambda x: x["打开任务学生数"] / x["接收任务学生数"] * 100 if x["接收任务学生数"] > 0 else 0,
        axis=1
    )
    out["参与后完成率"] = out.apply(
        lambda x: x["完成任务学生数"] / x["打开任务学生数"] * 100 if x["打开任务学生数"] > 0 else 0,
        axis=1
    )
    out["收到后完成率"] = out.apply(
        lambda x: x["完成任务学生数"] / x["接收任务学生数"] * 100 if x["接收任务学生数"] > 0 else 0,
        axis=1
    )

    return out.sort_values("任务总数", ascending=False).reset_index(drop=True)