"""Multiple OLS with channel-clustered covariance; full diagnostics, VIF and drop-one-group R².
Design matrix is explicitly defined to make R/Python comparisons unambiguous.
"""
import argparse
from pathlib import Path
import re
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analysis_common import save_csv,save_json

BINARY=['title_has_question','title_has_exclaim','title_has_digit','title_has_emoji','pub_is_weekend','is_short_60']
CONTENT=['log_duration','tags_count','title_len','title_upper_ratio','title_has_question','title_has_exclaim','title_has_digit','title_has_emoji','is_short_60']
NUMERIC=['log_age','log_subs','log_duration','tags_count','title_len','title_upper_ratio']+BINARY

def build_design(h,omit_short=False):
    cols=['log_views','age_days_last','log_subs','duration_sec','tags_count','title_len','title_upper_ratio','channel_id','pub_slot','category_name']+BINARY
    d=h[cols].copy()
    for c in ['log_views','age_days_last','log_subs','duration_sec','tags_count','title_len','title_upper_ratio']:
        d[c]=pd.to_numeric(d[c],errors='coerce')
    for c in BINARY:d[c]=d[c].astype(float)
    d=d.loc[d.age_days_last.gt(0)&d.duration_sec.gt(0)&d.channel_id.notna()].dropna()
    d['log_age']=np.log10(d.age_days_last)
    d['log_duration']=np.log10(d.duration_sec)
    base=['log_age','log_subs','log_duration','tags_count','title_len','title_upper_ratio']+BINARY
    if omit_short:base.remove('is_short_60')
    x=d[base].copy().astype(float)
    for categorical in ['pub_slot','category_name']:
        counts=d[categorical].astype(str).value_counts()
        baseline=sorted(counts[counts==counts.max()].index)[0]
        levels=[baseline]+sorted(v for v in counts.index if v!=baseline)
        d[categorical]=pd.Categorical(d[categorical],categories=levels,ordered=True)
        z=pd.get_dummies(d[categorical],prefix=categorical, prefix_sep='__',drop_first=True,dtype=float)
        x=pd.concat([x,z],axis=1)
    return d,x

def vif_values(x):
    # All explanatory columns, no intercept. Invert Pearson correlation matrix.
    std=x.std(ddof=1)
    if (std<=0).any():raise ValueError('Constant explanatory variable; cannot compute VIF.')
    z=(x-x.mean())/std
    corr=(z.T@z).to_numpy()/(len(z)-1)
    try:values=np.diag(np.linalg.inv(corr))
    except np.linalg.LinAlgError:values=np.diag(np.linalg.pinv(corr))
    return pd.DataFrame({'term':list(x),'VIF':values}).sort_values('VIF',ascending=False)

def fit(d,x,cluster=True):
    XX=sm.add_constant(x,has_constant='add')
    model=sm.OLS(d['log_views'].to_numpy(dtype=float),XX.to_numpy(dtype=float))
    if cluster:
        f=model.fit(cov_type='cluster',cov_kwds={'groups':d.channel_id.astype(str).to_numpy(),
            'use_correction':True,'df_correction':True},use_t=True)
    else: f=model.fit()
    return f,XX.columns

def r2_of(d,x):
    # Faster and deterministic, identical fitted values to OLS with intercept.
    m=sm.OLS(d.log_views.to_numpy(float),sm.add_constant(x,has_constant='add').to_numpy(float)).fit()
    return float(m.rsquared)

