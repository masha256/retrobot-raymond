// Read-only live probe of AERO's new adapter metrics through the real transport (no DB). Prints values only.
import { readFileSync } from 'node:fs';
import { loadAsset } from '/home/hermes/git/orion/.worktrees/aero-supply/src/config/load.ts';
import { getAdapter } from '/home/hermes/git/orion/.worktrees/aero-supply/src/ingest/adapters/registry.ts';
import { createViemRpc } from '/home/hermes/git/orion/.worktrees/aero-supply/src/ingest/transport/viemRpc.ts';
import { contractResolver } from '/home/hermes/git/orion/.worktrees/aero-supply/src/ingest/types.ts';

const env = Object.fromEntries(readFileSync('/home/hermes/git/orion/.env', 'utf8').split('\n').filter((l) => l.includes('=') && !l.startsWith('#')).map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1).replace(/^["']|["']$/g, '')]));
const { config } = loadAsset('/home/hermes/git/orion/.worktrees/aero-supply', 'aero');
const rpc = createViemRpc(env.ORION_BASE_RPC_URL!, 8453);
const latest = await rpc.latestBlock();
const block = process.argv[2] ? await rpc.getBlock(BigInt(process.argv[2])) : latest;
const ctx = { asset: config, nowIso: new Date(block.timestamp * 1000).toISOString(), http: null as never, rpc, block, env: {}, contract: contractResolver(config) };
const out: Record<string, unknown> = { block: block.number.toString(), ts: new Date(block.timestamp * 1000).toISOString() };
for (const [k, d] of Object.entries(config.metrics)) {
  const srcs = [d.source, ...(d.cross_checks ?? []).map((c) => c.source)];
  for (const [i, s] of srcs.entries()) {
    if (s?.type !== 'adapter') continue;
    try {
      const v = await getAdapter(s.name).run(ctx as never, s.params);
      out[`${k}${i ? ' (check)' : ''}`] = v.kind === 'level' ? v.value : v.kind;
    } catch (e) {
      out[`${k}${i ? ' (check)' : ''}`] = `ERROR ${(e as Error).message}`;
    }
  }
}
console.log(JSON.stringify(out, null, 1).replace(/\/v2\/[A-Za-z0-9_-]+/g, '/v2/***'));
