# README - Phần của Bảo (IS403.R13 - Nhóm 4)

Phần phụ trách: B3–B12; báo cáo Mục 3.1–3.5, 5.1, 5.3b; Phụ lục C, D.
Dữ liệu chốt: `Dữ liệu chính thức/data_final_20261113/` ở gốc repo (22/10–12/11/2026), 5 file, chỉ đọc.

## Cấu trúc

| Thư mục / file | Nội dung | Việc |
| --- | --- | --- |
| `python/prep.py`, `R/prep.R` | Quần thể H, age_b, lv_adj, viral_A, bộ 6 số | B3, B9 |
| `python/q1_descriptive.py`, `R/q1_descriptive.R` | Q1 thống kê mô tả; CSV và hình | B4 |
| `python/q3b_logistic.py`, `R/q3b_logistic.R` | Q3b Logistic (M1, M2, M3), SE theo cụm kênh | B5 |
| `python/reliability.py`, `python/make_collection_log.py` | Bảng độ tin cậy, tổng hợp thu thập, nhật ký thu thập | B6, B2 |
| `python/pick30.py` | Chọn 30 video và tính sai lệch so với YouTube | B7 |
| `python/make_final_package.py` | Đóng gói `data_final_20261113/`, checksums, sample 1.000 video | B8 |
| `python/gen_data_dictionary.py` → `docs/data_dictionary.md` | Từ điển 55 cột master + measurements, trending, channels, dq_report | B10 |
| `python/export_powerbi.py`, `python/prepare_b11_inputs.py`, `docs/PowerBI_guide.md`, `outputs/powerbi/` | CSV đầu vào và hướng dẫn dựng Power BI | B11 |
| `python/build_report_data.py` + `report/build_muc_bao.js` → `report/Muc_Bao.docx` | Sinh báo cáo Mục 3.1–3.5, 5.1, 5.3b, Phụ lục C, D | B12 |
| `Bao_Q1_Q3b_reliability.ipynb` | Notebook gọi lại các script, có sẵn kết quả | B3–B6 |
| `python/compare_py_r.py` | Đối chiếu số Python và R | B4, B5 |
| `outputs/reliability/references_log_Bao.csv` | 5 nguồn đã mở đọc, APA 7 | B12 |

## Cách chạy

1. Cài thư viện: `pip install -r requirements.txt`; với phần Word, `cd report && npm install docx`.
2. `prep.py` và `prep.R` tự tìm `data_final_20261113/` trong `Dữ liệu chính thức/` ở gốc repo (hoặc thư mục hiện tại/các thư mục cha), nên chạy được cả từ `Bao/` và từ `Bao/05_Code_Output/`. Có thể ghi đè bằng biến môi trường `DATA_DIR`.
3. Chạy toàn bộ: `bash run_all.sh`, hoặc lần lượt:
   `python python/prep.py` → `python python/q1_descriptive.py` → `python python/q3b_logistic.py` → `python python/reliability.py` → `python python/gen_data_dictionary.py` → `python python/export_powerbi.py` → `python python/prepare_b11_inputs.py` → `python python/build_report_data.py` → `node report/build_muc_bao.js`.
4. R (đã chạy lại trên dữ liệu chốt): `cd R && Rscript prep.R && Rscript q1_descriptive.R && Rscript q3b_logistic.R`, sau đó `cd ../python && python compare_py_r.py`.
5. Đóng gói lại dữ liệu (chỉ khi có chủ đích): `python python/make_final_package.py --force`. Script này tạo gói mới trong `Bảo/`; không chạy lại nếu không muốn `prep.py` chọn nhầm bản gần hơn.

## Bộ 6 số kiểm tra (data_final_20261113)

n_H = **139.227** · số kênh trong H = **464** · video H thuộc nhóm tuổi [7, 10) = **2.325** · tổng viral_A = **13.931** (10,01%) · trung vị lv_adj = **0,0895** · video H có ever_trending = **892**.

Số chi tiết và phân bố nhóm tuổi nằm trong `docs/so_kiem_tra_Bao.txt`. Kết quả Python và R khớp đến 3 chữ số (xem `python/compare_py_r.py`: TẤT CẢ KHỚP).

## Kết quả chính của phần Bảo

