# =============================================================================
# 01_check_labels.R
# -----------------------------------------------------------------------------
# MUC DICH: Doc lai 05_Code_Output/outputs/4.4 labels/labels.csv do Python tao va KIEM TRA
#           CHEO (khong tao lai file, khong ghi de labels.csv).
#
# Chay trong RStudio: mo file nay -> Source (Ctrl+Shift+S)
# Chay bang command line:
#   "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" 05_Code_Output/R/01_check_labels.R
#
# Script chi dung base R, khong can cai them package.
# =============================================================================

options(stringsAsFactors = FALSE)

# ---------------------------------------------------------------------------
# 1. Tim thu muc goc cua do an
# ---------------------------------------------------------------------------
get_script_dir <- function() {
  if (requireNamespace("rstudioapi", quietly = TRUE) &&
      rstudioapi::isAvailable()) {
    p <- rstudioapi::getSourceEditorContext()$path
    if (nzchar(p)) {
      return(dirname(normalizePath(p, winslash = "/", mustWork = FALSE)))
    }
  }
  args <- commandArgs(trailingOnly = FALSE)
  m <- grep("^--file=", args, value = TRUE)
  if (length(m) > 0) {
    p <- sub("^--file=", "", m[1])
    return(dirname(normalizePath(p, winslash = "/", mustWork = FALSE)))
  }
  getwd()
}

find_project_dir <- function(start) {
  candidates <- unique(c(
    normalizePath(file.path(start, "..", ".."), winslash = "/", mustWork = FALSE),
    normalizePath(start, winslash = "/", mustWork = FALSE),
    normalizePath(getwd(), winslash = "/", mustWork = FALSE)
  ))
  for (d in candidates) {
    if (file.exists(file.path(d, "05_Code_Output", "outputs", "4.4 labels", "labels.csv"))) {
      return(d)
    }
  }
  stop(
    "Khong tim thay 05_Code_Output/outputs/4.4 labels/labels.csv.\n",
    "Hay mo RStudio tai thu muc Do an, hoac setwd() ve thu muc chua videos_master.csv."
  )
}

script_dir  <- get_script_dir()
project_dir <- find_project_dir(script_dir)
out_dir     <- file.path(project_dir, "05_Code_Output", "outputs")
labels_dir  <- file.path(out_dir, "4.4 labels")

labels_path  <- file.path(labels_dir, "labels.csv")
summary_path <- file.path(labels_dir, "labels_summary.csv")
trend_path   <- file.path(project_dir, "trending_clean.csv")
log_path     <- file.path(labels_dir, "labels_check_R.txt")

cat("Project:", project_dir, "\n")
cat("Reading:", labels_path, "\n")

# ---------------------------------------------------------------------------
# 2. Doc du lieu (labels.csv co UTF-8 BOM)
# ---------------------------------------------------------------------------
lb <- read.csv(labels_path, fileEncoding = "UTF-8-BOM",
               na.strings = c("", "NA"), check.names = FALSE)

# Python ghi True/False (chu hoa dau tu), R chi hieu TRUE/FALSE.
# Chuyen cac cot logic ve logical that.
as_bool <- function(x) {
  if (is.logical(x)) return(x)
  x <- as.character(x)
  out <- rep(NA, length(x))
  out[x %in% c("True", "TRUE", "true", "1")]  <- TRUE
  out[x %in% c("False", "FALSE", "false", "0")] <- FALSE
  out
}

for (col in c("in_H", "is_short_60", "ever_trending", "in_window_C")) {
  lb[[col]] <- as_bool(lb[[col]])
}

h <- lb[lb$in_H %in% TRUE, ]

# ---------------------------------------------------------------------------
# 3. Tinh lai bo 6 so kiem tra (Bang 4.3)
# ---------------------------------------------------------------------------
n_H          <- nrow(h)
n_channels   <- length(unique(h$channel_id))
n_age_7_10   <- sum(h$age_b == "[7,10)", na.rm = TRUE)
viral_A_pos  <- sum(h$viral_A == 1, na.rm = TRUE)

h$lv_adj <- h$log_views -
  ave(h$log_views, h$age_b, FUN = function(x) mean(x, na.rm = TRUE))
median_lv_adj <- round(median(h$lv_adj, na.rm = TRUE), 4)

