// Phase 3 R2 proof (controller): write chain/first-party prices into a prod-copy schema with the branch's writer.
// Copy into the root of the proof checkout (imports ./src), then:
//   npx tsx r2-prices.ts <home with .env: ORION_DATABASE_URL, ORION_DB_SCHEMA + the 4 RPC keys> <from YYYY-MM-DD> <to YYYY-MM-DD> [refs,comma]
// Prints one JSON line per chunk (calls, written, missing by reason, breaches, errors) and a final summary. Read-only on chain.
import { readFileSync } from 'node:fs';
import { openDb, databaseConfig } from './src/db/connection.js';
import { loadPrices } from './src/prices/config.js';
import { makePriceDeps, writeChainPrices } from './src/prices/writer.js';
import { realFetchDeps } from './src/ingest/deps.js';

const [home, from, to, refsArg] = process.argv.slice(2);
const env: Record<string, string> = {};
for (const l of readFileSync(`${home}/.env`, 'utf8').split('\n')) { const i = l.indexOf('='); if (i > 0) env[l.slice(0, i)] = l.slice(i + 1); }
const db = await openDb(databaseConfig(env), { max: 2 });
const prices = loadPrices(process.cwd());
const refs = refsArg ? refsArg.split(',') : [...prices.keys()];
const H = 3_600_000;
const fromMs = Date.parse(`${from}T00:00:00Z`);
const lastHour = Math.floor(Date.now() / H) * H - H; // last completed hour start
const toMs = Math.min(Date.parse(`${to}T00:00:00Z`) + 24 * H, lastHour);
const total = { calls: {} as Record<string, number>, written: {} as Record<string, number>, missing: {} as Record<string, number>, breaches: 0, errors: [] as string[], runs: 0 };
const t0 = Date.now();
for (;;) {
  const f = realFetchDeps(env, () => new Date());
  const deps = makePriceDeps(f.env, { rpcFactory: f.rpcFactory, prices, http: f.http, now: new Date() });
  const r = await writeChainPrices(db, deps, refs, fromMs, toMs, { budgetMs: 10 * 60_000 });
  total.runs++;
  for (const [k, n] of Object.entries(r.calls ?? {})) total.calls[k] = (total.calls[k] ?? 0) + (n as number);
  for (const [k, n] of Object.entries(r.written ?? {})) total.written[k] = (total.written[k] ?? 0) + (n as number);
  for (const m of r.missing ?? []) { const k = `${m.ref}|${m.reason}`; total.missing[k] = (total.missing[k] ?? 0) + 1; }
  total.breaches += (r.breaches ?? []).length;
  for (const e of r.errors ?? []) total.errors.push(`${e.chain} ${new Date(e.hourMs).toISOString()} ${String(e.error).split('\n')[0].replace(/\/v[23]\/[A-Za-z0-9_-]+/g, '/v2/***').slice(0, 300)}`);
  console.log(JSON.stringify({ run: total.runs, elapsedS: Math.round((Date.now() - t0) / 1000), stoppedByBudget: r.stoppedByBudget, reachedMs: r.reachedMs, calls: r.calls, errors: (r.errors ?? []).length }));
  if (!r.stoppedByBudget) break;
  if (process.env.STOP_AT && Date.now() > Date.parse(process.env.STOP_AT)) { console.log(JSON.stringify({ stoppedAt: new Date().toISOString(), reason: 'STOP_AT' })); break; }
}
// missing is from the last run only per the writer's design; keep the last run's view
console.log(JSON.stringify({ summary: true, elapsedS: Math.round((Date.now() - t0) / 1000), ...total }));
await db.close();
