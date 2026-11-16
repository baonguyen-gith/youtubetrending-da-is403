import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
d = json.load(open('_tools/map_noidung.json', encoding='utf-8'))
for x in d:
    if x['type'] == 't':
        print(f"T{x['i']} after P{x['prev_p']} ({x['rows']}x{x['cols']}) first={' | '.join(x['first'])[:90]}")
