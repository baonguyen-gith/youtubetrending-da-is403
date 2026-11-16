"""Đối chiếu Q4: Python vs R (K8). Dùng: python compare_py_r_q4.py [q4_py_dir] [q4_R_dir]"""
import sys, pandas as pd, numpy as np
A, B = (sys.argv[1] if len(sys.argv) > 1 else "outputs/q4"), (sys.argv[2] if len(sys.argv) > 2 else "outputs/q4_R")
a = pd.read_csv(f"{A}/q4_model_comparison.csv"); b = pd.read_csv(f"{B}/q4_model_comparison.csv")
m = a.merge(b, on=["series", "model"], suffixes=("_py", "_R"))
cols = ["series", "model", "order_py", "order_R", "aic_py", "aic_R", "mae_test_py", "mae_test_R", "ljungbox_p_py", "ljungbox_p_R"]
pd.set_option("display.width", 220); print(m[cols].round(4).to_string(index=False))
print("\nCùng bậc:", int((m.order_py == m.order_R).sum()), "/", len(m), "| lệch AIC lớn nhất:", np.nanmax(np.abs(m.aic_py - m.aic_R)).round(3),
      "| lệch MAE test lớn nhất:", np.nanmax(np.abs(m.mae_test_py - m.mae_test_R)).round(4))
print("Mô hình chọn theo AIC:", dict(zip(m.loc[m.chon_theo_AIC_py, "series"], m.loc[m.chon_theo_AIC_py, "model"])), "(Py) vs", dict(zip(m.loc[m.chon_theo_AIC_R, "series"], m.loc[m.chon_theo_AIC_R, "model"])), "(R)")
