# q2b_anova.R - Q2b: ANOVA một yếu tố của lv_adj theo pub_slot (5 nhóm) và category_name (N5).
# Levene -> ANOVA kinh điển + Welch ANOVA -> Games-Howell (Tukey HSD chỉ đúng khi phương sai đều) -> Kruskal-Wallis.
# Chạy từ 05_Code_Output:  Rscript R/q2b_anova.R
suppressPackageStartupMessages({library(dplyr); library(readr); library(ggplot2); library(car); library(rstatix)})
f <- sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE)); script_dir <- dirname(normalizePath(f))
source(file.path(script_dir, "prep.R"))
set.seed(42)
OUT <- file.path(out_root, "q2b"); dir.create(OUT, recursive = TRUE, showWarnings = FALSE)
ALPHA <- 0.05

group_table <- function(d, col, order) {
  d %>% group_by(group = .data[[col]]) %>%
    summarise(n = n(), mean_lv_adj = mean(lv_adj), sd = sd(lv_adj), median_lv_adj = median(lv_adj), .groups = "drop") %>%
    mutate(group = as.character(group), se = sd / sqrt(n),
           ci_low = mean_lv_adj - qt(0.975, n - 1) * se, ci_high = mean_lv_adj + qt(0.975, n - 1) * se) %>%
    arrange(match(group, order))
}

omnibus <- function(d, col, order, label) {
  d$g <- factor(d[[col]], levels = order); N <- nrow(d); k <- nlevels(d$g)
  lev <- car::leveneTest(lv_adj ~ g, data = d, center = median)
  an <- summary(aov(lv_adj ~ g, data = d))[[1]]
  ssb <- an$`Sum Sq`[1]; sse <- an$`Sum Sq`[2]; sst <- ssb + sse
  wa <- oneway.test(lv_adj ~ g, data = d, var.equal = FALSE)
  kw <- kruskal.test(lv_adj ~ g, data = d)
  data.frame(dataset = label, factor = col, k_groups = k, N = N,
             levene_F = lev$`F value`[1], levene_df1 = lev$Df[1], levene_df2 = lev$Df[2], levene_p = lev$`Pr(>F)`[1],
             anova_F = an$`F value`[1], anova_df1 = an$Df[1], anova_df2 = an$Df[2], anova_p = an$`Pr(>F)`[1],
             eta2 = ssb / sst, omega2 = (ssb - (k - 1) * (sse / (N - k))) / (sst + sse / (N - k)),
             welch_F = unname(wa$statistic), welch_df1 = unname(wa$parameter[1]), welch_df2 = unname(wa$parameter[2]),
             welch_p = wa$p.value, kw_H = unname(kw$statistic), kw_df = unname(kw$parameter), kw_p = kw$p.value,
             eta2_H = (unname(kw$statistic) - k + 1) / (N - k))
}

games_howell <- function(d, col, order, label) {
  d$g <- factor(d[[col]], levels = order)
  gh <- rstatix::games_howell_test(d, lv_adj ~ g)
  st <- group_table(d, col, order) %>% as.data.frame(); rownames(st) <- st$group
  gh %>% rowwise() %>% mutate(
    a = if (match(group1, order) < match(group2, order)) group1 else group2,
    b = if (match(group1, order) < match(group2, order)) group2 else group1,
    diff = st[a, "mean_lv_adj"] - st[b, "mean_lv_adj"],
    flip = if (a == group1) 1 else -1,
    # rstatix: estimate = mean(group2) - mean(group1)  =>  diff(a-b) = flip * (-estimate)
    ci_low_ = if (flip == 1) -conf.high else conf.low, ci_high_ = if (flip == 1) -conf.low else conf.high,
    sp = sqrt((st[a, "sd"]^2 + st[b, "sd"]^2) / 2)) %>% ungroup() %>%
    transmute(dataset = label, factor = col, group1 = a, group2 = b,
              n1 = st[a, "n"], n2 = st[b, "n"], diff = diff, ci_low = ci_low_, ci_high = ci_high_,
              p_adj = p.adj, d_pair = diff / sp, significant = p.adj < ALPHA)
}

