import sys, os, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

path = sys.argv[1]
outpath = sys.argv[2]
doc = Document(path)
body = doc.element.body
items = []
pidx = -1
tidx = -1
for child in body.iterchildren():
    if child.tag == qn('w:p'):
        p = Paragraph(child, doc)
        pidx += 1
        blips = child.findall('.//' + qn('a:blip'))
        rid = [b.get(qn('r:embed')) for b in blips if b.get(qn('r:embed'))]
        imgs = []
        for r in rid:
            try:
                imgs.append(os.path.basename(doc.part.related_parts[r].partname))
            except Exception:
                imgs.append('?' + str(r))
        items.append({
            'type': 'p', 'i': pidx, 'style': p.style.name if p.style is not None else '',
            'text': p.text, 'images': imgs, 'prev_p': pidx,
        })
    elif child.tag == qn('w:tbl'):
        t = Table(child, doc)
        tidx += 1
        rows = [[c.text.replace('\n', ' / ').strip() for c in r.cells] for r in t.rows]
        items.append({'type': 't', 'i': tidx, 'prev_p': pidx, 'rows': len(t.rows),
                      'cols': len(t.columns), 'first': rows[0] if rows else [], 'all': rows})
with open(outpath, 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=1)
print('paras', pidx + 1, 'tables', tidx + 1)
