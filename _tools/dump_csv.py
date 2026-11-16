import sys, os, glob
import pandas as pd

root = os.getcwd()
bases = [d for d in glob.glob(os.path.join(root, '*')) if os.path.isdir(d) and os.path.isdir(os.path.join(d, 'B\u1ea3o'))]
assert bases, 'base not found'
base = bases[0]

paths = [
    ('Ki\u00ean/Outputs/data_final/prep', '*.csv'),
    ('Ki\u00ean/Outputs/data_final/prep', '*.json'),
    ('Ki\u00ean/Outputs/data_final/q2a', '*.csv'),
    ('Ki\u00ean/Outputs/data_final/q2a', '*.json'),
    ('Ki\u00ean/Outputs/data_final/q2b', '*.csv'),
    ('Ki\u00ean/Outputs/data_final/q2b', '*.json'),
    ('Ki\u00ean/Outputs/data_final/q3a', '*.csv'),
    ('Ki\u00ean/Outputs/data_final/q3a', '*.json'),
    ('Ki\u00ean/Outputs/data_final', '*.json'),
    ('Ki\u00ean/outputs/q2d', '*.csv'),
    ('B\u1ea3o/05_Code_Output/outputs/q1', '*.csv'),
    ('B\u1ea3o/05_Code_Output/outputs/q3b', '*.csv'),
    ('B\u1ea3o/05_Code_Output/outputs/reliability', '*.csv'),
    ('B\u1ea3o/05_Code_Output/outputs/powerbi', '*.csv'),
    ('Kh\u00f4i/5.4 timeseries', '*.csv'),
    ('Kh\u00f4i/outputs/trends_check', '*.csv'),
    ('Qu\u1ef3nh/outputs/4.4 labels', '*.csv'),
    ('Qu\u1ef3nh/outputs/5.2c q2c/tables', '*.csv'),
    ('Qu\u1ef3nh/outputs/5.5 Q5', '*.csv'),
    ('Qu\u1ef3nh/outputs/5.6 Q6', '*.csv'),
]

out = open(sys.argv[1], 'w', encoding='utf-8')
for rel, pat in paths:
    d = os.path.join(base, rel)
    files = sorted(glob.glob(os.path.join(d, pat)))
    if not files:
        out.write('\n[MISSING] ' + d + '\n')
    for f in files:
        out.write('\n' + '=' * 80 + '\n')
        out.write('FILE: ' + os.path.relpath(f, root) + '\n')
        if f.endswith('.json'):
            with open(f, encoding='utf-8') as fh:
                out.write(fh.read() + '\n')
            continue
        try:
            df = pd.read_csv(f, encoding='utf-8-sig', dtype=str)
        except Exception as e:
            out.write('ERROR ' + str(e) + '\n')
            continue
        out.write('SHAPE: %d rows x %d cols\n' % df.shape)
        with pd.option_context('display.max_columns', 200, 'display.width', 300,
                               'display.max_colwidth', 80):
            out.write(df.head(80).to_string(index=False) + '\n')
        if len(df) > 80:
            out.write('... (%d more rows)\n' % (len(df)-80))
out.close()
print('ok')
