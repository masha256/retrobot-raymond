def _bts(chain, ns):
    r = batch(chain, [("eth_getBlockByNumber", [hex(n), False]) for n in ns])
    return [int(x["timestamp"], 16) for x in r]

def blocks_at(chain, tss):
    """First block with timestamp >= ts, for each ts. Timestamp search: secant steps on (block, ts) pairs, then an
    exact bracket check (block b has ts >= T and block b-1 has ts < T). No fixed block-time assumption."""
    head = int(rpc(chain, "eth_blockNumber", []), 16)
    lo_b = max(1, head - 50_000_000)
    hts, lts = _bts(chain, [head, lo_b])
    known = {head: hts, lo_b: lts}
    out = {}
    for T in sorted(tss):
        if T > hts: out[T] = None; continue
        # bracket from known points
        for it in range(40):
            below = max((b for b, t in known.items() if t < T), default=None)
            above = min((b for b, t in known.items() if t >= T), default=None)
            if below is not None and above is not None and above == below + 1:
                out[T] = above; break
            if below is None:
                g = max(1, above // 2)
            else:
                tb, ta = known[below], known[above]
                g = below + int((T - tb) * (above - below) / max(1, ta - tb))
                g = min(max(g, below + 1), above - 1)
            # probe a small window around the guess in one batch
            span = max(1, (above - (below or 0)) // 1000)
            probes = sorted({min(max(g + d, (below or 0) + 1), above - 1) for d in (-span, 0, span)})
            probes = [p for p in probes if p not in known]
            if not probes:
                probes = [((below or 0) + above) // 2]
            for p, t in zip(probes, _bts(chain, probes)):
                known[p] = t
        else:
            raise RuntimeError(f"no convergence {chain} {T}")
    return out
