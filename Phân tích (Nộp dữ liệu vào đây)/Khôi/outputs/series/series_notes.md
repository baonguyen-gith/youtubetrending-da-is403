# series_notes.md (DATA_DIR = data_clean_temp)

- Ngày thu cuối (giờ VN): 03/11/2026. S1 chạy 01/01/2024 đến 02/11/2026 (1037 ngày, không thiếu ngày nào).
- S2 dùng video thuộc H, bỏ video đăng trong 7 ngày cuối, kết thúc 27/10/2026; ngày không có video H: 0 ngày (NaN).
- Số kênh đủ lịch sử (dưới 500 video in_history): 213 / 328 kênh; số video in_history của các kênh này: 34,728; trong H: 34,498.
- N1: ngày NaN = 22/10, 25/10, 26/10, 30/10, 31/10, 01/11, 02/11, 03/11 (ngày đầu 22/10, ngày thiếu chụp và ngày ngay sau ngày thiếu). Số điểm hợp lệ N1: 5.
- N2: ngày NaN = 25/10, 30/10, 01/11, 02/11; số điểm hợp lệ: 9. Giờ chụp không cố định 20:00 (xem cột snapshot_time_vn), nên N2 chịu nhiễu theo giờ chụp.
- Ngày thiếu chụp Trending: 25/10, 30/10, 01/11, 02/11.
- Cách diễn giải cần Khôi xác nhận: (a) "ngày thu cuối trừ ngày cuối" hiểu là bỏ đúng ngày thu cuối; (b) n_videos = số video H dùng tính S2 mỗi ngày; n_channels = số kênh đủ lịch sử (hằng số).
