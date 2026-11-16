# -*- coding: utf-8 -*-
"""
make_collection_log.py - Sinh collection_log.csv NHÁP (việc B2, dùng cho Mục 3.1 và 3.5)

Mỗi dòng = một ngày x một nguồn (trending / tracking / history) trong khoảng từ ngày đo đầu đến ngày đo cuối:
  so_luot_chay, so_dong, so_video, co_du_lieu (CÓ/THIẾU)  <- tính từ measurements.csv, KHÔNG phải điền tay
  ly_do, cach_xu_ly                                          <- BẠN điền cho các dòng THIẾU (script để trống)

Lưu ý: history không chạy hằng ngày nên "THIẾU" ở history chưa chắc là sự cố; ghi rõ trong ly_do.
Cách dùng:  (PowerShell) $env:PYTHONIOENCODING="utf-8"; python make_collection_log.py
"""
import os
import pandas as pd

from prep import DATA_DIR

OUT = os.environ.get("OUT_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", "reliability"))
os.makedirs(OUT, exist_ok=True)
FILE = os.path.join(OUT, "collection_log.csv")

m = pd.read_csv(os.path.join(DATA_DIR, "measurements.csv"), usecols=["video_id", "run_ts", "run_date", "source"],
                dtype={"video_id": str}, low_memory=False, encoding="utf-8-sig")
m["run_date"] = m["run_date"].astype(str)
days = pd.date_range(m["run_date"].min(), m["run_date"].max()).strftime("%Y-%m-%d")
g = (m.groupby(["run_date", "source"]).agg(so_luot_chay=("run_ts", "nunique"), so_dong=("video_id", "size"),
                                            so_video=("video_id", "nunique")))
rows = []
for d in days:
    for src in ["trending", "tracking", "history"]:
        if (d, src) in g.index:
            r = g.loc[(d, src)]
            rows.append([d, src, int(r.so_luot_chay), int(r.so_dong), int(r.so_video), "CÓ", "", ""])
        else:
            rows.append([d, src, 0, 0, 0, "THIẾU", "", ""])
log = pd.DataFrame(rows, columns=["ngay", "nguon", "so_luot_chay", "so_dong", "so_video", "co_du_lieu", "ly_do", "cach_xu_ly"])
if os.path.exists(FILE):
    old = pd.read_csv(FILE, encoding="utf-8-sig", dtype=str).fillna("")
    keep = old.set_index(["ngay", "nguon"])[["ly_do", "cach_xu_ly"]]
    for i, r in log.iterrows():                           # giữ lại phần đã điền tay nếu chạy lại
        k = (r["ngay"], r["nguon"])
        if k in keep.index:
            log.loc[i, ["ly_do", "cach_xu_ly"]] = keep.loc[k].values
log.to_csv(FILE, index=False, encoding="utf-8-sig")

miss = log[log["co_du_lieu"] == "THIẾU"]
print(f"Đã ghi {os.path.abspath(FILE)}: {len(log)} dòng, khoảng {days[0]} → {days[-1]}")
for src in ["trending", "tracking", "history"]:
    x = miss[miss["nguon"] == src]["ngay"].tolist()
    print(f"  {src}: {len(x)} ngày THIẾU", x if x else "")
print("\nBạn mở file, điền cột ly_do và cach_xu_ly cho các dòng THIẾU của trending và tracking.")
