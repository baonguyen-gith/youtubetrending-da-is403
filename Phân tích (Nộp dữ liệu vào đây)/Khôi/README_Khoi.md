# README_Khoi.md - phần của Khôi (Q4 chuỗi thời gian, Q2d lễ và Tết) - BẢN CHẠY THỬ trên data_clean_temp

> Số liệu trong file này chỉ để kiểm tra code. Chưa dùng trong báo cáo. Sau 13/11: đổi `DATA_DIR=data_final_20261113`, chạy `./run_all.sh`, thay mọi số.

## Cách chạy
Đặt thư mục dữ liệu (có `videos_master.csv`, `trending_clean.csv`) cạnh các script, hoặc đặt biến `DATA_DIR`.
`DATA_DIR=data_clean_temp ./run_all.sh` (khoảng 1,5 phút). Cần Python (pandas, numpy, scipy, statsmodels, matplotlib; pytrends cho K5) và R (forecast, tseries, data.table).

| Việc | File | Sản phẩm |
|---|---|---|
| K1 từ khóa Trends | trends_keywords.csv | 5 từ khóa + lý do (chưa kiểm lượng tìm kiếm) |
| K2 lịch lễ | make_holidays.py, holidays_vn.csv, holidays_sources.md | 15 kỳ, 18/22/25 ngày (2024/2025/2026) |
| K3 tiền xử lý | prep.py, prep.R | bộ 6 số (bên dưới) |
| K4 bốn chuỗi | build_series.py | outputs/series/ (series_daily.csv, series_trending.csv, series_notes.md) |
| K5 Trends | trends_fetch.py, trends_raw.csv | Khôi đã chạy trên máy cá nhân ngày 06/11 (149 tuần mỗi từ khóa). Tải lại ngày 13/11 với `python trends_fetch.py 2026-11-12` |
| K10 đối chiếu Trends | trends_check.py | outputs/trends_check/ (Spearman theo tuần, hình hai trục) |
| K6, K8 Q4 | q4_timeseries.py, q4_timeseries.R | outputs/q4/ (Python), outputs/q4_R/ (R) |
| K7 Q2d | q2d_holiday.py, q2d_holiday.R | outputs/q2d/, outputs/q2d_R/ |
| Đối chiếu | compare_py_r.py, compare_py_r_q4.py | in độ lệch Python vs R |

## Bộ 6 số (data_clean_temp; Python và R giống nhau)
n_H = 95.319 | số kênh trong H = 328 | n_H nhóm tuổi [7,10) = 1.594 | tổng viral_A = 9.542 (10,01% của H) | trung vị lv_adj = 0,0905 | n_H có ever_trending = 399.

## Kết quả chạy thử (chỉ minh họa)
**Q4.** S1 (213 kênh, 01/01/2024-02/11/2026): log + sai phân bậc 1. ARIMAX(2,1,2)(1,0,1,7) được chọn theo AIC; MAE test 41,97 so với seasonal naive 42,71 (hơn 1,7%, gần như hòa); Ljung-Box p = 0,159. Hệ số Tết trên log S1 = -0,176 (z = -3,6), tức ngày Tết có liên quan đến số video đăng thấp hơn khoảng 16%; hệ số lễ khác không có ý nghĩa.
S2 (đến 27/10/2026): SARIMA(1,0,1)(1,0,1,7); MAE test 0,150 so với seasonal naive 0,233 (tốt hơn); Ljung-Box p = 0,709. Biến lễ/Tết trong ARIMAX không có ý nghĩa.
N1, N2: không chạy (chỉ 5 và 9 điểm hợp lệ, ngưỡng 10); nhánh code đã thử trên dữ liệu giả 22 điểm ở cả hai ngôn ngữ.
**Q2d.** Kỳ Tết 2026: chênh lệch lv_adj +0,119 (d = 0,11); sau Holm p = 0,167. Bỏ video ngắn: +0,162, p Holm = 0,011; Gộp Tết bỏ video ngắn: +0,145, p Holm = 0,005 (d = 0,14). Gộp lễ khác không có ý nghĩa. Kết quả nhạy với việc có bỏ video ngắn hay không; hiệu ứng nhỏ (d dưới 0,2).
**Python vs R.** Q2d: lệch tối đa 5e-7 (làm tròn CSV). Q4: cùng bậc 8/8 mô hình, AIC lệch tối đa 0,011, MAE test lệch tối đa 0,07 (S1).

## Điều cần biết khi dùng
1. **S1 không dừng vì cách thu thập**, không phải xu hướng thật: số video/tháng tăng từ khoảng 500-600 (2024) lên 4.384 (10/2026). Mô hình chưa bắt được đà tăng trong 28 ngày test. Phải nói rõ trong Mục 5.4.
2. **sMAPE của S2 vô nghĩa về mặt diễn giải** (150% trở lên) vì S2 quanh 0 và có giá trị âm. Báo MAE là chính.
3. **Hạng tử mùa vụ gần triệt tiêu** (AR mùa 0,994, MA mùa -0,976): mô hình bắt thứ Bảy cao hơn (trung bình +0,12) nhưng mong manh.
4. **KPSS của S2 ở mức gốc không đồng nhất giữa hai ngôn ngữ** (p = 0,068 Python, 0,018 R do cách chọn độ trễ). d = 0 được chọn vì ADF bác bỏ nghiệm đơn vị; thử d = 1 cho MAE test tương đương (0,143) và vẫn thắng seasonal naive.
5. **Cách diễn giải cần xác nhận với nhóm trưởng:** "ngày thu cuối trừ ngày cuối" (hiểu là bỏ đúng ngày thu cuối); ý nghĩa cột n_videos, n_channels; kỳ dưới 100 video gộp thành một nhóm (kết quả đổi theo bản có/không video ngắn nên nhóm gộp không giống nhau hai bản); Holm áp dụng cho tất cả các dòng báo cáo (từng kỳ, gộp Tết, gộp lễ khác, gộp chung).
6. Q2d chưa tính tương quan giữa các video cùng kênh (Welch t-test coi độc lập). Nên ghi vào hạn chế hoặc làm bản sai số chuẩn theo kênh nếu còn thời gian.
7. Giờ chụp Trending không cố định 20:00 (08:35 đến 21:41), nên N2 nhiễu theo giờ; lịch thu 4 lần/ngày sẽ sửa điều này ở data_final.

## Đối chiếu Google Trends (chạy thử, dữ liệu tạm)
146 tuần đủ 7 ngày (07/01/2024-18/10/2026). Spearman giữa S2 theo tuần và Trends gần 0 ở cả 5 từ khóa (YouTube 0,03; TikTok 0,11; MV -0,09; Liên Quân -0,14; Tết -0,05), không có p (Holm) nào dưới 0,46; theo sai phân bậc 1 cũng không có ý nghĩa. Tức là trên dữ liệu tạm chưa thấy S2 cùng xu hướng với tìm kiếm Trends. Cần xem lại sau khi có data_final.
Lưu ý: (1) điểm Trends của YouTube và TikTok tụt mạnh vào các tuần 13/09 và 20/09/2026 (YouTube 38 và 35, TikTok 42 và 45) rồi hồi phục; nên kiểm tra tay trên trends.google.com trước khi dùng; (2) tuần của Trends bắt đầu Chủ nhật, script gộp S2 theo cùng tuần và chỉ giữ tuần đủ 7 ngày; (3) cả hai chuỗi có xu hướng nên p-value theo mức có thể lạc quan, vì vậy có thêm cột sai phân.
