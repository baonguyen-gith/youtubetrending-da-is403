script_file <- grep('^--file=', commandArgs(FALSE), value=TRUE)
SCRIPT_DIR <- if (length(script_file)) dirname(normalizePath(sub('^--file=', '', script_file[1]))) else getwd()
source(file.path(SCRIPT_DIR,'common.R'))
q2a_evaluate <- function(h,label) {
  require_pkg('car')
  a <- h$lv_adj[h$pub_is_weekend & !is.na(h$lv_adj)]
  b <- h$lv_adj[!h$pub_is_weekend & !is.na(h$lv_adj)]
  na <- length(a);nb <- length(b)
  if (min(na,nb)<3) stop('Group too small')
  va <- var(a);vb <- var(b);ma <- mean(a);mb <- mean(b)
  te <- stats::t.test(a,b,var.equal=FALSE,conf.level=.95)
  pooled <- sqrt(((na-1)*va+(nb-1)*vb)/(na+nb-2))
  lev <- car::leveneTest(c(a,b),factor(c(rep('weekend',na),rep('weekday',nb))),center=median)
  wm <- stats::wilcox.test(a,b,exact=FALSE,correct=TRUE,alternative='two.sided')
  data.frame(subset=label,n_weekend=na,n_weekday=nb,mean_weekend=ma,mean_weekday=mb,
    sd_weekend=sqrt(va),sd_weekday=sqrt(vb),difference_weekend_minus_weekday=ma-mb,
    t_welch=unname(te$statistic),df_welch=unname(te$parameter),p_welch=te$p.value,
    ci95_low=te$conf.int[1],ci95_high=te$conf.int[2],cohens_d_pooled=(ma-mb)/pooled,
    levene_F=lev[1,'F value'],levene_p=lev[1,'Pr(>F)'],
    mann_whitney_U=unname(wm$statistic),
    mann_whitney_p=wm$p.value)
}
q2a_run <- function(h,out_dir) {
  p<-file.path(out_dir,'q2a');dir.create(p,recursive=TRUE,showWarnings=FALSE)
  tab<-rbind(q2a_evaluate(h,'H'),q2a_evaluate(h[!h$is_short_60,,drop=FALSE],'H_no_short_60'))
  write_out(tab,file.path(p,'q2a_tests_R.csv'))
  set.seed(42);png(file.path(p,'q2a_qqplot_R.png'),width=1200,height=520,res=150)
  par(mfrow=c(1,2)); for (flag in c(TRUE,FALSE)) {
    v<-h$lv_adj[h$pub_is_weekend==flag];v<-sample(v,min(5000,length(v)))
    qqnorm(v,main=if(flag)'Cuối tuần' else 'Ngày thường');qqline(v,col='red')
  };dev.off()
  message('R Q2a complete');invisible(tab)
}
if (sys.nframe()==0L) {a<-get_args();q2a_run(load_h(a$data_dir)$h,a$output_dir)}
