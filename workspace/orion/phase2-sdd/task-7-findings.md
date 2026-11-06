# Task 7 review: 4a6540e..e801bf3 (spec + quality)

### Spec Compliance

- ✅ Spec compliant. Every file the brief lists has its hunk: 0005, prices.ts, coingeckoHourly.ts, tokenBackfill.ts, data.ts (both commands, every option), flow.ts, apiFlow.ts, lit.ts, hype.ts, solana.ts, and the four test files (all 8 named tests are present).
  - Deviation, justified: the writer upserts only the **hourly** points it loaded, not the daily ones (flow.ts `hourlyPriceRows(s.hourly)`, diff 1342). A daily point is not an hour's price (correction 13), so this is correct.
  - Review Focus 3 says "refuses ... when the day has no active row". The brief's test name says "skips ... and says so", and the code skips and lists the day (tokenBackfill.ts diff 1819). This follows the brief.
  - The 6 h staleness bound (0005 diff 504) and the `coingecko:<id>` refs are the implementer's choices, and the controller accepted them (progress.md Task 7). R18 is not re-reported.
- ⚠️ Cannot verify from the diff:
  - That every Lighter exchangeMetrics kind except `buyback` really is in dollars (lit.ts diff 836).
  - The real backfill/compare figures and the cross-release proof. Both belong to the controller (Step 4/5).
  - Whether the daemon's nightly `refresh` job takes the same `withRunLock` that `data backfill-tokens` takes. If it does not, the stale-snapshot case in M7 can happen in production. It stays safe either way because of the `AND amount IS NULL AND active` guard.

### Named-risk checks (what I checked)

1. **Value equality.**
   - I compared the old inline loop (diff 1405-1464) line by line against `openDayScanner.scanDay` (diff 1212-1284). They match: the same filters in the same order (zero, from_ignore, dust, clone, from_any, unlisted); the same `amount = sharePrice ? tokens×pps : tokens`, then `×priceAt(...)`; the same `values` accumulation order per member; and the same throw text when a price is missing.
   - The token bookkeeping is added before the `×price` step and does not alias `amount` (it uses `let` and is read before the multiply).
   - `series` is always a Map in the writer, so `values` is never null there. Day-block caching keeps `!dryRun` semantics (`cacheDayBlocks: !dryRun`). Unlisted transfers flow through `onUnlisted` exactly as `result.unlisted.push` did.
   - The flow.test.ts fixtures did not change. flow.tokens.test pins the hand-computed USD and the 1e-12 hourly sum.
2. **Backfill safety.**
   - `fillObservationTokens` (observations.ts diff 410-418) sets only token_ref, amount and hourly_amounts, `WHERE id AND amount IS NULL AND active`. It is called inside `db.tx(..., {lockAsset})`, one day per transaction, and every call is awaited on `t`.
   - There is no `insertObservation` import in tokenBackfill.ts.
   - The twin check (diff 1829-1837) compares against stored `flow_tokens` values at 1e-9 relative and refuses the whole day.
   - A dry run takes the early return in `backfillPrices`, skips upsertToken, and sets `cacheDayBlocks:false`.
   - Idempotence is guaranteed by the `amount IS NULL` guard and tested (second run fills 0, snapshot equal).
3. **Prices table and view.**
   - PK (token_ref, ts, source) with ON CONFLICT DO UPDATE. Hours are floored and the earlier point in an hour is kept.
   - Source priority comes before recency, as the brief asks.
   - The 6 h bound and the five `usd_basis` labels are tested.
   - `grep flow_usd_v src/`: only prices.ts `compareUsd` reads the view. No report code does.
4. **Prod traffic.**
   - The writer's step 3 makes the same calls as before: `readDecimals` is the old multicall, and `loadPrices` is unchanged. The new work is DB upserts only (diff 1337-1345). The test asserts one market_chart call.
   - The backfill goes through `deps.http` (the spaced transport) and fetches one id at a time.
5. **Migration and importer.**
   - 0005 only creates tables, adds nullable columns (FKs on all-null columns) and creates the view. It has no `-- breaking` marker.
   - migrate.test inserts a named-column N−1-style row on 0005.
   - The importer's carry test excludes the 3 columns, tokens, prices and the view.
   - Staging refresh restores tokens and prices as prod data. They are not in ENV_LOCAL_TABLES, and the comment and test agree.
   - Opening a newer schema with an older release is covered by the "ahead" test.

### Strengths

- The scanner extraction is a clean, faithful move: one shared `openDayScanner`, so the writer and the backfill cannot count different transfers.
- The backfill test checks the whole row: every column except the 3 token ones, before and after, plus a second run. That is a real proof that values do not change.
- The view's `usd_basis` makes every fallback visible. Leaving zero-amount hours out of `hours_needed` is a careful touch.
- `fetchHourlyRange` stops at the first failing window and reports it, newest first. That is exactly correction 13's "key reach".

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)

**I1. `flow_usd_v` hour buckets depend on the session TimeZone** (`src/db/pg/migrations/0005_tokens_prices.sql`, diff 499: `o.observed_at - make_interval(days => 1) + make_interval(hours => ...)`).
- Problem: `timestamptz − 1 day` is calendar arithmetic in the session's TimeZone. Verified on orion_test:
  - With `SET timezone='America/Los_Angeles'`, `'2026-11-02T00:00Z'::timestamptz - make_interval(days=>1)` gives `2026-10-31 23:00Z`.
  - `- make_interval(hours=>24)` gives `2026-11-01 00:00Z`.
