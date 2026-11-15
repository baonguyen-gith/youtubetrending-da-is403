# =============================================================================
# 02_q2c_chisq.R
# -----------------------------------------------------------------------------
# MUC DICH: Kiem tra cheo Q2c (Chi-square the loai x kha nang lot Trending)
#           so voi ket qua Python trong 05_Code_Output/outputs/5.2c q2c/.
#
# Script KHONG tao lai labels.csv; chi doc labels.csv + videos_master.csv,
# tinh lai chi2, df, p, Cramer's V, phan du chuan hoa va so sanh.
#
# Chay trong RStudio: mo file -> Source (Ctrl+Shift+S)
# Chay command line:
#   "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" 05_Code_Output/R/02_q2c_chisq.R
# =============================================================================

options(stringsAsFactors = FALSE)

# ---------------------------------------------------------------------------
# 1. Tim thu muc goc
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
  stop("Khong tim thay 05_Code_Output/outputs/4.4 labels/labels.csv. Hay setwd() ve thu muc Do an.")
}

script_dir  <- get_script_dir()
project_dir <- find_project_dir(script_dir)
out_dir     <- file.path(project_dir, "05_Code_Output", "outputs")
labels_dir  <- file.path(out_dir, "4.4 labels")
q2c_dir     <- file.path(out_dir, "5.2c q2c")
table_dir   <- file.path(q2c_dir, "tables")
log_path    <- file.path(q2c_dir, "q2c_R_check.txt")

cat("Project:", project_dir, "\n")

# ---------------------------------------------------------------------------
# 2. Doc du lieu
# ---------------------------------------------------------------------------
lb <- read.csv(file.path(labels_dir, "labels.csv"), fileEncoding = "UTF-8-BOM",
               na.strings = c("", "NA"), check.names = FALSE)
vm <- read.csv(file.path(project_dir, "videos_master.csv"),
               fileEncoding = "UTF-8-BOM", check.names = FALSE,
               colClasses = c(video_id = "character",
                              category_name = "character"))
vm <- vm[, c("video_id", "category_name")]

df <- merge(lb, vm, by = "video_id", all.x = TRUE, sort = FALSE)
if (any(is.na(df$category_name))) stop("Co video thieu category_name")

as_bool <- function(x) {
  if (is.logical(x)) return(x)
  x <- as.character(x)
  out <- rep(NA, length(x))
  out[x %in% c("True", "TRUE", "true", "1")]   <- TRUE
  out[x %in% c("False", "FALSE", "false", "0")] <- FALSE
  out
}
for (col in c("in_H", "is_short_60", "in_window_C")) {
  df[[col]] <- as_bool(df[[col]])
}

h <- df[df$in_H %in% TRUE, ]

# ---------------------------------------------------------------------------
# 3. Ham phan tich giong Python
# ---------------------------------------------------------------------------
analyze_pair <- function(d, label_col, pair_name) {
  d <- d[!is.na(d[[label_col]]), c("category_name", label_col)]
  d[[label_col]] <- as.integer(d[[label_col]])

  obs <- table(d$category_name, d[[label_col]])
  for (cl in c("0", "1")) {
    if (!cl %in% colnames(obs)) obs <- cbind(obs, matrix(0, nrow(obs), 1,
                                                         dimnames = list(rownames(obs), cl)))
  }
  obs <- obs[, c("0", "1"), drop = FALSE]

  # Lan 1: expected tren bang day du
  test0 <- suppressWarnings(chisq.test(obs, correct = FALSE))
  exp0  <- test0$expected
  bad   <- apply(exp0 < 5, 1, any)
  merged <- rownames(obs)[bad]

  if (any(bad)) {
    other <- colSums(obs[bad, , drop = FALSE])
    obs2 <- rbind(obs[!bad, , drop = FALSE], "Khác" = other)
  } else {
    obs2 <- obs
  }

  test <- suppressWarnings(chisq.test(obs2, correct = FALSE))
  n    <- sum(obs2)
  chi2 <- unname(test$statistic)
  dof  <- unname(test$parameter)
  p    <- test$p.value
  v    <- sqrt(chi2 / (n * (min(dim(obs2)) - 1)))

  list(pair = pair_name, obs = obs2, exp = test$expected,
       resid = test$residuals, n = n, chi2 = chi2, df = dof, p = p,
       v = v, min_expected = min(test$expected),
       n_cells_lt5 = sum(test$expected < 5),
       merged = merged)
}

