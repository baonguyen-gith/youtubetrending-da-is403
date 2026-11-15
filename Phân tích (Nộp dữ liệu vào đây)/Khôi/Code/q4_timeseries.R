# q4_timeseries.R - Q4 chuỗi thời gian (K6, K8), bản R (ngôn ngữ chính). Cùng quy ước với q4_timeseries.py:
# d(S1)=1 trên log(S1); d(S2)=0 trên S2 gốc; lưới p,q in 0..2, P,Q in {0,1}; Ljung-Box lag 14; test 28 ngày; ARIMAX = cấu trúc SARIMA tốt nhất + biến lễ/Tết.
# Dùng: Rscript q4_timeseries.R [series_dir] [out_dir]   (mặc định outputs/series, outputs/q4_R)
invisible(try(Sys.setlocale("LC_ALL", "C.UTF-8"), silent = TRUE))
suppressPackageStartupMessages({ library(forecast); library(tseries); library(data.table) })
set.seed(42)
args <- commandArgs(trailingOnly = TRUE)
SDIR <- if (length(args) >= 1) args[1] else "outputs/series"
OUT <- if (length(args) >= 2) args[2] else "outputs/q4_R"
dir.create(OUT, recursive = TRUE, showWarnings = FALSE)
TEST <- 28; HORIZON <- 28; SEAS <- 7; LB_LAG <- 14
CFG <- list(S1 = list(log = TRUE, d = 1), S2 = list(log = FALSE, d = 0))

daily <- fread(file.path(SDIR, "series_daily.csv")); daily[, date := as.Date(date)]
hol <- fread("holidays_vn.csv", encoding = "UTF-8"); hol[, date := as.Date(date)]
exog_for <- function(dates) cbind(hol_other = as.numeric(dates %in% hol[tet == 0, date]), tet = as.numeric(dates %in% hol[tet == 1, date]))

smape <- function(y, f) mean(2 * abs(y - f) / (abs(y) + abs(f))) * 100
mae <- function(y, f) mean(abs(y - f))
fit_arima <- function(y, order, sorder = c(0, 0, 0), xreg = NULL) {
  seas <- if (any(sorder != 0)) list(order = c(sorder[1], 0, sorder[3]), period = SEAS) else c(0, 0, 0)
  suppressWarnings(Arima(y, order = order, seasonal = seas, xreg = xreg, include.constant = (order[2] == 0), method = "CSS-ML"))
}
safe_p <- function(f, ...) suppressWarnings(tryCatch(f(...)$p.value, error = function(e) NA_real_))

