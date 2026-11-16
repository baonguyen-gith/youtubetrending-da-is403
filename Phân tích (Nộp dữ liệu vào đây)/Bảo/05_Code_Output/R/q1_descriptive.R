# q1_descriptive.R - Q1 thống kê mô tả (việc B4): bản R, dùng để VẼ HÌNH và đối chiếu số với Python
# Quy ước công thức GIỐNG HỆT python/q1_descriptive.py:
#   sd mẫu (n-1); CV = sd/mean; độ lệch g1 = m3/m2^1.5; độ nhọn dư g2 = m4/m2^2 - 3 (mô-men, không hiệu chỉnh mẫu)
# Chạy:  Rscript q1_descriptive.R     (cần: readr, dplyr, tidyr, ggplot2)
suppressPackageStartupMessages({ library(dplyr); library(tidyr); library(ggplot2) })
source("prep.R")

OUT_DIR <- Sys.getenv("OUT_DIR", unset = file.path("..", "outputs", "q1_R"))
dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)
MIN_CELL <- 30
DOW_LAB <- c("T2", "T3", "T4", "T5", "T6", "T7", "CN")

skew_g1 <- function(x) { m <- mean(x); m2 <- mean((x - m)^2); mean((x - m)^3) / m2^1.5 }
kurt_g2 <- function(x) { m <- mean(x); m2 <- mean((x - m)^2); mean((x - m)^4) / m2^2 - 3 }
desc <- function(x) { x <- x[!is.na(x)]
  tibble(n = length(x), mean = mean(x), median = median(x), sd = sd(x), cv = sd(x) / mean(x),
         skew = skew_g1(x), kurtosis_excess = kurt_g2(x)) }

H <- prep(load_master())
H$lv_within_ch <- H$lv_adj - ave(H$lv_adj, H$channel_id, FUN = median)
cat("n_H =", nrow(H), "\n")

# (a) bảng mô tả --------------------------------------------------------------
groups <- list(`Tất cả` = H, `Video ngắn (<=60s)` = filter(H, is_short_60), `Video dài (>60s)` = filter(H, !is_short_60))
vars <- c(views = "Lượt xem", likes = "Lượt thích", comments = "Bình luận")
ta <- bind_rows(lapply(names(groups), function(gn) bind_rows(lapply(names(vars), function(v) {
  x <- groups[[gn]][[v]]
  bind_rows(bind_cols(nhom = gn, bien = paste0(vars[[v]], " (gốc)"), desc(x)),
            bind_cols(nhom = gn, bien = paste0(vars[[v]], " (log10)"), desc(log10(x[!is.na(x) & x > 0]))))
}))))
write.csv(ta, file.path(OUT_DIR, "q1_descriptive_table.csv"), row.names = FALSE, fileEncoding = "UTF-8")

# (b) theo giờ / thứ / tháng ---------------------------------------------------
smry <- function(d, key) d %>% group_by(across(all_of(key))) %>%
  summarise(n = n(), median_lv_adj = median(lv_adj), mean_lv_adj = mean(lv_adj),
            median_lv_within_channel = median(lv_within_ch),
            n_like_rate = sum(!is.na(like_rate)), median_like_rate = median(like_rate, na.rm = TRUE), .groups = "drop")
by_hour <- smry(H, "pub_hour"); by_dow <- smry(H, "pub_dow")
H$ym <- substr(as.character(H$pub_date_vn), 1, 7); by_month <- smry(H, "ym")
stopifnot(sum(by_hour$n) == nrow(H), sum(by_dow$n) == nrow(H), sum(by_month$n) == nrow(H))
write.csv(by_hour,  file.path(OUT_DIR, "q1_by_hour.csv"),  row.names = FALSE, fileEncoding = "UTF-8")
write.csv(by_dow,   file.path(OUT_DIR, "q1_by_dow.csv"),   row.names = FALSE, fileEncoding = "UTF-8")
write.csv(by_month, file.path(OUT_DIR, "q1_by_month.csv"), row.names = FALSE, fileEncoding = "UTF-8")

# (c) heatmap giờ x thứ ----------------------------------------------------------
cell <- H %>% group_by(pub_hour, pub_dow) %>% summarise(n = n(), median_lv_adj = median(lv_adj), .groups = "drop") %>%
  mutate(masked = ifelse(n >= MIN_CELL, median_lv_adj, NA_real_))
write.csv(cell, file.path(OUT_DIR, "q1_heatmap.csv"), row.names = FALSE, fileEncoding = "UTF-8")
lim <- max(abs(cell$masked), na.rm = TRUE)
p_heat <- ggplot(cell, aes(factor(pub_dow, labels = DOW_LAB), factor(pub_hour, levels = 23:0), fill = masked)) +
  geom_tile(colour = "white") + geom_text(aes(label = ifelse(is.na(masked), "", sprintf("%.2f", masked))), size = 2.3) +
  scale_fill_gradient2(low = "#2166AC", mid = "white", high = "#B2182B", midpoint = 0, limits = c(-lim, lim), na.value = "white") +
  labs(x = "Thứ đăng", y = "Giờ đăng (giờ Việt Nam)", fill = "Trung vị lv_adj",
       title = sprintf("Trung vị lv_adj theo giờ x thứ (ô trắng: n < %d)", MIN_CELL)) + theme_minimal(base_size = 11)
ggsave(file.path(OUT_DIR, "q1_heatmap.png"), p_heat, width = 7, height = 7, dpi = 150)

# (d) boxplot 10 thể loại nhiều video nhất -----------------------------------------
top10 <- H %>% count(category_name, sort = TRUE) %>% slice_head(n = 10) %>% pull(category_name)
p_box <- H %>% filter(category_name %in% top10) %>%
  mutate(category_name = factor(category_name, levels = top10)) %>%
  ggplot(aes(category_name, lv_adj)) + geom_boxplot(outlier.shape = NA, fill = "#9FC3E8") +
  geom_hline(yintercept = 0, linetype = "dashed", colour = "grey50") + coord_cartesian(ylim = c(-4, 3.2)) +
  labs(x = NULL, y = "lv_adj", title = "Phân bố lv_adj theo 10 thể loại có nhiều video nhất") +
  theme_minimal(base_size = 11) + theme(axis.text.x = element_text(angle = 35, hjust = 1))
ggsave(file.path(OUT_DIR, "q1_box_category.png"), p_box, width = 9, height = 5, dpi = 150)

p_hour <- ggplot(by_hour, aes(pub_hour, median_lv_adj)) + geom_line(colour = "#1F5FA8") + geom_point(colour = "#1F5FA8") +
  geom_line(aes(y = median_lv_within_channel), colour = "#C0392B", linetype = "dashed") +
  geom_hline(yintercept = 0, colour = "grey50", linetype = "dashed") +
  labs(x = "Giờ đăng (giờ Việt Nam)", y = "Trung vị lv_adj", title = "Trung vị lv_adj theo giờ đăng (đỏ: sau khi trừ trung vị của kênh)") +
  theme_minimal(base_size = 11)
ggsave(file.path(OUT_DIR, "q1_by_hour.png"), p_hour, width = 8, height = 4, dpi = 150)
cat("Xong. File ở:", normalizePath(OUT_DIR), "\n")