res_c <- analyze_pair(
  h[h$in_window_C %in% TRUE, ], "viral_C", "category_name x viral_C"
)
res_a <- analyze_pair(h, "viral_A", "category_name x viral_A")
res_a_ns <- analyze_pair(
  h[h$is_short_60 %in% FALSE, ], "viral_A",
  "category_name x viral_A (non-short)"
)
h_drop <- h[h$category_name != "Nonprofits & Activism", ]
res_a_drop <- analyze_pair(
  h_drop, "viral_A", "category_name x viral_A (drop sparse)"
)
res_a_ns_drop <- analyze_pair(
  h_drop[h_drop$is_short_60 %in% FALSE, ], "viral_A",
  "category_name x viral_A (non-short, drop sparse)"
)

r_tests <- data.frame(
  pair = c(res_c$pair, res_a$pair, res_a_ns$pair,
           res_a_drop$pair, res_a_ns_drop$pair),
  n = c(res_c$n, res_a$n, res_a_ns$n, res_a_drop$n, res_a_ns_drop$n),
  chi2 = c(res_c$chi2, res_a$chi2, res_a_ns$chi2,
           res_a_drop$chi2, res_a_ns_drop$chi2),
  df = c(res_c$df, res_a$df, res_a_ns$df, res_a_drop$df, res_a_ns_drop$df),
  p = c(res_c$p, res_a$p, res_a_ns$p, res_a_drop$p, res_a_ns_drop$p),
  v = c(res_c$v, res_a$v, res_a_ns$v, res_a_drop$v, res_a_ns_drop$v),
  stringsAsFactors = FALSE
)

# ---------------------------------------------------------------------------
# 4. So sanh voi Python
# ---------------------------------------------------------------------------
py_tests <- read.csv(file.path(table_dir, "q2c_tests.csv"),
                     fileEncoding = "UTF-8-BOM", check.names = FALSE)

cmp <- merge(r_tests, py_tests, by = "pair", suffixes = c("_R", "_Py"))
cmp <- cmp[match(r_tests$pair, cmp$pair), ]

tests_ok <- all(
  cmp$n_R == cmp$n_Py &
    abs(cmp$chi2_R - cmp$chi2_Py) < 1e-6 &
    cmp$df_R == cmp$df_Py &
    abs(cmp$p_R - cmp$p_Py) < 1e-12 &
    abs(cmp$v_R - cmp$v_Py) < 1e-6
)

drop_total <- function(x) x[rownames(x) != "T\u1ed5ng", , drop = FALSE]

read_py_resid <- function(file) {
  x <- read.csv(file.path(table_dir, file), fileEncoding = "UTF-8-BOM",
                row.names = 1, check.names = FALSE)
  drop_total(x)
}
py_res_c <- read_py_resid("q2c_residuals_viral_C.csv")
py_res_a <- read_py_resid("q2c_residuals_viral_A.csv")

cmp_resid <- function(r_res, py_res) {
  cats <- rownames(r_res$resid)
  all(cats %in% rownames(py_res)) &&
    isTRUE(all.equal(as.numeric(r_res$resid[, "1"]),
                     as.numeric(py_res[cats, "resid_1"]),
                     tolerance = 1e-6, check.attributes = FALSE))
}
resid_c_ok <- cmp_resid(res_c, py_res_c)
resid_a_ok <- cmp_resid(res_a, py_res_a)

