# -*- coding: utf-8 -*-
"""q3a_regression.py - Q3a: hồi quy tuyến tính bội cho log_views (N6).
log_views ~ log10(age_days_last) + log_subs + log10(duration_sec) + tags_count + title_len + title_upper_ratio
            + title_has_question + title_has_exclaim + title_has_digit + title_has_emoji
            + pub_is_weekend + pub_slot + category_name + is_short_60
Sai số chuẩn bền vững theo kênh (cluster-robust, cov_type="cluster"; đề cương ghi HAC -> sửa, vì các video cùng kênh tương quan nhau).
Nhóm tham chiếu: pub_slot = "Tối 18-21h", category_name = "Gaming".
Chạy từ 05_Code_Output:  python python/q3a_regression.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
import statsmodels.api as sm

from prep import DATA_DIR, OUT_ROOT, read_master, prep, SLOT_ORDER, MIN_GROUP_N

OUT = os.path.join(OUT_ROOT, "q3a")
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "savefig.dpi": 300})
np.random.seed(42)

REF_SLOT, REF_CAT = "Tối 18-21h", "Gaming"
NUM_TERMS = ["log10(age_days_last)", "log_subs", "log10(duration_sec)", "tags_count", "title_len", "title_upper_ratio",
             "title_has_question", "title_has_exclaim", "title_has_digit", "title_has_emoji", "pub_is_weekend",
             "is_short_60"]
FACTOR_TERMS = ["pub_slot", "category_name"]
ALL_TERMS = NUM_TERMS + FACTOR_TERMS
PROTECTED = {"log10(age_days_last)"}
GROUPS = {"kenh": ["log_subs"],
          "noi_dung": ["log10(duration_sec)", "tags_count", "title_len", "title_upper_ratio", "title_has_question",
                       "title_has_exclaim", "title_has_digit", "title_has_emoji", "is_short_60"],
          "thoi_gian": ["pub_is_weekend", "pub_slot"],
          "the_loai": ["category_name"]}


def build_columns(d):
    """Trả về dict term -> DataFrame các cột (tên chuẩn hóa giống bản R)."""
    cols = {}
    cols["log10(age_days_last)"] = pd.DataFrame({"log10(age_days_last)": np.log10(d.age_days_last)})
    cols["log10(duration_sec)"] = pd.DataFrame({"log10(duration_sec)": np.log10(d.duration_sec)})
    for t in ["log_subs", "tags_count", "title_len", "title_upper_ratio"]:
        cols[t] = pd.DataFrame({t: d[t].astype(float)})
    for t in ["title_has_question", "title_has_exclaim", "title_has_digit", "title_has_emoji", "pub_is_weekend", "is_short_60"]:
        cols[t] = pd.DataFrame({t: d[t].astype(float)})
    for t, ref in [("pub_slot", REF_SLOT), ("category_name", REF_CAT)]:
        lv = [x for x in (SLOT_ORDER if t == "pub_slot" else sorted(d[t].unique())) if x != ref]
        pre = "pub_slot" if t == "pub_slot" else "category"
        cols[t] = pd.DataFrame({f"{pre}={x}": (d[t] == x).astype(float) for x in lv})
    return cols


def design(cols, terms):
    X = pd.concat([cols[t] for t in terms], axis=1)
    return sm.add_constant(X, has_constant="add").rename(columns={"const": "Intercept"})


def fit(y, cols, terms, groups):
    X = design(cols, terms)
    return sm.OLS(y, X).fit(), sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": groups, "use_correction": True}, use_t=False)


def vif_tables(cols, terms):
    X = pd.concat([cols[t] for t in terms], axis=1)
    R = np.corrcoef(X.to_numpy(float), rowvar=False)
    vcol = pd.DataFrame({"column": X.columns, "vif": np.diag(np.linalg.inv(R))})
    detR = np.linalg.det(R)
    rows, start = [], 0
    for t in terms:
        k = cols[t].shape[1]; idx = list(range(start, start + k)); rest = [i for i in range(R.shape[0]) if i not in idx]
        gv = np.linalg.det(R[np.ix_(idx, idx)]) * (np.linalg.det(R[np.ix_(rest, rest)]) if rest else 1.0) / detR
        rows.append({"term": t, "df": k, "gvif": gv, "adj_vif": gv ** (1.0 / k)})   # adj_vif = GVIF^(1/df) = (GVIF^(1/2df))^2, so sánh được với VIF
        start += k
    return vcol, pd.DataFrame(rows)


def main():
    H = prep(read_master())
    print(f"n_H = {len(H)}  (DATA_DIR={DATA_DIR})")
    cnt = H.category_name.value_counts()
    keep = cnt[cnt >= MIN_GROUP_N].index
    dropped_cat = cnt[cnt < MIN_GROUP_N]
    D = H[H.category_name.isin(keep)].copy()
    assert D.pub_slot.isin(SLOT_ORDER).all() and (D.duration_sec > 0).all()
    print(f"Loại {int(dropped_cat.sum())} video thuộc thể loại n<{MIN_GROUP_N}: {dict(dropped_cat)}; n mô hình = {len(D)}")
    y = D.log_views.to_numpy(float)
    g = pd.factorize(D.channel_id)[0]
    cols = build_columns(D)

    # --- vòng lặp VIF: loại biến có VIF hiệu chỉnh > 10 (không bao giờ loại log10(age)) ---
    terms, removed = list(ALL_TERMS), []
    while True:
        vcol, vterm = vif_tables(cols, terms)
        cand = vterm[~vterm.term.isin(PROTECTED)].sort_values("adj_vif", ascending=False)
        if cand.iloc[0].adj_vif > 10:
            removed.append(cand.iloc[0].term); terms.remove(cand.iloc[0].term)
        else:
            break
    vterm["vuot_5"] = vterm.adj_vif > 5; vterm["vuot_10"] = vterm.adj_vif > 10
    vcol.to_csv(os.path.join(OUT, "q3a_vif_columns_python.csv"), index=False, encoding="utf-8-sig")
    vterm.to_csv(os.path.join(OUT, "q3a_vif_python.csv"), index=False, encoding="utf-8-sig")

    ols, rob = fit(y, cols, terms, g)
    X = design(cols, terms)
    sdx = X.std(ddof=1); sdy = y.std(ddof=1)
    ci = rob.conf_int()
    coef = pd.DataFrame({"term": X.columns, "coef": ols.params.values, "se_ols": ols.bse.values, "se_cluster": rob.bse.values,
                         "z_cluster": rob.tvalues.values, "p_cluster": rob.pvalues.values,
                         "ci_low": ci.iloc[:, 0].values, "ci_high": ci.iloc[:, 1].values})
    coef["beta_std"] = np.where(coef.term == "Intercept", np.nan, coef.coef * sdx.reindex(coef.term).values / sdy)
    coef["ti_so_se"] = coef.se_cluster / coef.se_ols
    coef.to_csv(os.path.join(OUT, "q3a_coefficients_python.csv"), index=False, encoding="utf-8-sig")

    model = pd.DataFrame([{"n": int(ols.nobs), "k_tham_so": int(ols.df_model + 1), "n_clusters": int(g.max() + 1),
                           "r2": ols.rsquared, "adj_r2": ols.rsquared_adj, "rmse": np.sqrt(np.mean(ols.resid**2)), "residual_sd": np.sqrt(ols.mse_resid),
                           "bien_bi_loai_do_VIF": ";".join(removed) or "khong",
                           "n_video_bi_loai_the_loai_nho": int(dropped_cat.sum())}])
    model.to_csv(os.path.join(OUT, "q3a_model_python.csv"), index=False, encoding="utf-8-sig")

    # --- đóng góp theo nhóm: mức giảm R² khi bỏ nhóm (giữ log10(age)) + R² chỉ gồm age + nhóm ---
    r2_full = ols.rsquared
    r2_age = sm.OLS(y, design(cols, ["log10(age_days_last)"])).fit().rsquared
    rows = []
    for gname, gterms in GROUPS.items():
        gt = [t for t in gterms if t in terms]
        rest = [t for t in terms if t not in gt]
        r2_wo = sm.OLS(y, design(cols, rest)).fit().rsquared
        r2_only = sm.OLS(y, design(cols, ["log10(age_days_last)"] + gt)).fit().rsquared
        rows.append({"nhom": gname, "bien": ";".join(gt), "R2_day_du": r2_full, "R2_khi_bo_nhom": r2_wo,
                     "giam_R2": r2_full - r2_wo, "R2_chi_age_va_nhom": r2_only, "tang_R2_so_voi_chi_age": r2_only - r2_age})
    contrib = pd.DataFrame(rows).sort_values("giam_R2", ascending=False)
    contrib.attrs["r2_age"] = r2_age
    contrib.to_csv(os.path.join(OUT, "q3a_group_contribution_python.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame([{"R2_chi_log10_age": r2_age}]).to_csv(os.path.join(OUT, "q3a_r2_age_only_python.csv"), index=False, encoding="utf-8-sig")

    pd.set_option("display.width", 220); pd.set_option("display.max_rows", 100)
    print(model.T); print(coef.round(4).to_string()); print(vterm.round(3).to_string()); print(contrib.round(4).to_string())
    print("R2 chỉ gồm log10(age):", round(r2_age, 4))

    # --- sensitivity: 2 video có title_upper_ratio > 1 (chữ cái Unicode đặc biệt) ---
    out = D.title_upper_ratio > 1
    if out.any() and "title_upper_ratio" in terms:
        Xs = design({k: v[~out.values] for k, v in cols.items()}, terms)
        m2 = sm.OLS(y[~out.values], Xs).fit(cov_type="cluster", cov_kwds={"groups": g[~out.values]}, use_t=False)
        print("Bỏ", int(out.sum()), "video title_upper_ratio>1: hệ số title_upper_ratio",
              round(m2.params["title_upper_ratio"], 4), "so với", round(ols.params["title_upper_ratio"], 4))

    # --- hình chẩn đoán ---
    res = ols.resid.to_numpy(); fv = ols.fittedvalues.to_numpy()
    rng = np.random.default_rng(42)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    r_sorted = np.sort(res); q = stats.norm.ppf((np.arange(1, len(res) + 1) - 0.5) / len(res))
    axes[0].scatter(q, r_sorted / res.std(ddof=1), s=1.5, alpha=0.4, color="#1f77b4", rasterized=True)
    axes[0].plot([-4, 4], [-4, 4], color="#d62728", lw=1)
    axes[0].set_xlabel("Phân vị lý thuyết (chuẩn)"); axes[0].set_ylabel("Phần dư chuẩn hóa"); axes[0].set_title("QQ-plot phần dư")
    s = rng.choice(len(res), size=min(20000, len(res)), replace=False)
    axes[1].scatter(fv[s], res[s], s=2, alpha=0.3, color="#1f77b4", rasterized=True)
    axes[1].axhline(0, color="#d62728", lw=1)
    axes[1].set_xlabel("Giá trị dự đoán của log_views"); axes[1].set_ylabel("Phần dư"); axes[1].set_title("Phần dư theo giá trị dự đoán (mẫu 20.000 điểm)")
    fig.suptitle(f"Q3a – Chẩn đoán phần dư (n = {len(res):,}; R² = {ols.rsquared:.3f})")
    fig.text(0.01, 0.005, f"Nguồn: {DATA_DIR}/videos_master.csv, H; outputs/q3a/q3a_coefficients_python.csv", fontsize=7, color="gray")
    fig.tight_layout(rect=(0, 0.02, 1, 0.96)); fig.savefig(os.path.join(OUT, "q3a_diagnostics_python.png")); plt.close(fig)

    # --- hình đóng góp theo nhóm + hệ số chuẩn hóa ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    c = contrib.sort_values("giam_R2")
    axes[0].barh(c.nhom, c.giam_R2, color="#1f77b4")
    for i, v in enumerate(c.giam_R2): axes[0].text(v, i, f" {v:.3f}", va="center", fontsize=8)
    axes[0].set_xlabel("Mức giảm R² khi bỏ nhóm"); axes[0].set_title("Đóng góp của từng nhóm nhân tố")
    b = coef[(coef.term != "Intercept") & ~coef.term.str.contains("=")].sort_values("beta_std")
    axes[1].barh(b.term, b.beta_std, color=np.where(b.beta_std >= 0, "#1f77b4", "#d62728"))
    axes[1].axvline(0, color="gray", lw=0.8); axes[1].set_xlabel("Hệ số chuẩn hóa (β*)"); axes[1].set_title("Biến số / nhị phân (không gồm thể loại, khung giờ)")
    axes[1].tick_params(axis="y", labelsize=8)
    fig.suptitle("Q3a – Nhân tố nào mạnh nhất?")
    fig.text(0.01, 0.005, f"Nguồn: {DATA_DIR}/videos_master.csv, H; outputs/q3a/q3a_group_contribution_python.csv", fontsize=7, color="gray")
    fig.tight_layout(rect=(0, 0.02, 1, 0.96)); fig.savefig(os.path.join(OUT, "q3a_contribution_python.png")); plt.close(fig)

    with open(os.path.join(OUT, "env_python.txt"), "w") as f:
        import sys, scipy, statsmodels, matplotlib
        f.write(f"python {sys.version.split()[0]}\npandas {pd.__version__}\nnumpy {np.__version__}\nscipy {scipy.__version__}\n"
                f"statsmodels {statsmodels.__version__}\nmatplotlib {matplotlib.__version__}\n")


if __name__ == "__main__":
    main()
