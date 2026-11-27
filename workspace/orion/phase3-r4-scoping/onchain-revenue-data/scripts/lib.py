"""R4 scoping helpers: multi-chain batched JSON-RPC + Multicall3. Never prints the key."""
import json, time, urllib.request, urllib.error, re, threading
from collections import Counter

_env = dict(l.split("=", 1) for l in open("/home/hermes/git/orion/.env").read().splitlines()
            if l and not l.startswith("#") and "=" in l)
_base = _env["ORION_BASE_RPC_URL"].strip().strip('"').strip("'")
_key = _base.rsplit("/", 1)[1]
SUB = {"base": "base-mainnet", "ethereum": "eth-mainnet", "optimism": "opt-mainnet", "arbitrum": "arb-mainnet",
       "ink": "ink-mainnet", "robinhood": "robinhood-mainnet", "arc": "arc-mainnet", "elysium": "elysium-mainnet"}
CHAINS = list(SUB)
def url(c): return f"https://{SUB[c]}.g.alchemy.com/v2/{_key}"
def mask(s): return str(s).replace(_key, "***")

STATS = Counter()   # (chain, kind) -> count
ERRS = []
MC3 = "0xcA11bde05977b3631167028862bE2a173976CA11"

def _post(c, payload, timeout=120):
    data = json.dumps(payload).encode()
    for attempt in range(6):
        try:
            req = urllib.request.Request(url(c), data=data, headers={"Content-Type": "application/json"})
            r = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
            return r
        except urllib.error.HTTPError as e:
            body = e.read()[:300]
            ERRS.append((c, e.code, mask(body)))
            if e.code == 429: time.sleep(3 * (attempt + 1)); continue
            if e.code >= 500: time.sleep(2 * (attempt + 1)); continue
            raise RuntimeError(mask(f"{c} HTTP {e.code} {body}"))
        except Exception as e:
            ERRS.append((c, "exc", mask(repr(e))[:200]))
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{c} rpc failed")

