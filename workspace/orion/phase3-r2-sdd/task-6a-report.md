# Task 6a report: flows, levels and PUMP burn read chain prices; price_coingecko_id retired

Status: DONE. Commit `7063c22 feat(prices): flows, levels and PUMP burn read chain prices; price_coingecko_id retired`
(base 7ff7562, 77 files, +949/-830).

## What changed (6a scope, Ruling R18/R19)

1. **flow.ts**: `loadPrices`/`priceAt`/`PriceSeries`/`parseMarketChart`/`isMarketChartBody` and every CoinGecko request
   are gone. Before scanning, `scanFlowGroup` calls `args.priceWriter(db, refs, rangeStart, rangeEnd, { dryRun })` for
   the usd members' refs (`memberToken`: the scanned token's `evmTokenRef`, or a share's `share_price.underlying`), then
   reads them with the new `chainPricesAt` (db/prices.ts): chain:/first_party: rows only, newest at or before the hour
   start, <= 6 h old, tie-break fetched_at DESC then source (R6), identical to `flow_usd_chain_v`. Value per usd member =
   sum over the day's 24 hours of `hourly[h] x price(h)` (hour buckets). An hour with a non-zero amount and no price
   throws `no <ref> price point at or before <hour ISO>; day <day> was not written` (the old pattern, naming the ref and
   the hour), so the day is withheld and the cursor stays. Writer chain errors become outcome notes.
   - New type `ChainPriceWriter`; `FlowScanArgs.http/env` replaced by `priceWriter`.
   - R19: `writeChainPrices` takes `dryRun` (no `prices`, no `hour_blocks` write, no breach evaluation) and returns the
     rows in `WriteResult.rows`; the dry-run scan ranks them with the stored rows (`chainPricesAt(..., extra)`).
   - `FetchDeps.priceWriter?` (test injection); default `priceWriterOf(deps, loaded.prices)` = writeChainPrices over
     `makePriceDeps(env, { rpcFactory, prices, http, now })`. `LoadedAsset.prices` (optional) carries the prices.yaml map
     `loadAsset`/`parseAssetObject(obj, prices)` was given. refresh.ts binds the writer to the *unwrapped* base deps so
     the writer's block reads never overwrite the fetch's block_number capture.
2. **tokenBackfill.ts**: `backfillPrices`, `BackfillPrices`, `result.prices`, the market_chart/range use and the CLI's
   `prices ...` line are deleted. Token amount backfill stays (used by `data backfill-tokens`). Dead helpers
   `storedPriceHours` and `coingeckoTokenRef` deleted (no other user).
3. **solana.ts `supply_burn_daily`**: USD = tokens x mean of the day's 24 chain prices of `solana:mainnet/<mint>` read
   through the new `SourceContext.chainHourPrices` (exact-hour chain rows, run.ts wires `chainHourPrices(db, ...)`); a
   day with fewer than 24 gets no USD row (listed in the detail: `no price (fewer than 24 chain hours of <ref>) for
   <days>`); if on-chain days exist but none is priced the read fails. No market_chart; `params.coingecko`/priceId gone;
   the token row's coingeckoId is null. History-day token conversion (unit tokens) uses the same daily mean.
4. **levels**: `runLevels(..., { prices })` after the level reads calls the writer once for every prices.yaml ref over
   `recentPriceHours`: per ref, from the hour after its newest row under its primary's source (methodSource), floored
   at 48 h back, to the top of the current hour (min over refs; the writer skips stored hours without reads). A writer
   throw is recorded (`prices.error`), never fails the read. The job handler loads prices.yaml from the config root,
   posts each `WriteResult.breaches` entry once as `ORION WATCH <env> price <symbol> <ts>: <+/-gap 2dp>% vs <check>`
   (through `ctx.notify`, counted in undelivered/deadman like the watch posts; no anomaly), and reports
   `result.prices = { written, missing, errors, breaches }` (null when nothing ran). `/coins/markets` prefetch is
   unchanged in code: it prefetches every remaining coingecko source id (price_usd until 6b, circulating_supply).
