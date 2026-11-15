import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Python'))
import numpy as np
import pandas as pd
from scipy import stats
from analysis_common import make_H,six_numbers
from q2b_anova import welch_anova,games_howell
from q2a_tests import evaluate

def toy():
    n=60
    return pd.DataFrame({'video_id':[f'v{i}' for i in range(n)],
      'channel_id':[f'c{i//6}' for i in range(n)], 'in_history':[True]*n,
      'is_live_or_upcoming':[False]*n, 'views':np.arange(10,70,dtype=float),
      'age_days_last':[1,2,3,5,7,10]*10, 'pub_is_weekend':[False,True]*30,
      'pub_slot':['Sáng']*30+['Tối']*30,'category_name':['Music']*30+['Gaming']*30,
      'ever_trending':[False]*n,'is_short_60':[False]*n})

def test_age_b_and_center():
    h=make_H(toy())
    assert len(h)==60
    assert h.loc[1,'age_b']=='[2,3)'
    assert h.loc[4,'age_b']=='[7,10)'
    assert np.max(np.abs(h.groupby('age_b',observed=True).lv_adj.mean()))<1e-12
    six=six_numbers(toy(),h)
    assert six['n_H']==60 and six['n_age_7_10']==10

def test_welch():
    h=make_H(toy())
    r=evaluate(h,'toy')
    a=h.loc[h.pub_is_weekend,'lv_adj'];b=h.loc[~h.pub_is_weekend,'lv_adj']
    v=stats.ttest_ind(a,b,equal_var=False)
    assert np.isclose(r['t_welch'],v.statistic)
    assert np.isclose(r['p_welch'],v.pvalue)
    assert r['ci95_low'] < r['difference_weekend_minus_weekday'] < r['ci95_high']

def test_welch_anova():
    rng=np.random.default_rng(42)
    a=rng.normal(size=40);b=rng.normal(1,3,size=22);c=rng.normal(2,2,size=31)
    xs=[a,b,c];ns=[len(x) for x in xs]
    F,df2,p=welch_anova(ns,[x.mean() for x in xs],[x.var(ddof=1) for x in xs])
    chk=stats.f_oneway(*xs,equal_var=False)
    assert np.isclose(F,chk.statistic,rtol=1e-11)
    assert np.isclose(p,chk.pvalue,rtol=1e-11)
    pairs=games_howell(pd.DataFrame({'n':ns,'mean':[x.mean() for x in xs],
               'var':[x.var(ddof=1) for x in xs]},index=['a','b','c']),3)
    assert len(pairs)==3 and pairs.p_GH.between(0,1).all()

if __name__=='__main__':
    test_age_b_and_center();test_welch();test_welch_anova();print('3/3 tests passed')
