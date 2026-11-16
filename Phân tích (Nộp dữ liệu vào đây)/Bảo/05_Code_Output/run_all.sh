#!/usr/bin/env bash
# Chạy lại toàn bộ phần của Bảo trên data_final_20261113/ (việc B9, B10).
# prep.py tự tìm data_final_20261113/ trong Dữ liệu chính thức/ ở gốc repo
# (hoặc thư mục hiện tại/các thư mục cha); chỉ cần đặt DATA_DIR nếu muốn dùng đường dẫn khác.
set -e
if [ -n "${DATA_DIR:-}" ]; then export DATA_DIR; fi
cd "$(dirname "$0")/python"
python prep.py | tee ../docs/so_kiem_tra_Bao.txt     # B3/B9: bộ 6 số
python q1_descriptive.py                              # B4: Q1
python q3b_logistic.py                                # B5: Q3b
python reliability.py                                 # B6: bảng độ tin cậy
python gen_data_dictionary.py                         # B10: từ điển dữ liệu
python export_powerbi.py                              # B11: CSV cho Power BI
python prepare_b11_inputs.py                          # B11: CSV Q2b/Q4/Q5/Q6 của thành viên khác
python build_report_data.py && node ../report/build_muc_bao.js   # B12: Muc_Bao.docx
# Sau khi chạy R (Rscript R/q1_descriptive.R, R/q3b_logistic.R, đứng trong thư mục R/):  python compare_py_r.py
