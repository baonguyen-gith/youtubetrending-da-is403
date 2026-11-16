# -*- coding: utf-8 -*-
"""
q3b_logistic.py - Q3b: Hồi quy Logistic cho viral_A (việc B5, Mục 5.3b của báo cáo)

Y = viral_A.   X = X_PRE (Mục 4.5).
  * Biến số được chuẩn hóa z-score (trung bình 0, sd mẫu n-1)  => OR = đổi theo mỗi +1 độ lệch chuẩn.
  * Biến nhị phân (pub_is_weekend, is_short_60, title_has_*) giữ 0/1                => OR = có so với không.
  * category_id là biến nhóm; nhóm gốc = thể loại nhiều video nhất; thể loại < MIN_CAT video gộp vào "Khác".
  * Hai mô hình bắt buộc:  M1 = đủ biến;  M2 = bỏ nhóm biến kênh (log_subs, channel_age_days, total_videos).
  * Mô hình bổ sung (độ vững, không bắt buộc): M3 = M1 nhưng pub_hour thay bằng 5 khung giờ pub_slot.
  * Sai số chuẩn bền vững theo cụm channel_id (statsmodels cov_type="cluster").

LƯU Ý - chuyển đổi log (khác nhẹ so với danh sách thô trong Bảng 4.2, cần ghi trong báo cáo):
  duration_sec -> log10(max(duration_sec,1)),  total_videos -> log10(total_videos+1)
  vì hai biến này lệch phải rất mạnh (duration tối đa ~2,3 triệu giây), z-score trên giá trị thô bị vài điểm cực đoan chi phối.
  Bản R (q3b_logistic.R) dùng đúng các chuyển đổi này.

Kết luận dùng ngôn ngữ "có liên quan", không dùng "gây ra".
"""
import os
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from prep import load_master, prep, DATA_DIR

OUT_DIR = os.environ.get("OUT_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", "q3b"))
os.makedirs(OUT_DIR, exist_ok=True)
MIN_CAT = 100                       # thể loại có ít hơn 100 video trong H -> gộp "Khác"
plt.rcParams.update({"font.family": "DejaVu Sans", "figure.dpi": 130, "savefig.bbox": "tight"})

BINARY = ["pub_is_weekend", "is_short_60", "title_has_question", "title_has_exclaim",
          "title_has_digit", "title_has_emoji", "title_has_bracket", "title_has_pipe"]
NUMERIC = ["pub_hour", "pub_dow", "pub_month", "duration_log", "tags_count", "title_len", "title_words",
           "title_upper_ratio", "title_n_hashtag", "log_subs", "channel_age_days", "total_videos_log"]
CHANNEL_GROUP = ["log_subs", "channel_age_days", "total_videos_log"]

LABELS = {
    "pub_hour": "Giờ đăng (pub_hour)", "pub_dow": "Thứ đăng (pub_dow)", "pub_month": "Tháng đăng (pub_month)",
    "pub_is_weekend": "Đăng cuối tuần", "duration_log": "log10 độ dài video (duration_sec)",
    "is_short_60": "Video ngắn (<=60s)", "tags_count": "Số thẻ tag (tags_count)",
    "title_len": "Độ dài tiêu đề (title_len)", "title_words": "Số từ tiêu đề (title_words)",
    "title_upper_ratio": "Tỷ lệ chữ HOA tiêu đề", "title_has_question": "Tiêu đề có dấu ?",
    "title_has_exclaim": "Tiêu đề có dấu !", "title_has_digit": "Tiêu đề có chữ số",
    "title_has_emoji": "Tiêu đề có emoji", "title_has_bracket": "Tiêu đề có ngoặc",
    "title_has_pipe": "Tiêu đề có ký tự |", "title_n_hashtag": "Số hashtag trong tiêu đề",
    "log_subs": "log10 số người đăng ký (log_subs)", "channel_age_days": "Tuổi kênh (channel_age_days)",
    "total_videos_log": "log10(số video của kênh + 1)",
}