plot_means <- function(gm, suffix, fname, n_total) {
  gm <- gm %>% mutate(fac_lab = ifelse(factor == "pub_slot", "Khung giờ đăng", "Thể loại"),
                      lab = sprintf("%s (n=%s)", group, format(n, big.mark = ",", trim = TRUE)))
  gm <- gm %>% group_by(factor) %>% mutate(lab = factor(lab, levels = lab[if (factor[1] == "category_name") order(mean_lv_adj) else rev(seq_along(lab))])) %>% ungroup()
  p <- ggplot(gm, aes(mean_lv_adj, lab)) + geom_vline(xintercept = 0, linetype = "dashed", colour = "grey50") +
    geom_errorbarh(aes(xmin = ci_low, xmax = ci_high), height = 0.25, colour = "#1f77b4") + geom_point(colour = "#1f77b4") +
    facet_wrap(~fac_lab, scales = "free_y") +
    labs(title = paste("Q2b – Trung bình lv_adj theo nhóm", suffix), x = "Trung bình lv_adj (KTC 95%)", y = NULL,
         caption = sprintf("Nguồn: %s/videos_master.csv, H (n_H = %s); outputs/q2b/q2b_group_means.csv", data_dir, format(n_total, big.mark = ","))) +
    theme_bw(base_size = 10)
  ggsave(file.path(OUT, fname), p, width = 12, height = 5.2, dpi = 300)
}

H <- prep(read_master())
cat(sprintf("n_H = %d  (data_dir=%s)\n", nrow(H), data_dir))
subsets <- list(H_toan_bo = H, H_bo_video_ngan = H %>% filter(!is_short_60))
omn <- list(); means <- list(); pairs <- list(); dropped <- list()
for (label in names(subsets)) {
  d0 <- subsets[[label]]
  for (fac in c("pub_slot", "category_name")) {
    if (fac == "pub_slot") { order <- SLOT_ORDER; d <- d0 } else {
      cnt <- table(d0$category_name); order <- sort(names(cnt)[cnt >= MIN_GROUP_N], method = "radix")
      for (cc in names(cnt)[cnt < MIN_GROUP_N]) dropped[[length(dropped) + 1]] <- data.frame(dataset = label, factor = fac, group = cc, n = as.integer(cnt[cc]), ly_do = paste0("n < ", MIN_GROUP_N))
      d <- d0 %>% filter(category_name %in% order)
    }
    stopifnot(all(d[[fac]] %in% order))
    omn[[length(omn) + 1]] <- omnibus(d, fac, order, label)
    gt <- group_table(d, fac, order) %>% mutate(dataset = label, factor = fac, .before = 1)
    means[[length(means) + 1]] <- gt
    pairs[[length(pairs) + 1]] <- games_howell(d, fac, order, label)
  }
}
omn <- bind_rows(omn); means <- bind_rows(means); pairs <- bind_rows(pairs)
write_excel_csv(omn, file.path(OUT, "q2b_anova_results_R.csv"))
write_excel_csv(means, file.path(OUT, "q2b_group_means_full_R.csv"))
# CSV cho Power BI (mục 0.5): factor, group, n, mean_lv_adj, ci_low, ci_high  (quần thể H đầy đủ; bản R là bản chính)
write_excel_csv(means %>% filter(dataset == "H_toan_bo") %>% select(factor, group, n, mean_lv_adj, ci_low, ci_high),
                file.path(OUT, "q2b_group_means.csv"))
write_excel_csv(pairs, file.path(OUT, "q2b_gameshowell_all_R.csv"))
write_excel_csv(pairs %>% filter(significant) %>% arrange(dataset, factor, p_adj), file.path(OUT, "q2b_gameshowell_significant_R.csv"))
write_excel_csv(if (length(dropped)) distinct(bind_rows(dropped)) else data.frame(dataset = character(), factor = character(), group = character(), n = integer(), ly_do = character()),
                file.path(OUT, "q2b_dropped_groups_R.csv"))
print(t(omn)); print(pairs %>% group_by(dataset, factor) %>% summarise(sig = sum(significant), n_pairs = n(), .groups = "drop"))

plot_means(means %>% filter(dataset == "H_toan_bo"), "(toàn bộ quần thể H)", "q2b_group_means_R.png", nrow(H))
plot_means(means %>% filter(dataset == "H_bo_video_ngan"), "(bỏ video ngắn ≤ 60 giây)", "q2b_group_means_noshort_R.png", sum(!H$is_short_60))
writeLines(capture.output(sessionInfo()), file.path(OUT, "env_R.txt"))
