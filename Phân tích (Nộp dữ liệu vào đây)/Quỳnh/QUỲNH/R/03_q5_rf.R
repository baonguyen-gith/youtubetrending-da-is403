# -*- coding: utf-8 -*-
# =============================================================================
# 03_q5_rf.R
# -----------------------------------------------------------------------------
# Q5 - Đối chiếu Random Forest giữa Python và R (nhãn viral_A, fold 1).
#
# Dữ liệu vào : 05_Code_Output/outputs/5.5 Q5/q5_model_data_viral_A.csv
#               (do 03_q5_forecast.py xuất: video_id, channel_id, pub_date_vn,
#                y, fold, X_PRE đã one-hot category_id; UTF-8 có BOM)
# Kết quả     : 05_Code_Output/outputs/5.5 Q5/q5_R_check.txt
#
# Cấu hình R trùng với Python:
#   ntree = 300, nodesize = 5, mtry = floor(sqrt(p)), set.seed(42)
#   train = fold != 1, test = fold == 1
# Tiêu chí đạt: |AUC_R - AUC_Python| <= 0,03 (theo yêu cầu Mục 5.5).
#
# Chạy: "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" 05_Code_Output/R/03_q5_rf.R
# =============================================================================

args_all <- commandArgs(trailingOnly = FALSE)
file_arg <- sub("^--file=", "", args_all[grep("^--file=", args_all)])
script_dir <- if (length(file_arg)) dirname(normalizePath(file_arg)) else getwd()
project_dir <- dirname(dirname(script_dir))
q5_dir <- file.path(project_dir, "05_Code_Output", "outputs", "5.5 Q5")

if (!requireNamespace("randomForest", quietly = TRUE)) {
  stop("Thiếu gói randomForest. Cài bằng: install.packages('randomForest')")
}
suppressPackageStartupMessages(library(randomForest))

data_path <- file.path(q5_dir, "q5_model_data_viral_A.csv")
if (!file.exists(data_path)) {
  stop("Không thấy ", data_path, " - hãy chạy 03_q5_forecast.py trước.")
}

cat("Đọc dữ liệu:", data_path, "\n")
d <- read.csv(data_path, check.names = FALSE, stringsAsFactors = FALSE,
              fileEncoding = "UTF-8-BOM")

meta <- c("video_id", "channel_id", "pub_date_vn", "y", "fold")
feats <- setdiff(names(d), meta)

train <- d[d$fold != 1, , drop = FALSE]
test  <- d[d$fold == 1, , drop = FALSE]

if (nrow(train) == 0 || nrow(test) == 0) stop("Fold 1 rỗng - kiểm tra cột fold.")

y_tr <- as.integer(train$y)
y_te <- as.integer(test$y)

cat(sprintf("Train: %s dòng (%s dương) | Test: %s dòng (%s dương) | p = %d\n",
            format(nrow(train), big.mark = ","), format(sum(y_tr), big.mark = ","),
            format(nrow(test), big.mark = ","), format(sum(y_te), big.mark = ","),
            length(feats)))

auc_rank <- function(y, p) {
  n1 <- sum(y == 1)
  n0 <- sum(y == 0)
  if (n1 == 0 || n0 == 0) return(NA_real_)
  r <- rank(p, ties.method = "average")
  (sum(r[y == 1]) - n1 * (n1 + 1) / 2) / (n1 * n0)
}

set.seed(42)
t0 <- Sys.time()
rf <- randomForest(
  x = train[, feats, drop = FALSE],
  y = as.factor(y_tr),
  ntree = 300,
  nodesize = 5,
  mtry = floor(sqrt(length(feats))),
  importance = FALSE,
  na.action = na.omit
)
elapsed <- as.numeric(difftime(Sys.time(), t0, units = "secs"))

p_te <- predict(rf, test[, feats, drop = FALSE], type = "prob")[, "1"]
auc_r <- auc_rank(y_te, p_te)

# ---- AUC của Python (fold 1) ----
cv_path <- file.path(q5_dir, "q5_cv_folds.csv")
auc_py <- NA_real_
if (file.exists(cv_path)) {
  cv <- read.csv(cv_path, fileEncoding = "UTF-8-BOM", check.names = FALSE)
  sel <- cv$label == "viral_A" & cv$fold == 1 & cv$model == "Random Forest"
  if (any(sel)) auc_py <- cv$roc_auc[which(sel)[1]]
}
diff_auc <- abs(auc_r - auc_py)
pass <- !is.na(auc_py) && diff_auc <= 0.03

lines <- c(
  "======================================================================",
  "Q5 - ĐỐI CHIẾU RANDOM FOREST: PYTHON vs R",
  "======================================================================",
  paste0("Thời điểm chạy     : ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  paste0("R version          : ", R.version.string),
  paste0("randomForest       : ", as.character(packageVersion("randomForest"))),
  paste0("Dữ liệu            : ", basename(data_path)),
  paste0("Nhãn               : viral_A"),
  paste0("Fold đối chiếu     : 1 / 5 (GroupKFold theo channel_id)"),
  paste0("Số đặc trưng       : ", length(feats)),
  paste0("Train              : ", format(nrow(train), big.mark = ","),
         " dòng (", format(sum(y_tr), big.mark = ","), " dương)"),
  paste0("Test               : ", format(nrow(test), big.mark = ","),
         " dòng (", format(sum(y_te), big.mark = ","), " dương)"),
  paste0("Cấu hình           : ntree=300, nodesize=5, mtry=",
         floor(sqrt(length(feats))), ", seed=42"),
  paste0("Thời gian huấn luyện: ", sprintf("%.1f", elapsed), " giây"),
  "----------------------------------------------------------------------",
  paste0("ROC-AUC Python     : ", sprintf("%.4f", auc_py)),
  paste0("ROC-AUC R          : ", sprintf("%.4f", auc_r)),
  paste0("Chênh lệch |ΔAUC|  : ", sprintf("%.4f", diff_auc),
         " (ngưỡng cho phép: 0,03)"),
  paste0("KẾT LUẬN           : ", ifelse(pass, "PASS", "FAIL")),
  "----------------------------------------------------------------------",
  "Ghi chú:",
  "- AUC tính bằng công thức hạng (Mann-Whitney U), tương đương roc_auc_score.",
  "- Python dùng class_weight='balanced_subsample'; R không có tùy chọn tương",
  "  đương trực tiếp nên chênh lệch nhỏ về AUC là chấp nhận được (<= 0,03).",
  "- SVM và XGBoost chỉ chạy Python theo quy ước của nhóm.",
  "======================================================================"
)

out_path <- file.path(q5_dir, "q5_R_check.txt")
writeLines(lines, out_path, useBytes = TRUE)
cat(paste(lines, collapse = "\n"), "\n")
cat("Đã ghi:", out_path, "\n")
