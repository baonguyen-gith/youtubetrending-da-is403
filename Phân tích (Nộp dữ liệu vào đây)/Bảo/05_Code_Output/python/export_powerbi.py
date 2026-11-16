# -*- coding: utf-8 -*-
"""export_powerbi.py - Gom CSV cho Power BI (việc B11): kpi_overview.csv + sao chép bảng Q1, độ tin cậy, Logistic.
Power BI chỉ đọc các CSV trong outputs/; file của người khác (q2b, q5, q6, q4) chưa có thì bỏ biểu đồ đó."""
import os, shutil
import pandas as pd
from prep import load_master, prep, DATA_DIR

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")
OUT = os.path.join(BASE, "powerbi"); os.makedirs(OUT, exist_ok=True)

master = load_master(); H = prep(master)
tr = pd.read_csv(os.path.join(DATA_DIR, "trending_clean.csv"), usecols=["run_ts", "video_id"], dtype={"video_id": str})
meas = pd.read_csv(os.path.join(DATA_DIR, "measurements.csv"), usecols=["run_date"], low_memory=False)
kpi = pd.DataFrame([
    ("Số video (videos_master)", len(master)), ("Số kênh (videos_master)", master.channel_id.nunique()),
    ("n_H (quần thể phân tích)", len(H)), ("Số kênh trong H", H.channel_id.nunique()),
    ("Số video từng lọt Trending", int(master.ever_trending.sum())), ("Số lần chụp Trending", tr.run_ts.nunique()),
    ("Số lần đo (measurements)", len(meas)), ("Số ngày có dữ liệu đo", meas.run_date.nunique()),
    ("Số video H có ever_trending", int(H.ever_trending.sum())),
    ("Số video viral_A", int(H.viral_A.sum())), ("Tỷ lệ viral_A (%)", round(100 * H.viral_A.mean(), 2)),
    ("Trung vị lv_adj trên H", round(float(H.lv_adj.median()), 4)),
    ("Ngày đo đầu", meas.run_date.min()), ("Ngày đo cuối", meas.run_date.max())], columns=["chi_so", "gia_tri"])
# Tách bảng số và bảng ngày: Power BI không trộn kiểu số/văn bản trong cùng một cột.
is_num = pd.to_numeric(kpi["gia_tri"], errors="coerce").notna()
kpi[is_num].to_csv(os.path.join(OUT, "kpi_overview.csv"), index=False, encoding="utf-8-sig")
kpi[~is_num].to_csv(os.path.join(OUT, "kpi_dates.csv"), index=False, encoding="utf-8-sig")

copy = [("q1/q1_by_hour.csv", "q1_by_hour.csv"), ("q1/q1_heatmap.csv", "q1_heatmap.csv"),
        ("q1/q1_by_category.csv", "q1_by_category.csv"), ("q1/q1_by_dow.csv", "q1_by_dow.csv"),
        ("q1/q1_by_month.csv", "q1_by_month.csv"), ("q1/q1_descriptive_table.csv", "q1_descriptive_table.csv"),
        ("reliability/reliability_table.csv", "reliability_table.csv"), ("q3b/q3b_or_table.csv", "q3b_or_table.csv"),
        ("q3b/q3b_model_fit.csv", "q3b_model_fit.csv")]
for src, dst in copy:
    shutil.copy(os.path.join(BASE, src), os.path.join(OUT, dst))
print(kpi.to_string(index=False)); print("Đã ghi vào", os.path.abspath(OUT))
