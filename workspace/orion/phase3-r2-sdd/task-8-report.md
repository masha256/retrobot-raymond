# Task 8 report: `data reprice`, `data rebuild-price-levels`, `data purge-prices`

Status: DONE. Commit 13ece08 `feat(data): reprice stored flows, rebuild price levels, purge CoinGecko prices` (base 6c0b54e).

## What

- `src/db/reprice.ts` `repriceAsset(db, loaded, { from?, yes, now, exportDir, release?, syncDir? })`, following Ruling R26.
  - Scope: active `flow_usd.*` rows with a period, day >= `--from`.
  - Classification, checked in this order:
    - skipped `usd_native` (token `usd`), `third_party`, `disclosed`, `derived`, `periodic` (period != 1);
    - (a) `log_scan`: hourly when the row has `hourly_amounts`, refused `no token amounts` when it has none;
    - (b) `locator.adapter = solana.supply_burn_daily`: priced on the daily mean. A row without an amount takes the
      active `flow_tokens.<same name>` twin at the same `observed_at`, with the twin's ref or else the mint's
      `solana:mainnet/<mint>` ref. With no twin it is refused (`no amount and no flow_tokens.X twin row`);
    - anything else: skipped `not_coingecko_priced:<rung>`.
  - Pricing matches flow_usd_chain_v:
    - hourly: for each hour with an amount, the newest chain/first-party row at or before the hour, at most 6 h old. Ties
      go to the newest `fetched_at`, then the source (R6), through `chainHourPrices`. Any unpriced hour refuses the row
      with `<p> of <n> hours with an amount priced` (Review Focus 5: `23 of 24 ...`);
    - daily_mean: all 24 hours at exactly those timestamps, else `<n> of 24 hours priced (daily mean)`.
  - P4 remap covers every row of the asset (any metric or status) under `coingecko:crvusd` or `coingecko:yearn-crv`.
    The dry run prices from the mapped ref. `--yes` adds the address tokens row if it is missing (yCRV: symbol yCRV,
    decimals 18; crvUSD likewise, `ON CONFLICT DO NOTHING`), then remaps before the value writes in the same day
    transaction.
  - Derived: each `derived` metric whose inputs include a repriced `flow_usd` metric. Stored active rows whose window holds
    a changed day are recomputed with `derivedFunction` at their own observed_at, using the summing and `minus` rules of
    run.ts. Rows whose window is no longer complete are counted `incomplete` and left alone.
  - Marker: `locator.repriced = { at, release, basis }`. `basis` is `hourly`, `daily_mean`, or `derived` for derived rows.
    The release is `ctx.release.tag`, else `codeVersion()`.
  - `--yes` flow:
    - take the asset run lock and build the plan;
    - export every touched row with `to_jsonb` (plus `derived` old/new values) to `<exportDir>/<asset>-<UTCstamp>.json`,
      fsynced like purge;
    - apply one transaction per asset-day, oldest first. Each UPDATE is guarded by the old `value` and `token_ref`, and
      any mismatch raises `reprice_conflict`.
  - Idempotent: a row at its new value that carries the marker and needs no token change counts as `unchanged`. A second
    `--yes` writes nothing and creates no file.
- `src/db/priceLevels.ts` `rebuildPriceLevels(db, loaded, { yes, now, release? })`.
  - Applies to each active `market_data` row of `price_usd` / `diem_price_usd` that is configured.
  - The ref is the source's `params.ref`; for AERO it is the EVM address of the contract named by the adapter's `token`
    param.
  - The price is the newest chain/first-party price with `ts <= observed_at - 1h` and at most 6 h before that (R6 order).
    With none, the row is refused and listed.
  - Writes go through `insertObservation`, which supersedes the CoinGecko row. Provenance: method derived; rung
    `first_party_api` for `first_party:*` sources (plus `input_origin: 'api'`), else `contract_state`; chain from
    `venueOfMethod`; locator `{ from: 'prices', token_ref, ts, source }`; formula `price_level_from_prices@1`.
  - Runs under the asset lock, one transaction per day, and rechecks that the CoinGecko row is still active.