- Q1: n_H = 139.227 video, 464 kênh. Trung vị lv_adj theo giờ cao nhất 4h (0,513) và thấp nhất 13h (−0,377); khoảng cách thô 0,890 log10 nhưng chỉ còn 0,209 sau khi trừ trung vị kênh. 68,0% phương sai lv_adj nằm giữa các kênh.
- Q1 theo thể loại: khoảng cách thô giữa 10 thể loại đông nhất là 1,752 log10 (Gaming cao nhất, Education thấp nhất); sau khi trừ trung vị kênh chỉ còn 0,018 và thứ hạng đảo lại (Music cao nhất, Howto & Style thấp nhất). Vì vậy không đọc chênh lệch thô theo thể loại như tác động của thể loại.
- Q3b: n = 139.223; 13.930 video dương (10,01%); 464 cụm kênh. AIC M1 = 67.617,0; M2 = 82.766,3; M3 = 67.531,0. McFadden R² = 0,254 (M1) và 0,087 (M2). log_subs: OR 8,83 (CI 95% 6,20–12,57).
- Q3b theo thể loại: 12/13 thể loại có OR điểm ước lượng dưới 1 so với Gaming, nhưng chỉ 6 thể loại có CI hoàn toàn dưới 1; 7 thể loại còn lại có CI chứa 1.

## B7 - Đối chiếu 30 video

Đã điền đủ 30 dòng trong `outputs/reliability/reliability_check_30videos.csv`; **không lưu ảnh chụp màn hình**, số được ghi trực tiếp vào CSV. Lượt xem trùng hoàn toàn ở 5/30 video; lượt thích 17/30; bình luận 27/30 (tính cả cặp API = YouTube = 0). Nếu chỉ tính video có số đếm API khác 0: lượt thích 16/29, bình luận 18/21. Trung vị sai lệch tương đối của lượt xem là 0,08%; sai lệch tuyệt đối lớn nhất 2,78%. Cột `ten_anh` để trống vì không có ảnh.

## B8 - Gói dữ liệu chốt

- Gói nằm ở gốc repo: `Dữ liệu chính thức/data_final_20261113/` gồm 5 file `videos_master.csv`, `measurements.csv`, `trending_clean.csv`, `channels_latest.csv`, `dq_report.txt`; đã đặt chỉ đọc.
- `Dữ liệu chính thức/checksums.txt`: SHA-256 của 5 file dữ liệu và `sample_1000.csv`; UTF-8 không BOM, xuống dòng LF. Đã kiểm tra khớp cả 6 file tại vị trí mới.
- `Dữ liệu chính thức/sample_1000.csv`: 1.000 video chọn ngẫu nhiên từ master, `random_state = 42`, giữ đủ 55 cột.
- Gói đã được đưa lên Drive `03_Dataset/`; hướng dẫn kiểm tra lại sau khi tải nằm trong `docs/B8_huong_dan_va_kiem_tra.md`.

## B10 - Từ điển dữ liệu

`docs/data_dictionary.md` mô tả đủ 55 cột của `videos_master.csv`, toàn bộ cột của `measurements.csv`, `trending_clean.csv`, `channels_latest.csv`, và `dq_report.txt`. Script `gen_data_dictionary.py` báo "Không cột nào thiếu mô tả".

## B11 - Power BI

Đã có đủ CSV đầu vào trong `outputs/powerbi/`: 6 thẻ KPI, bảng độ tin cậy, Q1 (mô tả, giờ, heatmap, thể loại, thứ), Q3b (OR và model fit), Q2b nhóm trung bình (bản sao từ Kiên), Q4 dự báo S1/S2 (bản sao từ Khôi). `python/prepare_b11_inputs.py` tự tìm và chuẩn hóa các file của thành viên khác; Q5/Q6 chưa có nên bỏ biểu đồ, không chờ. Hướng dẫn dựng 3 trang, DAX, cách lưu `dashboard.pbix` và xuất 3 PNG nằm trong `docs/PowerBI_guide.md`; bản rút gọn để làm và tích từng bước là `docs/B11_checklist.md`.

Chưa có `dashboard.pbix` và 3 ảnh PNG (phải thao tác trong Power BI Desktop); Phụ lục D hiện ghi rõ chưa kèm ảnh, sẽ cập nhật sau khi có ảnh.

## Ghi chú

- `outputs/reliability/collection_log.csv` đã điền lý do cho 17 dòng THIẾU: các ngày history ngoài lịch lấy lịch sử; các ngày trending/tracking thiếu không được log vận hành ghi nguyên nhân, không điền bù.
- Không còn bản lưu riêng `dq_report_0911.txt`; xem `docs/ghi_chu_dq_report_0911.md`. Mọi số trong báo cáo lấy từ `dq_report.txt` cuối kỳ.
- B13/B14 (slide, video) không nằm trong phần đã làm.
