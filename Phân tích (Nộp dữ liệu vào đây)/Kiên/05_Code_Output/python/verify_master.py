"""Kiểm tra độc lập trực tiếp trên dữ liệu video, không cần statsmodels, pingouin hoặc R."""
import hashlib
import os
import platform
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import scipy
from scipy import stats

ROOT=Path(os.environ.get("OUT_ROOT","outputs"))
DATA=Path(os.environ.get("DATA_DIR","../data_clean_temp"))/"videos_master.csv"
checks=[]

def check(section,metric,value,reference,tolerance=1e-7):
    checks.append((section,metric,float(value),float(reference),abs(value-reference)<=tolerance))

def result(section,file):
    return pd.read_csv(ROOT/section/file)

def test_groups(h,label):
    a=h.loc[h.pub_is_weekend,"adj"];b=h.loc[~h.pub_is_weekend,"adj"]
    row=result("q2a","q2a_results_R.csv").set_index("dataset").loc[label]
    w=stats.ttest_ind(a,b,equal_var=False);diff=a.mean()-b.mean()
    pooled=np.sqrt(((len(a)-1)*a.var()+(len(b)-1)*b.var())/(len(h)-2))
    for k,v in dict(welch_t=w.statistic,welch_df=w.df,welch_p=w.pvalue,ci_low=w.confidence_interval().low,ci_high=w.confidence_interval().high,cohen_d=diff/pooled,levene_F=stats.levene(a,b).statistic,mw_U=stats.mannwhitneyu(a,b,method="asymptotic").statistic).items():
        check("q2a",f"{label}/{k}",v,row[k])
    om=result("q2b","q2b_anova_results_R.csv").set_index(["dataset","factor"])
    pairs=result("q2b","q2b_gameshowell_all_R.csv")
    for fac in ["pub_slot","category_name"]:
        d=h.copy()
        if fac=="category_name":
            d=d[d[fac].map(d[fac].value_counts())>=30]
        g=d.groupby(fac).adj.agg(["count","mean","var"])
        n=g["count"];mu=g["mean"];v=g["var"];weights=n/v;k=len(g)
        grand=np.average(mu,weights=weights)
        correction=((1-weights/weights.sum())**2/(n-1)).sum()
        f=(weights*(mu-grand)**2).sum()/(k-1)/(1+2*(k-2)*correction/(k*k-1))
        df=(k*k-1)/(3*correction); groups=[s.adj for _,s in d.groupby(fac)]
        eta=(n*(mu-d.adj.mean())**2).sum()/((d.adj-d.adj.mean())**2).sum()
        for key,val in dict(welch_F=f,welch_df1=k-1,welch_df2=df,welch_p=stats.f.sf(f,k-1,df),eta2=eta,kw_H=stats.kruskal(*groups).statistic,levene_F=stats.levene(*groups).statistic).items():
            check("q2b",f"{label}/{fac}/{key}",val,om.loc[(label,fac),key])
        for r in pairs[(pairs.dataset==label)&(pairs.factor==fac)].itertuples():
            x,y=r.group1,r.group2
            vx,vy=v[x]/n[x],v[y]/n[y]
            est=mu[x]-mu[y];se=np.sqrt(vx+vy)
            df=(vx+vy)**2/(vx**2/(n[x]-1)+vy**2/(n[y]-1))
            p=stats.studentized_range.sf(abs(est)*np.sqrt(2)/se,k,df)
            path=f"{label}/{fac}/{x} vs {y}"
            check("q2b",path+"/diff",est,r.diff)
            check("q2b",path+"/p_adj",p,r.p_adj,5e-4)
            check("q2b",path+"/significant",int(p<.05),int(r.significant))

