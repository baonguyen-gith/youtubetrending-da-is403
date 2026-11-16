# B11 - Hướng dẫn dựng dashboard Power BI (3 trang)

Mục tiêu: tạo `dashboard.pbix` và 3 ảnh PNG để đưa vào Phụ lục D. Chỉ dùng các CSV trong `05_Code_Output/outputs/` (hoặc bản làm việc `Bao/outputs/powerbi/` trước khi đóng gói). File nào chưa có thì bỏ biểu đồ đó, không chờ.

## 0. Chuẩn bị

1. Mở thư mục `Bao/05_Code_Output/outputs/powerbi/` (bản chính thức). Khi đang sửa CSV, làm ở `Bao/outputs/powerbi/` rồi chạy `python python/make_code_output.py --force` để đồng bộ sang 05.
2. Kiểm tra đủ các file:

| File | Dùng cho | Số dòng |
| --- | --- | --- |
| `kpi_overview.csv` | thẻ KPI trang 1 | 12 |
| `kpi_dates.csv` | ngày đo đầu/cuối (chỉ để ghi chú) | 2 |
| `q1_descriptive_table.csv` | bảng mô tả Q1 trang 1 | 18 |
| `q1_by_dow.csv` | cột theo thứ trang 1 | 7 |
| `q1_by_hour.csv` | đường/cột theo giờ trang 2 | 24 |
| `q1_heatmap.csv` | heatmap giờ × thứ trang 2 | 168 |
| `q1_by_category.csv` | cột theo thể loại trang 2 | 15 |
| `q2b_group_means.csv` | trung bình nhóm Q2b trang 2 (bản sao từ Kiên) | 19 |
| `q3b_or_table.csv` | odds ratio Q3b trang 3 | 34 |
| `q3b_model_fit.csv` | so sánh M1/M2/M3 trang 3 | 3 |
| `q4_forecast_S1.csv` | dự báo S1 trang 3 (bản sao từ Khôi) | 1.065 |
| `q4_forecast_S2.csv` | dự báo S2 trang 3 (bản sao từ Khôi) | 1.059 |
| `q4_model_comparison.csv` | bảng so sánh mô hình Q4 (dự phòng) | 8 |
| `reliability_table.csv` | bảng độ tin cậy trang 1 | 17 |

`README_nguon_CSV.md` ghi rõ file nào lấy từ thành viên nào. Q5/Q6 chưa có file tại thời điểm làm B11 nên **không dựng biểu đồ Q5/Q6**; ghi chú này vào trang 3.

3. Mở Power BI Desktop. Nếu chưa có, dùng bản đã cài ở `C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe`.

## 1. Nạp dữ liệu

1. `Home` → `Get data` → `Text/CSV` (Nhận dữ liệu → Văn bản/CSV).
2. Vào `Bao/05_Code_Output/outputs/powerbi/`, chọn tất cả file CSV (Ctrl+A) → `Open`.
   - Nếu hộp thoại chỉ cho chọn một file, nạp lần lượt 14 file; giữ nguyên tên bảng.
3. Ở cửa sổ xem trước, đặt:
   - `File origin` = **65001: Unicode (UTF-8)**.
   - `Delimiter` = **Comma**.
   - `Data type detection` = **Based on first 200 rows**.
4. Bấm `Load` (không cần `Transform Data` nếu dữ liệu hiện đúng).
5. Kiểm tra kiểu dữ liệu ở chế độ `Data view` (biểu tượng bảng bên trái):
   - Các cột số (`gia_tri`, `n`, `median_lv_adj`, `mean_lv_adj`, `OR_M1`, `AIC`, `McFadden_R2`, `actual`, `forecast`, `lo95`, `hi95`, …) phải là **Decimal Number** hoặc **Whole Number**.
   - `q4_forecast_*[date]` phải là **Date**.
   - `kpi_overview[chi_so]`, `q3b_or_table[label]`, `q2b_group_means[group]` là **Text**.
   - Nếu cột số bị nhận là Text: chọn cột → `Transform` → `Data Type` → `Decimal Number`; nếu vẫn lỗi, dùng `Using Locale` → **English (United States)** vì file dùng dấu chấm thập phân.