5. **daemon**: `sharedHttpCache` (JobContext, Daemon.slotCaches, SHARED_CACHE_SLOTS, refresh plumbing,
   FetchDeps.sharedHttpCache, `withSharedCache`, `isMarketChartUrl`) removed.
6. `src/prices/coingeckoHourly.ts` deleted.
7. **price_coingecko_id retired**: removed from the transfer_flow zod schema (strict: refused by name). sourceIssues
   now requires `share_price.underlying` on a usd vault-share member. Load-time check (load.ts, when a non-empty prices
   map is given): every usd transfer_flow's ref (`usdFlowRefs`, prices/config.ts) must be in prices.yaml, else
   `invalid_asset_config` naming metric, contract and ref. All 34 YAML lines dropped; yCRV `flow_usd.fees` and
   `flow_usd.yearn_revenue` -> `underlying: crvusd`, `flow_usd.yearn_styc_fee` -> `underlying: token` (yCRV). Comments
   on pump.yaml/vvv.yaml that said "CoinGecko price" updated. `tools/sources-register/generate.ts`: transfer_flow and
   `solana.supply_burn_daily` no longer list CoinGecko; `docs/ops/sources-register.md` regenerated (only the CoinGecko
   row's "used by" cell changed; `--check` passes).
   - Forced by the retirement (outside the file list): `docs/templates/T1,T3-T10*.md` (tests/config/templates.test.ts
     loads them): `price_coingecko_id` dropped, T5's share lines get `underlying: fee_token`, now-unused example values
     removed, T3's comment updated.

## Hash re-pins (combined hash, loadAsset; `grep -rl <old> tests`)

| asset | old | new | test files |
|---|---|---|---|
| cake | 86b98b90382d… | 86359b56c1c1… | tests/assets/cake.ingest.test.ts |
| crv | 5e797f7ca2ac… | 2cbf746088a8… | tests/assets/crv.ingest.test.ts |
| cvxcrv | e4eed3b4b90c… | f1a2f4bafa91… | tests/assets/lockers.ingest.test.ts |
| link | de8fdaa00cc4… | 4479e2426ded… | tests/assets/link.ingest.test.ts |
| sdcrv | 20de7d924c8f… | db7ef33f45e5… | tests/assets/lockers.ingest.test.ts |
| sky | 9d97775d492b… | 48c23f259234… | tests/assets/sky.ingest.test.ts |
| uni | 255b8a06512f… | 7ece78194e01… | tests/assets/uni.ingest.test.ts |
| vvv | d8223609d9e3… | b32ee86f97fe… | tests/assets/vvv.ingest.test.ts, tests/config/load.test.ts |
| ycrv | fad46ffce87b… | 7f6c53a1d473… | tests/assets/ycrv.ingest.test.ts |

aero, hype, lit, pump unchanged (pump: comment only). Config-only hashes of the 9 moved too; none is pinned in tests.

## Goldens

No golden path moved: tests/report/golden/*, tests/agent/golden/* and report parity tests pass unmodified. Every test
that seeded a CoinGecko market_chart for a flow was re-seeded with identical chain prices (fake writer
`tests/helpers/chainPrices.ts` `fakePriceWriter`/`seedChainPrices`, source `chain:test`): flat charts per ref
(cake 2.3, link 12.5, uni 7.5, sky 0.07/USDS 1, crv 0.9993, ycrv 0.9991, lockers per stream), VVV's captured
hour-aligned series as-is, PUMP 0.005 for 400 days of hours. All flow values in those tests are unchanged.

## Tests (TDD)

New/rewritten (RED first unless noted):
- flow.test.ts: bucket sum (914 = 2x7 + 100x9; writer called once with [MINI_REF] over exactly the scanned hours; no
  HTTP call); 6 h lookback / CoinGecko row ignored; missing hour withholds the day with the exact message; dry run writes
  no prices row (writer called with dryRun) and makes no HTTP call. RED: 12/12 scan tests failed (undefined priceWriter).
- writer.test.ts: dry run returns the same rows, writes no prices/hour_blocks, real run stores identical prices. RED:
  rows written in the dry run.
- coingeckoPlan.test.ts: a full mini fetch makes no market_chart request; CoinGecko only /coins/markets.
- three-place retirement: tests/config/sources.test.ts (load), tests/agent/tools.test.ts (filing),
  tests/app/proposals.test.ts (approve; YAML untouched, proposal pending), plus the share_price.underlying requirement.
  RED shown by running them against HEAD's src/config/sources.ts: 4/4 failed; GREEN after.
- load.test.ts: prices.yaml load-time check (every repo asset loads; yv_crvusd underlying refused naming ref).
- db/prices.test.ts: chainHourPrices/chainPricesAt rule (tie-break, 6 h, CoinGecko ignored, dry-run extras).
- adapters.solana.test.ts: mean of 24 hours (0.005/0.007 -> 6M USD), refused with 23 hours (no USD row; token row kept),
  no CoinGecko call, fails when no on-chain day is priced. (Written with the code; HEAD's solana.ts cannot load against
  the new flow.ts, so no separate RED run.)
- levels.test.ts (recentPriceHours, runLevels writer call + last completed hour for every ref + writer throw recorded,
  formatPriceBreach) and levelsJob.test.ts (last completed hour of every ref written, breach posted once with the exact
  text, nothing posted next hour, no anomaly). Written after the code; RED shown by swapping in HEAD's levels.ts and
  jobs/levels.ts: 5 failed (recentPriceHours/formatPriceBreach not functions, writer not called, result shape); GREEN after.
- Deleted (CoinGecko-only): priceAt/parseMarketChart, daily fallback, "no daily call", shared market_chart cache (3),
  daemon slot cache, fetchHourlyRange, token-backfill price fetch assertions.

Final runs:
- `npx vitest run --maxWorkers=2`: **150 files, 1861/1861 passed** (no load-sensitive timeouts this run).
- `npm run typecheck`: clean. `npm run lint:promises`: clean. `python3 -m unittest scripts/provision/test/test_orion_remote.py`: 52 OK.
- `npx tsx tools/sources-register/generate.ts --check`: current.

## Self-review / concerns

1. **First backfill cost**: a scan with no stored prices now writes every hour of its range inline (yCRV's 100-day
   first backfill = 2,400 chain-hours) through the real writer during the fetch. Task 7's prices backfill is expected
   to fill history first; until then a nightly scan of new days writes ~24 h per ref (cheap). No budget is passed to
   the writer from a flow scan.
2. **Price-chain RPC env**: the default writer needs the price chains' URLs (ORION_ETH_RPC_URL for every Ethereum ref
   and for off-chain refs' USD feed; Base/BNB default). A missing one is an OrionError (`no_rpc_url`) that stops the
   fetch as a configuration error, like `missing_rpc_url`.
3. **Load-time ref check applies only with a non-empty prices map** (a root with no prices.yaml, or parseAssetObject
   without a map, is not checked: the Task 1 deferred minor). Such a fetch then fails at the writer with
   `unknown_price_ref`.
4. **Levels breach "once"** relies on the writer's per-run breach rule (Task 3: reported at the hour completing a run,
   only when that run includes a newly written hour); the levels tests use a fake writer for the breach list, so the
   once-per-run semantics are pinned by Task 3's writer tests, not re-pinned end-to-end here.
5. `LoadedAsset.prices` is a Map on the loaded object (not serialised anywhere I found).
6. Docs not updated (Task 9): docs/ops mentions of the nightly's shared market_chart cache / CoinGecko flow pricing,
   the ingestion spec's `price_coingecko_id` row. Historical plans/specs left as written.
7. Process slip, recovered: while recording the levels RED run a `cp` clobbered `src/daemon/jobs/levels.ts`; it was
   rebuilt from HEAD plus the same scripted edit, re-verified (8/8 levelsJob, full suite after), and committed.

Not in 6a (6b): price.token / price.token_check adapters, price_usd/diem_price_usd sources and cross-checks, type:price
checks, entriesFor from refs (R11), report goldens beyond hash pins.
