# Task 3 report: hour blocks and the resumable chain price writer

Status: DONE. Commit `a4d49c7 feat(prices): hour-block cache and a resumable chain price writer` (on 1d8e9bd).

## What
- `src/db/pg/migrations/0008_chain_prices.sql` (expand-only, no `-- breaking`): `CREATE TABLE hour_blocks (chain_id bigint, hour timestamptz, block bigint NOT NULL, block_ts bigint NOT NULL, PRIMARY KEY (chain_id, hour))`, and `ALTER TABLE prices ADD COLUMN check_gap_pct double precision, ADD COLUMN "check" text COLLATE "C", ADD COLUMN detail jsonb`, with a header comment. Task 5 appends the view.
- `src/db/hourBlocks.ts`: `dbHourBlocks(db, chainId): { get(hourMs), put(hourMs, b) }`. The first write wins (as day_blocks). An hour that is not on the hour is refused with `invalid_hour`.
- `src/db/prices.ts`: `PriceRow` gains optional `checkGapPct`, `check` and `detail`. `upsertPrices` writes them through one `jsonb_to_recordset` parameter; a conflict also updates them. CoinGecko callers are unchanged and store null. A non-finite gap is refused.
- `src/prices/types.ts`: `PriceDeps.prices` (prices.yaml) added, so the writer can resolve refs and quote refs. `WriteResult.errors` added (`{chain, hourMs, error}`).
- `src/ingest/transport/chains.ts`: the switch comment now says block 53,556,128 (2026-11-05T18:00:01Z).
- `src/prices/writer.ts`:
  - **Registry (R4).** `PRICE_CHAIN_METHODS: Record<chain, PriceChainMethod>` with `(deps, entries, hour: {hourMs, blocks|null}, ctx: {feedUsd, checks, feeds, cache}) => Promise<{prices, missing, feedUsd?, checks?, calls?}>`. This returns a result object rather than R4's bare `Map`, so a method can report why a ref is missing. eip155:1/56/8453 wrap `priceHourEvm`. A ref on a chain with no registered method is refused with `no_price_method`.
  - **Walk.** Days run newest first. Within each day, chains run in this order: eip155:1, the other EVM chains, then the off-chain venues. Each chain walks the day's hours newest first and commits one chain-day per transaction (rows, tokens rows and the hour blocks found). Budget and abort are checked after each chain-day that did work.
  - **Skip rule.** An hour is skipped when it is already stored for the ref under `methodSource(entry.primary)`; a CoinGecko row does not count. Hours before `valid_from` are out of scope. Quote refs are read but written only if they were asked for.
  - **R5.** Chain 1 also reads the `usd_feed` of every off-chain entry in the run. It also reads LIT's v4 check: an off-chain primary's EVM check is read on its ref's chain. Its `feedUsd` and `checks` go to the off-chain method of the same hour. A chain-1 hour that failed (no block yet, a transport error, or the entry's feed missing from `feedUsd`) gives the off-chain ref `quote_missing`, and the method is not called. An off-chain hour that is not yet closed (`H+1h > now`) gives `no_block_yet`.
  - **Carry.** One `BlockReadCache` per chain is kept for the whole run and pruned after each hour to that hour's B(H). A TWAP chain therefore costs N+1 multicalls for N hours.
  - **Hour blocks.** Each block is looked up first in the in-run map, then in `hour_blocks`, and only then searched. The search starts from the neighbouring hour's block, at the rate the previous two hours' blocks show. The upper bracket is B(H+1h), or the head when that is unknown. A block is cached only when it is at least 1 h below the head (`HOUR_BLOCK_MIN_AGE_SEC`, the same rule as day_blocks), because a younger block could still be reorged away.
  - `findHourBlock` probes the estimate and the block before it, then re-estimates once from the probe's own spacing. That spacing is the one-block step when it is ≥2 s; when blocks share integer seconds it is the spacing back to the anchor. If both guesses miss, it hands over to `firstBlockAtOrAfter` (rpc.ts:111, unchanged). Without this step, the scoping's 21 probes per hour before the switch came back (proven by mutation, below).
  - **Breach rule.** Over the stored non-null gaps within ±(48 + consecutive) h of the rows just written (an absent or null hour neither breaches nor resets), a run of `consecutive` breaching hours (|gap| > tolerance, or for `bound` any gap ≠ 0) that includes a new row is reported once, at the hour that completes it. Runs can span writer runs.
  - **Errors.** A transport error on a chain records `errors` and `read_failed` for that hour's refs. It also stops that chain for the rest of the run, and `reachedMs` stops advancing. An `OrionError` (config) is rethrown.
  - **`calls`** counts every multicall, getBlock and latestBlock per EVM chain, plus an off-chain method's reported `calls`.
  - `makePriceDeps(env, { rpcFactory, prices, solana?, http?, now? })` makes one transport per chain on first use: ORION_ETH_RPC_URL, ORION_BNB_RPC_URL, ORION_BASE_RPC_URL (Base falls back to `CHAINS[8453].defaultRpcUrl`). A chain without a URL, or a non-EVM chain, gets `no_rpc_url`, and the URL is never put in the message. Missing Solana/HTTP slots reject with `no_price_transport` when used.

