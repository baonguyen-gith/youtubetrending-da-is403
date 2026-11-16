import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
items = json.load(open(sys.argv[1], encoding='utf-8'))
start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
end = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
for it in items:
    if it['type'] == 'p':
        if not (start <= it['i'] <= end):
            continue
        tag = f"P{it['i']:03d}"
        img = (' IMG:' + ','.join(it['images'])) if it['images'] else ''
        print(f"{tag} [{it['style']}]{img} {it['text']}")
    else:
        if not (start <= it['i'] <= end):
            continue
        print(f"--- TABLE {it['i']} ({it['rows']}x{it['cols']}): {' | '.join(it['first'])[:160]}")