- `src/db/purge.ts`:
  - `writeExport` is generalized into the exported `writeDurableExport` (plus `exportStamp` and `fsyncDir`). Purge
    behaves the same (its tests are unchanged and pass).
  - `purgePrices(db, { source: 'coingecko', yes, exportDir, now, syncDir? })` behaviour:
    - refuses `purge_prices_coingecko_refs` while an active observation has a `coingecko:*` ref, on both the dry run and
      `--yes`;
    - holds `PRICES_RUN_LOCK = 'prices'` (a test pins it equal to the backfill's `PRICES_LOCK`);
    - in one transaction: export to `purged/prices-coingecko-<stamp>.json`, delete every `source='coingecko'` row, then
      delete the `coingecko:*` tokens rows that nothing references. A tokens row still referenced by a rejected or
      superseded observation, or by another source's prices, is kept and listed in `keptTokens`;
    - `invalid_price_source` for any other source.
- CLI (`src/cli/commands/data.ts`): `data reprice <a> [--from D] [--yes] [--json]`, `data rebuild-price-levels <a> [--yes]
  [--json]`, `data purge-prices --source coingecko [--yes] [--json]`. Refusals print the code under `--json` and exit 1
  (`guarded`). Exports go to `$ORION_HOME/repriced` and `$ORION_HOME/purged`. No exit code is set when rows are refused:
  they are listed for Task 9's decision.
- orion-remote:
  - the verbs `data reprice <a> [--from <day>] [--yes]`, `data rebuild-price-levels <a> [--yes]` and
    `data purge-prices --source coingecko [--yes]`;
  - `PRICE_SOURCE_RE = ^coingecko$`, and every value is checked with fullmatch;
  - the help text and the `data:` refusal message are updated;
  - 5 new tests (passthroughs plus 52 refused or injected forms, each exiting 64).
- `docs/ops/deploy.md`: three verb-table entries.

## Tests (RED -> GREEN)

- `tests/db/reprice.test.ts` (9):
  - RED: `Cannot find module '../../src/db/reprice.js'` (0 tests ran);
  - GREEN: 9/9;
  - covers: the dry run writes nothing (whole-table to_jsonb snapshot equal; no lock taken, no export dir); Review Focus 5
    (a 1-of-2 and a 23-of-24 row refused, counted, keep their value, no marker; dry run and `--yes`); the export equals
    the old rows from to_jsonb; values equal the hourly sums; view `usd == value`; `usage_index` (burn_momentum) and
    `burn_rate` (flow_annualized) equal `derived.ts` on the new values; `--yes` twice is a no-op; `--from`; PUMP (twin
    amount + ref, daily mean, history skipped, no-twin refused, 23-of-24 refused); P4 remap (dry run vs `--yes`, yCRV
    tokens row inserted); run_in_progress; export failure leaves nothing written.
- `tests/db/priceLevels.test.ts` (4):
  - RED: module not found; GREEN: 4/4;
  - covers: values and locator, the 6 h refusal, the diem ref, CoinGecko price rows never read, a second run no-op;
    **rebuild then `purgeMetrics --source-type market_data` succeeds and every report day (latestLevel at day end) still
    has a price level**; AERO's token ref; the first-party rung; run_in_progress.
- `tests/db/purge.test.ts` (+4):
  - RED: `purgePrices is not a function` (4 failed); GREEN: 19/19;
  - covers: refused before the remap and successful after `repriceAsset --yes`; the export holds the prices and tokens
    rows from to_jsonb; a kept, still-referenced tokens row is listed; the invalid source; the `prices` lock; the lock
    constant matches.
- `tests/cli/reprice.cli.test.ts` (3): written after the CLI code (not test-first), GREEN 3/3.
- Python: RED against HEAD's orion-remote: 3 failures (the passthrough tests); GREEN `Ran 59 tests OK (skipped=1)`.
- Full: `npx vitest run --maxWorkers=2` 1924/1924 (154 files), no failures and no reruns needed. `npm run typecheck`
  clean, `npm run lint:promises` clean.

## Self-review / decisions to check

1. **How PUMP history is told apart** (not in R26 verbatim). Chain and DefiLlama-history buyback rows share
   `locator.adapter`, the rung and the source_detail format, and both have a `flow_tokens` twin (the history twin is USD /
   CoinGecko price). Rule: a (b) row without an amount whose day began before the first stored supply reading (the earliest
   `observed_at` of `params.supply_metric` with `locator.adapter = solana.token_supply`, any status) is skipped as
   `defillama_history`. This mirrors the adapter's own rule. Without it, the 369 history days would be "repriced" from
   CoinGecko-derived twin amounts. If prod's first reading is not about 2026-10-24, the split moves with it. Task 9's
   dry run should show 21 repriceable and 369 `defillama_history` rows.
2. **"23 of 24" for hourly rows follows the view.** An hour counts as priced when a chain row exists at or up to 6 h
   before it. So one missing hour inside a priced run is not a refusal, matching what the report reads. The test removes
   seven consecutive hours to get exactly one unpriced hour. The daily mean needs all 24 exact hours.
3. The remap covers every row of the asset, ignoring `--from`. It is a ref rename with no value change. It lets
   purge-prices delete the `coingecko:*` tokens rows (superseded rows would otherwise keep them through the FK). The remap
   does not mark rows.
4. Derived rows are updated in place with marker basis `derived`, which goes beyond the brief's `hourly|daily_mean`.
5. A derived row is recomputed only when its window holds a flow day whose value moved, so a stale derived row with
   unchanged inputs is not rewritten.
6. Plan-then-apply: prices written between the export and a day's transaction are not seen (the prices lock is not taken).
   A row whose value or ref changed since the plan raises `reprice_conflict` for that day. Earlier days stay committed;
   rerun to continue.
7. The new value is computed in TypeScript, not read from the view. That keeps the dry run, which needs the remapped refs,
   on the same path as `--yes`. Sums match the view to float rounding (tests use `toBeCloseTo(.., 9)`), and the report
   reads the view's `usd` for these rows anyway.
8. Rebuilt level rows record the release tag (or the dev version) in `code_version`, and the asset's `loaded.hash` in
   config_hash.
9. purge-prices only deletes tokens rows that start with `coingecko:`. `tokens.coingecko_id` values are left for R8.

## Files

src/db/reprice.ts (new), src/db/priceLevels.ts (new), src/db/purge.ts, src/cli/commands/data.ts,
scripts/provision/files/orion-remote, scripts/provision/test/test_orion_remote.py, docs/ops/deploy.md,
tests/db/reprice.test.ts (new), tests/db/priceLevels.test.ts (new), tests/db/purge.test.ts, tests/cli/reprice.cli.test.ts (new).

## Concerns

- Decision 1 (PUMP history split) is an inference from the adapter, not stated in R26. Please confirm it.
- CLI tests were written after the CLI code. Everything else was test-first.
- Nothing remains open from the brief.


## Fix round 1 (task-8-findings.md items 1-5; Rulings R30, R31)

Env: `export ORION_TEST_DATABASE_URL='postgresql://orion_dev@/orion_test?host=/var/run/postgresql'`. Base c5e6172.

RED command (items 1, 3, 5 tests written first):
`npx vitest run tests/db/reprice.test.ts tests/cli/reprice.cli.test.ts --maxWorkers=1` -> `Tests 3 failed | 11 passed (14)`.

1. **IMPORTANT, R30: derived rows over every repriced-or-marked day.**
   - Test: tests/db/reprice.test.ts `R30: a day that failed mid-apply, then a rerun: ...` (adapted from
     t8-review-probe.test.ts case 2). Five burn days, 10-04 zero burn (0 -> 0), usage_index burn_momentum 3 d and
     burn_rate flow_annualized 2 d stored on the old values; a trigger fails the 10-04 day transaction once; rerun; then
     assert both derived series equal derived.ts on the final flows; a third `--yes` writes nothing, no export,
     `recomputed` 0 everywhere, snapshot equal.
   - RED: `AssertionError ... usage_index 2026-10-05T00:00Z: expected 11.8975, received 7.666666666666667` (the old
     CoinGecko-era value, the reviewer's stale case).
   - Fix (src/db/reprice.ts): `changedDays` (days whose value changed in this run) replaced by `repricedDays`: every
     flow day this run prices (repriced or unchanged, never a refused one) plus every flow day of the asset already
     carrying `locator.repriced`. Derived rows whose window holds such a day are recomputed and written only when
     `v !== d.value`, so a second `--yes` stays a no-op (existing `--yes twice` test still green).
   - GREEN: see the focused run below.
2. **MINOR: rung from the venue** (src/db/priceLevels.ts). `sourceType` is now `venueOfMethod(...).rung` and the
   first-party origin key follows `venue.rung === 'first_party_api'`. A refactor: no behaviour change for any real
   source label, so no RED; the existing `AERO ... first-party candle ref gets the first_party_api rung` test and the
   CLI rebuild test pin it (GREEN).
3. **MINOR: supply split ignores rejected readings.**
   - Test: `PUMP: a rejected supply reading does not move the history/chain split` (rejected reading 10-20, active
     10-24; the 10-23 row with a twin and 24 priced hours must be `defillama_history`).
   - RED: `repriced: expected 0, received 1; skipped: expected { defillama_history: 1 }, received {}`.
   - Fix: the first-reading query adds `AND status <> 'rejected'`.
4. **MINOR: tautological assertion** (tests/db/reprice.test.ts Review Focus 5). `yes ? 1 : 1` -> `1`, plus a third
   call after `--yes` asserting `repriced 0, unchanged 1` and the gap row still refused. Test-only; it passes on the
   fixed code (it asserts existing behaviour, so no RED).
5. **MINOR: exit 3 on refused rows** (src/cli/commands/data.ts `REPRICE_REFUSED_EXIT = 3`, set after the output,
   dry run and `--yes`; JSON unchanged and still lists `refused`; error exits stay 1). CLI help and docs/ops/deploy.md
   say so. orion-remote's `passthrough` already returns the CLI's exit code, so the remote verb exits 3 as well.
   - Test: tests/cli/reprice.cli.test.ts: dry run `exit [3]`, `--yes` `exit [3]`, `--json` `exit [3]` with the
     refused list, `--from 2026-10-05` (nothing refused) `exit []`.
   - RED: `AssertionError: expected [] to deeply equal [ 3 ]`.

R31 (rebuild-price-levels 6 h staleness refusal) accepted as is; no change.

GREEN / gates:
- `npx vitest run tests/db/reprice* tests/db/priceLevels* tests/db/purge* tests/cli/reprice* --maxWorkers=1`
  -> `Test Files 4 passed (4); Tests 37 passed (37)` (35 before + 2 new).
- `python3 -m unittest scripts/provision/test/test_orion_remote.py` -> `Ran 59 tests ... OK`.
- `npx vitest run --maxWorkers=2` -> `Test Files 154 passed (154); Tests 1930 passed (1930)` (no load-sensitive
  failures this run).
- `npm run typecheck` -> clean; `npm run lint:promises` -> exit 0.

Commit: 3aca04e. Files: src/db/reprice.ts, src/db/priceLevels.ts, src/cli/commands/data.ts, docs/ops/deploy.md,
tests/db/reprice.test.ts, tests/cli/reprice.cli.test.ts, this report.

Self-review / notes:
- R30 widens recomputation to derived rows whose window holds any marked day, including marked days before `--from`
  (a window may reach back past it); only in-range derived rows are written, as before.
- A derived row stored by a later fetch on the new values is equal, so it is counted `unchanged`, never rewritten.
- Deferred (ledger) items untouched: reprice.ts log_scan `hourly_amounts` with null amount; CLI tests written after code
  in round 0.