- Impact: the pool pins `TimeZone=UTC` (pool.ts:308), so Orion's own reads are right today. But any other session, such as a psql G2 spot-check, an analyst's client or a dump restored elsewhere, gets every bucket of a DST-change day priced one hour off. That is silently different `usd` / `usd_basis` (hours can tip into `legacy_unpriced` at the 6 h edge).
- A view whose answer depends on the client's settings is fragile. 0005 becomes append-only once a staging release applies it, so this is the cheap moment to fix it.
- Fix: `o.observed_at - interval '24 hours' + (e.i - 1) * interval '1 hour'`. Add a test that runs the view under `SET LOCAL timezone='America/Los_Angeles'` for a DST day (2026-11-01).

#### Minor (Nice to Have)

**M1. `flow_usd_v` also lists `flow_tokens.*` rows** (0005 diff 509: the only filter is `period_days IS NOT NULL`).
- For those rows `legacy_usd` = `value` is a token count. `usd` is then either tokens × price (basis `hourly`) or, when unpriced, the token count labelled as USD.
- compareUsd filters by `unit: usd`, so nothing is wrong today, but Task 8 must remember to filter too.
- Fix: limit the view to `metric_key LIKE 'flow_usd.%'`, or rename/document the columns, before 0005 is staged.

**M2. The backfill makes extra keyless CoinGecko and RPC calls** (tokenBackfill.ts diff 1802-1805, 1812-1814).
- Price fetches are deduplicated by `tokenRef`, not by `coingeckoId`. On yCRV, crvusd's full range is fetched twice: once for `eip155:1/<crvusd>` and once for `coingecko:crvusd` (separate groups).
- The range is re-fetched on every re-run, even when every row is already filled.
- `scanner.dayStart` binary-searches block boundaries for every day in the range, including days with nothing to fill and days before the history starts. The report says "no log request", which is true, but block searches still run when day_blocks is cold, and a dry run never caches them.
- Fix: fetch each coingeckoId once and upsert under every ref that shares it, and skip the fetch when no row is pending.

**M3. Members with no `flow_tokens` twin are filled unverified** (tokenBackfill.ts `twinsOf`, diff 1731-1734). That covers most metrics: the CRV family, AERO, cvxCRV and the yCRV share members.
- If the allowlist or from_ignore changed after a row was written, current-config tokens get attached to an old-config `value`.
- compare-usd's per-day p90 is the only net.
- Fix: where the row has 0004 `tx_count`/`tx_digest`, compare them to the re-scan (`txRefsProvenance(scan.refs)`) and refuse on a mismatch. Otherwise count "unverified" rows in the result.

**M4. `data backfill-tokens` exits 0 when days were refused** (data.ts diff 217-227). The Step 5 stop rule ("any refusal") depends on parsing the JSON. A non-zero exit, or a `refused` line on stderr, would make scripted runs fail closed.

**M5. Days where legacy is 0 but hourly is not 0 drop out of the p50/p90** (prices.ts `gapStats`, diff 667). That hides exactly the discrepancy class a gate should show. Count them, or treat them as 100%.

**M6. Test gaps.**
- No test for the edge-hour clamp and its note.
- No test that a dry-run backfill writes no `day_blocks`.
- No test that a failure part-way through a backfill leaves whole days (e.g. throw from the RPC on day 2 and assert day 1 is filled and day 2 is untouched).
- The report admits that the RED for flow.tokens and prices came from HEAD's src, not test-first.

**M7. The backfill's stored-row snapshot is read before the per-day lock** (tokenBackfill.ts diff 1771-1772, 1851). A row superseded mid-run makes `fillObservationTokens` return false, and it is counted as `alreadyFilled`. That is safe but misleading. Count it as "superseded during the run" instead.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** Value equality and backfill safety hold: the scanner move is faithful, and the UPDATE is narrow, guarded and bounded. The view's DST/session-TimeZone dependence (I1) is a real correctness fragility in a migration that is about to become append-only, and it should be fixed (with M1) before 0005 reaches staging.

## Controller rulings on Task 7 findings (binding)
- I1 FIX: flow_usd_v (and any other SQL in this task) must be timezone-independent: use `interval '24 hours'` / explicit `AT TIME ZONE 'UTC'` instead of make_interval(days=>1); add a test that runs the view under `SET TIME ZONE 'America/Los_Angeles'` on a DST-change day (2026-11-01) and asserts the same hour starts and USD as under UTC. 0005 is unreleased, so edit it in place (R-c8: append-only only from the first staging release that applied it).
- Minors: FIX the view listing flow_tokens rows (restrict flow_usd_v to USD flow rows; legacy_usd must be dollars), FIX duplicate CoinGecko fetches (one market_chart range per coingecko id per backfill run, reused across members; no re-fetch of hours already in `prices` for that source), FIX CLI exit status (non-zero when any day was refused), FIX percentiles (legacy-0 days counted, gap defined for them), FIX test gaps (edge-hour clamp; crash mid-run leaves whole batches), FIX a row superseded mid-run (re-check the active id inside the tx; count it as skipped-superseded, not filled). ACCEPT members with no flow_tokens twin filled unverified (note in followups).
- Also in this fix round, R18: backfill-tokens fills USD-native first-party rows written before 0005 (Lighter fees, Hyperliquid fills/payments) with token_ref 'usd', amount = value, hourly_amounts null, same bounded/idempotent rules.
