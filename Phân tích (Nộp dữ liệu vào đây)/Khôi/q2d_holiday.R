# q2d_holiday.R - Q2d hiệu ứng dịp lễ và Tết (K7) bằng R. Cùng quy ước với q2d_holiday.py.
# Dùng: DATA_DIR=<thư mục> Rscript q2d_holiday.R [out_dir]   (mặc định outputs/q2d_R)
source("prep.R")
args <- commandArgs(trailingOnly = TRUE)
OUT <- if (length(args) >= 1) args[1] else "outputs/q2d_R"
dir.create(OUT, recursive = TRUE, showWarnings = FALSE)
MIN_N <- 100

hol <- as.data.frame(data.table::fread("holidays_vn.csv", encoding = "UTF-8"))
hol$date <- as.Date(hol$date)

v <- load_prep()
H <- v[v$in_H, c("video_id", "channel_id", "pub_date_vn", "lv_adj", "is_short_60")]
H$pub_date <- as.Date(H$pub_date_vn)
H$ym <- format(H$pub_date, "%Y-%m")
H$is_hol <- H$pub_date %in% hol$date

cohens_d <- function(x, y) {  # pooled SD
  nx <- length(x); ny <- length(y)
  sp <- sqrt(((nx - 1) * var(x) + (ny - 1) * var(y)) / (nx + ny - 2))
  (mean(x) - mean(y)) / sp
}

group_row <- function(D, label, days_df, kind) {
  days <- days_df$date
  mths <- unique(format(days, "%Y-%m"))
  treat <- D$lv_adj[D$pub_date %in% days]
  ctrl <- D$lv_adj[D$ym %in% mths & !D$is_hol]
  if (length(treat) < 2 || length(ctrl) < 2)
    return(data.frame(group = label, n_period = length(treat), n_control = length(ctrl), kind = kind))
  tt <- t.test(treat, ctrl, var.equal = FALSE)  # Welch
  data.frame(group = label, n_period = length(treat), n_control = length(ctrl),
             mean_period = mean(treat), mean_control = mean(ctrl),
             diff = unname(tt$estimate[1] - tt$estimate[2]), ci95_low = tt$conf.int[1], ci95_high = tt$conf.int[2],
             t = unname(tt$statistic), df = unname(tt$parameter), p = tt$p.value, cohens_d = cohens_d(treat, ctrl), kind = kind)
}

run <- function(D, version) {
  pids <- sort(unique(hol$period_id))
  n_in <- sapply(pids, function(p) sum(D$pub_date %in% hol$date[hol$period_id == p]))
  rows <- list(); small <- character(0)
  for (i in seq_along(pids)) {
    g <- hol[hol$period_id == pids[i], ]
    if (n_in[i] >= MIN_N) {
      rows[[length(rows) + 1]] <- group_row(D, sprintf("%s (%s)", pids[i], g$name[1]), g, if (g$tet[1] == 1) "tet" else "le")
    } else small <- c(small, pids[i])
  }
  if (length(small) > 0)
    rows[[length(rows) + 1]] <- group_row(D, sprintf("Gộp các kỳ < %d video (%s)", MIN_N, paste(small, collapse = ", ")), hol[hol$period_id %in% small, ], "gop_nho")
  rows[[length(rows) + 1]] <- group_row(D, "Gộp Tết", hol[hol$tet == 1, ], "gop")
  rows[[length(rows) + 1]] <- group_row(D, "Gộp lễ khác (không Tết)", hol[hol$tet == 0, ], "gop")
  rows[[length(rows) + 1]] <- group_row(D, "Gộp chung", hol, "gop")
  res <- as.data.frame(data.table::rbindlist(rows, fill = TRUE))
  res$p_holm <- NA_real_
  ok <- !is.na(res$p); res$p_holm[ok] <- p.adjust(res$p[ok], method = "holm")
  res$version <- version
  res
}

res <- rbind(run(H, "tat_ca"), run(H[!H$is_short_60, ], "bo_video_ngan"))
data.table::fwrite(res, file.path(OUT, "q2d_results.csv"))
cat(sprintf("DATA_DIR=%s | n_H=%d | so kenh=%d | so ky nghi le=%d\n", DATA_DIR, nrow(H), length(unique(H$channel_id)), length(unique(hol$period_id))))
print(format(res[, c("version", "group", "n_period", "n_control", "diff", "ci95_low", "ci95_high", "p", "p_holm", "cohens_d")], digits = 4), row.names = FALSE)