6. Kiểm tra nhanh số dòng ở góc dưới bảng: `q1_by_hour` = 24, `q1_heatmap` = 168, `q1_by_category` = 15, `q2b_group_means` = 19, `q3b_or_table` = 34, `q3b_model_fit` = 3, `kpi_overview` = 12.

## 2. Tạo các độ đo (DAX)

Vào `Modeling` → `New measure` và tạo lần lượt. Tên bảng phải đúng như tên file (Power BI đặt theo tên file CSV).

```DAX
n_H =
CALCULATE (
    MAX ( kpi_overview[gia_tri] ),
    kpi_overview[chi_so] = "n_H (quần thể phân tích)"
)

So_kenh_H =
CALCULATE (
    MAX ( kpi_overview[gia_tri] ),
    kpi_overview[chi_so] = "Số kênh trong H"
)

So_video_trending =
CALCULATE (
    MAX ( kpi_overview[gia_tri] ),
    kpi_overview[chi_so] = "Số video từng lọt Trending"
)

Ty_le_viral =
CALCULATE (
    MAX ( kpi_overview[gia_tri] ),
    kpi_overview[chi_so] = "Tỷ lệ viral_A (%)"
) / 100

So_lan_do =
CALCULATE (
    MAX ( kpi_overview[gia_tri] ),
    kpi_overview[chi_so] = "Số lần đo (measurements)"
)

Trung_vi_lv_adj =
CALCULATE (
    MAX ( kpi_overview[gia_tri] ),
    kpi_overview[chi_so] = "Trung vị lv_adj trên H"
)

Chenh_gio =
MAX ( q1_by_hour[median_lv_adj] ) - MIN ( q1_by_hour[median_lv_adj] )

Chenh_gio_trong_kenh =
MAX ( q1_by_hour[median_lv_within_channel] ) - MIN ( q1_by_hour[median_lv_within_channel] )

AIC_M1 =
CALCULATE ( MAX ( q3b_model_fit[AIC] ), q3b_model_fit[model] = "M1 (đủ biến)" )

AIC_M3 =
CALCULATE ( MAX ( q3b_model_fit[AIC] ), q3b_model_fit[model] = "M3 (pub_slot thay pub_hour)" )

McFadden_M1 =
CALCULATE ( MAX ( q3b_model_fit[McFadden_R2] ), q3b_model_fit[model] = "M1 (đủ biến)" )
```

Định dạng:
- `n_H`, `So_kenh_H`, `So_video_trending`, `So_lan_do`: **Whole Number**, bật dấu phân cách nghìn.
- `Ty_le_viral`: **Percentage**, 2 chữ số thập phân.
- `Trung_vi_lv_adj`: **Decimal Number**, 4 chữ số thập phân (0,0895).
- `Chenh_gio`, `Chenh_gio_trong_kenh`: **Decimal Number**, 3 chữ số thập phân.
- `AIC_M1`, `AIC_M3`: **Decimal Number**, 1 chữ số thập phân.
- `McFadden_M1`: **Decimal Number**, 3 chữ số thập phân.

## 3. Trang 1 - Tổng quan

Đổi tên trang thành `1. Tổng quan`.

### 3.1. Sáu thẻ KPI (hàng trên)

Tạo 6 thẻ `Card` (hoặc `New card` nếu bản mới), lần lượt kéo các độ đo:

| Thẻ | Độ đo | Giá trị đúng |
| --- | --- | --- |
| Cỡ mẫu H | `n_H` | 139.227 |
| Số kênh trong H | `So_kenh_H` | 464 |
| Video từng lên Trending | `So_video_trending` | 1.039 |
| Tỷ lệ viral_A | `Ty_le_viral` | 10,01% |
| Số lần đo | `So_lan_do` | 1.066.405 |
| Trung vị lv_adj | `Trung_vi_lv_adj` | 0,0895 |

Đặt 6 thẻ thành một hàng ngang, chiều cao khoảng 90-100 px, cỡ số 20-24. Thêm một `Text box` nhỏ dưới hàng thẻ:

> Dữ liệu 22/10–12/11/2026 · 140.387 video master · 46 lần chụp Trending · 19 ngày đo

