# Ghi chú về `dq_report_0911.txt` (việc B2)

B2 yêu cầu chạy `clean_data.py` ngày 09/11 để có `dq_report_0911.txt` cho buổi họp giữa kỳ. Trong thư mục hiện tại không còn bản lưu riêng của file này, và không thể dựng lại trung thực: `clean_data.py` đã chạy lại trên dữ liệu cuối, nên `dq_report.txt` hiện tại là bản 12/11 chứ không phải bản 09/11. Nhóm không tạo file giả.

Hệ quả:

- Các số của bản giữa kỳ không được dùng trong báo cáo.
- Mọi số trong Mục 3.1–3.5 lấy từ `data_final_20261113/dq_report.txt` (bản cuối kỳ) và các file sạch đi kèm.
- Nếu cần đối chiếu tiến độ giữa kỳ, dùng `outputs/reliability/collection_log.csv` (nhật ký theo ngày) thay cho `dq_report_0911.txt`.
