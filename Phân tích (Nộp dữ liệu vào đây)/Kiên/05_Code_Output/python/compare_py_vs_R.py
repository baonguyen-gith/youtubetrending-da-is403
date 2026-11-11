"""Đối chiếu theo khóa và giá trị công bố ở ba chữ số sau dấu thập phân."""
import os
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(os.environ.get("OUT_ROOT", "outputs"))
PAIRS = ["dataset","factor","group1","group2"]
KEYS = {
    "so_kiem_tra": [], "q2a_results": ["dataset"], "q2a_cluster": ["dataset","model"],
    "q2a_descriptives": ["pub_is_weekend"], "q2b_anova_results": ["dataset","factor"],
    "q2b_group_means_full": ["dataset","factor","group"], "q2b_group_means": ["factor","group"],
    "q2b_gameshowell_all": PAIRS, "q2b_gameshowell_significant": PAIRS,
    "q2b_dropped_groups": ["dataset","factor","group"], "q3a_coefficients": ["term"],
    "q3a_model": [], "q3a_group_contribution": ["nhom"], "q3a_vif": ["term"],
    "q3a_vif_columns": ["column"], "q3a_r2_age_only": [],
}

def align(a,b,keys):
    if not keys:
        if len(a)!=1 or len(b)!=1:
            raise ValueError("Bảng tổng hợp phải có đúng một dòng")
        return a,b
    a=a.set_index(keys,verify_integrity=True).sort_index()
    b=b.set_index(keys,verify_integrity=True).sort_index()
    if not a.index.equals(b.index):
        raise ValueError(f"Khóa không khớp: {a.index.symmetric_difference(b.index).tolist()[:5]}")
    return a,b

def main():
    summary=[]
    for name,keys in KEYS.items():
        folder=ROOT/("prep" if name=="so_kiem_tra" else name.split("_")[0])
        py=pd.read_csv(folder/f"{name}_python.csv")
        other=folder/(f"{name}.csv" if name=="q2b_group_means" else f"{name}_R.csv")
        r=pd.read_csv(other)
        if name.startswith("q2b_gameshowell") and "df" not in r:
            py=py.drop(columns="df") # rstatix không xuất df từng cặp
        if set(py)!=set(r):
            raise ValueError(f"{name}: cột khác nhau {set(py)^set(r)}")
        a,b=align(py,r,keys)
        for col in a:
            x,y=a[col],b[col]
            missing=x.isna()^y.isna()
            keep=x.notna()&y.notna()
            u,v=x[keep],y[keep]
            if pd.api.types.is_numeric_dtype(u) and not pd.api.types.is_bool_dtype(u):
                delta=(u-v).abs();same=np.round(u,3).eq(np.round(v,3))
                mx=delta.max() if len(delta) else 0
            else:
                same=u.astype(str).eq(v.astype(str));mx=None
            bad=int(missing.sum()+(~same).sum())
            summary.append(dict(bang=name,cot=col,so_dong=len(a),lech=bad,max_abs=mx))
    s=pd.DataFrame(summary);s.to_csv(ROOT/'doi_chieu_chi_tiet.csv',index=False,encoding='utf-8-sig')
    lines=['# Đối chiếu Python và R','', 'Ghép theo khóa, so số sau khi làm tròn ba chữ số thập phân; văn bản, cờ logic và vị trí thiếu phải khớp. df từng cặp Games–Howell chỉ có trong CSV Python.','', '| Bảng | Dòng | Cột so | Ô lệch |','|---|---:|---:|---:|']
    for name,g in s.groupby('bang',sort=False):
        lines.append(f'| {name} | {g.so_dong.iloc[0]} | {len(g)} | {g.lech.sum()} |')
    lines+=['','Chi tiết từng cột nằm trong doi_chieu_chi_tiet.csv. Hai bảng hậu kiểm dùng cùng cặp theo khóa; cờ có ý nghĩa được so riêng.']
    (ROOT/'note_python_vs_R.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if s.lech.sum():
        print(s[s.lech>0].to_string(index=False))
        raise SystemExit("Có sai lệch cần kiểm tra.")
    print(f"Đạt: {len(KEYS)} bảng, {len(s)} cột được đối chiếu.")
if __name__=="__main__":
    main()
