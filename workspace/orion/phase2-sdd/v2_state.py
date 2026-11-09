"""Read-only: per env, v2 report state that shows whether the Phase 2 backfills ran."""
import json, subprocess
for env in ('stage', 'prod'):
    ssh = ['ssh', '-i', f'/home/hermes/.ssh/orion-{env}_ed25519', '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
           '-o', 'ConnectTimeout=15', f'orion-{env}@192.168.0.12']
    for a in ('ycrv', 'crv', 'vvv', 'aero'):
        r = subprocess.run(ssh + ['report', 'yield', a], capture_output=True, text=True, timeout=120)
        try:
            d = json.loads(r.stdout); d = d.get('report', d); i = d.get('incomeStatement') or {}
        except Exception:
            print(env, a, 'ERR', r.stdout[:200], r.stderr[:200]); continue
        rev = i.get('revenue') or {}
        bases = sorted({str(l.get('priceBasis')) for sec in ('revenue', 'holders') for l in (i.get(sec) or {}).get('lines', [])})
        prov = i.get('provenance')
        prov_s = json.dumps(prov)[:160] if prov is not None else None
        checks = [(c.get('id'), c.get('status')) for c in i.get('checks') or []]
        print(f"{env:5} {a:5} day {d.get('day')} rev {rev.get('annualized')} growth {(rev.get('growth') or {}).get('annualized')} "
              f"bases {bases} flags {i.get('flags')} checks {checks}")
        print('       provenance', prov_s)
