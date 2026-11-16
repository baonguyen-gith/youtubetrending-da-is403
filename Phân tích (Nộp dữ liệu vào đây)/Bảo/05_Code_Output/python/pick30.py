# -*- coding: utf-8 -*-
"""
pick30.py - Chọn 30 video phân tầng để đối chiếu với YouTube (việc B7, Mục 3.4 của báo cáo)

Phân tầng theo lượt xem của LẦN ĐO GẦN NHẤT:
    10 video views < 10 nghìn | 10 video 10 nghìn <= views <= 1 triệu | 10 video views > 1 triệu
random_state = 42. Chỉ chọn video đang công khai bình thường (không live/upcoming, đủ likes và comments)
để có thể so ba chỉ số với trang YouTube.

QUY TRÌNH THỰC TẾ (bạn làm tay, script không làm thay được):
  1. Sau lần thu cuối 12/11 20:00 và tắt lịch thu: DATA_DIR=<data_clean mới nhất> python pick30.py
  2. Mở file reliability_check_30videos.csv, mở TỪNG video trên YouTube (khung 20:05–21:35),
     điền yt_views, yt_likes, yt_comments, yt_gio_xem (giờ xem, định dạng YYYY-MM-DD HH:MM), ten_anh (ảnh chụp màn hình).
  3. Chạy:  python pick30.py --summarize     -> tính sai lệch tương đối và bảng Bảng 3.4.
Sai lệch tương đối = (YouTube - API) / API. Chênh dương là bình thường vì thời gian trôi giữa hai lần đọc.
"""
import os
import sys
import numpy as np
import pandas as pd

from prep import load_master, DATA_DIR

OUT_DIR = os.environ.get("OUT_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", "reliability"))
os.makedirs(OUT_DIR, exist_ok=True)
CSV = os.path.join(OUT_DIR, "reliability_check_30videos.csv")
SEED = 42
WINDOW_HOURS = 6          # chỉ chọn video có lần đo trong 6 giờ cuối (lần thu cuối) để giờ chênh với YouTube chỉ vài chục phút
TIERS = [("1. < 10 nghìn", lambda v: v < 10_000),
         ("2. 10 nghìn – 1 triệu", lambda v: (v >= 10_000) & (v <= 1_000_000)),
         ("3. > 1 triệu", lambda v: v > 1_000_000)]


def pick() -> pd.DataFrame:
    m = pd.read_csv(os.path.join(DATA_DIR, "measurements.csv"), dtype={"video_id": str}, encoding="utf-8-sig",
                    usecols=["video_id", "title", "channel_title", "collected_ts", "views", "likes", "comments",
                             "is_live_or_upcoming", "likes_hidden", "comments_disabled"], low_memory=False)
    m["_t"] = pd.to_datetime(m["collected_ts"], utc=True)
    m = m[m["_t"] >= m["_t"].max() - pd.Timedelta(hours=WINDOW_HOURS)]                    # chỉ lần thu cuối
    m = m.sort_values("_t").groupby("video_id", as_index=False).tail(1).drop(columns="_t")  # lần đo gần nhất của mỗi video
    ok = m[(~m["is_live_or_upcoming"]) & (~m["likes_hidden"]) & (~m["comments_disabled"])
           & m[["views", "likes", "comments"]].notna().all(axis=1) & (m["views"] > 0)]
    parts = []
    for name, f in TIERS:
        pool = ok[f(ok["views"])]
        if len(pool) < 10:
            sys.exit(f"Tầng '{name}' chỉ có {len(pool)} video trong {WINDOW_HOURS} giờ cuối - tăng WINDOW_HOURS.")
        s = pool.sample(n=10, random_state=SEED).assign(tang=name)
        parts.append(s)
    out = pd.concat(parts, ignore_index=True)
    out = out.rename(columns={"views": "api_views", "likes": "api_likes", "comments": "api_comments",
                              "collected_ts": "api_gio_do_utc"})
    out["link"] = "https://www.youtube.com/watch?v=" + out["video_id"]
    for c in ["yt_views", "yt_likes", "yt_comments", "yt_gio_xem", "ten_anh"]:
        out[c] = np.nan if c.startswith("yt_v") or c in ("yt_likes", "yt_comments") else ""
    return out[["tang", "video_id", "link", "title", "channel_title", "api_views", "api_likes", "api_comments",
                "api_gio_do_utc", "yt_views", "yt_likes", "yt_comments", "yt_gio_xem", "ten_anh"]]


def summarize():
    d = pd.read_csv(CSV, encoding="utf-8-sig", dtype={"video_id": str})
    need = ["yt_views", "yt_likes", "yt_comments", "yt_gio_xem"]
    if d[need].isna().any().any():
        n_miss = int(d[need].isna().any(axis=1).sum())
        sys.exit(f"Còn {n_miss} dòng chưa điền đủ số hai bên - điền xong rồi chạy lại --summarize.")
    d["api_gio_do_utc"] = pd.to_datetime(d["api_gio_do_utc"], utc=True)
    # yt_gio_xem nhập theo giờ Việt Nam (UTC+7)
    d["yt_gio_xem_utc"] = pd.to_datetime(d["yt_gio_xem"]).dt.tz_localize("Asia/Ho_Chi_Minh").dt.tz_convert("UTC")
    d["gio_chenh_phut"] = (d["yt_gio_xem_utc"] - d["api_gio_do_utc"]).dt.total_seconds() / 60
    for a, b, c in [("views", "api_views", "yt_views"), ("likes", "api_likes", "yt_likes"), ("comments", "api_comments", "yt_comments")]:
        d[f"sai_lech_{a}"] = (d[c] - d[b]) / d[b].where(d[b] > 0)
    d.to_csv(CSV, index=False, encoding="utf-8-sig")
    g = d.groupby("tang").agg(so_video=("video_id", "size"), tv_sai_lech_views=("sai_lech_views", "median"),
                              tv_sai_lech_likes=("sai_lech_likes", "median"),
                              tv_sai_lech_comments=("sai_lech_comments", "median"),
                              tv_gio_chenh_phut=("gio_chenh_phut", "median")).reset_index()
    tot = pd.DataFrame([{"tang": "Chung", "so_video": len(d), "tv_sai_lech_views": d["sai_lech_views"].median(),
                         "tv_sai_lech_likes": d["sai_lech_likes"].median(),
                         "tv_sai_lech_comments": d["sai_lech_comments"].median(),
                         "tv_gio_chenh_phut": d["gio_chenh_phut"].median()}])
    res = pd.concat([g, tot], ignore_index=True)
    res.to_csv(os.path.join(OUT_DIR, "reliability_check_summary.csv"), index=False, encoding="utf-8-sig")
    print(res.round(4).to_string(index=False))
    print("\nTỷ lệ dòng có chênh dương (views):", round((d["sai_lech_views"] > 0).mean(), 3))
    print("Tương quan giữa giờ chênh và sai lệch views (Spearman):",
          round(d[["gio_chenh_phut", "sai_lech_views"]].corr(method="spearman").iloc[0, 1], 3))


if __name__ == "__main__":
    if "--summarize" in sys.argv:
        summarize()
    else:
        t = pick()
        if os.path.exists(CSV):
            sys.exit(f"{CSV} đã tồn tại (có thể đã điền tay) - xóa hoặc đổi tên nếu muốn chọn lại.")
        t.to_csv(CSV, index=False, encoding="utf-8-sig")
        print(f"Đã tạo {CSV}: {len(t)} video")
        print(t.groupby("tang")["api_views"].agg(["count", "min", "median", "max"]).to_string())
