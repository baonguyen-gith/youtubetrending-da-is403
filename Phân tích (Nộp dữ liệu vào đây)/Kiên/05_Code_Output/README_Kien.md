# Phân tích IS403 của Nguyễn Trung Kiên
**MSSV 24520886 · Nhóm 4 · N3–N6 và phần đối chiếu ngôn ngữ của N7**

Gói này dùng để phân tích trước trên dữ liệu tạm đến 03/11/2026 và chạy lại với dữ liệu chốt ngày 15/11. Bộ dữ liệu đi kèm chỉ chứa videos_master.csv, là bảng duy nhất bốn script của Kiên cần. File được sao chép nguyên byte từ folder data_clean_temp.zip → Dữ liệu mới. Không cần tải thêm dữ liệu YouTube.

## Mở kết quả tạm
| Việc | Mã nguồn Python và R | Kết quả trong outputs_temp |
|---|---|---|
| N3 | prep | prep/so_kiem_tra_Kien.csv gồm người, thời điểm, nguồn, sáu số; các bản gốc theo ngôn ngữ ở cùng thư mục |
| N4 | q2a_tests | q2a/ gồm Welch, KTC chênh lệch, Cohen’s d, Levene, Mann–Whitney, so sánh theo cụm và trong kênh, QQ và phân phối |
| N5 | q2b_anova | q2b/ gồm ANOVA thường, Welch, Kruskal–Wallis, η², hậu kiểm Games–Howell, danh sách nhóm nhỏ, KTC trung bình và hình |
| N6 | q3a_regression | q3a/ gồm hệ số OLS, sai số chuẩn cụm theo kênh, hệ số chuẩn hóa, VIF/GVIF, R² bỏ nhóm, chẩn đoán phần dư |
| N7 | compare_py_vs_R.py; verify_master.py | note_python_vs_R.md, doi_chieu_chi_tiet.csv, kiem_tra_tu_master.csv và .txt |

**Nguồn gốc từng kết quả.** Bảng và hình mang hậu tố R/Python trong outputs_temp kế thừa từ Kien_phan_tich_nhap.zip của nhóm. Các tệp đối chiếu, kiểm tra từ master, dòng kiểm tra của Kiên, bảng q3a_sai_so_tinh_lai và chú thích hình được tạo trong lượt kiểm tra này. Hai kết quả không có hậu tố ngôn ngữ dễ nhầm là q2b_group_means.csv (bảng Power BI do R xuất) và q3a_sai_so_tinh_lai.csv (tính mới bằng NumPy). Ảnh PNG đi kèm là đồ thị chẩn đoán của bản tạm. Phiên làm việc này không có Rscript và thiếu statsmodels/pingouin, nên hai pipeline gốc chưa được chạy lại trọn vẹn tại đây. Bản tạm đã được đối chiếu theo khóa trên 16 cặp bảng, 122 cột kết quả; kiểm tra độc lập 761 giá trị hoặc quyết định từ CSV đầu vào bằng NumPy/pandas/SciPy.

## Chạy từ đầu trên Windows
1. Giải nén ZIP. Mở PowerShell ở thư mục **05_Code_Output**. Cần Python 3.12 và R có lệnh Rscript trong PATH. Kiểm tra bằng lệnh sau.
   
   ~~~powershell
   py -3.12 --version
   Rscript --version
   ~~~
2. Cài thư viện lần đầu. Có thể dùng môi trường ảo mà không cần bật script kích hoạt.

   ~~~powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   Rscript install_R.R
   ~~~
3. Chạy lại trọn bộ trên dữ liệu tạm để kiểm tra máy.

   ~~~powershell
   .\.venv\Scripts\python.exe run_analysis.py --data "../data_clean_temp" --out "outputs_temp_rerun"
   ~~~
4. Khi chốt dữ liệu ngày 15/11, thay đối số --data bằng thư mục thực tế chứa videos_master.csv. Ví dụ nếu tên thư mục đúng là data_final_20261113 như file phân công:

   ~~~powershell
   .\.venv\Scripts\python.exe run_analysis.py --data "../data_final_20261113" --out "outputs_final_20261115"
   ~~~

Trên macOS/Linux dùng python3 -m venv .venv và .venv/bin/python thay đường dẫn Python của Windows. Đường dẫn chứa khoảng trắng cần đặt trong dấu ngoặc kép. Thư mục đích phải là tên mới để không trộn số cũ với số mới.

