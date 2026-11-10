# holidays_sources.md - nguồn và mức kiểm chứng của holidays_vn.csv

Cột `type`: `nghi_le` (ngày nghỉ theo lịch chính thức), `nghi_bu` (nghỉ bù/hoán đổi ngày làm việc), `cuoi_tuan` (thứ Bảy/Chủ nhật nằm trong kỳ nghỉ liên tục). Mỗi `period_id` là một kỳ nghỉ liên tiếp. Mọi ngày trong kỳ (kể cả cuối tuần) đều được Q2d tính là "ngày lễ"; cần lọc `type` nếu muốn bỏ cuối tuần.

| period_id | Các ngày | Văn bản căn cứ (theo bài báo/trang đã mở) | Trang đã mở |
|---|---|---|---|
| 2024-TDL | 01/01/2024 | Điều 112 Bộ luật Lao động 2019 | Tuổi Trẻ 01/01/2024 |
| 2024-TET | 08/02–14/02/2024 (7 ngày) | Công văn 8662/VPCP-KGVX ngày 03/11/2023 (VPCP), đã đối chiếu ngày nghỉ với văn bản | luatvietnam.vn (văn bản 8662) |
| 2024-GT | 18/04/2024 | Điều 112 Bộ luật Lao động; bài không nêu nghỉ bù | Tuổi Trẻ 01/01/2024 |
| 2024-3004 | 27/04–01/05/2024 (hoán đổi 29/04, làm bù 04/05) | Thủ tướng đồng ý đề nghị của Bộ LĐ-TB&XH (bài không nêu số văn bản) | hatinh.gov.vn |
| 2024-QK | 31/08–03/09/2024 | Công văn 8662/VPCP-KGVX ngày 03/11/2023 (VPCP), đã đối chiếu | luatvietnam.vn (văn bản 8662) |
| 2025-TDL | 01/01/2025 | Điều 112 Bộ luật Lao động | lsvn.vn |
| 2025-TET | 25/01–02/02/2025 (9 ngày) | Thông báo 6150/TB-BLĐTBXH ngày 03/12/2024 (Bộ LĐ-TB&XH), đã đối chiếu; bài báo còn nêu Công văn 8726/VPCP-KGVX ngày 26/11/2024 (VPCP) | thuvienphapluat.vn (TB 6150) |
| 2025-GT | 05/04–07/04/2025 | Điều 112 Bộ luật Lao động; thông báo Bộ LĐ-TB&XH | lsvn.vn |
| 2025-3004 | 30/04–04/05/2025 (nghỉ 02/05, làm bù 26/04) | Thông báo 6150/TB-BLĐTBXH, đã đối chiếu | thuvienphapluat.vn (TB 6150) |
| 2025-QK | 30/08–02/09/2025 | Thông báo 6150/TB-BLĐTBXH, đã đối chiếu | thuvienphapluat.vn (TB 6150) |
| 2026-TDL | 01/01–04/01/2026 (nghỉ 02/01, làm bù 10/01) | Điều 112 Bộ luật Lao động | tuoitre.vn 02/01/2026 |
| 2026-TET | 14/02–22/02/2026 (9 ngày) | Công văn 9859/VPCP-KGVX ngày 13/10/2025 (VPCP), đã đối chiếu | thuvienphapluat.vn (trang đăng lại công văn 9859) |
| 2026-GT | 25/04–27/04/2026 (Giỗ Tổ rơi Chủ nhật 26/04, nghỉ bù 27/04) | Điều 111, 112 Bộ luật Lao động | tuoitre.vn 02/01/2026 |
| 2026-3004 | 30/04–03/05/2026 | theo báo | tuoitre.vn 02/01/2026 |
| 2026-QK | 29/08–02/09/2026 (hoán đổi 31/08, làm bù 22/08) | Công văn 9859/VPCP-KGVX ngày 13/10/2025 (VPCP), đã đối chiếu | thuvienphapluat.vn (trang đăng lại công văn 9859) |

Số ngày nghỉ mỗi năm trong file: 2024 = 18, 2025 = 22 (khớp "22 ngày" mà lsvn.vn nêu cho công chức), 2026 = 25.

## Còn lại cần Khôi làm (sau khi đã thay link văn bản cho Tết và Quốc khánh 2024-2026, 30/4-1/5 2025)
1. Các kỳ còn dùng bài báo hoặc Điều 112 Bộ luật Lao động làm căn cứ: 2024-TDL, 2024-GT, 2024-3004, 2025-TDL, 2025-GT, 2026-TDL, 2026-GT, 2026-3004. Nếu còn thời gian, tìm văn bản chính thức cho 2024-3004 và 2026-3004 (thông báo của Bộ Nội vụ hoặc Bộ LĐ-TB&XH).
2. Trang thuvienphapluat.vn về công văn 9859 là bản đăng lại; có thể ghi trong báo cáo "theo Công văn 9859/VPCP-KGVX" và mở file PDF gốc nếu có.
3. Tết dương lịch 2024 (01/01) và Giỗ Tổ 2024 (18/04): bài báo chỉ ghi nghỉ 1 ngày; chưa thấy nghỉ bù. Kiểm tra lại.
4. Phân loại `nghi_le` và `nghi_bu` trong kỳ Tết là phân loại theo lịch, không theo từng ngày pháp định; Q2d không dùng cột này.
