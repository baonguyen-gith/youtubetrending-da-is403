# -*- coding: utf-8 -*-
"""
gen_data_dictionary.py - Sinh data_dictionary.md (việc B10)

Phần "ý nghĩa / đơn vị / cách tính / vì sao rỗng" đã được viết tay và kiểm chứng với dữ liệu (xem DICT bên dưới);
script chỉ bổ sung các cột đo được từ file: kiểu dữ liệu, % rỗng, ví dụ. Khi chạy trên data_final_20261113,
tỷ lệ rỗng tự cập nhật. Cột nào có trong file mà chưa có trong DICT sẽ bị in cảnh báo (để không bỏ sót cột nào).
"""
import os
import sys
import pandas as pd

from prep import DATA_DIR

OUT = os.environ.get("OUT_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "data_dictionary.md"))

# (ý nghĩa, đơn vị, cách tính, vì sao có thể rỗng — "Không" nếu không bao giờ rỗng)
VM = {
 "video_id": ("Mã video YouTube (11 ký tự)", "chuỗi", "Do YouTube cấp; đọc dưới dạng chuỗi", "Không"),
 "channel_id": ("Mã kênh đăng video", "chuỗi", "Từ API", "Không"),
 "title": ("Tiêu đề video", "văn bản", "Từ API (một số tiêu đề gốc chứa ký tự ? thật)", "Không"),
 "published_ts": ("Thời điểm đăng video", "UTC", "snippet.publishedAt của API", "Không"),
 "category_id": ("Mã thể loại YouTube", "số nguyên", "snippet.categoryId", "Không"),
 "tags_count": ("Số thẻ tag người đăng gắn", "số", "Đếm phần tử của snippet.tags; 0 nếu không có tag", "Không (0 nếu không gắn tag)"),
 "duration_sec": ("Độ dài video", "giây", "Đổi từ contentDetails.duration (ISO 8601)", "Có: một số ít video không trả độ dài; video live/upcoming có thể bằng 0"),
 "last_obs_ts": ("Thời điểm của lần đo mới nhất của video", "UTC", "Lớn nhất của collected_ts trong measurements", "Không"),
 "views": ("Lượt xem ở lần đo mới nhất", "lượt", "statistics.viewCount (đã làm chuỗi không giảm bằng cummax)", "Không"),
 "likes": ("Lượt thích ở lần đo mới nhất", "lượt", "statistics.likeCount; likes > views bị đặt NaN", "Có: người đăng ẩn lượt thích (likes_hidden) hoặc nhiễu API"),
 "comments": ("Số bình luận ở lần đo mới nhất", "bình luận", "statistics.commentCount; comments > views bị đặt NaN", "Có: tắt bình luận (comments_disabled) hoặc nhiễu API"),
 "age_days_last": ("Tuổi video tại lần đo mới nhất", "ngày", "(last_obs_ts − published_ts) / 86400", "Không"),
 "n_obs": ("Số lần video được đo", "lần", "Đếm dòng của video trong measurements", "Không"),
 "is_live_or_upcoming": ("Video đang phát trực tiếp hoặc chưa phát", "TRUE/FALSE", "Từ liveBroadcastContent", "Không"),
 "first_obs_ts": ("Thời điểm lần đo đầu tiên", "UTC", "Nhỏ nhất của collected_ts", "Không"),
 "first_obs_age_days": ("Tuổi video tại lần đo đầu tiên", "ngày", "(first_obs_ts − published_ts) / 86400", "Không"),
 "in_history": ("Video có trong dữ liệu lịch sử kênh", "TRUE/FALSE", "TRUE nếu video xuất hiện trong playlistItems của kênh", "Không"),
 "trend_days": ("Số ngày video có mặt trong Trending", "ngày", "Số run_date khác nhau của video trong trending_clean", "Không (0 nếu chưa từng lọt)"),
 "trend_best_rank": ("Hạng Trending tốt nhất (số nhỏ = cao)", "hạng 1–200", "min(rank) trong trending_clean", "Có: rỗng nếu video chưa từng lọt Trending"),
 "trend_mean_rank": ("Hạng Trending trung bình", "hạng", "mean(rank)", "Có: như trend_best_rank"),
 "trend_first_ts": ("Thời điểm lần đầu video xuất hiện trong Trending", "UTC", "min(run_ts) của video trong trending_clean", "Có: như trend_best_rank"),
 "trend_age_first_days": ("Tuổi video lúc lần đầu vào Trending", "ngày", "(trend_first_ts − published_ts) / 86400", "Có: như trend_best_rank"),
 "ever_trending": ("Video từng lọt Trending trong giai đoạn thu thập", "TRUE/FALSE", "trend_days > 0", "Không"),
 "pub_date_vn": ("Ngày đăng theo giờ Việt Nam", "YYYY-MM-DD", "Đổi published_ts sang UTC+7 rồi lấy ngày", "Không"),
 "pub_hour": ("Giờ đăng theo giờ Việt Nam", "0–23", "Giờ của published_ts ở UTC+7", "Không"),
 "pub_dow": ("Thứ đăng", "0–6 (0 = Thứ Hai)", "dayofweek của pub_date_vn", "Không"),
 "pub_is_weekend": ("Đăng vào cuối tuần", "TRUE/FALSE", "pub_dow ∈ {5, 6}", "Không"),
 "pub_month": ("Tháng đăng (1–12, không kèm năm)", "1–12", "Tháng của pub_date_vn", "Không"),
 "pub_slot": ("Khung giờ đăng (5 nhóm)", "nhãn", "Khuya 0–5h; Sáng 6–11h; Chiều 12–17h; Tối 18–21h; Đêm 22–23h", "Không"),
 "title_len": ("Độ dài tiêu đề", "ký tự", "len(title)", "Không"),
 "title_words": ("Số từ trong tiêu đề", "từ", "Tách theo khoảng trắng", "Không"),
 "title_upper_ratio": ("Tỷ lệ chữ HOA trong các chữ cái của tiêu đề", "0–1", "Số chữ cái viết hoa / tổng số chữ cái (isalpha); ngoại lệ hiếm >1 với ký tự chữ trong vòng tròn như Ⓗ", "Không"),
 "title_has_question": ("Tiêu đề có dấu hỏi", "TRUE/FALSE", "Chứa ký tự ?", "Không"),
 "title_has_exclaim": ("Tiêu đề có dấu chấm than", "TRUE/FALSE", "Chứa ký tự !", "Không"),
 "title_has_digit": ("Tiêu đề có chữ số", "TRUE/FALSE", "Chứa ký tự 0–9", "Không"),
 "title_has_emoji": ("Tiêu đề có emoji", "TRUE/FALSE", "Chứa ký tự emoji Unicode (quy tắc regex của clean_data.py)", "Không"),
 "title_n_hashtag": ("Số hashtag trong tiêu đề", "số", "Đếm ký tự #", "Không"),
 "title_has_bracket": ("Tiêu đề có ngoặc", "TRUE/FALSE", "Chứa ( ) hoặc [ ] (khớp ~99,5% với quy tắc này)", "Không"),
 "title_has_pipe": ("Tiêu đề có ký tự sổ đứng (pipe)", "TRUE/FALSE", "Chứa ký tự sổ đứng (pipe)", "Không"),
 "is_short_60": ("Video ngắn từ 60 giây trở xuống", "TRUE/FALSE", "0 < duration_sec ≤ 60 (duration rỗng hoặc 0 → FALSE)", "Không"),
 "is_short_180": ("Video ngắn từ 180 giây trở xuống", "TRUE/FALSE", "0 < duration_sec ≤ 180", "Không"),
 "category_name": ("Tên thể loại", "nhãn", "Tra category_id theo bảng thể loại YouTube", "Không"),
 "like_rate": ("Tỷ lệ thích trên lượt xem", "tỷ lệ 0–1", "likes / views", "Có: khi likes rỗng"),
 "comment_rate": ("Tỷ lệ bình luận trên lượt xem", "tỷ lệ", "comments / views", "Có: khi comments rỗng"),
 "log_views": ("Logarit cơ số 10 của lượt xem", "log10(lượt)", "log10(views); views = 0 không có giá trị hợp lệ", "Có thể: khi views = 0"),
 "views_per_day": ("Lượt xem trung bình mỗi ngày", "lượt/ngày", "views / max(age_days_last, 1)", "Không"),
 "likes_hidden": ("Người đăng ẩn lượt thích", "TRUE/FALSE", "Cờ từ API / likes rỗng", "Không"),
 "comments_disabled": ("Video tắt bình luận", "TRUE/FALSE", "Cờ từ API / comments rỗng", "Không"),
 "channel_name": ("Tên kênh", "văn bản", "Từ channels_latest", "Không"),
 "subscribers": ("Số người đăng ký của kênh TẠI LÚC THU THẬP", "người", "statistics.subscriberCount; API làm tròn XUỐNG 3 chữ số có nghĩa", "Không"),
 "log_subs": ("Logarit cơ số 10 của số người đăng ký", "log10(người)", "log10(subscribers)", "Không"),
 "subs_tier": ("Nhóm quy mô kênh", "nhãn", "<10K (nano); 10K–100K (micro); 100K–1M (mid); >1M (macro)", "Không"),
 "total_videos": ("Tổng số video của kênh lúc thu thập", "video", "statistics.videoCount", "Không"),
 "total_views": ("Tổng lượt xem của kênh lúc thu thập", "lượt", "statistics.viewCount của kênh", "Không"),
 "channel_age_days": ("Tuổi kênh lúc thu thập", "ngày", "(channel_info_ts − channel_created) / 86400", "Không"),
}

MEAS = {
 "video_id": ("Mã video", "chuỗi", "Từ API", "Không"),
 "channel_id": ("Mã kênh", "chuỗi", "Từ API", "Không"),
 "title": ("Tiêu đề tại thời điểm đo", "văn bản", "Từ API", "Không"),
 "channel_title": ("Tên kênh tại thời điểm đo", "văn bản", "Từ API", "Không"),
 "published_ts": ("Thời điểm đăng", "UTC", "snippet.publishedAt", "Không"),
 "category_id": ("Mã thể loại", "số nguyên", "snippet.categoryId", "Không"),
 "tags_count": ("Số thẻ tag", "số", "Đếm snippet.tags", "Không"),
 "duration_sec": ("Độ dài video", "giây", "Đổi từ ISO 8601", "Có: như videos_master"),
 "collected_ts": ("Thời điểm thu số liệu của video này", "UTC", "Giờ máy thu khi gọi API", "Không"),
 "run_ts": ("Thời điểm bắt đầu lượt chạy của script", "UTC", "Gán một lần cho mỗi lượt chạy", "Không"),
 "run_date": ("Ngày của lượt chạy", "YYYY-MM-DD", "Ngày của lượt chạy theo máy thu", "Không"),
 "views": ("Lượt xem sau khi làm chuỗi không giảm", "lượt", "cummax(views_raw) theo từng video", "Không"),
 "likes": ("Lượt thích", "lượt", "statistics.likeCount; likes > views đặt NaN", "Có: ẩn lượt thích hoặc nhiễu API"),
 "comments": ("Bình luận", "bình luận", "statistics.commentCount; comments > views đặt NaN", "Có: tắt bình luận hoặc nhiễu API"),
 "rank": ("Hạng trong danh sách Trending ở lần chụp", "hạng 1–200", "Thứ tự trong videos.list mostPopular", "Có: chỉ có khi source = trending"),
 "source": ("Nguồn dòng đo", "nhãn", "trending / tracking / history", "Không"),
 "is_live_or_upcoming": ("Video live hoặc chưa phát", "TRUE/FALSE", "liveBroadcastContent", "Không"),
 "likes_hidden": ("Ẩn lượt thích", "TRUE/FALSE", "Cờ từ API", "Không"),
 "comments_disabled": ("Tắt bình luận", "TRUE/FALSE", "Cờ từ API", "Không"),
 "views_raw": ("Lượt xem thô từ API trước cummax", "lượt", "statistics.viewCount nguyên bản", "Không"),
 "age_days": ("Tuổi video tại thời điểm đo", "ngày", "(collected_ts − published_ts) / 86400", "Không"),
 "n_obs": ("Thứ tự lần đo của video (đếm tích lũy)", "lần", "Số lần đo của video tính đến dòng này", "Không"),
 "is_last_of_day": ("Lần đo cuối cùng của video trong ngày", "TRUE/FALSE", "Dòng có collected_ts lớn nhất trong cùng (video_id, run_date)", "Không"),
}

TREND = {
 "run_ts": ("Thời điểm chụp Trending", "UTC", "Giờ bắt đầu lượt chụp", "Không"),
 "run_date": ("Ngày chụp", "YYYY-MM-DD", "Phần ngày của run_ts", "Không"),
 "rank": ("Hạng trong Trending", "hạng 1–200", "Thứ tự API trả về", "Không"),
 "video_id": ("Mã video (đã khôi phục các mã bị hỏng #NAME?)", "chuỗi", "Khôi phục qua (channel_id, published_at)", "Không"),
 "title": ("Tiêu đề", "văn bản", "Đã sửa dấu từ bảng đối chiếu", "Không"),
 "channel_id": ("Mã kênh", "chuỗi", "Từ API", "Không"),
 "channel_title": ("Tên kênh", "văn bản", "Đã sửa dấu", "Không"),
 "published_ts": ("Thời điểm đăng", "UTC", "snippet.publishedAt", "Không"),
 "category_id": ("Mã thể loại", "số nguyên", "snippet.categoryId", "Không"),
 "tags_count": ("Số thẻ tag", "số", "Đếm snippet.tags", "Không"),
 "duration_sec": ("Độ dài", "giây", "Đổi từ ISO 8601", "Không"),
 "views": ("Lượt xem lúc chụp", "lượt", "statistics.viewCount", "Không"),
 "likes": ("Lượt thích lúc chụp", "lượt", "statistics.likeCount", "Có: ẩn lượt thích"),
 "comments": ("Bình luận lúc chụp", "bình luận", "statistics.commentCount", "Có: tắt bình luận"),
 "age_days": ("Tuổi video lúc chụp", "ngày", "(run_ts − published_ts) / 86400", "Không"),
}

CH = {
 "channel_id": ("Mã kênh", "chuỗi", "Từ API", "Không"),
 "channel_name": ("Tên kênh", "văn bản", "snippet.title của kênh", "Không"),
 "channel_created": ("Thời điểm tạo kênh", "UTC", "snippet.publishedAt của kênh", "Không"),
 "subscribers": ("Số người đăng ký lần đo mới nhất", "người", "statistics.subscriberCount (làm tròn xuống 3 chữ số có nghĩa)", "Không"),
 "total_videos": ("Tổng số video", "video", "statistics.videoCount", "Không"),
 "total_views": ("Tổng lượt xem của kênh", "lượt", "statistics.viewCount", "Không"),
 "channel_info_ts": ("Thời điểm lấy thông tin kênh", "UTC", "Giờ thu", "Không"),
 "channel_age_days": ("Tuổi kênh lúc lấy thông tin", "ngày", "(channel_info_ts − channel_created) / 86400", "Không"),
 "log_subs": ("log10 số người đăng ký", "log10(người)", "log10(subscribers)", "Không"),
 "subs_tier": ("Nhóm quy mô kênh", "nhãn", "<10K / 10K–100K / 100K–1M / >1M", "Không"),
}

FILES = [
 ("videos_master.csv", "Mỗi dòng MỘT VIDEO, số liệu của lần đo mới nhất (55 cột). Dùng cho Q1, Q2, Q3, Q5.", VM),
 ("measurements.csv", "Mỗi dòng MỘT LẦN ĐO của một video (chuỗi theo thời gian). Dùng cho Q4 (S1, S2) và Q6; luôn lọc is_last_of_day = TRUE khi dựng chuỗi theo ngày.", MEAS),
 ("trending_clean.csv", "Mỗi dòng MỘT VIDEO trong MỘT LẦN CHỤP danh sách Trending (hạng 1–200).", TREND),
 ("channels_latest.csv", "Mỗi dòng MỘT KÊNH, số liệu kênh mới nhất.", CH),
]


def main():
    lines = ["# Từ điển dữ liệu (data_dictionary.md)", "",
             f"Sinh bởi `gen_data_dictionary.py` từ thư mục `{os.path.basename(os.path.normpath(DATA_DIR))}`. "
             "Cột *% rỗng* và *ví dụ* đo trực tiếp từ file; các cột mô tả được viết tay và kiểm chứng với dữ liệu.", "",
             "Quy ước chung: thời điểm lưu ở UTC (ký hiệu +00:00); các cột `pub_*` đã đổi sang giờ Việt Nam (UTC+7); "
             "`pub_dow = 0` là Thứ Hai; file CSV mã hóa `utf-8-sig`; `video_id` luôn đọc là chuỗi.", ""]
    problems = []
    for fname, desc, d in FILES:
        df = pd.read_csv(os.path.join(DATA_DIR, fname), dtype={"video_id": str, "channel_id": str},
                         encoding="utf-8-sig", low_memory=False)
        lines += [f"## {fname}", "", f"{desc} Số dòng: **{len(df):,}**; số cột: **{df.shape[1]}**.", "",
                  "| Cột | Kiểu | % rỗng | Ví dụ | Ý nghĩa | Đơn vị | Cách tính | Có thể rỗng? Vì sao |",
                  "| --- | --- | ---: | --- | --- | --- | --- | --- |"]
        for c in df.columns:
            if c not in d:
                problems.append(f"{fname}: cột '{c}' chưa có mô tả")
                continue
            ex = df[c].dropna().iloc[0] if df[c].notna().any() else ""
            ex = str(ex).replace("|", "/").replace("\n", " ")[:38]
            mean, unit, how, empty = d[c]
            lines.append(f"| `{c}` | {df[c].dtype} | {100 * df[c].isna().mean():.2f} | {ex} | {mean} | {unit} | {how} | {empty} |")
        extra = [c for c in d if c not in df.columns]
        if extra:
            problems.append(f"{fname}: mô tả thừa cho cột không còn trong file: {extra}")
        lines.append("")
    lines += ["## dq_report.txt", "",
              "Báo cáo chất lượng dữ liệu dạng văn bản do `clean_data.py` sinh ra (không có cột). Gồm 8 mục: đọc dữ liệu thô; "
              "sửa video_id hỏng; sửa tiêu đề mất dấu; gộp bảng lần đo (likes/comments > views, views = 0, views giảm); bảng kênh; "
              "Trending (ngày thiếu); bảng video master; tóm tắt chất lượng. Các số trong bảng độ tin cậy (Bảng 3.3) đối chiếu với file này.", ""]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write("\n".join(lines))
    print("Đã ghi", os.path.abspath(OUT))
    if problems:
        print("CẢNH BÁO:\n  " + "\n  ".join(problems)); sys.exit(1)
    print("Không cột nào thiếu mô tả.")


if __name__ == "__main__":
    main()
