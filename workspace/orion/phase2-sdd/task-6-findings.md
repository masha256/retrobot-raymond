# Task 6 review: provenance columns 0004, writers, scrubbed locators, backfill (f5c62a3..b594222)

### Spec Compliance

- ✅ Spec compliant. Every file the brief lists has its hunk: 0004 (15 nullable columns, NULL-tolerant CHECKs, `latest_levels.source_type`/`locator`, `idx_obs_method`), `src/provenance/{types,locator,scrub,backfill}.ts` (`scrub.ts` is extra: it was split out to break the import cycle the report describes, and that split is justified), `db backfill-provenance [--dry-run] [--json]`, `NewObservation.provenance` required, every writer, `latestLevels`/`levels`, `incomeStatement` provenance from the rows (`basis: 'observations'`). `tools/import-sqlite/importer.ts` did not need a change: it inserts named columns (importer.ts:216-220).
- The only CLI behaviour change is `data set` now refusing a call without `--citation` (data.ts:69, README updated). It follows the spec (no method other than `disclosed` fits a typed-in figure, and spec §3 requires a citation when the method is disclosed). Mike signs off on it (concern 1). It is not a finding.
- `tx_count` is bigint, not the spec's integer: correct under baseline 7.1. `tx_refs` keeps the first 50 sorted refs where the spec text says "null when more": this follows the brief's ruling ("capped at 50"), and the digest covers the full list.
- ⚠️ Cannot verify from the diff: **the `basis: 'observations'` path has never run on live data.** The controller's parity/reclass PASS ran on a copy at 0004 with no backfill applied, so every asset was on `basis: 'config'`. After a real `db backfill-provenance`, `provenance.methods`, `provenance.sources` and `revenue.lines[].daysMeasured` (incomeStatement.ts:438, :466) switch to the row-based path, and `daysMeasured` changes meaning (concern 5). Controller: run the real backfill on the proof copy, then re-run the cross-release proof. Legacy bytes and the parity map figures must not move. Record the v2 provenance fields that do move.
- ⚠️ The brief lists `tests/tools/proof.test.ts`, which the diff does not touch. That is acceptable: the test builds its schema with `createTestSchema` and so runs at 0004, `proof.ts:40` hashes `SELECT <carried names>`, and importSqlite.test.ts now pins `schemaVersion: 4` and the 15 uncarried columns.
- ⚠️ The implementer's full-suite run had 1 failure (`tests/tools/disclosureWatcher.test.ts`, clock-dependent, inherited from f5f36fa, fixed upstream in 48dcf2d). It is not caused by this diff, but the suite output is not clean.

### Strengths

- Mandatory provenance is enforced by the type: there is a single `INSERT INTO observations` in src (observations.ts:219), `tsc --noEmit` includes `tests`, so the `@ts-expect-error` case in provenance.writers.test.ts:4368 really compiles, and the `LatestLevel` fields are non-optional, so every `upsertLatestLevels` caller has to supply them.
- Values are untouched. Legacy columns go into the same statement unchanged. The skip-if-same-value paths (apiFlow `have === value`, periodic `stored.get(...) === p.value`, derived `have.get(observedAt) === point.value`) never look at provenance, so a re-fetch neither duplicates rows nor skips an update because of provenance. `Observation`/CLI JSON shapes are unchanged (asserted in cli.test.ts:3067 and observations.test.ts:3558). The backfill test asserts every legacy column is byte-equal before and after (backfill.test.ts:4965).
- Locators are scrubbed in depth: in the builders, again in `checkedProvenance` (observations.ts:138), and in `upsertLatestLevels`. The alch_SECRET fixture is read from rpc.test.ts. I probed shapes the tests don't cover: Solana Alchemy `/v2/<k>`, Helius `?api-key=`, QuickNode `/<token>/`, `wss://…alchemy…/v2/<k>` and BNB public dataseed. All came out clean.
- `writtenSource` for derived rows mirrors run.ts:496-500 exactly, and `sourceTypeOf` is shared with the report, so the backfill and the report cannot drift.
- The release-N-1 insert test uses the old statement verbatim and also checks that the CHECKs still refuse an invalid value.

