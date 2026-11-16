# B11 - Checklist dựng dashboard Power BI

Làm lần lượt từ trên xuống, tích vào ô khi xong. Hướng dẫn chi tiết kèm công thức DAX: `docs/PowerBI_guide.md`.
Thời gian ước tính: 90–150 phút cho lần đầu.

**Kết quả cần có:** `dashboard.pbix` + `Hinh_D1.png`, `Hinh_D2.png`, `Hinh_D3.png`.

## 0. Trước khi mở (2 phút)

- [ ] Mở thư mục `Bao/05_Code_Output/outputs/powerbi/`. Có 15 file CSV; 14 file trong bảng dưới là đủ cho 3 trang, `q1_by_month.csv` không dùng nên bỏ qua.
- [ ] Mở sẵn `docs/PowerBI_guide.md`, phần 2 (DAX) và phần 3–5 (từng trang).
- [ ] Mở Power BI Desktop: Start → gõ `Power BI Desktop`, hoặc chạy `C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe`.

## 1. Nạp dữ liệu (10 phút)

- [ ] `Home` → `Get data` → `Text/CSV`.
- [ ] Vào `Bao/05_Code_Output/outputs/powerbi/`, chọn 14 file trong bảng dưới (Ctrl + click từng file) → `Open`.
  Nếu hộp thoại chỉ cho chọn 1 file: nạp lần lượt từng file, giữ nguyên tên bảng.
- [ ] Ở cửa sổ xem trước: `File origin` = **65001: Unicode (UTF-8)**, `Delimiter` = **Comma**, `Data type detection` = **Based on first 200 rows** → `Load`.
- [ ] Chờ load xong; kiểm tra số dòng ở góc dưới `Data view`.

| Bảng | Số dòng | Dùng ở |
| --- | --- | --- |
| `kpi_overview` | 12 | thẻ KPI trang 1 |
| `kpi_dates` | 2 | ghi chú ngày |
| `q1_descriptive_table` | 18 | bảng Q1 trang 1 |
| `q1_by_dow` | 7 | cột theo thứ trang 1 |
| `q1_by_hour` | 24 | biểu đồ giờ trang 2 |
| `q1_heatmap` | 168 | heatmap trang 2 |
| `q1_by_category` | 15 | cột thể loại trang 2 |
| `q2b_group_means` | 19 | Q2b trang 2 |
| `q3b_or_table` | 34 | OR trang 3 |
| `q3b_model_fit` | 3 | bảng M1/M2/M3 trang 3 |
| `q4_forecast_S1` | 1.065 | dự báo S1 trang 3 |
| `q4_forecast_S2` | 1.059 | dự báo S2 trang 3 |
| `q4_model_comparison` | 8 | dự phòng |
| `reliability_table` | 17 | bảng độ tin cậy trang 1 |

## 2. Kiểm tra kiểu dữ liệu (5 phút)

Vào `Data view` (biểu tượng bảng bên trái), bấm từng cột và xem `Column tools` → `Data type`.

- [ ] `kpi_overview[gia_tri]`: Decimal Number hoặc Whole Number.
- [ ] `kpi_overview[chi_so]`: Text.
- [ ] `q1_by_hour[pub_hour]`, `q1_heatmap[pub_hour]`, `q1_heatmap[pub_dow]`, `q1_by_category[rank_n]`: Whole Number.
- [ ] Các cột `median_lv_adj`, `mean_lv_adj`, `median_lv_within_channel`, `median_lv_adj_masked`, `mean_lv_adj`, `ci_low`, `ci_high`, `OR_M1`, `OR_lo95_M1`, `OR_hi95_M1`, `p_M1`, `AIC`, `McFadden_R2`, `actual`, `forecast`, `lo95`, `hi95`: Decimal Number.
- [ ] `q4_forecast_S1[date]` và `q4_forecast_S2[date]`: Date.
- [ ] `q4_forecast_*[split]`, `q3b_model_fit[model]`, `q3b_or_table[label]`, `q2b_group_means[group]`, `q1_by_dow[dow_name]`: Text.

