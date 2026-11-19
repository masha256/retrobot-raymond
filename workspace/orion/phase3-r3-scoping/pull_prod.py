#!/usr/bin/env python3
"""R3 scoping: read-only prod pull (sql-ro + report yield) and one keyless CoinGecko /coins/markets call (dev-only reference).
Writes into ./prod/ next to this file. Refuses to run 05:00-06:30 PT."""
import datetime, json, os, subprocess, sys, urllib.request, zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'prod'); os.makedirs(OUT, exist_ok=True)
now_pt = datetime.datetime.now(zoneinfo.ZoneInfo('America/Los_Angeles'))
if datetime.time(5, 0) <= now_pt.time() < datetime.time(6, 30):
    sys.exit(f'refused: {now_pt:%H:%M} PT is inside 05:00-06:30')
KEY = os.path.expanduser('~/.ssh/orion-prod_ed25519')
SSH = ['ssh', '-i', KEY, '-o', 'IdentitiesOnly=yes', 'orion-prod@192.168.0.12']
ASSETS = 'aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv'.split()

def sqlro(q):
    r = subprocess.run(SSH + ['sql-ro', "'" + q + "'"], capture_output=True, text=True, timeout=120)
    if r.returncode != 0: raise SystemExit(f'sql-ro failed rc={r.returncode}: {r.stderr[:400]}')
    return r.stdout

def save(name, text):
    with open(os.path.join(OUT, name), 'w') as f: f.write(text)

Q = {
 'circ_obs_summary': "select asset_id, source_type, status, (superseded_by is null) as active, count(*) n, min(observed_at) first, max(observed_at) last from orion.observations where metric_key = $$circulating_supply$$ group by 1,2,3,4 order by 1,2,3,4",
 'circ_latest': "select distinct on (asset_id) asset_id, observed_at, value, source_type, locator::text loc from orion.observations where metric_key = $$circulating_supply$$ and superseded_by is null and status <> $$rejected$$ order by asset_id, observed_at desc",
 'supply_latest': "select distinct on (asset_id, metric_key) asset_id, metric_key, observed_at, value, source_type from orion.observations where metric_key in ($$total_supply$$,$$staked_supply$$) and superseded_by is null and status <> $$rejected$$ order by asset_id, metric_key, observed_at desc",
 'market_data_all': "select metric_key, status, (superseded_by is null) active, count(*) from orion.observations where source_type = $$market_data$$ group by 1,2,3 order by 1,2,3",
 'latest_levels_circ': "select * from orion.latest_levels where metric_key = $$circulating_supply$$ order by asset_id",
 'circ_daily_90d': "select asset_id, observed_at::date d, max(value) v from orion.observations where metric_key = $$circulating_supply$$ and superseded_by is null and status <> $$rejected$$ and observed_at > now() - interval $$100 days$$ group by 1,2 order by 1,2",
 'circ_anomalies': "select asset_id, kind, status, count(*), max(last_seen_at) from orion.anomalies where metric_key = $$circulating_supply$$ group by 1,2,3 order by 1,2,3",
 'latest_levels_supply': "select asset_id, metric_key, value, observed_at, source from orion.latest_levels where metric_key in ($$total_supply$$,$$staked_supply$$,$$price_usd$$) order by 1,2",
 'migrations': "select max(id) from orion.schema_migrations",
}
for k, q in Q.items():
    try: save(f'{k}.txt', sqlro(q)); print('ok', k)
    except SystemExit as e: print('FAIL', k, e)

for a in ASSETS:
    r = subprocess.run(SSH + ['report', 'yield', a, '--json'], capture_output=True, text=True, timeout=180)
    save(f'report-{a}.json', r.stdout)
    print('report', a, r.returncode, len(r.stdout))

ids = 'pancakeswap-token,curve-dao-token,hyperliquid,chainlink,lighter,pump-fun,sky,uniswap,venice-token,aero,convex-crv,stake-dao-crv,yearn-crv'
req = urllib.request.Request(f'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={ids}', headers={'User-Agent': 'orion-scoping'})
with urllib.request.urlopen(req, timeout=30) as resp:
    rows = json.load(resp)
keep = [{k: r.get(k) for k in ('id', 'symbol', 'current_price', 'market_cap', 'circulating_supply', 'total_supply', 'max_supply', 'last_updated')} for r in rows]
save('coingecko-markets-devonly.json', json.dumps({'fetched_at': datetime.datetime.utcnow().isoformat() + 'Z', 'label': 'dev-only reference', 'rows': keep}, indent=1))
print('coingecko rows', len(keep))
