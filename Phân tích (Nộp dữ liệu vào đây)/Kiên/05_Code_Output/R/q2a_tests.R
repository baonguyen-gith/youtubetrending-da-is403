# q2a_tests.R - Q2a: t-test lv_adj giữa video đăng cuối tuần và ngày thường (N4).
# Chạy từ 05_Code_Output:  Rscript R/q2a_tests.R
# Đầu ra: outputs/q2a/ (CSV *_R.csv, hình *_R.png)
suppressPackageStartupMessages({library(dplyr); library(readr); library(ggplot2); library(car); library(effectsize)
                                library(sandwich); library(lmtest)})
f <- sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE)); script_dir <- dirname(normalizePath(f))
source(file.path(script_dir, "prep.R"))
set.seed(42)
OUT <- file.path(out_root, "q2a"); dir.create(OUT, recursive = TRUE, showWarnings = FALSE)

cohen_d_ci <- function(x, y) {
  n1 <- length(x); n2 <- length(y)
  d <- effectsize::cohens_d(x, y, pooled_sd = TRUE)$Cohens_d      # (x - y) / sd gộp
  se <- sqrt((n1 + n2) / (n1 * n2) + d^2 / (2 * (n1 + n2)))       # cùng công thức Hedges-Olkin như bản Python
  c(d = d, lo = d - qnorm(0.975) * se, hi = d + qnorm(0.975) * se)
}

run_tests <- function(d, label) {
  x <- d$lv_adj[d$pub_is_weekend]; y <- d$lv_adj[!d$pub_is_weekend]   # chênh lệch = cuối tuần - ngày thường
  w <- t.test(x, y, var.equal = FALSE)
  dd <- cohen_d_ci(x, y)
  lev <- car::leveneTest(lv_adj ~ factor(pub_is_weekend), data = d, center = median)
  mw <- wilcox.test(x, y, exact = FALSE, correct = TRUE)
  data.frame(dataset = label, n_weekend = length(x), n_weekday = length(y),
             mean_weekend = mean(x), mean_weekday = mean(y), sd_weekend = sd(x), sd_weekday = sd(y),
             median_weekend = median(x), median_weekday = median(y),
             diff_mean = mean(x) - mean(y), ci_low = w$conf.int[1], ci_high = w$conf.int[2],
             welch_t = unname(w$statistic), welch_df = unname(w$parameter), welch_p = w$p.value,
             cohen_d = unname(dd["d"]), d_ci_low = unname(dd["lo"]), d_ci_high = unname(dd["hi"]),
             levene_F = lev$`F value`[1], levene_df1 = lev$Df[1], levene_df2 = lev$Df[2], levene_p = lev$`Pr(>F)`[1],
             mw_U = unname(mw$statistic), mw_p = mw$p.value,
             cliffs_delta = 2 * unname(mw$statistic) / (length(x) * length(y)) - 1)
}

cluster_ols <- function(d, label, demean = FALSE) {
  y <- d$lv_adj; x <- as.numeric(d$pub_is_weekend); g <- d$channel_id
  if (demean) {
    y <- y - ave(y, g); x <- x - ave(x, g)
    m <- lm(y ~ 0 + x); nm <- "x"
  } else {
    m <- lm(y ~ x); nm <- "x"
  }
  V <- sandwich::vcovCL(m, cluster = g, type = "HC1", cadjust = TRUE)
  ct <- lmtest::coeftest(m, vcov. = V, df = Inf)          # suy luận chuẩn (z), như statsmodels use_t = FALSE
  ci <- lmtest::coefci(m, vcov. = V, df = Inf)[nm, ]
  data.frame(dataset = label, model = if (demean) "FE_theo_kenh" else "OLS_cluster", n = length(y),
             n_clusters = length(unique(g)), coef = ct[nm, 1], se = ct[nm, 2], z = ct[nm, 3], p = ct[nm, 4],
             ci_low = ci[1], ci_high = ci[2], row.names = NULL)
}

H <- prep(read_master())
cat(sprintf("n_H = %d  (data_dir=%s)\n", nrow(H), data_dir))
subsets <- list(H_toan_bo = H, H_bo_video_ngan = H %>% filter(!is_short_60))
res <- bind_rows(lapply(names(subsets), function(k) run_tests(subsets[[k]], k)))
readr::write_excel_csv(res, file.path(OUT, "q2a_results_R.csv"))
cl <- bind_rows(lapply(names(subsets), function(k) bind_rows(cluster_ols(subsets[[k]], k, FALSE), cluster_ols(subsets[[k]], k, TRUE))))
readr::write_excel_csv(cl, file.path(OUT, "q2a_cluster_R.csv"))
desc <- H %>% group_by(pub_is_weekend) %>% summarise(n = n(), mean = mean(lv_adj), median = median(lv_adj), sd = sd(lv_adj))
readr::write_excel_csv(desc, file.path(OUT, "q2a_descriptives_R.csv"))
print(t(res)); print(cl)

src <- sprintf("Nguồn: %s/videos_master.csv, quần thể H (n_H = %s); outputs/q2a/", data_dir, format(nrow(H), big.mark = ","))
H <- H %>% mutate(nhom = factor(ifelse(pub_is_weekend, "Cuối tuần", "Ngày thường"), levels = c("Ngày thường", "Cuối tuần")))
nn <- table(H$nhom)
H2 <- H %>% mutate(nhom_lab = factor(sprintf("%s (n = %s)", nhom, format(nn[as.character(nhom)], big.mark = ",")),
                                     levels = sprintf("%s (n = %s)", names(nn), format(nn, big.mark = ","))))
p1 <- ggplot(H2, aes(sample = lv_adj)) + stat_qq(size = 0.3, alpha = 0.4, colour = "#1f77b4") + stat_qq_line(colour = "#d62728") +
  facet_wrap(~nhom_lab) + labs(title = "Q2a – QQ-plot của lv_adj theo nhóm ngày đăng", x = "Phân vị lý thuyết (chuẩn)",
                               y = "lv_adj (log10 lượt xem đã hiệu chỉnh tuổi)", caption = src) + theme_bw(base_size = 11)
ggsave(file.path(OUT, "q2a_qqplot_R.png"), p1, width = 10, height = 4.6, dpi = 300)
mu <- H %>% group_by(nhom) %>% summarise(m = mean(lv_adj))
r <- res[1, ]
p2 <- ggplot(H, aes(lv_adj, fill = nhom, colour = nhom)) +
  geom_histogram(aes(y = after_stat(density)), breaks = seq(-5, 5, length.out = 101), alpha = 0.5, position = "identity", colour = NA) +
  geom_vline(data = mu, aes(xintercept = m, colour = nhom), linewidth = 0.8) +
  scale_fill_manual(values = c("#1f77b4", "#ff7f0e"), labels = sprintf("%s (TB = %.3f)", mu$nhom, mu$m)) +
  scale_colour_manual(values = c("#1f77b4", "#ff7f0e"), guide = "none") + coord_cartesian(xlim = c(-5, 5)) +
  labs(title = sprintf("Q2a – Phân phối lv_adj: chênh lệch TB = %.3f, Cohen's d = %.3f", r$diff_mean, r$cohen_d),
       x = "lv_adj", y = "Mật độ", fill = NULL, caption = paste0(src, "q2a_results_R.csv")) + theme_bw(base_size = 11) +
  theme(legend.position = "bottom")
ggsave(file.path(OUT, "q2a_distribution_R.png"), p2, width = 7.5, height = 4.6, dpi = 300)

writeLines(c(capture.output(sessionInfo())), file.path(OUT, "env_R.txt"))
