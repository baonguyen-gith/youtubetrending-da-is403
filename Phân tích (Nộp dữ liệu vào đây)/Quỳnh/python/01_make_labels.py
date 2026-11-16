# -*- coding: utf-8 -*-
"""
01_make_labels.py
=================
Tao 3 nhan viral cho do an IS403 - Nhom 4 (phan cong: Vu Thi Nhu Quynh).

Nhan (theo Muc 4.4 cua bao cao):
  - viral_A    : pct_in_age >= 0.90, trong quan the H.
  - breakout_B : lvpd - ch_med_loo >= log10(2), trong H, can >= 5 video khac
                 cung kenh & cung nhom tuoi (leave-one-out).
  - viral_C    : ever_trending, trong H, khong phai video ngan, dang trong
                 cua so in_window_C = [2026-10-19, ngay_Trending_cuoi - 8 ngay].

Quan the H (Muc 4.1):
  in_history = TRUE, is_live_or_upcoming = FALSE, views > 0, age_days_last >= 1.

Input : videos_master.csv, trending_clean.csv
Output: 05_Code_Output/outputs/4.4 labels/labels.csv
        05_Code_Output/outputs/4.4 labels/labels_summary.csv
        05_Code_Output/outputs/4.4 labels/labels_check.md

Chay: py 05_Code_Output/python/01_make_labels.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Duong dan
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parents[1]          # .../Do an
OUTPUT_DIR = PROJECT_DIR / "05_Code_Output" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LABELS_DIR = OUTPUT_DIR / "4.4 labels"
LABELS_DIR.mkdir(parents=True, exist_ok=True)

VIDEOS_CSV = PROJECT_DIR / "videos_master.csv"
TRENDING_CSV = PROJECT_DIR / "trending_clean.csv"

# ---------------------------------------------------------------------------
# Quy uoc (Muc 4.2, 4.4)
# ---------------------------------------------------------------------------
AGE_BINS = [1, 2, 3, 5, 7, 10, 14, 21, 30, 60, 90, 180, 365, 730, np.inf]
AGE_LABELS = [
    "[1,2)", "[2,3)", "[3,5)", "[5,7)", "[7,10)", "[10,14)", "[14,21)",
    "[21,30)", "[30,60)", "[60,90)", "[90,180)", "[180,365)",
    "[365,730)", "[730,inf)",
]
VIRAL_A_CUT = 0.90
BREAKOUT_LOG2 = np.log10(2.0)
MIN_PEERS = 5                                # can it nhat 5 video khac
WINDOW_C_START = pd.Timestamp("2026-10-19")
WINDOW_C_LAG_DAYS = 8
RANDOM_SEED = 42                             # khong dung o buoc nay, ghi de tai lap


# ---------------------------------------------------------------------------
# Ham ho tro
# ---------------------------------------------------------------------------
def load_data() -> tuple[pd.DataFrame, pd.Timestamp]:
    videos = pd.read_csv(VIDEOS_CSV, low_memory=False)
    trending = pd.read_csv(TRENDING_CSV, usecols=["run_date"])

    if videos["video_id"].duplicated().any():
        raise ValueError("videos_master.csv co video_id trung lap")

    last_trending_date = pd.to_datetime(trending["run_date"]).max().normalize()
    return videos, last_trending_date


def population_h(df: pd.DataFrame) -> pd.Series:
    return (
        df["in_history"].eq(True)
        & df["is_live_or_upcoming"].eq(False)
        & (df["views"] > 0)
        & (df["age_days_last"] >= 1)
    )


def add_age_band(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["age_b"] = pd.cut(
        df["age_days_last"],
        bins=AGE_BINS,
        labels=AGE_LABELS,
        right=False,
        include_lowest=True,
    )
    return df


def compute_viral_a(h: pd.DataFrame) -> pd.DataFrame:
    """viral_A = hang trung binh cua log_views trong nhom tuoi / n nhom tuoi >= 0.90."""
    h = h.copy()
    h["log_views"] = np.log10(h["views"])
    grp = h.groupby("age_b", observed=True)["log_views"]
    h["rank_in_age"] = grp.rank(method="average")
    h["n_in_age"] = grp.transform("size")
    h["pct_in_age"] = h["rank_in_age"] / h["n_in_age"]
    h["viral_A"] = h["pct_in_age"] >= VIRAL_A_CUT
    return h


def compute_breakout_b(h: pd.DataFrame) -> pd.DataFrame:
    """breakout_B: so voi trung vi cua cac video khac cung kenh & nhom tuoi (LOO)."""
    h = h.copy()
    h["lvpd"] = np.log10(np.maximum(h["views_per_day"], 1.0))
    h["ch_med_loo"] = np.nan
    h["n_peers_loo"] = np.nan

    for _, g in h.groupby(["channel_id", "age_b"], observed=True, sort=False):
        n = len(g)
        vals = g["lvpd"].to_numpy(dtype=float)
        if not np.isfinite(vals).all():
            raise ValueError("lvpd co gia tri khong huu han trong nhom H")
        h.loc[g.index, "n_peers_loo"] = n - 1
        if n - 1 < MIN_PEERS:
            continue
        med = np.empty(n, dtype=float)
        for i in range(n):
            med[i] = np.median(np.delete(vals, i))
        h.loc[g.index, "ch_med_loo"] = med

    h["breakout_B"] = np.where(
        h["ch_med_loo"].notna(),
        (h["lvpd"] - h["ch_med_loo"]) >= BREAKOUT_LOG2,
        np.nan,
    )
    return h


def compute_viral_c(
    h: pd.DataFrame, last_trending_date: pd.Timestamp
) -> pd.DataFrame:
    """viral_C: ever_trending trong cua so in_window_C (video khong ngan)."""
    h = h.copy()
    window_end = last_trending_date - pd.Timedelta(days=WINDOW_C_LAG_DAYS)
    pub = pd.to_datetime(h["pub_date_vn"], errors="coerce").dt.normalize()

    h["in_window_C"] = (
        (pub >= WINDOW_C_START)
        & (pub <= window_end)
        & h["is_short_60"].eq(False)
    )
    h["viral_C"] = np.where(
        h["in_window_C"], h["ever_trending"].eq(True), np.nan
    )
    h.attrs["window_c_start"] = str(WINDOW_C_START.date())
    h.attrs["window_c_end"] = str(window_end.date())
    return h


def nullable_bool(values: pd.Series, eligible: pd.Series) -> pd.Series:
    """Tra ve Int8: 1/0 trong tap du dieu kien, NA ngoai tap.

    Dung 1/0/NA thay vi True/False/NA de doc duoc bang ca pandas va R
    ma khong bi canh bao mixed-type.
    """
    out = pd.array([pd.NA] * len(values), dtype="Int8")
    mask = eligible.fillna(False).to_numpy(dtype=bool)
    out[mask] = values.to_numpy(dtype=bool)[mask].astype("int8")
    return pd.Series(out, index=values.index)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    videos, last_trending_date = load_data()
    videos = add_age_band(videos)

    mask_h = population_h(videos)
    h = videos.loc[mask_h].copy()
    h = compute_viral_a(h)
    h = compute_breakout_b(h)
    h = compute_viral_c(h, last_trending_date)

    # ------------------------------------------------------------------
    # Ghep lai thanh labels.csv (giu tat ca video, co cot in_H)
    # ------------------------------------------------------------------
    labels = videos[["video_id", "channel_id", "pub_date_vn", "is_short_60",
                     "ever_trending", "age_days_last", "views",
                     "views_per_day"]].copy()
    labels["in_H"] = mask_h.to_numpy()
    labels["age_b"] = videos["age_b"]

    for col in ["log_views", "rank_in_age", "n_in_age", "pct_in_age"]:
        labels[col] = h[col].reindex(labels.index)

    labels["viral_A"] = nullable_bool(h["viral_A"], pd.Series(True, index=h.index))

    for col in ["lvpd", "ch_med_loo", "n_peers_loo"]:
        labels[col] = h[col].reindex(labels.index)

    eligible_b = h["ch_med_loo"].notna()
    labels["breakout_B"] = nullable_bool(
        h["breakout_B"].fillna(False).astype(bool), eligible_b
    )

    labels["in_window_C"] = h["in_window_C"].reindex(labels.index).fillna(False)
    labels["viral_C"] = nullable_bool(
        h["viral_C"].fillna(False).astype(bool), h["in_window_C"]
    )

    # Sap xep cot cho de doc
    labels = labels[[
        "video_id", "channel_id", "in_H", "age_days_last", "age_b",
        "views", "views_per_day", "log_views", "rank_in_age", "n_in_age",
        "pct_in_age", "viral_A",
        "lvpd", "ch_med_loo", "n_peers_loo", "breakout_B",
        "pub_date_vn", "is_short_60", "ever_trending", "in_window_C", "viral_C",
    ]]

    for col in ["pct_in_age", "lvpd", "ch_med_loo"]:
        labels[col] = labels[col].round(6)

    labels_path = LABELS_DIR / "labels.csv"
    labels.to_csv(labels_path, index=False, encoding="utf-8-sig")

    # ------------------------------------------------------------------
    # Bang tom tat cho Bang 5.12
    # ------------------------------------------------------------------
    n_h = int(mask_h.sum())
    rows = []

    va_elig = int(h.shape[0])
    va_pos = int(h["viral_A"].sum())
    rows.append({
        "label": "viral_A",
        "definition": "pct_in_age >= 0.90 (hạng trung bình log_views trong nhóm tuổi / n nhóm tuổi)",
        "eligible_n": va_elig,
        "positive_n": va_pos,
        "positive_rate": round(va_pos / va_elig, 6) if va_elig else np.nan,
    })

    bb_elig = int(h["ch_med_loo"].notna().sum())
    bb_pos = int((h["breakout_B"] == True).sum())
    rows.append({
        "label": "breakout_B",
        "definition": "lvpd - ch_med_loo >= log10(2), cần >= 5 video khác cùng kênh & nhóm tuổi",
        "eligible_n": bb_elig,
        "positive_n": bb_pos,
        "positive_rate": round(bb_pos / bb_elig, 6) if bb_elig else np.nan,
    })

    vc_elig = int(h["in_window_C"].sum())
    vc_pos = int((h["viral_C"] == True).sum())
    rows.append({
        "label": "viral_C",
        "definition": "ever_trending trong in_window_C (không ngắn, đăng trong cửa sổ)",
        "eligible_n": vc_elig,
        "positive_n": vc_pos,
        "positive_rate": round(vc_pos / vc_elig, 6) if vc_elig else np.nan,
    })

    summary = pd.DataFrame(rows)
    summary_path = LABELS_DIR / "labels_summary.csv"
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")

    # ------------------------------------------------------------------
    # Bo 6 so kiem tra chung (Bang 4.3) + thong tin phien ban du lieu
    # ------------------------------------------------------------------
    h["lv_adj"] = h["log_views"] - h.groupby("age_b", observed=True)[
        "log_views"].transform("mean")

    checks = {
        "n_H": n_h,
        "n_channels_H": int(h["channel_id"].nunique()),
        "n_age_7_10": int((h["age_b"] == "[7,10)").sum()),
        "viral_A_positive": va_pos,
        "median_lv_adj": round(float(h["lv_adj"].median()), 4),
        "ever_trending_H": int(h["ever_trending"].sum()),
    }

    data_info = {
        "source_file": VIDEOS_CSV.name,
        "n_rows_videos_master": int(len(videos)),
        "n_channels_videos_master": int(videos["channel_id"].nunique()),
        "n_ever_trending_total": int(videos["ever_trending"].sum()),
        "last_obs_ts_max": str(videos["last_obs_ts"].max()),
        "pub_date_vn_max": str(videos["pub_date_vn"].max()),
        "last_trending_date": str(last_trending_date.date()),
        "window_C": [h.attrs["window_c_start"], h.attrs["window_c_end"]],
        "expected_data_final": "data_final_20261113",
    }

    check_path = LABELS_DIR / "labels_check.md"
    with open(check_path, "w", encoding="utf-8") as f:
        f.write("# Kiểm tra labels.csv\n\n")
        f.write("## Bộ 6 số kiểm tra chung (Bảng 4.3)\n\n")
        f.write("| # | Số cần in ra | Giá trị |\n|---|---|---|\n")
        f.write(f"| 1 | n_H | {checks['n_H']:,} |\n")
        f.write(f"| 2 | Số kênh trong H | {checks['n_channels_H']:,} |\n")
        f.write(f"| 3 | Số video nhóm [7,10) | {checks['n_age_7_10']:,} |\n")
        f.write(f"| 4 | Tổng viral_A | {checks['viral_A_positive']:,} |\n")
        f.write(f"| 5 | Trung vị lv_adj (4 chữ số) | {checks['median_lv_adj']} |\n")
        f.write(f"| 6 | ever_trending trong H | {checks['ever_trending_H']:,} |\n\n")

        f.write("## Bảng tóm tắt nhãn (Bảng 5.12)\n\n")
        f.write("| Nhãn | Định nghĩa | Đủ điều kiện | Dương | Tỷ lệ dương |\n")
        f.write("|---|---|---:|---:|---:|\n")
        for _, r in summary.iterrows():
            f.write(f"| {r['label']} | {r['definition']} | "
                    f"{int(r['eligible_n']):,} | {int(r['positive_n']):,} | "
                    f"{r['positive_rate']:.2%} |\n")
        f.write("\n")

        f.write("## Thông tin phiên bản dữ liệu\n\n")
        f.write("| Trường | Giá trị |\n|---|---|\n")
        for k, v in data_info.items():
            f.write(f"| {k} | {v} |\n")

        f.write("\n> **Cảnh báo:** nếu `n_rows_videos_master` = 96.334 và "
                "`n_ever_trending_total` = 636 thì đây là bản `data_clean` "
                "ngày 03/11, chưa phải `data_final_20261113`. Phải chạy lại "
                "script này trên data_final trước hạn 15/11 23:59.\n")

        f.write("\n## Kiểm tra ràng buộc\n\n")
        rate = va_pos / va_elig
        f.write(f"- viral_A chiếm {rate:.4%} của H "
                f"({'ĐẠT' if 0.09 <= rate <= 0.11 else 'KHÔNG ĐẠT'} "
                "mức 9–11% theo Mục 4.4).\n")
        f.write(f"- viral_C có {vc_pos} video dương "
                f"({'đủ' if vc_pos >= 100 else 'KHÔNG đủ'} 100 để huấn luyện ở Q5).\n")
        f.write(f"- Số video không có đủ 5 video khác cùng kênh & nhóm tuổi: "
                f"{n_h - bb_elig:,} (breakout_B = NA).\n")
        f.write("- Cột nhãn viral_A / breakout_B / viral_C ghi 1/0, để trống (NA) "
                "khi video không đủ điều kiện. Lọc bằng `in_H` hoặc "
                "`in_window_C` trước khi huấn luyện.\n")

    # ------------------------------------------------------------------
    # Từ điển cột cho labels.csv
    # ------------------------------------------------------------------
    readme_path = LABELS_DIR / "labels_README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# labels.csv – Từ điển cột\n\n")
        f.write("Sinh bởi `05_Code_Output/python/01_make_labels.py`.\n\n")
        f.write("## Quần thể H và cách xác định `in_H`\n\n")
        f.write("`in_H = 1` khi video thỏa **đồng thời cả 4 điều kiện** của Mục 4.1:\n\n")
        f.write("| # | Điều kiện | Cột kiểm tra | Ý nghĩa |\n")
        f.write("|---|---|---|---|\n")
        f.write("| 1 | Video nằm trong lịch sử thu thập | `in_history == TRUE` | Video đã từng xuất hiện trong dữ liệu crawl |\n")
        f.write("| 2 | Không phải livestream/sắp công chiếu | `is_live_or_upcoming == FALSE` | Loại video chưa có lượt xem ổn định |\n")
        f.write("| 3 | Có lượt xem | `views > 0` | Loại video không có dữ liệu lượt xem |\n")
        f.write("| 4 | Đã đủ 1 ngày tuổi | `age_days_last >= 1` | Để `views_per_day` không bị chia cho 0 hoặc quá nhiễu |\n\n")
        f.write(f"Trên bản dữ liệu hiện tại: {len(videos):,} video → "
                f"**{checks['n_H']:,} video `in_H = 1`** "
                f"({len(videos) - checks['n_H']:,} video bị loại). Các điều kiện có thể "
                "trùng nhau nên số bị loại **không phải** tổng của 4 con số riêng lẻ.\n\n")
        f.write("Video có `in_H = 0` vẫn được giữ trong `labels.csv` để đối chiếu, "
                "nhưng **không dùng** khi tính nhãn hay huấn luyện mô hình. "
                "Các cột nhãn của chúng để trống (NA).\n\n")
        f.write("| Cột | Ý nghĩa |\n|---|---|\n")
        f.write("| video_id | Khóa video (duy nhất) |\n")
        f.write("| channel_id | Khóa kênh |\n")
        f.write("| in_H | 1 nếu thuộc quần thể H (Mục 4.1) |\n")
        f.write("| age_days_last | Tuổi video (ngày) tại lần đo cuối |\n")
        f.write("| age_b | Nhóm tuổi 14 mức [a,b) (Mục 4.2) |\n")
        f.write("| views | Lượt xem lũy kế tại lần đo cuối |\n")
        f.write("| views_per_day | Lượt xem / ngày |\n")
        f.write("| log_views | log10(views) |\n")
        f.write("| rank_in_age | Hạng trung bình của log_views trong age_b (1 = thấp nhất) |\n")
        f.write("| n_in_age | Số video của age_b trong H |\n")
        f.write("| pct_in_age | rank_in_age / n_in_age |\n")
        f.write("| viral_A | 1 nếu pct_in_age >= 0.90, 0 nếu không, NA ngoài H |\n")
        f.write("| lvpd | log10(max(views_per_day, 1)) |\n")
        f.write("| ch_med_loo | Trung vị lvpd của các video khác cùng kênh & age_b (leave-one-out); NA nếu < 5 video khác |\n")
        f.write("| n_peers_loo | Số video khác cùng kênh & age_b |\n")
        f.write("| breakout_B | 1 nếu lvpd − ch_med_loo >= log10(2), 0 nếu không, NA nếu không đủ peer |\n")
        f.write("| pub_date_vn | Ngày đăng (giờ Việt Nam, YYYY-MM-DD) |\n")
        f.write("| is_short_60 | Video <= 60 giây |\n")
        f.write("| ever_trending | Từng lọt Trending |\n")
        f.write("| in_window_C | 1 nếu không ngắn và đăng trong cửa sổ in_window_C |\n")
        f.write("| viral_C | 1 nếu ever_trending trong in_window_C, 0 nếu không, NA ngoài cửa sổ |\n")
        f.write("\n## Cửa sổ in_window_C\n\n")
        f.write(f"- Bắt đầu: {data_info['window_C'][0]}\n")
        f.write(f"- Kết thúc: {data_info['window_C'][1]} "
                f"(ngày Trending cuối {data_info['last_trending_date']} trừ 8 ngày)\n")
        f.write("\n## Cách dùng\n\n")
        f.write("Python:\n\n```python\n")
        f.write("import pandas as pd\n")
        f.write("lb = pd.read_csv('labels.csv', dtype={'video_id': str,\n")
        f.write("      'viral_A': 'Int8', 'breakout_B': 'Int8', 'viral_C': 'Int8'})\n")
        f.write("h = lb[lb.in_H]\n")
        f.write("y = h.loc[h.viral_A.notna(), 'viral_A'].astype(int)\n")
        f.write("```\n\n")
        f.write("R:\n\n```r\n")
        f.write("lb <- read.csv('labels.csv', na.strings = c('', 'NA'))\n")
        f.write("h <- subset(lb, in_H == 1)\n")
        f.write("table(h$viral_A, useNA = 'ifany')\n")
        f.write("```\n")
        f.write("\n## Lưu ý\n\n")
        f.write("- Không dùng `viral_A`/`breakout_B`/`viral_C` làm biến đầu vào X: "
                "đây là nhãn (target), không phải feature (Mục 4.5).\n")
        f.write("- Khi có `data_final_20261113`, chạy lại script và cập nhật "
                "Bảng 5.12 + bộ 6 số kiểm tra.\n")

    print("Da tao:", labels_path)
    print("Da tao:", summary_path)
    print("Da tao:", check_path)
    print("Da tao:", readme_path)
    print("\nBo 6 so kiem tra:")
    for k, v in checks.items():
        print(f"  {k}: {v}")
    print("\nTom tat nhan:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
