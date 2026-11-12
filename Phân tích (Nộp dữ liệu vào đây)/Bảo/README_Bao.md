# README – Phần của Bảo (IS403.R13 – Nhóm 4)

## Cấu trúc
| Thư mục / file | Nội dung | Việc |
| --- | --- | --- |
| `python/prep.py` | Quần thể H, age_b, lv_adj, viral_A, bộ 6 số | B3 |
| `python/q1_descriptive.py`, `R/q1_descriptive.R` | Q1 thống kê mô tả | B4 |
| `python/q3b_logistic.py`, `R/q3b_logistic.R` | Q3b hồi quy Logistic (M1, M2, M3), SE theo cụm kênh | B5 |
| `python/reliability.py` | Bảng độ tin cậy + tóm tắt thu thập | B6 |
| `python/pick30.py` | Chọn 30 video và tính sai lệch so với YouTube | B7 (phần làm tay: xem dưới) |
| `python/gen_data_dictionary.py` → `docs/data_dictionary.md` | Từ điển dữ liệu (55 cột + 3 file) | B10 |
| `python/export_powerbi.py`, `docs/PowerBI_guide.md`, `outputs/powerbi/` | CSV và hướng dẫn Power BI | B11 |
| `python/build_report_data.py` + `report/build_muc_bao.js` → `report/Muc_Bao.docx` | Báo cáo Mục 3.1–3.5, 5.1, 5.3b, Phụ lục C, D | B12 |
| `Bao_Q1_Q3b_reliability.ipynb` | Notebook gọi lại các script, có sẵn kết quả | B3–B6 |
| `python/compare_py_r.py` | Đối chiếu số Python và R (khớp 3 chữ số) | B4, B5 |
| `outputs/reliability/references_log_Bao.csv` | 5 nguồn đã mở đọc, APA 7 | B12 |

## Cách chạy
1. `pip install -r requirements.txt` (và `npm install docx` cho phần Word).
2. Đặt biến môi trường `DATA_DIR` trỏ tới thư mục chứa 4 CSV + `dq_report.txt`, rồi `bash run_all.sh` hoặc chạy lần lượt từng script. Khi có dữ liệu chốt chỉ cần đổi `DATA_DIR` sang `data_final_20261113` (việc B9) rồi chạy lại.
3. R: `cd R && Rscript q1_descriptive.R && Rscript q3b_logistic.R` (cần `readr dplyr tidyr ggplot2 sandwich lmtest`), sau đó `cd ../python && python compare_py_r.py`.

## Bộ 6 số kiểm tra (data_clean 03/11) – điền vào sheet `so_kiem_tra`
n_H = 95.319 · số kênh trong H = 328 · video H nhóm tuổi [7, 10) = 1.594 · tổng viral_A = 9.542 (10,01%) · trung vị lv_adj = 0,0905 · video H ever_trending = 399. Đối chiếu với số của các bạn khác; nếu lệch, kiểm tra điều kiện H (`in_history`, `~is_live_or_upcoming`, `views > 0`, `age_days_last >= 1`) và biên nhóm tuổi.

## Chưa làm được (cần bạn làm tay hoặc chưa kiểm chứng)
- **R chưa được chạy thử** (môi trường tạo file không có R). Code R viết theo đúng công thức của bản Python; hãy chạy và `compare_py_r.py`, sửa lỗi nếu có.
- **B7:** kết quả đối chiếu 30 video (cần mở YouTube sau 12/11 20:00). `pick30.py` chọn video và tính sai lệch; Bảng 3.4 đang để ô tô vàng.
- **B2, B8:** `collection_log.csv` (lý do ngày thiếu lượt), `checksums_raw.txt` (SHA-256), sao lưu `data_raw_20261103/`, tắt lịch thu.
- **B11:** file `dashboard.pbix` và 3 ảnh dashboard (chỉ có CSV và hướng dẫn).
- **B13/B14:** slide và video không nằm trong phần đã làm.
- Nhãn [A]/[C]/[B] của log trong Mục 3.1 cần bạn xác nhận.