### 3.2. Bảng độ tin cậy (trái, giữa trang)

1. Chọn visual `Table`.
2. Kéo các cột: `tieu_chi`, `so_dem`, `mau_so`, `ty_le_pct`.
3. Đổi tiêu đề thành `Bảng 3.3 - Độ tin cậy dữ liệu`.
4. Định dạng `ty_le_pct` 2 chữ số thập phân; cỡ chữ 9.
5. (Tùy chọn) `Cell elements` → `Data bars` cho `ty_le_pct` để dễ so sánh.

Bảng có 17 dòng; nếu không đủ chỗ, giảm cỡ chữ hoặc chỉ giữ 10 dòng chính (ẩn like, tắt bình luận, trùng lặp, ngoại lai, likes > views, comments > views, views giảm). Không xóa dòng nào trong CSV; chỉ lọc hiển thị nếu cần.

### 3.3. Bảng mô tả Q1 (phải, giữa trang)

1. Chọn visual `Table`.
2. Kéo: `bien`, `n`, `mean`, `median`, `sd`, `cv`.
3. Ở `Filters` → `nhom` → chọn **Tất cả** (6 dòng).
4. Tiêu đề: `Q1 - Thống kê mô tả (toàn bộ H)`.
5. Định dạng `mean`, `median`, `sd` 2 chữ số; `cv` 2 chữ số; cỡ chữ 9.

### 3.4. Cột theo ngày đăng (dưới cùng)

1. Chọn `Clustered column chart` (cột đứng).
2. Trục X: `dow_name`; trục Y: `median_lv_adj` (Average).
3. Sắp xếp trục X theo `pub_dow`: vào `Data view`, chọn `q1_by_dow[dow_name]` → `Column tools` → `Sort by column` → `q1_by_dow[pub_dow]`.
4. Bật data labels, tiêu đề `Q1 - Trung vị lv_adj theo ngày đăng`.
5. Thêm ghi chú nhỏ: *Khác biệt theo thứ nhỏ; xem thêm heatmap giờ × thứ ở trang 2.*

## 4. Trang 2 - Giờ đăng và thể loại

Đổi tên trang thành `2. Giờ đăng và thể loại`.

### 4.1. Biểu đồ kết hợp theo giờ (trên trái)

1. Chọn `Line and clustered column chart`.
2. Trục X: `pub_hour` (đặt `Type` = **Categorical** để đủ 24 giờ, không nối tắt).
3. Column Y: `n` (Sum).
4. Line Y: `median_lv_adj` (Average) và `median_lv_within_channel` (Average).
5. `Format` → `Y axis` → bật `Secondary y-axis` cho hai đường (vì `n` lớn hơn nhiều so với lv_adj).
6. Đổi màu: `median_lv_adj` xanh đậm, `median_lv_within_channel` cam; bật markers.
7. Tiêu đề: `Q1 - Số video và trung vị lv_adj theo giờ đăng`.
8. Thêm hai thẻ nhỏ cạnh biểu đồ:
   - `Chênh lệch thô` = `Chenh_gio` → 0,890
   - `Trong kênh` = `Chenh_gio_trong_kenh` → 0,209

### 4.2. Heatmap giờ × thứ (trên phải)

1. Chọn visual `Matrix`.
2. `Rows`: `pub_hour`.
3. `Columns`: `dow_name`.
   - Trước đó vào `Data view`, chọn `q1_heatmap[dow_name]` → `Column tools` → `Sort by column` → `q1_heatmap[pub_dow]` (sắp riêng cho bảng này; `q1_by_dow` ở trang 1 cũng cần sắp cột `dow_name` của nó).
4. `Values`: `median_lv_adj_masked` (Average). Mỗi ô chỉ có 1 dòng nên Average = giá trị.
5. `Format` → `Cell elements` → `Background color` → `fx`:
   - Format style: **Gradient**.
   - Minimum: **-0.5** (màu đỏ).
   - Maximum: **0.5** (màu xanh).
   - Center: **0** (màu trắng).
