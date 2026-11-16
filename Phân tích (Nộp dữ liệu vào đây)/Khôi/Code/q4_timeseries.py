"""q4_timeseries.py - Q4 chuỗi thời gian (K6, K8) bằng Python.
S1, S2: ADF/KPSS, ACF/PACF, ARIMA / SARIMA(7) / ARIMAX(lễ, Tết) + seasonal naive; test 28 ngày cuối;
N1, N2: ARIMA bậc nhỏ (p,q<=1), test 5 ngày cuối, chỉ minh họa.
Dùng: python q4_timeseries.py [series_dir] [out_dir]   (mặc định outputs/series, outputs/q4)
Quy ước dùng chung với bản R: d(S1)=1 trên log(S1); d(S2)=0 trên S2 gốc; lưới p,q in 0..2, P,Q in {0,1}; Ljung-Box lag 14.
"""
import os, sys, warnings
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller, kpss, acf, pacf
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.stats.diagnostic import acorr_ljungbox
warnings.filterwarnings("ignore")
np.random.seed(42)

SDIR = sys.argv[1] if len(sys.argv) > 1 else "outputs/series"
OUT = sys.argv[2] if len(sys.argv) > 2 else "outputs/q4"
os.makedirs(OUT, exist_ok=True)
TEST, HORIZON, SEAS, LB_LAG = 28, 28, 7, 14
CFG = {"S1": dict(log=True, d=1), "S2": dict(log=False, d=0)}

daily = pd.read_csv(os.path.join(SDIR, "series_daily.csv"), parse_dates=["date"], index_col="date")
hol = pd.read_csv("holidays_vn.csv", parse_dates=["date"])
hol_other = set(hol.loc[hol.tet == 0, "date"]); hol_tet = set(hol.loc[hol.tet == 1, "date"])
def exog_for(idx):
    return pd.DataFrame({"hol_other": [int(d in hol_other) for d in idx], "tet": [int(d in hol_tet) for d in idx]}, index=idx, dtype=float)

def smape(y, f): y, f = np.asarray(y, float), np.asarray(f, float); return float(np.mean(2 * np.abs(y - f) / (np.abs(y) + np.abs(f))) * 100)
def mae(y, f): return float(np.mean(np.abs(np.asarray(y, float) - np.asarray(f, float))))

def fit(y, order, sorder=(0, 0, 0, 0), exog=None):
    m = SARIMAX(y, exog=exog, order=order, seasonal_order=sorder, trend="n" if order[1] == 1 or sorder[1] else "c",
                enforce_stationarity=True, enforce_invertibility=True)  # bật ràng buộc để hàm hợp lý/AIC cùng cách tính với R::Arima
    r0 = m.fit(disp=False, maxiter=300)
    try:  # lbfgs hay dừng sớm: tinh chỉnh bằng BFGS từ nghiệm đầu, giữ nghiệm có AIC thấp hơn
        r1 = m.fit(start_params=r0.params, disp=False, method="bfgs", maxiter=300)
        return r1 if r1.aic < r0.aic else r0
    except Exception:
        return r0

# ---------- 1. Kiểm định tính dừng + ACF/PACF ----------
def stationarity_table(name, y, log):
    rows = []
    cands = [("goc", y)] + ([("log", np.log(y))] if log else [])
    base = cands[-1][1]
    cands += [("sai_phan_1" if not log else "log_sai_phan_1", base.diff().dropna())]
    for lab, x in cands:
        x = x.dropna()
        rows.append(dict(series=name, transform=lab, n=len(x), adf_p=adfuller(x, autolag="AIC")[1], kpss_p=kpss(x, regression="c", nlags="auto")[1]))
    return rows

def plot_acf(name, x, path):
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.2))
    n = 28
    for a, f, t in [(ax[0], acf(x, nlags=n), "ACF"), (ax[1], pacf(x, nlags=n), "PACF")]:
        a.bar(range(len(f)), f, width=.3, color="#2b6cb0"); a.axhline(0, color="k", lw=.6)
        a.axhline(1.96 / np.sqrt(len(x)), color="r", ls="--", lw=.7); a.axhline(-1.96 / np.sqrt(len(x)), color="r", ls="--", lw=.7)
        a.set_title(f"{t} - {name}")
    plt.tight_layout(); plt.savefig(path, dpi=150); plt.close()

