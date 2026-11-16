# Từ điển dữ liệu (data_dictionary.md)

Sinh bởi `gen_data_dictionary.py` từ thư mục `data_final_20261113`. Cột *% rỗng* và *ví dụ* đo trực tiếp từ file; các cột mô tả được viết tay và kiểm chứng với dữ liệu.

Quy ước chung: thời điểm lưu ở UTC (ký hiệu +00:00); các cột `pub_*` đã đổi sang giờ Việt Nam (UTC+7); `pub_dow = 0` là Thứ Hai; file CSV mã hóa `utf-8-sig`; `video_id` luôn đọc là chuỗi.

## videos_master.csv

Mỗi dòng MỘT VIDEO, số liệu của lần đo mới nhất (55 cột). Dùng cho Q1, Q2, Q3, Q5. Số dòng: **140,387**; số cột: **55**.

| Cột | Kiểu | % rỗng | Ví dụ | Ý nghĩa | Đơn vị | Cách tính | Có thể rỗng? Vì sao |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| `video_id` | str | 0.00 | KurrJn--qDE | Mã video YouTube (11 ký tự) | chuỗi | Do YouTube cấp; đọc dưới dạng chuỗi | Không |
| `channel_id` | str | 0.00 | UCEKXigs8deXOCRdKELgLrGQ | Mã kênh đăng video | chuỗi | Từ API | Không |
| `title` | str | 0.00 | Mukbang Xúc Xích Phô Mai BẮN TÙM LUM🥵😍 | Tiêu đề video | văn bản | Từ API (một số tiêu đề gốc chứa ký tự ? thật) | Không |
| `published_ts` | str | 0.00 | 2026-08-16 12:00:11+00:00 | Thời điểm đăng video | UTC | snippet.publishedAt của API | Không |
| `category_id` | int64 | 0.00 | 22 | Mã thể loại YouTube | số nguyên | snippet.categoryId | Không |
| `tags_count` | int64 | 0.00 | 0 | Số thẻ tag người đăng gắn | số | Đếm phần tử của snippet.tags; 0 nếu không có tag | Không (0 nếu không gắn tag) |
| `duration_sec` | float64 | 0.01 | 88.0 | Độ dài video | giây | Đổi từ contentDetails.duration (ISO 8601) | Có: một số ít video không trả độ dài; video live/upcoming có thể bằng 0 |
| `last_obs_ts` | str | 0.00 | 2026-10-22 14:11:32+00:00 | Thời điểm của lần đo mới nhất của video | UTC | Lớn nhất của collected_ts trong measurements | Không |
| `views` | float64 | 0.00 | 1339533.0 | Lượt xem ở lần đo mới nhất | lượt | statistics.viewCount (đã làm chuỗi không giảm bằng cummax) | Không |
| `likes` | float64 | 3.69 | 26685.0 | Lượt thích ở lần đo mới nhất | lượt | statistics.likeCount; likes > views bị đặt NaN | Có: người đăng ẩn lượt thích (likes_hidden) hoặc nhiễu API |
| `comments` | float64 | 2.12 | 930.0 | Số bình luận ở lần đo mới nhất | bình luận | statistics.commentCount; comments > views bị đặt NaN | Có: tắt bình luận (comments_disabled) hoặc nhiễu API |
| `age_days_last` | float64 | 0.00 | 67.09121527777778 | Tuổi video tại lần đo mới nhất | ngày | (last_obs_ts − published_ts) / 86400 | Không |
| `n_obs` | int64 | 0.00 | 1 | Số lần video được đo | lần | Đếm dòng của video trong measurements | Không |
| `is_live_or_upcoming` | bool | 0.00 | False | Video đang phát trực tiếp hoặc chưa phát | TRUE/FALSE | Từ liveBroadcastContent | Không |
| `first_obs_ts` | str | 0.00 | 2026-10-22 14:11:32+00:00 | Thời điểm lần đo đầu tiên | UTC | Nhỏ nhất của collected_ts | Không |
| `first_obs_age_days` | float64 | 0.00 | 67.09121527777778 | Tuổi video tại lần đo đầu tiên | ngày | (first_obs_ts − published_ts) / 86400 | Không |
| `in_history` | bool | 0.00 | True | Video có trong dữ liệu lịch sử kênh | TRUE/FALSE | TRUE nếu video xuất hiện trong playlistItems của kênh | Không |
| `trend_days` | int64 | 0.00 | 0 | Số ngày video có mặt trong Trending | ngày | Số run_date khác nhau của video trong trending_clean | Không (0 nếu chưa từng lọt) |
| `trend_best_rank` | float64 | 99.26 | 118.0 | Hạng Trending tốt nhất (số nhỏ = cao) | hạng 1–200 | min(rank) trong trending_clean | Có: rỗng nếu video chưa từng lọt Trending |
| `trend_mean_rank` | float64 | 99.26 | 150.0 | Hạng Trending trung bình | hạng | mean(rank) | Có: như trend_best_rank |
| `trend_first_ts` | str | 99.26 | 2026-10-26 05:45:20+00:00 | Thời điểm lần đầu video xuất hiện trong Trending | UTC | min(run_ts) của video trong trending_clean | Có: như trend_best_rank |
| `trend_age_first_days` | float64 | 99.26 | 4.961828703703704 | Tuổi video lúc lần đầu vào Trending | ngày | (trend_first_ts − published_ts) / 86400 | Có: như trend_best_rank |
| `ever_trending` | bool | 0.00 | False | Video từng lọt Trending trong giai đoạn thu thập | TRUE/FALSE | trend_days > 0 | Không |
| `pub_date_vn` | str | 0.00 | 2026-08-16 | Ngày đăng theo giờ Việt Nam | YYYY-MM-DD | Đổi published_ts sang UTC+7 rồi lấy ngày | Không |
| `pub_hour` | int64 | 0.00 | 19 | Giờ đăng theo giờ Việt Nam | 0–23 | Giờ của published_ts ở UTC+7 | Không |
| `pub_dow` | int64 | 0.00 | 6 | Thứ đăng | 0–6 (0 = Thứ Hai) | dayofweek của pub_date_vn | Không |
| `pub_is_weekend` | bool | 0.00 | True | Đăng vào cuối tuần | TRUE/FALSE | pub_dow ∈ {5, 6} | Không |
| `pub_month` | int64 | 0.00 | 8 | Tháng đăng (1–12, không kèm năm) | 1–12 | Tháng của pub_date_vn | Không |
| `pub_slot` | str | 0.00 | Tối 18-21h | Khung giờ đăng (5 nhóm) | nhãn | Khuya 0–5h; Sáng 6–11h; Chiều 12–17h; Tối 18–21h; Đêm 22–23h | Không |
| `title_len` | int64 | 0.00 | 38 | Độ dài tiêu đề | ký tự | len(title) | Không |
| `title_words` | int64 | 0.00 | 8 | Số từ trong tiêu đề | từ | Tách theo khoảng trắng | Không |
| `title_upper_ratio` | float64 | 0.00 | 0.4827586206896552 | Tỷ lệ chữ HOA trong các chữ cái của tiêu đề | 0–1 | Số chữ cái viết hoa / tổng số chữ cái (isalpha); ngoại lệ hiếm >1 với ký tự chữ trong vòng tròn như Ⓗ | Không |
| `title_has_question` | bool | 0.00 | False | Tiêu đề có dấu hỏi | TRUE/FALSE | Chứa ký tự ? | Không |
| `title_has_exclaim` | bool | 0.00 | False | Tiêu đề có dấu chấm than | TRUE/FALSE | Chứa ký tự ! | Không |
| `title_has_digit` | bool | 0.00 | False | Tiêu đề có chữ số | TRUE/FALSE | Chứa ký tự 0–9 | Không |
| `title_has_emoji` | bool | 0.00 | True | Tiêu đề có emoji | TRUE/FALSE | Chứa ký tự emoji Unicode (quy tắc regex của clean_data.py) | Không |
| `title_n_hashtag` | int64 | 0.00 | 0 | Số hashtag trong tiêu đề | số | Đếm ký tự # | Không |
| `title_has_bracket` | bool | 0.00 | False | Tiêu đề có ngoặc | TRUE/FALSE | Chứa ( ) hoặc [ ] (khớp ~99,5% với quy tắc này) | Không |
| `title_has_pipe` | bool | 0.00 | False | Tiêu đề có ký tự sổ đứng (pipe) | TRUE/FALSE | Chứa ký tự sổ đứng (pipe) | Không |
| `is_short_60` | bool | 0.00 | False | Video ngắn từ 60 giây trở xuống | TRUE/FALSE | 0 < duration_sec ≤ 60 (duration rỗng hoặc 0 → FALSE) | Không |
| `is_short_180` | bool | 0.00 | True | Video ngắn từ 180 giây trở xuống | TRUE/FALSE | 0 < duration_sec ≤ 180 | Không |
| `category_name` | str | 0.00 | People & Blogs | Tên thể loại | nhãn | Tra category_id theo bảng thể loại YouTube | Không |
| `like_rate` | float64 | 3.81 | 0.0199211217640774 | Tỷ lệ thích trên lượt xem | tỷ lệ 0–1 | likes / views | Có: khi likes rỗng |
| `comment_rate` | float64 | 2.26 | 0.000694271809653 | Tỷ lệ bình luận trên lượt xem | tỷ lệ | comments / views | Có: khi comments rỗng |
| `log_views` | float64 | 0.00 | 6.126953417116581 | Logarit cơ số 10 của lượt xem | log10(lượt) | log10(views); views = 0 không có giá trị hợp lệ | Có thể: khi views = 0 |
| `views_per_day` | float64 | 0.00 | 19965.847905033934 | Lượt xem trung bình mỗi ngày | lượt/ngày | views / max(age_days_last, 1) | Không |
| `likes_hidden` | bool | 0.00 | False | Người đăng ẩn lượt thích | TRUE/FALSE | Cờ từ API / likes rỗng | Không |
| `comments_disabled` | bool | 0.00 | False | Video tắt bình luận | TRUE/FALSE | Cờ từ API / comments rỗng | Không |
| `channel_name` | str | 0.00 | Khoai thích ăn cay | Tên kênh | văn bản | Từ channels_latest | Không |
| `subscribers` | int64 | 0.00 | 377000 | Số người đăng ký của kênh TẠI LÚC THU THẬP | người | statistics.subscriberCount; API làm tròn XUỐNG 3 chữ số có nghĩa | Không |
| `log_subs` | float64 | 0.00 | 5.576341350205793 | Logarit cơ số 10 của số người đăng ký | log10(người) | log10(subscribers) | Không |
| `subs_tier` | str | 0.00 | 100K-1M (mid) | Nhóm quy mô kênh | nhãn | <10K (nano); 10K–100K (micro); 100K–1M (mid); >1M (macro) | Không |
| `total_videos` | int64 | 0.00 | 232 | Tổng số video của kênh lúc thu thập | video | statistics.videoCount | Không |
| `total_views` | int64 | 0.00 | 259728604 | Tổng lượt xem của kênh lúc thu thập | lượt | statistics.viewCount của kênh | Không |
| `channel_age_days` | int64 | 0.00 | 657 | Tuổi kênh lúc thu thập | ngày | (channel_info_ts − channel_created) / 86400 | Không |

