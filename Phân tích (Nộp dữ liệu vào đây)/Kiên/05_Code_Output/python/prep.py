# -*- coding: utf-8 -*-
"""prep.py - Tiền xử lý chuẩn (mục 0.2 của Phan_cong.docx): quần thể H, age_b, lv_adj, viral_A.
Người phụ trách: Nguyễn Trung Kiên (N3).
Chạy từ thư mục 05_Code_Output:  python python/prep.py   -> in bộ 6 số kiểm tra (mục 0.4)
"""
import os
import numpy as np
import pandas as pd

DATA_DIR = os.environ.get("DATA_DIR", "data_clean")   # <-- CHỈ ĐỔI DÒNG NÀY sang "data_final_20261113" (hoặc đặt biến môi trường DATA_DIR)
OUT_ROOT = os.environ.get("OUT_ROOT", "outputs")       # thư mục outputs/

AGE_EDGES = [1, 2, 3, 5, 7, 10, 14, 21, 30, 60, 90, 180, 365, 730, np.inf]
SLOT_ORDER = ["Khuya 0-5h", "Sáng 6-11h", "Chiều 12-17h", "Tối 18-21h", "Đêm 22-23h"]
MIN_GROUP_N = 30   # nhóm thể loại có n < 30 bị loại khỏi ANOVA / hồi quy (ghi trong báo cáo)


def read_master(data_dir=None):
    data_dir = data_dir or DATA_DIR
    df = pd.read_csv(os.path.join(data_dir, "videos_master.csv"), encoding="utf-8-sig",
                     dtype={"video_id": str}, low_memory=False)
    assert (df.video_id.str.len() != 11).sum() == 0, "video_id không đủ 11 ký tự"
    return df


def prep(df):
    """Trả về H (đã có age_b, lv_adj, pct_in_age, viral_A) theo mục 0.2."""
    H = df[df.in_history & ~df.is_live_or_upcoming & (df.views > 0) & (df.age_days_last >= 1)].copy()
    H["age_b"] = pd.cut(H.age_days_last, AGE_EDGES, right=False)
    H["lv_adj"] = H.log_views - H.groupby("age_b", observed=True).log_views.transform("mean")
    H["pct_in_age"] = H.groupby("age_b", observed=True).log_views.rank(pct=True, method="average")
    H["viral_A"] = H.pct_in_age >= 0.90
    return H


def six_numbers(H):
    return {
        "n_H": int(len(H)),
        "so_kenh_trong_H": int(H.channel_id.nunique()),
        "n_nhom_tuoi_7_10": int((H.age_b == pd.Interval(7, 10, closed="left")).sum()),
        "tong_viral_A": int(H.viral_A.sum()),
        "trung_vi_lv_adj": round(float(H.lv_adj.median()), 4),
        "n_ever_trending_trong_H": int(H.ever_trending.sum()),
    }


if __name__ == "__main__":
    H = prep(read_master())
    s = six_numbers(H)
    print(f"DATA_DIR = {DATA_DIR}")
    for k, v in s.items():
        print(f"{k:28s} {v}")
    print(f"viral_A / n_H = {s['tong_viral_A'] / s['n_H']:.4%}  (phải trong 9-11%)")
    os.makedirs(os.path.join(OUT_ROOT, "prep"), exist_ok=True)
    pd.DataFrame([{"nguon": DATA_DIR, **s}]).to_csv(
        os.path.join(OUT_ROOT, "prep", "so_kiem_tra_python.csv"), index=False, encoding="utf-8-sig")
