# -*- coding: utf-8 -*-
"""
make_final_package.py - Đóng gói dữ liệu chốt (việc B8)

- Sao chép 5 file sạch từ "Data (Chính thức)" sang data_final_20261113/.
- Ghi checksums.txt (SHA-256, UTF-8 không BOM) cho 5 file dữ liệu và sample_1000.csv.
- Tạo sample_1000.csv: 1.000 video chọn ngẫu nhiên, random_state = 42, giữ đủ 55 cột.
- Đặt thư mục và các file dữ liệu ở chế độ chỉ đọc.

Chạy từ thư mục Bao/python:
    python make_final_package.py
    python make_final_package.py --force   # ghi đè gói đã có (gỡ chỉ đọc trước)
"""
import argparse
import csv
import hashlib
import os
import shutil
import stat
from pathlib import Path

import pandas as pd

def _find_bao_root(start: Path) -> Path:
    """Tìm thư mục Bảo/ (chứa 'Data (Chính thức)') từ vị trí script trở lên."""
    for p in [start, *start.parents]:
        if (p / "Data (Chính thức)").is_dir():
            return p
    return start.parents[2]


BASE = _find_bao_root(Path(__file__).resolve().parent)   # .../Bảo
SRC = BASE / "Data (Chính thức)"
DST = BASE / "data_final_20261113"
CHECKSUMS = BASE / "checksums.txt"
SAMPLE = BASE / "sample_1000.csv"

FILES = ["channels_latest.csv", "dq_report.txt", "measurements.csv", "trending_clean.csv", "videos_master.csv"]
EXPECTED = {"channels_latest.csv": 566, "measurements.csv": 1_066_405,
            "trending_clean.csv": 9_091, "videos_master.csv": 140_387}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def set_readonly(path: Path, readonly: bool):
    mode = 0o444 if path.is_file() else 0o555
    if not readonly:
        mode = 0o666 if path.is_file() else 0o777
    os.chmod(path, mode)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="ghi đè data_final_20261113/ đã có")
    args = ap.parse_args()

    if not SRC.is_dir():
        raise SystemExit(f"Không thấy thư mục nguồn: {SRC}")
    missing = [f for f in FILES if not (SRC / f).is_file()]
    if missing:
        raise SystemExit(f"Thiếu file nguồn: {missing}")

    if DST.exists():
        if not args.force:
            raise SystemExit(f"{DST} đã tồn tại; dùng --force nếu muốn ghi đè.")
        for p in DST.rglob("*"):
            if p.is_file():
                set_readonly(p, False)
        set_readonly(DST, False)
        shutil.rmtree(DST)
    DST.mkdir(parents=True)

    for f in FILES:
        shutil.copy2(SRC / f, DST / f)

    # Kiểm tra số dòng trước khi chốt
    for f, expected in EXPECTED.items():
        if f.endswith(".csv"):
            with open(DST / f, encoding="utf-8-sig", newline="") as fh:
                n = sum(1 for _ in csv.reader(fh)) - 1
            if n != expected:
                raise SystemExit(f"{f}: {n:,} dòng, kỳ vọng {expected:,}")

    master = pd.read_csv(DST / "videos_master.csv", dtype={"video_id": str, "channel_id": str},
                         encoding="utf-8-sig", low_memory=False)
    sample = master.sample(n=1000, random_state=42).sort_values("video_id")
    sample.to_csv(SAMPLE, index=False, encoding="utf-8-sig")

    lines = []
    for f in FILES + [SAMPLE.name]:
        p = DST / f if (DST / f).exists() else SAMPLE
        # Ghi đường dẫn tương đối từ thư mục Bảo/ để `sha256sum -c checksums.txt`
        # kiểm tra được cả 5 file dữ liệu và sample_1000.csv từ một chỗ.
        lines.append(f"{sha256(p)}  {p.relative_to(BASE).as_posix()}")
    CHECKSUMS.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    # Chỉ đọc: file dữ liệu trong gói, thư mục gói, sample và checksums
    for f in FILES:
        set_readonly(DST / f, True)
    set_readonly(DST, True)
    set_readonly(SAMPLE, True)
    set_readonly(CHECKSUMS, True)

    print(f"Đã tạo {DST}")
    for f in FILES:
        print(f"  {f:22s} {os.path.getsize(DST / f):>12,} bytes")
    print(f"Đã tạo {SAMPLE} ({len(sample):,} dòng, 55 cột)")
    print(f"Đã ghi {CHECKSUMS}")
    print("Đã đặt chỉ đọc.")


if __name__ == "__main__":
    main()