Nếu cột số bị nhận là Text: `Transform Data` → chọn cột → `Data Type` → `Decimal Number`. Nếu báo lỗi do dấu thập phân, dùng `Using Locale` → **English (United States)**.

## 3. Tạo 11 độ đo (15 phút)

`Modeling` → `New measure`, dán từng công thức trong mục 2 của `docs/PowerBI_guide.md`. Đặt đúng tên, chọn đúng định dạng:

| Độ đo | Định dạng | Giá trị đúng |
| --- | --- | --- |
| `n_H` | Whole Number, có dấu nghìn | 139.227 |
| `So_kenh_H` | Whole Number | 464 |
| `So_video_trending` | Whole Number | 1.039 |
| `Ty_le_viral` | Percentage, 2 số lẻ | 10,01% |
| `So_lan_do` | Whole Number | 1.066.405 |
| `Trung_vi_lv_adj` | Decimal, 4 số lẻ | 0,0895 |
| `Chenh_gio` | Decimal, 3 số lẻ | 0,890 |
| `Chenh_gio_trong_kenh` | Decimal, 3 số lẻ | 0,209 |
| `AIC_M1` | Decimal, 1 số lẻ | 67.617,0 |
| `AIC_M3` | Decimal, 1 số lẻ | 67.531,0 |
| `McFadden_M1` | Decimal, 3 số lẻ | 0,254 |

Gợi ý: bấm vào bảng tương ứng ở cột phải trước khi `New measure` để độ đo nằm gọn trong bảng đó (không bắt buộc).

## 4. Trang 1 - Tổng quan (20 phút)

Đổi tên trang: nháy đúp chữ `Page 1` ở dưới cùng → `1. Tổng quan`.

- [ ] 6 thẻ `Card`, lần lượt: `n_H`, `So_kenh_H`, `So_video_trending`, `Ty_le_viral`, `So_lan_do`, `Trung_vi_lv_adj`. Xếp một hàng ngang, cao 90–100 px, cỡ số 20–24.
- [ ] `Text box` dưới hàng thẻ: `Dữ liệu 22/10–12/11/2026 · 140.387 video master · 46 lần chụp Trending · 19 ngày đo`.
- [ ] Bảng trái: `Table` với `tieu_chi`, `so_dem`, `mau_so`, `ty_le_pct` từ `reliability_table`; tiêu đề `Bảng 3.3 - Độ tin cậy dữ liệu`; `ty_le_pct` 2 số lẻ, cỡ chữ 9.
- [ ] Bảng phải: `Table` với `bien`, `n`, `mean`, `median`, `sd`, `cv` từ `q1_descriptive_table`; filter `nhom` = `Tất cả`; tiêu đề `Q1 - Thống kê mô tả (toàn bộ H)`.
- [ ] Biểu đồ cột dưới cùng: `Clustered column chart`, X = `dow_name`, Y = `median_lv_adj` (Average); tiêu đề `Q1 - Trung vị lv_adj theo ngày đăng`.
- [ ] Sắp trục thứ đúng: `Data view` → `q1_by_dow[dow_name]` → `Column tools` → `Sort by column` → `q1_by_dow[pub_dow]`.
- [ ] Footer: `Nguồn: 05_Code_Output/outputs/ · Dữ liệu 22/10–12/11/2026 · Số liệu chốt 13/11/2026`.

## 5. Trang 2 - Giờ đăng và thể loại (25 phút)

Đổi tên trang thành `2. Giờ đăng và thể loại`.

