"""build_series.py - Dựng bốn chuỗi S1, S2, N1, N2 (nhiệm vụ K4).
Dùng:  DATA_DIR=<thư mục> python build_series.py [thư_mục_ra]   (mặc định ./outputs/series)
Xuất: series_daily.csv (date,S1,S2,n_videos,n_channels), series_trending.csv (date,N1,N2,...), series_notes.md
"""
import os, sys
import numpy as np
import pandas as pd
from prep import load_prep, DATA_DIR

OUT = sys.argv[1] if len(sys.argv) > 1 else "outputs/series"
os.makedirs(OUT, exist_ok=True)
START = pd.Timestamp("2024-01-01")
MAX_PER_CHANNEL = 500

v = load_prep()
v["pub_date"] = pd.to_datetime(v["pub_date_vn"])
last_obs_vn = pd.to_datetime(v["last_obs_ts"], utc=True).dt.tz_convert("Asia/Ho_Chi_Minh")
collect_last = last_obs_vn.max().normalize().tz_localize(None)  # ngày thu cuối (giờ VN)

# ---- Lọc kênh đủ lịch sử: số video in_history = TRUE của mỗi kênh < 500 ----
cnt = v[v["in_history"].astype(bool)].groupby("channel_id").size()
keep = cnt[cnt < MAX_PER_CHANNEL].index
n_channels_all, n_channels = int(cnt.size), int(len(keep))
vk = v[v["in_history"].astype(bool) & v["channel_id"].isin(keep)]

# ---- Khoảng ngày ----
end_s1 = collect_last - pd.Timedelta(days=1)          # bỏ ngày thu cuối (chưa đủ ngày)
end_s2 = collect_last - pd.Timedelta(days=7)          # S2 bỏ video đăng trong 7 ngày cuối
idx = pd.date_range(START, end_s1, freq="D")
daily = pd.DataFrame(index=idx)
daily["S1"] = vk.groupby("pub_date").size().reindex(idx, fill_value=0).astype(int)
Hk = vk[vk["in_H"]]
g = Hk[Hk["pub_date"] <= end_s2].groupby("pub_date")["lv_adj"]
daily["S2"] = g.mean().reindex(idx)
daily["n_videos"] = g.size().reindex(idx)
daily.loc[daily.index > end_s2, ["S2", "n_videos"]] = np.nan
daily["n_channels"] = n_channels
daily.index.name = "date"
daily.to_csv(os.path.join(OUT, "series_daily.csv"), float_format="%.6f")

# ---- Trending: N1, N2 ----
t = pd.read_csv(os.path.join(DATA_DIR, "trending_clean.csv"), encoding="utf-8-sig")
t["ts"] = pd.to_datetime(t["run_ts"], utc=True).dt.tz_convert("Asia/Ho_Chi_Minh")
t["date"] = t["ts"].dt.normalize().dt.tz_localize(None)
days_present = sorted(t["date"].unique())
full = pd.date_range(days_present[0], days_present[-1], freq="D")
missing = [d for d in full if d not in set(days_present)]
first_date = t.groupby("video_id")["date"].min()
n1 = first_date.value_counts().reindex(full, fill_value=0).astype(float)
n1.loc[full[0]] = np.nan                                 # bỏ ngày đầu (lần chụp đầu)
after_missing = [d + pd.Timedelta(days=1) for d in missing if d + pd.Timedelta(days=1) in set(full)]
n1.loc[after_missing] = np.nan                           # NaN cho ngày ngay sau ngày thiếu
n1.loc[missing] = np.nan                                 # ngày thiếu: không có dữ liệu
# N2: lần chụp gần 20:00 giờ VN nhất trong ngày; trung vị views của hạng 1-50
runs = t.drop_duplicates("run_ts")[["run_ts", "ts", "date"]].copy()
runs["gap"] = (runs["ts"].dt.hour * 60 + runs["ts"].dt.minute - 20 * 60).abs()
pick = runs.sort_values(["date", "gap"]).groupby("date").head(1).set_index("date")
top = t[t["rank"] <= 50]
n2 = pd.Series({d: top.loc[top["run_ts"] == pick.loc[d, "run_ts"], "views"].median() for d in pick.index}).reindex(full)
st = pd.DataFrame({"N1": n1, "N2": n2})
st["snapshot_time_vn"] = pick["ts"].dt.strftime("%H:%M").reindex(full)
st.index.name = "date"
st.to_csv(os.path.join(OUT, "series_trending.csv"), float_format="%.6f")

# ---- series_notes.md ----
nan_n1 = [d.strftime("%d/%m") for d in st.index[st["N1"].isna()]]
nan_n2 = [d.strftime("%d/%m") for d in st.index[st["N2"].isna()]]
S2_nan = daily.loc[daily.index <= end_s2, "S2"].isna().sum()
with open(os.path.join(OUT, "series_notes.md"), "w", encoding="utf-8") as f:
    f.write(f"""# series_notes.md (DATA_DIR = {DATA_DIR})

- Ngày thu cuối (giờ VN): {collect_last:%d/%m/%Y}. S1 chạy {START:%d/%m/%Y} đến {end_s1:%d/%m/%Y} ({len(idx)} ngày, không thiếu ngày nào).
- S2 dùng video thuộc H, bỏ video đăng trong 7 ngày cuối, kết thúc {end_s2:%d/%m/%Y}; ngày không có video H: {S2_nan} ngày (NaN).
- Số kênh đủ lịch sử (dưới {MAX_PER_CHANNEL} video in_history): {n_channels} / {n_channels_all} kênh; số video in_history của các kênh này: {len(vk):,}; trong H: {len(Hk):,}.
- N1: ngày NaN = {', '.join(nan_n1)} (ngày đầu 22/10, ngày thiếu chụp và ngày ngay sau ngày thiếu). Số điểm hợp lệ N1: {int(st['N1'].notna().sum())}.
- N2: ngày NaN = {', '.join(nan_n2) if nan_n2 else 'không có'}; số điểm hợp lệ: {int(st['N2'].notna().sum())}. Giờ chụp không cố định 20:00 (xem cột snapshot_time_vn), nên N2 chịu nhiễu theo giờ chụp.
- Ngày thiếu chụp Trending: {', '.join(d.strftime('%d/%m') for d in missing)}.
- Cách diễn giải cần Khôi xác nhận: (a) "ngày thu cuối trừ ngày cuối" hiểu là bỏ đúng ngày thu cuối; (b) n_videos = số video H dùng tính S2 mỗi ngày; n_channels = số kênh đủ lịch sử (hằng số).
""")
print(open(os.path.join(OUT, "series_notes.md"), encoding="utf-8").read())
print(daily.describe().T[["count", "mean", "min", "max"]])
print(st)
