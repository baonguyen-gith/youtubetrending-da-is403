# prep.R - Tiền xử lý chuẩn (mục 0.2 của Phan_cong.docx): quần thể H, age_b, lv_adj, viral_A.
# Người phụ trách: Nguyễn Trung Kiên (N3).
# Chạy từ thư mục 05_Code_Output:  Rscript R/prep.R   -> in bộ 6 số kiểm tra (mục 0.4)
suppressPackageStartupMessages({library(readr); library(dplyr)})

data_dir <- Sys.getenv("DATA_DIR", "data_clean")   # <-- CHỈ ĐỔI DÒNG NÀY sang "data_final_20261113" (hoặc đặt biến môi trường DATA_DIR)
out_root <- Sys.getenv("OUT_ROOT", "outputs")       # thư mục outputs/

AGE_EDGES   <- c(1, 2, 3, 5, 7, 10, 14, 21, 30, 60, 90, 180, 365, 730, Inf)
SLOT_ORDER  <- c("Khuya 0-5h", "Sáng 6-11h", "Chiều 12-17h", "Tối 18-21h", "Đêm 22-23h")
MIN_GROUP_N <- 30   # nhóm thể loại có n < 30 bị loại khỏi ANOVA / hồi quy (ghi trong báo cáo)

read_master <- function(dir = data_dir) {
  df <- readr::read_csv(file.path(dir, "videos_master.csv"),
                        col_types = cols(video_id = "c", trend_first_ts = "c", .default = col_guess()),
                        guess_max = 200000, progress = FALSE)
  stopifnot(sum(nchar(df$video_id) != 11) == 0)
  df
}

prep <- function(df) {
  df %>%
    filter(in_history, !is_live_or_upcoming, views > 0, age_days_last >= 1) %>%
    mutate(age_b = cut(age_days_last, AGE_EDGES, right = FALSE)) %>%
    group_by(age_b) %>%
    mutate(lv_adj = log_views - mean(log_views),
           pct_in_age = rank(log_views, ties.method = "average") / n()) %>%
    ungroup() %>%
    mutate(viral_A = pct_in_age >= 0.90)
}

six_numbers <- function(H) {
  list(n_H = nrow(H),
       so_kenh_trong_H = n_distinct(H$channel_id),
       n_nhom_tuoi_7_10 = sum(H$age_b == "[7,10)"),
       tong_viral_A = sum(H$viral_A),
       trung_vi_lv_adj = round(median(H$lv_adj), 4),
       n_ever_trending_trong_H = sum(H$ever_trending))
}

if (sys.nframe() == 0) {
  H <- prep(read_master()); s <- six_numbers(H)
  cat("data_dir =", data_dir, "\n")
  for (k in names(s)) cat(sprintf("%-28s %s\n", k, format(s[[k]], nsmall = 0)))
  cat(sprintf("viral_A / n_H = %.4f%%  (phải trong 9-11%%)\n", 100 * s$tong_viral_A / s$n_H))
  dir.create(file.path(out_root, "prep"), recursive = TRUE, showWarnings = FALSE)
  readr::write_excel_csv(as.data.frame(c(list(nguon = data_dir), s)),
                         file.path(out_root, "prep", "so_kiem_tra_R.csv"))
}
