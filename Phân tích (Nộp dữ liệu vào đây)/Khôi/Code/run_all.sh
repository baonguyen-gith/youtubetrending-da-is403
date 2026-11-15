#!/usr/bin/env bash
# run_all.sh - chạy toàn bộ phần của Khôi (Python và R). Dùng: DATA_DIR=data_clean_temp ./run_all.sh
set -e
export DATA_DIR=${DATA_DIR:-data_clean_temp}
echo "== K3: bộ 6 số =="; python3 prep.py; Rscript prep.R
echo "== K2: lịch lễ =="; python3 make_holidays.py
echo "== K4: bốn chuỗi =="; python3 build_series.py outputs/series
echo "== Q4 =="; python3 q4_timeseries.py outputs/series outputs/q4; Rscript q4_timeseries.R outputs/series outputs/q4_R
echo "== Q2d =="; python3 q2d_holiday.py outputs/q2d; Rscript q2d_holiday.R outputs/q2d_R
echo "== Đối chiếu Python vs R =="; python3 compare_py_r.py; python3 compare_py_r_q4.py
