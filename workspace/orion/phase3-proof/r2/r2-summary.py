#!/usr/bin/env python3
"""Summarise stage B dry runs: per asset/metric rows, repriced, refused, skipped by reason, old->new sum, inactive CoinGecko rows;
plus rebuild-price-levels counts and refusals."""
import json, glob, os, sys
B = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/.hermes/profiles/raymond/workspace/orion/phase3-proof/r2/B')
tot_inactive = 0
print('asset | metric | rows | repriced | unchanged | refused | skipped | old -> new USD (delta %) | inactive CG rows')
for f in sorted(glob.glob(f'{B}/reprice-dry-*.json')):
    a = f.split('reprice-dry-')[1][:-5]
    d = json.load(open(f))
    for m in d.get('perMetric', []):
        if m['repriced'] == 0 and not m['refused'] and not m.get('inactiveCoingeckoRows'):
            continue
        o, n = m['oldSum'], m['newSum']
        pct = (n / o - 1) * 100 if o else 0
        tot_inactive += m.get('inactiveCoingeckoRows', 0)
        print(f"{a} | {m['metric']} | {m['rows']} | {m['repriced']} | {m['unchanged']} | {len(m['refused'])} | {m['skipped']} | {o:,.0f} -> {n:,.0f} ({pct:+.3f}%) | {m.get('inactiveCoingeckoRows', 0)}")
    if d.get('derived'): print(f"{a} | derived | {json.dumps(d['derived'])[:300]}")
    if d.get('remapped'): print(f"{a} | remapped | {json.dumps(d['remapped'])[:300]}")
print('inactive CoinGecko rows total', tot_inactive)
print()
for f in sorted(glob.glob(f'{B}/levels-dry-*.json')):
    a = f.split('levels-dry-')[1][:-5]
    try: d = json.load(open(f))
    except Exception as e: print(a, 'unreadable', e); continue
    print(a, json.dumps({k: (v if not isinstance(v, list) else (len(v), v[:2])) for k, v in d.items() if k not in ('asset',)})[:400])
