# -*- coding: utf-8 -*-
"""
prep.py - Tiền xử lý chuẩn (việc B3, Mục 4.1–4.4 của báo cáo)
Tạo: quần thể H, age_b, log_views, lv_adj, pct_in_age, viral_A và in BỘ 6 SỐ KIỂM TRA.

Cách dùng:
    python prep.py                       # đọc data_final_20261113/ mặc định
    DATA_DIR=/duong/dan/data_final_20261113 python prep.py
Từ B9, mặc định đã trỏ tới data_final_20261113/ (có thể ghi đè bằng biến môi trường DATA_DIR).
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- cấu hình
def _default_data_dir() -> str:
    """Tìm data_final_20261113/ ở thư mục hiện tại hoặc các thư mục cha.

    Nhờ vậy cùng một file chạy được từ Bao/python/, Bao/05_Code_Output/python/
    và vẫn tìm thấy gói dữ liệu nếu gói được chuyển vào Dữ liệu chính thức/ ở gốc repo.
    """
    rels = ("data_final_20261113", os.path.join("Dữ liệu chính thức", "data_final_20261113"))
    for parent in Path(__file__).resolve().parents:
        for rel in rels:
            cand = parent / rel
            if cand.is_dir():
                return str(cand)
    return "/mnt/user-data/uploads"


DATA_DIR = os.environ.get("DATA_DIR", _default_data_dir())   # B9: mặc định trỏ tới data_final_20261113/
AGE_EDGES = [1, 2, 3, 5, 7, 10, 14, 21, 30, 60, 90, 180, 365, 730, np.inf]  # 14 nhóm, [a, b)
AGE_LABELS = [f"[{a}, {b})" if np.isfinite(b) else f"[{a}, inf)"
              for a, b in zip(AGE_EDGES[:-1], AGE_EDGES[1:])]
VIRAL_A_CUT = 0.90


def load_master(data_dir: str = DATA_DIR) -> pd.DataFrame:
    """Đọc videos_master.csv, video_id luôn là chuỗi."""
    path = os.path.join(data_dir, "videos_master.csv")
    return pd.read_csv(path, dtype={"video_id": str, "channel_id": str},
                       encoding="utf-8-sig", low_memory=False)


def prep(df: pd.DataFrame) -> pd.DataFrame:
    """Trả về H (đã có age_b, lv_adj, pct_in_age, viral_A).

    H = in_history & ~is_live_or_upcoming & views > 0 & age_days_last >= 1   (Mục 4.1)
    lv_adj = log10(views) - trung bình log10(views) của nhóm tuổi, tính trên H  (Mục 4.3)
    pct_in_age = hạng trung bình của log_views trong nhóm tuổi / số video nhóm  (Mục 4.4)
    viral_A = pct_in_age >= 0.90
    """
    h = df[(df["in_history"]) & (~df["is_live_or_upcoming"])
           & (df["views"] > 0) & (df["age_days_last"] >= 1)].copy()
    h["log_views"] = np.log10(h["views"])
    h["age_b"] = pd.cut(h["age_days_last"], bins=AGE_EDGES, labels=AGE_LABELS, right=False)
    g = h.groupby("age_b", observed=True)["log_views"]
    h["lv_adj"] = h["log_views"] - g.transform("mean")
    h["pct_in_age"] = g.rank(method="average") / g.transform("size")
    h["viral_A"] = (h["pct_in_age"] >= VIRAL_A_CUT).astype(int)
    return h


def six_numbers(h: pd.DataFrame) -> dict:
    """Bộ 6 số kiểm tra chung của nhóm (Bảng 4.3)."""
    return {
        "1. n_H (số video trong H)": int(len(h)),
        "2. Số kênh khác nhau trong H": int(h["channel_id"].nunique()),
        "3. Số video H thuộc nhóm tuổi [7, 10)": int((h["age_b"] == "[7, 10)").sum()),
        "4. Tổng viral_A (số video dương)": int(h["viral_A"].sum()),
        "5. Trung vị lv_adj trên H (4 chữ số)": round(float(h["lv_adj"].median()), 4),
        "6. Số video H có ever_trending = TRUE": int(h["ever_trending"].sum()),
    }


if __name__ == "__main__":
    master = load_master()
    H = prep(master)
    print(f"DATA_DIR = {DATA_DIR}")
    print(f"videos_master: {len(master):,} dòng | H: {len(H):,} dòng")
    print("\n=== BỘ 6 SỐ KIỂM TRA (điền vào sheet so_kiem_tra) ===")
    for k, v in six_numbers(H).items():
        print(f"{k}: {v:,}" if isinstance(v, int) else f"{k}: {v}")
    pct = H["viral_A"].mean() * 100
    print(f"\nviral_A chiếm {pct:.2f}% H (yêu cầu 9–11%)", "OK" if 9 <= pct <= 11 else "!!! NGOÀI KHOẢNG")
    print("\nPhân bố nhóm tuổi:")
    print(H["age_b"].value_counts().sort_index().to_string())
