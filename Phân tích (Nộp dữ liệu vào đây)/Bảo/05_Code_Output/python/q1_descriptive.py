# -*- coding: utf-8 -*-
"""
q1_descriptive.py - Q1: Thống kê mô tả (việc B4, Mục 5.1 của báo cáo)

(a) Bảng n, trung bình, trung vị, độ lệch chuẩn, CV, độ lệch, độ nhọn của views, likes, comments
    (gốc và log10), tách video ngắn (is_short_60) và dài.
(b) Trung vị lv_adj và like_rate theo pub_hour, pub_dow, năm-tháng của pub_date_vn.
(c) Heatmap giờ x thứ của trung vị lv_adj; ô có n < 30 để trống.
(d) Boxplot lv_adj theo 10 thể loại nhiều video nhất.
Xuất 3 CSV cho Power BI: q1_by_hour.csv, q1_heatmap.csv, q1_by_category.csv.

QUY ƯỚC THỐNG KÊ (R phải dùng đúng công thức này để khớp 3 chữ số):
  - độ lệch chuẩn: mẫu (n-1);  CV = sd / mean
  - độ lệch  g1 = m3 / m2^1.5            (mô-men, scipy skew bias=True ; R: moments::skewness)
  - độ nhọn  g2 = m4 / m2^2 - 3          (độ nhọn dư, scipy kurtosis fisher=True bias=True)
  - log10 của likes/comments chỉ tính trên giá trị > 0 (log10(0) không xác định)
  - likes/comments rỗng (ẩn/tắt) giữ NaN, không đưa vào bảng
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

from prep import load_master, prep, DATA_DIR

OUT_DIR = os.environ.get("OUT_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", "q1"))
os.makedirs(OUT_DIR, exist_ok=True)
MIN_CELL = 30                       # ô heatmap có n < 30 để trống
DOW_LABELS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ nhật"]
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 130, "savefig.bbox": "tight"})


# ------------------------------------------------------------------ (a) bảng mô tả
def describe_series(x: pd.Series) -> dict:
    x = x.dropna().astype(float)
    n = len(x)
    mean, sd = x.mean(), x.std(ddof=1)
    return {"n": n, "mean": mean, "median": x.median(), "sd": sd,
            "cv": sd / mean if mean != 0 else np.nan,
            "skew": stats.skew(x, bias=True), "kurtosis_excess": stats.kurtosis(x, fisher=True, bias=True)}


def table_a(h: pd.DataFrame) -> pd.DataFrame:
    rows = []
    groups = {"Tất cả": h, "Video ngắn (<=60s)": h[h["is_short_60"]], "Video dài (>60s)": h[~h["is_short_60"]]}
    for gname, g in groups.items():
        for var, label in [("views", "Lượt xem"), ("likes", "Lượt thích"), ("comments", "Bình luận")]:
            raw = g[var]
            rows.append({"nhom": gname, "bien": f"{label} (gốc)", **describe_series(raw)})
            pos = raw[raw > 0]
            rows.append({"nhom": gname, "bien": f"{label} (log10)", **describe_series(np.log10(pos))})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ (b) theo giờ / thứ / tháng
def summarize_by(h: pd.DataFrame, key) -> pd.DataFrame:
    g = h.groupby(key, observed=True)
    out = g.agg(n=("lv_adj", "size"), median_lv_adj=("lv_adj", "median"),
                mean_lv_adj=("lv_adj", "mean"),
                median_lv_within_channel=("lv_within_ch", "median"),
                n_like_rate=("like_rate", "count"), median_like_rate=("like_rate", "median"))
    return out.reset_index()


# ------------------------------------------------------------------ hình
def plot_by_hour(by_hour: pd.DataFrame, path: str):
    fig, ax1 = plt.subplots(figsize=(9, 4.4))
    ax2 = ax1.twinx()
    ax2.bar(by_hour["pub_hour"], by_hour["n"], color="#D9E4F0", width=0.8, zorder=1)
    ax2.set_ylabel("Số video (cột)", color="#6B7C93")
    ax2.spines["right"].set_visible(True)
    ax1.set_zorder(ax2.get_zorder() + 1); ax1.patch.set_visible(False)
    ax1.plot(by_hour["pub_hour"], by_hour["median_lv_adj"], marker="o", color="#1F5FA8", lw=2, label="Trung vị lv_adj (so sánh giữa kênh)")
    ax1.plot(by_hour["pub_hour"], by_hour["median_lv_within_channel"], marker="s", color="#C0392B", lw=1.5, ls="--",
             label="Trung vị lv_adj sau khi trừ trung vị của kênh")
    ax1.legend(loc="lower left", fontsize=8, frameon=False)
    ax1.axhline(0, color="grey", lw=0.8, ls="--")
    ax1.set_xlabel("Giờ đăng (giờ Việt Nam)"); ax1.set_ylabel("Trung vị lv_adj")
    ax1.set_xticks(range(0, 24)); ax1.set_title("Trung vị lv_adj theo giờ đăng")
    fig.savefig(path); plt.close(fig)


def plot_by_dow(by_dow: pd.DataFrame, path: str):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([DOW_LABELS[i] for i in by_dow["pub_dow"]], by_dow["median_lv_adj"], color="#1F5FA8")
    ax.axhline(0, color="grey", lw=0.8, ls="--")
    for i, (m, n) in enumerate(zip(by_dow["median_lv_adj"], by_dow["n"])):
        ax.text(i, m + (0.004 if m >= 0 else -0.012), f"n={n:,}", ha="center", fontsize=7)
    ax.set_ylabel("Trung vị lv_adj"); ax.set_title("Trung vị lv_adj theo thứ đăng")
    plt.setp(ax.get_xticklabels(), rotation=20)
    fig.savefig(path); plt.close(fig)


def plot_by_month(by_month: pd.DataFrame, path: str):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(by_month["ym"], by_month["median_lv_adj"], marker="o", color="#1F5FA8")
    ax.axhline(0, color="grey", lw=0.8, ls="--")
    ax.set_ylabel("Trung vị lv_adj"); ax.set_title("Trung vị lv_adj theo tháng đăng (năm-tháng)")
    ax.set_xticks(range(len(by_month))); ax.set_xticklabels(by_month["ym"], rotation=60, fontsize=7)
    fig.savefig(path); plt.close(fig)


def plot_heatmap(piv: pd.DataFrame, path: str):
    fig, ax = plt.subplots(figsize=(9, 7))
    vmax = np.nanmax(np.abs(piv.values))
    im = ax.imshow(piv.values, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(7)); ax.set_xticklabels(["T2", "T3", "T4", "T5", "T6", "T7", "CN"])
    ax.set_yticks(range(24)); ax.set_yticklabels(piv.index)
    ax.set_xlabel("Thứ đăng"); ax.set_ylabel("Giờ đăng (giờ Việt Nam)")
    ax.set_title(f"Trung vị lv_adj theo giờ x thứ (ô trắng: n < {MIN_CELL})")
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.5,
                        color="white" if abs(v) > 0.6 * vmax else "black")
    fig.colorbar(im, ax=ax, label="Trung vị lv_adj")
    fig.savefig(path); plt.close(fig)


def plot_box_category(h: pd.DataFrame, top_cats, path: str):
    data = [h.loc[h["category_name"] == c, "lv_adj"].values for c in top_cats]
    fig, ax = plt.subplots(figsize=(10, 5))
    bp = ax.boxplot(data, showfliers=False, patch_artist=True, medianprops=dict(color="black"))
    for patch in bp["boxes"]:
        patch.set_facecolor("#9FC3E8")
    ax.axhline(0, color="grey", lw=0.8, ls="--")
    ax.set_xticklabels([f"{c}\n(n={len(d):,})" for c, d in zip(top_cats, data)], rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("lv_adj"); ax.set_title("Phân bố lv_adj theo 10 thể loại có nhiều video nhất (ẩn điểm ngoại lai)")
    fig.savefig(path); plt.close(fig)


# ------------------------------------------------------------------ main
def main():
    H = prep(load_master())
    # Kiểm tra độ vững: trừ trung vị lv_adj của chính kênh -> loại bỏ khác biệt do KÊNH nào đăng giờ nào
    H["lv_within_ch"] = H["lv_adj"] - H.groupby("channel_id")["lv_adj"].transform("median")
    n_H = len(H)
    print(f"DATA_DIR={DATA_DIR} | n_H={n_H:,} | kênh trong H={H['channel_id'].nunique()}")

    # (a)
    ta = table_a(H)
    ta.to_csv(os.path.join(OUT_DIR, "q1_descriptive_table.csv"), index=False, encoding="utf-8-sig")

    # (b)
    by_hour = summarize_by(H, "pub_hour")
    by_dow = summarize_by(H, "pub_dow")
    H["ym"] = H["pub_date_vn"].astype(str).str[:7]
    by_month = summarize_by(H, "ym")
    assert by_hour["n"].sum() == n_H, "Tổng n theo giờ phải bằng n_H"
    assert by_dow["n"].sum() == n_H and by_month["n"].sum() == n_H
    by_hour.to_csv(os.path.join(OUT_DIR, "q1_by_hour.csv"), index=False, encoding="utf-8-sig")
    by_dow.assign(dow_name=[DOW_LABELS[i] for i in by_dow["pub_dow"]]).to_csv(
        os.path.join(OUT_DIR, "q1_by_dow.csv"), index=False, encoding="utf-8-sig")
    by_month.to_csv(os.path.join(OUT_DIR, "q1_by_month.csv"), index=False, encoding="utf-8-sig")

    # (c) heatmap
    cell = H.groupby(["pub_hour", "pub_dow"]).agg(n=("lv_adj", "size"), median_lv_adj=("lv_adj", "median")).reset_index()
    cell["median_lv_adj_masked"] = np.where(cell["n"] >= MIN_CELL, cell["median_lv_adj"], np.nan)
    cell["dow_name"] = [DOW_LABELS[i] for i in cell["pub_dow"]]
    cell.to_csv(os.path.join(OUT_DIR, "q1_heatmap.csv"), index=False, encoding="utf-8-sig")
    piv = cell.pivot(index="pub_hour", columns="pub_dow", values="median_lv_adj_masked").reindex(
        index=range(24), columns=range(7))

    # (d) thể loại
    cat = H.groupby("category_name").agg(n=("lv_adj", "size"), median_lv_adj=("lv_adj", "median"),
                                         mean_lv_adj=("lv_adj", "mean"),
                                         median_lv_within_channel=("lv_within_ch", "median"),
                                         q1=("lv_adj", lambda s: s.quantile(.25)),
                                         q3=("lv_adj", lambda s: s.quantile(.75)),
                                         median_like_rate=("like_rate", "median")).reset_index()
    cat = cat.sort_values("n", ascending=False)
    cat["rank_n"] = range(1, len(cat) + 1)
    cat.to_csv(os.path.join(OUT_DIR, "q1_by_category.csv"), index=False, encoding="utf-8-sig")
    top10 = cat["category_name"].head(10).tolist()

    # hình
    plot_by_hour(by_hour, os.path.join(OUT_DIR, "q1_by_hour.png"))
    plot_by_dow(by_dow, os.path.join(OUT_DIR, "q1_by_dow.png"))
    plot_by_month(by_month, os.path.join(OUT_DIR, "q1_by_month.png"))
    plot_heatmap(piv, os.path.join(OUT_DIR, "q1_heatmap.png"))
    plot_box_category(H, top10, os.path.join(OUT_DIR, "q1_box_category.png"))

    # tóm tắt để viết báo cáo / kiểm tra
    best = cell[cell["n"] >= MIN_CELL].sort_values("median_lv_adj", ascending=False)
    summ = {
        "n_H": n_H, "n_channels_H": int(H["channel_id"].nunique()),
        "hour_best": int(by_hour.loc[by_hour["median_lv_adj"].idxmax(), "pub_hour"]),
        "hour_best_val": float(by_hour["median_lv_adj"].max()),
        "hour_worst": int(by_hour.loc[by_hour["median_lv_adj"].idxmin(), "pub_hour"]),
        "hour_worst_val": float(by_hour["median_lv_adj"].min()),
        "hour_range": float(by_hour["median_lv_adj"].max() - by_hour["median_lv_adj"].min()),
        "hour_range_within_channel": float(by_hour["median_lv_within_channel"].max() - by_hour["median_lv_within_channel"].min()),
        "dow_range_within_channel": float(by_dow["median_lv_within_channel"].max() - by_dow["median_lv_within_channel"].min()),
        "between_channel_var_share": float(H.groupby("channel_id")["lv_adj"].transform("mean").var() / H["lv_adj"].var()),
        "dow_range": float(by_dow["median_lv_adj"].max() - by_dow["median_lv_adj"].min()),
        "cells_total": int(len(cell)), "cells_blank": int((cell["n"] < MIN_CELL).sum()),
        "cell_best": f'{int(best.iloc[0].pub_hour)}h {best.iloc[0].dow_name} ({best.iloc[0].median_lv_adj:.3f}, n={int(best.iloc[0].n)})',
        "cell_worst": f'{int(best.iloc[-1].pub_hour)}h {best.iloc[-1].dow_name} ({best.iloc[-1].median_lv_adj:.3f}, n={int(best.iloc[-1].n)})',
        "cat_best": cat[cat.category_name.isin(top10)].sort_values("median_lv_adj").iloc[-1].category_name,
        "cat_worst": cat[cat.category_name.isin(top10)].sort_values("median_lv_adj").iloc[0].category_name,
        "cat_range_top10": float(cat[cat.category_name.isin(top10)]["median_lv_adj"].max() - cat[cat.category_name.isin(top10)]["median_lv_adj"].min()),
        "cat_best_within": cat[cat.category_name.isin(top10)].sort_values("median_lv_within_channel").iloc[-1].category_name,
        "cat_worst_within": cat[cat.category_name.isin(top10)].sort_values("median_lv_within_channel").iloc[0].category_name,
        "cat_range_top10_within_channel": float(cat[cat.category_name.isin(top10)]["median_lv_within_channel"].max()
                                                 - cat[cat.category_name.isin(top10)]["median_lv_within_channel"].min()),
    }
    pd.Series(summ).to_csv(os.path.join(OUT_DIR, "q1_summary_for_report.csv"), header=["value"], encoding="utf-8-sig")
    print(pd.Series(summ).to_string())
    print("\nBảng (a) - tất cả:")
    print(ta[ta.nhom == "Tất cả"].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