def build_design(h: pd.DataFrame, hour_as_slot: bool = False):
    """Trả về (y, X_df (chưa có const), groups, thông tin). Loại dòng thiếu biến."""
    d = h.copy()
    d["duration_log"] = np.log10(d["duration_sec"].clip(lower=1))
    d["total_videos_log"] = np.log10(d["total_videos"] + 1)
    for c in BINARY:
        d[c] = d[c].astype(float)
    num = [c for c in NUMERIC if not (hour_as_slot and c == "pub_hour")]
    need = num + BINARY + ["category_name", "pub_slot", "viral_A", "channel_id"]
    n0 = len(d)
    d = d.dropna(subset=need).copy()
    n_drop = n0 - len(d)

    # biến nhóm thể loại: gộp nhóm nhỏ, nhóm gốc = nhóm đông nhất
    vc = d["category_name"].value_counts()
    small = vc[vc < MIN_CAT].index
    d["cat"] = d["category_name"].where(~d["category_name"].isin(small), "Khác")
    # nếu nhóm "Khác" quá nhỏ (< MIN_CAT) thì bỏ hẳn các video đó: nhóm cực nhỏ gây tách hoàn toàn (OR -> vô cực)
    n_khac = int((d["cat"] == "Khác").sum())
    n_removed_small_cat = 0
    if 0 < n_khac < MIN_CAT:
        n_removed_small_cat = n_khac
        d = d[d["cat"] != "Khác"].copy()
    ref = d["cat"].value_counts().index[0]
    cats = [c for c in sorted(d["cat"].unique()) if c != ref]
    X = d[num].astype(float).copy()
    X = (X - X.mean()) / X.std(ddof=1)                    # z-score
    X = pd.concat([X, d[BINARY]], axis=1)
    if hour_as_slot:
        slots = [s for s in sorted(d["pub_slot"].unique()) if s != d["pub_slot"].value_counts().index[0]]
        for s in slots:
            X["slot: " + s] = (d["pub_slot"] == s).astype(float)
    for c in cats:
        X["cat: " + c] = (d["cat"] == c).astype(float)
    info = {"n_dropped_missing": n_drop, "n_removed_small_category": n_removed_small_cat,
            "cat_reference": ref, "cat_small_merged_or_removed": list(small)}
    return d["viral_A"].astype(int), X, d["channel_id"], info


def fit_logit(y, X, groups):
    Xc = sm.add_constant(X, has_constant="add")
    codes = pd.factorize(groups)[0]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = sm.Logit(y, Xc).fit(method="newton", maxiter=100, disp=0,
                                  cov_type="cluster", cov_kwds={"groups": codes})
    return res, Xc


def coef_table(res) -> pd.DataFrame:
    ci = res.conf_int()
    t = pd.DataFrame({"coef": res.params, "se_cluster": res.bse, "z": res.tvalues, "p": res.pvalues,
                      "OR": np.exp(res.params), "OR_lo95": np.exp(ci[0]), "OR_hi95": np.exp(ci[1])})
    t.index.name = "term"
    return t.reset_index()


def vif_table(Xc: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in Xc.columns if c != "const"]
    arr = Xc.values
    vifs = [variance_inflation_factor(arr, Xc.columns.get_loc(c)) for c in cols]
    return pd.DataFrame({"term": cols, "VIF": vifs})


def fit_stats(res, y, name, n_clusters) -> dict:
    llnull = res.llnull
    return {"model": name, "n": int(res.nobs), "n_pos": int(y.sum()), "pct_pos": 100 * y.mean(),
            "n_clusters": int(n_clusters), "k_params": int(len(res.params)),
            "loglik": res.llf, "loglik_null": llnull, "AIC": res.aic, "BIC": res.bic,
            "McFadden_R2": 1 - res.llf / llnull, "converged": bool(res.mle_retvals.get("converged", True))}


def forest_plot(tab: pd.DataFrame, path: str, title: str):
    t = tab[tab["term"] != "const"].copy()
    t["label"] = [LABELS.get(x, x) for x in t["term"]]
    t = t.sort_values("OR")
    fig, ax = plt.subplots(figsize=(9, 0.28 * len(t) + 1.5))
    y = np.arange(len(t))
    sig = t["p"] < 0.05
    ax.hlines(y, t["OR_lo95"], t["OR_hi95"], color=np.where(sig, "#1F5FA8", "#9AA5B1"), lw=1.8)
    ax.scatter(t["OR"], y, color=np.where(sig, "#1F5FA8", "#9AA5B1"), zorder=3, s=22)
    ax.axvline(1, color="grey", ls="--", lw=0.8)
    ax.set_xscale("log"); ax.set_yticks(y); ax.set_yticklabels(t["label"], fontsize=7.5)
    ax.set_xlabel("Odds ratio (thang log), CI 95% bền vững theo kênh; xanh đậm: p < 0,05")
    ax.set_title(title, fontsize=10)
    fig.savefig(path); plt.close(fig)


