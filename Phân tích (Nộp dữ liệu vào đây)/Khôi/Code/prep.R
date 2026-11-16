# prep.R - Tiền xử lý chuẩn (Chương 4 báo cáo): H, age_b, lv_adj, viral_A.
# Dùng:  DATA_DIR=<thư mục> Rscript prep.R      (mặc định ./data_clean_temp)
#        source("prep.R"); v <- load_prep()
invisible(try(Sys.setlocale("LC_ALL", "C.UTF-8"), silent = TRUE))  # tiếng Việt UTF-8
DATA_DIR <- Sys.getenv("DATA_DIR", "data_clean_temp")
AGE_EDGES <- c(1, 2, 3, 5, 7, 10, 14, 21, 30, 60, 90, 180, 365, 730, Inf)  # 14 nhóm, [a, b)

load_prep <- function(data_dir = DATA_DIR) {
  f <- file.path(data_dir, "videos_master.csv")
  v <- if (requireNamespace("data.table", quietly = TRUE)) {
    as.data.frame(data.table::fread(f, encoding = "UTF-8", na.strings = c("", "NA")))
  } else read.csv(f, fileEncoding = "UTF-8-BOM", stringsAsFactors = FALSE, na.strings = c("", "NA"))
  names(v)[1] <- sub("^\\W*video_id$", "video_id", names(v)[1])
  lg <- function(x) if (is.logical(x)) x else as.logical(x)
  v$in_history <- lg(v$in_history); v$is_live_or_upcoming <- lg(v$is_live_or_upcoming)
  v$ever_trending <- lg(v$ever_trending); v$is_short_60 <- lg(v$is_short_60)
  # Quần thể H (mục 4.1)
  v$in_H <- v$in_history & !v$is_live_or_upcoming & !is.na(v$views) & v$views > 0 & !is.na(v$age_days_last) & v$age_days_last >= 1
  v$in_H[is.na(v$in_H)] <- FALSE
  # Nhóm tuổi (mục 4.2): khoảng đóng trái, mở phải
  v$age_b <- cut(v$age_days_last, breaks = AGE_EDGES, right = FALSE)
  v$log_views <- ifelse(!is.na(v$views) & v$views > 0, log10(v$views), NA_real_)
  # lv_adj (mục 4.3): trừ trung bình log_views của nhóm tuổi, trung bình tính trên H
  v$lv_adj <- NA_real_; v$pct_in_age <- NA_real_; v$viral_A <- FALSE
  ih <- which(v$in_H)
  v$lv_adj[ih] <- v$log_views[ih] - ave(v$log_views[ih], v$age_b[ih], FUN = mean)
  # viral_A (mục 4.4)
  v$pct_in_age[ih] <- ave(v$log_views[ih], v$age_b[ih], FUN = function(x) rank(x, ties.method = "average") / length(x))
  v$viral_A[ih] <- v$pct_in_age[ih] >= 0.90
  v
}

six_numbers <- function(v) {
  H <- v[v$in_H, ]
  c("1. n_H" = nrow(H),
    "2. so kenh trong H" = length(unique(H$channel_id)),
    "3. n_H thuoc nhom tuoi [7,10)" = sum(H$age_days_last >= 7 & H$age_days_last < 10),
    "4. tong viral_A" = sum(H$viral_A),
    "5. trung vi lv_adj (4 chu so)" = round(median(H$lv_adj), 4),
    "6. n_H co ever_trending = TRUE" = sum(H$ever_trending, na.rm = TRUE))
}

if (sys.nframe() == 0) {
  v <- load_prep()
  cat("DATA_DIR =", DATA_DIR, "\n")
  s <- six_numbers(v); for (k in names(s)) cat(k, ":", format(s[[k]], nsmall = ifelse(grepl("lv_adj", k), 4, 0)), "\n")
  H <- v[v$in_H, ]
  cat(sprintf("[kiem tra] viral_A chiem %.2f%% cua H (phai trong 9-11%%)\n", mean(H$viral_A) * 100))
  cat("[kiem tra] so nhom tuoi co mat trong H:", length(unique(H$age_b)), "/ 14\n")
}
