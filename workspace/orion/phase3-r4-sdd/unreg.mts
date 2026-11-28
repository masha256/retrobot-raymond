import { loadAsset } from '../src/config/load.js';
import { scanChainDay } from '../src/ingest/poolscan/scan.js';
import { priceDay } from '../src/ingest/poolscan/pricing.js';
import { rpcChainReader } from '../src/ingest/poolscan/reader.js';
import { chainRpcFor } from '../src/ingest/transport/chainRpcEnv.js';
import { createViemRpc } from '../src/ingest/transport/viemRpc.js';
const asset: any = loadAsset(process.cwd(), 'aero').config;
const scan = asset.metrics['flow_usd.pool_fees_gross'].source.params.scan;
const rpcFor = chainRpcFor(process.env, createViemRpc);
const chainId = Number(process.argv[2]);
const cfg = scan.chains.find((c: any) => c.chain_id === chainId);
const readers = new Map<number, any>(); for (const c of scan.chains) readers.set(c.chain_id, rpcChainReader(rpcFor(c.chain_id), c.chain_id));
for (const day of process.argv.slice(3)) {
  const s = await scanChainDay(readers.get(chainId), cfg, day);
  const book: any = await priceDay(readers, cfg, s);
  let unregAlloc = 0, totAlloc = 0;
  const unreg = new Set(s.pools.filter((p: any) => !p.registered).map((p: any) => p.pool.toLowerCase()));
  for (const [pool, amts] of s.allocatorByPool as Map<string, Map<string, bigint>>) {
    let usd = 0; for (const [tok, a] of amts) { const px = book.usd.get(tok.toLowerCase()) ?? book.usd.get(tok); const dec = book.decimals?.get?.(tok.toLowerCase()) ?? book.decimals?.get?.(tok); if (px != null && dec != null) usd += Number(a) / 10 ** dec * px; }
    totAlloc += usd; if (unreg.has(pool.toLowerCase())) unregAlloc += usd;
  }
  console.log(day, chainId, 'unregistered pools', unreg.size, 'allocator usd total', totAlloc.toFixed(0), 'on unregistered pools', unregAlloc.toFixed(0));
}
