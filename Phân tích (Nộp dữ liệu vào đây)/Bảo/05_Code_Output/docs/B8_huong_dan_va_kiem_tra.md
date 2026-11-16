# B8 - Gói dữ liệu chốt: vị trí, tải Drive và kiểm tra

Gói B8 nằm ở gốc repo, trong thư mục `Dữ liệu chính thức/` (đã chuyển từ `Bảo/` sau khi chốt):

- `data_final_20261113/` (5 file, chỉ đọc)
- `checksums.txt` (SHA-256, UTF-8 không BOM, LF)
- `sample_1000.csv` (1.000 video, `random_state = 42`, đủ 55 cột)

Trạng thái: gói đã được đưa lên Drive của nhóm ở `03_Dataset/`; cả 6 mã SHA-256 đã đối chiếu khớp tại vị trí mới. Nếu tải lại từ Drive, làm theo các bước dưới đây để kiểm tra.

## Các bước kiểm tra sau khi tải từ Drive

1. Tải nguyên thư mục `data_final_20261113/`, kèm `checksums.txt` và `sample_1000.csv`, về cùng một thư mục.
2. Mở link Drive bằng cửa sổ ẩn danh hoặc tài khoản Google khác; xác nhận tải được cả 5 file dữ liệu.
3. Chạy lệnh kiểm tra SHA-256 trong thư mục vừa tải (xem bên dưới).
4. Gửi link vào nhóm; ghi vào `bang_tien_do` rằng cả 3 thành viên còn lại đã tải và xác nhận.

## Mã SHA-256

| File | SHA-256 |
| --- | --- |
| `channels_latest.csv` | `add149818183d1b95a76b0f1b5d2a2ffff8714ed879738ad5cc0490dafa0966d` |
| `dq_report.txt` | `41ffb0b0d83ac98082d1862fa5c8270dda471aedfc0d4e3efd44a4c2fbaece39` |
| `measurements.csv` | `f4e17060ec593a553a46553886f717f6cb379f271aedc1a217b12be28aa1b397` |
| `trending_clean.csv` | `6abf42c3bbf243685853464c8ed831b850fe400750ae4d1cc4068592ad67960d` |
| `videos_master.csv` | `abc3de61fc1fb59af710589f0abe8ca11b7cb0efc0165b6f628e9d38246f7544` |
| `sample_1000.csv` | `265c20e82bc8aed5a6a16789a6e2d8d2f7f0e26363c33a2c1370776789eac7aa` |

Kiểm tra trên Windows (chạy trong thư mục chứa `checksums.txt`, ví dụ `Dữ liệu chính thức/`):

```powershell
# Kiểm tra một file
Get-FileHash -Algorithm SHA256 .\data_final_20261113\videos_master.csv

# Kiểm tra toàn bộ theo checksums.txt
Get-Content .\checksums.txt | ForEach-Object {
    $hash, $file = $_ -split '\s+', 2
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $file).Hash
    if ($actual -ieq $hash) { "OK   $file" } else { "FAIL $file" }
}
```

`checksums.txt` ghi đường dẫn tương đối (`data_final_20261113/...` và `sample_1000.csv`), nên phải chạy lệnh ở thư mục chứa `checksums.txt`.

Kiểm tra toàn bộ bằng `sha256sum` (Git Bash/WSL):

```bash
cd "Dữ liệu chính thức"
sha256sum -c checksums.txt
```
