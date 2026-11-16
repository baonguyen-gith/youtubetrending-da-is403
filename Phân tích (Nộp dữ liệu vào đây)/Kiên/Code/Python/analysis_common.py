"""Shared contract: age bins [a,b), population H, locale-independent outputs.
Runs on Python >=3.10. No access to the Internet is required.
"""
from pathlib import Path
import json
import platform
import sys
import numpy as np
import pandas as pd

AGE_BREAKS = [1,2,3,5,7,10,14,21,30,60,90,180,365,730,float('inf')]
AGE_LABELS = [f'[{AGE_BREAKS[i]},{AGE_BREAKS[i+1] if np.isfinite(AGE_BREAKS[i+1]) else "Inf"})' for i in range(len(AGE_BREAKS)-1)]
NUMERIC = ['views','age_days_last','duration_sec','log_subs','tags_count','title_len','title_upper_ratio','pub_hour']
BINARY = ['in_history','is_live_or_upcoming','pub_is_weekend','is_short_60','title_has_question','title_has_exclaim','title_has_digit','title_has_emoji']

def parse_bool(s):
    if pd.api.types.is_bool_dtype(s):
        return s.fillna(False)
    return s.astype('string').str.strip().str.lower().isin(['true','1','yes','y','t'])

def get_data(data_dir):
    p=Path(data_dir) / 'videos_master.csv'
    if not p.exists(): raise FileNotFoundError(f'Missing {p}')
    df=pd.read_csv(p, encoding='utf-8-sig', low_memory=False, dtype={'video_id':'string','channel_id':'string'}, memory_map=True)
    cols=['video_id','channel_id','views','age_days_last','in_history','is_live_or_upcoming','pub_is_weekend','pub_slot','category_name']
    missing=set(cols)-set(df.columns)
    if missing: raise ValueError(f'Missing required fields: {missing}')
    for c in NUMERIC:
        if c in df: df[c]=pd.to_numeric(df[c],errors='coerce')
    for c in BINARY:
        if c in df: df[c]=parse_bool(df[c])
    return df

def make_H(df):
    # H contract from §4.1, not estimated from earlier report.
    mask=(df.in_history & ~df.is_live_or_upcoming & df.views.gt(0) & df.age_days_last.ge(1))
    h=df.loc[mask].copy()
    h['log_views']=np.log10(h['views'])
    h['age_b']=pd.cut(h.age_days_last, bins=AGE_BREAKS, labels=AGE_LABELS,right=False,include_lowest=True)
    if h.age_b.isna().any():raise AssertionError('Age bin failure')
    # Mean adjustment computed *only on H*, not whole dataset or per channel.
    h['lv_adj']=h['log_views']-h.groupby('age_b',observed=True)['log_views'].transform('mean')
    h['pct_in_age']=h.groupby('age_b',observed=True)['log_views'].rank(method='average',pct=True)
    h['viral_A']=h['pct_in_age'].ge(.9)
    if h.video_id.duplicated().any():raise AssertionError('Duplicate video_id in H')
    return h

def save_csv(df, path):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(p,index=False,encoding='utf-8-sig',float_format='%.12g')

def save_json(obj,path):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    def conv(v):
        if isinstance(v,(np.integer,)):return int(v)
        if isinstance(v,(np.floating,)):return float(v)
        if isinstance(v,(np.bool_,)):return bool(v)
        if isinstance(v,(pd.Timestamp,)):return str(v)
        raise TypeError(type(v))
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=conv),encoding='utf-8')

def six_numbers(df,h):
    # Source: Table 4.3 of the uploaded report: 6 ordered test numbers.
    count_age=int(h.age_b.astype(str).eq('[7,10)').sum())
    return {'n_H':int(len(h)), 'n_channels_H':int(h.channel_id.nunique()),
            'n_age_7_10':count_age,
            'n_viral_A':int(h.viral_A.sum()),
            'median_lv_adj':float(h.lv_adj.median()),
            'n_ever_trending_H':int(h.ever_trending.fillna(False).astype(str).str.lower().isin(['true','1']).sum())}

def deps():
    import scipy,statsmodels,matplotlib
    return {'python':sys.version.split()[0],'platform':platform.platform(),
            'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,
            'statsmodels':statsmodels.__version__,'matplotlib':matplotlib.__version__}
