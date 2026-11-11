# q3a_regression.R - Q3a: hồi quy tuyến tính bội cho log_views (N6).
# log_views ~ log10(age_days_last) + log_subs + log10(duration_sec) + tags_count + title_len + title_upper_ratio
#             + title_has_question + title_has_exclaim + title_has_digit + title_has_emoji
#             + pub_is_weekend + pub_slot + category_name + is_short_60
# Sai số chuẩn bền vững theo kênh: sandwich::vcovCL(cluster = channel_id). Nhóm tham chiếu: pub_slot = "Tối 18-21h", category = "Gaming".
# Chạy từ 05_Code_Output:  Rscript R/q3a_regression.R
suppressPackageStartupMessages({library(dplyr); library(readr); library(ggplot2); library(sandwich); library(lmtest)})
f <- sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE)); script_dir <- dirname(normalizePath(f))
source(file.path(script_dir, "prep.R"))
set.seed(42)
OUT <- file.path(out_root, "q3a"); dir.create(OUT, recursive = TRUE, showWarnings = FALSE)
REF_SLOT <- "Tối 18-21h"; REF_CAT <- "Gaming"

NUM_TERMS <- c("log10(age_days_last)", "log_subs", "log10(duration_sec)", "tags_count", "title_len", "title_upper_ratio",
               "title_has_question", "title_has_exclaim", "title_has_digit", "title_has_emoji", "pub_is_weekend", "is_short_60")
ALL_TERMS <- c(NUM_TERMS, "pub_slot", "category_name")
PROTECTED <- "log10(age_days_last)"
GROUPS <- list(kenh = "log_subs",
               noi_dung = c("log10(duration_sec)", "tags_count", "title_len", "title_upper_ratio", "title_has_question",
                            "title_has_exclaim", "title_has_digit", "title_has_emoji", "is_short_60"),
               thoi_gian = c("pub_is_weekend", "pub_slot"), the_loai = "category_name")

canon <- function(n) { n <- sub("^pub_slot", "pub_slot=", n); n <- sub("^category_name", "category=", n); sub("\\(Intercept\\)", "Intercept", n) }
fml <- function(terms) as.formula(paste("log_views ~", paste(terms, collapse = " + ")))

H <- prep(read_master())
cat(sprintf("n_H = %d  (data_dir=%s)\n", nrow(H), data_dir))
cnt <- table(H$category_name); keep <- names(cnt)[cnt >= MIN_GROUP_N]; dropped <- cnt[cnt < MIN_GROUP_N]
D <- H %>% filter(category_name %in% keep) %>%
  mutate(across(c(title_has_question, title_has_exclaim, title_has_digit, title_has_emoji, pub_is_weekend, is_short_60), as.numeric),
         pub_slot = relevel(factor(pub_slot, levels = SLOT_ORDER), ref = REF_SLOT),
         category_name = relevel(factor(category_name), ref = REF_CAT))
stopifnot(!anyNA(D$pub_slot), all(D$duration_sec > 0))
cat(sprintf("Loại %d video thuộc thể loại n<%d; n mô hình = %d\n", sum(dropped), MIN_GROUP_N, nrow(D)))

# --- VIF: cột (diag của nghịch đảo ma trận tương quan) và theo term (GVIF; adj_vif = GVIF^(1/df)) ---
vif_tables <- function(terms) {
  mm <- model.matrix(fml(terms), D)[, -1, drop = FALSE]
  R <- cor(mm); vcol <- data.frame(column = canon(colnames(mm)), vif = diag(solve(R)))
  # gán cột cho term: số cột của từng term
  k_of <- sapply(terms, function(t) if (t == "pub_slot") nlevels(D$pub_slot) - 1 else if (t == "category_name") nlevels(D$category_name) - 1 else 1)
  rows <- list(); start <- 0; detR <- det(R)
  for (t in terms) {
    idx <- (start + 1):(start + k_of[[t]]); rest <- setdiff(seq_len(ncol(R)), idx)
    gv <- det(R[idx, idx, drop = FALSE]) * (if (length(rest)) det(R[rest, rest, drop = FALSE]) else 1) / detR
    rows[[t]] <- data.frame(term = t, df = k_of[[t]], gvif = gv, adj_vif = gv^(1 / k_of[[t]])); start <- start + k_of[[t]]
  }
  list(vcol = vcol, vterm = bind_rows(rows))
}
terms <- ALL_TERMS; removed <- character()
repeat {
  vt <- vif_tables(terms)
  cand <- vt$vterm %>% filter(!term %in% PROTECTED) %>% arrange(desc(adj_vif))
  if (cand$adj_vif[1] > 10) { removed <- c(removed, cand$term[1]); terms <- setdiff(terms, cand$term[1]) } else break
}
vterm <- vt$vterm %>% mutate(vuot_5 = adj_vif > 5, vuot_10 = adj_vif > 10)
write_excel_csv(vt$vcol, file.path(OUT, "q3a_vif_columns_R.csv"))
write_excel_csv(vterm, file.path(OUT, "q3a_vif_R.csv"))