def run(h,out_dir):
    p=Path(out_dir)/'q3a';p.mkdir(parents=True,exist_ok=True)
    d,x=build_design(h)
    initial_vif=vif_values(x)
    save_csv(initial_vif,p/'q3a_vif_before.csv')
    removed=[]
    # Contract: if VIF > 10, first remove is_short_60 because it strongly overlaps duration.
    # If another regressor/factor still violates VIF>10, remove the named predictor or the entire factor.
    for step in range(20):
        vv=vif_values(x)
        offending=vv.loc[vv.VIF>10]
        if offending.empty:break
        if 'is_short_60' in x and x['is_short_60'].name in set(offending.term):
            key='is_short_60'; drop=[key]
        else:
            key=offending.iloc[0]['term']
            if key.startswith('category_name__'):drop=[c for c in x if c.startswith('category_name__')];key='category_name (factor)'
            elif key.startswith('pub_slot__'):drop=[c for c in x if c.startswith('pub_slot__')];key='pub_slot (factor)'
            else:drop=[key]
        if 'log_age' in drop: raise ValueError('Age control has VIF>10; report and inspect source, do not remove mandatory control.')
        removed.append({'step':step+1,'variable':key,'trigger_vif':float(offending.iloc[0].VIF),'dropped_terms':';'.join(drop)})
        x=x.drop(columns=drop)
    final_vif=vif_values(x);save_csv(final_vif,p/'q3a_vif.csv')
    save_csv(pd.DataFrame(removed,columns=['step','variable','trigger_vif','dropped_terms']),p/'q3a_removed_vif.csv')
    f,terms=fit(d,x)
    betas=f.params
    T=pd.DataFrame({'term':terms,'coefficient':betas,'se_cluster':f.bse,'t_cluster':f.tvalues,
      'p_cluster':f.pvalues,'ci95_low':f.conf_int()[:,0],'ci95_high':f.conf_int()[:,1]})
    # standardized slope for scalar and 0/1 dummy terms only; categorical indicators are not global group effects.
    sd_y=d.log_views.std(ddof=1)
    T['beta_standardized']=T.apply(lambda row:float(row.coefficient*x[row.term].std(ddof=1)/sd_y) if row.term in x else np.nan,axis=1)
    save_csv(T,p/'q3a_coefficients.csv')
    full=float(f.rsquared)
    groups={'channel':['log_subs'],
      'content':[c for c in CONTENT if c in x],
      'timing':['pub_is_weekend']+[c for c in x if c.startswith('pub_slot__')],
      'category':[c for c in x if c.startswith('category_name__')]}
    contributions=[]
    for name,candidates in groups.items():
        dropped=[c for c in candidates if c in x]
        reduced=r2_of(d,x.drop(columns=dropped)) if dropped else full
        contributions.append({'group':name,'n_terms':len(dropped),'R2_full':full,'R2_without_group':reduced,
          'delta_R2':full-reduced,'removed_columns':';'.join(dropped)})
    save_csv(pd.DataFrame(contributions),p/'q3a_delta_R2.csv')
    fitted=f.fittedvalues; residual=f.resid
    stats_summary={'n_used':len(d),'n_channels':int(d.channel_id.nunique()),'n_parameters':len(terms),
      'R2':full,'adjusted_R2':float(f.rsquared_adj),'RMSE':float(np.sqrt(np.mean(residual**2))),
      'df_cluster':int(d.channel_id.nunique()-1),'removed_due_to_VIF_gt10':removed,
      'factor_baselines':{'pub_slot':str(d.pub_slot.cat.categories[0]),
         'category_name':str(d.category_name.cat.categories[0])},
      'inference':'cluster CR1 finite sample correction n_clusters/(n_clusters-1)*(n-1)/(n-k); t reference df G-1',
      'vif_gt5_remaining':final_vif.loc[final_vif.VIF>5].term.tolist(),
      'important':'Association, not causation; log_subs measured at data collection, not publication.'}
    save_json(stats_summary,p/'q3a_summary.json')
    fig,ax=plt.subplots(figsize=(7,4.5));rng=np.random.default_rng(42)
    ids=rng.choice(len(residual),min(len(residual),10000),replace=False)
    ax.scatter(fitted[ids],residual[ids],s=2,alpha=.16)
    ax.axhline(0,color='red',linewidth=1)
    ax.set(xlabel='Fitted log10(views)',ylabel='Residual',title='Q3a: phần dư theo giá trị dự báo (mẫu tối đa 10k)')
    fig.tight_layout();fig.savefig(p/'q3a_residual_vs_fitted.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,5));zz=residual[rng.choice(len(residual),min(len(residual),6000),replace=False)]
    stats.probplot(zz,dist='norm',plot=ax);ax.set_title('Q3a: QQ plot phần dư (mẫu tối đa 6k)')
    fig.tight_layout();fig.savefig(p/'q3a_residual_qq.png',dpi=180);plt.close(fig)
    c=pd.DataFrame(contributions).sort_values('delta_R2')
    fig,ax=plt.subplots(figsize=(7,4));ax.barh(c.group,c.delta_R2,color='#32759b')
    ax.set_xlabel('Giảm R² khi bỏ nhóm');ax.set_title('Q3a: đóng góp giải thích bổ sung')
    fig.tight_layout();fig.savefig(p/'q3a_delta_R2.png',dpi=180);plt.close(fig)
    print('Q3a:',stats_summary)
    print(pd.DataFrame(contributions)[['group','delta_R2']].to_string(index=False))
    return stats_summary

if __name__=='__main__':
    from analysis_common import get_data,make_H
    ap=argparse.ArgumentParser();ap.add_argument('--data-dir',required=True);ap.add_argument('--output-dir',required=True)
    a=ap.parse_args();run(make_H(get_data(a.data_dir)),a.output_dir)
