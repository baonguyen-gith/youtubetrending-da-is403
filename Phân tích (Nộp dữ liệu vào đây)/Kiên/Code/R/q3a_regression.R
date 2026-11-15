script_file <- grep('^--file=', commandArgs(FALSE), value=TRUE)
SCRIPT_DIR <- if (length(script_file)) dirname(normalizePath(sub('^--file=', '', script_file[1]))) else getwd()
source(file.path(SCRIPT_DIR,'common.R'))
BINARY <- c('title_has_question','title_has_exclaim','title_has_digit',
            'title_has_emoji','pub_is_weekend','is_short_60')
CONTENT <- c('log_duration','tags_count','title_len','title_upper_ratio',
    'title_has_question','title_has_exclaim','title_has_digit','title_has_emoji','is_short_60')

q3a_design <- function(h) {
  v <- c('log_views','age_days_last','log_subs','duration_sec','tags_count','title_len',
    'title_upper_ratio','channel_id','pub_slot','category_name',BINARY)
  d <- h[,v,drop=FALSE]
  for (z in c('log_views','age_days_last','log_subs','duration_sec','tags_count','title_len','title_upper_ratio'))
    d[[z]] <- suppressWarnings(as.numeric(d[[z]]))
  for (z in BINARY) d[[z]] <- as.numeric(d[[z]])
  d <- d[is.finite(d$age_days_last) & d$age_days_last>0 &
    is.finite(d$duration_sec) & d$duration_sec>0 & !is.na(d$channel_id),,drop=FALSE]
  d <- stats::na.omit(d)
  d$log_age <- log10(d$age_days_last);d$log_duration <- log10(d$duration_sec)
  base <- c('log_age','log_subs','log_duration','tags_count','title_len','title_upper_ratio',BINARY)
  x <- d[,base,drop=FALSE]
  # Explicit reference group is the MOST FREQUENT category, which avoids artificial
  # inflation of dummy VIF caused by rare 'Autos & Vehicles' as reference.
  baselines <- list()
  for (cat in c('pub_slot','category_name')) {
    f<-as.character(d[[cat]]);tbl<-table(f)
    b<-sort(names(tbl)[tbl==max(tbl)],method='radix')[1]
    levels<-c(b,sort(setdiff(names(tbl),b),method='radix'))
    d[[cat]]<-factor(f,levels=levels)
    baselines[[cat]]<-b
    if (length(levels)>1) for (lev in levels[-1]) {
      x[[paste0(cat,'__',lev)]]<-as.numeric(as.character(d[[cat]])==lev)
    }
  }
  list(d=d,x=x,baselines=baselines)
}

q3a_vif <- function(x) {
  z <- scale(as.matrix(x))
  cc <- crossprod(z)/(nrow(z)-1)
  inv <- tryCatch(solve(cc),error=function(e) qr.solve(cc,tol=1e-12))
  res<-data.frame(term=names(x),VIF=diag(inv));res[order(-res$VIF),,drop=FALSE]
}