m <- lm(fml(terms), data = D)
V <- sandwich::vcovCL(m, cluster = D$channel_id, type = "HC1", cadjust = TRUE)
ct <- lmtest::coeftest(m, vcov. = V, df = Inf); ci <- lmtest::coefci(m, vcov. = V, df = Inf)
se_ols <- summary(m)$coefficients[, 2]
mm <- model.matrix(m)
sdx <- apply(mm, 2, sd); sdy <- sd(D$log_views)
coef_tbl <- data.frame(term = canon(rownames(ct)), coef = unname(ct[, 1]), se_ols = unname(se_ols), se_cluster = unname(ct[, 2]),
                       z_cluster = unname(ct[, 3]), p_cluster = unname(ct[, 4]), ci_low = unname(ci[, 1]), ci_high = unname(ci[, 2]))
coef_tbl$beta_std <- ifelse(coef_tbl$term == "Intercept", NA, coef_tbl$coef * sdx[rownames(ct)] / sdy)
coef_tbl$ti_so_se <- coef_tbl$se_cluster / coef_tbl$se_ols
write_excel_csv(coef_tbl, file.path(OUT, "q3a_coefficients_R.csv"))

sm_ <- summary(m)
model_tbl <- data.frame(n = nobs(m), k_tham_so = length(coef(m)), n_clusters = length(unique(D$channel_id)), r2 = sm_$r.squared,
                        adj_r2 = sm_$adj.r.squared, rmse = sqrt(mean(resid(m)^2)), residual_sd = sm_$sigma, bien_bi_loai_do_VIF = if (length(removed)) paste(removed, collapse = ";") else "khong",
                        n_video_bi_loai_the_loai_nho = sum(dropped))
write_excel_csv(model_tbl, file.path(OUT, "q3a_model_R.csv"))

# --- đóng góp theo nhóm ---
r2 <- function(tt) summary(lm(fml(tt), data = D))$r.squared
r2_full <- sm_$r.squared; r2_age <- r2("log10(age_days_last)")
contrib <- bind_rows(lapply(names(GROUPS), function(gn) {
  gt <- intersect(GROUPS[[gn]], terms); rest <- setdiff(terms, gt)
  r2_wo <- r2(rest); r2_only <- r2(c("log10(age_days_last)", gt))
  data.frame(nhom = gn, bien = paste(gt, collapse = ";"), R2_day_du = r2_full, R2_khi_bo_nhom = r2_wo, giam_R2 = r2_full - r2_wo,
             R2_chi_age_va_nhom = r2_only, tang_R2_so_voi_chi_age = r2_only - r2_age)
})) %>% arrange(desc(giam_R2))
write_excel_csv(contrib, file.path(OUT, "q3a_group_contribution_R.csv"))
write_excel_csv(data.frame(R2_chi_log10_age = r2_age), file.path(OUT, "q3a_r2_age_only_R.csv"))
print(model_tbl); print(coef_tbl %>% mutate(across(where(is.numeric), ~round(.x, 4)))); print(vterm); print(contrib %>% select(-bien))
cat("R2 chỉ gồm log10(age):", round(r2_age, 4), "\n")

