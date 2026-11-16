# q3b_logistic.R - Q3b hồi quy Logistic cho viral_A (việc B5), bản R tương đương python/q3b_logistic.py
# Cần: readr, dplyr, sandwich, lmtest.   Chạy:  Rscript q3b_logistic.R
# Thiết kế GIỐNG Python: z-score (sd n-1) cho biến số; nhị phân giữ 0/1; duration -> log10(max(x,1)); total_videos -> log10(x+1);
# thể loại < 100 video gộp "Khác" (nếu nhóm "Khác" < 100 video thì bỏ hẳn); nhóm gốc = thể loại đông nhất.
# SE bền vững theo kênh: sandwich::vcovCL(cluster = ~channel_id), mặc định type "HC1" có hiệu chỉnh G/(G-1)*(N-1)/(N-K).
# Python (statsmodels) dùng cùng dạng hiệu chỉnh; nếu CI lệch > 0,01 ghi nguyên nhân trong báo cáo.
suppressPackageStartupMessages({ library(dplyr); library(sandwich); library(lmtest) })
source("prep.R")
OUT_DIR <- Sys.getenv("OUT_DIR", unset = file.path("..", "outputs", "q3b_R")); dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)
MIN_CAT <- 100
BINARY  <- c("pub_is_weekend","is_short_60","title_has_question","title_has_exclaim","title_has_digit","title_has_emoji","title_has_bracket","title_has_pipe")
NUMERIC <- c("pub_hour","pub_dow","pub_month","duration_log","tags_count","title_len","title_words","title_upper_ratio",
             "title_n_hashtag","log_subs","channel_age_days","total_videos_log")
CHANNEL_GROUP <- c("log_subs","channel_age_days","total_videos_log")

H <- prep(load_master())
d <- H %>% mutate(duration_log = log10(pmax(duration_sec, 1)), total_videos_log = log10(total_videos + 1),
                  across(all_of(BINARY), as.numeric)) %>%
  filter(if_all(all_of(c(NUMERIC, BINARY, "category_name", "viral_A", "channel_id")), ~ !is.na(.x)))
vc <- table(d$category_name); small <- names(vc)[vc < MIN_CAT]
d$cat <- ifelse(d$category_name %in% small, "Khác", d$category_name)
n_khac <- sum(d$cat == "Khác"); if (n_khac > 0 && n_khac < MIN_CAT) d <- d[d$cat != "Khác", ]
ref <- names(sort(table(d$cat), decreasing = TRUE))[1]
cats <- setdiff(sort(unique(d$cat)), ref)
cat("n_H =", nrow(H), "| n dung =", nrow(d), "| nhom goc the loai =", ref, "| so cum kenh =", n_distinct(d$channel_id), "\n")

Z <- as.data.frame(lapply(d[, NUMERIC], function(x) as.numeric(scale(x))))   # scale(): sd mẫu n-1
D <- cbind(Z, d[, BINARY])
for (c in cats) D[[paste0("cat: ", c)]] <- as.numeric(d$cat == c)
names(D) <- make.names(names(D), unique = TRUE)
D$y <- d$viral_A

fit_model <- function(vars) {
  f <- as.formula(paste("y ~", paste(vars, collapse = " + ")))
  m <- glm(f, data = D, family = binomial())
  vc <- vcovCL(m, cluster = d$channel_id)           # cluster-robust theo channel_id
  ct <- coeftest(m, vcov. = vc)
  tab <- data.frame(term = rownames(ct), coef = ct[, 1], se_cluster = ct[, 2], z = ct[, 3], p = ct[, 4])
  tab$OR <- exp(tab$coef); tab$OR_lo95 <- exp(tab$coef - 1.96 * tab$se_cluster); tab$OR_hi95 <- exp(tab$coef + 1.96 * tab$se_cluster)
  list(model = m, tab = tab)
}
all_vars <- setdiff(names(D), "y")
m1 <- fit_model(all_vars)
m2 <- fit_model(setdiff(all_vars, make.names(CHANNEL_GROUP)))

mcfadden <- function(m) 1 - as.numeric(logLik(m)) / as.numeric(logLik(update(m, . ~ 1)))
fit <- data.frame(model = c("M1", "M2"), n = nobs(m1$model), n_pos = sum(D$y),
                  AIC = c(AIC(m1$model), AIC(m2$model)), McFadden_R2 = c(mcfadden(m1$model), mcfadden(m2$model)))

vif_manual <- function(vars) sapply(vars, function(v) { r2 <- summary(lm(as.formula(paste(v, "~", paste(setdiff(vars, v), collapse = " + "))), data = D))$r.squared; 1 / (1 - r2) })
vif1 <- data.frame(term = all_vars, VIF = vif_manual(all_vars))

write.csv(m1$tab, file.path(OUT_DIR, "q3b_coef_M1_R.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(m2$tab, file.path(OUT_DIR, "q3b_coef_M2_R.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(fit,    file.path(OUT_DIR, "q3b_model_fit_R.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(vif1,   file.path(OUT_DIR, "q3b_vif_M1_R.csv"), row.names = FALSE, fileEncoding = "UTF-8")
print(fit); print(
  transform(
    m1$tab[, c("term", "OR", "OR_lo95", "OR_hi95", "p")],
    OR = round(OR, 3),
    OR_lo95 = round(OR_lo95, 3),
    OR_hi95 = round(OR_hi95, 3),
    p = signif(p, 3)
  )
); cat("VIF > 5:\n"); print(vif1[vif1$VIF > 5, ])
