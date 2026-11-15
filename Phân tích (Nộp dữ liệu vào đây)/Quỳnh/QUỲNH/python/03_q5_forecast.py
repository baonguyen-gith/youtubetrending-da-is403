# -*- coding: utf-8 -*-
"""
03_q5_forecast.py
=================
Q5: Dự báo video viral (Mục 5.5).

Nhãn:
  - viral_A    : toàn bộ quần thể H (n = 95.319; dương = 9.542)
  - breakout_B : video có đủ ch_med_loo (n = 92.055; dương = 23.174)
  - viral_C    : video trong in_window_C (n = 3.877; dương = 168 >= 100 nên vẫn huấn luyện)

Đầu vào: chỉ X_PRE (Bảng 4.2). Có assert chặn cột cấm.
Chia dữ liệu:
  - GroupKFold 5 fold theo channel_id.
  - Kiểm tra thời gian: train trước 01/07/2026, test từ 01/07/2026.
Mô hình:
  - Mô hình nền (log_subs)  : LogisticRegression
  - Decision Tree           : max_depth=6, min_samples_leaf=50, class_weight='balanced'
  - Random Forest           : 300 cây, min_samples_leaf=5, class_weight='balanced_subsample'
  - SVM (RBF)               : StandardScaler + SVC, mẫu phân tầng 18.000 dòng
  - XGBoost                 : scale_pos_weight = âm/dương, max_depth=4, 280 cây, lr=0.06
Ngưỡng: chọn trên 20% kênh của train (GroupShuffleSplit) để tối đa F1, sau đó fit lại
toàn bộ train và đánh giá trên test. Để bền với lệch thang điểm giữa các fold, ngưỡng
được biểu diễn theo tỷ lệ dương tối ưu (top-rate) rồi áp dụng cùng tỷ lệ cho test.

Input : 05_Code_Output/outputs/4.4 labels/labels.csv, videos_master.csv
Output: 05_Code_Output/outputs/5.5 Q5/
          Q5_tong_hop.xlsx, q5_report.docx, q5_importance.png
          q5_labels_summary.csv, q5_model_comparison.csv, q5_cv_folds.csv,
          q5_time_test.csv, q5_ablation.csv, q5_sensitivity.csv,
          q5_importance.csv, q5_model_data_*.csv

Chạy:
  py 05_Code_Output/python/03_q5_forecast.py            # chạy đầy đủ
  py 05_Code_Output/python/03_q5_forecast.py --quick    # kiểm tra nhanh 2 fold
"""

from __future__ import annotations

import argparse
import sys
import time
import warnings
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Đường dẫn và hằng số
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parents[1]
OUTPUT_DIR = PROJECT_DIR / "05_Code_Output" / "outputs"
Q5_DIR = OUTPUT_DIR / "5.5 Q5"
Q5_DIR.mkdir(parents=True, exist_ok=True)

LABELS_CSV = OUTPUT_DIR / "4.4 labels" / "labels.csv"
VIDEOS_CSV = PROJECT_DIR / "videos_master.csv"

RANDOM_STATE = 42
N_FOLDS = 5
SVM_SAMPLE = 15_000
TIME_CUTOFF = pd.Timestamp("2026-07-01")

X_PRE = [
    "pub_hour", "pub_dow", "pub_is_weekend", "pub_month",
    "duration_sec", "is_short_60", "tags_count", "category_id",
    "title_len", "title_words", "title_upper_ratio",
    "title_has_question", "title_has_exclaim", "title_has_digit",
    "title_has_emoji", "title_has_bracket", "title_has_pipe",
    "title_n_hashtag",
    "log_subs", "channel_age_days", "total_videos",
]

FORBIDDEN = [
    "views", "likes", "comments", "like_rate", "comment_rate",
    "views_per_day", "age_days_last", "n_obs", "ever_trending",
    "log_views", "lv_adj", "pct_in_age",
]
CHANNEL_FEATURES = ["log_subs", "channel_age_days", "total_videos"]

BOOL_FEATURES = [
    "pub_is_weekend", "is_short_60", "title_has_question", "title_has_exclaim",
    "title_has_digit", "title_has_emoji", "title_has_bracket", "title_has_pipe",
]

LABEL_INFO = OrderedDict([
    ("viral_A", {
        "name": "viral_A",
        "title": "viral_A",
        "eligible": lambda d: d["in_H"].astype(bool),
        "y_col": "viral_A",
    }),
    ("breakout_B", {
        "name": "breakout_B",
        "title": "breakout_B",
        "eligible": lambda d: d["breakout_B"].notna(),
        "y_col": "breakout_B",
    }),
    ("viral_C", {
        "name": "viral_C",
        "title": "viral_C",
        "eligible": lambda d: d["in_window_C"].astype(bool),
        "y_col": "viral_C",
    }),
])

