import sys, json, os, time, traceback
R4 = "/home/hermes/.hermes/profiles/raymond/cache/scratch/r4"
for f in ("lib", "poolenum", "measure"): exec(open(f"{R4}/{f}.py").read())
OUT = "/home/hermes/.hermes/profiles/raymond/workspace/orion/phase3-r4-scoping/onchain-revenue-data/raw"
os.makedirs(OUT, exist_ok=True)
E = json.load(open(R4 + "/enum_head.json")); BLKS = json.load(open(R4 + "/blocks.json"))
days = sys.argv[1].split(","); chains = sys.argv[2].split(",") if len(sys.argv) > 2 else CHAINS
for d in days:
    for c in chains:
        fn = f"{OUT}/{d}_{c}.json"
        if os.path.exists(fn): print("skip", fn, flush=True); continue
        try:
            m = measure(c, d, E, BLKS)
            m["errors_sample"] = ERRS[-5:]
            json.dump(m, open(fn, "w"))
            print(d, c, m["cost"], m["seconds"], "logs", m["n_fees_collected_logs"], flush=True)
        except Exception as ex:
            print("FAIL", d, c, mask(traceback.format_exc())[-800:], flush=True)
print("DONE", flush=True)
