"""q2d_holiday.py - Q2d hiệu ứng dịp lễ và Tết (K7) bằng Python.
Mỗi period_id là 1 kỳ. So lv_adj của video H đăng trong kỳ với video H đăng ở ngày KHÔNG nghỉ lễ trong cùng các tháng dương lịch kỳ chạm tới.
Welch t-test, Cohen's d (pooled SD), KTC 95% của chênh lệch (Welch), Holm. Kỳ < 100 video gộp thành 1 nhóm. Chạy thêm bản bỏ video ngắn (is_short_60).
Dùng: DATA_DIR=<thư mục> python q2d_holiday.py [out_dir]   (mặc định outputs/q2d)
"""
import os, sys
import numpy as np, pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from prep import load_prep, DATA_DIR

OUT = sys.argv[1] if len(sys.argv) > 1 else "outputs/q2d"
os.makedirs(OUT, exist_ok=True)
MIN_N = 100

hol = pd.read_csv("holidays_vn.csv", parse_dates=["date"], encoding="utf-8-sig")
hol_days = set(hol["date"])

v = load_prep()
H = v[v["in_H"]].copy()
H["pub_date"] = pd.to_datetime(H["pub_date_vn"])
H["ym"] = H["pub_date"].dt.to_period("M")
H["is_hol"] = H["pub_date"].isin(hol_days)
H = H[["video_id", "channel_id", "pub_date", "ym", "is_hol", "lv_adj", "is_short_60"]]

def welch(x, y):
    """x = kỳ lễ, y = đối chứng. Trả về chênh lệch (x - y), KTC 95%, t, df, p, Cohen's d."""
    nx, ny = len(x), len(y)
    vx, vy = x.var(ddof=1), y.var(ddof=1)
    diff = x.mean() - y.mean()
    se = np.sqrt(vx / nx + vy / ny)
    df = se**4 / ((vx / nx) ** 2 / (nx - 1) + (vy / ny) ** 2 / (ny - 1))
    t = diff / se
    p = 2 * stats.t.sf(abs(t), df)
    tcrit = stats.t.ppf(0.975, df)
    sp = np.sqrt(((nx - 1) * vx + (ny - 1) * vy) / (nx + ny - 2))
    return diff, diff - tcrit * se, diff + tcrit * se, t, df, p, diff / sp

def months_of(days):
    return set(pd.Series(days).dt.to_period("M"))

def group_rows(D, label, days_df):
    """days_df: các dòng lịch nghỉ thuộc nhóm. Kỳ = video có pub_date trong days_df; đối chứng = ngày không nghỉ lễ trong các tháng chạm tới."""
    days = set(days_df["date"])
    mths = months_of(days_df["date"])
    treat = D[D["pub_date"].isin(days)]["lv_adj"]
    ctrl = D[D["ym"].isin(mths) & ~D["is_hol"]]["lv_adj"]
    if len(treat) < 2 or len(ctrl) < 2:
        return dict(group=label, n_period=len(treat), n_control=len(ctrl))
    diff, lo, hi, t, df, p, d = welch(treat, ctrl)
    return dict(group=label, n_period=len(treat), n_control=len(ctrl), mean_period=treat.mean(), mean_control=ctrl.mean(),
                diff=diff, ci95_low=lo, ci95_high=hi, t=t, df=df, p=p, cohens_d=d)

def run(D, version):
    periods = hol.groupby("period_id")
    n_in = {pid: D["pub_date"].isin(set(g["date"])).sum() for pid, g in periods}
    rows, small = [], []
    for pid, g in periods:
        if n_in[pid] >= MIN_N:
            r = group_rows(D, f"{pid} ({g['name'].iloc[0]})", g); r["kind"] = "tet" if g["tet"].iloc[0] else "le"; rows.append(r)
        else:
            small.append(g)
    if small:
        r = group_rows(D, f"Gộp các kỳ < {MIN_N} video ({', '.join(g['period_id'].iloc[0] for g in small)})", pd.concat(small)); r["kind"] = "gop_nho"; rows.append(r)
    # các dòng gộp
    r = group_rows(D, "Gộp Tết", hol[hol.tet == 1]); r["kind"] = "gop"; rows.append(r)
    r = group_rows(D, "Gộp lễ khác (không Tết)", hol[hol.tet == 0]); r["kind"] = "gop"; rows.append(r)
    r = group_rows(D, "Gộp chung", hol); r["kind"] = "gop"; rows.append(r)
    res = pd.DataFrame(rows)
    ok = res["p"].notna()
    res["p_holm"] = np.nan
    res.loc[ok, "p_holm"] = multipletests(res.loc[ok, "p"], method="holm")[1]
    res["version"] = version
    return res

if __name__ == "__main__":
    all_res = run(H, "tat_ca")
    nos = run(H[~H["is_short_60"].astype(bool)], "bo_video_ngan")
    res = pd.concat([all_res, nos], ignore_index=True)
    res.to_csv(os.path.join(OUT, "q2d_results.csv"), index=False, float_format="%.6f")
    print(f"DATA_DIR={DATA_DIR} | n_H={len(H):,} | so kenh={H['channel_id'].nunique()} | so ky nghi le={hol['period_id'].nunique()}")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
    print(res[["version", "group", "n_period", "n_control", "diff", "ci95_low", "ci95_high", "p", "p_holm", "cohens_d"]].round(4).to_string(index=False))
