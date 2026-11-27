"""Regenerate per-day summary JSON files. Run: /usr/bin/python3 final_eval.py"""
import json, os, datetime
from collections import Counter
R4 = "/home/hermes/.hermes/profiles/raymond/cache/scratch/r4"
for f in ("lib", "poolenum", "agg", "pricing", "evaluate", "vwap"): exec(open(f"{R4}/{f}.py").read())
OUTD = "/home/hermes/.hermes/profiles/raymond/workspace/orion/phase3-r4-scoping/onchain-revenue-data"
TOK = json.load(open(R4 + "/tokens.json"))
_af = json.load(open(R4 + "/anchors_feeds.json")); anchors, FEEDREAD, CROSS = _af["anchors"], _af["feeds"], _af["cross"]
DLP = {tuple(k.split("|")): v for k, v in json.load(open(R4 + "/dl_prices_devonly.json")).items()}
DLsum = json.load(open(R4 + "/dl_summary.json"))
def dl_rows(dt):
    return {datetime.datetime.fromtimestamp(r[0], datetime.timezone.utc).date().isoformat(): r[1]
            for r in DLsum[f"aero-protocol|{dt}"]["totalDataChartBreakdown"]}
DLF, DLR = dl_rows("dailyFees"), dl_rows("dailyRevenue")
DLNAME = {"base": "Base", "ethereum": "Ethereum", "optimism": "OP Mainnet", "arbitrum": "Arbitrum", "ink": "Ink",
          "robinhood": "Robinhood Chain", "arc": "Arc", "elysium": "Elysium"}
def dl_chain(rows, d, c):
    x = rows.get(d, {}).get(DLNAME[c], {})
    return {"aero": sum(v for k, v in x.items() if k in ("Aero Slipstream", "Aero Basic")), "by_child": x}
def ts_of(d): return int(datetime.datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc).timestamp())

def composite(d, c, floor, tiers=("A",), twap=False):
    """Recommended: Chainlink tier-A anchors -> global graph (deepest pool, anchor-side depth >= floor, <=3 hops)
    -> pool-local fallback (fee token valued at its own pool's price vs a priced side) -> unpriced."""
    m = load(d, c); pools = [p for p in m["pools"] if p.get("token0")]
    dec = lambda t: (TOK[c].get(t, {}).get("decimals") or 18)
    base = anchor_prices(c, d, tiers, CROSS.get(c))
    pr, src = price_graph(c, pools, base, floor, use_twap=twap, dec=dec)
    P_dl = {t: v.get("price") for t, v in DLP.get((d, c), {}).items()}
    usd = al = fb = unp_ref = 0.0; imp = {}; unp = Counter()
    for p in pools:
        a = pool_amounts(p); t0, t1 = p["token0"], p["token1"]
        f = spot_1_per_0(p, dec(t0), dec(t1))
        for k, (t, o) in enumerate(((t0, t1), (t1, t0))):
            amt = a["gross"][k] / 10 ** dec(t); aal = max(0, (a.get("alloc") or [0, 0])[k]) / 10 ** dec(t)
            if amt <= 0 and aal <= 0: continue
            if t in pr: pt = pr[t]
            elif o in pr and f: pt = f * pr[o] if k == 0 else pr[o] / f; fb += amt * pt
            else: unp[t] += amt; unp_ref += amt * (P_dl.get(t) or 0); continue
            usd += amt * pt; al += aal * pt
            e = imp.setdefault(t, [0, 0]); e[0] += amt * pt; e[1] += amt
    s = score_prices(d, c, usd, {t: v[0] / v[1] for t, v in imp.items() if v[1] > 0})
    s.update({"alloc_usd": al, "fallback_pool_local_usd": fb, "unpriced_ref_usd_devonly": unp_ref, "unpriced_tokens": len(unp),
              "graph_sources": dict(Counter(v[0] for v in src.values()))})
    return s

ALL = {}
REC_LABELS = {"rec_A_floor10k_fallback": (10_000, ("A",), False), "rec_A_floor50k_fallback": (50_000, ("A",), False),
              "rec_A_floor250k_fallback": (250_000, ("A",), False), "rec_A_floor10k_twap_fallback": (10_000, ("A",), True),
              "rec_AB_floor10k_fallback": (10_000, ("A", "B"), False)}
