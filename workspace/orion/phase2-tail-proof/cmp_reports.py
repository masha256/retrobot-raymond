"""Compare old vs new report JSON files (v2 and legacy) per asset; numbers at rel 1e-12, everything else exact."""
import json, os, sys
P = sys.argv[1]
o = json.load(open(f'{P}/origin-check.txt')) if open(f'{P}/origin-check.txt').read().strip().startswith('{') else None
if o:
    print('origin-check:', {k: v for k, v in o.items() if not isinstance(v, (list, dict)) or k == 'mismatches'})


def walk(x, p=''):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from walk(v, f'{p}.{k}' if p else k)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from walk(v, f'{p}[{i}]')
    else:
        yield p, x


tot = bad = 0
for f in sorted(os.listdir(f'{P}/out/old')):
    if not f.endswith('.json'):
        continue
    a = json.load(open(f'{P}/out/old/{f}')); b = json.load(open(f'{P}/out/new/{f}'))
    A, B = dict(walk(a)), dict(walk(b)); n = 0
    for k in set(A) | set(B):
        x, y = A.get(k), B.get(k); tot += 1
        same = x == y or (isinstance(x, float) and isinstance(y, float) and abs(x - y) <= 1e-12 * max(abs(x), abs(y)))
        if not same:
            n += 1; bad += 1
            if n <= 5:
                print('  DIFF', f, k, str(x)[:60], '->', str(y)[:60])
    print(f, 'fields', len(A), 'diffs', n)
print('TOTAL fields', tot, 'diffs', bad)
