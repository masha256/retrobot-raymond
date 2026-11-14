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