for d in DAYS:
    day = {"day": d, "labels": "MEASURED on chain (blocks in each chain entry) except *_devonly (coins.llama.fi historical at day-end, "
           "dev-only reference) and dl_* (CLAIMED: api.llama.fi/summary/fees/aero-protocol, chart row stamped D = UTC day D)", "chains": {}}
    for c in CHAINS:
        if not os.path.exists(f"{RAW}/{d}_{c}.json"): continue
        m = load(d, c); r = evaluate(d, c)
        ALL.setdefault(d, {"chains": {}})["chains"][c] = r
        pools = [p for p in m["pools"] if p.get("token0")]
        dec = lambda t, c=c: (TOK[c].get(t, {}).get("decimals") or 18)
        bA = anchor_prices(c, d, ("A",), CROSS.get(c)); bAB = anchor_prices(c, d, ("A", "B"), CROSS.get(c))
        for lab, base in (("AB", bAB), ("A", bA)):
            u, imp, _ = pool_local(d, c, base, spot_1_per_0); r["methods"][f"pool_local_spot_{lab}"] = score_prices(d, c, u, imp)
            u, imp, _ = pool_local(d, c, base, vwap_1_per_0); r["methods"][f"pool_local_vwap_{lab}"] = score_prices(d, c, u, imp)
            pr, _ = graph_vwap(c, pools, base, 10_000, dec); r["methods"][f"graph_vwap_{lab}_floor10k"] = score_prices(d, c, pr)
        for lab, (F, ti, tw) in REC_LABELS.items(): r["methods"][lab] = composite(d, c, F, ti, tw)
        r["recommended"] = "rec_A_floor10k_fallback"
        r.update({"block_start": m["block_start"], "block_end": m["block_end"], "pools_at_start": m["nstart"], "pools_at_end": m["nend"],
                  "pools_created_in_day": sum(1 for p in m["pools"] if p["new_in_day"]),
                  "gauged_pools_in_set": sum(1 for p in m["pools"] if p.get("gauge")),
                  "pools_with_tape_swaps": sum(1 for p in m["pools"] if (p.get("d") or {}).get("swaps", 0) > 0),
                  "swaps_on_tape": sum((p.get("d") or {}).get("swaps", 0) for p in m["pools"]),
                  "fees_collected_logs": m["n_fees_collected_logs"], "rpc_cost": m["cost"], "seconds": m["seconds"],
                  "dl_fees": dl_chain(DLF, d, c), "dl_revenue": dl_chain(DLR, d, c)})
        day["chains"][c] = r
    json.dump(day, open(f"{OUTD}/{d}.json", "w"), indent=1, default=str)
    ALL[d] = day
json.dump({"anchors": anchors, "cross_chain_anchors": CROSS, "feeds": FEEDREAD}, open(f"{OUTD}/anchors-chainlink.json", "w"), indent=1)
# compact table
rows = []
for d in DAYS:
    for c, r in ALL[d]["chains"].items():
        M = r["methods"]["rec_A_floor10k_fallback"]
        rows.append({"day": d, "chain": c, "gross_usd": round(M["gross_usd"]), "alloc_usd": round(M["alloc_usd"]),
                     "ref_gross_usd_devonly": round(r["ref_gross_usd_devonly"]), "ref_alloc_usd_devonly": round(r["ref_alloc_usd_devonly"]),
                     "coverage_pct": round(M["coverage_pct_of_ref"], 2), "vs_ref_pct": round(M["gross_vs_ref_pct"], 2),
                     "fallback_pct": round(100 * M["fallback_pool_local_usd"] / max(M["gross_usd"], 1), 2),
                     "anchorsA_cov_pct": round(r["methods"]["anchors_A"]["coverage_pct_of_ref"], 1),
                     "anchorsAB_cov_pct": round(r["methods"]["anchors_AB"]["coverage_pct_of_ref"], 1),
                     "graphA10k_cov_pct": round(r["methods"]["graph_A_floor10k"]["coverage_pct_of_ref"], 1),
                     "graphA50k_cov_pct": round(r["methods"]["graph_A_floor50k"]["coverage_pct_of_ref"], 1),
                     "graphA250k_cov_pct": round(r["methods"]["graph_A_floor250k"]["coverage_pct_of_ref"], 1),
                     "dl_fees": round(r["dl_fees"]["aero"]), "dl_rev": round(r["dl_revenue"]["aero"]),
                     "top30_worst": M["top30_worst"][:2], "top30_feeweighted_err_pct": M["top30_feeweighted_err_pct"]})
json.dump(rows, open(f"{OUTD}/summary-table.json", "w"), indent=1)
for x in rows: print(x)
