# QA sign-off - Phần của Nguyễn Gia Bảo (IS403.R13)

**Bài phân tích:** Q1 thống kê mô tả và Q3b hồi quy Logistic cho viral_A; độ tin cậy thu thập; đóng gói dữ liệu chốt  
**Người soát:** AI QA pass (theo checklist analysis-qa-checklist)  
**Tác giả:** Nguyễn Gia Bảo (24520166)  
**Ngày soát:** 2026-11-15  
**Đối tượng đọc:** Nhóm 4 và giảng viên IS403.R13  
**Hình thức nộp:** Báo cáo Word, mã nguồn và dữ liệu chốt

---

## Kết quả kiểm tra tự động

| Kiểm tra | Trạng thái | Ghi chú |
|---|---|---|
| `qa_runner.py` trên `q1_by_category.csv` | PASS | 15 dòng, 0 FAIL, 0 WARN |
| `qa_runner.py` trên `q3b_or_table.csv` | PASS | 34 dòng, 0 FAIL, 0 WARN |
| `qa_runner.py` trên `reliability_table.csv` | PASS | 17 dòng, 0 FAIL, 0 WARN |
| `qa_runner.py` trên `collection_log.csv` | PASS | 66 dòng, 0 FAIL, 0 WARN |
| Cú pháp toàn bộ file `.py` | PASS | Không lỗi |
| SHA-256 của 5 file dữ liệu + `sample_1000.csv` | PASS | Khớp `Dữ liệu chính thức/checksums.txt` tại vị trí mới; không BOM, xuống dòng LF |
| Quét chỗ trống trong báo cáo | PASS | Không còn `GHI CHÚ CHO KIÊN`, `[Bảo:`, `⟦`, `03_Dataset`, `Chèn ảnh dashboard` |
| Số cũ còn sót | PASS | Không còn 95.319; 9.542; 0,0905; 16/30; 18/30 |

---

## Tóm tắt checklist thủ công

| Mục | Trạng thái | Vấn đề đã gặp |
|---|---|---|
| 1. Đặt câu hỏi | PASS | Q1/Q3b, quần thể H và giới hạn diễn giải được nêu rõ |
| 2. Nguồn dữ liệu | PASS | Mọi số lấy từ `data_final_20261113/`; số dòng khớp từ điển dữ liệu |
| 3. Biến đổi và tính toán | PASS | Đã sửa gộp thể loại lẫn kênh ở Q1; mẫu số B7 minh bạch |
| 4. Giá trị thống kê | PASS | SE theo cụm kênh, 464 cụm; nêu rõ OR không phải nhân quả |
| 5. Kết luận | PASS | Kết luận Q1/Q3b không còn mâu thuẫn; danh sách CI Q3b khớp bảng |
| 6. Trình bày | PASS | Đường dẫn đúng; Phụ lục D ghi trung thực không có ảnh dashboard |

---

## Vấn đề đã phát hiện và xử lý

| # | Mức độ | Mô tả | Cách xử lý | Trạng thái |
|---|---|---|---|---|
| 1 | MUST FIX | Q1 so sánh thể loại thô nhưng bỏ qua cơ cấu kênh | Thêm trung vị trong kênh; báo cáo nêu 1,752 log10 thô so với 0,018 sau khi trừ kênh | Đã sửa |
| 2 | MUST FIX | B7 đếm trùng khớp bằng `sai_lech_*` nên bỏ sót cặp API = YouTube = 0 | Đếm trên giá trị gốc; nêu 17/30 và 27/30, kèm 16/29 và 18/21 | Đã sửa |
| 3 | MUST FIX | Q3b liệt kê sai số thể loại có CI chứa 1 | Sinh danh sách động: 6 thể loại CI dưới 1, 7 thể loại CI chứa 1 | Đã sửa |
| 4 | SHOULD FIX | Còn khối ghi chú nội bộ, placeholder Phụ lục D, đường dẫn cũ | Đã xóa; Phụ lục D ghi rõ không kèm ảnh | Đã sửa |
| 5 | SHOULD FIX | `collection_log.csv` còn 17 dòng THIẾU chưa có lý do | Đã điền lý do và cách xử lý; không điền bù số liệu | Đã sửa |
| 6 | MINOR | `dq_report_0911.txt` không còn bản lưu | Ghi chú trung thực trong `docs/ghi_chu_dq_report_0911.md`; không dựng lại | Chấp nhận |

---

## Quyết định bàn giao

- [x] **Approved with caveats** - bàn giao kèm các giới hạn đã ghi rõ

**Giới hạn khi bàn giao:**

> B8 đã đưa gói dữ liệu, checksums và mẫu 1.000 video lên Drive `03_Dataset/`; SHA-256 đã đối chiếu khớp tại `Dữ liệu chính thức/`. B11 đã có đủ CSV đầu vào và hướng dẫn dựng 3 trang, nhưng chưa có `dashboard.pbix` và 3 ảnh dashboard, nên Phụ lục D chỉ mô tả phần đã chuẩn bị. B7 không lưu ảnh chụp màn hình; số liệu được ghi trực tiếp trong CSV.

**Người soát:** AI QA pass  **Ngày:** 2026-11-14