ever_trending_H <- sum(h$ever_trending %in% TRUE, na.rm = TRUE)

checks <- c(
  "1. n_H"                          = n_H,
  "2. So kenh trong H"              = n_channels,
  "3. So video nhom [7,10)"         = n_age_7_10,
  "4. Tong viral_A"                 = viral_A_pos,
  "5. Trung vi lv_adj (4 chu so)"   = median_lv_adj,
  "6. ever_trending trong H"        = ever_trending_H
)

# ---------------------------------------------------------------------------
# 4. Bang tom tat nhan (Bang 5.12)
# ---------------------------------------------------------------------------
r_summary <- data.frame(
  label = c("viral_A", "breakout_B", "viral_C"),
  eligible_n = c(
    sum(!is.na(h$viral_A)),
    sum(!is.na(h$breakout_B)),
    sum(!is.na(h$viral_C))
  ),
  positive_n = c(
    sum(h$viral_A == 1, na.rm = TRUE),
    sum(h$breakout_B == 1, na.rm = TRUE),
    sum(h$viral_C == 1, na.rm = TRUE)
  ),
  stringsAsFactors = FALSE
)
r_summary$positive_rate <- round(r_summary$positive_n / r_summary$eligible_n, 6)

# ---------------------------------------------------------------------------
# 5. Kiem tra cong thuc tung nhan
# ---------------------------------------------------------------------------
# 5a. viral_A = (pct_in_age >= 0.90)
idx <- !is.na(h$viral_A)
viral_A_ok <- all(h$viral_A[idx] == as.integer(h$pct_in_age[idx] >= 0.90))

# 5b. breakout_B = (lvpd - ch_med_loo >= log10(2))
idx <- !is.na(h$breakout_B)
diff_b <- h$lvpd[idx] - h$ch_med_loo[idx]
thr    <- log10(2)
# bo qua cac diem sat nguong do lam tron 6 chu so trong CSV
near   <- abs(abs(diff_b) - thr) < 1e-5
breakout_ok <- all(
  h$breakout_B[idx][!near] == as.integer(diff_b[!near] >= thr)
)
n_near_threshold <- sum(near)

# 5c. viral_C = ever_trending trong in_window_C
idx <- !is.na(h$viral_C)
viral_C_ok <- all(h$viral_C[idx] == as.integer(h$ever_trending[idx] %in% TRUE))

# 5d. in_window_C dung cong thuc
tr <- read.csv(trend_path, fileEncoding = "UTF-8-BOM")
last_trending <- max(as.Date(tr$run_date), na.rm = TRUE)
window_start  <- as.Date("2026-10-19")
window_end    <- last_trending - 8

pub <- as.Date(h$pub_date_vn)
expected_window <- !is.na(pub) &
  pub >= window_start & pub <= window_end &
  h$is_short_60 %in% FALSE
window_ok <- all(expected_window == (h$in_window_C %in% TRUE))

# 5e. age_b dung 14 nhom [a,b)
breaks <- c(1, 2, 3, 5, 7, 10, 14, 21, 30, 60, 90, 180, 365, 730, Inf)
labs <- c("[1,2)", "[2,3)", "[3,5)", "[5,7)", "[7,10)", "[10,14)", "[14,21)",
          "[21,30)", "[30,60)", "[60,90)", "[90,180)", "[180,365)",
          "[365,730)", "[730,inf)")
age_re <- cut(h$age_days_last, breaks = breaks, right = FALSE,
              labels = labs, include.lowest = TRUE)
age_ok <- all(as.character(age_re) == h$age_b)

# 5f. Kiem tra 1 nhom leave-one-out median
split_idx <- split(seq_len(nrow(h)), paste(h$channel_id, h$age_b, sep = "|"))
loo_ok <- NA
for (g in split_idx) {
  if (length(g) >= 8) {
    v <- h$lvpd[g]
    i <- 4L
    expected <- median(v[-i])
    got <- h$ch_med_loo[g[i]]
    loo_ok <- isTRUE(all.equal(expected, got, tolerance = 1e-6))
    break
  }
}

# ---------------------------------------------------------------------------
# 6. So sanh voi ket qua Python (labels_summary.csv)
# ---------------------------------------------------------------------------
py_summary <- read.csv(summary_path, fileEncoding = "UTF-8-BOM",
                       na.strings = c("", "NA"), check.names = FALSE)
