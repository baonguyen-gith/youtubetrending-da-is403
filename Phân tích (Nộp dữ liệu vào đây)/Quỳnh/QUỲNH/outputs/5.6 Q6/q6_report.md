# Q6 — Phân cụm video bằng K-means

*Sinh tự động: 2026-11-15 12:43 — dữ liệu `measurements.csv` và `labels.csv` (bản final 12/11/2026).*

## 1. Lọc dữ liệu

| Bước | Số dòng đo | Số video |
|---|---:|---:|
| 0. Toàn bộ measurements.csv | 1,066,405 | 140,387 |
| 1. Chỉ giữ is_last_of_day = TRUE | 411,843 | 140,387 |
| 2. Có >= 5 ngày đo | 290,192 | 26,520 |
| 3. Khoảng cách lần đo đầu–cuối >= 5 ngày | 282,652 | 25,012 |
| 4. Đủ likes/comments (không ẩn like, không tắt comment) | 256,985 | 22,886 |
| 5. Views lần đo cuối > 0 | 256,593 | 22,851 |
| 6. Ghép được subscribers + thể loại (dùng cho hồ sơ cụm) |  | 22,851 |

## 2. Sáu biến hành vi

| Biến | Công thức | Ý nghĩa |
|---|---|---|
| `vpd_log` | log10(max(views_cuoi / age_days_cuoi, 1)) | Video lan nhanh hay chậm tính trung bình cả đời |
| `growth_log` | log10(views_cuoi) − log10(max(views_dau, 1)) | Tổng mức tăng lượt xem trong cửa sổ quan sát |
| `momentum` | log10((vpd_khoảng_cuối + 0,01) / (vpd_trung_binh + 0,01)) | Dương: đang tăng tốc; âm: đã nguội dần |
| `like_rate` | likes_cuoi / views_cuoi (cắt phân vị 99) | Mức yêu thích trên mỗi lượt xem |
| `comment_rate` | comments_cuoi / views_cuoi (cắt phân vị 99) | Mức bình luận trên mỗi lượt xem |
| `volatility` | độ lệch chuẩn / trung bình của vpd từng khoảng (cắt phân vị 99) | Tốc độ tăng có đều hay dồn cục |

## 3. Chọn số cụm k

| k | Inertia | Silhouette | Davies-Bouldin | Cụm nhỏ nhất (%) | Dùng được |
|---:|---:|---:|---:|---:|---|
| 2 | 110,567 | 0.2659 | 1.591 | 28.9 | có |
| 3 | 93,851 | 0.2962 | 1.437 | 8.0 | có |
| 4 | 80,152 | 0.3142 | 1.301 | 4.6 | không |
| 5 | 69,973 | 0.3275 | 1.111 | 3.0 | không |
| 6 | 62,242 | 0.2026 | 1.255 | 2.9 | không |
| 7 | 57,124 | 0.2039 | 1.274 | 2.8 | không |
| 8 | 52,858 | 0.2052 | 1.229 | 2.8 | không |

**Chọn k=3 vì silhouette cao nhất trong các k thoả ràng buộc mỗi cụm >= 5%. Elbow (giảm inertia mạnh nhất) gợi ý k=2.**

## 4. Độ ổn định

- 20 lần bootstrap 80/20, ARI trung bình **0.991** (nhỏ nhất 0.982, lớn nhất 0.997).
- ARI ≥ 0,6: phân cụm ổn định, có thể diễn giải.

## 5. Hồ sơ cụm (Bảng 5.17)

| Cụm | n | % | vpd_log | growth_log | momentum | like_rate | comment_rate | volatility | Subs (trung vị) | Tuổi (ngày) | % Trending | % viral_A | Thể loại nổi bật |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 1,820 | 8.0 | 2.503 | 0.037 | -1.302 | 0.0389 | 0.0024 | 0.680 | 188,000 | 19 | 2.1 | 8.9 | Music (29%) |
| 2 | 15,222 | 66.6 | 3.245 | 0.040 | -1.257 | 0.0074 | 0.0002 | 0.583 | 516,000 | 20 | 4.8 | 14.6 | Gaming (32%) |
| 3 | 5,809 | 25.4 | 2.011 | 0.010 | -3.258 | 0.0040 | 0.0000 | 1.569 | 397,000 | 22 | 0.6 | 0.5 | News & Politics (38%) |

## 6. Liên hệ cụm với thể loại và viral_A

| Cặp biến | n | Chi-square | df | p-value | Cramér's V |
|---|---:|---:|---:|---|---:|
| Cụm × thể loại | 22,851 | 4,970.21 | 20 | < 1e-300 | 0.330 |
| Cụm × viral_A | 22,782 | 896.54 | 2 | 2.09e-195 | 0.198 |

## 7. Đối chiếu với R

| Chỉ tiêu | Giá trị |
|---|---|
| Số video | 22,851 |
| Số biến dùng để cụm | 6 (z_vpd_log, z_growth_log, z_momentum, z_like_rate, z_comment_rate, z_volatility) |
| k (Python chọn) | 3 |
| Số video mỗi cụm (R) | 1813 / 5812 / 15226 |
| ARI (Python vs R) | 0.9986 |
| Kết luận | PASS |

Tiêu chí đạt: ARI ≥ 0,8. Nhãn cụm của R có thể đánh số khác Python nhưng ARI đo mức trùng khớp của cách chia, không phụ thuộc số thứ tự.


## 8. Hình và dữ liệu kèm theo

- Hình 5.9: `q6_figure_5_9.png` — PC1 29.2%, PC2 19.4% phương sai.
- `q6_pca_points.csv`: toạ độ PCA của từng video, kèm cụm.
- `q6_cluster_profile.csv`: hồ sơ cụm (Bảng 5.17).
- `q6_cluster_assignments.csv`: nhãn cụm của từng video và 6 biến gốc.
- `q6_R_input.csv`: dữ liệu đã chuẩn hoá để R chạy lại K-means (đối chiếu ARI).

## 9. Cách đọc kết quả

- Cụm hình thành từ **hành vi** (tốc độ, tăng trưởng, tương tác), không phải từ quy mô kênh: subscribers và tuổi video chỉ dùng để mô tả sau khi phân cụm.
- Chênh lệch giữa các cụm là **mô tả**, không chứng minh quan hệ nhân quả.
- Mọi con số tính trên mẫu video có ≥ 5 ngày đo, nên không đại diện cho toàn bộ video của kênh.
- Tham số chuẩn hoá: vpd_log mean=2.8658, scale=1.0566; growth_log mean=0.1993, scale=0.4824; momentum mean=-1.8079, scale=1.1986; like_rate mean=0.0125, scale=0.0173; comment_rate mean=0.0005, scale=0.0009; volatility mean=0.9258, scale=0.6930.