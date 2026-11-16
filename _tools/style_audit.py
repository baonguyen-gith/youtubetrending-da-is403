import sys, io, re
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from docx import Document
from docx.oxml.ns import qn

for path in sys.argv[1:]:
    doc = Document(path)
    print('=' * 20, path)
    for sname in ['Normal', 'Heading 1', 'Heading 2', 'Heading 3', 'Caption Bang', 'Caption Hinh', 'List Paragraph']:
        try:
            st = doc.styles[sname]
        except KeyError:
            print(sname, 'MISSING'); continue
        f = st.font
        pf = st.paragraph_format
        print(f"{sname}: font={f.name} size={f.size.pt if f.size else None} bold={f.bold} italic={f.italic} color={f.color.rgb if f.color and f.color.rgb else None} align={pf.alignment} before={pf.space_before.pt if pf.space_before else None} after={pf.space_after.pt if pf.space_after else None} line={pf.line_spacing}")
    sec = doc.sections[0]
    print('page', sec.page_width.cm, sec.page_height.cm, 'margins', sec.left_margin.cm, sec.right_margin.cm, sec.top_margin.cm, sec.bottom_margin.cm)
    fonts = Counter()
    for p in doc.paragraphs:
        for r in p.runs:
            fonts[(r.font.name, r.font.size.pt if r.font.size else None)] += 1
    print('run fonts top:', fonts.most_common(8))
    xml = doc.element.xml
    instr = re.findall(r'<w:instrText[^>]*>([^<]*)</w:instrText>', xml)
    print('fields:', instr[:20], 'count', len(instr))
    hl = 0
    for p in doc.paragraphs:
        for r in p.runs:
            if r.font.highlight_color is not None:
                hl += 1
    print('highlighted runs:', hl)
