#!/usr/bin/env python3
"""Flat field diff of two report dirs (old/new <asset>.json): per asset, every changed path with old, new, rel change.
Usage: r2-diff.py <dirA> <dirB> [--max N] [--values-only]"""
import json, sys, os, math
def flat(x, p='', out=None):
    out = {} if out is None else out
    if isinstance(x, dict):
        for k, v in x.items(): flat(v, f'{p}.{k}' if p else k, out)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            key = v.get('id') if isinstance(v, dict) and 'id' in v else i
            flat(v, f'{p}[{key}]', out)
    else: out[p] = x
    return out
a, b = sys.argv[1], sys.argv[2]
mx = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 15
vo = '--values-only' in sys.argv
for f in sorted(os.listdir(a)):
    if not f.endswith('.json'): continue
    try: A = flat(json.load(open(f'{a}/{f}'))); B = flat(json.load(open(f'{b}/{f}')))
    except Exception as e: print(f'{f}: ERROR {e}'); continue
    ch = []
    for k in sorted(set(A) | set(B)):
        x, y = A.get(k, '<absent>'), B.get(k, '<absent>')
        if x == y: continue
        if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
            rel = (y - x) / abs(x) if x else (math.inf if y else 0)
            if abs(rel) < 1e-12: continue
            ch.append((k, x, y, rel))
        elif not vo: ch.append((k, x, y, None))
    print(f'== {f[:-5]}: {len(ch)} changed')
    big = sorted(ch, key=lambda c: -abs(c[3]) if c[3] is not None and math.isfinite(c[3]) else 0)
    for k, x, y, r in big[:mx]:
        rs = f'{r*100:+.4f}%' if r is not None and math.isfinite(r) else ''
        xs, ys = (str(x)[:60], str(y)[:60])
        print(f'   {k}: {xs} -> {ys} {rs}')