read_py_obs <- function(file) {
  x <- read.csv(file.path(table_dir, file), fileEncoding = "UTF-8-BOM",
                row.names = 1, check.names = FALSE)
  drop_total(x)
}
py_obs_c <- read_py_obs("q2c_table_viral_C.csv")
py_obs_a <- read_py_obs("q2c_table_viral_A.csv")

cmp_obs <- function(r_res, py_obs) {
  cats <- rownames(r_res$obs)
  all(cats %in% rownames(py_obs)) &&
    isTRUE(all.equal(as.numeric(r_res$obs[, "1"]),
                     as.numeric(py_obs[cats, "1"]),
                     tolerance = 1e-9, check.attributes = FALSE))
}
obs_c_ok <- cmp_obs(res_c, py_obs_c)
obs_a_ok <- cmp_obs(res_a, py_obs_a)

# ---------------------------------------------------------------------------
# 5. Ghi log
# ---------------------------------------------------------------------------
pass <- function(x) if (isTRUE(x)) "PASS" else "FAIL"
most_over <- function(res) {
  r <- res$resid[, "1"]
  names(r)[which.max(r)]
}
fmt_num <- function(x, digits = 3) {
  formatC(x, format = "f", digits = digits, big.mark = ".",
          decimal.mark = ",", drop0trailing = TRUE)
}
fmt_p <- function(p) {
  if (is.na(p)) return("NA")
  if (p == 0) return("< 1e-300")
  formatC(p, format = "e", digits = 3)
}

lines <- c(
  "# Kiem tra cheo Q2c bang R",
  "",
  paste("Thoi diem:", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  paste("R:", R.version.string),
  "",
  "## Bang 5.4 (R tinh lai)",
  "",
  "| Cap bien | n | chi2 | df | p | Cramer's V | The loai vuot ky vong |",
  "|---|---:|---:|---:|---:|---:|---|",
  sprintf("| %s | %s | %s | %d | %s | %s | %s |",
          r_tests$pair,
          formatC(r_tests$n, format = "d", big.mark = ".", decimal.mark = ","),
          fmt_num(r_tests$chi2, 3),
          r_tests$df,
          vapply(r_tests$p, fmt_p, character(1)),
          fmt_num(r_tests$v, 3),
          vapply(list(res_c, res_a, res_a_ns, res_a_drop, res_a_ns_drop),
                 most_over, character(1))),
  "",
  "## So sanh voi Python",
  "",
  sprintf("- Bang thong ke (n, chi2, df, p, V): %s", pass(tests_ok)),
  sprintf("- Bang quan sat viral_C: %s", pass(obs_c_ok)),
  sprintf("- Bang quan sat viral_A: %s", pass(obs_a_ok)),
  sprintf("- Phan du chuan hoa viral_C: %s", pass(resid_c_ok)),
  sprintf("- Phan du chuan hoa viral_A: %s", pass(resid_a_ok)),
  "",
  "## The loai bi gop vao Khác",
  "",
  sprintf("- viral_C: %s", paste(res_c$merged, collapse = "; ")),
  sprintf("- viral_A: %s", paste(res_a$merged, collapse = "; ")),
  "",
  "## Ket luan",
  "",
  if (all(tests_ok, obs_c_ok, obs_a_ok, resid_c_ok, resid_a_ok)) {
    "TAT CA KIEM TRA DAT: ket qua R khop voi Python."
  } else {
    "CO KIEM TRA KHONG DAT: xem chi tiet o tren."
  }
)

con <- file(log_path, open = "w", encoding = "UTF-8")
writeLines(lines, con)
close(con)

cat(paste(lines, collapse = "\n"), "\n")
cat("\nDa ghi log:", log_path, "\n")

all_ok <- all(tests_ok, obs_c_ok, obs_a_ok, resid_c_ok, resid_a_ok)
if (!all_ok && !interactive()) quit(status = 1)

