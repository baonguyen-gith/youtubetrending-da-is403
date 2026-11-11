"""Chạy từ đầu trên Windows, macOS hoặc Linux; chỉ công bố thư mục đầu ra khi thành công."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

BASE=Path(__file__).resolve().parent
STEPS=("prep","q2a_tests","q2b_anova","q3a_regression")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data",type=Path,required=True,help="Thư mục chứa videos_master.csv")
    parser.add_argument("--out",type=Path,required=True,help="Thư mục kết quả mới")
    args=parser.parse_args();data=args.data.resolve();dest=args.out.resolve()
    if dest.exists(): parser.error("Thư mục kết quả đã tồn tại. Hãy chọn tên mới để giữ lần chạy trước.")
    if not (data/"videos_master.csv").is_file():parser.error("Không tìm thấy videos_master.csv.")
    r=shutil.which("Rscript") or shutil.which("Rscript.exe")
    if not r:parser.error("Cần cài R và thêm Rscript vào PATH để chạy độc lập hai ngôn ngữ.")
    dest.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix=dest.name+"_dang_chay_",dir=dest.parent))
    env=dict(os.environ,DATA_DIR=str(data),OUT_ROOT=str(stage),PYTHONUTF8="1",MPLBACKEND="Agg",OPENBLAS_NUM_THREADS="1")
    commands=[[sys.executable, f"python/{step}.py"] for step in STEPS]
    commands += [[r, f"R/{step}.R"] for step in STEPS]
    commands += [[sys.executable,f"python/{step}.py"] for step in ["compare_py_vs_R","verify_master","figure_notes"]]
    with (stage/"run.log").open("w",encoding="utf-8") as log:
        log.write(f"Dữ liệu: {data}\nUTC: {datetime.now(timezone.utc).isoformat()}\n")
        for command in commands:
            start=time.monotonic();print("Đang chạy",command[-1],flush=True)
            log.write(f"\n>>> {command[-1]}\n");log.flush()
            step=subprocess.run(command,cwd=BASE,env=env,stdout=log,stderr=subprocess.STDOUT)
            log.write(f"\nMã thoát {step.returncode}; {time.monotonic()-start:.2f} giây\n")
            if step.returncode:
                print(f"Lỗi. Xem {stage/'run.log'}",file=sys.stderr);return step.returncode
    stage.rename(dest);print(f"Kết quả đã kiểm tra: {dest}");return 0
if __name__=="__main__":
    sys.exit(main())
