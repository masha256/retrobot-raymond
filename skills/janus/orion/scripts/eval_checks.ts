// Read-only evaluation of an asset set's reconciliation checks over a window on a proof schema. Never records.
// Copy into the root of a checkout at the commit under test (it imports ./src), then:
//   npx tsx eval_checks.ts <home with .env naming ORION_DATABASE_URL + ORION_DB_SCHEMA> <lastDay YYYY-MM-DD> <days> > out.json
// Output: { <asset>: { "<checkId>:<type>": { ok, breach, incomplete, maxGap, breaches[<=6], lastIncompleteMissing } } }
import { readFileSync } from 'node:fs';
import { openDb, databaseConfig } from './src/db/connection.js';
import { listAssetIds, loadAsset } from './src/config/load.js';
import { evaluateChecks } from './src/checks/evaluate.js';
import { resolveChecks } from './src/checks/schema.js';

const [home, lastDay, daysS] = process.argv.slice(2);
const env: Record<string, string> = {};
for (const l of readFileSync(`${home}/.env`, 'utf8').split('\n')) { const i = l.indexOf('='); if (i > 0) env[l.slice(0, i)] = l.slice(i + 1); }
const db = await openDb(databaseConfig(env), { max: 1 });
const out: Record<string, unknown> = {};
const days = Number(daysS);
const end = new Date(lastDay + 'T00:00:00Z');
for (const id of listAssetIds(home)) {
  const asset = loadAsset(home, id).config;
  if (resolveChecks(asset).length === 0) continue;
  const per: Record<string, { ok: number; breach: number; incomplete: number; breaches: unknown[]; maxGap: number | null; lastIncompleteMissing?: unknown }> = {};
  for (let k = days - 1; k >= 0; k--) {
    const d = new Date(end.getTime() - k * 86400000).toISOString().slice(0, 10);
    const res = await evaluateChecks(db, asset, d, { now: new Date() });
    for (const r of res as any[]) {
      const key = `${r.checkId ?? r.check_id ?? r.id}:${r.type}`;
      const p = (per[key] ??= { ok: 0, breach: 0, incomplete: 0, breaches: [], maxGap: null });
      p[r.status as 'ok' | 'breach' | 'incomplete']++;
      const g = r.gapPct ?? r.gap_pct;
      if (typeof g === 'number') p.maxGap = Math.max(p.maxGap ?? 0, g);
      if (r.status === 'breach' && p.breaches.length < 6) p.breaches.push({ day: d, lhs: r.lhs, rhs: r.rhs, gap: g });
      if (r.status === 'incomplete') p.lastIncompleteMissing = { day: d, missing: r.missing ?? r.detail?.missing };
    }
  }
  out[id] = per;
}
console.log(JSON.stringify(out, null, 1));
await (db as any).close();
