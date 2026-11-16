import sys, io, zipfile, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from docx import Document
for path in sys.argv[1:]:
    print('=' * 20, path)
    doc = Document(path)
    print([s.name for s in doc.styles][:40])
    z = zipfile.ZipFile(path)
    x = z.read('word/styles.xml').decode('utf-8')
    m = re.search(r'<w:docDefaults>.*?</w:docDefaults>', x, re.S)
    print(m.group(0)[:1200] if m else 'no docDefaults')
