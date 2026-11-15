# Kiểm tra labels.csv

## Bộ 6 số kiểm tra chung (Bảng 4.3)

| # | Số cần in ra | Giá trị |
|---|---|---|
| 1 | n_H | 139,227 |
| 2 | Số kênh trong H | 464 |
| 3 | Số video nhóm [7,10) | 2,325 |
| 4 | Tổng viral_A | 13,931 |
| 5 | Trung vị lv_adj (4 chữ số) | 0.0895 |
| 6 | ever_trending trong H | 892 |

## Bảng tóm tắt nhãn (Bảng 5.12)

| Nhãn | Định nghĩa | Đủ điều kiện | Dương | Tỷ lệ dương |
|---|---|---:|---:|---:|
| viral_A | pct_in_age >= 0.90 (hạng trung bình log_views trong nhóm tuổi / n nhóm tuổi) | 139,227 | 13,931 | 10.01% |
| breakout_B | lvpd - ch_med_loo >= log10(2), cần >= 5 video khác cùng kênh & nhóm tuổi | 134,703 | 34,055 | 25.28% |
| viral_C | ever_trending trong in_window_C (không ngắn, đăng trong cửa sổ) | 10,925 | 550 | 5.03% |

## Thông tin phiên bản dữ liệu

| Trường | Giá trị |
|---|---|
| source_file | videos_master.csv |
| n_rows_videos_master | 140387 |
| n_channels_videos_master | 566 |
| n_ever_trending_total | 1039 |
| last_obs_ts_max | 2026-11-12 12:41:23+00:00 |
| pub_date_vn_max | 2026-11-12 |
| last_trending_date | 2026-11-12 |
| window_C | ['2026-10-19', '2026-11-04'] |
| expected_data_final | data_final_20261113 |

> **Cảnh báo:** nếu `n_rows_videos_master` = 96.334 và `n_ever_trending_total` = 636 thì đây là bản `data_clean` ngày 03/11, chưa phải `data_final_20261113`. Phải chạy lại script này trên data_final trước hạn 15/11 23:59.

## Kiểm tra ràng buộc

- viral_A chiếm 10.0060% của H (ĐẠT mức 9–11% theo Mục 4.4).
- viral_C có 550 video dương (đủ 100 để huấn luyện ở Q5).
- Số video không có đủ 5 video khác cùng kênh & nhóm tuổi: 4,524 (breakout_B = NA).
- Cột nhãn viral_A / breakout_B / viral_C ghi 1/0, để trống (NA) khi video không đủ điều kiện. Lọc bằng `in_H` hoặc `in_window_C` trước khi huấn luyện.
