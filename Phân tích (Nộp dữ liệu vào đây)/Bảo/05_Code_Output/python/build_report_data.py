# -*- coding: utf-8 -*-
"""
build_report_data.py - Gom MỌI con số của Muc_Bao.docx vào report_data.json (mỗi số truy được về 1 file trong outputs/).
Chạy lại sau khi chạy các script trên data_final:   python build_report_data.py && node ../report/build_muc_bao.js
Số được định dạng kiểu Việt Nam (dấu chấm phân cách nghìn, dấu phẩy thập phân) như trong báo cáo mẫu.
"""
import os, json, re
import numpy as np
import pandas as pd
from prep import load_master, prep, DATA_DIR

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
O = os.path.join(BASE, "outputs")
OUT_JSON = os.path.join(BASE, "report", "report_data.json")
os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)


def vn(x, d=0):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    s = f"{x:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def pv(p):
    return "< 0,001" if p < 0.001 else vn(p, 3)


def fmt_big(x):  # số lớn trong bảng mô tả
    return vn(x, 0) if (abs(x) >= 1000 or float(x).is_integer()) else vn(x, 2)


def main():
    R = {}
    master = load_master(); H = prep(master)
    dq = open(os.path.join(DATA_DIR, "dq_report.txt"), encoding="utf-8-sig").read()
    R["data_dir"] = os.environ.get("DATA_LABEL", "data_clean (bản 03/11/2026)" if os.path.basename(os.path.normpath(DATA_DIR)) == "uploads" else os.path.basename(os.path.normpath(DATA_DIR)))

    # ---- quy mô
    ch = pd.read_csv(os.path.join(DATA_DIR, "channels_latest.csv"), encoding="utf-8-sig")
    meas = pd.read_csv(os.path.join(DATA_DIR, "measurements.csv"), usecols=["video_id", "run_ts", "run_date", "source", "collected_ts"], low_memory=False,
                       dtype={"video_id": str})
    tr = pd.read_csv(os.path.join(DATA_DIR, "trending_clean.csv"), usecols=["run_ts", "video_id", "run_date"], dtype={"video_id": str})
    nh = master.groupby("channel_id").in_history.sum()
    R["scale"] = {
        "n_video": vn(len(master)), "n_channels": vn(len(ch)), "n_channels_master": vn(master.channel_id.nunique()),
        "n_trending_videos": vn(int(master.ever_trending.sum())), "n_meas": vn(len(meas)),
        "n_trending_rows": vn(len(tr)), "n_trending_snap": vn(tr.run_ts.nunique()),
        "last_collect_vn": pd.to_datetime(meas.collected_ts, utc=True).max().tz_convert("Asia/Ho_Chi_Minh").strftime("%H:%M"),
        "last_collect_date": pd.to_datetime(meas.collected_ts, utc=True).max().tz_convert("Asia/Ho_Chi_Minh").strftime("%d/%m/%Y"),
        "n_runs": vn(meas.run_ts.nunique()), "n_days": vn(meas.run_date.nunique()),
        "day_first": meas.run_date.min(), "day_last": meas.run_date.max(),
        "n_H": vn(len(H)), "n_ch_H": vn(H.channel_id.nunique()),
        "n_not_hist": vn(int((~master.in_history).sum())), "n_live": vn(int(master.is_live_or_upcoming.sum())),
        "n_excl": vn(len(master) - len(H)),
        "n_ch_ge500": vn(int((nh >= 500).sum())), "n_ch_lt500": vn(int(((nh < 500) & (nh > 0)).sum())),
        "n_ch_no_hist": vn(int((nh == 0).sum())), "n_ch_hist": vn(int((nh > 0).sum())),
        "n_ch_ge480": vn(int((nh >= 480).sum())), "max_ch_hist": vn(int(nh.max())),
        "pct_viral": vn(100 * H.viral_A.mean(), 2), "n_viral": vn(int(H.viral_A.sum())),
    }
    # video bị loại khỏi H, từng lý do (có thể chồng lấn)
    R["excl"] = {"not_hist": int((~master.in_history).sum()), "live": int(master.is_live_or_upcoming.sum()),
                 "views0": int((master.views <= 0).sum()), "age_lt1": int((master.age_days_last < 1).sum())}

    # ---- dq_report (đọc nguyên số từ file)
    def g(p, i=1):
        m = re.search(p, dq); return m.group(i) if m else "?"
    R["dq"] = {"trend_raw": g(r"trending_snapshots\.csv:\s*([\d,]+)"), "track_raw": g(r"video_tracking\.csv:\s*([\d,]+)"),
               "hist_raw": g(r"channel_history\.csv:\s*([\d,]+)"), "chan_raw": g(r"channels_info\.csv:\s*([\d,]+)"),
               "bad_id": g(r"(\d+) dòng video_id hỏng"), "fixed_id": g(r"khôi phục (\d+) dòng"),
               "title_suspect": g(r"trước đó ([\d,]+) dòng nghi hỏng"),
               "lk_gt": g(r"likes > views:\s*([\d,]+)"), "cm_gt": g(r"comments > views:\s*([\d,]+)"),
               "v0": g(r"views = 0:\s*([\d,]+)"), "vnan": g(r"views = NaN:\s*([\d,]+)"),
               "dec": g(r"views GIẢM giữa 2 lần đo liên tiếp:\s*([\d,]+)"), "pairs": g(r"liên tiếp:\s*[\d,]+/([\d,]+)"),
               "pct_dq": g(r"cặp \(([\d\.]+)%"), "missing_days": g(r"NGÀY THIẾU:\s*(.*)"),
               "dq_n_meas_vid": g(r"measurements\.csv:\s*([\d,]+) lần đo"), "ge2": g(r"có >=2 lần đo:\s*([\d,]+)"),
               "ge5": g(r">=5 lần đo:\s*([\d,]+)")}
    for k in list(R["dq"]):                      # số trong dq_report dùng dấu phẩy nghìn -> đổi sang kiểu Việt Nam
        v = R["dq"][k]
        if re.fullmatch(r"[\d,]+", v):
            R["dq"][k] = vn(int(v.replace(",", "")))
    d, p = int(R["dq"]["dec"].replace(".", "").replace(",", "")), int(R["dq"]["pairs"].replace(".", "").replace(",", ""))
    R["dq"]["pct_true"] = vn(100 * d / p, 2)

    def _runs(src):
        m = re.search(rf"\n\s+{src}: (\d+) lượt chạy, (\d+) ngày:\s*(.*)", dq)
        return (m.group(1), m.group(2), m.group(3).split(", ")) if m else ("?", "?", [])
    def _ranges(days):
        if not days: return "?"
        ds = pd.to_datetime(pd.Series(days)); out, st, pr = [], ds[0], ds[0]
        for d in list(ds[1:]) + [None]:
            if d is None or (d - pr).days > 1:
                out.append(st.strftime("%d/%m") if st == pr else f"{st:%d/%m}–{pr:%d/%m}"); st = d
            pr = d if d is not None else pr
        return ", ".join(out)
    for nm in ("trending", "tracking", "history"):
        n_run, n_day, days = _runs(nm)
        R["dq"][f"{nm}_runs"], R["dq"][f"{nm}_ndays"], R["dq"][f"{nm}_ranges"] = n_run, n_day, _ranges(days)
    _pd = meas.groupby(["run_date", "source"]).run_ts.nunique().unstack()
    R["perday"] = {k: [int(_pd[k].dropna().min()), int(_pd[k].dropna().max())] for k in ("trending", "tracking")}
    R["dq"]["trend_per_day"] = vn(len(tr) and tr.run_ts.nunique() / max(1, tr.run_date.nunique()), 1)
    mm = master.copy()
    ph = pd.to_datetime(mm["published_ts"], utc=True).dt.tz_convert("Asia/Ho_Chi_Minh").dt.hour
    R["pub_hour_match"] = vn(100 * float((ph == mm["pub_hour"]).mean()), 2)
    R["is_final"] = bool(S_last := meas.run_date.max()) and S_last >= "2026-11-12"
    R["data_label"] = f"dữ liệu chính thức {pd.to_datetime(meas.run_date.min()):%d/%m}–{pd.to_datetime(meas.run_date.max()):%d/%m/%Y}"

    # ---- đối chiếu 30 video (nếu đã điền và chạy pick30.py --summarize)
    f_sum, f_30 = os.path.join(O, "reliability", "reliability_check_summary.csv"), os.path.join(O, "reliability", "reliability_check_30videos.csv")
    R["c30"] = None
    if os.path.exists(f_sum) and os.path.exists(f_30):
        sm, d30 = pd.read_csv(f_sum, encoding="utf-8-sig"), pd.read_csv(f_30, encoding="utf-8-sig")
        if "sai_lech_views" in d30.columns and d30["sai_lech_views"].notna().all():
            pc = lambda x: vn(100 * x, 2) + "%"
            tms = pd.to_datetime(d30["yt_gio_xem"])
            R["c30"] = {
                "rows": [[r.tang.replace("1. ", "").replace("2. ", "").replace("3. ", ""), vn(r.so_video), pc(r.tv_sai_lech_views), pc(r.tv_sai_lech_likes),
                          pc(r.tv_sai_lech_comments), vn(r.tv_gio_chenh_phut, 1)] for r in sm.itertuples()],
                "med_views": pc(d30.sai_lech_views.median()), "med_likes": pc(d30.sai_lech_likes.median()), "med_comments": pc(d30.sai_lech_comments.median()),
                "max_views": pc(d30.sai_lech_views.abs().max()), "share_pos": vn(100 * float((d30.sai_lech_views > 0).mean()), 0),
                "n_neg_views": int((d30.sai_lech_views < 0).sum()),
                # Đếm trùng khớp trên giá trị gốc: cặp (API = 0, YouTube = 0) cũng là trùng khớp.
                # Không dùng sai_lech_* vì tỷ lệ này là NaN khi mẫu số API bằng 0.
                "n_exact_views": int((d30.yt_views == d30.api_views).sum()),
                "n_exact_likes": int((d30.yt_likes == d30.api_likes).sum()),
                "n_exact_comments": int((d30.yt_comments == d30.api_comments).sum()),
                "n_nonzero_views": int((d30.api_views > 0).sum()),
                "n_nonzero_likes": int((d30.api_likes > 0).sum()),
                "n_nonzero_comments": int((d30.api_comments > 0).sum()),
                "n_exact_views_nonzero": int(((d30.api_views > 0) & (d30.yt_views == d30.api_views)).sum()),
                "n_exact_likes_nonzero": int(((d30.api_likes > 0) & (d30.yt_likes == d30.api_likes)).sum()),
                "n_exact_comments_nonzero": int(((d30.api_comments > 0) & (d30.yt_comments == d30.api_comments)).sum()),
                "lag_min": vn(d30.gio_chenh_phut.min(), 0), "lag_max": vn(d30.gio_chenh_phut.max(), 0),
                "t_first": tms.min().strftime("%H:%M"), "t_last": tms.max().strftime("%H:%M"), "t_date": tms.min().strftime("%d/%m/%Y"),
            }

    # ---- độ tin cậy
    rt = pd.read_csv(os.path.join(O, "reliability", "reliability_table.csv"), encoding="utf-8-sig")
    R["rel"] = [{"tc": r.tieu_chi, "cnt": ("–" if pd.isna(r.so_dem) else vn(r.so_dem)), "den": vn(r.mau_so),
                 "pct": ("–" if pd.isna(r.ty_le_pct) else vn(r.ty_le_pct, 2)), "how": r.cach_xu_ly} for r in rt.itertuples()]
    cs = pd.read_csv(os.path.join(O, "reliability", "collection_summary.csv"), encoding="utf-8-sig")
    md = pd.read_csv(os.path.join(O, "reliability", "missing_days.csv"), encoding="utf-8-sig", index_col=0).iloc[:, 0].to_dict()
    R["missing"] = md
    R["runs_by_day"] = cs.groupby("run_date").so_luot_chay.sum().to_dict()

    # ---- Q1
    qa = pd.read_csv(os.path.join(O, "q1", "q1_descriptive_table.csv"), encoding="utf-8-sig")
    def rows(nhom):
        out = []
        for r in qa[qa.nhom == nhom].itertuples():
            out.append([r.bien, vn(r.n), fmt_big(r.mean), fmt_big(r.median), fmt_big(r.sd), vn(r.cv, 2), vn(r.skew, 2), vn(r.kurtosis_excess, 2)])
        return out
    R["q1_all"], R["q1_short"], R["q1_long"] = rows("Tất cả"), rows("Video ngắn (<=60s)"), rows("Video dài (>60s)")
    S = pd.read_csv(os.path.join(O, "q1", "q1_summary_for_report.csv"), encoding="utf-8-sig", index_col=0)["value"]
    R["q1_sum"] = S.to_dict()
    dow = pd.read_csv(os.path.join(O, "q1", "q1_by_dow.csv"), encoding="utf-8-sig")
    R["q1_dow"] = [[r.dow_name, vn(r.n), vn(r.median_lv_adj, 3), vn(r.median_lv_within_channel, 3), vn(100 * r.median_like_rate, 2)] for r in dow.itertuples()]
    hr = pd.read_csv(os.path.join(O, "q1", "q1_by_hour.csv"), encoding="utf-8-sig")
    R["q1_hour_top"] = [[int(r.pub_hour), vn(r.n), vn(r.median_lv_adj, 3), vn(r.median_lv_within_channel, 3)] for r in hr.sort_values("median_lv_adj", ascending=False).head(3).itertuples()]
    R["q1_hour_bot"] = [[int(r.pub_hour), vn(r.n), vn(r.median_lv_adj, 3), vn(r.median_lv_within_channel, 3)] for r in hr.sort_values("median_lv_adj").head(3).itertuples()]
    R["q1_hour_within_max"] = [int(hr.loc[hr.median_lv_within_channel.idxmax(), "pub_hour"]), vn(hr.median_lv_within_channel.max(), 3)]
    R["q1_hour_within_min"] = [int(hr.loc[hr.median_lv_within_channel.idxmin(), "pub_hour"]), vn(hr.median_lv_within_channel.min(), 3)]
    R["q1_like_rate_range"] = [vn(100 * hr.median_like_rate.min(), 2), vn(100 * hr.median_like_rate.max(), 2)]
    cat = pd.read_csv(os.path.join(O, "q1", "q1_by_category.csv"), encoding="utf-8-sig").head(10)
    R["q1_cat"] = [[r.category_name, vn(r.n), vn(r.median_lv_adj, 3), vn(r.q1, 2), vn(r.q3, 2),
                    vn(r.median_lv_within_channel, 3)] for r in cat.itertuples()]
    mo = pd.read_csv(os.path.join(O, "q1", "q1_by_month.csv"), encoding="utf-8-sig")
    R["q1_month"] = {"first": mo.ym.iloc[0], "last": mo.ym.iloc[-1], "n_first": vn(mo.n.iloc[0]), "n_last_full": vn(int(mo[mo.ym == "2026-10"].n.iloc[0])) if (mo.ym == "2026-10").any() else "–",
                     "n_min": vn(mo.n.min()), "n_max": vn(mo.n.max())}
    sh, lg, al = qa[(qa.nhom == "Video ngắn (<=60s)")], qa[(qa.nhom == "Video dài (>60s)")], qa[qa.nhom == "Tất cả"]
    g_ = lambda d, b, c: float(d[d.bien == b][c].iloc[0])
    R["q1_like_mean_ratio"] = vn(g_(sh, "Lượt thích (gốc)", "mean") / g_(lg, "Lượt thích (gốc)", "mean"), 1)
    R["q1_views_mean_over_median"] = vn(g_(al, "Lượt xem (gốc)", "mean") / g_(al, "Lượt xem (gốc)", "median"), 1)
    R["q1_dow_ratio"] = vn(10 ** float(S["dow_range"]), 2)
    R["q1_dow_within_ratio"] = vn(10 ** float(S["dow_range_within_channel"]), 2)
    R["q1_dow_hi"] = [vn(dow.median_lv_adj.iloc[4:].min(), 3), vn(dow.median_lv_adj.iloc[4:].max(), 3)]        # Thứ Sáu–Chủ nhật
    R["q1_dow_lo"] = [vn(dow.median_lv_adj.iloc[:4].min(), 3), vn(dow.median_lv_adj.iloc[:4].max(), 3)]        # Thứ Hai–Thứ Năm
    R["q1_dow_hi_gt_lo"] = bool(dow.median_lv_adj.iloc[4:].min() > dow.median_lv_adj.iloc[:4].max() or dow.median_lv_adj.iloc[4:].mean() > dow.median_lv_adj.iloc[:4].mean())
    R["q1_dow_within_rng"] = [vn(dow.median_lv_within_channel.min(), 3), vn(dow.median_lv_within_channel.max(), 3)]
    R["q1_month_rng"] = [vn(mo.median_lv_adj.min(), 3), vn(mo.median_lv_adj.max(), 3)]
    hm = pd.read_csv(os.path.join(O, "q1", "q1_heatmap.csv"), encoding="utf-8-sig").pivot(index="pub_hour", columns="pub_dow", values="median_lv_adj")
    hr_rng, dw_rng = float(hm.mean(axis=1).max() - hm.mean(axis=1).min()), float(hm.mean(axis=0).max() - hm.mean(axis=0).min())
    R["q1_heat"] = {"hour_rng": vn(hr_rng, 3), "dow_rng": vn(dw_rng, 3), "hour_dominant": bool(hr_rng > 3 * dw_rng)}
    for k in ("cell_best", "cell_worst"):          # "4h Thứ Tư (1.031, n=100)" -> kiểu Việt Nam
        mt = re.match(r"(.*) \((-?[\d\.]+), n=(\d+)\)", str(R["q1_sum"][k]))
        if mt: R["q1_sum"][k] = f"{mt.group(1)} ({vn(float(mt.group(2)), 3)}, n = {vn(int(mt.group(3)))})"
    R["q1_between_share"] = vn(100 * float(S["between_channel_var_share"]), 1)
    R["q1_hour_range_ratio"] = vn(10 ** float(S["hour_range"]), 1)
    R["q1_within_ratio"] = vn(10 ** float(S["hour_range_within_channel"]), 2)
    R["q1_cat_ratio"] = vn(10 ** float(S["cat_range_top10"]), 0)
    R["q1_cat_within_range"] = vn(float(S["cat_range_top10_within_channel"]), 3)
    R["q1_cat_within_ratio"] = vn(10 ** float(S["cat_range_top10_within_channel"]), 2)

    # ---- Q3b
    t = pd.read_csv(os.path.join(O, "q3b", "q3b_or_table.csv"), encoding="utf-8-sig")
    fit = pd.read_csv(os.path.join(O, "q3b", "q3b_model_fit.csv"), encoding="utf-8-sig")
    info = pd.read_csv(os.path.join(O, "q3b", "q3b_design_info.csv"), encoding="utf-8-sig", index_col=0)["value"]
    m3 = pd.read_csv(os.path.join(O, "q3b", "q3b_M3_slot_sensitivity.csv"), encoding="utf-8-sig")
    def orci(o, lo, hi): return f"{vn(o, 2)} ({vn(lo, 2)}–{vn(hi, 2)})" if not pd.isna(o) else "không có trong M2"
    tt = t[t.term != "const"]
    R["q3b_rows"] = [[r.label, orci(r.OR_M1, r.OR_lo95_M1, r.OR_hi95_M1), pv(r.p_M1),
                      orci(r.OR_M2, r.OR_lo95_M2, r.OR_hi95_M2) if not pd.isna(r.OR_M2) else "–",
                      ("–" if pd.isna(r.OR_M2) else pv(r.p_M2)), vn(r.VIF, 2)] for r in tt.itertuples()]
    f1, f2, f3 = fit.iloc[0], fit.iloc[1], fit.iloc[2]
    R["q3b_fit"] = {"n": vn(f1.n), "n_pos": vn(f1.n_pos), "pct_pos": vn(f1.pct_pos, 2), "clusters": vn(f1.n_clusters),
                    "aic1": vn(f1.AIC, 1), "aic2": vn(f2.AIC, 1), "aic3": vn(f3.AIC, 1),
                    "mf1": vn(f1.McFadden_R2, 3), "mf2": vn(f2.McFadden_R2, 3), "mf3": vn(f3.McFadden_R2, 3),
                    "lr": vn(f2.LR_vs_M1, 0), "daic": vn(f2.AIC - f1.AIC, 1), "k1": int(f1.k_params), "k2": int(f2.k_params),
                    "removed_cat": str(info.get("n_removed_small_category", "0")), "ref": str(info.get("cat_reference", "")),
                    "removed_name": str(info.get("cat_small_merged_or_removed", ""))}
    def get(term, col): return float(t.loc[t.term == term, col].iloc[0])
    def j(term, a="M1"):
        return orci(get(term, f"OR_{a}"), get(term, f"OR_lo95_{a}"), get(term, f"OR_hi95_{a}"))
    R["q3b_key"] = {"subs": j("log_subs"), "age": j("channel_age_days"), "tv": j("total_videos_log"),
                    "dow": j("pub_dow"), "month": j("pub_month"), "hour": j("pub_hour"), "weekend": j("pub_is_weekend"),
                    "bracket": j("title_has_bracket"), "bracket_p": pv(get("title_has_bracket", "p_M1")),
                    "excl2": j("title_has_exclaim", "M2"), "emoji2": j("title_has_emoji", "M2"), "q2": j("title_has_question", "M2"),
                    "excl2_p": pv(get("title_has_exclaim", "p_M2")), "emoji2_p": pv(get("title_has_emoji", "p_M2")),
                    "m3_subs": orci(*[float(m3.loc[m3.term == "log_subs", c].iloc[0]) for c in ["OR", "OR_lo95", "OR_hi95"]]),
                    "vif_len": vn(get("title_len", "VIF"), 2), "vif_words": vn(get("title_words", "VIF"), 2),
                    "vif_max_other": vn(float(t[~t.term.isin(["title_len", "title_words", "const"])].VIF.max()), 2),
                    "autos": j("cat: Autos & Vehicles"), "comedy": j("cat: Comedy"), "edu": j("cat: Education"),
                    "sci": j("cat: Science & Tech"), "music": j("cat: Music"), "ent": j("cat: Entertainment")}
    lab_of = dict(zip(t.term, t.label))
    def lp(term, a):
        pp = pv(get(term, f"p_{a}"))
        return f"{lab_of[term]}: OR {orci(get(term, f'OR_{a}'), get(term, f'OR_lo95_{a}'), get(term, f'OR_hi95_{a}'))}, p {pp if pp.startswith('<') else '= ' + pp}"
    ttl = [x for x in tt.term if x.startswith("title_") and x != "title_len" and x != "title_words"]
    chan = {"log_subs", "channel_age_days", "total_videos_log"}
    cats = tt[tt.term.str.startswith("cat:")].copy()
    cats["short"] = cats.term.str.replace("cat: ", "", regex=False)
    ci_has1 = cats[(cats.OR_lo95_M1 <= 1) & (cats.OR_hi95_M1 >= 1)]
    ci_below1 = cats[cats.OR_hi95_M1 < 1]
    ci_above1 = cats[cats.OR_lo95_M1 > 1]
    R["q3b_dyn"] = {
        "nonchan_sig": [lp(x, "M1") for x in tt[(tt.p_M1 < 0.05) & ~tt.term.isin(chan) & ~tt.term.str.startswith("cat:")].term],
        "m2_title_sig": [lp(x, "M2") for x in ttl if get(x, "p_M2") < 0.05],
        "m2_title_near": [lp(x, "M2") for x in ttl if 0.05 <= get(x, "p_M2") < 0.10],
        "news": [j("cat: News & Politics", "M1"), j("cat: News & Politics", "M2")],
        "n_cat": int(tt.term.str.startswith("cat:").sum()),
        "n_cat_below1": int(((tt.term.str.startswith("cat:")) & (tt.OR_M1 < 1)).sum()),
        "cat_ci_has1": ci_has1.short.tolist(), "n_cat_ci_has1": int(len(ci_has1)),
        "cat_ci_below1": ci_below1.short.tolist(), "n_cat_ci_below1": int(len(ci_below1)),
        "cat_ci_above1": ci_above1.short.tolist(), "n_cat_ci_above1": int(len(ci_above1)),
        "n_title_ci_has1_m1": int(sum((get(x, "OR_lo95_M1") <= 1 <= get(x, "OR_hi95_M1")) for x in ttl)), "n_title": len(ttl),
    }
    n_sig = int((tt.p_M1 < 0.05).sum()); R["q3b_nsig"] = {"n_terms": len(tt), "n_sig": n_sig,
                                                         "n_sig_nonchan_noncat": int(((tt.p_M1 < 0.05) & ~tt.term.isin(["log_subs", "channel_age_days", "total_videos_log"]) & ~tt.term.str.startswith("cat:")).sum())}

    # ---- trích từ điển
    from gen_data_dictionary import VM
    VM = dict(VM); VM["lv_adj*"] = ("Log10 lượt xem đã trừ trung bình nhóm tuổi (biến dẫn xuất, không nằm trong CSV)", "log10(lượt)", "log_views − trung bình log_views của age_b trên H (prep.py)", "Không (chỉ tính cho video thuộc H)")
    R["dict_rows"] = [[c, *VM[c]] for c in ["views", "likes", "comments", "age_days_last", "lv_adj*", "log_views", "pub_hour", "pub_dow", "pub_slot", "is_short_60", "like_rate", "subscribers", "log_subs", "ever_trending"]]
    R["dict_cols"] = ["views", "likes", "comments", "age_days_last", "lv_adj*", "log_views", "pub_hour", "pub_dow", "pub_slot",
                      "is_short_60", "like_rate", "subscribers", "log_subs", "ever_trending", "is_last_of_day"]
    json.dump(R, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Đã ghi", os.path.abspath(OUT_JSON))


if __name__ == "__main__":
    main()
