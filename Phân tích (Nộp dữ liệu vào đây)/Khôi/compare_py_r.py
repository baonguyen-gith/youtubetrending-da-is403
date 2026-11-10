"""compare_py_r.py - đối chiếu kết quả Python vs R (K8). Dùng: python compare_py_r.py"""
import pandas as pd, numpy as np
a = pd.read_csv("outputs/q2d/q2d_results.csv"); b = pd.read_csv("outputs/q2d_R/q2d_results.csv")
m = a.merge(b, on=["version", "group"], suffixes=("_py", "_R"))
print(f"Q2d: {len(a)} dòng Python, {len(b)} dòng R, ghép được {len(m)}")
for c in ["n_period", "n_control", "diff", "ci95_low", "ci95_high", "t", "df", "p", "p_holm", "cohens_d"]:
    x, y = m[c + "_py"], m[c + "_R"]
    print(f"  {c:10s} lệch tuyệt đối lớn nhất = {np.nanmax(np.abs(x - y)):.2e}")
