"""Per (chain, day) measurement. exec after lib.py + enum.py; needs E (head enumeration) and BLKS."""
import json, time, datetime
FEES_COLLECTED = topic("FeesCollected(address,address,uint256)")

WIN = {}
CAP = {}
import re as _re
def getlogs(c, addresses, topics, fb, tb, depth=0):
    """Adaptive eth_getLogs over [fb, tb]; window shrinks on provider range/size errors."""
    out = []
    cur = fb
    win = WIN.get(c, tb - fb + 1)
    while cur <= tb:
        end = min(tb, cur + win - 1)
        params = {"fromBlock": hex(cur), "toBlock": hex(end), "topics": topics}
        if addresses: params["address"] = addresses
        try:
            out += rpc(c, "eth_getLogs", [params])
            cur = end + 1
            if c in CAP: win = min(CAP[c], win * 2)
            else: win = win * 2
        except RuntimeError as e:
            msg = str(e)
            STATS[(c, "getLogs_err")] += 1
            mm = _re.search(r"up to a (\d+) block range", msg)
            if mm: CAP[c] = int(mm.group(1)); win = CAP[c]
            mm = _re.search(r"should work: \[0x([0-9a-f]+), 0x([0-9a-f]+)\]", msg)
            if mm:
                win = max(1, int(mm.group(2), 16) - int(mm.group(1), 16) + 1)
            elif not _re.search(r"up to a (\d+) block range", msg):
                if win == 1: raise
                win = max(1, win // 2)
        WIN[c] = win
    return out

def decode_v2_acc(h):
    w = words(h)
    if len(w) < 10: return None
    return {"fee0": int(w[0], 16), "fee1": int(w[1], 16), "vol0": int(w[2], 16), "vol1": int(w[3], 16),
            "mevFee0": int(w[6], 16), "mevFee1": int(w[7], 16), "last": int(w[8], 16), "swaps": int(w[9], 16)}

def decode_cl_acc(h):
    w = words(h)
    if len(w) < 20: return None
    return {"fee0": int(w[11], 16), "fee1": int(w[12], 16), "vol0": int(w[8], 16), "vol1": int(w[9], 16),
            "mevFee0": int(w[18], 16), "mevFee1": int(w[19], 16), "last": int(w[0], 16), "swaps": int(w[2], 16)}

def measure(c, day, E, BLKS, with_logs=True):
    t = int(datetime.datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc).timestamp())
    s, e = BLKS[c][str(t)], BLKS[c][str(t + 86400)]
    a = addrs(c)
    st0 = dict(STATS); t0 = time.time()
    facs = list(a["factories"]) + (a["lite"]["factories"] if "lite" in a else [])
    calls = [(f, calldata("allPoolsLength()")) for _, f, _ in facs]
    ns = [dec_uint(x) or 0 for x in multicall(c, s, calls)]
    ne = [dec_uint(x) or 0 for x in multicall(c, e, calls)]
    nstart = {k: n for (k, _, _), n in zip(facs, ns)}; nend = {k: n for (k, _, _), n in zip(facs, ne)}
    # pools existing at e (by factory index order)
    byk = {}
    for p in E[c]["pools"]: byk.setdefault(p["kind"], []).append(p)
    pools = []
    for k, _, _ in facs:
        for i, p in enumerate(byk.get(k, [])[:nend[k]]):
            q = dict(p); q["new_in_day"] = i >= nstart[k]; pools.append(q)
    def tape_of(p):
        src = a["lite"] if p["kind"].startswith("lite") else a
        return src["clPoolTape" if "cl" in p["kind"] else "poolTape"]
    tc = [(tape_of(p), calldata("accumulators(address)", pad(p["pool"]))) for p in pools]
    rs, re_ = multicall(c, s, tc, chunk=200), multicall(c, e, tc, chunk=200)
    for p, x0, x1 in zip(pools, rs, re_):
        dec = decode_cl_acc if "cl" in p["kind"] else decode_v2_acc
        A0 = dec(x0[1]) if x0[0] else None; A1 = dec(x1[1]) if x1[0] else None
        p["acc_s"], p["acc_e"] = A0, A1
        if A1:
            z = A0 or {k: 0 for k in A1}
            # sentinel 1-wei init: treat pre-first-swap (last==0) start as zero
            if A0 and A0["last"] == 0: z = {k: 0 for k in A1}
            p["d"] = {k: A1[k] - z[k] for k in ("fee0", "fee1", "vol0", "vol1", "mevFee0", "mevFee1", "swaps")}
            if A1["last"] == 0: p["d"] = {k: 0 for k in p["d"]}
    # gauge raw pending + VRM state at s and e
    gp = [p for p in pools if p.get("gauge")]
    def gcalls(p):
        g, v = p["gauge"], p["vrm"]
        pend = (p["pool"], calldata("gaugeFees()")) if "cl" in p["kind"] else (p["pool"], calldata("pendingFees(address)", pad(g)))
        return [pend, (g, calldata("pendingFees()")), (v, calldata("feeRewardPerVotingPower()")), (v, calldata("totalSupply()")),
                (v, calldata("lastPendingFees0()")), (v, calldata("lastPendingFees1()")), (v, calldata("bufferedFees0()")),
                (v, calldata("bufferedFees1()"))]
    K = 8
    allc = [x for p in gp for x in gcalls(p)]
    for tag, blk in (("s", s), ("e", e)):
        r = multicall(c, blk, allc, chunk=240)
        for i, p in enumerate(gp):
            x = r[K * i: K * i + K]
            def two(y): 
                if not y[0] or len(y[1]) < 130: return None
                return [int(y[1][2:66], 16), int(y[1][66:130], 16)]
            p["g_" + tag] = {"raw": two(x[0]), "gated": two(x[1]),
                             "acc": two(x[2]), "supply": dec_uint(x[3]),
                             "lastPend": [dec_uint(x[4]), dec_uint(x[5])], "buf": [dec_uint(x[6]), dec_uint(x[7])]}
    # FeesCollected logs over VRM list
    logs = []
    if with_logs and gp:
        vrms = sorted({p["vrm"] for p in gp if p.get("vrm")})
        for i in range(0, len(vrms), 500):
            logs += getlogs(c, vrms[i:i + 500], [FEES_COLLECTED], s, e - 1)
    coll = {}
    for L in logs:
        key = (L["address"].lower(), "0x" + L["topics"][2][-40:])
        coll[key] = coll.get(key, 0) + int(L["data"][2:66], 16)
    for p in gp:
        v = (p.get("vrm") or "").lower()
        p["collected"] = [coll.get((v, p["token0"]), 0), coll.get((v, p["token1"]), 0)]
    # pricing state at e: V2 reserves, CL slot0/liquidity + TWAP ticks + token balances
    pc = []
    for p in pools:
        if "cl" in p["kind"]:
            pc += [(p["pool"], calldata("slot0()")), (p["pool"], calldata("liquidity()")),
                   (p["pool"], calldata("observe(uint32[])", enc_uint(32), enc_uint(2), enc_uint(1800), enc_uint(0)))]
        else:
            pc += [(p["pool"], calldata("getReserves()")), (p["pool"], calldata("totalSupply()")), (p["pool"], calldata("token0()"))]
        pc += [(p["token0"], calldata("balanceOf(address)", pad(p["pool"]))), (p["token1"], calldata("balanceOf(address)", pad(p["pool"])))]
    r = multicall(c, e, pc, chunk=250)
    for i, p in enumerate(pools):
        x = r[5 * i: 5 * i + 5]
        if "cl" in p["kind"]:
            p["sqrtP"] = int(x[0][1][2:66], 16) if x[0][0] and len(x[0][1]) >= 66 else None
            p["tick"] = w2i(x[0][1][66:130], True) if x[0][0] and len(x[0][1]) >= 130 else None
            p["L"] = dec_uint(x[1])
            if x[2][0] and len(x[2][1]) > 2 + 64 * 4:
                w = words(x[2][1])
                # (int56[] tickCumulatives, uint160[] spl): offsets, then arrays
                o1 = int(w[0], 16) // 32
                tc0, tc1 = w2i(w[o1 + 1], True), w2i(w[o1 + 2], True)
                p["twap_tick_1800"] = (tc1 - tc0) / 1800
            else:
                p["twap_tick_1800"] = None
        else:
            p["reserves"] = [int(x[0][1][2:66], 16), int(x[0][1][66:130], 16)] if x[0][0] and len(x[0][1]) >= 130 else None
        p["bal"] = [dec_uint(x[3]), dec_uint(x[4])]
    st1 = dict(STATS)
    cost = {k[1]: st1.get(k, 0) - st0.get(k, 0) for k in st1 if k[0] == c and st1.get(k, 0) - st0.get(k, 0)}
    return {"chain": c, "day": day, "block_start": s, "block_end": e, "nstart": nstart, "nend": nend,
            "pools": pools, "n_fees_collected_logs": len(logs), "cost": cost, "seconds": round(time.time() - t0, 1)}
