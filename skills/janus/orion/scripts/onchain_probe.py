"""Read-only Ethereum probe helpers for orion spikes (fee routes, revenue splits, reward funding).

Load in execute_code with:
    exec(open('/home/hermes/.hermes/profiles/raymond/skills/janus/orion/scripts/onchain_probe.py').read())
Scratch copies get pruned after 24h idle; load from here instead of rewriting helpers.
Reads ORION_ETH_RPC_URL from orion/.env and never prints it.
"""
import json, time, urllib.request
from collections import defaultdict

root = "/home/hermes/git/orion/"
TMP = "/home/hermes/.hermes/profiles/raymond/cache/scratch"
_env = dict(l.split("=", 1) for l in open(root + ".env").read().splitlines() if l and not l.startswith("#") and "=" in l)
RPC = _env["ORION_ETH_RPC_URL"].strip().strip('"').strip("'")


def get(u):
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read())


def rpc(method, params):
    for attempt in range(5):
        try:
            req = urllib.request.Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
                                         headers={"Content-Type": "application/json"})
            r = json.loads(urllib.request.urlopen(req, timeout=120).read())
            if "error" in r:
                raise RuntimeError(r["error"])
            return r["result"]
        except RuntimeError:
            raise
        except Exception:
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("rpc failed")


_sel = {}
def call(addr, sig, args="", block="latest"):
    """eth_call; selector via web3_sha3 (keccak). args = concatenated 32-byte hex words."""
    if sig not in _sel:
        _sel[sig] = rpc("web3_sha3", ["0x" + sig.encode().hex()])[:10]
    return rpc("eth_call", [{"to": addr, "data": _sel[sig] + args}, block])


def pad(a):
    return a.lower().replace("0x", "").rjust(64, "0")


def u(h, d=18):
    return int(h, 16) / 10 ** d


_head = None
def head():
    global _head
    if _head is None:
        _head = int(rpc("eth_blockNumber", []), 16)
    return _head


def transfers(frm=None, to=None, contracts=None, since_days=91, maxn=100000, cats=("erc20",)):
    """alchemy_getAssetTransfers, paged. Each item has from/to/asset/value/hash/metadata.blockTimestamp."""
    start = head() - int(since_days * 86400 / 12)
    p = {"fromBlock": hex(start), "toBlock": "latest", "category": list(cats), "withMetadata": True,
         "maxCount": "0x3e8", "excludeZeroValue": True}
    if frm: p["fromAddress"] = frm
    if to: p["toAddress"] = to
    if contracts: p["contractAddresses"] = contracts
    out = []
    while True:
        r = rpc("alchemy_getAssetTransfers", [p])
        out += r["transfers"]
        if len(out) >= maxn or not r.get("pageKey"):
            break
        p["pageKey"] = r["pageKey"]
    return out


_names = {}
def name(a):
    """Blockscout label for an address (contract name, token name, 'EOA')."""
    a = a.lower()
    if a in _names: return _names[a]
    if int(a, 16) == 0:
        _names[a] = "ZERO"; return "ZERO"
    try:
        d = get(f"https://eth.blockscout.com/api/v2/addresses/{a}")
        n = d.get("name") or ((d.get("token") or {}).get("name")) or ("contract" if d.get("is_contract") else "EOA")
    except Exception:
        n = "?"
    _names[a] = n
    return n


def io(addr, days=91, toks=None, top=8, show=True):
    """In/out token totals for one address, grouped by (counterparty, asset). Returns {'IN':..., 'OUT':...}."""
    res = {}
    for lbl, dirn in [("IN", "to"), ("OUT", "from")]:
        t = transfers(**({"to": addr} if dirn == "to" else {"frm": addr}), contracts=toks, since_days=days, maxn=200000)
        s = defaultdict(lambda: [0.0, 0])
        for x in t:
            cp = (x["from"] if dirn == "to" else x["to"]).lower()
            s[(cp, x["asset"])][0] += x["value"] or 0
            s[(cp, x["asset"])][1] += 1
        res[lbl] = s
        if show:
            print("  ", lbl, len(t))
            for (cp, a), (v, n) in sorted(s.items(), key=lambda kv: -kv[1][0])[:top]:
                print("     ", cp, name(cp), a, round(v), n)
    return res


CRV = "0xD533a949740bb3306d119CC777fa900bA034cd52"
CVX = "0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B"
CRVUSD = "0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E"
