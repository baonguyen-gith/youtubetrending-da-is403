# -*- coding: utf-8 -*-
# =============================================================================
# 04_q6_kmeans.R
# -----------------------------------------------------------------------------
# Q6 - Đối chiếu K-means giữa Python và R.
#
# Dữ liệu vào : 05_Code_Output/outputs/5.6 Q6/q6_R_input.csv
#               (do 04_q6_kmeans.py xuất: video_id, cluster, z_<6 biến>;
#                6 biến đã StandardScaler trong chính Python, UTF-8 có BOM)
# Kết quả     : 05_Code_Output/outputs/5.6 Q6/q6_R_check.txt
#
# Cấu hình R trùng với Python:
#   k = số cụm Python đã chọn (đọc từ q6_k_selection.csv)
#   kmeans(x, centers = k, nstart = 10, iter.max = 300, algorithm = "Hartigan-Wong")
#   set.seed(42)
# Tiêu chí đạt: ARI(R, Python) >= 0,8 (theo yêu cầu Mục 5.6).
#
# ARI tính thủ công từ bảng đếm chéo (adjusted Rand index) để không phụ thuộc
# package ngoài; công thức Hubert & Arabie (1985).
#
# Chạy: "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" 05_Code_Output/R/04_q6_kmeans.R
# =============================================================================

args_all <- commandArgs(trailingOnly = FALSE)
file_arg <- sub("^--file=", "", args_all[grep("^--file=", args_all)])
script_dir <- if (length(file_arg)) dirname(normalizePath(file_arg[1], winslash = "/")) else getwd()
proj <- normalizePath(file.path(script_dir, "..", ".."), winslash = "/")
out_dir <- file.path(proj, "05_Code_Output", "outputs", "5.6 Q6")

in_csv <- file.path(out_dir, "q6_R_input.csv")
sel_csv <- file.path(out_dir, "q6_k_selection.csv")
out_txt <- file.path(out_dir, "q6_R_check.txt")

lines <- character(0)
say <- function(...) {
  txt <- paste0(...)
  cat(txt, "\n", sep = "")
  lines <<- c(lines, txt)
}

say("=================================================================")
say("Q6 - DOI CHIEU K-MEANS PYTHON vs R")
say(format(Sys.time(), "Thoi diem chay: %d/%m/%Y %H:%M"))
say("=================================================================")

if (!file.exists(in_csv)) {
  say("KHONG TIM THAY: ", in_csv)
  say("Hay chay 04_q6_kmeans.py truoc.")
  writeLines(lines, out_txt, useBytes = TRUE)
  quit(status = 1)
}

d <- read.csv(in_csv, fileEncoding = "UTF-8-BOM", check.names = FALSE,
              stringsAsFactors = FALSE)
z_cols <- grep("^z_", names(d), value = TRUE)
say("Du lieu vao          : ", basename(in_csv))
say("So video             : ", format(nrow(d), big.mark = ","))
say("So bien dung de cum  : ", length(z_cols), " (", paste(z_cols, collapse = ", "), ")")

X <- as.matrix(d[, z_cols, drop = FALSE])
storage.mode(X) <- "double"

# k do Python chon
k <- NA_integer_
if (file.exists(sel_csv)) {
  sel <- read.csv(sel_csv, fileEncoding = "UTF-8-BOM", stringsAsFactors = FALSE)
  if ("chon" %in% names(sel)) {
    k <- as.integer(sel$k[which(as.logical(sel$chon))[1]])
  }
}
if (is.na(k)) {
  k <- length(unique(d$cluster))
  say("Khong doc duoc cot 'chon' trong q6_k_selection.csv -> dung k = so cum Python (", k, ")")
} else {
  say("k (Python chon)      : ", k)
}

# ---------------------------------------------------------------------------
# K-means trong R
# ---------------------------------------------------------------------------
set.seed(42)
t0 <- Sys.time()
km <- kmeans(X, centers = k, nstart = 10, iter.max = 300,
             algorithm = "Hartigan-Wong")
elapsed <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
lab_r <- as.integer(km$cluster)

say("Thuat toan           : Hartigan-Wong, nstart = 10, iter.max = 300, seed = 42")
say("Thoi gian chay       : ", sprintf("%.1f giay", elapsed))
say("Within-cluster SS    : ", format(km$tot.withinss, big.mark = ",", digits = 6))
say("So video moi cum (R) : ", paste(tabulate(lab_r, nbins = k), collapse = " / "))

# ---------------------------------------------------------------------------
# ARI thu cong (Hubert & Arabie 1985)
# ---------------------------------------------------------------------------
ari <- function(a, b) {
  tab <- table(a, b)
  n <- sum(tab)
  c2 <- function(x) x * (x - 1) / 2
  sum_ij <- sum(c2(tab))
  sum_a <- sum(c2(rowSums(tab)))
  sum_b <- sum(c2(colSums(tab)))
  expect <- sum_a * sum_b / c2(n)
  max_idx <- (sum_a + sum_b) / 2
  (sum_ij - expect) / (max_idx - expect)
}

lab_py <- as.integer(d$cluster)
ari_val <- ari(lab_py, lab_r)

tab <- table(Python = lab_py, R = lab_r)
say("")
say("Bang doi chieu so video (Python x R):")
print_tab <- capture.output(print(tab))
lines <- c(lines, print_tab)
cat(print_tab, sep = "\n")

say("")
say("ARI (Python vs R)    : ", sprintf("%.4f", ari_val))

# do "thuan" cua tung cum: cum R trung voi cum Python nao nhieu nhat
match_rate <- mean(apply(tab, 1, function(r) max(r)) / rowSums(tab)) * 100
say("Ty le video duoc xep cung nhom voi cum tuong ung (best match): ",
    sprintf("%.2f%%", match_rate))

threshold <- 0.8
say("Nguong chap nhan     : ARI >= ", sprintf("%.1f", threshold))
say("")
if (ari_val >= threshold) {
  say("KET LUAN             : PASS")
  say("- Hai cach cai dat K-means (Python scikit-learn va R stats::kmeans)")
  say("  cho ra cung mot cach phan cum tren thuc te.")
} else {
  say("KET LUAN             : FAIL")
  say("- ARI duoi nguong. Kiem tra lai: so bien, chuan hoa, k, hoac thu")
  say("  algorithm = 'Lloyd' / tang nstart truoc khi ket luan sai khac.")
}
say("")
say("- ARI = 1 khi hai cach chia giong het; ARI ~ 0 khi giong ngau nhien.")
say("- Lech nho (0,8-1,0) la binh thuong vi kmeans cua R va sklearn khoi tao")
say("  tam cum khac nhau; chi so sanh nhan cuoi cung, khong so sanh tam cum.")

con <- file(out_txt, open = "wb")
writeLines(enc2utf8(lines), con, useBytes = TRUE)
close(con)
cat("\nDa ghi: ", out_txt, "\n", sep = "")
