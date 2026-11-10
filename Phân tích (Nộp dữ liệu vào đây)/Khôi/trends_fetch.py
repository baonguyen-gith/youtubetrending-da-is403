"""trends_fetch.py - K5: tải Google Trends (geo VN, theo tuần) cho các từ khóa trong trends_keywords.csv.
Chạy từng từ khóa, nghỉ 5-10 giây, lưu CSV gốc ngay. Nếu lỗi 429: tải tay từ trends.google.com (Explore > Download).
LƯU Ý: chưa được kiểm chạy trong môi trường của trợ lý (không có mạng tới Google) - Khôi chạy trên máy cá nhân.
Dùng: python trends_fetch.py [ngày_kết_thúc YYYY-MM-DD]
"""
import sys, time, random, datetime as dt
import pandas as pd
from pytrends.request import TrendReq

end = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().isoformat()
kws = pd.read_csv("trends_keywords.csv", encoding="utf-8-sig")["keyword"].tolist()
pt = TrendReq(hl="vi-VN", tz=-420)
frames = []
for kw in kws:
    pt.build_payload([kw], geo="VN", timeframe=f"2024-01-01 {end}")
    df = pt.interest_over_time().reset_index()[["date", kw]].rename(columns={kw: "interest"})
    df["keyword"] = kw; df.to_csv(f"trends_raw_{kw.replace(' ', '_')}.csv", index=False)
    frames.append(df); print(kw, len(df), "tuần"); time.sleep(random.uniform(5, 10))
pd.concat(frames).to_csv("trends_raw.csv", index=False)