# --- hình chẩn đoán ---
src <- sprintf("Nguồn: %s/videos_master.csv, H; outputs/q3a/", data_dir)
rs <- resid(m); fv <- fitted(m)
dq <- data.frame(q = qnorm((rank(rs) - 0.5) / length(rs)), r = rs / sd(rs))
p1 <- ggplot(dq, aes(q, r)) + geom_point(size = 0.3, alpha = 0.3, colour = "#1f77b4") + geom_abline(colour = "#d62728") +
  labs(title = "QQ-plot phần dư", x = "Phân vị lý thuyết (chuẩn)", y = "Phần dư chuẩn hóa") + theme_bw(base_size = 11)
s <- sample(length(rs), min(20000, length(rs)))
p2 <- ggplot(data.frame(fv = fv[s], r = rs[s]), aes(fv, r)) + geom_point(size = 0.4, alpha = 0.3, colour = "#1f77b4") +
  geom_hline(yintercept = 0, colour = "#d62728") +
  labs(title = "Phần dư theo giá trị dự đoán (mẫu 20.000 điểm)", x = "Giá trị dự đoán của log_views", y = "Phần dư") + theme_bw(base_size = 11)
png(file.path(OUT, "q3a_diagnostics_R.png"), width = 11, height = 4.8, units = "in", res = 300, type = "cairo")
grid::grid.newpage(); grid::pushViewport(grid::viewport(layout = grid::grid.layout(2, 2, heights = grid::unit(c(0.1, 0.9), "npc"))))
grid::grid.text(sprintf("Q3a – Chẩn đoán phần dư (n = %s; R² = %.3f)", format(nobs(m), big.mark = ","), r2_full), gp = grid::gpar(fontsize = 13),
                vp = grid::viewport(layout.pos.row = 1, layout.pos.col = 1:2))
print(p1, vp = grid::viewport(layout.pos.row = 2, layout.pos.col = 1)); print(p2, vp = grid::viewport(layout.pos.row = 2, layout.pos.col = 2))
grid::grid.text(src, x = 0.01, y = 0.01, just = c("left", "bottom"), gp = grid::gpar(fontsize = 6, col = "gray40"))
dev.off()

# --- hình đóng góp theo nhóm + hệ số chuẩn hóa ---
c1 <- ggplot(contrib, aes(giam_R2, reorder(nhom, giam_R2))) + geom_col(fill = "#1f77b4") + geom_text(aes(label = sprintf("%.3f", giam_R2)), hjust = -0.1, size = 3) +
  scale_x_continuous(expand = expansion(mult = c(0, 0.15))) + labs(title = "Đóng góp của từng nhóm nhân tố", x = "Mức giảm R² khi bỏ nhóm", y = NULL) + theme_bw(base_size = 11)
b <- coef_tbl %>% filter(term != "Intercept", !grepl("=", term))
c2 <- ggplot(b, aes(beta_std, reorder(term, beta_std), fill = beta_std >= 0)) + geom_col(show.legend = FALSE) + scale_fill_manual(values = c("#d62728", "#1f77b4")) +
  labs(title = "Biến số / nhị phân (không gồm thể loại, khung giờ)", x = "Hệ số chuẩn hóa (β*)", y = NULL) + theme_bw(base_size = 10)
png(file.path(OUT, "q3a_contribution_R.png"), width = 12, height = 5, units = "in", res = 300, type = "cairo")
grid::grid.newpage(); grid::pushViewport(grid::viewport(layout = grid::grid.layout(2, 2, heights = grid::unit(c(0.1, 0.9), "npc"))))
grid::grid.text("Q3a – Nhân tố nào mạnh nhất?", gp = grid::gpar(fontsize = 13), vp = grid::viewport(layout.pos.row = 1, layout.pos.col = 1:2))
print(c1, vp = grid::viewport(layout.pos.row = 2, layout.pos.col = 1)); print(c2, vp = grid::viewport(layout.pos.row = 2, layout.pos.col = 2))
grid::grid.text(paste0(src, "q3a_group_contribution_R.csv"), x = 0.01, y = 0.01, just = c("left", "bottom"), gp = grid::gpar(fontsize = 6, col = "gray40"))
dev.off()
writeLines(capture.output(sessionInfo()), file.path(OUT, "env_R.txt"))