q3a_fit <- function(d,x,cluster=TRUE) {
  require_pkg('sandwich')
  # Formula-independent numeric design; make.names only affects printed coefficient labels.
  df<-data.frame(log_views=d$log_views,x,check.names=TRUE)
  fit<-stats::lm(log_views~.,data=df)
  if (!cluster) return(list(fit=fit,vcov=stats::vcov(fit)))
  vc<-sandwich::vcovCL(fit,cluster=as.character(d$channel_id),type='HC1',cadjust=TRUE)
  list(fit=fit,vcov=vc)
}
q3a_r2 <- function(d,x) {
  if (ncol(x)==0) return(0)
  A<-cbind('(Intercept)'=1,as.matrix(x))
  coeff<-stats::lm.fit(A,d$log_views)
  1-sum(coeff$residuals^2)/sum((d$log_views-mean(d$log_views))^2)
}
q3a_run <- function(h,out_dir) {
  require_pkg('sandwich')
  p<-file.path(out_dir,'q3a');dir.create(p,recursive=TRUE,showWarnings=FALSE)
  dat<-q3a_design(h);d<-dat$d;x<-dat$x
  write_out(q3a_vif(x),file.path(p,'q3a_vif_before_R.csv'))
  rem<-data.frame(step=integer(),variable=character(),trigger_vif=numeric(),dropped_terms=character())
  for (step in 1:20) {
    v<-q3a_vif(x);b<-v[v$VIF>10,,drop=FALSE]
    if (!nrow(b)) break
    if ('is_short_60' %in% b$term) {
      key <- 'is_short_60'; drop <- key
    } else {
      key<-b$term[1];drop<-key
      if (startsWith(key,'category_name__')) {
        key<-'category_name (factor)';drop<-grep('^category_name__',names(x),value=TRUE)
      } else if (startsWith(key,'pub_slot__')) {
        key<-'pub_slot (factor)';drop<-grep('^pub_slot__',names(x),value=TRUE)
      }
    }
    if ('log_age' %in% drop) stop('Mandatory age control has VIF >10; inspect input')
    rem<-rbind(rem,data.frame(step=step,variable=key,trigger_vif=b$VIF[1],dropped_terms=paste(drop,collapse=';')))
    x<-x[,setdiff(names(x),drop),drop=FALSE]
  }
  write_out(q3a_vif(x),file.path(p,'q3a_vif_R.csv'))
  write_out(rem,file.path(p,'q3a_removed_vif_R.csv'))
  result<-q3a_fit(d,x);m<-result$fit;V<-result$vcov
  coefficients<-stats::coef(m)
  se<-sqrt(diag(V));df_t<-length(unique(d$channel_id))-1
  t<-coefficients/se;pval<-2*stats::pt(-abs(t),df=df_t)
  half<-stats::qt(.975,df=df_t)*se
  sd_y<-stats::sd(d$log_views)
  std<-rep(NA_real_,length(coefficients))
  for (j in seq_along(coefficients)) if (j>1) std[j]<-coefficients[j]*stats::sd(x[[j-1]])/sd_y
  terms<-c('(Intercept)',names(x))
  out<-data.frame(term=terms,term_R=names(coefficients),coefficient=as.numeric(coefficients),
      se_cluster=as.numeric(se),t_cluster=as.numeric(t),p_cluster=as.numeric(pval),
      ci95_low=as.numeric(coefficients-half),ci95_high=as.numeric(coefficients+half),
      beta_standardized=std)
  write_out(out,file.path(p,'q3a_coefficients_R.csv'))
  full<-summary(m)$r.squared
  groups<-list(channel='log_subs',content=intersect(CONTENT,names(x)),
    timing=c(intersect('pub_is_weekend',names(x)),grep('^pub_slot__',names(x),value=TRUE)),
    category=grep('^category_name__',names(x),value=TRUE))
  contr<-do.call(rbind,lapply(names(groups),function(nm) {
    drop<-groups[[nm]];reduced<-if(length(drop))q3a_r2(d,x[,setdiff(names(x),drop),drop=FALSE]) else full
    data.frame(group=nm,n_terms=length(drop),R2_full=full,R2_without_group=reduced,
      delta_R2=full-reduced,removed_columns=paste(drop,collapse=';'))
  }))
  write_out(contr,file.path(p,'q3a_delta_R2_R.csv'))
  summarytab<-data.frame(metric=c('n_used','n_channels','n_parameters','R2','adjusted_R2',
    'RMSE','df_cluster','category_reference','pub_slot_reference'),
    value=as.character(c(nrow(d),length(unique(d$channel_id)),length(coefficients),full,
      summary(m)$adj.r.squared,sqrt(mean(resid(m)^2)),df_t,
      dat$baselines$category_name,dat$baselines$pub_slot)))
  write_out(summarytab,file.path(p,'q3a_summary_R.csv'))
  set.seed(42)
  png(file.path(p,'q3a_residual_vs_fitted_R.png'),width=1100,height=700,res=150)
  idx<-sample(seq_along(resid(m)),min(10000,nrow(d)))
  plot(stats::fitted(m)[idx],resid(m)[idx],pch=16,cex=.2,col='#22558833',
       xlab='Fitted log10 views',ylab='Residual',main='Q3a: residual vs fitted')
  abline(h=0,col='red');dev.off()
  png(file.path(p,'q3a_qq_R.png'),width=850,height=750,res=150)
  idx<-sample(seq_along(resid(m)),min(6000,nrow(d)))
  qqnorm(resid(m)[idx]);qqline(resid(m)[idx],col='red');dev.off()
  message('R Q3a complete: n=',nrow(d),' R2=',round(full,6))
  invisible(list(summary=summarytab,coefficients=out,delta=contr))
}
if (sys.nframe()==0L) {a<-get_args();q3a_run(load_h(a$data_dir)$h,a$output_dir)}