cmp <- merge(r_summary, py_summary, by = "label", suffixes = c("_R", "_Py"))
cmp <- cmp[match(r_summary$label, cmp$label), ]

summary_ok <- all(
  cmp$eligible_n_R == cmp$eligible_n_Py &
    cmp$positive_n_R == cmp$positive_n_Py &
    abs(cmp$positive_rate_R - cmp$positive_rate_Py) < 1e-6
)

# ---------------------------------------------------------------------------
# 7. Ghi log
# ---------------------------------------------------------------------------
pass <- function(x) if (isTRUE(x)) "PASS" else "FAIL"

fmt_so <- function(x) {
  if (is.na(x)) return("NA")
  if (abs(x - round(x)) < 1e-9) {
    formatC(round(x), format = "d", big.mark = ".", decimal.mark = ",")
  } else {
    formatC(x, format = "f", digits = 4, big.mark = ".", decimal.mark = ",")
  }
}

lines <- c(
  "# Kiem tra cheo labels.csv bang R",
  "",
  paste("Thoi diem:", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  paste("R:", R.version.string),
  paste("File:", labels_path),
  "",
  "## Bo 6 so kiem tra (Bang 4.3)",
  "",
  "| # | So can in ra | Gia tri |",
  "|---|---|---:|",
  sprintf("| %s | %s | %s |",
          sub("\\..*$", "", names(checks)),
          sub("^[0-9]+\\. ", "", names(checks)),
          vapply(checks, fmt_so, character(1))),
  "",
  "## Bang tom tat nhan (Bang 5.12)",
  "",
  "| Nhan | Du dieu kien | Duong | Ty le duong |",
  "|---|---:|---:|---:|",
  sprintf("| %s | %s | %s | %.2f%% |",
          r_summary$label,
          formatC(r_summary$eligible_n, format = "d", big.mark = ".", decimal.mark = ","),
          formatC(r_summary$positive_n, format = "d", big.mark = ".", decimal.mark = ","),
          100 * r_summary$positive_rate),
  "",
  "## Kiem tra cong thuc",
  "",
  sprintf("- viral_A = (pct_in_age >= 0.90): %s", pass(viral_A_ok)),
  sprintf("- breakout_B = (lvpd - ch_med_loo >= log10(2)): %s", pass(breakout_ok)),
  sprintf("  (so diem sat nguong do lam tron, da bo qua: %d)", n_near_threshold),
  sprintf("- viral_C = ever_trending trong in_window_C: %s", pass(viral_C_ok)),
  sprintf("- in_window_C dung cong thuc: %s", pass(window_ok)),
  sprintf("- age_b dung 14 nhom [a,b): %s", pass(age_ok)),
  sprintf("- leave-one-out median (1 nhom mau): %s", pass(loo_ok)),
  "",
  "## So sanh voi ket qua Python",
  "",
  sprintf("- labels_summary.csv khop: %s", pass(summary_ok)),
  "",
  "## Cua so in_window_C",
  "",
  sprintf("- Bat dau: %s", window_start),
  sprintf("- Ket thuc: %s (Trending cuoi %s tru 8 ngay)", window_end, last_trending),
  "",
  "## Ket luan",
  "",
  if (all(c(viral_A_ok, breakout_ok, viral_C_ok, window_ok, age_ok,
            summary_ok, isTRUE(loo_ok)))) {
    "TAT CA KIEM TRA DAT: labels.csv do Python tao nhat quan voi cong thuc."
  } else {
    "CO KIEM TRA KHONG DAT: xem chi tiet o tren."
  }
)

con <- file(log_path, open = "w", encoding = "UTF-8")
writeLines(lines, con)
close(con)

cat("\n")
cat(paste(lines, collapse = "\n"), "\n")
cat("\nDa ghi log:", log_path, "\n")

# Ma thoat khac 0 neu co loi, chi ap dung khi chay bang Rscript (khong quit RStudio)
all_ok <- all(c(viral_A_ok, breakout_ok, viral_C_ok, window_ok, age_ok,
                summary_ok, isTRUE(loo_ok)))
if (!all_ok && !interactive()) quit(status = 1)
