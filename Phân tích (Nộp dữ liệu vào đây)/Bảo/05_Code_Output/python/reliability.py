# -*- coding: utf-8 -*-
"""
reliability.py - Độ tin cậy (a): reliability_table.csv (việc B6, Mục 3.3 của báo cáo) và
                 collection_summary.csv (tóm tắt thu thập theo ngày, hỗ trợ B2 / Mục 3.1, 3.5)

Mỗi dòng của reliability_table có: số đếm, mẫu số, tỷ lệ %, cách xử lý, nguồn tính.
Những số chỉ có ở bước làm sạch (trước khi đặt NaN / cummax) được đọc từ dq_report.txt, KHÔNG tự bịa;
mọi số còn lại được tính trực tiếp từ các CSV sạch.

Cách dùng:  DATA_DIR=... python reliability.py
"""
import os
import re
import numpy as np
import pandas as pd

from prep import load_master, prep, DATA_DIR

OUT_DIR = os.environ.get("OUT_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", "reliability"))
os.makedirs(OUT_DIR, exist_ok=True)


def num(s: str) -> int:
    return int(s.replace(",", "").replace(".", ""))


def parse_dq(path: str) -> dict:
    """Đọc các số từ dq_report.txt. Thiếu số nào thì trả None (không đoán)."""
    out = {}
    if not os.path.exists(path):
        return out
    t = open(path, encoding="utf-8-sig").read()
    pats = {
        "likes_gt_views": r"likes > views:\s*([\d,\.]+)\s*dòng",
        "comments_gt_views": r"comments > views:\s*([\d,\.]+)\s*dòng",
        "views_zero": r"views = 0:\s*([\d,\.]+)\s*dòng",
        "views_nan": r"views = NaN:\s*([\d,\.]+)\s*dòng",
    }
    for k, p in pats.items():
        m = re.search(p, t)
        out[k] = num(m.group(1)) if m else None
    m = re.search(r"views GIẢM giữa 2 lần đo liên tiếp:\s*([\d,\.]+)\s*/\s*([\d,\.]+)\s*cặp", t)
    out["views_dec_pairs"], out["views_pairs"] = (num(m.group(1)), num(m.group(2))) if m else (None, None)
    return out


def pct(a, b):
    return round(100 * a / b, 2) if (a is not None and b) else np.nan