## Tests (TDD)
- RED (`npx vitest run tests/prices/writer.test.ts tests/db/hourBlocks.test.ts tests/db/pg/migrate.test.ts --maxWorkers=1`, with hourBlocks.ts moved aside because I had written it before running): "Cannot find module '../../src/db/hourBlocks.js'" for the writer and hourBlocks files. In migrate.test.ts, 3 failed ("expected undefined to match object { id: 8, name: 'chain_prices' }", codeRequires 7 vs 8). Test Files 3 failed, Tests 3 failed | 9 passed.
- GREEN: the 3 files pass 35/35, as follows.
  - `tests/prices/writer.test.ts`:
    - Base closed form: B(18:00Z) = 53,556,127, B(19:00Z) = 53,574,123.
    - `findHourBlock` walking back from 21:00Z to 16:00Z gets each first block exactly, with ≤4 getBlock calls per hour (2, 2, 4, 4, 2).
    - The halt case is found exactly.
    - The writer over 16:00..20:00Z, with B(21:00) seeded in hour_blocks, gives exact `detail.block`/`start_block`, ≤20 getBlock, exactly 6 multicalls for 5 hours, and all 6 hour blocks cached.
    - With the head at 20:30Z: `no_block_yet` for 20:00Z, and 20:00's block is not cached.
    - Idempotence: the second run gives written 0, skippedExisting 5, and no multicall or getBlock. A CoinGecko row at the hour is kept and is not the chain source.
    - Budget 0: stoppedByBudget, exactly one chain-day (2026-11-05, 24 rows, 25 multicalls), reachedMs 11-05T00:00. The re-run writes 11-04.
    - Aborted signal; `valid_from`.
    - cvxCRV 3.4% then 3.5% gives one breach at the second hour; 3.4% then 0.1% gives none; 3.4%, then skipped, then 3.5% gives one breach at the third hour; a run that spans two writer runs gives one breach.
    - sdCRV bound gives one breach at +20%, and the stored gaps are 20/30/0.
    - HYPE through a fake hyperliquid entry gets the chain-1 USDC feed of the same hour; a failed feed read gives `quote_missing`.
    - When the chain-1 head is behind, or chain 1 throws: `quote_missing`, the method is not called, and the error is recorded.
    - LIT through a fake lighter entry gets chain 1's v4 check, and the gap is stored.
    - Refusals: `unknown_price_ref`, `no_price_method`, `invalid_price_range`.
    - `makePriceDeps`.
  - `tests/db/hourBlocks.test.ts`: first write wins, per chain and hour; `invalid_hour`.
  - `tests/db/pg/migrate.test.ts`: counts moved to 8. The new 0008 test is on a populated schema 7: column types and nullability, the PK, the `"check"` collation C, the old row kept with null columns. orion-2026.11.12.1's statements still run on schema 8: its upsertPrices INSERT, storedPriceHours, listPrices verbatim from 8f50ac6, and `flow_usd_v`.
- Mutation checks, each of which fails the named tests:
  - A fresh cache per hour fails the N+1 and budget tests.
  - With no guess step (straight to `firstBlockAtOrAfter`), the ≤4 tests fail.
  - A null gap that resets the run fails the skipped-check test.
  - Caching every block fails the head test.
  - Ignoring the source in the skip rule fails the idempotence test.
- Full suite `npx vitest run --maxWorkers=2`: **1808/1809 (149 files)**. The one failure was `tests/release/deploy.test.ts > deploy.sh > deploy: the tarball goes to install on stdin and switch follows only after install exits 0` (7.3 s, load timeout). Rerun alone at `--maxWorkers=1`: 9/9 passed. Real total 1809/1809 = 1785 + 24 new.
- `npm run typecheck` and `npm run lint:promises` are clean. `python3 -m unittest scripts/provision/test/test_orion_remote.py`: 52 OK.

## Files beyond the brief's list (forced by migration 8)
- `tests/cli/db.cli.test.ts`, `tests/db/daemonSchema.test.ts`, `tests/tools/importSqlite.test.ts`: migration counts 7 → 8. The daemonSchema 0007 test now applies `all.slice(0, 7)`. The "schema ahead" fake migration moved to 9.
- `tests/db/pg/baseline.test.ts`: `hour_blocks` added as a non-carried table.
- `tests/daemon/stagingRefresh.test.ts`: the "every table is decided" test forced a choice. I put `hour_blocks` in the **restored-from-prod** list (test-only change), not in ENV_LOCAL_TABLES (which would mean a src change in stagingRefresh.ts). The mismatch texts moved to schema 8.

