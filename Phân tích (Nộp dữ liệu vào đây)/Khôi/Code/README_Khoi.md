# README_Khoi.md - phần của Khôi (Mục 3.6, 5.2d, 5.4) - chạy trên data_final (chốt 13/11)

## Cách chạy
Đặt thư mục `data_final` (có `videos_master.csv`, `trending_clean.csv`) cạnh các script hoặc đặt biến `DATA_DIR=data_final`, rồi chạy `./run_all.sh` (khoảng 1,5 phút).
Cần Python (pandas, numpy, scipy, statsmodels, matplotlib, pytrends cho Trends) và R (forecast, tseries, data.table).
Trước khi chạy lại: đổi tên thư mục `outputs` cũ (ví dụ `outputs_tam`) để không lẫn kết quả.

| Việc | File | Sản phẩm | Thư mục kết quả |
|---|---|---|---|
| Lịch lễ | make_holidays.py | holidays_vn.csv, holidays_sources.md (không sửa tay trong Excel) | 5.2d holiday_tet |
| Tiền xử lý | prep.py, prep.R | bộ 6 số kiểm tra | (đối chiếu với Kiên) |
| Bốn chuỗi S1, S2, N1, N2 | build_series.py | series_daily.csv, series_trending.csv, series_notes.md | 5.4 timeseries |
| Chuỗi thời gian | q4_timeseries.py, q4_timeseries.R | q4_* (tiền tố Python_ / R_) | 5.4 timeseries |
| Lễ và Tết | q2d_holiday.py, q2d_holiday.R | q2d_results_Python/R.csv | 5.2d holiday_tet |
| Google Trends | trends_fetch.py, trends_check.py | trends_check_*.csv, .png | 3.6 trends_check |
| Đối chiếu Python và R | compare_py_r.py, compare_py_r_q4.py | in ra màn hình | - |

Kết quả Python và R khớp nhau; điểm khác duy nhất là bậc mô hình của N1 và N2 (chuỗi chỉ 14 và 18 điểm).
