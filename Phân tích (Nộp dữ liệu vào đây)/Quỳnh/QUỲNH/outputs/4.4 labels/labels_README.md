# labels.csv – Từ điển cột

Sinh bởi `05_Code_Output/python/01_make_labels.py`.

## Quần thể H và cách xác định `in_H`

`in_H = 1` khi video thỏa **đồng thời cả 4 điều kiện** của Mục 4.1:

| # | Điều kiện | Cột kiểm tra | Ý nghĩa |
|---|---|---|---|
| 1 | Video nằm trong lịch sử thu thập | `in_history == TRUE` | Video đã từng xuất hiện trong dữ liệu crawl |
| 2 | Không phải livestream/sắp công chiếu | `is_live_or_upcoming == FALSE` | Loại video chưa có lượt xem ổn định |
| 3 | Có lượt xem | `views > 0` | Loại video không có dữ liệu lượt xem |
| 4 | Đã đủ 1 ngày tuổi | `age_days_last >= 1` | Để `views_per_day` không bị chia cho 0 hoặc quá nhiễu |

Trên bản dữ liệu hiện tại: 140,387 video → **139,227 video `in_H = 1`** (1,160 video bị loại). Các điều kiện có thể trùng nhau nên số bị loại **không phải** tổng của 4 con số riêng lẻ.

Video có `in_H = 0` vẫn được giữ trong `labels.csv` để đối chiếu, nhưng **không dùng** khi tính nhãn hay huấn luyện mô hình. Các cột nhãn của chúng để trống (NA).

| Cột | Ý nghĩa |
|---|---|
| video_id | Khóa video (duy nhất) |
| channel_id | Khóa kênh |
| in_H | 1 nếu thuộc quần thể H (Mục 4.1) |
| age_days_last | Tuổi video (ngày) tại lần đo cuối |
| age_b | Nhóm tuổi 14 mức [a,b) (Mục 4.2) |
| views | Lượt xem lũy kế tại lần đo cuối |
| views_per_day | Lượt xem / ngày |
| log_views | log10(views) |
| rank_in_age | Hạng trung bình của log_views trong age_b (1 = thấp nhất) |
| n_in_age | Số video của age_b trong H |
| pct_in_age | rank_in_age / n_in_age |
| viral_A | 1 nếu pct_in_age >= 0.90, 0 nếu không, NA ngoài H |
| lvpd | log10(max(views_per_day, 1)) |
| ch_med_loo | Trung vị lvpd của các video khác cùng kênh & age_b (leave-one-out); NA nếu < 5 video khác |
| n_peers_loo | Số video khác cùng kênh & age_b |
| breakout_B | 1 nếu lvpd − ch_med_loo >= log10(2), 0 nếu không, NA nếu không đủ peer |
| pub_date_vn | Ngày đăng (giờ Việt Nam, YYYY-MM-DD) |
| is_short_60 | Video <= 60 giây |
| ever_trending | Từng lọt Trending |
| in_window_C | 1 nếu không ngắn và đăng trong cửa sổ in_window_C |
| viral_C | 1 nếu ever_trending trong in_window_C, 0 nếu không, NA ngoài cửa sổ |

## Cửa sổ in_window_C

- Bắt đầu: 2026-10-19
- Kết thúc: 2026-11-04 (ngày Trending cuối 2026-11-12 trừ 8 ngày)

## Cách dùng

Python:

```python
import pandas as pd
lb = pd.read_csv('labels.csv', dtype={'video_id': str,
      'viral_A': 'Int8', 'breakout_B': 'Int8', 'viral_C': 'Int8'})
h = lb[lb.in_H]
y = h.loc[h.viral_A.notna(), 'viral_A'].astype(int)
```

R:

```r
lb <- read.csv('labels.csv', na.strings = c('', 'NA'))
h <- subset(lb, in_H == 1)
table(h$viral_A, useNA = 'ifany')
```

## Lưu ý

- Không dùng `viral_A`/`breakout_B`/`viral_C` làm biến đầu vào X: đây là nhãn (target), không phải feature (Mục 4.5).
- Khi có `data_final_20261113`, chạy lại script và cập nhật Bảng 5.12 + bộ 6 số kiểm tra.