6. Thêm `n` vào `Tooltips` (Sum) để rê chuột thấy số video từng ô.
7. Tiêu đề: `Q1 - Heatmap giờ × thứ (ô n < 30 để trống)`.
8. Ô trống là các cặp giờ × thứ có `n < 30`, đúng thiết kế; không điền 0.

### 4.3. Hai biểu đồ thể loại (dưới trái và dưới giữa)

**Biểu đồ 1 - chênh lệch thô:**

1. `Clustered bar chart` (thanh ngang).
2. Trục Y: `category_name`; trục X: `median_lv_adj` (Average).
3. `Filters` → `rank_n` → **is less than or equal to 10**.
4. Sắp xếp theo `median_lv_adj` giảm dần; bật data labels; cỡ chữ 9.
5. Tiêu đề: `Q1 - Trung vị lv_adj theo thể loại (10 thể loại nhiều video nhất)`.

**Biểu đồ 2 - sau khi trừ trung vị kênh:**

1. Sao chép biểu đồ 1.
2. Đổi trục X thành `median_lv_within_channel` (Average).
3. Sắp xếp lại theo giá trị này; đặt trục X từ **-0,03** đến **0,03** để thấy khác biệt.
4. Tiêu đề: `Sau khi trừ trung vị kênh (cùng 10 thể loại)`.
5. Thêm ghi chú: *Chênh lệch thô 1,752 log10 chỉ còn 0,018 sau khi trừ kênh.*

### 4.4. Trung bình nhóm Q2b (dưới phải)

1. `Clustered bar chart`.
2. Trục Y: `group`; trục X: `mean_lv_adj` (Average).
3. `Filters` → `factor` → chọn **pub_slot** (5 nhóm: Khuya, Sáng, Chiều, Tối, Đêm).
4. Sắp xếp theo `mean_lv_adj` giảm dần; bật data labels.
5. Thêm `ci_low`, `ci_high`, `n` vào `Tooltips`.
6. Tiêu đề: `Q2b - Trung bình lv_adj theo khung giờ (95% CI trong tooltip)`.

## 5. Trang 3 - Viral và dự báo

Đổi tên trang thành `3. Viral và dự báo`.

### 5.1. Odds ratio Q3b (trên trái)

1. Ở `Data view`, chọn bảng `q3b_or_table` → `New column`:
   ```DAX
   Abs_log_OR = ABS ( LN ( q3b_or_table[OR_M1] ) )
   ```
2. Chọn `Clustered bar chart` (thanh ngang).
3. Trục Y: `label`; trục X: `OR_M1` (Average).
4. `Filters` cho visual:
   - `term` **is not** `const`.
   - `term` **does not begin with** `cat:`.
   - `Abs_log_OR` → **Top N** → Top **12** → By value `Abs_log_OR`.
5. Sắp xếp theo `OR_M1` giảm dần.
6. Bật `Log scale` cho trục giá trị (`Format` → `X axis` → `Log scale`). Nếu bản Power BI không cho bật ở trục X, đổi sang `Clustered column chart` và bật `Log scale` ở trục Y.
7. `Analytics` → `Reference line` → `Constant` = **1**, nhãn `OR = 1`.
8. Thêm `OR_lo95_M1`, `OR_hi95_M1`, `p_M1` vào `Tooltips`.
9. Tiêu đề: `Q3b - Odds ratio của viral_A (M1, 12 biến mạnh nhất; thang log)`.
10. Ghi chú dưới biểu đồ: *OR > 1: tăng khả năng viral; OR < 1: giảm. Đây là liên quan, không phải nhân quả.*

### 5.2. So sánh mô hình Q3b (trên phải)

1. Chọn `Table`.
2. Kéo: `model`, `n`, `n_pos`, `pct_pos`, `AIC`, `McFadden_R2`, `converged`.
3. Định dạng `AIC` 1 chữ số, `McFadden_R2` 3 chữ số, `pct_pos` 2 chữ số.
4. Tiêu đề: `Q3b - So sánh M1 / M2 / M3`.
5. Có thể thêm 2 thẻ nhỏ: `AIC_M1` = 67.617,0; `McFadden_M1` = 0,254.

### 5.3. Dự báo Q4 - S1 (dưới trái)

