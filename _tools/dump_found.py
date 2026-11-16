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
    out.write(f"=== FILE: {path} ===\n")
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
    needles = sys.argv[2:]
    found = []
    for root, dirs, files in os.walk('.'):
        if '_tools' in root:
            continue
        for f in files:
            if not f.lower().endswith('.docx'):
                continue
            if any(n in f for n in needles):
                found.append(os.path.join(root, f))
    with open(outpath, 'w', encoding='utf-8') as out:
        for p in sorted(found):
            try:
                dump(p, out)
            except Exception as e:
                out.write(f"!!! FAILED {p}: {e}\n")
            out.write("\n\n")
    print(f"dumped {len(found)} files")
