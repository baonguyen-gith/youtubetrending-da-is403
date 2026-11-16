# figure_notes.md – ghi chú hình của Q1 (số lấy từ data_final_20261113, 22/10–12/11/2026)

| Hình | File | Cách đọc | Lưu ý khi dùng |
| --- | --- | --- | --- |
| 5.1 | q1_by_hour.png | Đường xanh: trung vị lv_adj theo giờ đăng; đường đứt đỏ: sau khi trừ trung vị của chính kênh; cột: số video | Đường xanh dao động mạnh (khoảng cách ≈ 0,890 log10) nhưng đường đỏ co lại còn ≈ 0,209: chênh lệch theo giờ phần lớn là do cơ cấu kênh. Không viết "đăng giờ X được nhiều view hơn". |
| 5.2 | q1_heatmap.png | Màu đỏ: trung vị lv_adj cao hơn mức trung bình của nhóm tuổi; xanh: thấp hơn; ô trắng: n < 30 | Dải màu chạy theo hàng (giờ) chứ không theo cột (thứ). Ô 4h Thứ Tư có n = 100 nên không diễn giải riêng. |
| 5.3 | q1_box_category.png | Hộp: Q1–Q3 của lv_adj; vạch đen: trung vị; ẩn điểm ngoại lai | Thể loại gắn chặt với kênh: khoảng cách thô giữa 10 thể loại đông nhất là ≈ 1,752 log10 nhưng chỉ còn ≈ 0,018 sau khi trừ trung vị kênh, và thứ hạng đảo lại. Đây là chênh lệch tương quan, không phải tác động của thể loại. |
| (phụ) | q1_by_dow.png, q1_by_month.png | Theo thứ và theo năm-tháng | Theo tháng: số video mỗi tháng bị chi phối bởi giới hạn 500 video/kênh, không dùng để nói về xu hướng. |

Quy ước thống kê: độ lệch chuẩn mẫu (n−1); độ lệch g1 và độ nhọn dư g2 tính theo mô-men (scipy `skew/kurtosis` với `bias=True`; R: công thức trong `q1_descriptive.R`).
