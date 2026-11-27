"""Load raw per (day, chain) files and aggregate token amounts. exec after lib.py."""
import json, glob, os
RAW = "/home/hermes/.hermes/profiles/raymond/workspace/orion/phase3-r4-scoping/onchain-revenue-data/raw"
DAYS = ["2026-10-22", "2026-10-23", "2026-11-01", "2026-11-15", "2026-11-25", "2026-11-26"]

def load(d, c): return json.load(open(f"{RAW}/{d}_{c}.json"))

def pool_amounts(p):
    """returns dict: gross [f0,f1], mev [m0,m1], alloc [a0,a1] (None if ungauged), alloc_gated"""
    d = p.get("d") or {}
    out = {"gross": [d.get("fee0", 0), d.get("fee1", 0)], "mev": [d.get("mevFee0", 0), d.get("mevFee1", 0)],
           "swaps": d.get("swaps", 0), "vol": [d.get("vol0", 0), d.get("vol1", 0)]}
    if p.get("gauge"):
        gs, ge = p.get("g_s") or {}, p.get("g_e") or {}
        col = p.get("collected", [0, 0])
        def acc(key):
            a, b = gs.get(key), ge.get(key)
            if b is None: return None
            a = a or [0, 0]
            return [b[0] - a[0] + col[0], b[1] - a[1] + col[1]]
        out["alloc"] = acc("raw"); out["alloc_gated"] = acc("gated")
        # VRM state-only estimate: d(acc)*supply_e/1e24 + d(buf) + d(pending_gated - lastPend)
        try:
            S = ge["supply"]; est = []
            for i in range(2):
                da = ge["acc"][i] - (gs.get("acc") or [0, 0])[i]
                db = ge["buf"][i] - (gs.get("buf") or [0, 0])[i]
                dp = (ge["gated"][i] - ge["lastPend"][i]) - (((gs.get("gated") or [0, 0])[i]) - ((gs.get("lastPend") or [0, 0])[i] or 0))
                est.append(da * S / 1e24 + db + dp)
            out["alloc_vrm_state"] = est
        except Exception:
            out["alloc_vrm_state"] = None
    return out