def regression(h):
    d=h[h.category_name.map(h.category_name.value_counts())>=30].copy()
    ref=result("q3a","q3a_coefficients_R.csv").set_index("term")
    model=result("q3a","q3a_model_R.csv").iloc[0]
    # Đọc danh sách biến được giữ sau vòng VIF từ bảng hệ số; đối chứng nghiệm OLS và phương sai theo cụm.
    x=pd.DataFrame(index=d.index)
    for term in ref.index:
        if term=="Intercept": x[term]=1.
        elif term.startswith("log10("): x[term]=np.log10(d[term[6:-1]])
        elif "=" in term:
            field,group=term.split("=",1)
            x[term]=d["category_name" if field=="category" else field].eq(group)
        else: x[term]=d[term]
    X=x.to_numpy(float);y=d.log_views.to_numpy()
    beta=np.linalg.lstsq(X,y,rcond=None)[0];res=y-X@beta
    score=pd.DataFrame(X*res[:,None]).groupby(d.channel_id.to_numpy()).sum().to_numpy()
    n,k=X.shape;G=len(score)
    bread=np.linalg.inv(X.T@X);cov=bread@(score.T@score)@bread*(G/(G-1))*((n-1)/(n-k))
    se=np.sqrt(np.diag(cov));sst=((y-y.mean())**2).sum()
    r2=1-res@res/sst
    for key,value in dict(n=n,k_tham_so=k,n_clusters=G,r2=r2,adj_r2=1-(1-r2)*(n-1)/(n-k),rmse=np.sqrt(res@res/(n if "residual_sd" in model.index else n-k))).items():
        check("q3a",key,value,model[key])
    errors=pd.DataFrame([{"n":n,"k":k,"SSE":res@res,"rmse":np.sqrt(res@res/n),"residual_sd":np.sqrt(res@res/(n-k))}])
    errors.to_csv(ROOT/"q3a"/"q3a_sai_so_tinh_lai.csv",index=False,encoding="utf-8-sig")
    for i,t in enumerate(x):
        check("q3a",t+"/coef",beta[i],ref.loc[t,"coef"])
        check("q3a",t+"/se_cluster",se[i],ref.loc[t,"se_cluster"])
    vif=result("q3a","q3a_vif_columns_R.csv").set_index("column")
    for col,val in zip(x.columns[1:],np.diag(np.linalg.inv(np.corrcoef(X[:,1:],rowvar=False)))):
        check("q3a",col+"/VIF",val,vif.loc[col,"vif"])
    for row in result("q3a","q3a_group_contribution_R.csv").itertuples():
        terms=str(row.bien).split(";")
        keep=[col for col in x if col not in terms and not any(col.startswith(prefix+"=") for prefix in ["category" if t=="category_name" else t for t in terms])]
        sub=x[keep].to_numpy(float);e=y-sub@np.linalg.lstsq(sub,y,rcond=None)[0]
        check("q3a","delta_R2/"+row.nhom,r2-(1-e@e/sst),row.giam_R2)

def main():
    m=pd.read_csv(DATA,dtype={"video_id":str},low_memory=False)
    if m.video_id.isna().any() or not m.video_id.str.len().eq(11).all() or not m.video_id.is_unique:
        raise ValueError("video_id thiếu, trùng hoặc sai độ dài.")
    h=m.loc[m.in_history&~m.is_live_or_upcoming&(m.views>0)&(m.age_days_last>=1)].copy()
    np.testing.assert_allclose(h.log_views,np.log10(h.views),rtol=0,atol=1e-10)
    edges=[1,2,3,5,7,10,14,21,30,60,90,180,365,730,np.inf]
    age=np.searchsorted(edges,h.age_days_last,side="right")-1
    grouped=h.groupby(age).log_views
    h["adj"]=h.log_views-grouped.transform("mean")
    six=dict(n_H=len(h),so_kenh_trong_H=h.channel_id.nunique(),n_nhom_tuoi_7_10=h.age_days_last.between(7,10,inclusive="left").sum(),tong_viral_A=(grouped.rank(pct=True)>=.90).sum(),trung_vi_lv_adj=round(h.adj.median(),4),n_ever_trending_trong_H=h.ever_trending.sum())
    for lang in ["R","python"]:
        ref=result("prep","so_kiem_tra_"+lang+".csv").iloc[0]
        for key,v in six.items(): check("prep",lang+"/"+key,v,ref[key])
    test_groups(h,"H_toan_bo")
    test_groups(h.loc[~h.is_short_60],"H_bo_video_ngan")
    regression(h)
    dst=ROOT/"kiem_tra_tu_master.csv"
    frame=pd.DataFrame(checks,columns=["phan","chi_so","tinh_lai","tham_chieu","dat"])
    frame.to_csv(dst,index=False,encoding="utf-8-sig")
    digest=hashlib.sha256(DATA.read_bytes()).hexdigest()
    text=f"SHA-256 videos_master.csv: {digest}\nThời điểm kiểm tra UTC: {datetime.now(timezone.utc).isoformat()}\nPython {platform.python_version()}, NumPy {np.__version__}, pandas {pd.__version__}, SciPy {scipy.__version__}\n{len(m)} video đầu vào. {frame.dat.sum()}/{len(frame)} đối chiếu đạt.\n"
    (ROOT/"kiem_tra_tu_master.txt").write_text(text,encoding="utf-8")
    sixrow={"nguoi":"Nguyễn Trung Kiên","thoi_diem_UTC":datetime.now(timezone.utc).isoformat(),"nguon":DATA.parent.name,**six}
    pd.DataFrame([sixrow]).to_csv(ROOT/"prep"/"so_kiem_tra_Kien.csv",index=False,encoding="utf-8-sig")
    print(text)
    if not frame.dat.all():
        print(frame.loc[~frame.dat].to_string(index=False));raise SystemExit(1)
if __name__=="__main__":
    main()