1. Chọn `Line chart`.
2. Trục X: `date`.
3. Trục Y: `actual`, `forecast`, `lo95`, `hi95` (Average).
4. `Filters` → `split` → chọn **test** và **forecast** (56 điểm: 28 ngày test + 28 ngày dự báo). Nếu muốn xem cả lịch sử, đổi filter thành `date` ≥ 2026-07-01.
5. Đặt `actual` màu xám đậm, `forecast` màu xanh, `lo95`/`hi95` màu xanh nhạt/nét đứt.
6. Tiêu đề: `Q4 - Dự báo S1 (số video/ngày) 4 tuần tới`.
7. Ghi chú: *28 ngày test + 28 ngày dự báo; khoảng tin cậy 95% là hai đường lo95/hi95.*

### 5.4. Dự báo Q4 - S2 (dưới phải)

1. Sao chép biểu đồ S1.
2. Đổi bảng sang `q4_forecast_S2` (cùng tên cột).
3. Tiêu đề: `Q4 - Dự báo S2 (lv_adj trung bình/ngày)`.
4. Giữ filter `split` = test/forecast.

### 5.5. Ghi chú Q5/Q6

Thêm một `Text box` nhỏ ở cuối trang:

> Q5/Q6 chưa có CSV trong `05_Code_Output/outputs/` tại thời điểm 17/11 17:00, nên không dựng biểu đồ theo quy ước B11. Khi Quỳnh bổ sung `q5_model_comparison.csv`, `q5_importance.csv`, `q6_cluster_profile.csv`, `q6_pca_points.csv`, chạy lại `python python/prepare_b11_inputs.py` rồi `Refresh`.

Nếu file đã có trước khi làm:

- **Q5 - so sánh mô hình:** bảng `model` × các cột `pr_auc_mean`, `roc_auc_mean`, `f1_mean` (hoặc tên cột thực tế); thêm cột chênh lệch so với mô hình nền.
- **Q5 - importance:** `Clustered bar chart`, trục Y `feature`, trục X `importance`, Top 10.
- **Q6 - hồ sơ cụm:** bảng `cluster`, `n`, `pct`, 6 biến trung vị, `ever_trending_rate`.
- **Q6 - PCA:** `Scatter chart`, X `pc1`, Y `pc2`, Legend `cluster`.

## 6. Định dạng chung

1. `View` → `Page view` → `Actual size`; `Format` → `Page setup` → `16:9`.
2. Nền trang trắng hoặc xám rất nhạt; tiêu đề trang đặt bằng `Text box` cỡ 20-24, đậm.
3. Dùng font `Segoe UI`; tiêu đề visual 12-14, nội dung 9-10.
4. Căn đều các visual: chọn nhiều visual → `Format` → `Align` → `Align top` / `Distribute horizontally`.
5. Mỗi trang có footer:
   > Nguồn: `05_Code_Output/outputs/` · Dữ liệu 22/10–12/11/2026 · Số liệu chốt 13/11/2026
6. Đặt tên trang lần lượt `1. Tổng quan`, `2. Giờ đăng và thể loại`, `3. Viral và dự báo`.

## 7. Lưu file và xuất 3 ảnh PNG

1. `File` → `Save as` → lưu vào:
   `Bao/outputs/powerbi/dashboard.pbix`
2. Kiểm tra từng trang không bị cắt chữ, không có visual lỗi đỏ.
3. Xuất ảnh từng trang:
   - Cách 1 (nhanh): mở trang → `View` → `Full screen` (hoặc thu gọn pane) → `Win + Shift + S` → chọn đúng vùng trang → lưu:
     - `Bao/report/assets/Hinh_D1.png`
     - `Bao/report/assets/Hinh_D2.png`
     - `Bao/report/assets/Hinh_D3.png`
   - Cách 2 (nét hơn): `File` → `Export` → `Export to PDF`, sau đó chuyển từng trang PDF sang PNG (150-200 dpi) và lưu đúng 3 tên trên.