# ---------- 2. Mô hình chuỗi dài ----------
def run_long(name):
    cfg = CFG[name]
    y_raw = daily[name].dropna()
    y_raw = y_raw.asfreq("D")
    z = np.log(y_raw) if cfg["log"] else y_raw
    train_z, test_idx = z.iloc[:-TEST], z.index[-TEST:]
    train_raw, test_raw = y_raw.iloc[:-TEST], y_raw.iloc[-TEST:]
    d = cfg["d"]; inv = (lambda a: np.exp(a)) if cfg["log"] else (lambda a: a)
    ex_all = exog_for(z.index); ex_tr, ex_te = ex_all.iloc[:-TEST], ex_all.iloc[-TEST:]
    stat_rows = stationarity_table(name, y_raw, cfg["log"])
    plot_acf(name, (z.diff().dropna() if d else z), os.path.join(OUT, f"q4_acf_pacf_{name}.png"))

    res = {}
    for fam in ["ARIMA", "SARIMA"]:
        best = None
        for p in range(3):
            for q in range(3):
                for P, Q in ([(0, 0)] if fam == "ARIMA" else [(0, 1), (1, 0), (1, 1)]):
                    try:
                        r = fit(train_z, (p, d, q), (P, 0, Q, SEAS) if fam == "SARIMA" else (0, 0, 0, 0))
                    except Exception: continue
                    if best is None or r.aic < best[0].aic: best = (r, (p, d, q), (P, 0, Q, SEAS) if fam == "SARIMA" else (0, 0, 0, 0))
        res[fam] = best
    so = res["SARIMA"]
    r = fit(train_z, so[1], so[2], ex_tr); res["ARIMAX"] = (r, so[1], so[2])  # ARIMAX = cấu trúc SARIMA tốt nhất + biến lễ/Tết

    rows, preds = [], {}
    last_week = train_raw.iloc[-SEAS:].values
    sn = np.tile(last_week, int(np.ceil(TEST / SEAS)))[:TEST]
    rows.append(dict(series=name, model="Seasonal naive", order="-", seasonal="-", aic=np.nan, mae_test=mae(test_raw, sn), smape_test=smape(test_raw, sn), ljungbox_p=np.nan))
    preds["Seasonal naive"] = pd.DataFrame({"pred": sn, "lo": np.nan, "hi": np.nan}, index=test_idx)
    for fam, (r, o, s) in res.items():
        ex = ex_te if fam == "ARIMAX" else None
        fc = r.get_forecast(TEST, exog=ex); mean = inv(fc.predicted_mean.values); ci = inv(fc.conf_int(0.05).values)
        resid = r.resid.iloc[max(d, 1) + (SEAS if s[0] or s[2] else 0):]
        lb = acorr_ljungbox(resid, lags=[LB_LAG], model_df=o[0] + o[2] + s[0] + s[2])["lb_pvalue"].iloc[0]
        rows.append(dict(series=name, model=fam, order=str(o), seasonal=str(s) if fam != "ARIMA" else "-", aic=r.aic, mae_test=mae(test_raw, mean), smape_test=smape(test_raw, mean), ljungbox_p=lb))
        preds[fam] = pd.DataFrame({"pred": mean, "lo": ci[:, 0], "hi": ci[:, 1]}, index=test_idx)
    comp = pd.DataFrame(rows)
    # chọn theo AIC (trong ARIMA/SARIMA/ARIMAX); đối chiếu seasonal naive
    cand = comp[comp.model != "Seasonal naive"]
    chosen = cand.loc[cand.aic.idxmin(), "model"]
    sn_mae = comp.loc[comp.model == "Seasonal naive", "mae_test"].iloc[0]
    comp["chon_theo_AIC"] = comp.model == chosen
    comp["tot_hon_seasonal_naive"] = np.where(comp.model == "Seasonal naive", np.nan, comp.mae_test < sn_mae)
    # hệ số ARIMAX
    r_x = res["ARIMAX"][0]
    coef = pd.DataFrame({"series": name, "term": r_x.params.index, "coef": r_x.params.values, "se": r_x.bse.values})
    # dự báo 4 tuần với mô hình đã chọn, khớp lại trên toàn bộ chuỗi
    r_ch, o, s = res[chosen]
    use_x = chosen == "ARIMAX"
    r_full = fit(z, o, s, ex_all if use_x else None)
    fidx = pd.date_range(z.index[-1] + pd.Timedelta(days=1), periods=HORIZON, freq="D")
    fc = r_full.get_forecast(HORIZON, exog=exog_for(fidx) if use_x else None)
    fmean, fci = inv(fc.predicted_mean.values), inv(fc.conf_int(0.05).values)
    out = pd.concat([
        pd.DataFrame({"date": train_raw.index, "set": "train", "actual": train_raw.values}),
        pd.DataFrame({"date": test_idx, "set": "test", "actual": test_raw.values, "pred": preds[chosen].pred.values,
                      "lo95": preds[chosen].lo.values, "hi95": preds[chosen].hi.values, "snaive": sn}),
        pd.DataFrame({"date": fidx, "set": "forecast", "pred": fmean, "lo95": fci[:, 0], "hi95": fci[:, 1]}),
    ], ignore_index=True)
    out["model"] = chosen
    out.to_csv(os.path.join(OUT, f"q4_forecast_{name}.csv"), index=False, float_format="%.6f")
    # hình
    fig, ax = plt.subplots(figsize=(11, 4)); tail = out[out["date"] >= out["date"].iloc[-HORIZON - TEST - 90]]
    ax.plot(tail.loc[tail.set != "forecast", "date"], tail.loc[tail.set != "forecast", "actual"], color="#444", lw=1.2, label="thực tế")
    t = out[out.set == "test"]; ax.plot(t.date, t.pred, color="#dd6b20", label=f"{chosen} (test 28 ngày)"); ax.plot(t.date, t.snaive, color="#999", ls=":", label="seasonal naive")
    f = out[out.set == "forecast"]; ax.plot(f.date, f.pred, color="#2b6cb0", label="dự báo 4 tuần"); ax.fill_between(f.date, f.lo95, f.hi95, color="#2b6cb0", alpha=.2, label="KTC 95%")
    ax.set_title(f"Dự báo {name} ({chosen}), DATA_DIR={os.environ.get("DATA_DIR", "data_clean_temp")}"); ax.legend(fontsize=8); plt.tight_layout(); plt.savefig(os.path.join(OUT, f"q4_forecast_{name}.png"), dpi=150); plt.close()
    return stat_rows, comp, coef