## measurements.csv

Mỗi dòng MỘT LẦN ĐO của một video (chuỗi theo thời gian). Dùng cho Q4 (S1, S2) và Q6; luôn lọc is_last_of_day = TRUE khi dựng chuỗi theo ngày. Số dòng: **1,066,405**; số cột: **23**.

| Cột | Kiểu | % rỗng | Ví dụ | Ý nghĩa | Đơn vị | Cách tính | Có thể rỗng? Vì sao |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| `video_id` | str | 0.00 | ---YYokQpsA | Mã video | chuỗi | Từ API | Không |
| `channel_id` | str | 0.00 | UCDzJOrDYIlAkW9iR4Z7qKCQ | Mã kênh | chuỗi | Từ API | Không |
| `title` | str | 0.00 | Bị em gái mờ lem bắt nạt! / Black Myth | Tiêu đề tại thời điểm đo | văn bản | Từ API | Không |
| `channel_title` | str | 0.00 | Cá Khô | Tên kênh tại thời điểm đo | văn bản | Từ API | Không |
| `published_ts` | str | 0.00 | 2024-08-27 16:27:57+00:00 | Thời điểm đăng | UTC | snippet.publishedAt | Không |
| `category_id` | int64 | 0.00 | 20 | Mã thể loại | số nguyên | snippet.categoryId | Không |
| `tags_count` | int64 | 0.00 | 0 | Số thẻ tag | số | Đếm snippet.tags | Không |
| `duration_sec` | float64 | 0.07 | 11045.0 | Độ dài video | giây | Đổi từ ISO 8601 | Có: như videos_master |
| `collected_ts` | str | 0.00 | 2026-10-22 15:00:44+00:00 | Thời điểm thu số liệu của video này | UTC | Giờ máy thu khi gọi API | Không |
| `run_ts` | str | 0.00 | 2026-10-22 14:50:31+00:00 | Thời điểm bắt đầu lượt chạy của script | UTC | Gán một lần cho mỗi lượt chạy | Không |
| `run_date` | str | 0.00 | 2026-10-22 | Ngày của lượt chạy | YYYY-MM-DD | Ngày của lượt chạy theo máy thu | Không |
| `views` | float64 | 0.00 | 51092.0 | Lượt xem sau khi làm chuỗi không giảm | lượt | cummax(views_raw) theo từng video | Không |
| `likes` | float64 | 7.66 | 904.0 | Lượt thích | lượt | statistics.likeCount; likes > views đặt NaN | Có: ẩn lượt thích hoặc nhiễu API |
| `comments` | float64 | 1.27 | 22.0 | Bình luận | bình luận | statistics.commentCount; comments > views đặt NaN | Có: tắt bình luận hoặc nhiễu API |
| `rank` | float64 | 99.07 | 180.0 | Hạng trong danh sách Trending ở lần chụp | hạng 1–200 | Thứ tự trong videos.list mostPopular | Có: chỉ có khi source = trending |
| `source` | str | 0.00 | history | Nguồn dòng đo | nhãn | trending / tracking / history | Không |
| `is_live_or_upcoming` | bool | 0.00 | False | Video live hoặc chưa phát | TRUE/FALSE | liveBroadcastContent | Không |
| `likes_hidden` | bool | 0.00 | False | Ẩn lượt thích | TRUE/FALSE | Cờ từ API | Không |
| `comments_disabled` | bool | 0.00 | False | Tắt bình luận | TRUE/FALSE | Cờ từ API | Không |
| `views_raw` | float64 | 0.00 | 51092.0 | Lượt xem thô từ API trước cummax | lượt | statistics.viewCount nguyên bản | Không |
| `age_days` | float64 | 0.00 | 785.9394328703704 | Tuổi video tại thời điểm đo | ngày | (collected_ts − published_ts) / 86400 | Không |
| `n_obs` | int64 | 0.00 | 1 | Thứ tự lần đo của video (đếm tích lũy) | lần | Số lần đo của video tính đến dòng này | Không |
| `is_last_of_day` | bool | 0.00 | True | Lần đo cuối cùng của video trong ngày | TRUE/FALSE | Dòng có collected_ts lớn nhất trong cùng (video_id, run_date) | Không |

