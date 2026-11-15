import argparse
from pathlib import Path
import numpy as np
from analysis_common import get_data,make_H,six_numbers,save_csv,save_json,deps

def run(data_dir,out_dir):
    d=get_data(data_dir)
    h=make_H(d)
    out=Path(out_dir)/'prep'; out.mkdir(parents=True,exist_ok=True)
    # Only fields required by all specified Kien analyses and downstream Power BI.
    keep=['video_id','channel_id','views','log_views','age_days_last','age_b','lv_adj',
      'pct_in_age','viral_A','log_subs','duration_sec','tags_count','title_len','title_upper_ratio',
      'title_has_question','title_has_exclaim','title_has_digit','title_has_emoji',
      'pub_is_weekend','pub_slot','category_name','is_short_60','ever_trending']
    save_csv(h[keep],out/'H_clean.csv')
    six=six_numbers(d,h)
    save_csv(__import__('pandas').DataFrame({'metric':list(six),'value':list(six.values())}),out/'bo_6_so.csv')
    audit={'dataset':str(data_dir),'input_videos':len(d),'n_H':len(h),'excluded':len(d)-len(h),
       'excluded_reasons_overlapping':{'not_history':int((~d.in_history).sum()),
         'live_or_upcoming':int(d.is_live_or_upcoming.sum()),
         'views_not_positive_or_na':int((~d.views.gt(0)).sum()),
         'age_lt_1_or_na':int((~d.age_days_last.ge(1)).sum())},
       'n_age_bins':len(h.age_b.cat.categories),'lv_adj_center_check_max_abs':float(h.groupby('age_b',observed=True).lv_adj.mean().abs().max()),
       'six_numbers':six,'versions':deps()}
    save_json(audit,out/'data_audit.json')
    print('H:',len(h),'channels:',h.channel_id.nunique(),'age-centered max:',audit['lv_adj_center_check_max_abs'])
    return h

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-dir',required=True);p.add_argument('--output-dir',required=True)
    a=p.parse_args();run(a.data_dir,a.output_dir)
