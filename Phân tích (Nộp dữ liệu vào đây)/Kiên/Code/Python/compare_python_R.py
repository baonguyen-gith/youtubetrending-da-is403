"""Compare actual (not imagined) Python and R execution outputs. Nonzero exit on mismatch.
Usage: python compare_python_R.py --output-dir ../../04_Outputs/data_final
"""
from pathlib import Path
import argparse,json,sys
import numpy as np
import pandas as pd
from analysis_common import save_json

CHECKS=[
  ('prep/bo_6_so.csv','prep/bo_6_so_R.csv',['value'], 'metric'),
  ('q2a/q2a_tests.csv','q2a/q2a_tests_R.csv',
    ['n_weekend','n_weekday','mean_weekend','mean_weekday','difference_weekend_minus_weekday','t_welch','df_welch','p_welch','cohens_d_pooled','ci95_low','ci95_high','levene_F','levene_p'], 'subset'),
  ('q2b/q2b_anova.csv','q2b/q2b_anova_R.csv',
    ['n_total','k','anova_F','anova_p','welch_F','welch_df2','welch_p','levene_F','levene_p','kruskal_H','kruskal_p','eta_sq_classic'], ['subset','factor']),
  ('q3a/q3a_coefficients.csv','q3a/q3a_coefficients_R.csv',
    ['coefficient','se_cluster','t_cluster','p_cluster','ci95_low','ci95_high','beta_standardized'], 'sequence'),
  ('q3a/q3a_delta_R2.csv','q3a/q3a_delta_R2_R.csv',
    ['R2_full','R2_without_group','delta_R2'], 'group')]

def compare(o):
    details=[];failures=[]
    for left,right,cols,index in CHECKS:
        l=o/left;r=o/right
        if not r.exists():
            details.append({'python_file':left,'R_file':right,'status':'R_NOT_RUN'})
            continue
        a=pd.read_csv(l);b=pd.read_csv(r)
        if index=='sequence':
            a=a.reset_index(drop=True);b=b.reset_index(drop=True)
        else:
            on=index if isinstance(index,list) else [index]
            a=a.sort_values(on).reset_index(drop=True)
            b=b.sort_values(on).reset_index(drop=True)
            if a[on].astype(str).values.tolist()!=b[on].astype(str).values.tolist():
                failures.append(f'Mismatch group keys {left}');continue
        if len(a)!=len(b):failures.append(f'Mismatch row count {left}');continue
        for col in cols:
            if col not in a or col not in b:
                failures.append(f'Missing column {col} in {right}');continue
            x=pd.to_numeric(a[col],errors='coerce').to_numpy(float)
            y=pd.to_numeric(b[col],errors='coerce').to_numpy(float)
            # Demand matching rounded 3 decimal places, but compare small p-values using abs tolerance.
            same=np.isclose(x,y,rtol=1e-4,atol=5e-4,equal_nan=True)
            if not bool(same.all()):
                bad=np.where(~same)[0].tolist()[:5]
                failures.append(f'{left} {col}: rows {bad}; Python {x[bad]}, R {y[bad]}')
        details.append({'python_file':left,'R_file':right,'status':'COMPARED'})
    state='NOT_RUN' if any(z['status']=='R_NOT_RUN' for z in details) else ('FAIL' if failures else 'PASS')
    save_json({'status':state,'details':details,'failures':failures,
      'note':'PASS only when all actual R output files exist and each comparison matches. Do not interpret NOT_RUN as PASS.'},o/'python_r_comparison.json')
    print('Comparison:',state)
    for fail in failures:print('ERROR:',fail)
    if failures:return 1
    return 0 if state=='PASS' else 2

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',required=True)
    a=ap.parse_args();sys.exit(compare(Path(a.output_dir)))