def main():
    H = prep(load_master())
    n_H = len(H)
    print(f"DATA_DIR={DATA_DIR} | n_H={n_H:,} | viral_A dương={int(H['viral_A'].sum()):,}")

    y, X, g, info = build_design(H)
    print("Thông tin thiết kế:", info, "| n dùng:", len(y), "| số cụm kênh:", g.nunique())

    # ---- M1, M2
    res1, X1c = fit_logit(y, X, g)
    X2 = X.drop(columns=CHANNEL_GROUP)
    res2, X2c = fit_logit(y, X2, g)
    t1, t2 = coef_table(res1), coef_table(res2)
    vif1 = vif_table(X1c)

    # ---- M3: pub_hour -> pub_slot (độ vững)
    y3, X3, g3, _ = build_design(H, hour_as_slot=True)
    res3, X3c = fit_logit(y3, X3, g3)
    t3 = coef_table(res3)

    nclu = g.nunique()
    fit = pd.DataFrame([fit_stats(res1, y, "M1 (đủ biến)", nclu),
                        fit_stats(res2, y, "M2 (bỏ nhóm biến kênh)", nclu),
                        fit_stats(res3, y3, "M3 (pub_slot thay pub_hour)", g3.nunique())])
    # LR M1 vs M2 (tham khảo; LR kinh điển không hiệu chỉnh cụm)
    lr = 2 * (res1.llf - res2.llf)
    fit.loc[fit.model.str.startswith("M2"), "LR_vs_M1"] = lr

    # ---- bảng gộp cho báo cáo
    m = (t1[["term", "coef", "se_cluster", "p", "OR", "OR_lo95", "OR_hi95"]]
         .rename(columns={c: c + "_M1" for c in ["coef", "se_cluster", "p", "OR", "OR_lo95", "OR_hi95"]})
         .merge(t2[["term", "p", "OR", "OR_lo95", "OR_hi95"]].rename(
             columns={c: c + "_M2" for c in ["p", "OR", "OR_lo95", "OR_hi95"]}), on="term", how="left")
         .merge(vif1, on="term", how="left"))
    m["label"] = [LABELS.get(x, x.replace("cat: ", "Thể loại: ").replace("const", "Hằng số")) for x in m["term"]]
    m = m[["term", "label", "OR_M1", "OR_lo95_M1", "OR_hi95_M1", "p_M1", "OR_M2", "OR_lo95_M2", "OR_hi95_M2", "p_M2",
           "VIF", "coef_M1", "se_cluster_M1"]]
    m.to_csv(os.path.join(OUT_DIR, "q3b_or_table.csv"), index=False, encoding="utf-8-sig")
    fit.to_csv(os.path.join(OUT_DIR, "q3b_model_fit.csv"), index=False, encoding="utf-8-sig")
    t3.to_csv(os.path.join(OUT_DIR, "q3b_M3_slot_sensitivity.csv"), index=False, encoding="utf-8-sig")
    vif1.to_csv(os.path.join(OUT_DIR, "q3b_vif_M1.csv"), index=False, encoding="utf-8-sig")
    pd.Series({**info, "n_H": n_H, "n_used": int(len(y)), "n_clusters": int(nclu)}).astype(str).to_csv(
        os.path.join(OUT_DIR, "q3b_design_info.csv"), header=["value"], encoding="utf-8-sig")
    forest_plot(t1, os.path.join(OUT_DIR, "q3b_forest_M1.png"), "Odds ratio của M1 cho viral_A (biến số đã chuẩn hóa z-score)")
    forest_plot(t2, os.path.join(OUT_DIR, "q3b_forest_M2.png"), "Odds ratio của M2 (bỏ nhóm biến kênh)")

    pd.set_option("display.width", 220, "display.max_rows", 100)
    print("\n=== Độ phù hợp ===\n", fit.round(4).to_string(index=False))
    print("\n=== OR M1 / M2 ===")
    print(m[["label", "OR_M1", "OR_lo95_M1", "OR_hi95_M1", "p_M1", "OR_M2", "p_M2", "VIF"]].round(3).to_string(index=False))
    big = vif1[vif1["VIF"] > 5]
    print("\nVIF > 5:", big.round(2).to_dict("records") if len(big) else "không có")


if __name__ == "__main__":
    main()