- [ ] `Line and clustered column chart`: X = `pub_hour` (Type = Categorical); Column Y = `n` (Sum); Line Y = `median_lv_adj` và `median_lv_within_channel` (Average); bật `Secondary y-axis`; tiêu đề `Q1 - Số video và trung vị lv_adj theo giờ đăng`.
- [ ] 2 thẻ nhỏ cạnh biểu đồ: `Chenh_gio` = 0,890; `Chenh_gio_trong_kenh` = 0,209.
- [ ] `Matrix` heatmap: Rows = `pub_hour`; Columns = `dow_name`; Values = `median_lv_adj_masked` (Average); `Cell elements` → `Background color` → `fx` → Gradient, min −0,5, max 0,5, center 0; thêm `n` vào Tooltips.
- [ ] Sắp cột thứ của heatmap: `Data view` → `q1_heatmap[dow_name]` → `Sort by column` → `q1_heatmap[pub_dow]`.
- [ ] Cột thể loại 1: `Clustered bar chart`, Y = `category_name`, X = `median_lv_adj`; filter `rank_n` ≤ 10; tiêu đề `Q1 - Trung vị lv_adj theo thể loại (10 thể loại nhiều video nhất)`.
- [ ] Cột thể loại 2: sao chép biểu đồ 1, đổi X = `median_lv_within_channel`; trục X từ −0,03 đến 0,03; tiêu đề `Sau khi trừ trung vị kênh (cùng 10 thể loại)`.
- [ ] Ghi chú: `Chênh lệch thô 1,752 log10 chỉ còn 0,018 sau khi trừ kênh.`
- [ ] Q2b: `Clustered bar chart`, Y = `group`, X = `mean_lv_adj`; filter `factor` = `pub_slot`; thêm `ci_low`, `ci_high`, `n` vào Tooltips; tiêu đề `Q2b - Trung bình lv_adj theo khung giờ (95% CI trong tooltip)`.
- [ ] Footer như trang 1.

## 6. Trang 3 - Viral và dự báo (25 phút)

Đổi tên trang thành `3. Viral và dự báo`.

- [ ] `Data view` → `q3b_or_table` → `New column`: `Abs_log_OR = ABS ( LN ( q3b_or_table[OR_M1] ) )`.
- [ ] `Clustered bar chart`: Y = `label`, X = `OR_M1`; filter `term` is not `const`, `term` does not begin with `cat:`, Top N 12 theo `Abs_log_OR`; bật `Log scale`; thêm reference line = 1; Tooltips có `OR_lo95_M1`, `OR_hi95_M1`, `p_M1`; tiêu đề `Q3b - Odds ratio của viral_A (M1, 12 biến mạnh nhất; thang log)`.
- [ ] Ghi chú dưới biểu đồ: `OR > 1: tăng khả năng viral; OR < 1: giảm. Đây là liên quan, không phải nhân quả.`
- [ ] `Table` so sánh mô hình: `model`, `n`, `n_pos`, `pct_pos`, `AIC`, `McFadden_R2`, `converged`; tiêu đề `Q3b - So sánh M1 / M2 / M3`.
- [ ] 2 thẻ nhỏ: `AIC_M1` = 67.617,0; `McFadden_M1` = 0,254.
- [ ] `Line chart` S1: X = `date`, Y = `actual`, `forecast`, `lo95`, `hi95`; filter `split` = `test`, `forecast`; tiêu đề `Q4 - Dự báo S1 (số video/ngày) 4 tuần tới`.
- [ ] `Line chart` S2: sao chép biểu đồ S1, đổi bảng sang `q4_forecast_S2`; tiêu đề `Q4 - Dự báo S2 (lv_adj trung bình/ngày)`.
- [ ] `Text box` cuối trang: `Q5/Q6 chưa có CSV trong 05_Code_Output/outputs/ tại thời điểm 17/11 17:00, nên không dựng biểu đồ theo quy ước B11.`
- [ ] Footer như trang 1.

## 7. Định dạng, lưu, xuất 3 ảnh (15 phút)

