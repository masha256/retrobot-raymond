"""On-chain pricing engine for fee tokens. exec after lib.py + agg.py; needs TOK, anchors/FEEDREAD."""
import math
Q96 = 2 ** 96

def spot_1_per_0(p, dec0, dec1):
    """Human price of token0 in token1 at end block (spot)."""
    if "cl" in p["kind"]:
        if not p.get("sqrtP"): return None
        return (p["sqrtP"] / Q96) ** 2 * 10 ** (dec0 - dec1)
    r = p.get("reserves")
    if not r or r[0] == 0 or r[1] == 0: return None
    x, y = r[0] / 10 ** dec0, r[1] / 10 ** dec1
    if p.get("stable") or p["kind"] in ("v2s", "lite_v2s"):  # stable() getter reverts on these pools; the factory defines the curve
        return (3 * x * x * y + y ** 3) / (x ** 3 + 3 * x * y * y)
    return y / x

def twap_1_per_0(p, dec0, dec1):
    if "cl" in p["kind"] and p.get("twap_tick_1800") is not None:
        return 1.0001 ** p["twap_tick_1800"] * 10 ** (dec0 - dec1)
    return spot_1_per_0(p, dec0, dec1)

def anchor_prices(c, day, tiers=("A", "B"), cross=None):
    """token -> USD from Chainlink feeds read at the day-end block."""
    out = {}
    for t, v in anchors[c].items():
        if v["tier"] not in tiers: continue
        fr = FEEDREAD[c]["days"].get(day, {}).get(v["feed"])
        if fr and fr["answer"] > 0: out[t] = fr["answer"]
    if cross:
        for t, (cc, ft) in cross.items():
            fr = FEEDREAD[cc]["days"].get(day, {}).get(ft)
            if fr: out[t] = fr["answer"]
    return out

def price_graph(c, pools, base_prices, floor_usd, use_twap=False, rounds=3, dec=None):
    """Iteratively price tokens from their deepest qualifying pool vs an already-priced token."""
    prices = dict(base_prices); src = {t: ("anchor", None, 0) for t in base_prices}
    for rnd in range(1, rounds + 1):
        cand = {}
        for p in pools:
            t0, t1 = p["token0"], p["token1"]
            d0, d1 = dec(t0), dec(t1)
            f = (twap_1_per_0 if use_twap else spot_1_per_0)(p, d0, d1)
            if not f or f <= 0 or not math.isfinite(f): continue
            bal = p.get("bal") or [None, None]
            for known, unk, k_idx in ((t1, t0, 1), (t0, t1, 0)):
                if known in prices and unk not in prices and bal[k_idx]:
                    depth = bal[k_idx] / 10 ** dec(known) * prices[known]
                    if depth < floor_usd: continue
                    pu = f * prices[known] if unk == t0 else prices[known] / f
                    if unk not in cand or depth > cand[unk][1]: cand[unk] = (pu, depth, p["pool"])
        if not cand: break
        for t, (pu, depth, pool) in cand.items():
            prices[t] = pu; src[t] = (f"pool_hop{rnd}", pool, depth)
    return prices, src

def pool_local_value(p, amounts, base_prices, dec, floor_usd=0):
    """Value one pool's fee amounts [a0, a1] via its own anchor side; None for the unpriceable part."""
    t0, t1 = p["token0"], p["token1"]; d0, d1 = dec(t0), dec(t1)
    f = spot_1_per_0(p, d0, d1)
    v, unp = 0.0, 0.0
    for k, (t, o) in enumerate(((t0, t1), (t1, t0))):
        a = amounts[k] / 10 ** (d0 if k == 0 else d1)
        if a == 0: continue
        if t in base_prices: v += a * base_prices[t]; continue
        bal = (p.get("bal") or [0, 0])[1 - k] or 0
        depth = bal / 10 ** dec(o) * base_prices.get(o, 0)
        if o in base_prices and f and depth >= floor_usd:
            pt = f * base_prices[o] if k == 0 else base_prices[o] / f
            v += a * pt
        else:
            unp += 1  # flag
            v += float("nan") if False else 0
    return v