def rpc(c, method, params):
    STATS[(c, "http")] += 1; STATS[(c, method)] += 1
    r = _post(c, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    if "error" in r: raise RuntimeError(mask(f"{c} {method} {r['error']}"))
    return r["result"]

def batch(c, calls, chunk=100):
    """calls = [(method, params)] -> list of results (None + error recorded on error)."""
    out = []
    for i in range(0, len(calls), chunk):
        part = calls[i:i + chunk]
        STATS[(c, "http")] += 1
        for m, _ in part: STATS[(c, m)] += 1
        for attempt in range(5):
            r = _post(c, [{"jsonrpc": "2.0", "id": j, "method": m, "params": p} for j, (m, p) in enumerate(part)])
            if isinstance(r, dict):  # whole-batch error
                ERRS.append((c, "batch", mask(r)[:200])); time.sleep(3 * (attempt + 1)); continue
            byid = {x["id"]: x for x in r}
            bad = [j for j in range(len(part)) if "result" not in byid.get(j, {}) and
                   "429" in json.dumps(byid.get(j, {}).get("error", ""))]
            if bad and attempt < 4: time.sleep(3 * (attempt + 1)); continue
            for j in range(len(part)):
                x = byid.get(j, {})
                if "result" in x: out.append(x["result"])
                else: out.append(None); ERRS.append((c, part[j][0], mask(x.get("error"))[:200]))
            break
    return out

# ---------- ABI helpers ----------
_RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000, 0x000000000000808B,
       0x0000000080000001, 0x8000000080008081, 0x8000000000008009, 0x000000000000008A, 0x0000000000000088,
       0x0000000080008009, 0x000000008000000A, 0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
       0x8000000000008003, 0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
       0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
_ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
_M = (1 << 64) - 1
def _rol(x, n): return ((x << n) | (x >> (64 - n))) & _M if n else x
def _f(A):
    for rc in _RC:
        C = [A[x][0] ^ A[x][1] ^ A[x][2] ^ A[x][3] ^ A[x][4] for x in range(5)]
        D = [C[(x - 1) % 5] ^ _rol(C[(x + 1) % 5], 1) for x in range(5)]
        A = [[A[x][y] ^ D[x] for y in range(5)] for x in range(5)]
        B = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                B[y][(2 * x + 3 * y) % 5] = _rol(A[x][y], _ROT[x][y])
        A = [[B[x][y] ^ ((~B[(x + 1) % 5][y]) & B[(x + 2) % 5][y]) for y in range(5)] for x in range(5)]
        A[0][0] ^= rc
    return A
def keccak256(data: bytes) -> bytes:
    rate = 136
    p = bytearray(data) + b"\x01"
    while len(p) % rate: p += b"\x00"
    p[-1] |= 0x80
    A = [[0] * 5 for _ in range(5)]
    for off in range(0, len(p), rate):
        blk = p[off:off + rate]
        for i in range(rate // 8):
            x, y = i % 5, i // 5
            A[x][y] ^= int.from_bytes(blk[8 * i:8 * i + 8], "little")
        A = _f(A)
    out = b""
    for i in range(4):
        out += A[i % 5][i // 5].to_bytes(8, "little")
    return out
_sel = {}
def sel(sig):
    if sig not in _sel: _sel[sig] = keccak256(sig.encode()).hex()[:8]
    return _sel[sig]
def topic(sig): return "0x" + keccak256(sig.encode()).hex()
def pad(a): return a.lower().replace("0x", "").rjust(64, "0")
def enc_uint(n): return hex(n)[2:].rjust(64, "0")
def words(h):
    h = h[2:] if h.startswith("0x") else h
    return [h[i:i + 64] for i in range(0, len(h), 64)]
def w2i(w, signed=False):
    v = int(w, 16)
    if signed and v >= 2 ** 255: v -= 2 ** 256
    return v
def w2a(w): return "0x" + w[-40:]
def calldata(sig, *args):
    return "0x" + sel(sig) + "".join(args)

def multicall(c, block, calls, chunk=250, gas=None):
    """calls = [(target, calldata_hex)] -> list of (ok, returndata_hex). Uses aggregate3 with allowFailure."""
    res = []
    blk = block if isinstance(block, str) else hex(block)
    reqs = []
    chunks = [calls[i:i + chunk] for i in range(0, len(calls), chunk)]
    for part in chunks:
        # encode aggregate3((address,bool,bytes)[])
        n = len(part)
        head = enc_uint(32) + enc_uint(n)
        offs, tails, cur = [], [], 32 * n
        for t, d in part:
            d = d[2:]
            dl = len(d) // 2
            body = pad(t) + enc_uint(1) + enc_uint(96) + enc_uint(dl) + d.ljust(((dl + 31) // 32) * 64, "0")
            offs.append(enc_uint(cur)); tails.append(body); cur += len(body) // 2
        data = "0x" + sel("aggregate3((address,bool,bytes)[])") + head + "".join(offs) + "".join(tails)
        p = {"to": MC3, "data": data}
        if gas: p["gas"] = hex(gas)
        reqs.append(("eth_call", [p, blk]))
    outs = batch(c, reqs, chunk=10)
    for part, o in zip(chunks, outs):
        STATS[(c, "inner_calls")] += len(part)
        if o is None:
            # fallback: split in half recursively via direct calls
            if len(part) > 1:
                res += multicall(c, block, part, chunk=max(1, len(part) // 4), gas=gas); continue
            res.append((False, "")); continue
        h = o[2:]
        n = int(h[64:128], 16)
        base = 128
        for i in range(n):
            off = int(h[base + i * 64: base + i * 64 + 64], 16) * 2 + 128
            ok = int(h[off: off + 64], 16) == 1
            boff = int(h[off + 64: off + 128], 16) * 2 + off
            bl = int(h[boff: boff + 64], 16)
            res.append((ok, "0x" + h[boff + 64: boff + 64 + bl * 2]))
    return res

def blk_ts(c, n):
    b = rpc(c, "eth_getBlockByNumber", [hex(n), False]); return int(b["timestamp"], 16)

def block_at(c, ts, cache={}):
    """First block with timestamp >= ts (the day-boundary block)."""
    key = (c, ts)
    if key in cache: return cache[key]
    hi = int(rpc(c, "eth_blockNumber", []), 16); hts = blk_ts(c, hi)
    if hts < ts: raise RuntimeError("future")
    lo = max(0, hi - int((hts - ts) / 0.1) - 10)  # assume >=0.1s/block lower bound guess
    lts = blk_ts(c, lo)
    while lts >= ts:
        lo = max(0, lo - (hi - lo)); lts = blk_ts(c, lo)
    # interpolation + bisection
    while hi - lo > 1:
        if hts > lts:
            g = lo + int((ts - lts) * (hi - lo) / (hts - lts))
            g = min(max(g, lo + 1), hi - 1)
        else:
            g = (lo + hi) // 2
        gts = blk_ts(c, g)
        if gts >= ts: hi, hts = g, gts
        else: lo, lts = g, gts
        if hi - lo > 1:
            m = (lo + hi) // 2; mts = blk_ts(c, m)
            if mts >= ts: hi, hts = m, mts
            else: lo, lts = m, mts
    cache[key] = hi
    return hi
