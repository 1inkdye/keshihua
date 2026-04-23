import pandas as pd

def calculate_teacher_retention_metrics(df_cur, df_last):
    df_cur = df_cur.copy()
    df_last = df_last.copy()

    if "老师姓名" in df_cur.columns:
        df_cur["老师姓名"] = df_cur["老师姓名"].astype(str).str.strip()
    if "老师姓名" in df_last.columns:
        df_last["老师姓名"] = df_last["老师姓名"].astype(str).str.strip()

    cur_active = df_cur[df_cur["发布任务总数"] > 0]["老师姓名"].dropna().unique()
    last_active = df_last[df_last["发布任务总数"] > 0]["老师姓名"].dropna().unique()

    cur_set = set(cur_active)
    last_set = set(last_active)

    retained = cur_set & last_set
    new_teachers = cur_set - last_set
    lost_teachers = last_set - cur_set

    retention_rate = len(retained) / len(last_set) * 100 if len(last_set) > 0 else 0

    return {
        "retention_rate": retention_rate,
        "retained": len(retained),
        "new": len(new_teachers),
        "lost": len(lost_teachers),
        "last_active": len(last_set),
        "cur_active": len(cur_set)
    }