### Named-risk checks

1. **Secrets.** Checked: no locator builder takes an env value or an RPC URL. `chainOfSource` emits only CAIP-2, the coingecko locator has no headers, and adapter params in the 13 YAMLs hold only public URLs (lighter, venice, defillama-datasets). The http_json URLs in assets/ carry no key. `CHAINS.defaultRpcUrl` values are keyless and never enter a locator. The backfill takes its `api` locator from `source_detail` through `scrubUrl` (backfill.ts:134). The CLI backfill output prints ids, metric keys, source and reason only. `responseDigest` hashes `source_detail` and never stores it. **No key reaches any of the new columns, the snapshot body or the CLI output.** `source_detail` is written exactly as before (outside this diff; viemRpc.ts:13 already keeps keyed URLs out of details).
2. **Values unchanged.** See Strengths. No report figure reads the new columns. Only the v2 `provenance` block and `daysMeasured` do, on basis observations, which the brief mandates (see ⚠️).
3. **Mandatory provenance.** All paths pass one: flow, apiFlow, periodic, run (schedule, level, derived; constants via level), data set/confirm, proposals (insert + confirm), ledger, latest_levels. The importer intentionally leaves the columns null.
4. **N-1 / importer / staging.** The N-1 insert works on 0004 (observations.test.ts:3578). The proof hashes carried columns by name. The stagingRefresh mismatch test now pins `prod 1, staging 4` and `prod 5, staging 4`, which matches Review Focus 5.
5. **Backfill.** The dry run returns before any write (backfill.ts:160). Unmapped rows are listed with a reason and never written. The re-run is idempotent: `WHERE method IS NULL`, and the test re-runs it. The rules match correction 1, and I judged the extra rules: `onchain`-now-API → `source_changed` is right (the row can't be mapped, so it is listed); `block N` → from = to = N is right; leaving `tx_count` unset is right (no per-member count in history). Live check (read-only sqlite): every `api` row whose `source_detail` names llama.fi/llama.box sits on a metric whose current source is DefiLlama, llama.box http_json or `lit.unlocks_next_year` (all third_party), so no live row is mislabelled. Bounded transactions: see Important 1.

### Issues

#### Critical (Must Fix)

None.

#### Important (Should Fix)

1. **src/provenance/backfill.ts:158-172: the backfill's transaction is not bounded, and building its row lists is quadratic.** Each asset's rows are updated in **one** transaction, one `UPDATE` round trip per row, while the asset's advisory lock is held. Live today that is up to 4,005 rows (sdcrv). At the 10x the brief names, ~40k sequential UPDATEs sit in one tx, and every fetch, refresh and confirm of that asset waits for the whole run. `perAsset.set(id, [...old, x])` also copies the array on every row: O(n²) per asset (~8×10⁸ element copies at 40k). The brief's risk 5 asks for bounded transactions.
   - Fix: `push` into the list. Write in chunks of ≤1,000 ids per tx with one set-based statement (`UPDATE observations o SET … FROM unnest($1::bigint[], $2::text[], …) AS m(id, …) WHERE o.id = m.id AND o.method IS NULL`). Each chunk is still idempotent through `method IS NULL`.
   - Add a test that the per-tx row count is capped (e.g. 2,500 seeded rows with a cap of 1,000 → 3 txs).

#### Minor (Nice to Have)

1. **src/provenance/scrub.ts:9, :65: the object-key scrub drops harmless fields.** Probed: HYPE `flow_usd.reserve_yield`'s locator loses `params.token: "USDC"`. Any locator key that ends in key/token/secret goes the same way: today only adapter params, and a contract named `token` would go too if it were ever a sender or subtract key. `KEY_LIKE_SEGMENT` (:16) also drops any 20+ character path segment with a digit, such as a contract address (`https://api.example.com/v1/token/0x0d01…` → `/v1/token`). This is not a leak, but the locator stops saying where the value came from. Fix: apply the key-name rule to URL query keys and to top-level credential fields only, not to `params`/`senders` maps, or exempt `0x[0-9a-f]{40}` and base58 addresses.
2. **src/ingest/apiFlow.ts:186, src/ingest/run.ts:174: `response_digest` hashes Orion's own parsed output, not the response slice.** It covers `{metric, day, value}` (plus `detail` for levels), which is a hash of the stored value itself. That proves nothing about the response the spec's "sha256 of the normalized response slice used" refers to. Either thread the raw point through the adapters (`DailyPoint`) or document the column as a value digest.
3. **src/provenance/backfill.ts:98: `blocksOf` matches only `^block N$`.** RPC-adapter levels write `block N: <detail>` (adapters/chain.ts:30, crv.ts:67), so their history gets no `block_from/to`. Use `/^block (\d+)(?::|$)/`.
4. **src/provenance/backfill.ts:133: an `api` row whose metric now writes `onchain` is labelled by the current source only.** It becomes `first_party_api` even when its `source_detail` URL is api.llama.fi. That follows correction 1's literal text, and no live row is affected today (checked). Labelling by the URL host would be a mechanical rule, not a guess (`THIRD_PARTY_HOST` → `third_party`). Bring it to Mike as a rule refinement.
5. **src/levels/levels.ts:86-88: the inserted `levelProvenance` sits between `toLatestLevels`'s doc comment ("One row per metric read…") and the function, so that comment now documents the wrong function.** Move it.
6. **src/db/latestLevels.ts:46: after a rollback, N-1's upsert leaves stale provenance.** The previous release's `ON CONFLICT DO UPDATE` does not set `source_type`/`locator`, so a row can carry provenance from the newer release next to a value from the older one. The window is small (the hourly levels file in the snapshot), but the cross-release note should mention it.
7. **src/cli/commands/data.ts:97: `data confirm` (and a `confirm_observation` approval) now has to load the asset's YAML for `configHash`.** Confirming a row of an asset whose YAML is gone or invalid used to work and now throws. Fall back to the stored `config_hash`, or `pre-v2`, when the load fails.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The secrets, values-unchanged, mandatory-provenance and N-1/importer risks all hold, with tests and a live probe behind them. The backfill's per-asset, row-at-a-time transaction (plus quadratic list building) does not meet the "bounded transactions at 10x" requirement. The row-based v2 provenance path still needs a proof run after a real backfill.

## Controller rulings on Task 6 findings (binding)
- I1 FIX: the backfill runs in bounded transactions (at most 1,000 rows per tx, each under the asset lock, resumable: a re-run skips rows already set) and builds its row lists in linear time; a test with a large synthetic set (e.g. 25k rows) asserts the batch count and that a crash mid-way leaves only whole batches.
- M1 FIX: drop secrets by context, not by key suffix: (a) URL query parameters named key, apikey, api_key, token, access_token, secret (case-insensitive) and keyed RPC path segments; (b) object keys named authorization, password, secret, api_key, apikey, and any key inside a `headers`/`auth` object. A plain `token` field holding a symbol (HYPE `params.token: "USDC"`) survives. Tests for both.
- M2 FIX: response_digest = sha256 of the normalized raw response slice the value was read from (the JSON sub-tree for that day/metric, canonical key order), not of Orion's parsed output; where an adapter can't expose it, leave response_digest null and say so in a comment.
- M3 FIX: blocksOf matches `/^block (\d+)(?::|$)/`.
- M4 FIX: a historical `api` row whose source_detail names a DefiLlama host (api.llama.fi, coins.llama.fi, pro-api.llama.fi, yields.llama.fi) is third_party regardless of the metric's current source; test.
- M5 FIX (move the comment).
- M6 deferred (rollback-only staleness of latest_levels provenance; followups note).
- M7 FIX: data confirm / confirm_observation work when the asset YAML is gone/invalid: configHash 'unloaded' in that case (test).
- Concern 1 (data set requires --citation): kept; Mike sign-off at G2 (spec: disclosed needs a citation).
