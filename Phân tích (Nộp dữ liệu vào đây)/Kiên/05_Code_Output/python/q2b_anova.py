# -*- coding: utf-8 -*-
"""q2b_anova.py - Q2b: ANOVA một yếu tố của lv_adj theo pub_slot (5 nhóm) và category_name (N5).
Levene -> ANOVA kinh điển + Welch ANOVA -> Games-Howell (Tukey HSD chỉ đúng khi phương sai đều) -> Kruskal-Wallis.
Chạy từ 05_Code_Output:  python python/q2b_anova.py
"""
import os
import itertools
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
import pingouin as pg

from prep import DATA_DIR, OUT_ROOT, read_master, prep, SLOT_ORDER, MIN_GROUP_N

OUT = os.path.join(OUT_ROOT, "q2b")
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "savefig.dpi": 300})
np.random.seed(42)
ALPHA = 0.05


def group_table(d, col, order):
    g = d.groupby(col, observed=True).lv_adj
    t = g.agg(n="count", mean_lv_adj="mean", sd="std").reindex(order)
    t["se"] = t.sd / np.sqrt(t.n)
    q = stats.t.ppf(0.975, t.n - 1)
    t["ci_low"] = t.mean_lv_adj - q * t.se
    t["ci_high"] = t.mean_lv_adj + q * t.se
    t["median_lv_adj"] = g.median().reindex(order)
    return t.reset_index().rename(columns={col: "group"})


def omnibus(d, col, order, factor, label):
    groups = [d.loc[d[col] == k, "lv_adj"].to_numpy() for k in order]
    N, k = sum(len(x) for x in groups), len(groups)
    lev = stats.levene(*groups, center="median")
    fo = stats.f_oneway(*groups)
    grand = d.loc[d[col].isin(order), "lv_adj"].mean()
    ssb = sum(len(x) * (x.mean() - grand) ** 2 for x in groups)
    sst = sum(((x - grand) ** 2).sum() for x in groups)
    eta2 = ssb / sst
    wa = pg.welch_anova(data=d[d[col].isin(order)], dv="lv_adj", between=col).iloc[0]
    kw = stats.kruskal(*groups)
    return {"dataset": label, "factor": factor, "k_groups": k, "N": N,
            "levene_F": lev.statistic, "levene_df1": k - 1, "levene_df2": N - k, "levene_p": lev.pvalue,
            "anova_F": fo.statistic, "anova_df1": k - 1, "anova_df2": N - k, "anova_p": fo.pvalue,
            "eta2": eta2, "omega2": (ssb - (k - 1) * ((sst - ssb) / (N - k))) / (sst + (sst - ssb) / (N - k)),
            "welch_F": wa["F"], "welch_df1": wa["ddof1"], "welch_df2": wa["ddof2"], "welch_p": wa["p_unc"] if "p_unc" in wa.index else wa["p-unc"],
            "kw_H": kw.statistic, "kw_df": k - 1, "kw_p": kw.pvalue, "eta2_H": (kw.statistic - k + 1) / (N - k)}


def games_howell(d, col, order, factor, label):
    dd = d[d[col].isin(order)]
    gh = pg.pairwise_gameshowell(data=dd, dv="lv_adj", between=col)
    stat = group_table(dd, col, order).set_index("group")
    k = len(order)
    rows = []
    rank = {g: i for i, g in enumerate(order)}
    for _, r in gh.iterrows():
        a, b = r["A"], r["B"]
        if rank[a] > rank[b]:
            a, b, sign = b, a, -1
        else:
            sign = 1
        diff = sign * r["diff"]              # = mean(a) - mean(b), a đứng trước b theo thứ tự nhóm
        se = np.sqrt(stat.loc[a, "sd"] ** 2 / stat.loc[a, "n"] + stat.loc[b, "sd"] ** 2 / stat.loc[b, "n"])
        crit = stats.studentized_range.ppf(1 - ALPHA, k, r["df"]) / np.sqrt(2)
        sp = np.sqrt((stat.loc[a, "sd"] ** 2 + stat.loc[b, "sd"] ** 2) / 2)
        rows.append({"dataset": label, "factor": factor, "group1": a, "group2": b, "n1": int(stat.loc[a, "n"]),
                     "n2": int(stat.loc[b, "n"]), "diff": diff, "ci_low": diff - crit * se, "ci_high": diff + crit * se,
                     "df": r["df"], "p_adj": r["pval"], "d_pair": diff / sp})
    out = pd.DataFrame(rows)
    out["significant"] = out.p_adj < ALPHA
    return out


