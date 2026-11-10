"""prep.py - Tiền xử lý chuẩn (Chương 4 báo cáo): H, age_b, log_views, lv_adj, viral_A.
Dùng:  DATA_DIR=<thư mục dữ liệu> python prep.py      (mặc định ./data_clean_temp)
Hoặc:  from prep import load_prep, six_numbers
"""
import os, sys
import numpy as np
import pandas as pd

DATA_DIR = os.environ.get("DATA_DIR", "data_clean_temp")
AGE_EDGES = [1, 2, 3, 5, 7, 10, 14, 21, 30, 60, 90, 180, 365, 730, np.inf]  # 14 nhóm, [a, b)


def load_prep(data_dir=None, usecols=None):
    """Trả về toàn bộ videos_master kèm cột in_H, age_b, log_views, lv_adj, pct_in_age, viral_A."""
    data_dir = data_dir or DATA_DIR
    v = pd.read_csv(os.path.join(data_dir, "videos_master.csv"), encoding="utf-8-sig", usecols=usecols, low_memory=False)
    # Quần thể H (mục 4.1)
    v["in_H"] = (
        v["in_history"].astype(bool)
        & ~v["is_live_or_upcoming"].astype(bool)
        & (v["views"] > 0)
        & (v["age_days_last"] >= 1)
    )
    # Nhóm tuổi (mục 4.2): khoảng đóng trái, mở phải
    v["age_b"] = pd.cut(v["age_days_last"], bins=AGE_EDGES, right=False)
    v["log_views"] = np.where(v["views"] > 0, np.log10(v["views"].where(v["views"] > 0)), np.nan)
    # lv_adj (mục 4.3): trừ trung bình log_views của nhóm tuổi, trung bình tính trên H
    H = v[v["in_H"]]
    grp_mean = H.groupby("age_b", observed=True)["log_views"].mean()
    v["lv_adj"] = np.where(v["in_H"], v["log_views"] - v["age_b"].map(grp_mean).astype(float), np.nan)
    # viral_A (mục 4.4): hạng trung bình trong nhóm tuổi / số video của nhóm, >= 0.90
    g = H.groupby("age_b", observed=True)["log_views"]
    pct = g.rank(method="average") / g.transform("size")
    v["pct_in_age"] = np.nan
    v.loc[H.index, "pct_in_age"] = pct
    v["viral_A"] = np.where(v["in_H"], v["pct_in_age"] >= 0.90, False)
    return v


def six_numbers(v):
    H = v[v["in_H"]]
    return {
        "1. n_H": int(len(H)),
        "2. so kenh trong H": int(H["channel_id"].nunique()),
        "3. n_H thuoc nhom tuoi [7,10)": int((H["age_days_last"] >= 7).sum() - (H["age_days_last"] >= 10).sum()),
        "4. tong viral_A": int(H["viral_A"].sum()),
        "5. trung vi lv_adj (4 chu so)": round(float(H["lv_adj"].median()), 4),
        "6. n_H co ever_trending = TRUE": int(H["ever_trending"].astype(bool).sum()),
    }


if __name__ == "__main__":
    v = load_prep()
    print(f"DATA_DIR = {DATA_DIR}")
    for k, val in six_numbers(v).items():
        print(f"{k}: {val}")
    H = v[v["in_H"]]
    print(f"[kiem tra] viral_A chiem {H['viral_A'].mean()*100:.2f}% cua H (phai trong 9-11%)")
    print(f"[kiem tra] so nhom tuoi co mat trong H: {H['age_b'].nunique()} / 14")