MODEL_NAMES = [
    "Mô hình nền (log_subs)",
    "Decision Tree",
    "Random Forest",
    "SVM (RBF)",
    "XGBoost",
]

METRIC_COLS = ["roc_auc", "pr_auc", "precision", "recall", "f1", "recall_top10"]

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


def log(msg: str = "") -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Dữ liệu
# ---------------------------------------------------------------------------
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    labels = pd.read_csv(
        LABELS_CSV,
        dtype={
            "video_id": str, "channel_id": str,
            "viral_A": "Int8", "breakout_B": "Int8", "viral_C": "Int8",
            "in_H": bool, "in_window_C": bool,
        },
        low_memory=False,
    )
    videos = pd.read_csv(
        VIDEOS_CSV,
        usecols=["video_id"] + X_PRE,
        low_memory=False,
    )
    # is_short_60 có ở cả hai file -> giữ bản từ videos_master
    labels = labels.drop(columns=[c for c in X_PRE if c in labels.columns and c != "video_id"])
    df = labels.merge(videos, on="video_id", how="left", validate="one_to_one")
    missing = [c for c in X_PRE if c not in df.columns]
    if missing:
        raise ValueError(f"Thiếu cột X_PRE: {missing}")

    # ---- assert chặn cột cấm (kiểm tra trên X_PRE và ma trận X) ----
    leaked = [c for c in X_PRE if c in FORBIDDEN or c.startswith("trend_")]
    if leaked:
        raise AssertionError(f"X_PRE chứa cột cấm: {leaked}")

    # ---- dựng ma trận đặc trưng một lần, cố định cột ----
    categories = sorted(int(c) for c in df["category_id"].dropna().unique())
    base = df.drop(columns=["category_id"]).copy()
    for c in BOOL_FEATURES:
        base[c] = base[c].astype(bool).astype(np.int8)
    for c in [c for c in X_PRE if c not in BOOL_FEATURES and c != "category_id"]:
        base[c] = pd.to_numeric(base[c], errors="coerce").astype(float)

    for cat in categories[1:]:  # bỏ nhóm gốc (category_id nhỏ nhất)
        base[f"cat_{cat}"] = (df["category_id"] == cat).astype(np.int8)

    feature_cols = [c for c in X_PRE if c != "category_id"] + [
        f"cat_{c}" for c in categories[1:]
    ]
    assert not set(feature_cols) & set(FORBIDDEN)
    return df, base, feature_cols


def stratified_sample(y: np.ndarray, n: int, seed: int) -> np.ndarray:
    if len(y) <= n:
        return np.arange(len(y))
    rng = np.random.RandomState(seed)
    parts = []
    for cls in np.unique(y):
        cls_idx = np.flatnonzero(y == cls)
        take = max(1, int(round(n * len(cls_idx) / len(y))))
        take = min(take, len(cls_idx))
        parts.append(rng.choice(cls_idx, take, replace=False))
    idx = np.concatenate(parts)
    rng.shuffle(idx)
    return idx[:n]


# ---------------------------------------------------------------------------
# Mô hình
# ---------------------------------------------------------------------------
def make_model(name: str, y_train: np.ndarray):
    pos = int(np.sum(y_train))
    neg = int(len(y_train) - pos)
    spw = neg / max(pos, 1)
    if name == "Mô hình nền (log_subs)":
        return Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
        ])
    if name == "Decision Tree":
        return DecisionTreeClassifier(
            max_depth=6, min_samples_leaf=50,
            class_weight="balanced", random_state=RANDOM_STATE,
        )
    if name == "Random Forest":
        return RandomForestClassifier(
            n_estimators=300, min_samples_leaf=5,
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE, n_jobs=-1,
        )
    if name == "SVM (RBF)":
        return Pipeline([
            ("scaler", StandardScaler()),
            ("clf", SVC(kernel="rbf", C=1.0, gamma="scale",
                        cache_size=1500, random_state=RANDOM_STATE)),
        ])
    if name == "XGBoost":
        return XGBClassifier(
            n_estimators=280, max_depth=4, learning_rate=0.06,
            scale_pos_weight=spw, subsample=0.9, colsample_bytree=0.9,
            random_state=RANDOM_STATE, n_jobs=-1,
            eval_metric="logloss", tree_method="hist", verbosity=0,
        )
    raise ValueError(name)


def _select(name: str, X: pd.DataFrame) -> pd.DataFrame:
    """Mô hình nền chỉ dùng log_subs."""
    if name == "Mô hình nền (log_subs)":
        return X[["log_subs"]]
    return X