## Self-review / decisions to check
1. `PriceDeps.prices` was added, because the writer's signature takes refs and not entries. `makePriceDeps` takes `prices` in its factories argument.
2. The registry method returns `{prices, missing, ...}`, not R4's `Map`.
3. Per-run once-per-run breach semantics: with `consecutive` 1, a run of 5 breaching hours is one breach, at its first hour. The second hour of the same run is never reported again unless a backfill joins two runs across a chain-day written later; in that case a second breach for one run is possible. The window is ±(48 + consecutive) h.
4. A chain-day is committed even when a chain fails part-way, so the rows read before the failure are kept. A failed chain is skipped for the rest of the run. When chain 1 fails, every later off-chain hour is listed `quote_missing` (R5), which can be a long list in a big backfill.
5. Hour blocks younger than 1 h below the head are not cached, but the price rows read at those blocks are written and never rewritten (plan P2, as specified).

## Concerns
- stagingRefresh: `hour_blocks` was classed restored-from-prod (test list). Moving it to ENV_LOCAL_TABLES, beside day_blocks, is a one-line src change if preferred.
- `src/ingest/transport/rpc.ts:108` still says "~53,556,072" in its comment. I did not edit it because it is not in the file list.
- A leftover test schema `t_79b19239ec0df6c5` (created 14:47Z, before my first run at 15:29Z) is in orion_test; presumably the parallel reviewer's. I left it alone.


## Fix round 1 (task-3-findings.md items 1-4), on top of 27a6ff1

Env: `export ORION_TEST_DATABASE_URL='postgresql://orion_dev@/orion_test?host=/var/run/postgresql'`. RED command for all three new tests and the changed one:
`npx vitest run tests/prices/writer.test.ts --maxWorkers=1` -> `Tests 4 failed | 20 passed (24)`.

1. **Abort inside a chain-day (Important).** `src/prices/writer.ts`: `aborted()` is checked at the chain loop (as before), at the top
   of every hour, and just before the chain-day's `db.tx`; on abort the in-flight chain-day is not committed (no prices,
   tokens or hour_blocks rows) and the run ends. New `WriteResult.stoppedBySignal` (`src/prices/types.ts`) marks the stop.
   - Test (new): `a signal aborted inside a multicall stops at the next hour: nothing of that chain-day is committed, no
     further read` — a fake Base multicall aborts on the 3rd call (the second hour's read); asserts written 0,
     `stoppedBySignal` true, `reachedMs` null, multicall and getBlock counts unchanged after the abort, 0 `prices` rows,
     0 `hour_blocks` rows. RED: `written ... 24` (expected 0), `stoppedBySignal` absent.
   - The pre-aborted test now also asserts `stoppedBySignal: true` (RED: field absent).
2. **One breach per run across midnight (Minor).** Breaches are no longer evaluated per committed chain-day; the writer
   collects each ref's written hours over the whole run and calls `breachesOf` once per ref after the day loop
   (chronological over the stored rows), also after a budget or signal stop (over what was committed).
   - Test (new): `a run across midnight is one breach: 3.5% at 23:00, 00:00 and 01:00 in one writer run -> one breach, at
     00:00` (cvxCRV, consecutive 2, run 22:00..03:00). RED: breaches at 00:00 and 01:00.
3. **A missing hour resets the run (Minor).** `breachesOf` now reads null-gap rows too: a gap of more than 1 h between
   consecutive rows resets the run; a null-gap row is skipped (neither breaches nor resets, unchanged).
   - Test (new): `an hour with no row resets the run: 3.4% stored at 00:00, no row at 01:00, 3.5% written at 02:00 -> no
     breach`. RED: one breach at 02:00 (gap 3.5). The existing `3.4%, a skipped check (null gap), 3.5%` test still passes.
4. **stagingRefresh doc comment (Minor).** `src/daemon/jobs/stagingRefresh.ts`: under the `day_blocks` bullet, names
   `hour_blocks` as the opposite choice, restored from prod (Ruling R14), and why. Comment only; no test.

GREEN:
- `npx vitest run tests/prices tests/daemon/stagingRefresh.test.ts --maxWorkers=1` -> `Test Files 5 passed (5)`, `Tests 90 passed (90)`.
- `npx vitest run --maxWorkers=2` -> `Test Files 150 passed (150)`, `Tests 1830 passed (1830)` (1827 + 3 new); no load-timeout failures.
- `npm run typecheck` -> clean.

Files: `src/prices/writer.ts`, `src/prices/types.ts`, `src/daemon/jobs/stagingRefresh.ts`, `tests/prices/writer.test.ts`.

Notes: the hour blocks found by an aborted chain-day are dropped (re-searched by the next run; a few getBlock). The
deferred minors (failed chain's later `missing`, the fallback bracket, function size) are untouched.
