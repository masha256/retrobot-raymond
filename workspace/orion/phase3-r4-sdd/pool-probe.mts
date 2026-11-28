import { loadAsset } from '../src/config/load.js';
import { scanChainDay } from '../src/ingest/poolscan/scan.js';
import { priceDay } from '../src/ingest/poolscan/pricing.js';
import { rpcChainReader } from '../src/ingest/poolscan/reader.js';
import { chainRpcFor } from '../src/ingest/transport/chainRpcEnv.js';
import { createViemRpc } from '../src/ingest/transport/viemRpc.js';
const asset: any = loadAsset(process.cwd(), 'aero').config;
const scan = asset.metrics['flow_usd.pool_fees_gross'].source.params.scan;
const rpcFor = chainRpcFor(process.env, createViemRpc);
const chainId = Number(process.argv[2]); const day = process.argv[3];
const cfg = scan.chains.find((c: any) => c.chain_id === chainId);
const readers = new Map<number, any>(); for (const c of scan.chains) readers.set(c.chain_id, rpcChainReader(rpcFor(c.chain_id), c.chain_id));
const s: any = await scanChainDay(readers.get(chainId), cfg, day);
const book: any = await priceDay(readers, cfg, s);
const px = (t: string) => book.usd.get(t.toLowerCase()); const dec = (t: string) => book.decimals?.get(t.toLowerCase());
const usd = (t: string, a: bigint) => { const p = px(t), d = dec(t); return p == null || d == null ? NaN : Number(a) / 10 ** d * p; };
const rows: any[] = [];
for (const p of s.pools) {
  const g = usd(p.token0, p.fee0) + usd(p.token1, p.fee1);
  const al = s.allocatorByPool.get(p.pool) ?? s.allocatorByPool.get(p.pool.toLowerCase());
  let a = 0; if (al) for (const [t, v] of al) a += usd(t, v);
  if (a > 0 || g > 0) rows.push({ pool: p.pool, reg: p.registered, newInDay: p.newInDay, gauge: p.gauge, g: +g.toFixed(2), a: +a.toFixed(2), d: +(a - g).toFixed(2), f0: String(p.fee0), f1: String(p.fee1), al: al ? Object.fromEntries([...al].map(([k, v]) => [k, String(v)])) : null });
}
rows.sort((x, y) => y.d - x.d);
console.log(JSON.stringify({ blocks: { s: String(s.blocks.s), e: String(s.blocks.e) }, counts: s.counts, drift: s.drift, top: rows.slice(0, 8) }, null, 1));
