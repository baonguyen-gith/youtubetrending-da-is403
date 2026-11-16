script_file <- grep('^--file=', commandArgs(FALSE), value=TRUE)
SCRIPT_DIR <- if (length(script_file)) dirname(normalizePath(sub('^--file=', '', script_file[1]))) else getwd()
source(file.path(SCRIPT_DIR,'common.R'))
q2b_one_factor <- function(h,col,label) {
  require_pkg('car');require_pkg('rstatix')
  dat <- h[,c('lv_adj',col),drop=FALSE];names(dat) <- c('lv_adj','group')
  dat <- dat[complete.cases(dat),,drop=FALSE]
  dat$group <- factor(as.character(dat$group),levels=sort(unique(as.character(dat$group)),method='radix'))
  n <- table(dat$group); valid <- names(n)[n>=2];dat<-dat[dat$group %in% valid,,drop=FALSE]
  dat$group <- droplevels(dat$group);n<-table(dat$group)
  model <- stats::aov(lv_adj ~ group,data=dat)
  F <- summary(model)[[1]][['F value']][1];pval<-summary(model)[[1]][['Pr(>F)']][1]
  w <- stats::oneway.test(lv_adj ~ group,data=dat,var.equal=FALSE)
  lev <- car::leveneTest(lv_adj ~ group,data=dat,center=median)
  kw<-kruskal.test(lv_adj~group,data=dat)
  sums<-tapply(dat$lv_adj,dat$group,mean);variances<-tapply(dat$lv_adj,dat$group,var)
  grand<-mean(dat$lv_adj)
  ss_between<-sum(n*(sums-grand)^2)
  ss_within<-sum((n-1)*variances)
  eta<-ss_between/(ss_between+ss_within)
  tab<-data.frame(subset=label,factor=col,n_total=nrow(dat),k=nlevels(dat$group),
    min_group_n=min(n),anova_F=unname(F),anova_df1=nlevels(dat$group)-1,anova_df2=nrow(dat)-nlevels(dat$group),
    anova_p=pval,welch_F=unname(w$statistic),welch_df1=unname(w$parameter[1]),welch_df2=unname(w$parameter[2]),
    welch_p=w$p.value,levene_F=lev[1,'F value'],levene_p=lev[1,'Pr(>F)'],
    kruskal_H=unname(kw$statistic),kruskal_p=kw$p.value,eta_sq_classic=eta,
    decision_primary=ifelse(lev[1,'Pr(>F)']<.05,'Welch','classic_ANOVA'))
  gm<-do.call(rbind,lapply(levels(dat$group),function(v) {
    z<-dat$lv_adj[dat$group==v]; s<-sd(z);se<-s/sqrt(length(z));half<-qt(.975,length(z)-1)*se
    data.frame(subset=label,factor=col,group=v,n=length(z),mean=mean(z),sd=s,se=se,ci95_low=mean(z)-half,ci95_high=mean(z)+half)
  }))
  # Official R implementation of heteroscedastic Games-Howell method.
  gh<-rstatix::games_howell_test(dat,lv_adj~group)
  # Keep explicit originals/adjusted results; R output differs naming from Python by design.
  gh$subset<-label;gh$factor<-col
  tab$games_howell_pairs<-nrow(gh)
  tab$games_howell_significant_pairs<-sum(gh$p.adj<.05,na.rm=TRUE)
  list(result=tab,means=gm,gh=gh)
}
q2b_run <- function(h,out_dir) {
  p<-file.path(out_dir,'q2b');dir.create(p,recursive=TRUE,showWarnings=FALSE)
  objects<-list()
  for (label in c('H','H_no_short_60')) for (factor in c('pub_slot','category_name')) {
    d<-if (label=='H') h else h[!h$is_short_60,,drop=FALSE]
    objects[[paste(label,factor)]]<-q2b_one_factor(d,factor,label)
  }
  res<-do.call(rbind,lapply(objects,`[[`,'result'))
  gm<-do.call(rbind,lapply(objects,`[[`,'means'))
  gh<-do.call(rbind,lapply(objects,`[[`,'gh'))
  write_out(res,file.path(p,'q2b_anova_R.csv'));write_out(gm,file.path(p,'q2b_group_means_R.csv'))
  write_out(gh,file.path(p,'q2b_games_howell_R.csv'))
  write_out(gh[gh$p.adj<.05,,drop=FALSE],file.path(p,'q2b_significant_pairs_R.csv'))
  for (factor in c('pub_slot','category_name')) {
    g<-gm[gm$factor==factor & gm$subset=='H',,drop=FALSE];g<-g[order(g$mean),]
    png(file.path(p,paste0('q2b_',factor,'_R.png')),width=1400,height=max(650,65*nrow(g)),res=150)
    par(mar=c(5,12,4,2));plot(g$mean,seq_len(nrow(g)),xlim=range(c(g$ci95_low,g$ci95_high)),
      yaxt='n',pch=19,xlab='Mean lv_adj (95% CI)',ylab='',main=paste('Q2b',factor))
    axis(2,at=seq_len(nrow(g)),labels=paste0(g$group,' (n=',g$n,')'),las=2,cex.axis=.7)
    segments(g$ci95_low,seq_len(nrow(g)),g$ci95_high,seq_len(nrow(g)))
    abline(v=0,col='gray',lty=2);dev.off()
  }
  message('R Q2b complete');invisible(res)
}
if (sys.nframe()==0L) {a<-get_args();q2b_run(load_h(a$data_dir)$h,a$output_dir)}
