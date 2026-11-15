# 05_Code_Output — Phần của Vũ Thị Như Quỳnh (24521515)

Code và kết quả phần cá nhân trong đồ án IS403:
nhãn viral (Mục 4.4), Q2c Chi-square (Mục 5.2c), Q5 dự báo viral (Mục 5.5),
Q6 K-means (Mục 5.6 — sẽ bổ sung).

## Cấu trúc

```
05_Code_Output/
├── python/
│   ├── 01_make_labels.py        # 4.4: tạo labels.csv (viral_A, breakout_B, viral_C)
│   ├── 02_q2c_chisquare.py      # 5.2c: Q2c + xuất Excel tổng hợp
│   ├── 03_q5_forecast.py        # 5.5: Q5 dự báo viral (DT, RF, SVM, XGBoost, baseline)
│   └── md2docx_q5.py            # chuyển báo cáo Q5 (Markdown) sang Word
├── R/
│   ├── 01_check_labels.R        # kiểm tra chéo labels.csv
│   ├── 02_q2c_chisq.R           # đối chiếu Chi-square Q2c
│   └── 03_q5_rf.R               # đối chiếu Random Forest Q5 (viral_A, fold 1)
├── outputs/
│   ├── 4.4 labels/              # Task 1
│   │   ├── labels.csv           # nhãn viral cho 96.334 video
│   │   ├── labels_summary.csv
│   │   ├── labels_check.md
│   │   ├── labels_check_R.txt
│   │   └── labels_README.md
│   ├── 5.2c q2c/                # Task 2 — Bảng 5.4, Hình 5.5, workbook, report
│   └── 5.5 Q5/                  # Task 3 — Bảng 5.11–5.16, Hình 5.8, workbook, report
├── requirements.txt
├── env_python.txt
└── env_R.txt
```

## Chạy lại

```powershell
py 05_Code_Output/python/01_make_labels.py
py 05_Code_Output/python/02_q2c_chisquare.py
py 05_Code_Output/python/03_q5_forecast.py
py 05_Code_Output/python/03_q5_forecast.py --quick   # kiểm tra nhanh 2 fold

# Đối chiếu bằng R (Rscript không có trong PATH)
& "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" 05_Code_Output/R/01_check_labels.R
& "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" 05_Code_Output/R/02_q2c_chisq.R
& "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" 05_Code_Output/R/03_q5_rf.R
```

## Quy ước chung

- `random_state = 42` / `set.seed(42)`; kết quả tất định phải khớp 3 chữ số thập phân.
- Chỉ dùng X_PRE (Bảng 4.2) cho Q5; có `assert` chặn cột cấm.
- GroupKFold 5 fold theo `channel_id`; kiểm tra thời gian với mốc 01/07/2026.
- Mọi số liệu hiện tại tính trên snapshot 07/11/2026 và **phải chạy lại** trên
  `data_final_20261113` trước hạn 15/11/2026 23:59.

## Đầu ra chính của Q5 (`outputs/5.5 Q5/`)

| File | Nội dung |
|---|---|
| `q5_labels_summary.csv` | Bảng 5.12 — số dương từng nhãn |
| `q5_model_comparison.csv` | Bảng 5.11 / 5.13 — so sánh 5 mô hình qua 5 fold |
| `q5_cv_folds.csv` | Kết quả từng fold (để tái lập, đối chiếu R) |
| `q5_time_test.csv` | Bảng 5.14 — kiểm tra theo thời gian |
| `q5_ablation.csv` | Bảng 5.15 — bỏ nhóm biến kênh |
| `q5_sensitivity.csv` | Bảng 5.16 — độ nhạy ngưỡng nhãn A |
| `q5_importance.csv` + `.png` | Hình 5.8 — permutation importance |
| `q5_model_data_*.csv` | Dữ liệu huấn luyện (CSV, UTF-8 BOM) để R đối chiếu |
| `Q5_tong_hop.xlsx` | Workbook tổng hợp nhiều sheet |
| `q5_report.docx` | Bản thảo Mục 5.5 (số liệu thật, chờ data_final) |
| `q5_R_check.txt` | Kết quả đối chiếu Random Forest Python vs R |
