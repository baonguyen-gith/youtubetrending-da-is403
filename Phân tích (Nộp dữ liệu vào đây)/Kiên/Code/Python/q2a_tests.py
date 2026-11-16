"""Welch t-test, pooled SD Cohen's d, Levene(median), MWU and no-short sensitivity."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analysis_common import save_csv,save_json

def evaluate(h,subset):
    a=h.loc[h.pub_is_weekend,'lv_adj'].dropna().to_numpy(dtype=float)
    b=h.loc[~h.pub_is_weekend,'lv_adj'].dropna().to_numpy(dtype=float)
    if min(len(a),len(b))<3: raise ValueError('Insufficient samples for Welch t-test')
    na,nb=len(a),len(b)
    va,vb=a.var(ddof=1),b.var(ddof=1)
    ma,mb=a.mean(),b.mean()
    se=np.sqrt(va/na+vb/nb)
    df=(va/na+vb/nb)**2/((va/na)**2/(na-1)+(vb/nb)**2/(nb-1))
    t,p=stats.ttest_ind(a,b,equal_var=False)
    diff=ma-mb
    ci=diff+np.array([-1,1])*stats.t.ppf(.975,df)*se
    pooled=np.sqrt(((na-1)*va+(nb-1)*vb)/(na+nb-2))
    d=diff/pooled
    lev=stats.levene(a,b,center='median')
    mwu=stats.mannwhitneyu(a,b,alternative='two-sided',method='asymptotic')
    return {'subset':subset,'n_weekend':na,'n_weekday':nb,'mean_weekend':ma,'mean_weekday':mb,
       'sd_weekend':np.sqrt(va),'sd_weekday':np.sqrt(vb),'difference_weekend_minus_weekday':diff,
       't_welch':t,'df_welch':df,'p_welch':p,'ci95_low':ci[0],'ci95_high':ci[1],
       'cohens_d_pooled':d,'levene_F':lev.statistic,'levene_p':lev.pvalue,
       'mann_whitney_U':mwu.statistic,'mann_whitney_p':mwu.pvalue}

def run(h,out_dir):
    p=Path(out_dir)/'q2a';p.mkdir(parents=True,exist_ok=True)
    rows=[evaluate(h,'H'),evaluate(h.loc[~h.is_short_60],'H_no_short_60')]
    save_csv(pd.DataFrame(rows),p/'q2a_tests.csv')
    # Deterministic QQ subsamples, stratified by group and no random state ambiguity.
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,(key,label) in zip(axes,[(True,'Cuối tuần'),(False,'Ngày thường')]):
        x=h.loc[h.pub_is_weekend==key,'lv_adj'].dropna().to_numpy()
        rng=np.random.default_rng(42);x=rng.choice(x,min(5000,len(x)),replace=False)
        stats.probplot(x,dist='norm',plot=ax);ax.set_title('QQ-plot: '+label)
    fig.tight_layout();fig.savefig(p/'q2a_qqplot.png',dpi=170);plt.close(fig)
    save_json({'assumptions':'Welch không giả định phương sai bằng nhau; Levene median đánh giá đồng nhất phương sai. MWU không đo chênh lệch trung bình.',
      'cohens_d':'SD gộp theo (n-1), không phải Hedges g; bản R dùng cùng định nghĩa.',
      'contrast':'Weekend - weekday','confidence':.95,'qq_seed':42},p/'method.json')
    print('Q2a:',rows[0])
    return rows

if __name__=='__main__':
    from analysis_common import get_data,make_H
    p=argparse.ArgumentParser();p.add_argument('--data-dir',required=True);p.add_argument('--output-dir',required=True)
    a=p.parse_args();run(make_H(get_data(a.data_dir)),a.output_dir)
