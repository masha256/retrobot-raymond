"""Enumerate Aero pools + gauges per chain at a block. exec after lib.py."""
import json, os
R4 = "/home/hermes/.hermes/profiles/raymond/cache/scratch/r4"
DEP = R4 + "/metadex-public/deployment-addresses"
DEPCL = R4 + "/metadex-slipstream-public/deployment-addresses"
FN = {"base": "base", "ethereum": "ethereum", "optimism": "optimism", "arbitrum": "arbitrum", "ink": "ink",
      "robinhood": "robinhood", "arc": "arc"}
LEAFVOTER = "0x382409fad8503FbCdbB27A4211551fa03e884078"

ELYSIUM = {"poolTape": "0x34bdD64B19D8631F936c2D07F19AAa6B83515992", "clPoolTape": "0x27D5EB73e7406675F6B0CbD037490ec3dba935a4",
           "factories": [("v2s", "0x78589E876edcEbdce72ee3436ab3c9AD3a7cEF2D", "0xb89Df768aF2CFE637ceB352c587Fe8edAf491d03"),
                         ("v2v", "0x8E6a9FCd1d638CC760Ffba397605Fe3355dE76D2", "0xf2E6DB898840e0ae91C44E1BDDEA16B50a369862"),
                         ("cl", "0xEfd7A089D3057F05189B05f74Ffcf30610c42891", "0xf437f62053ACB121665b8fDBfeA8F214FB8E589d")],
           "hook": "0xC0ed888AfE87ed1AcF01D9f19bB850159e3ce434"}  # app.aero.xyz/docs/security (CLAIMED), verified on chain below
def addrs(c):
    if c == "elysium": return ELYSIUM
    p = json.load(open(f"{DEP}/pools-{FN[c]}.json"))
    cl = json.load(open(f"{DEPCL}/cl-{FN[c]}.json"))
    g = json.load(open(f"{DEP}/gaugestack-{FN[c]}.json"))
    a = {"poolTape": p["poolTape"], "clPoolTape": cl["clPoolTape"],
         "factories": [("v2s", p["stablePoolFactory"], g["stableGaugeFactory"]),
                       ("v2v", p["volatilePoolFactory"], g["volatileGaugeFactory"]),
                       ("cl", cl["clFactory"], cl["clGaugeFactory"])],
         "hook": cl["dynamicSwapFeeHook"]}
    if c == "arc":
        lite = json.load(open(f"{DEP}/arclitelaunch-arc.json")); cll = json.load(open(f"{DEPCL}/cllitelaunch-arc.json"))
        up = json.load(open(f"{DEPCL}/clliteupgrade-arc.json"))
        a["lite"] = {"poolTape": lite["poolTape"], "clPoolTape": cll["clPoolTape"], "hook": cll["dynamicSwapFeeHook"],
                     "factories": [("lite_v2s", lite["stablePoolFactory"], None), ("lite_v2v", lite["volatilePoolFactory"], None),
                                   ("lite_cl", cll["clFactory"], up["clGaugeFactory"])]}
    return a

def dec_addr(x): return w2a(x[1][2:66]) if x[0] and len(x[1]) >= 66 else None
def dec_uint(x): return int(x[1][2:66], 16) if x[0] and len(x[1]) >= 66 else None

def enumerate_chain(c, block="latest", with_gauges=True):
    a = addrs(c)
    out = {"chain": c, "block": block, "factories": {}, "pools": []}
    facs = list(a["factories"]) + (a["lite"]["factories"] if "lite" in a else [])
    calls = []
    for kind, f, gf in facs:
        calls.append((f, calldata("allPoolsLength()")))
        calls.append((f, calldata("clPoolTape()" if "cl" in kind else "poolTape()")))
        calls.append((f, calldata("defaultSwapHook()" if "cl" in kind else "poolTapeGasLimit()")))
    r = multicall(c, block, calls)
    for i, (kind, f, gf) in enumerate(facs):
        n = dec_uint(r[3 * i]); tape = dec_addr(r[3 * i + 1]); extra = r[3 * i + 2]
        out["factories"][kind] = {"factory": f, "gaugeFactory": gf, "allPoolsLength": n, "tape": tape,
                                  ("defaultSwapHook" if "cl" in kind else "poolTapeGasLimit"):
                                      (dec_addr(extra) if "cl" in kind else dec_uint(extra))}
    # enumerate pools
    calls, meta = [], []
    for kind, f, gf in facs:
        n = out["factories"][kind]["allPoolsLength"] or 0
        for i in range(n):
            calls.append((f, calldata("allPools(uint256)", enc_uint(i)))); meta.append(kind)
    r = multicall(c, block, calls)
    pools = [{"pool": dec_addr(x), "kind": k} for x, k in zip(r, meta)]
    # tokens + cl hook + gauge address
    calls = []
    fmap = {k: (f, gf) for k, f, gf in facs}
    for p in pools:
        calls += [(p["pool"], calldata("token0()")), (p["pool"], calldata("token1()"))]
        if "cl" in p["kind"]:
            calls.append((fmap[p["kind"]][0], calldata("getPoolSwapHook(address)", pad(p["pool"]))))
            calls.append((p["pool"], calldata("tickSpacing()")))
        else:
            calls.append((p["pool"], calldata("stable()")))
            calls.append((p["pool"], calldata("poolFees()")))
        gf = fmap[p["kind"]][1]
        calls.append((gf, calldata("computeGaugeAddress(address)", pad(p["pool"]))) if gf else (p["pool"], calldata("token0()")))
    r = multicall(c, block, calls)
    for i, p in enumerate(pools):
        x = r[5 * i: 5 * i + 5]
        p["token0"], p["token1"] = dec_addr(x[0]), dec_addr(x[1])
        if "cl" in p["kind"]: p["hook"] = dec_addr(x[2]); p["tickSpacing"] = (w2i(x[3][1][2:66], True) if x[3][0] else None)
        else: p["stable"] = dec_uint(x[2]); p["poolFees"] = dec_addr(x[3])
        p["gaugeCandidate"] = dec_addr(x[4]) if fmap[p["kind"]][1] else None
    if with_gauges:
        calls = []
        for p in pools:
            gf = fmap[p["kind"]][1]; g = p["gaugeCandidate"]
            if not g: g = "0x" + "0" * 40; gf = p["pool"]
            calls += [(gf, calldata("isGauge(address)", pad(g))), (gf, calldata("emissionCap(address)", pad(g))),
                      (LEAFVOTER, calldata("isActivated(address)", pad(g))), (g, calldata("votingRewardsManager()"))]
        r = multicall(c, block, calls)
        for i, p in enumerate(pools):
            x = r[4 * i: 4 * i + 4]
            isg = dec_uint(x[0]) == 1 if p["gaugeCandidate"] else False
            p["gauge"] = p["gaugeCandidate"] if isg else None
            if isg:
                p["emissionCap"] = dec_uint(x[1]); p["activated"] = dec_uint(x[2]) == 1; p["vrm"] = dec_addr(x[3])
    out["pools"] = pools
    return out