def scores_of(model, X: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    return model.decision_function(X)


def fit_model(name: str, X: pd.DataFrame, y: np.ndarray):
    model = make_model(name, y)
    Xs = _select(name, X)
    if name == "SVM (RBF)":
        idx = stratified_sample(y, SVM_SAMPLE, RANDOM_STATE)
        model.fit(Xs.iloc[idx], y[idx])
    else:
        model.fit(Xs, y)
    return model


def best_top_rate(s: np.ndarray, y: np.ndarray) -> float:
    """Tỷ lệ dương tối ưu F1 trên tập validation (bền với lệch thang điểm giữa fold)."""
    n = len(y)
    total = int(np.sum(y))
    if total == 0:
        return 0.1
    order = np.argsort(-s)
    cum = np.cumsum(y[order])
    ks = np.arange(1, n + 1)
    prec = cum / ks
    rec = cum / total
    f1 = 2 * prec * rec / np.clip(prec + rec, 1e-12, None)
    max_k = max(1, int(0.50 * n))
    k = int(np.argmax(f1[:max_k])) + 1
    return k / n


def tune_threshold(model, X_val: pd.DataFrame, y_val: np.ndarray) -> tuple[float, float]:
    """Trả về (tỷ lệ dương tối ưu F1, ngưỡng tuyệt đối tương ứng)."""
    s = scores_of(model, X_val)
    rate = best_top_rate(s, y_val)
    thr = float(np.quantile(s, 1.0 - rate))
    return rate, thr


def evaluate(y: np.ndarray, s: np.ndarray, rate: float) -> dict:
    k = max(1, int(np.ceil(rate * len(y))))
    thr = float(np.sort(s)[-k])
    pred = (s >= thr).astype(int)
    k_top = max(1, int(np.ceil(0.10 * len(y))))
    top_idx = np.argsort(-s)[:k_top]
    return {
        "roc_auc": float(roc_auc_score(y, s)),
        "pr_auc": float(average_precision_score(y, s)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "recall_top10": float(np.sum(y[top_idx]) / max(int(np.sum(y)), 1)),
    }


def run_fold(name, X_tr, y_tr, groups_tr, X_te, y_te, seed):
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
    fit_idx, val_idx = next(gss.split(X_tr, y_tr, groups=groups_tr))

    m_val = fit_model(name, X_tr.iloc[fit_idx], y_tr[fit_idx])
    rate, thr = tune_threshold(m_val, _select(name, X_tr.iloc[val_idx]), y_tr[val_idx])

    m_full = fit_model(name, X_tr, y_tr)
    s = scores_of(m_full, _select(name, X_te))
    met = evaluate(y_te, s, rate)
    met["threshold"] = thr
    met["pos_rate"] = rate
    return met, m_full, s


# ---------------------------------------------------------------------------
# Các khối phân tích
# ---------------------------------------------------------------------------
def cv_experiment(label_key, df, base, features, quick=False):
    info = LABEL_INFO[label_key]
    mask = info["eligible"](df).to_numpy()
    d = df.loc[mask].reset_index(drop=True)
    X = base.loc[mask, features].reset_index(drop=True)
    if X.isna().any().any():
        raise ValueError(
            f"{label_key}: X còn giá trị thiếu ở "
            f"{X.columns[X.isna().any()].tolist()}"
        )
    y = d[info["y_col"]].astype(int).to_numpy()
    groups = d["channel_id"].to_numpy()

    log(f"\n=== {label_key}: n={len(y):,} | dương={int(y.sum()):,} "
        f"({y.mean()*100:.2f}%) | kênh={len(np.unique(groups)):,} ===")

    gkf = GroupKFold(n_splits=N_FOLDS)
    fold_rows = []
    fold_models = []
    folds = list(gkf.split(X, y, groups=groups))
    if quick:
        folds = folds[:2]

    for k, (tr, te) in enumerate(folds, start=1):
        log(f"--- fold {k}/{len(folds)}: train={len(tr):,} test={len(te):,}")
        for name in MODEL_NAMES:
            t0 = time.time()
            met, model, _ = run_fold(
                name, X.iloc[tr], y[tr], groups[tr], X.iloc[te], y[te],
                seed=RANDOM_STATE + k,
            )
            met.update({"label": label_key, "fold": k, "model": name,
                        "n_train": len(tr), "n_test": len(te),
                        "n_pos_test": int(y[te].sum())})
            fold_rows.append(met)
            fold_models.append((k, name, model, te, thr_of(met)))
            log(f"    {name:26s} AUC={met['roc_auc']:.3f} "
                f"PR={met['pr_auc']:.3f} F1={met['f1']:.3f} "
                f"({time.time()-t0:.0f}s)")

    folds_df = pd.DataFrame(fold_rows)
    comp = summarize(folds_df, ["label", "model"])
    log(f"--- {label_key}: xong 5 fold")
    return d, X, y, groups, folds_df, comp, fold_models


def thr_of(met):
    return met.get("threshold", 0.5)


def summarize(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    g = df.groupby(keys, sort=False)
    out = g[METRIC_COLS].mean().reset_index()
    sd = g[METRIC_COLS].std(ddof=0).reset_index()
    for c in METRIC_COLS:
        out[c + "_sd"] = sd[c].to_numpy()
    out["n_folds"] = g.size().to_numpy()
    return out


def pick_best(comp: pd.DataFrame) -> str:
    c = comp.copy()
    c = c.sort_values(["pr_auc", "roc_auc"], ascending=False)
    return str(c.iloc[0]["model"])


def time_experiment(label_key, d, X, y, best_name):
    dates = pd.to_datetime(d["pub_date_vn"])
    tr = np.flatnonzero((dates < TIME_CUTOFF).to_numpy())
    te = np.flatnonzero((dates >= TIME_CUTOFF).to_numpy())
    log(f"\n=== Kiểm tra thời gian {label_key}: train={len(tr):,} | test={len(te):,}")
    if len(tr) == 0 or len(te) == 0 or y[tr].sum() == 0 or y[te].sum() == 0:
        log("    -> bỏ qua (không đủ dữ liệu hai phía mốc 01/07/2026)")
        return pd.DataFrame()

    rows = []
    test_models = {}
    for name in [MODEL_NAMES[0], best_name]:
        if name in test_models:
            continue
        t0 = time.time()
        met, model, _ = run_fold(
            name, X.iloc[tr], y[tr], d["channel_id"].to_numpy()[tr],
            X.iloc[te], y[te], seed=RANDOM_STATE,
        )
        met.update({"label": label_key, "model": name,
                    "n_train": len(tr), "n_test": len(te),
                    "n_pos_test": int(y[te].sum())})
        rows.append(met)
        test_models[name] = model
        log(f"    {name:26s} AUC={met['roc_auc']:.3f} PR={met['pr_auc']:.3f} "
            f"({time.time()-t0:.0f}s)")
    return pd.DataFrame(rows), test_models


def ablation_experiment(label_key, X, y, groups, best_name):
    no_chan = [c for c in X.columns if c not in CHANNEL_FEATURES]
    Xn = X[no_chan]
    # dùng lại đúng fold của channel_id
    gkf = GroupKFold(n_splits=N_FOLDS)
    rows = []
    for k, (tr, te) in enumerate(gkf.split(Xn, y, groups=groups), start=1):
        met, _, _ = run_fold(
            best_name, Xn.iloc[tr], y[tr], groups[tr], Xn.iloc[te], y[te],
            seed=RANDOM_STATE + k,
        )
        met.update({"label": label_key, "fold": k, "model": best_name,
                    "config": "Bỏ nhóm biến kênh"})
        rows.append(met)
        log(f"    ablation fold {k}: PR={met['pr_auc']:.3f} AUC={met['roc_auc']:.3f}")
    return pd.DataFrame(rows)


def sensitivity_experiment(label_key, df, base, features, best_name, thresholds):
    info = LABEL_INFO["viral_A"]
    mask = info["eligible"](df).to_numpy()
    d = df.loc[mask].reset_index(drop=True)
    X = base.loc[mask, features].reset_index(drop=True)
    groups = d["channel_id"].to_numpy()
    pct = d["pct_in_age"].to_numpy()
    gkf = GroupKFold(n_splits=N_FOLDS)
    rows = []
    for q in thresholds:
        y = (pct >= 1.0 - q).astype(int)
        log(f"\n=== Độ nhạy viral_A top {q*100:.0f}%: dương={int(y.sum()):,} "
            f"({y.mean()*100:.2f}%)")
        for k, (tr, te) in enumerate(gkf.split(X, y, groups=groups), start=1):
            met, _, _ = run_fold(
                best_name, X.iloc[tr], y[tr], groups[tr], X.iloc[te], y[te],
                seed=RANDOM_STATE + k,
            )
            met.update({"label": "viral_A", "fold": k, "model": best_name,
                        "threshold_pct": int(round(q * 100)), "n_pos": int(y.sum())})
            rows.append(met)
        log(f"    xong top {q*100:.0f}%")
    return pd.DataFrame(rows)


def importance_experiment(label_key, d, X, y, best_name, model, test_idx):
    feats = list(X.columns)
    n = min(len(test_idx), 20_000)
    rng = np.random.RandomState(RANDOM_STATE)
    idx = rng.choice(test_idx, n, replace=False)
    Xs, ys = X.iloc[idx], y[idx]
    log(f"\n=== Permutation importance ({best_name}, {label_key}, n={n:,})")
    t0 = time.time()
    # n_jobs=1: tránh BrokenProcessPool của joblib/loky khi mô hình Random Forest
    # quá lớn để pickle sang tiến trình con (đã gặp lỗi "failed to un-serialize").
    r = permutation_importance(
        model, Xs, ys, scoring="roc_auc",
        n_repeats=3, random_state=RANDOM_STATE, n_jobs=1,
    )
    out = pd.DataFrame({
        "feature": feats,
        "importance_mean": r.importances_mean,
        "importance_std": r.importances_std,
    }).sort_values("importance_mean", ascending=False).reset_index(drop=True)
    log(f"    xong ({time.time()-t0:.0f}s)")
    return out


# ---------------------------------------------------------------------------
# Xuất file
# ---------------------------------------------------------------------------
def fmt(v, nd=3):
    if pd.isna(v):
        return ""
    return f"{v:.{nd}f}"


def write_excel(sheets: dict[str, pd.DataFrame], path: Path, notes: dict[str, str]):
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        pd.DataFrame({"Nội dung": ["Xem hướng dẫn ở sheet 00_Huong_dan"]}).to_excel(
            xw, sheet_name="00_Huong_dan", index=False)
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name, index=False)
        for name, note in notes.items():
            pd.DataFrame({"Ghi chú": [note]}).to_excel(
                xw, sheet_name=f"GC_{name[:20]}", index=False)
    # định dạng
    from openpyxl import load_workbook
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    t_start = time.time()
    log("=" * 78)
    log("Q5 - DỰ BÁO VIDEO VIRAL")
    log(f"Chạy: {'QUICK (2 fold)' if args.quick else 'ĐẦY ĐỦ'} | {datetime.now():%Y-%m-%d %H:%M}")
    log("=" * 78)

    df, base, features = load_data()
    log(f"Đã nạp {len(df):,} dòng; {len(features)} đặc trưng sau one-hot category_id")
    log(f"X_PRE gốc: {len(X_PRE)} biến; cột cấm: đã assert không lọt")

    # ---------- Bảng 5.12 ----------
    rows = []
    for key, info in LABEL_INFO.items():
        mask = info["eligible"](df)
        y = df.loc[mask, info["y_col"]].astype(int)
        rows.append({
            "label": key,
            "n_eligible": int(mask.sum()),
            "n_positive": int(y.sum()),
            "rate_pct": float(y.mean() * 100),
        })
    labels_summary = pd.DataFrame(rows)
    labels_summary.to_csv(Q5_DIR / "q5_labels_summary.csv", index=False, encoding="utf-8-sig")
    log("\nBảng 5.12 (số dương từng nhãn):")
    log(labels_summary.to_string(index=False))

    results = {}
    comp_all = []
    folds_all = []
    time_all = []
    best_models = {}

    for key in LABEL_INFO:
        d, X, y, groups, folds_df, comp, fold_models = cv_experiment(
            key, df, base, features, quick=args.quick
        )
        best = pick_best(comp)
        best_models[key] = best
        comp_all.append(comp)
        folds_all.append(folds_df)
        results[key] = dict(d=d, X=X, y=y, groups=groups)
        log(f"*** Mô hình tốt nhất {key}: {best} "
            f"(PR-AUC={comp.loc[comp.model == best, 'pr_auc'].iloc[0]:.3f})")

        if not args.quick:
            # ----- kiểm tra thời gian -----
            te_res = time_experiment(key, d, X, y, best)
            if isinstance(te_res, tuple):
                tt, test_models = te_res
                if len(tt):
                    time_all.append(tt)
                if best in test_models:
                    results[key]["time_model"] = test_models[best]
                    dates = pd.to_datetime(d["pub_date_vn"])
                    results[key]["time_test_idx"] = np.flatnonzero(
                        (dates >= TIME_CUTOFF).to_numpy())

            # ----- xuất dữ liệu cho R (fold 1) -----
            export = d[["video_id", "channel_id", "pub_date_vn"]].copy()
            export["y"] = y
            export["fold"] = -1
            gkf = GroupKFold(n_splits=N_FOLDS)
            for k, (_, te) in enumerate(gkf.split(X, y, groups=groups), start=1):
                export.loc[te, "fold"] = k
            export = pd.concat(
                [export.reset_index(drop=True), X.reset_index(drop=True)], axis=1
            )
            export.to_csv(Q5_DIR / f"q5_model_data_{key}.csv",
                          index=False, encoding="utf-8-sig")

    comp_all = pd.concat(comp_all, ignore_index=True)
    folds_all = pd.concat(folds_all, ignore_index=True)
    comp_all.to_csv(Q5_DIR / "q5_model_comparison.csv", index=False, encoding="utf-8-sig")
    folds_all.to_csv(Q5_DIR / "q5_cv_folds.csv", index=False, encoding="utf-8-sig")
    if time_all:
        time_df = pd.concat(time_all, ignore_index=True)
        time_df.to_csv(Q5_DIR / "q5_time_test.csv", index=False, encoding="utf-8-sig")
    else:
        time_df = pd.DataFrame()

    # ---------- ablation, sensitivity, importance ----------
    ablation_rows = []
    sensitivity_df = pd.DataFrame()
    importance_df = pd.DataFrame()
    importance_label = "viral_A"

    if not args.quick:
        for key in ["viral_A", "breakout_B"]:
            r = results[key]
            log(f"\n>>> Ablation {key} với {best_models[key]}")
            ab = ablation_experiment(key, r["X"], r["y"],
                                     r["groups"], best_models[key])
            ablation_rows.append(ab)

        sensitivity_df = sensitivity_experiment(
            "viral_A", df, base, features, best_models["viral_A"], [0.05, 0.20]
        )

        best = best_models["viral_A"]
        r = results["viral_A"]
        if "time_model" in r:
            model = r["time_model"]
            idx = r["time_test_idx"]
        else:
            model = None
            idx = np.arange(len(r["y"]))
        if model is not None:
            importance_df = importance_experiment(
                "viral_A", r["d"], r["X"], r["y"], best, model, idx
            )

    ablation_df = pd.concat(ablation_rows, ignore_index=True) if ablation_rows else pd.DataFrame()

    # ---------- lưu CSV phụ ----------
    if len(ablation_df):
        ab_sum = summarize(ablation_df, ["label", "model", "config"])
        ab_sum.to_csv(Q5_DIR / "q5_ablation.csv", index=False, encoding="utf-8-sig")
    else:
        ab_sum = pd.DataFrame()
    if len(sensitivity_df):
        se_sum = summarize(sensitivity_df, ["label", "model", "threshold_pct", "n_pos"])
        se_sum.to_csv(Q5_DIR / "q5_sensitivity.csv", index=False, encoding="utf-8-sig")
    else:
        se_sum = pd.DataFrame()
    if len(importance_df):
        importance_df.to_csv(Q5_DIR / "q5_importance.csv", index=False, encoding="utf-8-sig")

    # ---------- Hình 5.8 ----------
    if len(importance_df):
        top = importance_df.head(15).iloc[::-1]
        fig, ax = plt.subplots(figsize=(8.6, 6.2), dpi=160)
        ax.barh(top["feature"], top["importance_mean"],
                xerr=top["importance_std"], color="#2E6DA4", ecolor="#888888")
        ax.set_xlabel("Giảm ROC-AUC khi hoán vị biến")
        ax.set_title(
            f"Hình 5.8. Permutation importance — {best_models['viral_A']} "
            f"(nhãn viral_A, tập kiểm tra theo thời gian)"
        )
        ax.grid(axis="x", alpha=0.3)
        fig.tight_layout()
        fig.savefig(Q5_DIR / "q5_importance.png")
        plt.close(fig)

    # ---------- Bảng 5.15 / 5.16 dạng đầy đủ ----------
    ab_table = pd.DataFrame()
    if len(ab_sum):
        rows_ab = []
        for label in ["viral_A", "breakout_B"]:
            full = comp_all[(comp_all.label == label)
                            & (comp_all.model == best_models[label])]
            base_pr = np.nan
            base_auc = np.nan
            if len(full):
                rr = full.iloc[0]
                base_pr, base_auc = rr["pr_auc"], rr["roc_auc"]
                rows_ab.append({
                    "label": label, "model": rr["model"],
                    "config": "Đủ biến X_PRE",
                    "pr_auc": base_pr, "roc_auc": base_auc,
                    "delta_pr_auc": 0.0, "delta_roc_auc": 0.0,
                })
            no = ab_sum[(ab_sum.label == label)
                        & (ab_sum.config == "Bỏ nhóm biến kênh")]
            if len(no):
                nn = no.iloc[0]
                rows_ab.append({
                    "label": label, "model": nn["model"],
                    "config": "Bỏ nhóm biến kênh",
                    "pr_auc": nn["pr_auc"], "roc_auc": nn["roc_auc"],
                    "delta_pr_auc": nn["pr_auc"] - base_pr,
                    "delta_roc_auc": nn["roc_auc"] - base_auc,
                })
        ab_table = pd.DataFrame(rows_ab)

    se_table = pd.DataFrame()
    if len(se_sum):
        se_table = se_sum[["threshold_pct", "n_pos", "pr_auc", "roc_auc"]].copy()
        if 10 not in set(se_table["threshold_pct"].astype(int)):
            ten = comp_all[(comp_all.label == "viral_A")
                           & (comp_all.model == best_models["viral_A"])]
            if len(ten):
                t = ten.iloc[0]
                n_pos_10 = int(labels_summary.loc[
                    labels_summary.label == "viral_A", "n_positive"].iloc[0])
                se_table.loc[len(se_table)] = [10, n_pos_10, t["pr_auc"], t["roc_auc"]]
        se_table = se_table.sort_values("threshold_pct").reset_index(drop=True)

    # ---------- Excel ----------
    sheets = {
        "01_Bang_5_11_viral_A": comp_all[comp_all.label == "viral_A"][
            ["model"] + METRIC_COLS + [c + "_sd" for c in METRIC_COLS]
        ].reset_index(drop=True),
        "02_Bang_5_13_breakout_B": comp_all[comp_all.label == "breakout_B"][
            ["model"] + METRIC_COLS + [c + "_sd" for c in METRIC_COLS]
        ].reset_index(drop=True),
        "03_Bang_5_12_nhan": labels_summary,
        "08_CV_folds": folds_all,
    }
    if len(time_df):
        sheets["04_Bang_5_14_thoi_gian"] = time_df[
            ["label", "model"] + METRIC_COLS
        ].reset_index(drop=True)
    if len(ab_table):
        sheets["05_Bang_5_15_ablation"] = ab_table
    if len(se_table):
        sheets["06_Bang_5_16_do_nhay"] = se_table
    if len(importance_df):
        sheets["07_Importance"] = importance_df.head(30)

    notes = {
        "Bang_5_11_viral_A": "Trung bình 5 fold GroupKFold theo channel_id; _sd là độ lệch chuẩn (ddof=0).",
        "Bang_5_13_breakout_B": "Trung bình 5 fold GroupKFold theo channel_id; _sd là độ lệch chuẩn (ddof=0).",
        "Bang_5_12_nhan": "viral_C chỉ huấn luyện vì có 168 >= 100 video dương.",
        "Bang_5_14_thoi_gian": "Train trước 01/07/2026, test từ 01/07/2026; viral_C không có train trước mốc.",
        "Bang_5_15_ablation": "Bỏ log_subs, channel_age_days, total_videos; so với đủ biến ở Bảng 5.11/5.13.",
        "Bang_5_16_do_nhay": "Nhãn viral_A định nghĩa lại theo pct_in_age >= 1 - q; top 10% là mặc định.",
        "Importance": "Permutation importance trên tập kiểm tra theo thời gian, scoring ROC-AUC, 3 lần lặp.",
    }
    write_excel(sheets, Q5_DIR / "Q5_tong_hop.xlsx", notes)

    # ---------- Báo cáo ----------
    write_report(labels_summary, comp_all, time_df, ab_sum, se_sum,
                 importance_df, best_models, features)

    log("\n" + "=" * 78)
    log(f"HOÀN TẤT sau {(time.time()-t_start)/60:.1f} phút")
    log(f"Thư mục: {Q5_DIR}")
    log("=" * 78)


def write_report(labels_summary, comp, time_df, ab, se, imp, best_models, features):
    L = []
    A = L.append
    A("# Q5 — Dự báo video viral\n")
    A(f"*Sinh tự động: {datetime.now():%Y-%m-%d %H:%M} — dữ liệu `labels.csv` "
      f"(snapshot hiện có, chưa phải data_final_20261113).*\n")
    A("## 1. Cỡ mẫu và nhãn\n")
    A("| Nhãn | Số video đủ điều kiện | Số video dương | Tỷ lệ dương (%) |")
    A("|---|---:|---:|---:|")
    for _, r in labels_summary.iterrows():
        A(f"| {r['label']} | {r['n_eligible']:,} | {r['n_positive']:,} | {r['rate_pct']:.2f} |")
    A("\n## 2. So sánh mô hình (5 fold GroupKFold theo channel_id)\n")
    for key, tbl in [("viral_A", "Bảng 5.11"), ("breakout_B", "Bảng 5.13")]:
        sub = comp[comp.label == key]
        if not len(sub):
            continue
        A(f"\n**{tbl} — {key}** (trung bình ± độ lệch chuẩn)\n")
        A("| Mô hình | ROC-AUC | PR-AUC | Precision | Recall | F1 | Recall top 10% |")
        A("|---|---:|---:|---:|---:|---:|---:|")
        for _, r in sub.iterrows():
            A(f"| {r['model']} | {r['roc_auc']:.3f} ± {r['roc_auc_sd']:.3f} | "
              f"{r['pr_auc']:.3f} ± {r['pr_auc_sd']:.3f} | "
              f"{r['precision']:.3f} | {r['recall']:.3f} | {r['f1']:.3f} | "
              f"{r['recall_top10']:.3f} |")
    A("\n## 3. Mô hình tốt nhất\n")
    for key, m in best_models.items():
        sub = comp[(comp.label == key) & (comp.model == m)]
        if len(sub):
            rr = sub.iloc[0]
            A(f"- **{key}**: {m} — PR-AUC {rr['pr_auc']:.3f}, "
              f"ROC-AUC {rr['roc_auc']:.3f}")
        else:
            A(f"- **{key}**: {m}")
    A("\nTiêu chí chọn: PR-AUC trung bình cao nhất (phụ: ROC-AUC). "
      "Nếu mô hình tốt nhất không hơn mô hình nền về PR-AUC thì kết quả được ghi trung thực.\n")

    if len(time_df):
        A("## 4. Kiểm tra theo thời gian (train trước 01/07/2026)\n")
        A("| Nhãn | Mô hình | ROC-AUC | PR-AUC | Precision | Recall | F1 |")
        A("|---|---|---:|---:|---:|---:|---:|")
        for _, r in time_df.iterrows():
            A(f"| {r['label']} | {r['model']} | {r['roc_auc']:.3f} | {r['pr_auc']:.3f} | "
              f"{r['precision']:.3f} | {r['recall']:.3f} | {r['f1']:.3f} |")
        A("\n*viral_C không có video nào đăng trước 01/07/2026 nên không kiểm tra thời gian được.*\n")

    if len(ab):
        A("## 5. Ablation — bỏ nhóm biến kênh\n")
        A("| Nhãn | Mô hình | Cấu hình | PR-AUC | ROC-AUC | Δ PR-AUC |")
        A("|---|---|---|---:|---:|---:|")
        for label in ["viral_A", "breakout_B"]:
            full = comp[(comp.label == label) & (comp.model == best_models[label])]
            base_pr = None
            if len(full):
                rr = full.iloc[0]
                base_pr = rr["pr_auc"]
                A(f"| {label} | {rr['model']} | Đủ biến X_PRE | "
                  f"{rr['pr_auc']:.3f} | {rr['roc_auc']:.3f} | – |")
            no = ab[(ab.label == label) & (ab.config == "Bỏ nhóm biến kênh")]
            if len(no):
                nn = no.iloc[0]
                delta = (f"{nn['pr_auc'] - base_pr:+.3f}"
                         if base_pr is not None else "")
                A(f"| {label} | {nn['model']} | Bỏ nhóm biến kênh | "
                  f"{nn['pr_auc']:.3f} | {nn['roc_auc']:.3f} | {delta} |")
        A("")

    if len(se):
        A("## 6. Độ nhạy ngưỡng nhãn viral_A\n")
        rows_se = se[["threshold_pct", "n_pos", "pr_auc", "roc_auc"]].to_dict("records")
        if not any(int(r["threshold_pct"]) == 10 for r in rows_se):
            ten = comp[(comp.label == "viral_A")
                       & (comp.model == best_models["viral_A"])]
            if len(ten):
                t = ten.iloc[0]
                rows_se.append({"threshold_pct": 10, "n_pos": 9542,
                                "pr_auc": t["pr_auc"], "roc_auc": t["roc_auc"]})
        rows_se = sorted(rows_se, key=lambda r: int(r["threshold_pct"]))
        A("| Ngưỡng | Số dương | PR-AUC | ROC-AUC |")
        A("|---|---:|---:|---:|")
        for r in rows_se:
            lab = "Top 10% (mặc định)" if int(r["threshold_pct"]) == 10 \
                else f"Top {int(r['threshold_pct'])}%"
            A(f"| {lab} | {int(r['n_pos']):,} | {r['pr_auc']:.3f} | "
              f"{r['roc_auc']:.3f} |")
        A("")

    if len(imp):
        A("## 7. Permutation importance (top 10)\n")
        A("| Biến | Giảm ROC-AUC (trung bình) | Độ lệch |")
        A("|---|---:|---:|")
        for _, r in imp.head(10).iterrows():
            A(f"| {r['feature']} | {r['importance_mean']:.4f} | {r['importance_std']:.4f} |")
        A("\n*Hình 5.8: `q5_importance.png`.*\n")

    A("## 8. Ghi chú kỹ thuật\n")
    A(f"- X_PRE gốc {len(X_PRE)} biến; `category_id` one-hot thành "
      f"{len([f for f in features if f.startswith('cat_')])} cột, tổng {len(features)} đặc trưng.")
    A("- Có `assert` chặn cột cấm (views, likes, comments, views_per_day, age_days_last, "
      "n_obs, ever_trending, log_views, lv_adj, pct_in_age, trend_*).")
    A(f"- SVM chạy trên mẫu phân tầng {SVM_SAMPLE:,} dòng mỗi lần fit (15–20 nghìn theo yêu cầu).")
    A("- Ngưỡng chọn trên 20% kênh của train (GroupShuffleSplit, random_state=42) để tối đa F1; "
      "ngưỡng biểu diễn theo tỷ lệ dương tối ưu (top-rate) để bền với lệch thang điểm giữa fold, "
      "sau đó fit lại toàn bộ train và đánh giá test.")
    A("- Random Forest được đối chiếu bằng R (`03_q5_rf.R`), xem `q5_R_check.txt`.")
    A("- Số liệu là tạm tính trên snapshot hiện có; phải chạy lại trên `data_final_20261113` "
      "trước hạn 15/11/2026 23:59.")

    # ---------- Xuất Word (.docx) ----------
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    from md2docx_q5 import convert_md_text

    convert_md_text("\n".join(L), Q5_DIR / "q5_report.docx")


if __name__ == "__main__":
    main()
