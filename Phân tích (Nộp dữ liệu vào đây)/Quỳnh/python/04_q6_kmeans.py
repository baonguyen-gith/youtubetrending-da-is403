# -*- coding: utf-8 -*-
"""
04_q6_kmeans.py
===============
Q6 - Phan cum video bang K-means (do an IS403 - Nhom 4, phan cong: Vu Thi Nhu Quynh).

Quy trinh theo Muc 5.6 cua bao cao:
  1. Loc measurements.csv: is_last_of_day = TRUE, >= 5 ngay do, khoang cach lan do
     dau-cuoi >= 5 ngay, du likes/comments, views cuoi > 0.
  2. 6 bien hanh vi (Bo A):
       vpd_log      = log10(max(views_cuoi / age_days_cuoi, 1))          - toc do xem/ngay
       growth_log   = log10(views_cuoi) - log10(max(views_dau, 1))       - tong tang truong
       momentum     = log10((vpd_lan_cuoi + .01) / (vpd_trung_binh + .01)) - dang tang toc hay nguoi
       like_rate    = likes_cuoi / views_cuoi        (cat phan vi 99)
       comment_rate = comments_cuoi / views_cuoi     (cat phan vi 99)
       volatility   = do lech chuan / trung binh cua vpd tung khoang   (cat phan vi 99)
  3. StandardScaler; K-means k = 2..8, n_init = 10, random_state = 42.
     Chon k bang Silhouette + elbow (inertia) + Davies-Bouldin, rang buoc moi cum >= 5%.
  4. On dinh: 20 mau bootstrap 80/20, ARI trung binh (< 0.6 -> canh bao).
  5. PCA 2 chieu -> Hinh 5.9, q6_pca_points.csv.
  6. Ho so cum + Chi-square cum x the loai, cum x viral_A -> Bang 5.17.
  7. Xuat q6_R_input.csv de doi chieu bang R (ARI >= 0.8).

Input : measurements.csv, videos_master.csv, labels.csv
Output: 05_Code_Output/outputs/5.6 Q6/

Chay: py 05_Code_Output/python/04_q6_kmeans.py
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score,
                             davies_bouldin_score, silhouette_score)
from sklearn.preprocessing import StandardScaler

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Duong dan
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT = SCRIPT_DIR.parent.parent                    # ...\Đồ án
OUT = PROJECT / "05_Code_Output" / "outputs" / "5.6 Q6"
OUT.mkdir(parents=True, exist_ok=True)

MEAS = PROJECT / "measurements.csv"
VIDEOS = PROJECT / "videos_master.csv"
LABELS = PROJECT / "05_Code_Output" / "outputs" / "4.4 labels" / "labels.csv"

RANDOM_STATE = 42
K_RANGE = list(range(2, 9))
N_INIT = 10
MIN_CLUSTER_SHARE = 0.05
N_BOOT = 20
SIL_SAMPLE = 10_000
MIN_DAYS = 5
MIN_SPAN = 5

BEHAV = ["vpd_log", "growth_log", "momentum", "like_rate", "comment_rate", "volatility"]
BEHAV_LABEL = {
    "vpd_log": "Tốc độ xem/ngày (log)",
    "growth_log": "Tăng trưởng trong cửa sổ đo (log)",
    "momentum": "Đang tăng tốc / nguội dần (log)",
    "like_rate": "Tỷ lệ like / view (cắt p99)",
    "comment_rate": "Tỷ lệ comment / view (cắt p99)",
    "volatility": "Độ biến động tốc độ (CV, cắt p99)",
}

LOG_LINES: list[str] = []


def log(msg: str = "") -> None:
    line = f"[{datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    LOG_LINES.append(line)


def p99_cap(s: pd.Series) -> pd.Series:
    cap = s.quantile(0.99)
    return s.clip(upper=cap)


# ---------------------------------------------------------------------------
# 1. Loc du lieu
# ---------------------------------------------------------------------------
def filter_measurements() -> tuple[pd.DataFrame, pd.DataFrame]:
    log("Đọc measurements.csv ...")
    cols = ["video_id", "channel_id", "run_date", "views", "likes", "comments",
            "age_days", "is_last_of_day", "likes_hidden", "comments_disabled",
            "is_live_or_upcoming"]
    m = pd.read_csv(MEAS, usecols=cols, low_memory=False)
    log(f"  tổng số dòng đo: {len(m):,} | số video: {m['video_id'].nunique():,}")

    steps = [{"buoc": "0. Toàn bộ measurements.csv", "n_dong": len(m),
              "n_video": int(m["video_id"].nunique())}]

    m = m[m["is_last_of_day"] == True].copy()
    steps.append({"buoc": "1. Chỉ giữ is_last_of_day = TRUE", "n_dong": len(m),
                  "n_video": int(m["video_id"].nunique())})

    g = m.groupby("video_id")
    n_days = g["run_date"].nunique()
    keep = n_days[n_days >= MIN_DAYS].index
    m = m[m["video_id"].isin(keep)].copy()
    steps.append({"buoc": f"2. Có >= {MIN_DAYS} ngày đo", "n_dong": len(m),
                  "n_video": int(m["video_id"].nunique())})

    d0 = pd.to_datetime(m.groupby("video_id")["run_date"].min())
    d1 = pd.to_datetime(m.groupby("video_id")["run_date"].max())
    span = (d1 - d0).dt.days
    keep = span[span >= MIN_SPAN].index
    m = m[m["video_id"].isin(keep)].copy()
    steps.append({"buoc": f"3. Khoảng cách lần đo đầu–cuối >= {MIN_SPAN} ngày",
                  "n_dong": len(m), "n_video": int(m["video_id"].nunique())})

    # coi "du likes/comments" = khong bi an like, khong tat comment, va co so lieu
    last = m.sort_values(["video_id", "run_date"]).groupby("video_id").tail(1)
    ok = (~last["likes_hidden"].astype(bool)) & (~last["comments_disabled"].astype(bool)) \
        & last["likes"].notna() & last["comments"].notna()
    keep = last.loc[ok, "video_id"]
    m = m[m["video_id"].isin(keep)].copy()
    steps.append({"buoc": "4. Đủ likes/comments (không ẩn like, không tắt comment)",
                  "n_dong": len(m), "n_video": int(m["video_id"].nunique())})

    last = m.sort_values(["video_id", "run_date"]).groupby("video_id").tail(1)
    keep = last.loc[last["views"] > 0, "video_id"]
    m = m[m["video_id"].isin(keep)].copy()
    steps.append({"buoc": "5. Views lần đo cuối > 0", "n_dong": len(m),
                  "n_video": int(m["video_id"].nunique())})

    log("Các bước lọc:")
    for s in steps:
        log(f"  {s['buoc']:58s} dòng={s['n_dong']:>9,} | video={s['n_video']:>7,}")
    return m, pd.DataFrame(steps)


# ---------------------------------------------------------------------------
# 2. 6 bien hanh vi
# ---------------------------------------------------------------------------
def build_features(m: pd.DataFrame) -> pd.DataFrame:
    log("Tính 6 biến hành vi ...")
    m = m.sort_values(["video_id", "run_date"]).copy()
    rows = []
    for vid, g in m.groupby("video_id", sort=False):
        v = g["views"].to_numpy(dtype=float)
        a = g["age_days"].to_numpy(dtype=float)
        if len(v) < MIN_DAYS:
            continue
        views_last = v[-1]
        views_first = v[0]
        age_last = a[-1]
        if views_last <= 0 or age_last <= 0:
            continue

        vpd_overall = views_last / age_last
        vpd_log = np.log10(max(vpd_overall, 1.0))
        growth_log = np.log10(max(views_last, 1.0)) - np.log10(max(views_first, 1.0))

        # toc do tung khoang (chi tinh khoang co dt >= 0.5 ngay)
        dv = np.diff(v)
        da = np.diff(a)
        ok = da >= 0.5
        if ok.sum() >= 1:
            iv = dv[ok] / da[ok]
            iv = np.clip(iv, 0, None)
            vpd_last_int = iv[-1]
            momentum = np.log10((vpd_last_int + 0.01) / (vpd_overall + 0.01))
            if len(iv) >= 2 and iv.mean() > 0:
                volatility = iv.std(ddof=0) / iv.mean()
            else:
                volatility = 0.0
        else:
            momentum = 0.0
            volatility = 0.0

        likes_last = float(g["likes"].to_numpy()[-1])
        com_last = float(g["comments"].to_numpy()[-1])
        like_rate = likes_last / views_last
        comment_rate = com_last / views_last

        rows.append({
            "video_id": vid,
            "channel_id": g["channel_id"].iloc[0],
            "n_days": len(g),
            "run_date_first": g["run_date"].iloc[0],
            "run_date_last": g["run_date"].iloc[-1],
            "views_first": views_first,
            "views_last": views_last,
            "age_days_last": age_last,
            "likes_last": likes_last,
            "comments_last": com_last,
            "vpd_log": vpd_log,
            "growth_log": growth_log,
            "momentum": momentum,
            "like_rate": like_rate,
            "comment_rate": comment_rate,
            "volatility": volatility,
        })

    f = pd.DataFrame(rows)
    log(f"  số video dựng được đủ 6 biến: {len(f):,}")

    for c in ["like_rate", "comment_rate", "volatility"]:
        before = f[c].quantile(0.99)
        f[c] = p99_cap(f[c])
        log(f"  cắt p99 {c:13s}: {before:.6g}")
    f[BEHAV] = f[BEHAV].replace([np.inf, -np.inf], np.nan)
    f = f.dropna(subset=BEHAV).reset_index(drop=True)
    log(f"  còn lại sau khi bỏ NaN/inf: {len(f):,}")
    return f


# ---------------------------------------------------------------------------
# 3. Quet k
# ---------------------------------------------------------------------------
def sweep_k(Xs: np.ndarray) -> tuple[pd.DataFrame, dict[int, np.ndarray]]:
    log("Quét k = 2..8 (K-means, n_init=10, random_state=42) ...")
    rng = np.random.RandomState(RANDOM_STATE)
    if len(Xs) > SIL_SAMPLE:
        sil_idx = rng.choice(len(Xs), SIL_SAMPLE, replace=False)
    else:
        sil_idx = np.arange(len(Xs))

    rows = []
    labels_by_k: dict[int, np.ndarray] = {}
    for k in K_RANGE:
        t0 = time.time()
        km = KMeans(n_clusters=k, n_init=N_INIT, random_state=RANDOM_STATE)
        lab = km.fit_predict(Xs)
        labels_by_k[k] = lab
        sizes = np.bincount(lab, minlength=k)
        share = sizes / len(lab)
        rows.append({
            "k": k,
            "inertia": km.inertia_,
            "silhouette": silhouette_score(Xs[sil_idx], lab[sil_idx]),
            "davies_bouldin": davies_bouldin_score(Xs, lab),
            "calinski_harabasz": calinski_harabasz_score(Xs, lab),
            "min_cluster_pct": float(share.min() * 100),
            "n_clusters_ge_5pct": int((share >= MIN_CLUSTER_SHARE).sum()),
            "dung_duoc": bool((share >= MIN_CLUSTER_SHARE).all()),
        })
        log(f"  k={k}: inertia={km.inertia_:,.0f} | silhouette={rows[-1]['silhouette']:.4f} "
            f"| DB={rows[-1]['davies_bouldin']:.3f} | cum nhỏ nhất={share.min()*100:.1f}% "
            f"({time.time()-t0:.0f}s)")
    return pd.DataFrame(rows), labels_by_k


def choose_k(sel: pd.DataFrame) -> tuple[int, str]:
    ok = sel[sel["dung_duoc"]]
    if len(ok) == 0:
        best = int(sel.sort_values("silhouette", ascending=False).iloc[0]["k"])
        return best, "Không k nào thoả ràng buộc 5% — chọn k theo silhouette cao nhất (có cảnh báo)."
    best = int(ok.sort_values("silhouette", ascending=False).iloc[0]["k"])
    # elbow: diem gãy lớn nhất của inertia (chỉ để tham khảo)
    s = sel.sort_values("k").reset_index(drop=True)
    drop = -np.diff(s["inertia"].to_numpy())
    elbow = int(s["k"].iloc[int(np.argmax(drop))])
    note = (f"Chọn k={best} vì silhouette cao nhất trong các k thoả ràng buộc mỗi cụm >= 5%. "
            f"Elbow (giảm inertia mạnh nhất) gợi ý k={elbow}.")
    return best, note


# ---------------------------------------------------------------------------
# 4. Do on dinh
# ---------------------------------------------------------------------------
def stability(Xs: np.ndarray, base_lab: np.ndarray, k: int) -> pd.DataFrame:
    log(f"Kiểm tra ổn định: {N_BOOT} mẫu bootstrap 80/20 ...")
    rng = np.random.RandomState(RANDOM_STATE)
    n = len(Xs)
    rows = []
    for b in range(1, N_BOOT + 1):
        idx = rng.choice(n, int(0.8 * n), replace=False)
        mask = np.ones(n, dtype=bool)
        mask[idx] = False
        oob = np.flatnonzero(mask)
        km = KMeans(n_clusters=k, n_init=N_INIT, random_state=RANDOM_STATE + b)
        km.fit(Xs[idx])
        pred = km.predict(Xs[oob])
        ari = adjusted_rand_score(base_lab[oob], pred)
        rows.append({"lan": b, "n_train": len(idx), "n_test": len(oob), "ari": ari})
        log(f"  lần {b:2d}: ARI = {ari:.3f}")
    st = pd.DataFrame(rows)
    log(f"  ARI trung bình = {st['ari'].mean():.3f} (min {st['ari'].min():.3f})")
    return st


# ---------------------------------------------------------------------------
# 5. Ho so cum
# ---------------------------------------------------------------------------
def profile(f: pd.DataFrame, lab: np.ndarray, k: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    f = f.copy()
    f["cluster"] = lab + 1
    rows = []
    for c in sorted(f["cluster"].unique()):
        s = f[f["cluster"] == c]
        top = s["category_name"].value_counts()
        rows.append({
            "cluster": int(c),
            "n": len(s),
            "pct": len(s) / len(f) * 100,
            "vpd_log_med": s["vpd_log"].median(),
            "growth_log_med": s["growth_log"].median(),
            "momentum_med": s["momentum"].median(),
            "like_rate_med": s["like_rate"].median(),
            "comment_rate_med": s["comment_rate"].median(),
            "volatility_med": s["volatility"].median(),
            "subscribers_med": s["subscribers"].median(),
            "age_days_med": s["age_days_last"].median(),
            "views_last_med": s["views_last"].median(),
            "pct_ever_trending": s["ever_trending"].mean() * 100,
            "pct_viral_A": (s["viral_A"] == 1).mean() * 100,
            "pct_breakout_B": (s["breakout_B"] == 1).mean() * 100,
            "top_category": top.index[0] if len(top) else "",
            "pct_top_category": top.iloc[0] / len(s) * 100 if len(top) else np.nan,
        })
    prof = pd.DataFrame(rows)
    total = {
        "cluster": "Tổng", "n": len(f), "pct": 100.0,
        "vpd_log_med": f["vpd_log"].median(), "growth_log_med": f["growth_log"].median(),
        "momentum_med": f["momentum"].median(), "like_rate_med": f["like_rate"].median(),
        "comment_rate_med": f["comment_rate"].median(),
        "volatility_med": f["volatility"].median(),
        "subscribers_med": f["subscribers"].median(),
        "age_days_med": f["age_days_last"].median(),
        "views_last_med": f["views_last"].median(),
        "pct_ever_trending": f["ever_trending"].mean() * 100,
        "pct_viral_A": (f["viral_A"] == 1).mean() * 100,
        "pct_breakout_B": (f["breakout_B"] == 1).mean() * 100,
        "top_category": "", "pct_top_category": np.nan,
    }
    prof = pd.concat([prof, pd.DataFrame([total])], ignore_index=True)
    return prof, f


def read_r_check(path: Path) -> pd.DataFrame:
    """Doc ket qua doi chieu R (neu da chay 04_q6_kmeans.R) thanh bang 2 cot."""
    if not path.exists():
        return pd.DataFrame({"chi_tieu": ["Đối chiếu R"],
                             "gia_tri": ["chưa chạy — chạy 04_q6_kmeans.R sau"]})
    txt = path.read_text(encoding="utf-8-sig", errors="replace")
    want = {
        "So video": "Số video",
        "k (Python chon)": "k (Python chọn)",
        "So bien dung de cum": "Số biến dùng để cụm",
        "So video moi cum (R)": "Số video mỗi cụm (R)",
        "ARI (Python vs R)": "ARI (Python vs R)",
        "KET LUAN": "Kết luận",
    }
    rows = []
    for line in txt.splitlines():
        line = line.strip()
        for k, label in sorted(want.items(), key=lambda kv: -len(kv[0])):
            if line.startswith(k) and ":" in line:
                rows.append({"chi_tieu": label,
                             "gia_tri": line.split(":", 1)[1].strip()})
                break
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        {"chi_tieu": ["Đối chiếu R"], "gia_tri": ["không đọc được q6_R_check.txt"]})


def chi2_tests(f: pd.DataFrame) -> pd.DataFrame:
    rows = []
    # cum x the loai (gop the loai qua it vao Khac de expected >= 5)
    for target, name in [("category_name", "Cụm × thể loại"),
                         ("viral_A", "Cụm × viral_A")]:
        d = f[[target]].copy()
        d["cluster"] = f["cluster"]
        d[target] = d[target].astype(str).replace({"nan": "khác", "<NA>": "khác", "None": "khác"})
        if target == "category_name":
            vc = d[target].value_counts()
            small = vc[vc < 0.01 * len(d)].index
            d[target] = d[target].where(~d[target].isin(small), "Khác")
        tab = pd.crosstab(d["cluster"], d[target])
        tab = tab.loc[:, tab.sum(axis=0) > 0]
        chi2, p, dof, exp = chi2_contingency(tab)
        n = tab.to_numpy().sum()
        v = np.sqrt(chi2 / (n * (min(tab.shape) - 1)))
        rows.append({
            "cap_bien": name, "n": int(n), "chi2": chi2, "df": int(dof),
            "p_value": p, "cramers_v": v,
            "min_expected": float(exp.min()),
            "n_cells_expected_lt5": int((exp < 5).sum()),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 6. Xuat file
# ---------------------------------------------------------------------------
def write_excel(sheets: dict[str, pd.DataFrame], path: Path, notes: dict[str, str]) -> None:
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        pd.DataFrame({"Nội dung": ["Xem hướng dẫn ở sheet 00_Huong_dan"]}).to_excel(
            xw, sheet_name="00_Huong_dan", index=False)
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name[:31], index=False)
        for name, note in notes.items():
            pd.DataFrame({"Ghi chú": [note]}).to_excel(
                xw, sheet_name=f"GC_{name}"[:31], index=False)

    wb = load_workbook(path)
    head_fill = PatternFill("solid", fgColor="1F3B57")
    head_font = Font(color="FFFFFF", bold=True)
    for ws in wb.worksheets:
        for cell in ws[1]:
            cell.fill = head_fill
            cell.font = head_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for col in ws.columns:
            letter = get_column_letter(col[0].column)
            width = max(len(str(c.value)) if c.value is not None else 0 for c in col[:200])
            ws.column_dimensions[letter].width = min(max(10, width + 2), 42)
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if isinstance(cell.value, float):
                    cell.number_format = "0.000"
    wb.save(path)


def main() -> None:
    t0 = time.time()
    log("=" * 78)
    log("Q6 - PHÂN CỤM VIDEO BẰNG K-MEANS")
    log("=" * 78)

    m, steps = filter_measurements()
    f = build_features(m)

    log("Ghép thông tin video / kênh / nhãn ...")
    vids = pd.read_csv(VIDEOS, usecols=["video_id", "subscribers", "category_name",
                                        "duration_sec", "is_short_60", "ever_trending",
                                        "trend_days", "pub_date_vn"], low_memory=False)
    lb = pd.read_csv(LABELS, usecols=["video_id", "viral_A", "breakout_B", "viral_C"],
                     low_memory=False)
    f = f.merge(vids, on="video_id", how="left").merge(lb, on="video_id", how="left")
    n_before = len(f)
    f = f.dropna(subset=["subscribers", "category_name"]).reset_index(drop=True)
    log(f"  sau khi ghép: {n_before:,} -> {len(f):,} video (có subscribers + thể loại)")

    steps = pd.concat([steps, pd.DataFrame([{
        "buoc": "6. Ghép được subscribers + thể loại (dùng cho hồ sơ cụm)",
        "n_dong": np.nan, "n_video": len(f)}])], ignore_index=True)
    steps.to_csv(OUT / "q6_filter_steps.csv", index=False, encoding="utf-8-sig")

    # ---- chuan hoa ----
    X = f[BEHAV].to_numpy(dtype=float)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    pd.DataFrame(scaler.mean_, index=BEHAV, columns=["mean"]).join(
        pd.DataFrame(scaler.scale_, index=BEHAV, columns=["scale"])
    ).to_csv(OUT / "q6_scaler_params.csv", encoding="utf-8-sig")
    log(f"Ma trận đặc trưng: {Xs.shape[0]:,} video × {Xs.shape[1]} biến (đã chuẩn hoá)")

    # ---- quet k ----
    sel, labels_by_k = sweep_k(Xs)
    best_k, note = choose_k(sel)
    sel["chon"] = sel["k"] == best_k
    sel["ghi_chu"] = ""
    sel.loc[sel["k"] == best_k, "ghi_chu"] = note
    sel.to_csv(OUT / "q6_k_selection.csv", index=False, encoding="utf-8-sig")
    log(note)

    base_lab = labels_by_k[best_k]

    # ---- on dinh ----
    st = stability(Xs, base_lab, best_k)
    st.to_csv(OUT / "q6_stability.csv", index=False, encoding="utf-8-sig")
    ari_mean = st["ari"].mean()
    if ari_mean < 0.6:
        log("CẢNH BÁO: ARI trung bình < 0.6 — cụm không ổn định, cần diễn giải cẩn thận.")

    # ---- PCA ----
    log("PCA 2 chiều ...")
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    P = pca.fit_transform(Xs)
    pca_df = pd.DataFrame({
        "video_id": f["video_id"], "cluster": base_lab + 1,
        "pc1": P[:, 0], "pc2": P[:, 1],
    })
    pca_df.to_csv(OUT / "q6_pca_points.csv", index=False, encoding="utf-8-sig")
    evr = pca.explained_variance_ratio_
    log(f"  phương sai giải thích: PC1={evr[0]*100:.1f}% | PC2={evr[1]*100:.1f}%")

    # ---- ho so cum ----
    prof, f = profile(f, base_lab, best_k)
    prof.to_csv(OUT / "q6_cluster_profile.csv", index=False, encoding="utf-8-sig")
    print(prof.round(3).to_string(index=False))

    chi = chi2_tests(f)
    chi.to_csv(OUT / "q6_chi2.csv", index=False, encoding="utf-8-sig")
    print(chi.round(4).to_string(index=False))

    # ---- phan bo the loai tung cum ----
    cat = pd.crosstab(f["cluster"], f["category_name"])
    cat.to_csv(OUT / "q6_cluster_category.csv", encoding="utf-8-sig")

    # ---- gan nhan + du lieu cho R ----
    out_cols = (["video_id", "cluster", "n_days", "views_last", "age_days_last",
                 "subscribers", "category_name", "ever_trending", "viral_A",
                 "breakout_B", "viral_C"] + BEHAV)
    f_out = f[out_cols].copy()
    for c in BEHAV:
        f_out[f"z_{c}"] = scaler.transform(f[BEHAV])[:, BEHAV.index(c)]
    f_out.to_csv(OUT / "q6_cluster_assignments.csv", index=False, encoding="utf-8-sig")

    r_in = f_out[["video_id", "cluster"] + BEHAV].copy()
    scaler2 = StandardScaler().fit(r_in[BEHAV])
    for c in BEHAV:
        r_in[f"z_{c}"] = scaler2.transform(r_in[BEHAV])[:, BEHAV.index(c)]
    r_in[["video_id", "cluster"] + [f"z_{c}" for c in BEHAV]].to_csv(
        OUT / "q6_R_input.csv", index=False, encoding="utf-8-sig")

    # ---- hinh 5.9 ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(8.6, 6.2), dpi=160)
    cmap = plt.get_cmap("tab10")
    for i, c in enumerate(sorted(pca_df["cluster"].unique())):
        s = pca_df[pca_df["cluster"] == c]
        ax.scatter(s["pc1"], s["pc2"], s=6, alpha=0.45,
                   color=cmap((c - 1) % 10), label=f"Cụm {c} (n={len(s):,})")
    ax.set_xlabel(f"PC1 ({evr[0]*100:.1f}% phương sai)")
    ax.set_ylabel(f"PC2 ({evr[1]*100:.1f}% phương sai)")
    ax.set_title(f"Hình 5.9. Các cụm video trên mặt phẳng hai thành phần chính (k={best_k})")
    ax.legend(markerscale=4, fontsize=8, loc="best")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / "q6_figure_5_9.png")
    plt.close(fig)

    # ---- Excel ----
    sheets = {
        "01_Bang_5_17_ho_so_cum": prof,
        "02_Chon_k": sel,
        "03_On_dinh_ARI": st,
        "04_Chi_square": chi,
        "05_The_loai_theo_cum": cat.reset_index(),
        "06_Tham_so_chuan_hoa": pd.read_csv(OUT / "q6_scaler_params.csv"),
        "07_Buoc_loc": steps,
        "08_Doi_chieu_R": read_r_check(OUT / "q6_R_check.txt"),
    }
    notes = {
        "01_Bang_5_17_ho_so_cum": "Trung vị các biến trong cụm; % Trending/viral tính trên video của cụm.",
        "02_Chon_k": "Silhouette tính trên mẫu 10.000 video; DB và CH tính trên toàn bộ.",
        "03_On_dinh_ARI": f"{N_BOOT} lần bootstrap 80/20, ARI so với phân cụm gốc trên phần giữ lại.",
        "04_Chi_square": "Thể loại có <1% số video được gộp vào 'Khác' trước khi kiểm định.",
        "05_The_loai_theo_cum": "Số video từng thể loại trong mỗi cụm.",
        "06_Tham_so_chuan_hoa": "StandardScaler: z = (x - mean) / scale.",
        "07_Buoc_loc": "Số dòng và số video còn lại sau từng bước lọc.",
        "08_Doi_chieu_R": "Đọc từ q6_R_check.txt (04_q6_kmeans.R); đạt khi ARI >= 0,8.",
    }
    write_excel(sheets, OUT / "Q6_tong_hop.xlsx", notes)

    # ---- bao cao markdown + docx ----
    write_report(f, steps, sel, best_k, note, ari_mean, st, prof, chi, evr, scaler)
    log(f"\nHOÀN TẤT sau {(time.time()-t0)/60:.1f} phút")
    log(f"Thư mục: {OUT}")


def write_report(f, steps, sel, best_k, note, ari_mean, st, prof, chi, evr, scaler) -> None:
    from md2docx_q5 import convert_md_text

    L = []
    A = L.append
    A("# Q6 — Phân cụm video bằng K-means\n")
    A(f"*Sinh tự động: {datetime.now():%Y-%m-%d %H:%M} — dữ liệu `measurements.csv` "
      f"và `labels.csv` (bản final 12/11/2026).*\n")

    A("## 1. Lọc dữ liệu\n")
    A("| Bước | Số dòng đo | Số video |")
    A("|---|---:|---:|")
    for _, r in steps.iterrows():
        nd = "" if pd.isna(r["n_dong"]) else f"{int(r['n_dong']):,}"
        A(f"| {r['buoc']} | {nd} | {int(r['n_video']):,} |")

    A("\n## 2. Sáu biến hành vi\n")
    A("| Biến | Công thức | Ý nghĩa |")
    A("|---|---|---|")
    formulas = {
        "vpd_log": "log10(max(views_cuoi / age_days_cuoi, 1))",
        "growth_log": "log10(views_cuoi) − log10(max(views_dau, 1))",
        "momentum": "log10((vpd_khoảng_cuối + 0,01) / (vpd_trung_binh + 0,01))",
        "like_rate": "likes_cuoi / views_cuoi (cắt phân vị 99)",
        "comment_rate": "comments_cuoi / views_cuoi (cắt phân vị 99)",
        "volatility": "độ lệch chuẩn / trung bình của vpd từng khoảng (cắt phân vị 99)",
    }
    meaning = {
        "vpd_log": "Video lan nhanh hay chậm tính trung bình cả đời",
        "growth_log": "Tổng mức tăng lượt xem trong cửa sổ quan sát",
        "momentum": "Dương: đang tăng tốc; âm: đã nguội dần",
        "like_rate": "Mức yêu thích trên mỗi lượt xem",
        "comment_rate": "Mức bình luận trên mỗi lượt xem",
        "volatility": "Tốc độ tăng có đều hay dồn cục",
    }
    for c in BEHAV:
        A(f"| `{c}` | {formulas[c]} | {meaning[c]} |")

    A("\n## 3. Chọn số cụm k\n")
    A("| k | Inertia | Silhouette | Davies-Bouldin | Cụm nhỏ nhất (%) | Dùng được |")
    A("|---:|---:|---:|---:|---:|---|")
    for _, r in sel.iterrows():
        A(f"| {int(r['k'])} | {r['inertia']:,.0f} | {r['silhouette']:.4f} | "
          f"{r['davies_bouldin']:.3f} | {r['min_cluster_pct']:.1f} | "
          f"{'có' if r['dung_duoc'] else 'không'} |")
    A(f"\n**{note}**\n")

    A("## 4. Độ ổn định\n")
    A(f"- {N_BOOT} lần bootstrap 80/20, ARI trung bình **{ari_mean:.3f}** "
      f"(nhỏ nhất {st['ari'].min():.3f}, lớn nhất {st['ari'].max():.3f}).")
    if ari_mean >= 0.6:
        A("- ARI ≥ 0,6: phân cụm ổn định, có thể diễn giải.")
    else:
        A("- **CẢNH BÁO:** ARI < 0,6 — cụm không ổn định, chỉ nên mô tả chứ không kết luận.")

    A("\n## 5. Hồ sơ cụm (Bảng 5.17)\n")
    A("| Cụm | n | % | vpd_log | growth_log | momentum | like_rate | comment_rate | volatility | Subs (trung vị) | Tuổi (ngày) | % Trending | % viral_A | Thể loại nổi bật |")
    A("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for _, r in prof.iterrows():
        if r["cluster"] == "Tổng":
            continue
        A(f"| {int(r['cluster'])} | {int(r['n']):,} | {r['pct']:.1f} | {r['vpd_log_med']:.3f} | "
          f"{r['growth_log_med']:.3f} | {r['momentum_med']:.3f} | {r['like_rate_med']:.4f} | "
          f"{r['comment_rate_med']:.4f} | {r['volatility_med']:.3f} | "
          f"{r['subscribers_med']:,.0f} | {r['age_days_med']:.0f} | "
          f"{r['pct_ever_trending']:.1f} | {r['pct_viral_A']:.1f} | "
          f"{r['top_category']} ({r['pct_top_category']:.0f}%) |")

    A("\n## 6. Liên hệ cụm với thể loại và viral_A\n")
    A("| Cặp biến | n | Chi-square | df | p-value | Cramér's V |")
    A("|---|---:|---:|---:|---|---:|")
    for _, r in chi.iterrows():
        p = "< 1e-300" if r["p_value"] == 0 else f"{r['p_value']:.3g}"
        A(f"| {r['cap_bien']} | {int(r['n']):,} | {r['chi2']:,.2f} | {int(r['df'])} | {p} | {r['cramers_v']:.3f} |")

    A("\n## 7. Đối chiếu với R\n")
    r_tab = read_r_check(OUT / "q6_R_check.txt")
    A("| Chỉ tiêu | Giá trị |")
    A("|---|---|")
    for _, r in r_tab.iterrows():
        A(f"| {r['chi_tieu']} | {r['gia_tri']} |")
    A("\nTiêu chí đạt: ARI ≥ 0,8. Nhãn cụm của R có thể đánh số khác Python "
      "nhưng ARI đo mức trùng khớp của cách chia, không phụ thuộc số thứ tự.\n")

    A("\n## 8. Hình và dữ liệu kèm theo\n")
    A(f"- Hình 5.9: `q6_figure_5_9.png` — PC1 {evr[0]*100:.1f}%, PC2 {evr[1]*100:.1f}% phương sai.")
    A("- `q6_pca_points.csv`: toạ độ PCA của từng video, kèm cụm.")
    A("- `q6_cluster_profile.csv`: hồ sơ cụm (Bảng 5.17).")
    A("- `q6_cluster_assignments.csv`: nhãn cụm của từng video và 6 biến gốc.")
    A("- `q6_R_input.csv`: dữ liệu đã chuẩn hoá để R chạy lại K-means (đối chiếu ARI).")

    A("\n## 9. Cách đọc kết quả\n")
    A("- Cụm hình thành từ **hành vi** (tốc độ, tăng trưởng, tương tác), không phải từ quy mô kênh: "
      "subscribers và tuổi video chỉ dùng để mô tả sau khi phân cụm.")
    A("- Chênh lệch giữa các cụm là **mô tả**, không chứng minh quan hệ nhân quả.")
    A("- Mọi con số tính trên mẫu video có ≥ 5 ngày đo, nên không đại diện cho toàn bộ video của kênh.")
    A(f"- Tham số chuẩn hoá: " + "; ".join(
        f"{c} mean={scaler.mean_[i]:.4f}, scale={scaler.scale_[i]:.4f}"
        for i, c in enumerate(BEHAV)) + ".")

    md = "\n".join(L)
    (OUT / "q6_report.md").write_text(md, encoding="utf-8")
    convert_md_text(md, OUT / "q6_report.docx")
    log("Đã ghi q6_report.md và q6_report.docx")


if __name__ == "__main__":
    main()
