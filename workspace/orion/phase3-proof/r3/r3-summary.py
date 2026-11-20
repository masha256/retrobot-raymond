#!/usr/bin/env python3
"""R3 proof summary: per-asset rebuild/purge counts, old -> new circulating-derived figures at D, every differing path
outside the expected classes (S: circulating-derived, L: source labels), D-91 identity, and the new-code-before-rebuild
check. Reads the files r3-proof.sh wrote. Exit 1 if any unexpected path differs."""
import json, os, re, sys
OUT = os.path.dirname(os.path.abspath(__file__))
A = 'aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv'.split()
S_PAT = re.compile(r'^(marketCap|incomeStatement\.multiples\.mcapTo.*|incomeStatement\.perToken\.(revenue|grossProfit|holderFlow\..*|dilution|circulatingSupply))$')
L_PAT = re.compile(r'^incomeStatement\.provenance\.(sources|thirdParty).*$')
ld = lambda p: json.load(open(p))
days = ld(f'{OUT}/days.json')
print(f"R3 proof: D = {days['D']}, D-91 = {days['D91']}")
bad = 0
print('\nRebuild / purge counts (copy):')
for a in A:
    dr, yr, d2 = (ld(f'{OUT}/{k}/rebuild-{a}.json') for k in ('dry', 'yes', 'dry2'))
    line = f"  {a:7} targets {dr['rows']} rebuilt {dr['rebuilt']}/{yr['rebuilt']} notRebuildable {len(dr['notRebuildable'])} kept {len(dr['kept'])} refused {len(dr['refused'])} unchanged {dr['unchanged']} calls {dr['calls']}+{yr['calls']} 2nd-dry rebuilt {d2['rebuilt']}"
    if os.path.exists(f'{OUT}/yes/purge-{a}.json'):
        pr = ld(f'{OUT}/yes/purge-{a}.json')
        pm = pr['perMetric'][0]
        line += f" | purged {pm['observations']} withoutReplacement {len(pm.get('withoutReplacement', []))}"
    if dr['refused'] or d2['rebuilt'] or dr['rebuilt'] != yr['rebuilt']: line += '  <-- CHECK'; bad += 1
    print(line)
print('\nAt D (old -> new):')
def g(r, path):
    o = r
    for k in path.split('.'):
        o = None if o is None else o.get(k)
    return o
for a in A:
    o, n = ld(f'{OUT}/old/{a}.json'), ld(f'{OUT}/new/{a}.json')
    def f(x):
        return 'null' if x is None else (f'{x:,.0f}' if abs(x) >= 1000 else f'{x:.4g}')
    c0, c1 = g(o, 'incomeStatement.perToken.circulatingSupply'), g(n, 'incomeStatement.perToken.circulatingSupply')
    m0, m1 = o.get('marketCap'), n.get('marketCap')
    h0, h1 = g(o, 'incomeStatement.multiples.mcapToHolderFlow.total'), g(n, 'incomeStatement.multiples.mcapToHolderFlow.total')
    r0, r1 = g(o, 'incomeStatement.multiples.mcapToRevenue'), g(n, 'incomeStatement.multiples.mcapToRevenue')
    pct = f'{(c1 / c0 - 1) * 100:+.2f}%' if c0 and c1 else 'n/a'
    hy = lambda h: f'{100 / h:.2f}%' if h else 'null'
    print(f"  {a:7} circ {f(c0)} -> {f(c1)} ({pct}) mcap {f(m0)} -> {f(m1)} mcap/rev {f(r0)} -> {f(r1)} mcap/HF {f(h0)} -> {f(h1)} HF/mcap {hy(h0)} -> {hy(h1)}")
print('\nDiffering paths outside classes S/L (must be none):')
for a in A:
    for fn in (a, f'{a}-91'):
        d = ld(f'{OUT}/diff/{fn}.json')
        for x in d['diffs']:
            p = x['path']
            if fn.endswith('-91') or not (S_PAT.match(p) or L_PAT.match(p)):
                print(f"  {fn}: {p} {x['kind']} {x.get('old')!r} -> {x.get('new')!r}"); bad += 1
        pre = ld(f'{OUT}/diff/pre-{fn}.json')
        for x in pre['diffs']:
            print(f"  pre-rebuild new-vs-old {fn}: {x['path']} {x.get('old')!r} -> {x.get('new')!r}"); bad += 1
print(f"\nunexpected: {bad}")
sys.exit(1 if bad else 0)
