# -*- coding: utf-8 -*-
"""
md2docx_q5.py
=============
Chuyển báo cáo Markdown của Q5 (q5_report.md) sang Word (.docx) với định dạng
bảng gọn gàng: tiêu đề bảng tô nền xanh navy, chữ trắng, kẻ khung, xen kẽ dòng,
cột số canh phải.

Dùng như hàm:
    from md2docx_q5 import convert_md_text, convert_md_file
    convert_md_text(md_text, Path("q5_report.docx"))

Dùng từ dòng lệnh:
    py 05_Code_Output/python/md2docx_q5.py <input.md> <output.docx>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

# ---------------------------------------------------------------------------
# Màu sắc / cỡ chữ
# ---------------------------------------------------------------------------
NAVY = "1F3864"
NAVY_RGB = RGBColor(0x1F, 0x38, 0x64)
ZEBRA = "F2F5FA"
BORDER = "B4C6E7"
CODE_RGB = RGBColor(0xA3, 0x1B, 0x1B)

HEADER_FILL = NAVY
HEADER_TEXT = RGBColor(0xFF, 0xFF, 0xFF)


# ---------------------------------------------------------------------------
# Tiện ích XML
# ---------------------------------------------------------------------------
def _set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    for old in tc_pr.findall(qn("w:shd")):
        tc_pr.remove(old)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.insert_element_before(
        shd,
        "w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText",
        "w:vAlign", "w:hideMark", "w:headers", "w:cellIns", "w:cellDel",
        "w:cellMerge", "w:tcPrChange",
    )


def _set_table_borders(table, color: str = BORDER, size: int = 6) -> None:
    tbl_pr = table._tbl.tblPr
    for old in tbl_pr.findall(qn("w:tblBorders")):
        tbl_pr.remove(old)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tbl_pr.insert_element_before(
        borders,
        "w:shd", "w:tblLayout", "w:tblCellMar", "w:tblLook",
        "w:tblCaption", "w:tblDescription", "w:tblPrChange",
    )


def _set_table_width_pct(table, pct: int = 100) -> None:
    tbl_pr = table._tbl.tblPr
    for old in tbl_pr.findall(qn("w:tblW")):
        tbl_pr.remove(old)
    width = OxmlElement("w:tblW")
    width.set(qn("w:type"), "pct")
    width.set(qn("w:w"), str(pct * 50))
    tbl_pr.insert_element_before(
        width,
        "w:jc", "w:tblCellSpacing", "w:tblInd", "w:tblBorders", "w:shd",
        "w:tblLayout", "w:tblCellMar", "w:tblLook", "w:tblCaption",
        "w:tblDescription", "w:tblPrChange",
    )


def _set_repeat_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    tr_pr.insert_element_before(
        header,
        "w:tblCellSpacing", "w:jc", "w:hidden", "w:ins", "w:del",
        "w:trPrChange",
    )


def _set_cant_split(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    cant = OxmlElement("w:cantSplit")
    cant.set(qn("w:val"), "true")
    tr_pr.insert_element_before(
        cant,
        "w:trHeight", "w:tblHeader", "w:tblCellSpacing", "w:jc",
        "w:hidden", "w:ins", "w:del", "w:trPrChange",
    )


def _set_cell_margins(table, top=40, bottom=40, left=90, right=90) -> None:
    tbl_pr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for name, val in (("top", top), ("left", left),
                      ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{name}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tbl_pr.insert_element_before(
        mar,
        "w:tblLook", "w:tblCaption", "w:tblDescription", "w:tblPrChange",
    )


# ---------------------------------------------------------------------------
# Inline markdown: **bold**, *italic*, `code`
# ---------------------------------------------------------------------------
INLINE_RE = re.compile(r"(\*\*.+?\*\*|`.+?`|\*[^*]+?\*)")


def _add_inline(paragraph, text: str, base_size: float | None = None,
                bold: bool = False, italic: bool = False) -> None:
    for part in INLINE_RE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            _add_inline(paragraph, part[2:-2], base_size, True, italic)
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt((base_size or 11) - 1)
            run.font.color.rgb = CODE_RGB
            run.bold = bold
            run.italic = italic
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            _add_inline(paragraph, part[1:-1], base_size, bold, True)
        else:
            run = paragraph.add_run(part)
            run.bold = bold
            run.italic = italic
            if base_size:
                run.font.size = Pt(base_size)


# ---------------------------------------------------------------------------
# Bảng
# ---------------------------------------------------------------------------
def _is_numeric(text: str) -> bool:
    t = text.strip().replace("±", "").replace(",", "").replace("%", "")
    t = t.replace("−", "-").replace("–", "-").replace("+", "")
    return bool(re.fullmatch(r"-?\d+(\.\d+)?", t))


def _split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _add_table(doc: Document, header: list[str], aligns: list[str],
               rows: list[list[str]], font_size: float = 9.5) -> None:
    table = doc.add_table(rows=1, cols=len(header))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    table.autofit = True
    _set_table_width_pct(table, 100)
    _set_table_borders(table)
    _set_cell_margins(table)

    hdr = table.rows[0]
    _set_repeat_header(hdr)
    _set_cant_split(hdr)
    for i, text in enumerate(header):
        cell = hdr.cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        _add_inline(p, text, base_size=font_size)
        for run in p.runs:
            run.bold = True
            run.font.color.rgb = HEADER_TEXT
        _set_cell_shading(cell, HEADER_FILL)

    for idx, cells in enumerate(rows):
        row = table.add_row()
        _set_cant_split(row)
        for i, text in enumerate(cells):
            cell = row.cells[i]
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            align = aligns[i] if i < len(aligns) else "left"
            if align == "right" or (align == "auto" and _is_numeric(text)):
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            elif align == "center":
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _add_inline(p, text, base_size=font_size)
            if idx % 2 == 1:
                _set_cell_shading(cell, ZEBRA)


def _parse_table(lines: list[str]) -> tuple[list[str], list[str], list[list[str]]]:
    header = _split_row(lines[0])
    align_cells = _split_row(lines[1])
    aligns = []
    for c in align_cells:
        c = c.strip()
        if c.endswith(":"):
            aligns.append("right")
        elif c.startswith(":") and c.endswith(":"):
            aligns.append("center")
        elif c.startswith(":"):
            aligns.append("left")
        else:
            aligns.append("auto")
    rows = [_split_row(line) for line in lines[2:]]
    # chuẩn hoá số cột
    n = len(header)
    rows = [(r + [""] * n)[:n] for r in rows]
    return header, aligns, rows


# ---------------------------------------------------------------------------
# Chuyển đổi
# ---------------------------------------------------------------------------
def _setup_document(doc: Document) -> None:
    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(1.8)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(11)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    style.paragraph_format.space_after = Pt(4)
    style.paragraph_format.line_spacing = 1.15


def convert_md_text(md_text: str, out_path: Path) -> Path:
    doc = Document()
    _setup_document(doc)
    lines = md_text.splitlines()
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # ---- Bảng ----
        if (stripped.startswith("|")
                and i + 1 < n
                and re.fullmatch(r"\|?[\s:\-|]+\|?", lines[i + 1].strip())
                and "-" in lines[i + 1]):
            block = [stripped]
            j = i + 1
            while j < n and lines[j].strip().startswith("|"):
                block.append(lines[j].strip())
                j += 1
            header, aligns, rows = _parse_table(block)
            _add_table(doc, header, aligns, rows,
                       font_size=9 if len(header) >= 6 else 9.5)
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            i = j
            continue

        # ---- Tiêu đề ----
        if stripped.startswith("# "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(10)
            run = p.add_run(stripped[2:].strip())
            run.bold = True
            run.font.size = Pt(18)
            run.font.name = "Times New Roman"
            run.font.color.rgb = NAVY_RGB
            i += 1
            continue

        if stripped.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(stripped[3:].strip())
            run.bold = True
            run.font.size = Pt(13)
            run.font.name = "Times New Roman"
            run.font.color.rgb = NAVY_RGB
            i += 1
            continue

        if stripped.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(stripped[4:].strip())
            run.bold = True
            run.font.size = Pt(12)
            run.font.name = "Times New Roman"
            i += 1
            continue

        # ---- Danh sách ----
        if re.match(r"^[-*]\s+", stripped):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(2)
            _add_inline(p, re.sub(r"^[-*]\s+", "", stripped))
            i += 1
            continue

        # ---- Đoạn văn ----
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(5)
        _add_inline(p, stripped)
        i += 1

    # ghi metadata nhẹ
    doc.core_properties.title = "Q5 - Dự báo video viral"
    doc.core_properties.subject = "Báo cáo Q5 (IS403 - Nhóm 4)"

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    return out_path


def convert_md_file(md_path: Path, out_path: Path) -> Path:
    text = Path(md_path).read_text(encoding="utf-8")
    return convert_md_text(text, out_path)


def main() -> None:
    if len(sys.argv) != 3:
        print("Cách dùng: py md2docx_q5.py <input.md> <output.docx>")
        raise SystemExit(1)
    out = convert_md_file(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