4. Mở lại 3 ảnh để chắc chắn đọc được số và không bị mất góc.
5. Chép `dashboard.pbix` và 3 ảnh vào gói nộp:
   - `Bao/05_Code_Output/outputs/powerbi/dashboard.pbix`
   - `Bao/05_Code_Output/report/assets/Hinh_D1.png` … `Hinh_D3.png`
   - Hoặc chạy `python python/make_code_output.py --force` để tự chép toàn bộ (nhớ kiểm tra lại gói sau khi chạy).

## 8. Đối chiếu số trước khi chụp

| Chỉ tiêu | Giá trị đúng | Nguồn |
| --- | --- | --- |
| n_H | 139.227 | `kpi_overview.csv` |
| Số kênh trong H | 464 | `kpi_overview.csv` |
| Video từng lọt Trending | 1.039 | `kpi_overview.csv` |
| Tỷ lệ viral_A | 10,01% | `kpi_overview.csv` |
| Số lần đo | 1.066.405 | `kpi_overview.csv` |
| Trung vị lv_adj | 0,0895 | `kpi_overview.csv` |
| Ẩn lượt thích | 5.119 (3,65%) | `reliability_table.csv` |
| Tắt bình luận | 2.966 (2,11%) | `reliability_table.csv` |
| Chênh lệch thô theo giờ | 0,890 | `q1_by_hour.csv` |
| Chênh lệch trong kênh | 0,209 | `q1_by_hour.csv` |
| log_subs OR (M1) | 8,83 (6,20–12,57) | `q3b_or_table.csv` |
| AIC M1 / M3 | 67.617,0 / 67.531,0 | `q3b_model_fit.csv` |
| McFadden M1 | 0,254 | `q3b_model_fit.csv` |

Nếu một số trên dashboard lệch: kiểm tra filter visual, kiểu dữ liệu (Text thay vì Number), hoặc đang dùng nhầm bảng (ví dụ `kpi_dates` thay vì `kpi_overview`).

## 9. Lỗi thường gặp

| Hiện tượng | Cách sửa |
| --- | --- |
| Số thập phân thành Text | `Transform` → `Data Type` → `Decimal Number`; dùng `Using Locale` = English (United States) |
| Chữ Việt bị lỗi font | File origin = 65001 UTF-8; kiểm tra `File origin` khi nạp lại |
| `kpi_overview` có ngày ở cột số | Dùng `kpi_dates.csv` cho ngày; `kpi_overview` chỉ còn 12 dòng số |
| Heatmap có ô trống | Đúng: ô có `n < 30` đã bị che bằng `median_lv_adj_masked` |
| Cột thứ trong matrix xếp sai | `Data view` → `dow_name` → `Sort by column` → `pub_dow` |
| Đường `n` và `lv_adj` chung trục, đường bị bẹp | Bật `Secondary y-axis` cho line values |
| Không thấy `Log scale` ở trục X | Đổi sang `Clustered column chart`, bật `Log scale` ở trục Y |
| `q4_forecast` không có `forecast` | Bản sao đã đổi `pred` → `forecast`; kiểm tra đang dùng file trong `outputs/powerbi/` |
| Q5/Q6 không có | Bỏ biểu đồ, ghi chú như mục 5.5; không chờ |

## 10. Sau khi có 3 ảnh

1. Đặt 3 ảnh đúng tên trong `Bao/report/assets/`: `Hinh_D1.png`, `Hinh_D2.png`, `Hinh_D3.png`.
2. Chạy `node report/build_muc_bao.js`. Phụ lục D tự phát hiện đủ 3 ảnh và chèn Hình D.1–D.3 kèm chú thích; không cần sửa tay.
3. Chép `Muc_Bao.docx` vào 3 vị trí như cũ:
   - `Bao/report/Muc_Bao.docx`
   - `Bao/05_Code_Output/report/Muc_Bao.docx`
   - `Bảo/Muc_Bao.docx`
   - Hoặc chạy `python python/make_code_output.py --force` để đồng bộ gói 05, rồi chép bản ở `Bao/report/Muc_Bao.docx` sang `Bảo/Muc_Bao.docx`.
4. Kiểm tra lần cuối: mở `dashboard.pbix`, bấm `Refresh`; nếu số không đổi thì ảnh và báo cáo khớp.