**Thứ tự thực thi.** Lần lượt prep → q2a_tests → q2b_anova → q3a_regression cho Python, rồi cùng thứ tự cho R. Sau đó so bảng theo khóa, kiểm tra độc lập từ master và tạo figure_notes.md theo từng mục. run.log lưu thời gian thực chạy từng bước, thông báo lỗi và đầu ra lệnh. Nếu có lỗi, thư mục tạm và log được giữ lại để kiểm tra. Chỉ khi các bước đều đạt thì thư mục mang tên --out mới xuất hiện. Thời gian cho lần chạy mới được đo trên máy thực tế; phiên bản của lần chạy gốc nằm ở env_python.txt và env_R.txt trong từng mục.

## Kiểm tra độc lập riêng trên bản tạm
Nếu máy đã có pandas, NumPy, SciPy nhưng chưa cài R, có thể xác minh các bảng đã đóng gói bằng PowerShell:

~~~powershell
$env:DATA_DIR="../data_clean_temp"
$env:OUT_ROOT="outputs_temp"
python python/compare_py_vs_R.py
python python/verify_master.py
~~~

Bước thứ nhất so hai đầu ra, dừng nếu lệch khóa, thiếu cột ngoài ngoại lệ đã ghi, khác vị trí giá trị thiếu hoặc khác số sau làm tròn ba chữ số. Bước thứ hai tính từ video gốc: tái dựng sáu số, kiểm tra t/df/p/KTC/d, Levene, U, F và bậc tự do Welch, η², Kruskal–Wallis, cặp Games–Howell, nghiệm bình phương tối thiểu, sai số cụm, VIF từng cột và mức giảm R². p hậu kiểm của R có làm tròn nên dùng ngưỡng tuyệt đối 0,0005; quyết định p < 0,05 phải trùng. Kiểm tra độc lập không tái tính mọi cột trong gói, ví dụ KTC Games–Howell được đối chiếu trực tiếp giữa hai đầu ra.

## Quy ước và kết quả tạm
- H gồm in_history, không live/upcoming, views > 0, age_days_last ≥ 1. ID video là chuỗi 11 ký tự và duy nhất. Tính lv_adj trên toàn H trước khi tách video dài hơn 60 giây. Sáu số theo thứ tự mẫu, kênh, tuổi [7,10), viral_A, trung vị lv_adj và từng Trending là **95.319; 328; 1.594; 9.542; 0,0905; 399**.
- Q2a: cuối tuần 27.914 video so với 67.405 ngày thường. Welch t = 4,514; chênh lệch 0,03488 log₁₀, KTC 95% [0,01974; 0,05003]; Cohen’s d = 0,03184. So trong cùng kênh cho p = 0,115. Mức khác biệt thực tiễn nhỏ.
- Q2b: trên H, khung giờ có Welch F = 61,156, η² = 0,00262. Thể loại có Welch F = 2.053,552, η² = 0,20734 sau khi bỏ một video thuộc thể loại n < 30. Có thêm kết quả bỏ video ngắn. Bảng Power BI gồm factor, group, n, mean_lv_adj, ci_low, ci_high.
- Q3a: 95.318 video, 328 cụm kênh, 30 tham số. R² = 0,484673; mức giảm khi bỏ quy mô kênh 0,226966, thể loại 0,112015, nội dung 0,006505, thời gian 0,001562. Các mức giảm lấy từ bốn mô hình riêng. Subscriber đo khi thu thập. Đây là liên hệ trên mẫu quan sát.
- VIF từng cột và GVIF theo khối biến đều có CSV. Quy tắc sàng lọc sử dụng GVIF^(1/df), bằng VIF với biến một bậc tự do; giữ biến tuổi. Không biến nào bị loại trên dữ liệu tạm. Với dữ liệu mới phải xem lại các nhóm đã loại và log.
- **Đính chính cách đặt tên sai số Q3a.** Trong hai CSV mô hình gốc của nhóm, cột rmse thực tế là √(SSE/(n−k)), tức độ lệch chuẩn phần dư. Bảng q3a_sai_so_tinh_lai.csv cung cấp riêng RMSE huấn luyện √(SSE/n) và residual_sd. Hai chương trình cho lần chạy mới đã xuất cả hai chỉ số đúng tên. Không dùng RMSE huấn luyện để xưng là sai số dự báo ngoài mẫu.

Nguồn quy ước: Phân công.docx, mục 0.2, 0.4, 0.5 và N3–N7; Phan_cong_cong_viec_Nhom4_IS403.xlsx, sheet Kiên. Dùng sáu số và các CSV mới sau khi dữ liệu chốt; bước đối chiếu giữa bốn thành viên cần số do chính từng thành viên chạy.
