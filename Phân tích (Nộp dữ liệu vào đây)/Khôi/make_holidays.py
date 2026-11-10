"""make_holidays.py - sinh holidays_vn.csv (date,name,type,tet,period_id,source_url).
Mỗi dòng = 1 ngày nằm trong kỳ nghỉ liên tục chính thức. type: nghi_le | nghi_bu | cuoi_tuan.
Thứ bảy/chủ nhật trong kỳ được gán 'cuoi_tuan' tự động theo lịch; ngày nghỉ bù/hoán đổi liệt kê tay (bu=...)."""
import pandas as pd
T24 = "https://tuoitre.vn/sau-tet-duong-lich-con-nhung-ngay-nghi-le-nao-trong-nam-2024-20240101082813046.htm"
NA = "https://hcc.nghean.gov.vn/chi-dao-dieu-hanh/lich-nghi-tet-nguyen-dan-giap-thin-va-nghi-le-quoc-khanh-nam-2024-636.html"
HT = "https://hatinh.gov.vn/vi/bai-viet/lich-nghi-le-dip-gio-to-hung-vuong-va-304-15-nam-2024"
L25 = "https://lsvn.vn/nam-2025-cong-chuc-nguoi-lao-dong-duoc-nghi-22-ngay-dip-le-tet-a152250.html"
D25 = "https://daibieunhandan.vn/print/10353630.html"
C8662 = "https://luatvietnam.vn/lao-dong/cong-van-8662-vpcp-kgvx-2023-ve-nghi-tet-am-lich-va-nghi-le-quoc-khanh-nam-2024-274255-d6.html"  # Công văn 8662/VPCP-KGVX, 03/11/2023 (VPCP): Tết 2024 và Quốc khánh 2024
TB6150 = "https://thuvienphapluat.vn/van-ban/Lao-dong-Tien-luong/Thong-bao-6150-TB-BLDTBXH-2024-nghi-tet-Am-lich-nghi-le-Quoc-khanh-doi-voi-can-bo-cong-chuc-633960.aspx"  # Thông báo 6150/TB-BLĐTBXH, 03/12/2024 (Bộ LĐ-TB&XH): Tết, 30/4-1/5, Quốc khánh 2025
C9859 = "https://thuvienphapluat.vn/phap-luat-nha-dat/da-co-cong-van-tra-loi-chinh-thuc-lich-nghi-tet-am-lich-binh-ngo-2026-9676.html"  # Công văn 9859/VPCP-KGVX, 13/10/2025 (VPCP), trang đăng lại: Tết và Quốc khánh 2026
T26 = "https://tuoitre.vn/chi-tiet-so-ngay-nghi-trong-cac-dip-le-nam-2026-20251231230420433.htm"
# (period_id, name, tet, start, end, bu_days, url)
P = [
 ("2024-TDL", "Tết Dương lịch 2024", 0, "2024-01-01", "2024-01-01", [], T24),
 ("2024-TET", "Tết Nguyên đán Giáp Thìn 2024", 1, "2024-02-08", "2024-02-14", [], C8662),
 ("2024-GT",  "Giỗ Tổ Hùng Vương 2024", 0, "2024-04-18", "2024-04-18", [], T24),
 ("2024-3004","Giải phóng miền Nam 30/4 và Quốc tế Lao động 1/5 2024", 0, "2024-04-27", "2024-05-01", ["2024-04-29"], HT),
 ("2024-QK",  "Quốc khánh 2/9/2024", 0, "2024-08-31", "2024-09-03", [], C8662),
 ("2025-TDL", "Tết Dương lịch 2025", 0, "2025-01-01", "2025-01-01", [], L25),
 ("2025-TET", "Tết Nguyên đán Ất Tỵ 2025", 1, "2025-01-25", "2025-02-02", [], TB6150),
 ("2025-GT",  "Giỗ Tổ Hùng Vương 2025", 0, "2025-04-05", "2025-04-07", [], L25),
 ("2025-3004","30/4 và 1/5 2025", 0, "2025-04-30", "2025-05-04", ["2025-05-02"], TB6150),
 ("2025-QK",  "Quốc khánh 2/9/2025", 0, "2025-08-30", "2025-09-02", [], TB6150),
 ("2026-TDL", "Tết Dương lịch 2026", 0, "2026-01-01", "2026-01-04", ["2026-01-02"], T26),
 ("2026-TET", "Tết Nguyên đán Bính Ngọ 2026", 1, "2026-02-14", "2026-02-22", [], C9859),
 ("2026-GT",  "Giỗ Tổ Hùng Vương 2026", 0, "2026-04-25", "2026-04-27", ["2026-04-27"], T26),
 ("2026-3004","30/4 và 1/5 2026", 0, "2026-04-30", "2026-05-03", [], T26),
 ("2026-QK",  "Quốc khánh 2/9/2026", 0, "2026-08-29", "2026-09-02", ["2026-08-31"], C9859),
]
rows = []
for pid, name, tet, s, e, bu, url in P:
    for d in pd.date_range(s, e):
        ds = d.strftime("%Y-%m-%d")
        typ = "nghi_bu" if ds in bu else ("cuoi_tuan" if d.dayofweek >= 5 and not (pid == "2026-GT" and ds == "2026-04-26") else "nghi_le")
        rows.append((ds, name, typ, tet, pid, url))
h = pd.DataFrame(rows, columns=["date", "name", "type", "tet", "period_id", "source_url"])
h.to_csv("holidays_vn.csv", index=False, encoding="utf-8-sig")
print(h.groupby("period_id").agg(ngay=("date", "size"), tu=("date", "min"), den=("date", "max")).to_string())
print(h.groupby(h.date.str[:4]).size().to_dict())
