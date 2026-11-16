# -*- coding: utf-8 -*-
"""compare_py_r.py - Đối chiếu số Python và R (tiêu chí "khớp 3 chữ số" của B4, B5).
Chạy SAU KHI đã chạy cả hai bản (đứng trong thư mục python/):   python compare_py_r.py
  Q1 : outputs/q1/{q1_descriptive_table,q1_by_hour,q1_by_dow}.csv  vs  outputs/q1_R/ (cùng tên)
  Q3b: outputs/q3b/q3b_or_table.csv  vs  outputs/q3b_R/q3b_coef_M1_R.csv, q3b_coef_M2_R.csv
Ghép hai bảng theo KHÓA (không theo thứ tự dòng); chỉ so các cột số; in rõ dòng nào lệch.
"""
import os
import re
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")
TOL_ABS, TOL_REL = 5e-4, 5e-4      # "khớp 3 chữ số"
all_ok = True


def cmp(a, b, name, labels=None, tol_abs=TOL_ABS, tol_rel=TOL_REL):
    """So hai dãy số; True nếu mọi cặp khớp (hai NaN cùng vị trí coi là khớp)."""
    global all_ok
    a = pd.to_numeric(pd.Series(a).reset_index(drop=True), errors="coerce").to_numpy(float)
    b = pd.to_numeric(pd.Series(b).reset_index(drop=True), errors="coerce").to_numpy(float)
    both_nan = np.isnan(a) & np.isnan(b)
    d = np.abs(a - b)
    rel = d / np.maximum(np.abs(b), 1e-12)
    bad = ~both_nan & ~((d <= tol_abs) | (rel <= tol_rel))      # NaN một bên cũng tính là lệch
    ok = not bad.any()
    all_ok &= ok
    worst = np.nanmax(np.where(both_nan, 0, d)) if len(d) else 0
    print(f"{'KHỚP ' if ok else 'LỆCH '} {name}: sai khác tuyệt đối lớn nhất = {worst:.6g}")
    if not ok and labels is not None:
        for i in np.where(bad)[0][:5]:
            print(f"      - {labels[i]}: Python = {a[i]:.6g} | R = {b[i]:.6g}")
    return ok


def merge_compare(fname, keys):
    global all_ok
    p, r = os.path.join(B, "q1", fname), os.path.join(B, "q1_R", fname)
    if not (os.path.exists(p) and os.path.exists(r)):
        print("Thiếu", fname, "(chạy bản R chưa?)")
        return
    a, b = pd.read_csv(p, encoding="utf-8-sig"), pd.read_csv(r, encoding="utf-8-sig")
    j = a.merge(b, on=keys, how="outer", suffixes=("_py", "_R"), indicator=True)
    if (j["_merge"] != "both").any():
        print(f"LỆCH  {fname}: {int((j['_merge'] != 'both').sum())} dòng chỉ có ở một bên (khác khóa {keys})")
        all_ok = False
    j = j[j["_merge"] == "both"]
    lab = j[keys].astype(str).agg(" | ".join, axis=1).tolist()
    for c in [c[:-3] for c in j.columns if c.endswith("_py")]:
        x, y = j[c + "_py"], j[c + "_R"]
        if is_numeric_dtype(x) and is_numeric_dtype(y):          # bỏ qua cột chữ (vd dow_name)
            cmp(x, y, f"{fname}:{c}", lab)


def norm(t):  # tên biến Python -> dạng make.names của R
    t = "(Intercept)" if t == "const" else t
    return re.sub(r"[^0-9A-Za-z_.()]", ".", t)


merge_compare("q1_descriptive_table.csv", ["nhom", "bien"])
merge_compare("q1_by_hour.csv", ["pub_hour"])
merge_compare("q1_by_dow.csv", ["pub_dow"])

pm = os.path.join(B, "q3b", "q3b_or_table.csv")
if os.path.exists(pm) and os.path.exists(os.path.join(B, "q3b_R", "q3b_coef_M1_R.csv")):
    a = pd.read_csv(pm, encoding="utf-8-sig")
    a["k"] = a["term"].map(norm)
    for tag in ["M1", "M2"]:
        r = pd.read_csv(os.path.join(B, "q3b_R", f"q3b_coef_{tag}_R.csv"), encoding="utf-8-sig").rename(columns={"term": "k"})
        j = a.merge(r, on="k", how="inner").dropna(subset=[f"OR_{tag}"])
        n_a = int(a[f"OR_{tag}"].notna().sum())
        if len(j) != n_a:
            print(f"LỆCH  Logit {tag}: Python có {n_a} hệ số, ghép được {len(j)} với R (kiểm tra tên biến / nhóm gốc thể loại)")
            all_ok = False
        lab = j["k"].tolist()
        cmp(j[f"OR_{tag}"], j["OR"], f"Logit {tag}: OR (3 chữ số)", lab)
        cmp(j[f"OR_lo95_{tag}"], j["OR_lo95"], f"Logit {tag}: CI dưới (cho phép lệch <= 0,01)", lab, tol_abs=1e-2, tol_rel=1e-2)
        cmp(j[f"OR_hi95_{tag}"], j["OR_hi95"], f"Logit {tag}: CI trên (cho phép lệch <= 0,01)", lab, tol_abs=1e-2, tol_rel=1e-2)
else:
    print("Chưa có kết quả R của Q3b (outputs/q3b_R/q3b_coef_M1_R.csv).")

print("\nKẾT LUẬN:", "TẤT CẢ KHỚP" if all_ok else "CÓ CHỖ LỆCH - xem các dòng LỆCH ở trên")
