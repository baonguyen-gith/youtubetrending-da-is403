# -*- coding: utf-8 -*-
"""q2a_tests.py - Q2a: t-test lv_adj giữa video đăng cuối tuần và ngày thường (N4).
Chạy từ 05_Code_Output:  python python/q2a_tests.py
Đầu ra: outputs/q2a/ (CSV *_python.csv, hình *_python.png)
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
import statsmodels.api as sm

from prep import DATA_DIR, OUT_ROOT, read_master, prep

OUT = os.path.join(OUT_ROOT, "q2a")
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "figure.dpi": 100, "savefig.dpi": 300})
np.random.seed(42)


def cohen_d(x, y):
    n1, n2 = len(x), len(y)
    v1, v2 = np.var(x, ddof=1), np.var(y, ddof=1)
    sp = np.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    d = (np.mean(x) - np.mean(y)) / sp
    se = np.sqrt((n1 + n2) / (n1 * n2) + d ** 2 / (2 * (n1 + n2)))
    return d, d - 1.959963984540054 * se, d + 1.959963984540054 * se


def run_tests(d, label):
    """x = cuối tuần, y = ngày thường; chênh lệch = trung bình(cuối tuần) - trung bình(ngày thường)."""
    x = d.loc[d.pub_is_weekend, "lv_adj"].to_numpy()
    y = d.loc[~d.pub_is_weekend, "lv_adj"].to_numpy()
    w = stats.ttest_ind(x, y, equal_var=False)
    ci = w.confidence_interval(0.95)
    dd, dlo, dhi = cohen_d(x, y)
    lev = stats.levene(x, y, center="median")
    mw = stats.mannwhitneyu(x, y, alternative="two-sided", use_continuity=True, method="asymptotic")
    return {
        "dataset": label, "n_weekend": len(x), "n_weekday": len(y),
        "mean_weekend": x.mean(), "mean_weekday": y.mean(), "sd_weekend": x.std(ddof=1), "sd_weekday": y.std(ddof=1),
        "median_weekend": np.median(x), "median_weekday": np.median(y),
        "diff_mean": x.mean() - y.mean(), "ci_low": ci.low, "ci_high": ci.high,
        "welch_t": w.statistic, "welch_df": w.df, "welch_p": w.pvalue,
        "cohen_d": dd, "d_ci_low": dlo, "d_ci_high": dhi,
        "levene_F": lev.statistic, "levene_df1": 1, "levene_df2": len(x) + len(y) - 2, "levene_p": lev.pvalue,
        "mw_U": mw.statistic, "mw_p": mw.pvalue, "cliffs_delta": 2 * mw.statistic / (len(x) * len(y)) - 1,
    }


def cluster_ols(d, label, demean=False):
    """OLS lv_adj ~ pub_is_weekend với sai số chuẩn bền vững theo kênh (kiểm tra bổ sung)."""
    y = d.lv_adj.to_numpy(float)
    x = d.pub_is_weekend.to_numpy(float)
    g = pd.factorize(d.channel_id)[0]
    if demean:   # hiệu ứng cố định theo kênh: so sánh TRONG cùng một kênh
        y = y - pd.Series(y).groupby(g).transform("mean").to_numpy()
        x = x - pd.Series(x).groupby(g).transform("mean").to_numpy()
        X = x.reshape(-1, 1)
        names = ["pub_is_weekend"]
    else:
        X = sm.add_constant(x)
        names = ["Intercept", "pub_is_weekend"]
    m = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": g, "use_correction": True}, use_t=False)
    i = names.index("pub_is_weekend")
    ci = m.conf_int()[i]
    return {"dataset": label, "model": "FE_theo_kenh" if demean else "OLS_cluster", "n": len(y),
            "n_clusters": int(g.max() + 1), "coef": m.params[i], "se": m.bse[i], "z": m.tvalues[i],
            "p": m.pvalues[i], "ci_low": ci[0], "ci_high": ci[1]}


def main():
    H = prep(read_master())
    print(f"n_H = {len(H)}  (DATA_DIR={DATA_DIR})")
    subsets = {"H_toan_bo": H, "H_bo_video_ngan": H[~H.is_short_60]}
    res = pd.DataFrame([run_tests(d, k) for k, d in subsets.items()])
    res.to_csv(os.path.join(OUT, "q2a_results_python.csv"), index=False, encoding="utf-8-sig")
    cl = pd.DataFrame([cluster_ols(d, k, dm) for k, d in subsets.items() for dm in (False, True)])
    cl.to_csv(os.path.join(OUT, "q2a_cluster_python.csv"), index=False, encoding="utf-8-sig")
    # mô tả nhóm
    desc = H.groupby("pub_is_weekend").lv_adj.agg(n="count", mean="mean", median="median", sd="std").reset_index()
    desc.to_csv(os.path.join(OUT, "q2a_descriptives_python.csv"), index=False, encoding="utf-8-sig")
    print(res.T.to_string()); print(cl.to_string())

    # ---- Hình 1: QQ-plot theo nhóm ----
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6), sharey=True)
    for ax, (lab, flag) in zip(axes, [("Ngày thường", False), ("Cuối tuần", True)]):
        v = np.sort(H.loc[H.pub_is_weekend == flag, "lv_adj"].to_numpy())
        q = stats.norm.ppf((np.arange(1, len(v) + 1) - 0.5) / len(v))
        ax.scatter(q, v, s=2, alpha=0.4, color="#1f77b4", rasterized=True)
        lo, hi = np.percentile(v, [25, 75]); ql, qh = stats.norm.ppf([.25, .75])
        sl = (hi - lo) / (qh - ql); ic = lo - sl * ql
        ax.plot([-4, 4], [ic - 4 * sl, ic + 4 * sl], color="#d62728", lw=1)
        ax.set_title(f"{lab} (n = {len(v):,})"); ax.set_xlabel("Phân vị lý thuyết (chuẩn)")
    axes[0].set_ylabel("lv_adj (log10 lượt xem đã hiệu chỉnh tuổi)")
    fig.suptitle("Q2a – QQ-plot của lv_adj theo nhóm ngày đăng")
    fig.text(0.01, 0.005, f"Nguồn: {DATA_DIR}/videos_master.csv, quần thể H (n_H = {len(H):,}); outputs/q2a/", fontsize=7, color="gray")
    fig.tight_layout(rect=(0, 0.02, 1, 0.97)); fig.savefig(os.path.join(OUT, "q2a_qqplot_python.png")); plt.close(fig)

    # ---- Hình 2: phân phối + trung bình ----
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    bins = np.linspace(-5, 5, 101)
    for lab, flag, col in [("Ngày thường", False, "#1f77b4"), ("Cuối tuần", True, "#ff7f0e")]:
        v = H.loc[H.pub_is_weekend == flag, "lv_adj"]
        ax.hist(v, bins=bins, density=True, alpha=0.5, color=col, label=f"{lab} (TB = {v.mean():.3f})")
        ax.axvline(v.mean(), color=col, lw=1.5)
    ax.set_xlabel("lv_adj"); ax.set_ylabel("Mật độ"); ax.legend()
    r = res.iloc[0]
    ax.set_title(f"Q2a – Phân phối lv_adj: chênh lệch TB = {r.diff_mean:.3f}, Cohen's d = {r.cohen_d:.3f}")
    fig.text(0.01, 0.005, f"Nguồn: {DATA_DIR}/videos_master.csv, H (n_H = {len(H):,}); outputs/q2a/q2a_results_python.csv", fontsize=7, color="gray")
    fig.tight_layout(rect=(0, 0.02, 1, 1)); fig.savefig(os.path.join(OUT, "q2a_distribution_python.png")); plt.close(fig)

    with open(os.path.join(OUT, "env_python.txt"), "w") as f:
        import sys, scipy, statsmodels, matplotlib
        f.write(f"python {sys.version.split()[0]}\npandas {pd.__version__}\nnumpy {np.__version__}\n"
                f"scipy {scipy.__version__}\nstatsmodels {statsmodels.__version__}\nmatplotlib {matplotlib.__version__}\n")


if __name__ == "__main__":
    main()
