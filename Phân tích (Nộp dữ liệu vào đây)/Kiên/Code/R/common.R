# Shared data contract. R >= 4.3; arguments --data-dir and --output-dir.
script_dir <- function() {
  x <- grep('^--file=', commandArgs(FALSE), value=TRUE)
  if (length(x)) return(dirname(normalizePath(sub('^--file=', '', x[1]))))
  getwd()
}
get_args <- function() {
  x <- commandArgs(trailingOnly=TRUE)
  take <- function(k) { i <- which(x == k); if (!length(i) || i[1] >= length(x)) stop(paste('Required',k)); x[i[1]+1] }
  list(data_dir=take('--data-dir'),output_dir=take('--output-dir'))
}
require_pkg <- function(package) {
  if (!requireNamespace(package,quietly=TRUE)) stop(paste('Missing R package:',package,'. Run install_packages.R'))
}
write_out <- function(d,path) {
  dir.create(dirname(path),recursive=TRUE,showWarnings=FALSE)
  utils::write.csv(d,path,row.names=FALSE,fileEncoding='UTF-8',na='')
}
tobool <- function(z) tolower(trimws(as.character(z))) %in% c('true','1','yes','y','t')
AGE_BREAKS <- c(1,2,3,5,7,10,14,21,30,60,90,180,365,730,Inf)
AGE_LABELS <- paste0('[',head(AGE_BREAKS,-1),',',ifelse(is.infinite(tail(AGE_BREAKS,-1)),'Inf',tail(AGE_BREAKS,-1)),')')
load_h <- function(data_dir) {
  file <- file.path(data_dir,'videos_master.csv')
  if (!file.exists(file)) stop(paste('Not found',file))
  if (requireNamespace('data.table',quietly=TRUE)) {
    d <- as.data.frame(data.table::fread(file,encoding='UTF-8',showProgress=FALSE))
  } else d <- utils::read.csv(file,fileEncoding='UTF-8-BOM',stringsAsFactors=FALSE,check.names=FALSE)
  for (v in c('in_history','is_live_or_upcoming','pub_is_weekend','is_short_60',
    'title_has_question','title_has_exclaim','title_has_digit','title_has_emoji')) d[[v]] <- tobool(d[[v]])
  for (v in c('views','age_days_last','duration_sec','log_subs','tags_count','title_len','title_upper_ratio'))
    d[[v]] <- suppressWarnings(as.numeric(d[[v]]))
  mask <- which(d$in_history & !d$is_live_or_upcoming & !is.na(d$views) & d$views > 0 &
                    !is.na(d$age_days_last) & d$age_days_last >= 1)
  h <- d[mask,,drop=FALSE]
  h$log_views <- log10(h$views)
  h$age_b <- cut(h$age_days_last,breaks=AGE_BREAKS,labels=AGE_LABELS,right=FALSE,include.lowest=TRUE)
  if (anyNA(h$age_b)) stop('Age bin contains NA in H')
  means <- tapply(h$log_views,h$age_b,mean)
  h$lv_adj <- h$log_views - means[as.character(h$age_b)]
  h$pct_in_age <- ave(h$log_views,h$age_b,FUN=function(v) rank(v,ties.method='average')/length(v))
  h$viral_A <- h$pct_in_age >= 0.90
  if (anyDuplicated(h$video_id)) stop('Duplicate video_id in H')
  list(raw=d,h=h)
}
six_numbers <- function(h) {
  c(n_H=nrow(h),n_channels_H=length(unique(h$channel_id)),
    n_age_7_10=sum(as.character(h$age_b)=='[7,10)'),
    n_viral_A=sum(h$viral_A),median_lv_adj=median(h$lv_adj),
    n_ever_trending_H=sum(tobool(h$ever_trending)))
}
