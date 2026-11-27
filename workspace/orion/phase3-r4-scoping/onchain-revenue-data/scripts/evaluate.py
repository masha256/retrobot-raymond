"""Evaluate pricing methods per (day, chain). exec after lib, agg, pricing; needs TOK, anchors, FEEDREAD, CROSS, DLP."""
import statistics

def evaluate(d, c, floors=(10_000, 50_000, 250_000), main_floor=50_000):
    m = load(d, c)
    pools = [p for p in m["pools"] if p.get("token0") and p.get("token1")]
    dec = lambda t: (TOK[c].get(t, {}).get("decimals") or 18)
    P_dl = {t: v.get("price") for t, v in DLP.get((d, c), {}).items()}
    # token fee amounts
    T = {}
    for p in pools:
        a = pool_amounts(p)
        for i, t in enumerate((p["token0"], p["token1"])):
            e = T.setdefault(t, {"gross": 0, "alloc": 0})
            e["gross"] += a["gross"][i]
            if a.get("alloc"): e["alloc"] += max(0, a["alloc"][i])
    human = {t: {k: v / 10 ** dec(t) for k, v in e.items()} for t, e in T.items()}
    ref = {t: human[t]["gross"] * P_dl[t] for t in human if P_dl.get(t) is not None}
    ref_total = sum(ref.values()); ref_alloc = sum(human[t]["alloc"] * P_dl[t] for t in human if P_dl.get(t) is not None)
    no_dl = sorted([(t, TOK[c].get(t, {}).get("symbol"), human[t]["gross"]) for t in human if P_dl.get(t) is None and human[t]["gross"] > 0], key=lambda x: -x[2])
    res = {"chain": c, "day": d, "ref_gross_usd_devonly": ref_total, "ref_alloc_usd_devonly": ref_alloc,
           "tokens_with_fees": sum(1 for t in human if human[t]["gross"] > 0), "tokens_no_dl_price": len(no_dl),
           "methods": {}}
    cross = CROSS.get(c)
    baseA = anchor_prices(c, d, tiers=("A",), cross=cross)
    baseAB = anchor_prices(c, d, tiers=("A", "B"), cross=cross)
    def score(prices, label, src=None):
        priced_ref = sum(v for t, v in ref.items() if t in prices)
        ours_g = sum(human[t]["gross"] * prices[t] for t in human if t in prices)
        ours_a = sum(human[t]["alloc"] * prices[t] for t in human if t in prices)
        # extra value we price that DL cannot
        ours_nodl = sum(human[t]["gross"] * prices[t] for t in human if t in prices and P_dl.get(t) is None)
        top = sorted(ref.items(), key=lambda kv: -kv[1])[:30]
        errs = []
        for t, v in top:
            if t in prices and P_dl[t]:
                errs.append((abs(prices[t] / P_dl[t] - 1), t, TOK[c].get(t, {}).get("symbol"), v, prices[t], P_dl[t], (src or {}).get(t, ("?",))[0]))
        errs.sort(reverse=True)
        w = sum(e[3] for e in errs)
        res["methods"][label] = {
            "coverage_pct_of_ref": 100 * priced_ref / ref_total if ref_total else None,
            "gross_usd": ours_g, "alloc_usd": ours_a, "gross_usd_tokens_dl_cannot_price": ours_nodl,
            "gross_vs_ref_pct": 100 * (ours_g / ref_total - 1) if ref_total else None,
            "top30_priced": len(errs),
            "top30_worst": [(round(100 * e[0], 2), e[2], round(e[3]), e[4], e[5], e[6]) for e in errs[:3]],
            "top30_median_err_pct": round(100 * statistics.median([e[0] for e in errs]), 3) if errs else None,
            "top30_feeweighted_err_pct": round(100 * sum(e[0] * e[3] for e in errs) / w, 3) if w else None,
        }
    score(baseA, "anchors_A")
    score(baseAB, "anchors_AB")
    for F in floors:
        pr, src = price_graph(c, pools, baseAB, F, dec=dec); score(pr, f"graph_AB_floor{F // 1000}k", src)
        pr, src = price_graph(c, pools, baseA, F, dec=dec); score(pr, f"graph_A_floor{F // 1000}k", src)
    pr, src = price_graph(c, pools, baseAB, main_floor, use_twap=True, dec=dec); score(pr, f"graph_AB_floor{main_floor // 1000}k_twap30m", src)
    prM, srcM = price_graph(c, pools, baseAB, main_floor, dec=dec)
    # pool-local: each pool's fees via its own anchor side (no global price)
    for F in (0, main_floor):
        v_g = 0.0; v_cov_ref = 0.0
        for p in pools:
            a = pool_amounts(p)
            t0, t1 = p["token0"], p["token1"]; d0, d1 = dec(t0), dec(t1)
            f = spot_1_per_0(p, d0, d1)
            for k, (t, o) in enumerate(((t0, t1), (t1, t0))):
                amt = a["gross"][k] / 10 ** dec(t)
                if amt <= 0: continue
                pt = None
                if t in baseAB: pt = baseAB[t]
                elif o in baseAB and f:
                    depth = ((p.get("bal") or [0, 0])[1 - k] or 0) / 10 ** dec(o) * baseAB[o]
                    if depth >= F: pt = f * baseAB[o] if k == 0 else baseAB[o] / f
                if pt is not None:
                    v_g += amt * pt
                    if P_dl.get(t) is not None: v_cov_ref += amt * P_dl[t]
        res["methods"][f"pool_local_floor{F // 1000}k"] = {"gross_usd": v_g, "coverage_pct_of_ref": 100 * v_cov_ref / ref_total if ref_total else None,
                                                          "gross_vs_ref_pct": 100 * (v_g / ref_total - 1) if ref_total else None}
    # recommended-method details
    res["recommended"] = f"graph_AB_floor{main_floor // 1000}k"
    res["price_sources_count"] = dict(Counter(v[0] for t, v in srcM.items() if t in human and human[t]["gross"] > 0))
    res["no_dl_price_top"] = [(t, s, a, prM.get(t)) for t, s, a in no_dl[:8]]
    # per-token table (for citations)
    res["tokens"] = {t: {"sym": TOK[c].get(t, {}).get("symbol"), "gross": human[t]["gross"], "alloc": human[t]["alloc"],
                         "p_onchain": prM.get(t), "p_src": srcM.get(t, (None,))[0], "p_src_pool": srcM.get(t, (None, None))[1],
                         "p_dl_devonly": P_dl.get(t)} for t in human if human[t]["gross"] > 0 or human[t]["alloc"] > 0}
    return res