- [ ] `View` → `Page view` → `Actual size`; `Format` → `Page setup` → `16:9`; font `Segoe UI`; nền trắng hoặc xám rất nhạt.
- [ ] Kiểm tra từng trang: không cắt chữ, không có visual lỗi đỏ, số đọc được.
- [ ] `File` → `Save as` → lưu `Bao/outputs/powerbi/dashboard.pbix`.
- [ ] Xuất ảnh từng trang (thu gọn pane, `Win + Shift + S`, chọn đúng vùng trang) và lưu:
  - `Bao/report/assets/Hinh_D1.png` (trang 1)
  - `Bao/report/assets/Hinh_D2.png` (trang 2)
  - `Bao/report/assets/Hinh_D3.png` (trang 3)
- [ ] Mở lại 3 ảnh, kiểm tra không mất góc và đọc được số.

## 8. Đối chiếu số trước khi báo xong

| Chỉ tiêu | Giá trị đúng |
| --- | --- |
| n_H | 139.227 |
| Số kênh trong H | 464 |
| Video từng lọt Trending | 1.039 |
| Tỷ lệ viral_A | 10,01% |
| Số lần đo | 1.066.405 |
| Trung vị lv_adj | 0,0895 |
| Ẩn lượt thích | 5.119 (3,65%) |
| Tắt bình luận | 2.966 (2,11%) |
| Chênh lệch thô theo giờ | 0,890 |
| Chênh lệch trong kênh | 0,209 |
| log_subs OR (M1) | 8,83 (6,20–12,57) |
| AIC M1 / M3 | 67.617,0 / 67.531,0 |
| McFadden M1 | 0,254 |

## 9. Báo lại để chạy phần còn lại

Khi đã có `dashboard.pbix` và đủ 3 ảnh, nhắn: **“đã có 3 ảnh”**. Phần tự động sẽ chạy:

```powershell
cd "Phân tích (Nộp dữ liệu vào đây)\Bảo\Bao"
node report/build_muc_bao.js
python python/make_code_output.py --force
Copy-Item -Force "report\Muc_Bao.docx" "..\Muc_Bao.docx"
```

Sau đó kiểm tra: Phụ lục D có Hình D.1–D.3; 3 bản `Muc_Bao.docx` giống nhau; gói `05_Code_Output` có `dashboard.pbix` và 3 ảnh.

## 10. Xong khi

- [ ] `dashboard.pbix` mở được, `Refresh` không lỗi.
- [ ] 3 ảnh đúng thứ tự trang, đọc được số.
- [ ] 6 KPI khớp bảng mục 8.
- [ ] Phụ lục D trong báo cáo có 3 hình.
- [ ] `Bao/report/`, `Bao/05_Code_Output/report/`, `Bảo/` có `Muc_Bao.docx` giống hệt nhau.

## Nếu kẹt

| Hiện tượng | Cách sửa nhanh |
| --- | --- |
| Số thập phân thành Text | `Transform Data` → `Data Type` → `Decimal Number`; `Using Locale` = English (United States) |
| Chữ Việt lỗi font | Nạp lại với `File origin` = 65001 UTF-8 |
| Card KPI trống | Kiểm tra measure có đúng tên bảng/cột `kpi_overview[chi_so]`, `kpi_overview[gia_tri]` |
| Heatmap có ô trống | Đúng thiết kế: ô có `n < 30` đã bị che bằng `median_lv_adj_masked` |
| Cột thứ xếp sai | `Sort by column` cho `dow_name` theo `pub_dow` ở đúng bảng |
| Đường `n` làm bẹp 2 đường lv_adj | Bật `Secondary y-axis` cho line values |
| Không thấy `Log scale` ở trục X | Đổi sang `Clustered column chart`, bật `Log scale` ở trục Y |
| Biểu đồ Q4 trống | Đang lọc `split` sai; chọn `test` và `forecast` |
| Không nạp được nhiều file một lúc | Nạp lần lượt 14 file, giữ nguyên tên bảng |