def plot_means(gm_all, title_suffix, fname, n_total):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), gridspec_kw={"width_ratios": [1, 1.5]})
    for ax, fac, ttl in zip(axes, ["pub_slot", "category_name"], ["Khung giờ đăng", "Thể loại"]):
        t = gm_all[gm_all.factor == fac].copy()
        if fac == "category_name":
            t = t.sort_values("mean_lv_adj")
        ypos = np.arange(len(t))
        ax.errorbar(t.mean_lv_adj, ypos, xerr=[t.mean_lv_adj - t.ci_low, t.ci_high - t.mean_lv_adj], fmt="o",
                    color="#1f77b4", ecolor="#1f77b4", capsize=3)
        ax.axvline(0, color="gray", ls="--", lw=0.8)
        ax.set_yticks(ypos); ax.set_yticklabels([f"{g} (n={n:,})" for g, n in zip(t.group, t.n)], fontsize=8)
        ax.set_xlabel("Trung bình lv_adj (KTC 95%)"); ax.set_title(ttl)
    fig.suptitle(f"Q2b – Trung bình lv_adj theo nhóm {title_suffix}")
    fig.text(0.01, 0.005, f"Nguồn: {DATA_DIR}/videos_master.csv, H (n_H = {n_total:,}); outputs/q2b/q2b_group_means_python.csv",
             fontsize=7, color="gray")
    fig.tight_layout(rect=(0, 0.02, 1, 0.96)); fig.savefig(os.path.join(OUT, fname)); plt.close(fig)


def main():
    H = prep(read_master())
    print(f"n_H = {len(H)}  (DATA_DIR={DATA_DIR})")
    H["pub_slot"] = pd.Categorical(H.pub_slot, categories=SLOT_ORDER, ordered=True)
    assert H.pub_slot.isna().sum() == 0, "pub_slot có giá trị lạ"
    subsets = {"H_toan_bo": H, "H_bo_video_ngan": H[~H.is_short_60]}
    omn, means, pairs, dropped = [], [], [], []
    for label, d in subsets.items():
        for fac in ["pub_slot", "category_name"]:
            if fac == "pub_slot":
                order = SLOT_ORDER
            else:
                cnt = d.category_name.value_counts()
                order = sorted(cnt[cnt >= MIN_GROUP_N].index)
                for c in cnt[cnt < MIN_GROUP_N].index:
                    dropped.append({"dataset": label, "factor": fac, "group": c, "n": int(cnt[c]), "ly_do": f"n < {MIN_GROUP_N}"})
                d = d[d.category_name.isin(order)].assign(category_name=lambda x: pd.Categorical(x.category_name, categories=order))
            omn.append(omnibus(d, fac, order, fac, label))
            gt = group_table(d, fac, order); gt.insert(0, "factor", fac); gt.insert(0, "dataset", label)
            means.append(gt)
            pairs.append(games_howell(d, fac, order, fac, label))
    omn = pd.DataFrame(omn); means = pd.concat(means); pairs = pd.concat(pairs)
    omn.to_csv(os.path.join(OUT, "q2b_anova_results_python.csv"), index=False, encoding="utf-8-sig")
    means.to_csv(os.path.join(OUT, "q2b_group_means_full_python.csv"), index=False, encoding="utf-8-sig")
    # CSV cho Power BI (mục 0.5): factor, group, n, mean_lv_adj, ci_low, ci_high  (quần thể H đầy đủ)
    means[means.dataset == "H_toan_bo"][["factor", "group", "n", "mean_lv_adj", "ci_low", "ci_high"]].to_csv(
        os.path.join(OUT, "q2b_group_means_python.csv"), index=False, encoding="utf-8-sig")
    pairs.to_csv(os.path.join(OUT, "q2b_gameshowell_all_python.csv"), index=False, encoding="utf-8-sig")
    pairs[pairs.significant].sort_values(["dataset", "factor", "p_adj"]).to_csv(
        os.path.join(OUT, "q2b_gameshowell_significant_python.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(dropped, columns=["dataset", "factor", "group", "n", "ly_do"]).drop_duplicates().to_csv(
        os.path.join(OUT, "q2b_dropped_groups_python.csv"), index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 250)
    print(omn.T.to_string()); print(pairs.groupby(["dataset", "factor"]).significant.agg(["sum", "count"]))

    plot_means(means[means.dataset == "H_toan_bo"], "(toàn bộ quần thể H)", "q2b_group_means_python.png", len(H))
    plot_means(means[means.dataset == "H_bo_video_ngan"], "(bỏ video ngắn ≤ 60 giây)", "q2b_group_means_noshort_python.png",
               int((~H.is_short_60).sum()))
    with open(os.path.join(OUT, "env_python.txt"), "w") as f:
        import sys, scipy, matplotlib
        f.write(f"python {sys.version.split()[0]}\npandas {pd.__version__}\nnumpy {np.__version__}\n"
                f"scipy {scipy.__version__}\npingouin {pg.__version__}\nmatplotlib {matplotlib.__version__}\n")


if __name__ == "__main__":
    main()
