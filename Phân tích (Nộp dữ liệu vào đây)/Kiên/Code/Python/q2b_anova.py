"""One-way Welch/standard ANOVA, median Levene, Kruskal, Games-Howell.
Pairwise p-values: studentized_range(q, k groups, Welch pair df), no Tukey assumption.
"""
import argparse
from itertools import combinations
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analysis_common import save_csv,save_json

def welch_anova(ns, means, vars_):
    n=np.asarray(ns,float); m=np.asarray(means,float); v=np.asarray(vars_,float)
    k=len(n); w=n/v; W=w.sum(); wm=np.dot(w,m)/W
    s=np.sum((1-w/W)**2/(n-1))
    F=(np.dot(w,(m-wm)**2)/(k-1))/(1+2*(k-2)*s/(k*k-1))
    df2=(k*k-1)/(3*s)
    return float(F), float(df2), float(stats.f.sf(F,k-1,df2))

def games_howell(g,k):
    result=[]
    for a,b in combinations(g.index,2):
        x,y=g.loc[a],g.loc[b]
        n1,n2=int(x.n),int(y.n)
        v1,v2=x["var"],y["var"]
        se2=v1/n1+v2/n2
        df=se2**2/((v1/n1)**2/(n1-1)+(v2/n2)**2/(n2-1))
        diff=x['mean']-y['mean']
        q=abs(diff)/np.sqrt(se2/2)
        p=float(stats.studentized_range.sf(q,k,df))
        crit=float(stats.studentized_range.ppf(.95,k,df))
        half=crit*np.sqrt(se2/2)
        result.append({'group1':a,'group2':b,'n1':n1,'n2':n2,'diff_mean':diff,
           'df_welch_pair':df,'q':q,'p_GH':p,'ci95_low':diff-half,'ci95_high':diff+half,'significant_0_05':p<.05})
    return pd.DataFrame(result)

def one_factor(h,col,subset):
    groups={str(k):grp['lv_adj'].dropna().to_numpy(dtype=float)
       for k,grp in h.groupby(col,dropna=True) if grp.lv_adj.notna().sum()>=2}
    if len(groups)<2:raise ValueError('Not enough groups')
    names=sorted(groups)
    arrays=[groups[x] for x in names]
    ns=np.array([len(x) for x in arrays]);means=np.array([x.mean() for x in arrays]);vs=np.array([x.var(ddof=1) for x in arrays]);k=len(names)
    classic=stats.f_oneway(*arrays,equal_var=True)
    # Same Welch formula as one-way Welch ANOVA (SciPy equal_var=False).
    wf,df2,wp=welch_anova(ns,means,vs)
    lev=stats.levene(*arrays,center='median')
    kw=stats.kruskal(*arrays)
    mu=np.dot(ns,means)/ns.sum()
    SSB=np.sum(ns*(means-mu)**2)
    SSW=np.sum((ns-1)*vs)
    eta=SSB/(SSB+SSW)
    details=pd.DataFrame({'subset':subset,'factor':col,'group':names,'n':ns,'mean':means,
       'sd':np.sqrt(vs),'se':np.sqrt(vs/ns),'ci95_low':means-stats.t.ppf(.975,ns-1)*np.sqrt(vs/ns),
       'ci95_high':means+stats.t.ppf(.975,ns-1)*np.sqrt(vs/ns)})
    g=pd.DataFrame({'n':ns,'mean':means,'var':vs},index=names)
    GH=games_howell(g,k)
    GH.insert(0,'subset',subset);GH.insert(1,'factor',col)
    result={'subset':subset,'factor':col,'n_total':int(ns.sum()),'k':k,
       'min_group_n':int(ns.min()),'anova_F':float(classic.statistic),'anova_df1':k-1,
       'anova_df2':int(ns.sum()-k),'anova_p':float(classic.pvalue),
       'welch_F':wf,'welch_df1':k-1,'welch_df2':df2,'welch_p':wp,
       'levene_F':float(lev.statistic),'levene_p':float(lev.pvalue),
       'kruskal_H':float(kw.statistic),'kruskal_p':float(kw.pvalue),
       'eta_sq_classic':float(eta),'decision_primary':'Welch' if lev.pvalue<.05 else 'classic_ANOVA',
       'games_howell_pairs':len(GH),'games_howell_significant_pairs':int(GH.significant_0_05.sum())}
    return result,details,GH

def plot_means(details,factor,path):
    a=details.query('factor == @factor and subset == "H"').sort_values('mean')
    fig,ax=plt.subplots(figsize=(11,max(4,len(a)*.44+1)))
    x=a['mean'].values; err=np.vstack([x-a.ci95_low.values,a.ci95_high.values-x])
    ax.errorbar(x,range(len(a)),xerr=err,fmt='o',capsize=3,color='#1f567b',ecolor='#6795aa')
    ax.set_yticks(range(len(a)),[f'{n} (n={cnt:,})' for n,cnt in zip(a.group,a.n)],fontsize=9)
    ax.axvline(0,linestyle='--',linewidth=1,color='gray')
    ax.set_xlabel('Trung bình lv_adj và CI 95% (video, không hiệu chỉnh theo kênh)')
    ax.set_title('Q2b — '+factor+' | dữ liệu chính thức')
    fig.tight_layout();fig.savefig(path,dpi=160);plt.close(fig)

def run(h,out_dir):
    p=Path(out_dir)/'q2b';p.mkdir(parents=True,exist_ok=True)
    rows=[];means=[];pairs=[]
    for subset,x in [('H',h),('H_no_short_60',h.loc[~h.is_short_60])]:
        for col in ['pub_slot','category_name']:
            r,m,g=one_factor(x,col,subset);rows.append(r);means.append(m);pairs.append(g)
    out=pd.DataFrame(rows); detail=pd.concat(means,ignore_index=True);GH=pd.concat(pairs,ignore_index=True)
    save_csv(out,p/'q2b_anova.csv');save_csv(detail,p/'q2b_group_means.csv')
    save_csv(GH,p/'q2b_games_howell.csv')
    save_csv(GH.loc[GH.significant_0_05],p/'q2b_significant_pairs.csv')
    for factor,slug in [('pub_slot','khung_gio'),('category_name','the_loai')]:
        plot_means(detail,factor,p/f'q2b_{slug}.png')
    save_json({'anova':'Classic F and Welch F are both reported. Primary inference Welch if median Levene p<0.05.',
        'eta':'Eta-square is classical SSB/SST; it is not Welch-specific.',
        'posthoc':'Games-Howell uses q=abs(mean1-mean2)/sqrt(0.5*(s1²/n1+s2²/n2)); family-wise p from studentized range.',
        'small_groups':'Groups with n>=2 retained (source requirement). Interpret very small categories cautiously; do not generalize.'},p/'method.json')
    print(out[['subset','factor','n_total','k','welch_F','welch_p','eta_sq_classic']].to_string(index=False))
    return out

if __name__=='__main__':
    from analysis_common import get_data,make_H
    ap=argparse.ArgumentParser();ap.add_argument('--data-dir',required=True);ap.add_argument('--output-dir',required=True)
    a=ap.parse_args();run(make_H(get_data(a.data_dir)),a.output_dir)