## trending_clean.csv

Mỗi dòng MỘT VIDEO trong MỘT LẦN CHỤP danh sách Trending (hạng 1–200). Số dòng: **9,091**; số cột: **15**.

| Cột | Kiểu | % rỗng | Ví dụ | Ý nghĩa | Đơn vị | Cách tính | Có thể rỗng? Vì sao |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| `run_ts` | str | 0.00 | 2026-10-22 12:51:09+00:00 | Thời điểm chụp Trending | UTC | Giờ bắt đầu lượt chụp | Không |
| `run_date` | str | 0.00 | 2026-10-22 | Ngày chụp | YYYY-MM-DD | Phần ngày của run_ts | Không |
| `rank` | int64 | 0.00 | 1 | Hạng trong Trending | hạng 1–200 | Thứ tự API trả về | Không |
| `video_id` | str | 0.00 | XoFALjTUXhw | Mã video (đã khôi phục các mã bị hỏng #NAME?) | chuỗi | Khôi phục qua (channel_id, published_at) | Không |
| `title` | str | 0.00 | TRONG ĐÔI MẮT THIẾU NỮ - RHYDER / OFFI | Tiêu đề | văn bản | Đã sửa dấu từ bảng đối chiếu | Không |
| `channel_id` | str | 0.00 | UCPjbFSSZXI7ERLRt3O0CGBQ | Mã kênh | chuỗi | Từ API | Không |
| `channel_title` | str | 0.00 | RHYDER OFFICIAL | Tên kênh | văn bản | Đã sửa dấu | Không |
| `published_ts` | str | 0.00 | 2026-10-12 13:00:07+00:00 | Thời điểm đăng | UTC | snippet.publishedAt | Không |
| `category_id` | int64 | 0.00 | 10 | Mã thể loại | số nguyên | snippet.categoryId | Không |
| `tags_count` | int64 | 0.00 | 13 | Số thẻ tag | số | Đếm snippet.tags | Không |
| `duration_sec` | int64 | 0.00 | 285 | Độ dài | giây | Đổi từ ISO 8601 | Không |
| `views` | float64 | 0.01 | 2652530.0 | Lượt xem lúc chụp | lượt | statistics.viewCount | Không |
| `likes` | float64 | 1.99 | 47096.0 | Lượt thích lúc chụp | lượt | statistics.likeCount | Có: ẩn lượt thích |
| `comments` | float64 | 1.74 | 23707.0 | Bình luận lúc chụp | bình luận | statistics.commentCount | Có: tắt bình luận |
| `age_days` | float64 | 0.00 | 9.993773148148149 | Tuổi video lúc chụp | ngày | (run_ts − published_ts) / 86400 | Không |

## channels_latest.csv

Mỗi dòng MỘT KÊNH, số liệu kênh mới nhất. Số dòng: **566**; số cột: **10**.

| Cột | Kiểu | % rỗng | Ví dụ | Ý nghĩa | Đơn vị | Cách tính | Có thể rỗng? Vì sao |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| `channel_id` | str | 0.00 | UCsropiY0KCwC90UDBsGl8vA | Mã kênh | chuỗi | Từ API | Không |
| `channel_name` | str | 0.00 | Thiên Tú Official | Tên kênh | văn bản | snippet.title của kênh | Không |
| `channel_created` | str | 0.00 | 2013-08-16 04:41:40+00:00 | Thời điểm tạo kênh | UTC | snippet.publishedAt của kênh | Không |
| `subscribers` | int64 | 0.00 | 848000 | Số người đăng ký lần đo mới nhất | người | statistics.subscriberCount (làm tròn xuống 3 chữ số có nghĩa) | Không |
| `total_videos` | int64 | 0.00 | 322 | Tổng số video | video | statistics.videoCount | Không |
| `total_views` | int64 | 0.00 | 505600355 | Tổng lượt xem của kênh | lượt | statistics.viewCount | Không |
| `channel_info_ts` | str | 0.00 | 2026-11-03 08:54:10+00:00 | Thời điểm lấy thông tin kênh | UTC | Giờ thu | Không |
| `channel_age_days` | int64 | 0.00 | 4827 | Tuổi kênh lúc lấy thông tin | ngày | (channel_info_ts − channel_created) / 86400 | Không |
| `log_subs` | float64 | 0.00 | 5.928395852256714 | log10 số người đăng ký | log10(người) | log10(subscribers) | Không |
| `subs_tier` | str | 0.00 | 100K-1M (mid) | Nhóm quy mô kênh | nhãn | <10K / 10K–100K / 100K–1M / >1M | Không |

## dq_report.txt

Báo cáo chất lượng dữ liệu dạng văn bản do `clean_data.py` sinh ra (không có cột). Gồm 8 mục: đọc dữ liệu thô; sửa video_id hỏng; sửa tiêu đề mất dấu; gộp bảng lần đo (likes/comments > views, views = 0, views giảm); bảng kênh; Trending (ngày thiếu); bảng video master; tóm tắt chất lượng. Các số trong bảng độ tin cậy (Bảng 3.3) đối chiếu với file này.
