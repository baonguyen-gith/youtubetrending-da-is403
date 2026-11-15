# 5.2c Q2c: Chi-square giữa thể loại và khả năng lọt Trending

## Phương pháp (tóm tắt)

Chỉ dùng video thuộc cửa sổ `in_window_C` (không ngắn) cho `viral_C`; lập bảng chéo `category_name × viral_C`, gộp các thể loại có tần số kỳ vọng dưới 5 vào nhóm **Khác**, báo χ², bậc tự do, p, Cramér's V và phần dư chuẩn hóa. Làm thêm `category_name × viral_A` trên toàn bộ H, kèm bản bỏ video ngắn và bản bỏ thể loại quá ít video. Python dùng `scipy.stats.chi2_contingency(correction=False)`; R dùng `chisq.test(correct=FALSE)`.

## Cỡ mẫu

- `viral_C`: **10.925** video trong cửa sổ, **550** video dương (5,03%).
- `viral_A`: **139.227** video trong H, **13.931** video dương (10,01%).
- Bản bỏ video ngắn: **110.585** video.

## Bảng 5.4. Kết quả Chi-square

| Cặp biến | χ² | df | p | V | Thể loại vượt kỳ vọng nhiều nhất |
|---|---:|---:|---:|---:|---|
| Thể loại × viral_C | 542,701 | 9 | 4,085e-111 | 0,223 | Gaming (phần dư +17,42) |
| Thể loại × viral_A | 4.485,278 | 14 | < 1e-300 | 0,179 | Gaming (phần dư +44,91) |

### Kiểm tra độ vững

| Cấu hình | n | χ² | df | p | V | Thể loại vượt kỳ vọng |
|---|---:|---:|---:|---:|---:|---|
| viral_A – bỏ video ngắn | 110.585 | 2.965,115 | 14 | < 1e-300 | 0,164 | Gaming |
| viral_A – bỏ Nonprofits & Activism | 139.223 | 4.484,451 | 13 | < 1e-300 | 0,179 | Gaming |

## Bảng hồ sơ theo thể loại (viral_C)

| Thể loại | n | Trending | Tỷ lệ | Kỳ vọng | Phần dư |
|---|---:|---:|---:|---:|---:|
| News & Politics | 2.488 | 0 | 0,00% | 125,25 | -11,19 |
| Gaming | 2.485 | 320 | 12,88% | 125,10 | +17,42 |
| People & Blogs | 2.144 | 80 | 3,73% | 107,94 | -2,69 |
| Music | 1.874 | 125 | 6,67% | 94,34 | +3,16 |
| Sports | 562 | 0 | 0,00% | 28,29 | -5,32 |
| Entertainment | 444 | 22 | 4,95% | 22,35 | -0,07 |
| Film & Animation | 434 | 2 | 0,46% | 21,85 | -4,25 |
| Khác | 189 | 1 | 0,53% | 9,51 | -2,76 |
| Education | 173 | 0 | 0,00% | 8,71 | -2,95 |
| Science & Tech | 132 | 0 | 0,00% | 6,65 | -2,58 |
| **Tổng** | 10.925 | 550 | 5,03% | 550,00 | -11,23 |

## Hình 5.5

`q2c_residuals.png` – Phần dư chuẩn hóa của bảng chéo thể loại × viral_C (nguồn: `outputs/5.2c q2c/`).

## Giải thích thực tiễn (draft)

Kết quả cho thấy thể loại có liên quan đến khả năng lọt Trending (χ² = 542,7; df = 9; p 4,085e-111; V = 0,223). Tuy nhiên, vì n rất lớn, p-value gần như luôn rất nhỏ; độ lớn của liên hệ nên đọc qua Cramér's V và phần dư chuẩn hóa (Cohen, 1988; Lin và cộng sự, 2013). Với V khoảng 0,22, mức liên hệ là nhỏ đến trung bình theo quy ước của Cohen, nhưng phần dư cho thấy khác biệt thực tiễn rõ ở một số thể loại: **Gaming** và **Music** lọt Trending nhiều hơn kỳ vọng, trong khi **News & Politics**, **Sports**, **Film & Animation** và nhóm **Khác** lọt ít hơn kỳ vọng. Kết quả này phù hợp với các nghiên cứu trước cho rằng thể loại nội dung và cách phân phối nội dung có liên quan đến mức độ phổ biến của video YouTube (Cha và cộng sự, 2007; Cheng và cộng sự, 2008; Borghol và cộng sự, 2012; Figueiredo và cộng sự, 2014).

Với `viral_A`, kết quả định hướng tương tự: **Gaming** và **Music** có tỷ lệ video thuộc nhóm 10% lượt xem cao nhất trong nhóm tuổi cao hơn kỳ vọng, còn **News & Politics**, **Education**, **Sports**, **People & Blogs** và **Autos & Vehicles** thấp hơn kỳ vọng. Cần lưu ý `viral_A` đo lượt xem tương đối trong nhóm tuổi, không đo trực tiếp việc lọt Trending, nên hai nhãn không thay thế nhau.

## Khuyến nghị (draft)

- Nhà sáng tạo trong **Gaming/Music** có thể ưu tiên tần suất và thời điểm đăng để tận dụng lợi thế thể loại; đây là tương quan, không phải quan hệ nhân quả.
- Nhà sáng tạo trong **News & Politics/Sports/Education** nên kiểm tra lại định dạng, độ dài và cách đặt tiêu đề vì tỷ lệ lọt Trending thấp hơn kỳ vọng dù lượng video lớn.
- Nhãn hàng nên chọn thể loại theo mục tiêu chiến dịch: Gaming/Music cho phủ rộng và khả năng lên Trending; News/Sports cho tiếp cận đúng đối tượng hơn là kỳ vọng lên Trending.

## Hạn chế (draft)

- `viral_C` chỉ xét video đăng trong cửa sổ ngắn 19/10–26/10/2026, nên số dương ít (550) và một số thể loại bị gộp vào **Khác**.
- Bảng `viral_A` còn 1 video **Nonprofits & Activism** tạo ô kỳ vọng 0,10 (< 5); bản bỏ thể loại này cho kết quả gần như không đổi (χ² = 4.484,5; V = 0,179).
- Đây là dữ liệu quan sát, không phải thử nghiệm; kết quả chỉ mô tả mối liên hệ.
- Số liệu hiện tại là bản `data_clean` 03/11 (96.334 video, 466 kênh, 636 video Trending); phải chạy lại trên `data_final_20261113` trước hạn 15/11 23:59.
