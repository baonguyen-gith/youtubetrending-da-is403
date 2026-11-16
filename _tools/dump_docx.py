import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn


def iter_block_items(parent):
    parent_elm = parent.element.body
    for child in parent_elm.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, parent)
        elif child.tag == qn('w:tbl'):
            yield Table(child, parent)


def dump(path, out):
    doc = Document(path)
    out.write(f"=== FILE: {os.path.basename(path)} ===\n")
    out.write(f"--- paragraphs: {len(doc.paragraphs)}, tables: {len(doc.tables)} ---\n")
    tcount = 0
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            t = block.text.strip()
            if not t:
                continue
            style = block.style.name if block.style is not None else ''
            out.write(f"[{style}] {t}\n")
        else:
            tcount += 1
            out.write(f"\n<TABLE {tcount}>\n")
            for row in block.rows:
                cells = []
                for c in row.cells:
                    cells.append(c.text.replace('\n', ' / ').strip())
                out.write(" | ".join(cells) + "\n")
            out.write(f"</TABLE {tcount}>\n\n")


if __name__ == '__main__':
    outpath = sys.argv[1]
    with open(outpath, 'w', encoding='utf-8') as out:
        for p in sys.argv[2:]:
            dump(p, out)
            out.write("\n\n")
