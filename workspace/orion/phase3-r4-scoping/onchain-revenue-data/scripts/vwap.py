"""Extra pricing variants: tape VWAP (delta volume ratio) pool-local and graph. exec after evaluate.py."""
def vwap_1_per_0(p, dec0, dec1):
    d = p.get("d") or {}
    v0, v1 = d.get("vol0", 0), d.get("vol1", 0)
    if v0 <= 0 or v1 <= 0: return None
    return (v1 / 10 ** dec1) / (v0 / 10 ** dec0)

def pool_local(d, c, base, pricefn, floor=0, min_swaps=0):
    """Value each pool's fees via its own anchor side. Returns (usd, per-token implied price dict fee-weighted, unpriced list)."""
    m = load(d, c); dec = lambda t: (TOK[c].get(t, {}).get("decimals") or 18)
    usd = 0.0; imp = {}; unp = Counter()
    for p in m["pools"]:
        a = pool_amounts(p); t0, t1 = p["token0"], p["token1"]
        f = pricefn(p, dec(t0), dec(t1))
        for k, (t, o) in enumerate(((t0, t1), (t1, t0))):
            amt = a["gross"][k] / 10 ** dec(t)
            if amt <= 0: continue
            pt = None
            if t in base: pt = base[t]
            elif o in base and f and (a["swaps"] >= min_swaps):
                depth = ((p.get("bal") or [0, 0])[1 - k] or 0) / 10 ** dec(o) * base[o]
                if depth >= floor: pt = f * base[o] if k == 0 else base[o] / f
            if pt is None: unp[t] += amt; continue
            usd += amt * pt
            e = imp.setdefault(t, [0.0, 0.0]); e[0] += amt * pt; e[1] += amt
    return usd, {t: v[0] / v[1] for t, v in imp.items() if v[1] > 0}, unp

def graph_vwap(c, pools, base, floor, dec, rounds=3):
    prices = dict(base); src = {t: ("anchor", None, 0) for t in base}
    for rnd in range(1, rounds + 1):
        cand = {}
        for p in pools:
            t0, t1 = p["token0"], p["token1"]
            f = vwap_1_per_0(p, dec(t0), dec(t1))
            if not f: continue
            bal = p.get("bal") or [None, None]
            for known, unk, ki in ((t1, t0, 1), (t0, t1, 0)):
                if known in prices and unk not in prices and bal[ki]:
                    depth = bal[ki] / 10 ** dec(known) * prices[known]
                    if depth < floor: continue
                    pu = f * prices[known] if unk == t0 else prices[known] / f
                    # weight by the day's volume on the known side (USD)
                    vol = ((p["d"]["vol1"] if ki == 1 else p["d"]["vol0"]) / 10 ** dec(known)) * prices[known]
                    if unk not in cand or vol > cand[unk][1]: cand[unk] = (pu, vol, p["pool"])
        if not cand: break
        for t, (pu, w, pool) in cand.items(): prices[t] = pu; src[t] = (f"vwap_hop{rnd}", pool, w)
    return prices, src

def score_prices(d, c, prices_or_usd, implied=None):
    r = ALL[d]["chains"][c]; T = r["tokens"]; ref_total = r["ref_gross_usd_devonly"]
    if implied is None:
        usd = sum(v["gross"] * prices_or_usd[t] for t, v in T.items() if t in prices_or_usd); implied = prices_or_usd
    else: usd = prices_or_usd
    cov = sum(v["gross"] * v["p_dl_devonly"] for t, v in T.items() if t in implied and v["p_dl_devonly"]) / ref_total * 100
    top = sorted([(v["gross"] * v["p_dl_devonly"], t) for t, v in T.items() if v["p_dl_devonly"]], reverse=True)[:30]
    errs = sorted([(abs(implied[t] / T[t]["p_dl_devonly"] - 1) * 100, T[t]["sym"], round(val)) for val, t in top if t in implied], reverse=True)
    w = sum(e[2] for e in errs) or 1
    return {"gross_usd": usd, "coverage_pct_of_ref": cov, "gross_vs_ref_pct": 100 * (usd / ref_total - 1),
            "top30_priced": len(errs), "top30_worst": [(round(e[0], 2), e[1], e[2]) for e in errs[:3]],
            "top30_feeweighted_err_pct": round(sum(e[0] * e[2] for e in errs) / w, 3)}