run_long <- function(name) {
  cfg <- CFG[[name]]
  d0 <- daily[!is.na(get(name)), .(date, y = get(name))]
  dates <- d0$date; y_raw <- d0$y
  z <- if (cfg$log) log(y_raw) else y_raw
  n <- length(z); tr <- 1:(n - TEST); te <- (n - TEST + 1):n
  inv <- if (cfg$log) exp else identity
  ex_all <- exog_for(dates)
  # tính dừng
  cands <- list(goc = y_raw); base <- y_raw
  if (cfg$log) { cands$log <- log(y_raw); base <- log(y_raw) }
  cands[[if (cfg$log) "log_sai_phan_1" else "sai_phan_1"]] <- diff(base)
  stat <- rbindlist(lapply(names(cands), function(k) data.table(series = name, transform = k, n = length(cands[[k]]),
            adf_p = safe_p(adf.test, cands[[k]]), kpss_p = safe_p(kpss.test, cands[[k]], null = "Level"))))
  png(file.path(OUT, sprintf("q4_acf_pacf_%s.png", name)), width = 1500, height = 480, res = 150)
  op <- par(mfrow = c(1, 2)); x <- if (cfg$d) diff(z) else z; acf(x, lag.max = 28, main = paste("ACF -", name)); pacf(x, lag.max = 28, main = paste("PACF -", name)); par(op); dev.off()

  res <- list()
  for (fam in c("ARIMA", "SARIMA")) {
    best <- NULL
    for (p in 0:2) for (q in 0:2) {
      combos <- if (fam == "ARIMA") list(c(0, 0, 0)) else list(c(0, 0, 1), c(1, 0, 0), c(1, 0, 1))
      for (so in combos) {
        r <- tryCatch(fit_arima(z[tr], c(p, cfg$d, q), so), error = function(e) NULL)
        if (is.null(r)) next
        if (is.null(best) || r$aic < best$fit$aic) best <- list(fit = r, order = c(p, cfg$d, q), sorder = so)
      }
    }
    res[[fam]] <- best
  }
  so <- res$SARIMA
  res$ARIMAX <- list(fit = fit_arima(z[tr], so$order, so$sorder, ex_all[tr, ]), order = so$order, sorder = so$sorder)

  last_week <- tail(y_raw[tr], SEAS); sn <- rep(last_week, length.out = TEST)
  rows <- list(data.table(series = name, model = "Seasonal naive", order = "-", seasonal = "-", aic = NA_real_,
                          mae_test = mae(y_raw[te], sn), smape_test = smape(y_raw[te], sn), ljungbox_p = NA_real_))
  preds <- list(`Seasonal naive` = data.table(pred = sn, lo = NA_real_, hi = NA_real_))
  for (fam in names(res)) {
    r <- res[[fam]]$fit; o <- res[[fam]]$order; s <- res[[fam]]$sorder
    fc <- forecast(r, h = TEST, xreg = if (fam == "ARIMAX") ex_all[te, ] else NULL, level = 95)
    mean_f <- inv(as.numeric(fc$mean)); lo <- inv(as.numeric(fc$lower)); hi <- inv(as.numeric(fc$upper))
    skip <- max(o[2], 1) + if (s[1] != 0 || s[3] != 0) SEAS else 0
    lb <- Box.test(residuals(r)[-(1:skip)], lag = LB_LAG, type = "Ljung-Box", fitdf = o[1] + o[3] + s[1] + s[3])$p.value
    rows[[length(rows) + 1]] <- data.table(series = name, model = fam, order = sprintf("(%d, %d, %d)", o[1], o[2], o[3]),
        seasonal = if (fam == "ARIMA") "-" else sprintf("(%d, 0, %d, %d)", s[1], s[3], SEAS), aic = r$aic,
        mae_test = mae(y_raw[te], mean_f), smape_test = smape(y_raw[te], mean_f), ljungbox_p = lb)
    preds[[fam]] <- data.table(pred = mean_f, lo = lo, hi = hi)
  }
  comp <- rbindlist(rows)
  cand <- comp[model != "Seasonal naive"]; chosen <- cand[which.min(aic), model]
  sn_mae <- comp[model == "Seasonal naive", mae_test]
  comp[, chon_theo_AIC := model == chosen]
  comp[, tot_hon_seasonal_naive := ifelse(model == "Seasonal naive", NA, mae_test < sn_mae)]
  rx <- res$ARIMAX$fit
  coef <- data.table(series = name, term = names(coef(rx)), coef = as.numeric(coef(rx)), se = sqrt(diag(vcov(rx))))
  # dự báo 4 tuần: khớp lại mô hình đã chọn trên toàn chuỗi
  o <- res[[chosen]]$order; s <- res[[chosen]]$sorder; use_x <- chosen == "ARIMAX"
  rf <- fit_arima(z, o, s, if (use_x) ex_all else NULL)
  fdates <- seq(max(dates) + 1, by = "day", length.out = HORIZON)
  fc <- forecast(rf, h = HORIZON, xreg = if (use_x) exog_for(fdates) else NULL, level = 95)
  pt <- preds[[chosen]]
  out <- rbindlist(list(
    data.table(date = as.character(dates[tr]), set = "train", actual = y_raw[tr]),
    data.table(date = as.character(dates[te]), set = "test", actual = y_raw[te], pred = pt$pred, lo95 = pt$lo, hi95 = pt$hi, snaive = sn),
    data.table(date = as.character(fdates), set = "forecast", pred = inv(as.numeric(fc$mean)), lo95 = inv(as.numeric(fc$lower)), hi95 = inv(as.numeric(fc$upper)))), fill = TRUE)
  out[, model := chosen]
  fwrite(out, file.path(OUT, sprintf("q4_forecast_%s.csv", name)))
  png(file.path(OUT, sprintf("q4_forecast_%s.png", name)), width = 1650, height = 600, res = 150)
  k <- tail(which(out$set != "forecast"), TEST + 90); f <- out[set == "forecast"]; t <- out[set == "test"]
  plot(as.Date(out$date[k]), out$actual[k], type = "l", col = "grey30", xlab = "", ylab = name, xlim = as.Date(c(out$date[k[1]], tail(f$date, 1))),
       ylim = range(c(out$actual[k], f$lo95, f$hi95), na.rm = TRUE), main = sprintf("Du bao %s (%s) - DATA_DIR=%s", name, chosen, Sys.getenv("DATA_DIR", "data_clean_temp")))
  polygon(c(as.Date(f$date), rev(as.Date(f$date))), c(f$lo95, rev(f$hi95)), col = rgb(.17, .42, .69, .2), border = NA)
  lines(as.Date(f$date), f$pred, col = "#2b6cb0", lwd = 2); lines(as.Date(t$date), t$pred, col = "#dd6b20", lwd = 2); lines(as.Date(t$date), t$snaive, col = "grey60", lty = 3)
  dev.off()
  list(stat = stat, comp = comp, coef = coef)
}

