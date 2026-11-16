script_file <- grep('^--file=', commandArgs(FALSE), value=TRUE)
SCRIPT_DIR <- if (length(script_file)) dirname(normalizePath(sub('^--file=', '', script_file[1]))) else getwd()
source(file.path(SCRIPT_DIR,'common.R'))
prep_run <- function(data_dir,out_dir) {
  dat <- load_h(data_dir);h <- dat$h; p <- file.path(out_dir,'prep')
  dir.create(p,recursive=TRUE,showWarnings=FALSE)
  keep <- c('video_id','channel_id','views','log_views','age_days_last','age_b','lv_adj',
    'pct_in_age','viral_A','log_subs','duration_sec','tags_count','title_len','title_upper_ratio',
    'title_has_question','title_has_exclaim','title_has_digit','title_has_emoji',
    'pub_is_weekend','pub_slot','category_name','is_short_60','ever_trending')
  write_out(h[,keep,drop=FALSE],file.path(p,'H_clean_R.csv'))
  six <- six_numbers(h)
  write_out(data.frame(metric=names(six),value=as.numeric(six)),file.path(p,'bo_6_so_R.csv'))
  audit <- data.frame(metric=c('n_input','n_H','n_excluded','n_channels_H','max_abs_age_center'),
         value=c(nrow(dat$raw),nrow(h),nrow(dat$raw)-nrow(h),length(unique(h$channel_id)),
         max(abs(tapply(h$lv_adj,h$age_b,mean)))))
  write_out(audit,file.path(p,'data_audit_R.csv'))
  message('R prep n_H=',nrow(h),' channels=',length(unique(h$channel_id)))
  invisible(h)
}
if (sys.nframe()==0L) {a<-get_args();prep_run(a$data_dir,a$output_dir)}
