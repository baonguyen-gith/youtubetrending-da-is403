# -*- coding: utf-8 -*-
"""
02_q2c_chisquare.py
===================
Q2c: Chi-square giua the loai (category_name) va kha nang lot Trending.

Hai cap bien (theo Muc 5.2c):
  1) category_name x viral_C  : chi tren video trong in_window_C (khong ngan)
  2) category_name x viral_A  : tren toan bo quan the H
     + ban do vung: bo video ngan (is_short_60 = FALSE)
     + ban do nhay: bo the loai qua it video (Nonprofits & Activism)

Quy uoc:
  - Gop cac the loai co tan so ky vong < 5 vao nhom "Khác".
  - chi2_contingency(correction=False) cho Python; chisq.test(correct=FALSE) cho R.
  - Cramer's V = sqrt(chi2 / (n * (min(r,c) - 1))).
  - Phan du chuan hoa (Pearson): (O - E) / sqrt(E).

Input : 05_Code_Output/outputs/4.4 labels/labels.csv, videos_master.csv
Output: 05_Code_Output/outputs/5.2c q2c/
          - Q2c_tong_hop.xlsx  (workbook tong hop, nhieu sheet)
          - q2c_report.md, q2c_residuals*.png, q2c_R_check.txt
          - tables/*.csv       (bang tho cho may doc va script R)

Chay: py 05_Code_Output/python/02_q2c_chisquare.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from scipy.stats import chi2_contingency

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Duong dan
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parents[1]
OUTPUT_DIR = PROJECT_DIR / "05_Code_Output" / "outputs"
Q2C_DIR = OUTPUT_DIR / "5.2c q2c"
TABLE_DIR = Q2C_DIR / "tables"
TABLE_DIR.mkdir(parents=True, exist_ok=True)

LABELS_CSV = OUTPUT_DIR / "4.4 labels" / "labels.csv"
VIDEOS_CSV = PROJECT_DIR / "videos_master.csv"

SPARSE_CATEGORY = "Nonprofits & Activism"
OTHER_LABEL = "Khác"
EXPECTED_MIN = 5.0

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


# ---------------------------------------------------------------------------
# Ham phan tich
# ---------------------------------------------------------------------------
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    labels = pd.read_csv(
        LABELS_CSV,
        dtype={"video_id": str, "viral_A": "Int8",
               "breakout_B": "Int8", "viral_C": "Int8"},
        low_memory=False,
    )
    videos = pd.read_csv(
        VIDEOS_CSV, usecols=["video_id", "category_name"], low_memory=False
    )
    df = labels.merge(videos, on="video_id", how="left", validate="one_to_one")
    if df["category_name"].isna().any():
        raise ValueError("Co video khong tim thay category_name")
    return df, labels


def cramers_v(chi2: float, n: int, r: int, c: int) -> float:
    denom = n * (min(r, c) - 1)
    return float(np.sqrt(chi2 / denom)) if denom > 0 else np.nan


def analyze_pair(
    data: pd.DataFrame,
    label_col: str,
    pair_name: str,
    note: str = "",
) -> dict:
    """Tra ve obs/exp/resid (DataFrame), thong ke va tom tat theo the loai."""
    d = data.loc[data[label_col].notna(), ["category_name", label_col]].copy()
    d[label_col] = d[label_col].astype(int)

    obs = pd.crosstab(d["category_name"], d[label_col])
    for col in (0, 1):
        if col not in obs.columns:
            obs[col] = 0
    obs = obs[[0, 1]]

    # Lan 1: tim the loai co expected < 5
    chi2_0, p_0, df_0, exp_0 = chi2_contingency(obs.to_numpy(), correction=False)
    bad = (exp_0 < EXPECTED_MIN).any(axis=1)
    merged = list(obs.index[bad])

    # Gop cac the loai do vao "Khác"
    if bad.any():
        other = obs.loc[bad].sum(axis=0)
        obs2 = pd.concat(
            [obs.loc[~bad],
             pd.DataFrame([other.to_numpy()], index=[OTHER_LABEL],
                          columns=obs.columns)]
        )
    else:
        obs2 = obs.copy()

    chi2, p, dof, exp = chi2_contingency(obs2.to_numpy(), correction=False)
    n = int(obs2.to_numpy().sum())
    r, c = obs2.shape
    v = cramers_v(chi2, n, r, c)

    resid = (obs2.to_numpy() - exp) / np.sqrt(exp)
    exp_df = pd.DataFrame(exp, index=obs2.index, columns=["exp_0", "exp_1"])
    resid_df = pd.DataFrame(resid, index=obs2.index,
                            columns=["resid_0", "resid_1"])

    summary = pd.DataFrame({
        "category": obs2.index,
        "n": obs2.sum(axis=1).to_numpy(),
        "trending": obs2[1].to_numpy(),
        "rate": obs2[1].to_numpy() / obs2.sum(axis=1).to_numpy(),
        "expected_trending": exp[:, 1],
        "resid_trending": resid[:, 1],
    }).sort_values("n", ascending=False).reset_index(drop=True)

    most_over = summary.loc[summary["resid_trending"].idxmax()]
    most_under = summary.loc[summary["resid_trending"].idxmin()]

    stats = {
        "pair": pair_name,
        "label": label_col,
        "n": n,
        "chi2": float(chi2),
        "df": int(dof),
        "p_value": float(p),
        "cramers_v": v,
        "min_expected": float(exp.min()),
        "n_cells_expected_lt5": int((exp < EXPECTED_MIN).sum()),
        "n_categories_merged": len(merged),
        "categories_merged": "; ".join(merged),
        "most_over_category": most_over["category"],
        "most_over_resid": float(most_over["resid_trending"]),
        "most_under_category": most_under["category"],
        "most_under_resid": float(most_under["resid_trending"]),
        "n_categories_in_table": int(r),
        "note": note,
    }
    return {
        "obs": obs2,
        "exp": exp_df,
        "resid": resid_df,
        "summary": summary,
        "stats": stats,
        "merged": merged,
    }


def fmt_p(p: float) -> str:
    if p == 0 or p < 1e-300:
        return "< 1e-300"
    return f"{p:.3e}"


def plot_residuals(
    summary: pd.DataFrame,
    path: Path,
    title: str,
    xlabel: str,
) -> None:
    s = summary.sort_values("resid_trending", ascending=True)
    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    colors = ["#c0392b" if v < 0 else "#2e86de"
              for v in s["resid_trending"]]
    bars = ax.barh(s["category"], s["resid_trending"], color=colors,
                   edgecolor="white", linewidth=0.6)
    ax.axvline(0, color="black", linewidth=0.9)
    for x in (-2, 2):
        ax.axvline(x, color="#7f8c8d", linestyle="--", linewidth=0.9)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel("Thể loại", fontsize=11)
    ax.tick_params(axis="both", labelsize=9)
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    ax.set_axisbelow(True)
    for bar, val in zip(bars, s["resid_trending"]):
        offset = 0.15 if val >= 0 else -0.15
        ha = "left" if val >= 0 else "right"
        ax.text(val + offset, bar.get_y() + bar.get_height() / 2,
                f"{val:+.2f}", va="center", ha=ha, fontsize=8)
    ax.margins(x=0.15)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def write_markdown(
    res_c: dict,
    res_a: dict,
    res_a_ns: dict,
    res_a_drop: dict,
    path: Path,
) -> None:
    s_c = res_c["stats"]
    s_a = res_a["stats"]
    s_a_ns = res_a_ns["stats"]
    s_a_drop = res_a_drop["stats"]
    n_window = s_c["n"]
    n_pos_c = int(res_c["obs"][1].sum())
    n_pos_a = int(res_a["obs"][1].sum())

    # Dinh dang so kieu Viet Nam: 1.234.567 va 0,123
    def fi(x: float) -> str:
        return f"{int(x):,}".replace(",", ".")

    def fd(x: float, d: int = 3, sign: bool = False) -> str:
        s = f"{x:+,.{d}f}" if sign else f"{x:,.{d}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")

    def fp(p: float) -> str:
        if p == 0 or p < 1e-300:
            return "< 1e-300"
        return f"{p:.3e}".replace(".", ",")

    def pct(x: float, d: int = 2) -> str:
        return f"{100 * x:.{d}f}%".replace(".", ",")

    lines = []
    lines.append("# 5.2c Q2c: Chi-square giữa thể loại và khả năng lọt Trending\n")
    lines.append("## Phương pháp (tóm tắt)\n")
    lines.append(
        "Chỉ dùng video thuộc cửa sổ `in_window_C` (không ngắn) cho `viral_C`; "
        "lập bảng chéo `category_name × viral_C`, gộp các thể loại có tần số "
        "kỳ vọng dưới 5 vào nhóm **Khác**, báo χ², bậc tự do, p, Cramér's V "
        "và phần dư chuẩn hóa. Làm thêm `category_name × viral_A` trên toàn "
        "bộ H, kèm bản bỏ video ngắn và bản bỏ thể loại quá ít video. "
        "Python dùng `scipy.stats.chi2_contingency(correction=False)`; "
        "R dùng `chisq.test(correct=FALSE)`.\n"
    )

    lines.append("## Cỡ mẫu\n")
    lines.append(f"- `viral_C`: **{fi(n_window)}** video trong cửa sổ, "
                 f"**{fi(n_pos_c)}** video dương ({pct(n_pos_c / n_window)}).")
    lines.append(f"- `viral_A`: **{fi(s_a['n'])}** video trong H, "
                 f"**{fi(n_pos_a)}** video dương "
                 f"({pct(n_pos_a / s_a['n'])}).")
    lines.append(f"- Bản bỏ video ngắn: **{fi(s_a_ns['n'])}** video.\n")

    lines.append("## Bảng 5.4. Kết quả Chi-square\n")
    lines.append("| Cặp biến | χ² | df | p | V | Thể loại vượt kỳ vọng nhiều nhất |")
    lines.append("|---|---:|---:|---:|---:|---|")
    lines.append(
        f"| Thể loại × viral_C | {fd(s_c['chi2'], 3)} | {s_c['df']} | "
        f"{fp(s_c['p_value'])} | {fd(s_c['cramers_v'], 3)} | "
        f"{s_c['most_over_category']} "
        f"(phần dư {fd(s_c['most_over_resid'], 2, sign=True)}) |"
    )
    lines.append(
        f"| Thể loại × viral_A | {fd(s_a['chi2'], 3)} | {s_a['df']} | "
        f"{fp(s_a['p_value'])} | {fd(s_a['cramers_v'], 3)} | "
        f"{s_a['most_over_category']} "
        f"(phần dư {fd(s_a['most_over_resid'], 2, sign=True)}) |"
    )
    lines.append("")

    lines.append("### Kiểm tra độ vững\n")
    lines.append("| Cấu hình | n | χ² | df | p | V | Thể loại vượt kỳ vọng |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")
    for label, s in [
        ("viral_A – bỏ video ngắn", s_a_ns),
        ("viral_A – bỏ Nonprofits & Activism", s_a_drop),
    ]:
        lines.append(
            f"| {label} | {fi(s['n'])} | {fd(s['chi2'], 3)} | {s['df']} | "
            f"{fp(s['p_value'])} | {fd(s['cramers_v'], 3)} | "
            f"{s['most_over_category']} |"
        )
    lines.append("")

    lines.append("## Bảng hồ sơ theo thể loại (viral_C)\n")
    lines.append("| Thể loại | n | Trending | Tỷ lệ | Kỳ vọng | Phần dư |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for _, r in res_c["summary"].iterrows():
        lines.append(
            f"| {r['category']} | {fi(r['n'])} | {fi(r['trending'])} | "
            f"{pct(r['rate'])} | {fd(r['expected_trending'], 2)} | "
            f"{fd(r['resid_trending'], 2, sign=True)} |"
        )
    total_n = res_c["summary"]["n"].sum()
    total_pos = res_c["summary"]["trending"].sum()
    lines.append(
        f"| **Tổng** | {fi(total_n)} | {fi(total_pos)} | "
        f"{pct(total_pos / total_n)} | "
        f"{fd(res_c['summary']['expected_trending'].sum(), 2)} | "
        f"{fd(res_c['summary']['resid_trending'].sum(), 2, sign=True)} |"
    )
    lines.append("")

    lines.append("## Hình 5.5\n")
    lines.append("`q2c_residuals.png` – Phần dư chuẩn hóa của bảng chéo "
                 "thể loại × viral_C (nguồn: `outputs/5.2c q2c/`).\n")

    lines.append("## Giải thích thực tiễn (draft)\n")
    lines.append(
        f"Kết quả cho thấy thể loại có liên quan đến khả năng lọt Trending "
        f"(χ² = {fd(s_c['chi2'], 1)}; df = {s_c['df']}; "
        f"p {fp(s_c['p_value'])}; V = {fd(s_c['cramers_v'], 3)}). "
        "Tuy nhiên, vì n rất lớn, p-value gần như luôn rất nhỏ; độ lớn của "
        "liên hệ nên đọc qua Cramér's V và phần dư chuẩn hóa (Cohen, 1988; "
        "Lin và cộng sự, 2013). Với V khoảng "
        f"{fd(s_c['cramers_v'], 2)}, mức liên hệ là nhỏ đến trung bình theo "
        "quy ước của Cohen, nhưng phần dư cho thấy khác biệt thực tiễn rõ ở "
        "một số thể loại: **Gaming** và **Music** lọt Trending nhiều hơn kỳ "
        "vọng, trong khi **News & Politics**, **Sports**, **Film & Animation** "
        "và nhóm **Khác** lọt ít hơn kỳ vọng. Kết quả này phù hợp với các "
        "nghiên cứu trước cho rằng thể loại nội dung và cách phân phối nội "
        "dung có liên quan đến mức độ phổ biến của video YouTube (Cha và "
        "cộng sự, 2007; Cheng và cộng sự, 2008; Borghol và cộng sự, 2012; "
        "Figueiredo và cộng sự, 2014).\n"
    )
    lines.append(
        "Với `viral_A`, kết quả định hướng tương tự: **Gaming** và **Music** "
        "có tỷ lệ video thuộc nhóm 10% lượt xem cao nhất trong nhóm tuổi cao "
        "hơn kỳ vọng, còn **News & Politics**, **Education**, **Sports**, "
        "**People & Blogs** và **Autos & Vehicles** thấp hơn kỳ vọng. Cần lưu "
        "ý `viral_A` đo lượt xem tương đối trong nhóm tuổi, không đo trực tiếp "
        "việc lọt Trending, nên hai nhãn không thay thế nhau.\n"
    )

    lines.append("## Khuyến nghị (draft)\n")
    lines.append(
        "- Nhà sáng tạo trong **Gaming/Music** có thể ưu tiên tần suất và thời "
        "điểm đăng để tận dụng lợi thế thể loại; đây là tương quan, không phải "
        "quan hệ nhân quả.\n"
        "- Nhà sáng tạo trong **News & Politics/Sports/Education** nên kiểm "
        "tra lại định dạng, độ dài và cách đặt tiêu đề vì tỷ lệ lọt Trending "
        "thấp hơn kỳ vọng dù lượng video lớn.\n"
        "- Nhãn hàng nên chọn thể loại theo mục tiêu chiến dịch: Gaming/Music "
        "cho phủ rộng và khả năng lên Trending; News/Sports cho tiếp cận đúng "
        "đối tượng hơn là kỳ vọng lên Trending.\n"
    )

    lines.append("## Hạn chế (draft)\n")
    lines.append(
        "- `viral_C` chỉ xét video đăng trong cửa sổ ngắn 19/10–26/10/2026, nên "
        f"số dương ít ({fi(n_pos_c)}) và một số thể loại bị gộp vào **Khác**.\n"
        "- Bảng `viral_A` còn 1 video **Nonprofits & Activism** tạo ô kỳ vọng "
        "0,10 (< 5); bản bỏ thể loại này cho kết quả gần như không đổi "
        f"(χ² = {fd(s_a_drop['chi2'], 1)}; "
        f"V = {fd(s_a_drop['cramers_v'], 3)}).\n"
        "- Đây là dữ liệu quan sát, không phải thử nghiệm; kết quả chỉ mô tả "
        "mối liên hệ.\n"
        "- Số liệu hiện tại là bản `data_clean` 03/11 (96.334 video, 466 kênh, "
        "636 video Trending); phải chạy lại trên `data_final_20261113` trước "
        "hạn 15/11 23:59.\n"
    )

    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Xuat workbook Excel tong hop (nhieu sheet)
# ---------------------------------------------------------------------------
HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(color="FFFFFF", bold=True)


def _style_sheet(ws, df: pd.DataFrame, freeze: str = "A2") -> None:
    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center",
                                   wrap_text=True)
    ws.freeze_panes = freeze
    ws.auto_filter.ref = ws.dimensions
    for i, col in enumerate(df.columns, start=1):
        values = [str(col)] + [str(v) for v in df[col].head(200).tolist()]
        width = min(max(len(v) for v in values) + 2, 60)
        ws.column_dimensions[get_column_letter(i)].width = max(width, 10)


def _add_df(writer, sheet_name: str, df: pd.DataFrame) -> None:
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    _style_sheet(writer.sheets[sheet_name], df)


def _add_text(writer, sheet_name: str, lines: list[str]) -> None:
    df = pd.DataFrame({"Noi dung": lines})
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    ws = writer.sheets[sheet_name]
    ws.column_dimensions["A"].width = 120
    for cell in ws["A"]:
        cell.alignment = Alignment(vertical="top", wrap_text=True)
    ws.freeze_panes = "A2"


TOTAL_LABEL = "Tổng"


def add_total_counts(df: pd.DataFrame, label: str = TOTAL_LABEL) -> pd.DataFrame:
    """Them dong tong cho bang dem (quan sat / ky vong / phan du)."""
    total = df.sum(axis=0, numeric_only=True)
    row = pd.DataFrame([total.to_numpy()], index=[label], columns=df.columns)
    out = pd.concat([df, row])
    out.index.name = df.index.name or "category_name"
    return out


def add_total_summary(df: pd.DataFrame, label: str = TOTAL_LABEL) -> pd.DataFrame:
    """Them dong tong cho bang ho so the loai."""
    n = float(df["n"].sum())
    pos = float(df["trending"].sum())
    row = pd.DataFrame([{
        "category": label,
        "n": n,
        "trending": pos,
        "rate": pos / n if n else np.nan,
        "expected_trending": float(df["expected_trending"].sum()),
        "resid_trending": float(df["resid_trending"].sum()),
    }])
    return pd.concat([df, row], ignore_index=True)


def _column_dictionary() -> pd.DataFrame:
    rows = [
        ("01_Bang_5_4", "pair", "Tên cặp biến được kiểm định"),
        ("01_Bang_5_4", "label", "Nhãn đích dùng trong kiểm định"),
        ("01_Bang_5_4", "n", "Số video đưa vào bảng chéo"),
        ("01_Bang_5_4", "chi2", "Giá trị thống kê Chi-square (không hiệu chỉnh liên tục)"),
        ("01_Bang_5_4", "df", "Bậc tự do = (số hàng - 1) × (số cột - 1)"),
        ("01_Bang_5_4", "p_value", "p-value của kiểm định"),
        ("01_Bang_5_4", "cramers_v", "Cramér's V, kích thước hiệu ứng (0 = không liên quan, 1 = liên quan hoàn toàn)"),
        ("01_Bang_5_4", "min_expected", "Tần số kỳ vọng nhỏ nhất trong bảng"),
        ("01_Bang_5_4", "n_cells_expected_lt5", "Số ô có tần số kỳ vọng < 5 (càng ít càng tốt)"),
        ("01_Bang_5_4", "n_categories_merged", "Số thể loại được gộp vào nhóm 'Khác'"),
        ("01_Bang_5_4", "categories_merged", "Tên các thể loại bị gộp"),
        ("01_Bang_5_4", "most_over_category", "Thể loại có phần dư dương lớn nhất (vượt kỳ vọng nhiều nhất)"),
        ("01_Bang_5_4", "most_over_resid", "Phần dư chuẩn hóa của thể loại đó"),
        ("01_Bang_5_4", "most_under_category", "Thể loại có phần dư âm nhất (thấp hơn kỳ vọng nhiều nhất)"),
        ("01_Bang_5_4", "most_under_resid", "Phần dư chuẩn hóa của thể loại đó"),
        ("01_Bang_5_4", "n_categories_in_table", "Số thể loại còn lại trong bảng sau khi gộp"),
        ("01_Bang_5_4", "note", "Ghi chú cấu hình kiểm định"),
        ("02_Ho_so_the_loai_C", "category", "Tên thể loại (hoặc nhóm 'Khác')"),
        ("02_Ho_so_the_loai_C", "n", "Số video của thể loại trong cửa sổ in_window_C"),
        ("02_Ho_so_the_loai_C", "trending", "Số video có viral_C = 1"),
        ("02_Ho_so_the_loai_C", "rate", "Tỷ lệ video lọt Trending = trending / n"),
        ("02_Ho_so_the_loai_C", "expected_trending", "Số video Trending kỳ vọng nếu thể loại không liên quan đến kết quả"),
        ("02_Ho_so_the_loai_C", "resid_trending", "Phần dư chuẩn hóa: (quan sát - kỳ vọng) / căn(kỳ vọng); > +2 là vượt rõ, < -2 là thấp rõ"),
        ("04_Quan_sat_C", "category_name", "Tên thể loại (dòng)"),
        ("04_Quan_sat_C", "0 / 1", "Số video quan sát: cột 0 = không viral, cột 1 = viral"),
        ("06_Ky_vong_C", "exp_0 / exp_1", "Số video kỳ vọng dưới giả thuyết độc lập"),
        ("08_Phan_du_C", "resid_0 / resid_1", "Phần dư chuẩn hóa Pearson của từng ô"),
        ("10_Gop_nhom", "pair", "Cấu hình kiểm định"),
        ("10_Gop_nhom", "category", "Thể loại bị gộp vào nhóm 'Khác'"),
        ("labels.csv", "video_id", "Khóa duy nhất của video"),
        ("labels.csv", "channel_id", "Khóa duy nhất của kênh"),
        ("labels.csv", "in_H", "1 nếu video thuộc quần thể phân tích H, 0 nếu không"),
        ("labels.csv", "age_days_last", "Tuổi video (ngày) tại lần đo cuối"),
        ("labels.csv", "age_b", "Nhóm tuổi dạng [a,b) theo Mục 4.2"),
        ("labels.csv", "views", "Tổng lượt xem lũy kế tại lần đo cuối"),
        ("labels.csv", "views_per_day", "Lượt xem bình quân mỗi ngày"),
        ("labels.csv", "log_views", "log10(views)"),
        ("labels.csv", "rank_in_age", "Hạng trung bình của log_views trong nhóm tuổi (1 = thấp nhất)"),
        ("labels.csv", "n_in_age", "Số video trong cùng nhóm tuổi"),
        ("labels.csv", "pct_in_age", "rank_in_age / n_in_age, dùng để tạo viral_A"),
        ("labels.csv", "viral_A", "1 nếu pct_in_age >= 0,90; 0 nếu không; NA nếu ngoài H"),
        ("labels.csv", "lvpd", "log10(max(views_per_day, 1))"),
        ("labels.csv", "ch_med_loo", "Trung vị lvpd của các video khác cùng kênh và nhóm tuổi (leave-one-out)"),
        ("labels.csv", "n_peers_loo", "Số video khác cùng kênh và nhóm tuổi"),
        ("labels.csv", "breakout_B", "1 nếu lvpd - ch_med_loo >= log10(2); 0 nếu không; NA nếu < 5 video khác"),
        ("labels.csv", "pub_date_vn", "Ngày đăng theo giờ Việt Nam"),
        ("labels.csv", "is_short_60", "TRUE nếu video dài <= 60 giây"),
        ("labels.csv", "ever_trending", "TRUE nếu video từng xuất hiện trong Trending"),
        ("labels.csv", "in_window_C", "TRUE nếu video không ngắn và đăng trong cửa sổ C"),
        ("labels.csv", "viral_C", "1 nếu ever_trending trong cửa sổ C; 0 nếu không; NA nếu ngoài cửa sổ"),
        ("Tất cả bảng đếm", "Tổng", "Dòng tổng ở cuối bảng: cộng các cột. Riêng bảng phần dư, dòng Tổng chỉ là tổng số học, không dùng để kết luận."),
        ("01_Bang_5_4", "Tổng", "Không có dòng tổng vì χ², df, p và Cramér's V không cộng dồn được."),
    ]
    return pd.DataFrame(rows, columns=["File / Sheet", "Cột", "Ý nghĩa"])


def write_workbook(
    tests: pd.DataFrame,
    res_c: dict,
    res_a: dict,
    merged: pd.DataFrame,
    report_path: Path,
    r_log_path: Path,
    path: Path,
) -> None:
    """Gop cac bang Q2c thanh mot workbook Excel nhieu sheet."""
    report_lines = report_path.read_text(encoding="utf-8").splitlines()
    r_lines = (r_log_path.read_text(encoding="utf-8").splitlines()
               if r_log_path.exists()
               else ["Chua chay script R 02_q2c_chisq.R."])

    guide = [
        "Q2c - Chi-square giua the loai (category_name) va kha nang lot Trending",
        "",
        f"Ngay xuat workbook: {datetime.now():%Y-%m-%d %H:%M:%S}",
        "Nguon du lieu: videos_master.csv (ban data_clean 03/11/2026) + labels.csv",
        "",
        "Cach doc workbook:",
        "- Sheet 01_Bang_5_4: bang tong hop 5 cau hinh kiem dinh (Bang 5.4 trong bao cao).",
        "- Sheet 02/03: ho so tung the loai (n, so Trending, ty le, ky vong, phan du).",
        "- Sheet 04-09: bang quan sat, ky vong va phan du chuan hoa cho viral_C va viral_A.",
        "- Sheet 10: danh sach the loai bi gop vao nhom 'Khac'.",
        "- Sheet 11: ket qua doi chieu R voi Python (PASS/FAIL).",
        "- Sheet 12: toan van draft Muc 5.2c de chep vao bao cao.",
        "- Sheet 13: tu dien cot cua labels.csv va cac bang Q2c.",
        "- Cac bang dem va ho so the loai co them dong 'Tong' o cuoi;",
        "  rieng bang kiem dinh (01_Bang_5_4) khong cong don vi chi2/df/p/V khong co y nghia tong.",
        "",
        "Luu y:",
        "- Cac file CSV tho nam trong thu muc con tables/ de may doc va script R doi chieu.",
        "- q2c_tests.csv giu so thuc dang dau cham (may doc); workbook hien thi theo dinh dang so.",
        "- So lieu hien tai la data_clean 03/11, phai chay lai tren data_final_20261113.",
    ]

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        _add_text(writer, "00_Huong_dan", guide)

        _add_df(writer, "01_Bang_5_4", tests)
        ws = writer.sheets["01_Bang_5_4"]
        for row in ws.iter_rows(min_row=2):
            row[2].number_format = "#,##0"
            row[3].number_format = "0.000"
            row[5].number_format = "0.000E+00"
            row[6].number_format = "0.000"
            row[7].number_format = "0.000"
            row[12].number_format = "0.000"
            row[14].number_format = "0.000"

        for name, summary in (
            ("02_Ho_so_the_loai_C", add_total_summary(res_c["summary"])),
            ("03_Ho_so_the_loai_A", add_total_summary(res_a["summary"])),
        ):
            _add_df(writer, name, summary)
            ws = writer.sheets[name]
            for row in ws.iter_rows(min_row=2):
                row[1].number_format = "#,##0"
                row[2].number_format = "#,##0"
                row[3].number_format = "0.00%"
                row[4].number_format = "0.00"
                row[5].number_format = "0.000"

        _add_df(writer, "04_Quan_sat_C", add_total_counts(res_c["obs"]).reset_index())
        _add_df(writer, "05_Quan_sat_A", add_total_counts(res_a["obs"]).reset_index())
        _add_df(writer, "06_Ky_vong_C", add_total_counts(res_c["exp"]).reset_index())
        _add_df(writer, "07_Ky_vong_A", add_total_counts(res_a["exp"]).reset_index())
        _add_df(writer, "08_Phan_du_C", add_total_counts(res_c["resid"]).reset_index())
        _add_df(writer, "09_Phan_du_A", add_total_counts(res_a["resid"]).reset_index())
        _add_df(writer, "10_Gop_nhom", merged)
        _add_text(writer, "11_Kiem_tra_R", r_lines)
        _add_text(writer, "12_Du_thao_bao_cao", report_lines)
        _add_df(writer, "13_Tu_dien_cot", _column_dictionary())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    df, _ = load_data()
    h = df.loc[df["in_H"] == True].copy()

    # 1) viral_C trong cua so in_window_C
    data_c = h.loc[h["in_window_C"] == True]
    res_c = analyze_pair(
        data_c, "viral_C", "category_name x viral_C",
        note="Chi dung video trong in_window_C (khong ngan)",
    )

    # 2) viral_A tren toan bo H
    res_a = analyze_pair(
        h, "viral_A", "category_name x viral_A",
        note="Tren toan bo quan the H",
    )

    # 3) Do vung: bo video ngan
    res_a_ns = analyze_pair(
        h.loc[h["is_short_60"] == False], "viral_A",
        "category_name x viral_A (non-short)",
        note="Bo video ngan (is_short_60 = FALSE)",
    )

    # 4) Do nhay: bo the loai qua it video
    h_drop = h.loc[h["category_name"] != SPARSE_CATEGORY]
    res_a_drop = analyze_pair(
        h_drop, "viral_A", "category_name x viral_A (drop sparse)",
        note=f"Bo {SPARSE_CATEGORY}",
    )

    # 5) Do nhay + do vung
    res_a_ns_drop = analyze_pair(
        h_drop.loc[h_drop["is_short_60"] == False], "viral_A",
        "category_name x viral_A (non-short, drop sparse)",
        note=f"Bo video ngan va {SPARSE_CATEGORY}",
    )

    # ------------------------------------------------------------------
    # Xuat file
    # ------------------------------------------------------------------
    add_total_counts(res_c["obs"]).to_csv(
        TABLE_DIR / "q2c_table_viral_C.csv", encoding="utf-8-sig")
    add_total_counts(res_a["obs"]).to_csv(
        TABLE_DIR / "q2c_table_viral_A.csv", encoding="utf-8-sig")
    add_total_counts(res_c["exp"]).to_csv(
        TABLE_DIR / "q2c_expected_viral_C.csv", encoding="utf-8-sig")
    add_total_counts(res_a["exp"]).to_csv(
        TABLE_DIR / "q2c_expected_viral_A.csv", encoding="utf-8-sig")
    add_total_counts(res_c["resid"]).to_csv(
        TABLE_DIR / "q2c_residuals_viral_C.csv", encoding="utf-8-sig")
    add_total_counts(res_a["resid"]).to_csv(
        TABLE_DIR / "q2c_residuals_viral_A.csv", encoding="utf-8-sig")
    add_total_summary(res_c["summary"]).to_csv(
        TABLE_DIR / "q2c_category_summary_viral_C.csv",
        index=False, encoding="utf-8-sig")
    add_total_summary(res_a["summary"]).to_csv(
        TABLE_DIR / "q2c_category_summary_viral_A.csv",
        index=False, encoding="utf-8-sig")

    tests = pd.DataFrame([
        res_c["stats"], res_a["stats"], res_a_ns["stats"],
        res_a_drop["stats"], res_a_ns_drop["stats"],
    ])
    tests.to_csv(TABLE_DIR / "q2c_tests.csv", index=False,
                 encoding="utf-8-sig")

    merged_rows = []
    for r in (res_c, res_a, res_a_ns, res_a_drop, res_a_ns_drop):
        for cat in r["merged"]:
            merged_rows.append({"pair": r["stats"]["pair"], "category": cat})
    pd.DataFrame(merged_rows).to_csv(
        TABLE_DIR / "q2c_merged_categories.csv", index=False,
        encoding="utf-8-sig")

    plot_residuals(
        res_c["summary"],
        Q2C_DIR / "q2c_residuals.png",
        "Phần dư chuẩn hóa: Thể loại × viral_C",
        "Phần dư chuẩn hóa (viral_C = 1: có lọt Trending)",
    )
    plot_residuals(
        res_a["summary"],
        Q2C_DIR / "q2c_residuals_viral_A.png",
        "Phần dư chuẩn hóa: Thể loại × viral_A",
        "Phần dư chuẩn hóa (viral_A = 1: nhóm 10% lượt xem cao nhất)",
    )

    write_markdown(res_c, res_a, res_a_ns, res_a_drop,
                   Q2C_DIR / "q2c_report.md")

    workbook_path = Q2C_DIR / "Q2c_tong_hop.xlsx"
    write_workbook(
        tests=tests,
        res_c=res_c,
        res_a=res_a,
        merged=pd.DataFrame(merged_rows),
        report_path=Q2C_DIR / "q2c_report.md",
        r_log_path=Q2C_DIR / "q2c_R_check.txt",
        path=workbook_path,
    )

    # ------------------------------------------------------------------
    # In tom tat
    # ------------------------------------------------------------------
    print("Da tao thu muc:", Q2C_DIR)
    print("Da tao workbook:", workbook_path)
    print("\nBang 5.4:")
    show = tests[["pair", "n", "chi2", "df", "p_value", "cramers_v",
                  "min_expected", "n_cells_expected_lt5",
                  "most_over_category", "most_over_resid"]]
    print(show.to_string(index=False))
    print("\nThe loai bi gop vao Khác:")
    print(pd.DataFrame(merged_rows).to_string(index=False))
    print("\nTom tat viral_C:")
    print(res_c["summary"].to_string(index=False))
    print("\nTom tat viral_A:")
    print(res_a["summary"].to_string(index=False))


if __name__ == "__main__":
    main()