run_short <- function(name, s, min_points = 10, test = 5) {
  ok <- !is.na(s$v); if (sum(ok) < min_points)
    return(data.table(series = name, n_points = sum(ok), order = "-", mae_last5 = "-", note = sprintf("không chạy: chỉ %d điểm hợp lệ (< %d); chạy lại trên data_final", sum(ok), min_points)))
  rng <- seq(min(s$date[ok]), max(s$date[ok]), by = "day"); y <- s$v[match(rng, s$date)]
  n <- length(y); tr <- 1:(n - test); te <- (n - test + 1):n; best <- NULL
  for (d in 0:1) for (p in 0:1) for (q in 0:1) {
    r <- tryCatch(suppressWarnings(Arima(y[tr], order = c(p, d, q), include.constant = (d == 0))), error = function(e) NULL)
    if (!is.null(r) && (is.null(best) || r$aic < best$fit$aic)) best <- list(fit = r, order = c(p, d, q))
  }
  fc <- as.numeric(forecast(best$fit, h = test)$mean); m <- !is.na(y[te])
  data.table(series = name, n_points = sum(ok), order = sprintf("(%d, %d, %d)", best$order[1], best$order[2], best$order[3]), mae_last5 = mean(abs(y[te][m] - fc[m])), note = "ngắn hạn, minh họa")
}

all_r <- lapply(c("S1", "S2"), run_long)
stat <- rbindlist(lapply(all_r, `[[`, "stat")); comp <- rbindlist(lapply(all_r, `[[`, "comp")); coefs <- rbindlist(lapply(all_r, `[[`, "coef"))
fwrite(stat, file.path(OUT, "q4_stationarity.csv")); fwrite(comp, file.path(OUT, "q4_model_comparison.csv")); fwrite(coefs, file.path(OUT, "q4_arimax_coef.csv"))
tr <- fread(file.path(SDIR, "series_trending.csv")); tr[, date := as.Date(date)]
short <- rbindlist(list(run_short("N1", tr[, .(date, v = N1)]), run_short("N2", tr[, .(date, v = N2)])), fill = TRUE)
fwrite(short, file.path(OUT, "q4_short_series.csv"))
options(width = 220); print(stat); print(comp); print(short)