# ---------- 3. Chuỗi ngắn N1, N2 ----------
def run_short(name, s, min_points=10, test=5):
    s = s.dropna()
    if len(s) < min_points:
        return dict(series=name, n_points=len(s), order="-", mae_last5="-", note=f"không chạy: chỉ {len(s)} điểm hợp lệ (< {min_points}); chạy lại trên data_final")
    y = s.asfreq("D").interpolate(limit_direction="both") if False else s  # chuỗi có thể có khoảng trống: SARIMAX xử lý NaN nếu reindex ngày
    y = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="D"))
    tr, te = y.iloc[:-test], y.iloc[-test:]
    best = None
    for d in (0, 1):
        for p in (0, 1):
            for q in (0, 1):
                try: r = SARIMAX(tr, order=(p, d, q), trend="c" if d == 0 else "n", enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
                except Exception: continue
                if best is None or r.aic < best[0].aic: best = (r, (p, d, q))
    r, o = best; fc = r.get_forecast(test).predicted_mean
    m = te.notna()
    return dict(series=name, n_points=len(s), order=str(o), mae_last5=mae(te[m], fc[m]), note="ngắn hạn, minh họa")

if __name__ == "__main__":
    st_all, comp_all, coef_all = [], [], []
    for nm in ["S1", "S2"]:
        a, b, c = run_long(nm); st_all += a; comp_all.append(b); coef_all.append(c)
    pd.DataFrame(st_all).to_csv(os.path.join(OUT, "q4_stationarity.csv"), index=False, float_format="%.4f")
    comp = pd.concat(comp_all); comp.to_csv(os.path.join(OUT, "q4_model_comparison.csv"), index=False, float_format="%.4f")
    pd.concat(coef_all).to_csv(os.path.join(OUT, "q4_arimax_coef.csv"), index=False, float_format="%.6f")
    tr = pd.read_csv(os.path.join(SDIR, "series_trending.csv"), parse_dates=["date"], index_col="date")
    short = pd.DataFrame([run_short("N1", tr["N1"]), run_short("N2", tr["N2"])])
    short.to_csv(os.path.join(OUT, "q4_short_series.csv"), index=False)
    pd.set_option("display.width", 200)
    print(pd.DataFrame(st_all).round(4).to_string(index=False)); print(); print(comp.round(4).to_string(index=False)); print(); print(short.to_string(index=False))
