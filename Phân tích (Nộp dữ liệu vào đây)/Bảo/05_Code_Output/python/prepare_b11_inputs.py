# -*- coding: utf-8 -*-
"""prepare_b11_inputs.py - Gom CSV của các thành viên khác cho dashboard B11.

Việc B11 chỉ đọc CSV trong 05_Code_Output/outputs/. Script này tìm đầu ra của
Kiên (q2b), Khôi (q4) và Quỳnh (q5, q6) trong thư mục làm việc của từng người,
chuẩn hóa tên cột theo mục 0.5 rồi chép vào outputs/powerbi/.

File nào chưa có thì bỏ qua và in cảnh báo - không chờ, đúng quy ước B11.

Cách dùng (chạy từ Bao/):
    python python/prepare_b11_inputs.py
"""
from pathlib import Path
import shutil

import pandas as pd

BASE = Path(__file__).resolve().parents[1]          # .../Bảo/Bao
GROUP = BASE.parent.parent                          # .../Phân tích (Nộp dữ liệu vào đây)
OUT = BASE / "outputs" / "powerbi"
OUT.mkdir(parents=True, exist_ok=True)

# (tên file đích, [các vị trí có thể có], ghi chú nguồn)
Q2B = ("q2b_group_means.csv", [
    GROUP / "Kiên" / "05_Code_Output" / "outputs" / "q2b" / "q2b_group_means.csv",
    GROUP / "Kiên" / "05_Code_Output" / "outputs_temp" / "q2b" / "q2b_group_means.csv",
], "Kiên - Q2b ANOVA nhóm trung bình")

Q4 = [
    ("q4_forecast_S1.csv", [
        GROUP / "Khôi" / "05_Code_Output" / "outputs" / "q4" / "q4_forecast_S1.csv",
        GROUP / "Khôi" / "outputs" / "q4" / "q4_forecast_S1.csv",
    ], "Khôi - Q4 dự báo S1"),
    ("q4_forecast_S2.csv", [
        GROUP / "Khôi" / "05_Code_Output" / "outputs" / "q4" / "q4_forecast_S2.csv",
        GROUP / "Khôi" / "outputs" / "q4" / "q4_forecast_S2.csv",
    ], "Khôi - Q4 dự báo S2"),
    ("q4_model_comparison.csv", [
        GROUP / "Khôi" / "05_Code_Output" / "outputs" / "q4" / "q4_model_comparison.csv",
        GROUP / "Khôi" / "outputs" / "q4" / "q4_model_comparison.csv",
    ], "Khôi - Q4 so sánh mô hình"),
]

Q5Q6 = [
    ("q5_model_comparison.csv", "q5", "Quỳnh - Q5 so sánh mô hình"),
    ("q5_importance.csv", "q5", "Quỳnh - Q5 độ quan trọng biến"),
    ("q6_cluster_profile.csv", "q6", "Quỳnh - Q6 hồ sơ cụm"),
    ("q6_pca_points.csv", "q6", "Quỳnh - Q6 điểm PCA"),
]

notes = []


def find(paths):
    for p in paths:
        if p.is_file():
            return p
    return None


def copy_plain(dst_name, paths, note):
    src = find(paths)
    if src is None:
        print(f"BỎ QUA {dst_name}: chưa có file nguồn")
        return
    shutil.copy2(src, OUT / dst_name)
    notes.append((dst_name, src, note))
    print(f"OK     {dst_name} <- {src}")


# Q2b: giữ nguyên cột theo mục 0.5
copy_plain(*Q2B)

# Q4: đổi set -> split, pred -> forecast theo đúng hợp đồng 0.5
for dst_name, paths, note in Q4:
    src = find(paths)
    if src is None:
        print(f"BỎ QUA {dst_name}: chưa có file nguồn")
        continue
    df = pd.read_csv(src, encoding="utf-8-sig")
    if {"date", "set", "actual", "pred", "lo95", "hi95"}.issubset(df.columns):
        df = df.rename(columns={"set": "split", "pred": "forecast"})
        df = df[["date", "actual", "forecast", "lo95", "hi95", "split"]]
        df.to_csv(OUT / dst_name, index=False, encoding="utf-8-sig")
    else:
        shutil.copy2(src, OUT / dst_name)
    notes.append((dst_name, src, note))
    print(f"OK     {dst_name} <- {src}")

# Q5/Q6: nếu Quỳnh đã có thì chép nguyên
for name, folder, note in Q5Q6:
    copy_plain(name, [
        GROUP / "Quỳnh" / "05_Code_Output" / "outputs" / folder / name,
        GROUP / "Quỳnh" / "outputs" / folder / name,
    ], note)

# Ghi nguồn để không nhầm file của ai
if notes:
    lines = ["# Nguồn CSV trong outputs/powerbi/", "",
             "Các file dưới đây do thành viên khác xuất; script `prepare_b11_inputs.py`",
             "chỉ chép và chuẩn hóa tên cột cho dashboard B11.", "",
             "| File đích | File nguồn | Ghi chú |", "| --- | --- | --- |"]
    for dst, src, note in notes:
        try:
            rel = src.relative_to(GROUP)
        except ValueError:
            rel = src
        lines.append(f"| `{dst}` | `{rel}` | {note} |")
    (OUT / "README_nguon_CSV.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Đã ghi", OUT / "README_nguon_CSV.md")
