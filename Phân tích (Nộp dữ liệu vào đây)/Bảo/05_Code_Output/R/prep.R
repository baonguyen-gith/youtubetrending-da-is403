# prep.R - Tiền xử lý chuẩn (việc B3), bản R tương đương python/prep.py
# Cách dùng:  Rscript prep.R            (hoặc source("prep.R") từ các script khác)
# Từ B9, mặc định trỏ tới data_final_20261113/; có thể ghi đè: Sys.setenv(DATA_DIR = "đường/dẫn/data_final_20261113")
suppressPackageStartupMessages({ library(readr); library(dplyr) })

find_data_dir <- function(start) {
  d <- start
  for (i in 1:6) {
    for (rel in c("data_final_20261113",
                  file.path("Dữ liệu chính thức", "data_final_20261113"))) {
      cand <- file.path(d, rel)
      if (dir.exists(cand)) return(cand)
    }
    d <- dirname(d)
  }
  "data_clean"
}
script_file <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
start_dir <- if (length(script_file)) dirname(normalizePath(script_file[1])) else getwd()
DATA_DIR <- Sys.getenv("DATA_DIR", unset = find_data_dir(start_dir))
AGE_EDGES  <- c(1, 2, 3, 5, 7, 10, 14, 21, 30, 60, 90, 180, 365, 730, Inf)    # 14 nhóm, [a, b)
AGE_LABELS <- paste0("[", head(AGE_EDGES, -1), ", ", ifelse(is.finite(tail(AGE_EDGES, -1)), tail(AGE_EDGES, -1), "inf"), ")")
VIRAL_A_CUT <- 0.90

load_master <- function(dir = DATA_DIR) {
  read_csv(file.path(dir, "videos_master.csv"),
           col_types = cols(video_id = col_character(), channel_id = col_character(), .default = col_guess()),
           progress = FALSE, guess_max = 100000)
}

prep <- function(df) {
  h <- df %>%
    filter(in_history, !is_live_or_upcoming, views > 0, age_days_last >= 1) %>%
    mutate(log_views = log10(views),
           age_b = cut(age_days_last, breaks = AGE_EDGES, labels = AGE_LABELS, right = FALSE)) %>%
    group_by(age_b) %>%
    mutate(lv_adj = log_views - mean(log_views),
           pct_in_age = rank(log_views, ties.method = "average") / n()) %>%
    ungroup() %>%
    mutate(viral_A = as.integer(pct_in_age >= VIRAL_A_CUT))
  h
}

six_numbers <- function(h) {
  c(`1. n_H` = nrow(h),
    `2. so kenh trong H` = n_distinct(h$channel_id),
    `3. so video nhom tuoi [7, 10)` = sum(h$age_b == "[7, 10)"),
    `4. tong viral_A` = sum(h$viral_A),
    `5. trung vi lv_adj (4 chu so)` = round(median(h$lv_adj), 4),
    `6. so video ever_trending` = sum(h$ever_trending))
}

if (sys.nframe() == 0) {          # chỉ chạy khi gọi trực tiếp Rscript prep.R
  H <- prep(load_master())
  cat("DATA_DIR =", DATA_DIR, "\n"); print(six_numbers(H))
  cat(sprintf("viral_A chiem %.2f%% H (yeu cau 9-11%%)\n", 100 * mean(H$viral_A)))
}
