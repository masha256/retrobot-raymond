"""Read-only multi-chain RPC helper for the R4 incentive scoping. Never prints the RPC key."""
import json, time, urllib.request, urllib.error, re

ROOT = "/home/hermes/git/orion/"
_env = dict(l.split("=", 1) for l in open(ROOT + ".env").read().splitlines() if l and not l.startswith("#") and "=" in l)
_BASE = _env["ORION_BASE_RPC_URL"].strip().strip('"').strip("'")
_KEY = _BASE.rsplit("/", 1)[1]
SUB = {"base": "base-mainnet", "ethereum": "eth-mainnet", "optimism": "opt-mainnet", "arbitrum": "arb-mainnet",
       "ink": "ink-mainnet", "robinhood": "robinhood-mainnet", "arc": "arc-mainnet"}
CHAINS = list(SUB)
def url(chain): return f"https://{SUB[chain]}.g.alchemy.com/v2/{_KEY}"
STATS = {"http": 0, "calls": 0}

# ---------------- keccak256 (pure python) ----------------
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
def keccak(data: bytes) -> bytes:
    rate = 136
    data = bytearray(data) + b"\x01"
    while len(data) % rate: data += b"\x00"
    data[-1] |= 0x80
    A = [[0] * 5 for _ in range(5)]
    for off in range(0, len(data), rate):
        blk = data[off:off + rate]
        for i in range(rate // 8):
            x, y = i % 5, i // 5
            A[x][y] ^= int.from_bytes(blk[8 * i:8 * i + 8], "little")
        A = _f(A)
    out = b"".join(A[i % 5][i // 5].to_bytes(8, "little") for i in range(4))
    return out
_selc = {}
def sel(sig):
    if sig not in _selc: _selc[sig] = "0x" + keccak(sig.encode()).hex()[:8]
    return _selc[sig]
def topic(sig): return "0x" + keccak(sig.encode()).hex()

# ---------------- RPC ----------------
def _post(chain, payload, timeout=120):
    for attempt in range(6):
        try:
            req = urllib.request.Request(url(chain), data=json.dumps(payload).encode(),
                                         headers={"Content-Type": "application/json"})
            STATS["http"] += 1
            r = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
            if isinstance(r, list):
                if any("error" in x and x["error"].get("code") == 429 for x in r):
                    raise IOError("429 in batch")
            return r
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(3 * (attempt + 1)); continue
            body = e.read()[:200]
            raise RuntimeError(f"HTTP {e.code} on {chain}: {body!r}")
        except Exception as e:
            if attempt == 5: raise RuntimeError(f"rpc failed on {chain}: {type(e).__name__}")
            time.sleep(2 * (attempt + 1))

def rpc(chain, method, params):
    STATS["calls"] += 1
    r = _post(chain, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    if "error" in r: raise RuntimeError(r["error"])
    return r["result"]

def batch(chain, reqs, size=50):
    """reqs: list of (method, params). Returns list of result or None (on error)."""
    out = []
    for i in range(0, len(reqs), size):
        chunk = reqs[i:i + size]
        STATS["calls"] += len(chunk)
        r = _post(chain, [{"jsonrpc": "2.0", "id": j, "method": m, "params": p} for j, (m, p) in enumerate(chunk)])
        d = {x["id"]: x for x in r}
        out += [d[j].get("result") if "error" not in d[j] else None for j in range(len(chunk))]
    return out

def pad(a): return a.lower().replace("0x", "").rjust(64, "0")
def enc_uint(n): return hex(n)[2:].rjust(64, "0")
def calldata(sig, *args):
    s = sel(sig)
    for a in args:
        s += enc_uint(a) if isinstance(a, int) else pad(a)
    return s

MC3 = "0xcA11bde05977b3631167028862bE2a173976CA11"
_has_mc = {}
def has_mc(chain):
    if chain not in _has_mc:
        _has_mc[chain] = rpc(chain, "eth_getCode", [MC3, "latest"]) not in ("0x", None)
    return _has_mc[chain]

def _enc_aggregate3(calls):
    # aggregate3((address target, bool allowFailure, bytes callData)[])
    n = len(calls)
    head = enc_uint(32) + enc_uint(n)
    tails = []; offs = []
    cur = 32 * n
    for tgt, data in calls:
        b = bytes.fromhex(data[2:])
        el = pad(tgt) + enc_uint(1) + enc_uint(96) + enc_uint(len(b)) + b.hex().ljust(((len(b) + 31) // 32) * 64, "0")
        offs.append(enc_uint(cur)); tails.append(el); cur += len(el) // 2
    return sel("aggregate3((address,bool,bytes)[])") + head + "".join(offs) + "".join(tails)

def _dec_aggregate3(h):
    b = bytes.fromhex(h[2:])
    w = lambda o: int.from_bytes(b[o:o + 32], "big")
    base = w(0); n = w(base); res = []
    for i in range(n):
        eo = base + 32 + w(base + 32 + 32 * i)
        ok = w(eo) == 1
        do = eo + w(eo + 32)
        ln = w(do)
        res.append("0x" + b[do + 32:do + 32 + ln].hex() if ok else None)
    return res

def mcall(chain, calls, block="latest", size=400, rpc_batch=10):
    """calls: list of (target, calldata). Returns list of hex return or None. Uses Multicall3 if present."""
    if isinstance(block, int): block = hex(block)
    if not has_mc(chain):
        return batch(chain, [("eth_call", [{"to": t, "data": d}, block]) for t, d in calls])
    reqs = []
    for i in range(0, len(calls), size):
        reqs.append(("eth_call", [{"to": MC3, "data": _enc_aggregate3(calls[i:i + size])}, block]))
    out = []
    raw = batch(chain, reqs, size=rpc_batch)
    for i, r in enumerate(raw):
        if r is None:  # retry smaller
            sub = calls[i * size:(i + 1) * size]
            if size > 25:
                out += mcall(chain, sub, block, size=max(25, size // 4), rpc_batch=rpc_batch)
            else:
                out += batch(chain, [("eth_call", [{"to": t, "data": d}, block]) for t, d in sub])
        else:
            out += _dec_aggregate3(r)
    return out

def words(h):
    if not h or h == "0x": return []
    b = h[2:]; return [b[i:i + 64] for i in range(0, len(b), 64)]
def addr(wd): return "0x" + wd[-40:]
def u(wd): return int(wd, 16)
def s(wd):
    v = int(wd, 16); return v - (1 << 256) if v >> 255 else v
def dec_addr_array(h):
    w = words(h)
    if not w: return []
    n = u(w[1]); return [addr(x) for x in w[2:2 + n]]
def dec_string(h):
    try:
        w = words(h)
        if len(w) >= 3 and u(w[0]) == 32:
            ln = u(w[1]); return bytes.fromhex("".join(w[2:])[:2 * ln]).decode(errors="replace")
        return bytes.fromhex(h[2:]).rstrip(b"\x00").decode(errors="replace")
    except Exception:
        return None

def block_at(chain, ts, cache={}):
    """first block with timestamp >= ts (binary search)."""
    key = (chain, ts)
    if key in cache: return cache[key]
    hi = int(rpc(chain, "eth_blockNumber", []), 16)
    def bts(n): return int(rpc(chain, "eth_getBlockByNumber", [hex(n), False])["timestamp"], 16)
    lo = 1
    if bts(hi) < ts: cache[key] = None; return None
    while lo < hi:
        mid = (lo + hi) // 2
        if bts(mid) < ts: lo = mid + 1
        else: hi = mid
    cache[key] = lo
    return lo
