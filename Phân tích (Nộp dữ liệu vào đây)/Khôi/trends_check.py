"""trends_check.py - K10: đối chiếu Google Trends với S2 theo tuần (Mục 3.6).
Tuần của Trends bắt đầu Chủ nhật; S2 hàng ngày được gộp theo cùng tuần (trung bình các ngày), chỉ giữ tuần đủ 7 ngày có S2
và nằm trong khoảng 01/01/2024 trở đi. Spearman theo mức (chính) và theo sai phân bậc 1 (kiểm tra độ vững, vì hai chuỗi đều có xu hướng).
Dùng: python trends_check.py [series_dir] [trends_raw.csv] [out_dir]   (mặc định outputs/series, trends_raw.csv, outputs/trends_check)
"""
import os, sys
import numpy as np, pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

SDIR = sys.argv[1] if len(sys.argv) > 1 else "outputs/series"
TRAW = sys.argv[2] if len(sys.argv) > 2 else "trends_raw.csv"
OUT = sys.argv[3] if len(sys.argv) > 3 else "outputs/trends_check"
os.makedirs(OUT, exist_ok=True)

d = pd.read_csv(os.path.join(SDIR, "series_daily.csv"), parse_dates=["date"], index_col="date")
s2 = d["S2"].dropna()
# tuần bắt đầu Chủ nhật: pandas dayofweek Thứ Hai = 0 ... Chủ nhật = 6
week_start = s2.index - pd.to_timedelta((s2.index.dayofweek + 1) % 7, unit="D")
g = s2.groupby(week_start)
wk = pd.DataFrame({"S2_week": g.mean(), "n_days": g.size(), "n_videos": d.loc[s2.index, "n_videos"].groupby(week_start).sum()})
wk["S2_week_w"] = (s2 * d.loc[s2.index, "n_videos"]).groupby(week_start).sum() / wk["n_videos"]  # trung bình có trọng số số video (kiểm tra)
wk = wk[(wk["n_days"] == 7) & (wk.index >= "2024-01-01")]

tr = pd.read_csv(TRAW, parse_dates=["date"], encoding="utf-8-sig")
rows, merged = [], []
for kw, t in tr.groupby("keyword", sort=False):
    m = wk.join(t.set_index("date")["interest"], how="inner").dropna()
    m["keyword"] = kw; m.index.name = "week_start"; merged.append(m.reset_index())
    rho, p = stats.spearmanr(m["interest"], m["S2_week"])
    rho_w, _ = stats.spearmanr(m["interest"], m["S2_week_w"])
    dm = m[["interest", "S2_week"]].diff().dropna()
    rho_d, p_d = stats.spearmanr(dm["interest"], dm["S2_week"])
    rows.append(dict(keyword=kw, n_weeks=len(m), tu=m.index.min().date(), den=m.index.max().date(), spearman_rho=rho, p=p,
                     rho_trong_so=rho_w, rho_sai_phan=rho_d, p_sai_phan=p_d, trends_std=m["interest"].std()))
res = pd.DataFrame(rows)
res["p_holm"] = multipletests(res["p"], method="holm")[1]
res.to_csv(os.path.join(OUT, "trends_check_results.csv"), index=False, float_format="%.4f")
pd.concat(merged).to_csv(os.path.join(OUT, "trends_check_weekly.csv"), index=False, float_format="%.5f")

# 1 hình, mỗi từ khóa một ô hai trục
kws = res["keyword"].tolist()
fig, axes = plt.subplots(len(kws), 1, figsize=(10, 2.3 * len(kws)), sharex=True)
for ax, kw in zip(np.atleast_1d(axes), kws):
    m = pd.concat(merged); m = m[m.keyword == kw].set_index("week_start")
    ax.plot(m.index, m["S2_week"], color="#2b6cb0", lw=1.4); ax.set_ylabel("S2 tuần", color="#2b6cb0", fontsize=8)
    ax2 = ax.twinx(); ax2.plot(m.index, m["interest"], color="#dd6b20", lw=1.2); ax2.set_ylabel("Trends", color="#dd6b20", fontsize=8)
    r = res[res.keyword == kw].iloc[0]; ax.set_title(f"{kw}: Spearman ρ = {r.spearman_rho:.2f} (n = {int(r.n_weeks)} tuần)", fontsize=9)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "trends_check.png"), dpi=150); plt.close()
pd.set_option("display.width", 200); print(res.round(4).to_string(index=False))
print("\nTuần S2 đủ 7 ngày:", len(wk), "từ", wk.index.min().date(), "đến", wk.index.max().date())
