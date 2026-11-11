from pathlib import Path
import os
root=Path(os.environ.get("OUT_ROOT","outputs"))
plots={
"q2a":{"qqplot":("Phân vị lv_adj của nhóm cuối tuần và ngày thường.","Độ lệch khỏi đường chuẩn cho thấy khác biệt hình dạng phân phối."),"distribution":("Phân bố lv_adj theo nhóm ngày đăng.","Đọc cùng d và khoảng tin cậy của chênh lệch trung bình.")},
"q2b":{"group_means":("Trung bình lv_adj từng khung giờ và thể loại, kèm KTC 95%.","Dùng bảng Games–Howell để so từng cặp."),"group_means_noshort":("Trung bình và KTC 95% sau khi loại video ≤ 60 giây.","Chuẩn tuổi vẫn lấy từ toàn bộ H trước khi lọc.")},
"q3a":{"diagnostics":("Q–Q phần dư và phần dư theo giá trị dự đoán.","Đọc cùng bảng hệ số và sai số chuẩn theo cụm kênh."),"contribution":("Mức giảm R² khi bỏ từng nhóm biến và hệ số chuẩn hóa.","Mỗi nhóm được bỏ riêng, giữ biến tuổi trong mô hình.")}}
for section,entries in plots.items():
    lines=["# Hướng dẫn đọc hình "+section,""]
    for key,(meaning,reading) in entries.items():
        for f in sorted((root/section).glob(section+"_"+key+"_*.png")):
            if f.stem.removesuffix("_R").removesuffix("_python")!=section+"_"+key:continue
            lines += ["### "+f.name,meaning,reading,"Nguồn: videos_master.csv của lần chạy; bảng số cùng thư mục.",""]
    (root/section/"figure_notes.md").write_text("\n".join(lines),encoding="utf-8")