def main():
    master = load_master()
    meas = pd.read_csv(os.path.join(DATA_DIR, "measurements.csv"), dtype={"video_id": str, "channel_id": str},
                       encoding="utf-8-sig", low_memory=False)
    trend = pd.read_csv(os.path.join(DATA_DIR, "trending_clean.csv"), dtype={"video_id": str}, encoding="utf-8-sig")
    dq = parse_dq(os.path.join(DATA_DIR, "dq_report.txt"))
    N_v, N_m = len(master), len(meas)
    rows = []

    def add(tc, cnt, den, how, src):
        rows.append({"tieu_chi": tc, "so_dem": cnt, "mau_so": den, "ty_le_pct": pct(cnt, den),
                     "cach_xu_ly": how, "nguon_tinh": src})

    # --- giá trị rỗng
    add("Ẩn lượt thích (likes_hidden)", int(master["likes_hidden"].sum()), N_v,
        "Giữ video; likes và like_rate để NaN, chỉ tính tỷ lệ trên video có likes", "videos_master.csv")
    add("Tắt bình luận (comments_disabled)", int(master["comments_disabled"].sum()), N_v,
        "Giữ video; comments và comment_rate để NaN", "videos_master.csv")
    add("Độ dài video rỗng (duration_sec)", int(master["duration_sec"].isna().sum()), N_v,
        "Giữ trong thống kê chung; loại khỏi mô hình dùng duration", "videos_master.csv")

    # --- trùng lặp (trên file sạch)
    add("Trùng lặp video (video_id lặp trong videos_master)", int(master["video_id"].duplicated().sum()), N_v,
        "Loại khi làm sạch; kiểm tra lại trên file sạch phải bằng 0", "videos_master.csv")
    add("Trùng lặp lần đo (cùng video_id và collected_ts)", int(meas.duplicated(["video_id", "collected_ts"]).sum()), N_m,
        "Loại khi làm sạch; kiểm tra lại trên file sạch phải bằng 0", "measurements.csv")
    add("Trùng lặp dòng Trending (cùng run_ts và video_id)", int(trend.duplicated(["run_ts", "video_id"]).sum()), len(trend),
        "Kiểm tra trên file sạch", "trending_clean.csv")

    # --- ngoại lai IQR trên log_views (video có views > 0)
    lv = np.log10(master.loc[master["views"] > 0, "views"])
    q1, q3 = lv.quantile(.25), lv.quantile(.75)
    lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    n_lo, n_hi = int((lv < lo).sum()), int((lv > hi).sum())
    add(f"Ngoại lai IQR trên log_views (dưới {lo:.2f})", n_lo, len(lv),
        "GIỮ (không loại): đây là video thật có ít lượt xem; phân tích dùng log10 và lv_adj", "videos_master.csv")
    add(f"Ngoại lai IQR trên log_views (trên {hi:.2f})", n_hi, len(lv),
        "GIỮ (không loại): video có lượt xem rất cao là hiện tượng thật của nền tảng", "videos_master.csv")

    # --- nhất quán logic: số trước làm sạch lấy từ dq_report, kiểm tra lại trên file sạch
    add("Lượt thích > lượt xem (trước làm sạch)", dq.get("likes_gt_views"), N_m,
        "Đặt likes = NaN (nhiễu API / video mới)", "dq_report.txt")
    add("Lượt thích > lượt xem (còn lại sau làm sạch)", int((meas["likes"] > meas["views"]).sum()), N_m,
        "Phải bằng 0", "measurements.csv")
    add("Bình luận > lượt xem (trước làm sạch)", dq.get("comments_gt_views"), N_m,
        "Đặt comments = NaN", "dq_report.txt")
    add("Bình luận > lượt xem (còn lại sau làm sạch)", int((meas["comments"] > meas["views"]).sum()), N_m,
        "Phải bằng 0", "measurements.csv")
    add("Lượt xem = 0", dq.get("views_zero"), N_m,
        "Giữ trong measurements; loại khỏi phân tích log và tỷ lệ (H yêu cầu views > 0)", "dq_report.txt")
    add("Lượt xem rỗng (NaN)", dq.get("views_nan"), N_m, "Loại dòng đo", "dq_report.txt")

    # --- views / likes giảm giữa 2 lần đo liên tiếp (tự tính lại để đối chiếu dq_report)
    m = meas.sort_values(["video_id", "collected_ts"]).copy()
    same = m["video_id"].eq(m["video_id"].shift())
    vr = m["views_raw"] if "views_raw" in m.columns else m["views"]
    dec_v = int(((vr < vr.shift()) & same & vr.notna() & vr.shift().notna()).sum())
    pairs_v = int((same & vr.notna() & vr.shift().notna()).sum())
    add("Lượt xem GIẢM giữa hai lần đo liên tiếp (tính lại từ views_raw)", dec_v, pairs_v,
        "Dùng cummax để chuỗi lượt xem đơn điệu (YouTube lọc view ảo)", "measurements.csv (views_raw)")
    if dq.get("views_dec_pairs") is not None:
        add("Lượt xem GIẢM giữa hai lần đo liên tiếp (theo dq_report)", dq["views_dec_pairs"], dq["views_pairs"],
            "Đối chiếu với dòng trên: hai số phải khớp", "dq_report.txt")
    lk = m["likes"]
    ok = same & lk.notna() & lk.shift().notna()
    add("Lượt thích GIẢM giữa hai lần đo liên tiếp", int(((lk < lk.shift()) & ok).sum()), int(ok.sum()),
        "Giữ nguyên (người dùng có thể bỏ thích); không dùng cummax cho likes", "measurements.csv")

    rt = pd.DataFrame(rows)
    rt.to_csv(os.path.join(OUT_DIR, "reliability_table.csv"), index=False, encoding="utf-8-sig")

    # --- tóm tắt thu thập theo ngày
    meas["run_date"] = meas["run_date"].astype(str)
    cs = (meas.groupby(["run_date", "source"]).agg(so_luot_chay=("run_ts", "nunique"), so_dong=("video_id", "size"),
                                                   so_video=("video_id", "nunique")).reset_index())
    cs.to_csv(os.path.join(OUT_DIR, "collection_summary.csv"), index=False, encoding="utf-8-sig")
    days = pd.date_range(meas["run_date"].min(), meas["run_date"].max()).strftime("%Y-%m-%d")
    missing = {}
    for src in ["trending", "tracking", "history"]:
        have = set(meas.loc[meas["source"] == src, "run_date"])
        missing[src] = [d for d in days if d not in have]
    pd.Series({k: ", ".join(v) if v else "(không thiếu)" for k, v in missing.items()}).to_csv(
        os.path.join(OUT_DIR, "missing_days.csv"), header=["ngay_thieu_trong_khoang_da_thu"], encoding="utf-8-sig")

    pd.set_option("display.width", 250, "display.max_colwidth", 70)
    print(rt[["tieu_chi", "so_dem", "mau_so", "ty_le_pct"]].to_string(index=False))
    print("\nNgày thiếu (trong khoảng từ ngày đầu đến ngày cuối có dữ liệu):")
    for k, v in missing.items():
        print(" ", k, ":", v if v else "không thiếu")
    print("\nKhoảng thu thập:", meas["run_date"].min(), "->", meas["run_date"].max(),
          "| số lượt chạy duy nhất:", meas["run_ts"].nunique())


if __name__ == "__main__":
    main()
