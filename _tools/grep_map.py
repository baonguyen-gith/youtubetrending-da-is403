import json, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
d = json.load(open('_tools/map_noidung.json', encoding='utf-8'))
words = sys.argv[1].split('|')
for x in d:
    if x['type'] != 'p':
        continue
    t = x['text']
    hits = [w for w in words if w.lower() in t.lower()]
    if hits:
        print(f"P{x['i']:03d} {hits} :: {t[:400]}")
