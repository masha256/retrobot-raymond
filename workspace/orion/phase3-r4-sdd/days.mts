import { loadAsset } from '../src/config/load.js';
import { getAdapter } from '../src/ingest/adapters/registry.js';
import { chainRpcFor } from '../src/ingest/transport/chainRpcEnv.js';
import { createViemRpc } from '../src/ingest/transport/viemRpc.js';
const M = { gross:['flow_usd.pool_fees_gross','pool.tape_fees_daily'], allocator:['flow_usd.voter_fees','pool.tape_fees_daily'], vote:['flow_usd.vote_incentives','pool.vrm_incentives_daily'], subsidy:['flow_usd.protocol_subsidy','pool.vrm_incentives_daily'] } as const;
for (const day of process.argv.slice(2)) {
  const asset: any = structuredClone(loadAsset(process.cwd(), 'aero').config);
  for (const [k] of Object.values(M)) asset.metrics[k].source.params.since = day;
  const next = new Date(Date.parse(day+'T00:00:00Z')+86400e3+12*3600e3).toISOString();
  const u = (w: string) => () => { throw new Error('unused '+w); };
  const ctx: any = { asset, nowIso: next, http:{getJson:u('http'),postJson:u('http')}, rpc:null, block:null, env:process.env, contract:u('contract'), rpcFor: chainRpcFor(process.env, createViemRpc), storedFlowDays: async()=>new Set<string>() };
  const t0 = Date.now(); const out: any = {};
  for (const [name,[metric,adapter]] of Object.entries(M)) {
    const v: any = await getAdapter(adapter).run(ctx, asset.metrics[metric].source.params);
    if (!v.ok && v.ok !== undefined) { out[name] = { error: v }; continue; }
    const s = v.value ?? v; out[name] = { total: s.points?.map((p:any)=>[p.day,+p.value.toFixed(2)]), chains: s.points?.[0]?.slice?.chains, warnings: (s.warnings??[]).map((w:any)=>w.dedupeKey) };
  }
  console.log(JSON.stringify({ day, secs: (Date.now()-t0)/1000, ...out }));
}
