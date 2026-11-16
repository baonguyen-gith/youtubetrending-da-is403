import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
d = json.load(open('_tools/map_noidung.json', encoding='utf-8'))
want = set(int(a) for a in sys.argv[1:])
for x in d:
    if x['type'] == 't' and x['i'] in want:
        print(f"===== TABLE {x['i']} after P{x['prev_p']} ({x['rows']}x{x['cols']}) =====")
        for r in x['all']:
            print(' | '.join(r))
        print()
