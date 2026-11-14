# Task 6b report: price_usd from chain/first-party methods on 12 assets; CoinGecko price reads removed

Status: DONE. Commit `661bf9c feat(prices): price_usd from chain/first-party methods on 12 assets; CoinGecko price reads removed`
(base 7063c22, 58 files, +1531/-284).

## What changed

1. **Adapters `price.token { ref }` / `price.token_check { ref }`** (src/ingest/adapters/price.ts, registered).
   - EVM ref: `priceHourEvm` (evmMethods.ts) over the ref plus its quote refs (primary and check, transitively; all on
     its chain), at `HourBlocks { start: first block at or after run block - 1 h (only when a v2/Aerodrome cumulative
     TWAP is among them, else the run block), end: run block }`. On the asset's ingest chain it uses the run's own RPC
     and block; another chain is read at that price chain's head through `ctx.priceDeps.rpcFor`. A ref with no price
     (quote missing, failed call) fails the reading naming the reason; a stale quote is never used.
   - Off-chain ref (HYPE, LIT, PUMP): `livePriceOffchain` (offchainMethods.ts), observedAt = the fetch time.
   - One read per run per ref (WeakMap on the SourceContext), shared by price.token and price.token_check, and one
     BlockReadCache per run (DIEM's read reuses VVV's calls). A failed read is not cached.
   - price.token_check: the check's USD from the same read; for `bound` (sdCRV) the primary itself inside the band and the
     nearer bound x the quote's USD outside it, so the cross-check gap (tolerance 0) is the distance outside; the detail
     names the primary in CRV, the band and the prices.yaml gap. A check not read (zero liquidity, error) fails the reading.
   - validateParams refuses any key but `ref`, a missing ref, and (when the loader has a non-empty prices.yaml) a ref not
     in it. `AdapterDef.validateParams(params, ctx?)` gained the optional `{ prices }` context, passed by parseAssetObject.
   - Stamp: `api` on a first-party venue (HYPE, LIT primaries), `onchain` otherwise, matching the rung.
2. **Rung / chain / RPC need per ref** (src/prices/venue.ts): EVM and Solana methods `contract_state`, Hyperliquid and
   Lighter candles `first_party_api`. parseAssetObject (given prices) notes each price source's venue on the parsed
   source object (a WeakMap; config and hash untouched); unnoted sources fall back to the ref's namespace.
   `typeOfSource` (sourceTypes.ts, `adapterSourceType`), `chainOfSource` (locator.ts) and `needsRpc` read it.
   `AdapterDef.needsRpc` may now be a function of the source (`adapterNeedsRpc`, used by plan.ts, run.ts, levels.ts):
   HYPE/PUMP/LIT's price.token need no asset RPC; LIT's check (v4 on Ethereum) does.
   ADAPTER_SOURCE_TYPES + ADAPTER_ORIGINS gain both names (contract_state / onchain as the no-ref default).
3. **Wiring**: SourceContext gains `prices` and `priceDeps` (run.ts: `makePriceDeps(env, { rpcFactory: priceRpcFactory ??
   rpcFactory, prices: loaded.prices, http: the run's cached http })`). New `FetchDeps.priceRpcFactory`: levels.ts and
   daemon/jobs/refresh.ts pass the unwrapped factory so a price read's Ethereum head never overwrites the fetch's
   block_number capture (refresh.ts: one-line change outside the file list).
4. **YAML** (12 assets; aero untouched): price_usd -> price.token + one price.token_check cross-check at the prices.yaml
   tolerance (CRV 1.5, cvxCRV 3, sdCRV 0, yCRV 3, SKY 2.5, LINK/UNI/CAKE 2, VVV 2, HYPE 2, LIT 3, PUMP 2); VVV
   diem_price_usd the same with the DIEM ref (cross-check added). Replaced checks: CAKE/LINK/UNI Chainlink contract_read,
   LIT orderBookDetails http_json, PUMP Jupiter http_json, VVV Venice vvv_stats price. CAKE/LINK/UNI `type: price` checks
   `against: price.token_check` (check id `price_chainlink` kept: stored check rows key on it); the `chainlink_*_usd`
   contract entries removed (nothing else referenced them). Comments updated.
5. **Checks** (src/checks/schema.ts): a `type: price` `against` may name the adapter of exactly one adapter cross-check
   of `level` (resolved as `{ kind: 'cross_check', contract: <name>, sourceId }`); the primary's own adapter is refused.
6. **R11** entriesFor: refs from price.token/price.token_check params (primaries and cross-checks), transfer_flow
   scanned tokens and `share_price.underlying`, plus quote refs; the symbol match and the every-contract scan are gone.
7. **levels.ts**: no code change to the prefetch (it already took every remaining coingecko id); comment updated; test
   pins that the 13 repo assets prefetch exactly the 9 circulating_supply ids and no asset names a CoinGecko price.
8. **Sources register**: ADAPTER_ENDPOINTS for both (by the ref's method in the repo prices.yaml: the price chain's RPC;
   Hyperliquid info / Lighter API / Solana RPC + the Ethereum RPC for USDC/USD); the Jupiter TERMS row removed (no reader);
   CoinGecko note now "circulating supply only"; docs/ops/sources-register.md regenerated, `--check` current.
9. prices.yaml header comment updated to the R11 rule (comment only; no hash moved by it).

## Hash re-pins (combined hash, `loadAsset`)

| asset | old | new | why |
|---|---|---|---|
| aero | 035327b9eec2… | 3c413feb4fbd… | R11: names no ref now (config-only hash) |
| cake | 86359b56c1c1… | e863393a2a48… | YAML + R11 |
| crv | 2cbf746088a8… | 9787bef1f28e… | YAML + R11 |
| cvxcrv | f1a2f4bafa91… | e2ba388d44ea… | YAML + R11 |
| hype | 2ec7d2cefc9b… | af6d3b0124f2… | YAML |
| link | 4479e2426ded… | 5fc85808ea63… | YAML + R11 |
| lit | 300863b835e7… | 7864c2836741… | YAML + R11 |
| pump | a616f10dacc9… | 9c0237adfb21… | YAML |
| sdcrv | db7ef33f45e5… | 357ee9ca0f15… | YAML + R11 |
| sky | 48c23f259234… | be03451c4a2e… | YAML + R11 |
| uni | 7ece78194e01… | 5c1d9cf48fe8… | YAML + R11 |
| vvv | b32ee86f97fe… | b9e654a8fe83… | YAML + R11 |
| ycrv | 7f6c53a1d473… | 908f12e73f67… | YAML + R11 |

Pins updated in tests/assets/*.ingest.test.ts, tests/config/load.test.ts (lit, vvv, hype, aero), tests/agent/disclosure.e2e.test.ts (LIT_HASH).

## Goldens (flattened old vs new, script scratch/golden_diff.py)

- **v2-report-13.json**: inputs unchanged (all 65 input hashes identical). In the 60 entries of the 12 assets exactly two
  paths moved: `incomeStatement.priceBasis.source` (`market_data:coingecko` -> `contract_state:price.token`; hype, lit ->
  `first_party_api:price.token`) and `incomeStatement.priceBasis.sourceType` (`market_data` -> `contract_state` /
  `first_party_api`). aero's 5 entries unchanged. **Report value paths outside the allowlist: 0** (no revenue, cost,
  holder-flow, yield, dilution, grade or price value moved).
- **packs-13.json**: aero unchanged; each of the 12 gains the `adapter_params` entries of price_usd's price.token and
  price.token_check (VVV also diem_price_usd's), with their paramsDoc (lit/pump: the inserted entries shift indexes).
  With the `price.*` entries removed every pack is identical to the old one (checked by script). No value moved.
- v1-report-13.json, parity: unchanged (parity.test passes on the new v2 golden).

## Tests (TDD)

New (RED recorded against the base code by stashing the src/assets changes):
- tests/ingest/adapters.price.test.ts (16): feed (LINK 12.5 vs v3 TWAP check, one multicall for both), Curve x CRV ref x
  crvUSD chain (cvxCRV), a missing quote fails naming quote_missing, Uniswap v2 TWAP over [run-1h, run] (SKY, start block
  asserted), Aerodrome TWAP x ETH/USD (VVV), chained DIEM via VVV, a ref off the asset's chain at that chain's head
  (CAKE), sdCRV bound inside (gap 0 at tolerance 0) and above (1.0 CRV bound, breach, gap 10%), Hyperliquid allMids
  (api stamp), Lighter mid with the v4 check (api / onchain), PumpSwap vaults with the Meteora check, validateParams
  refusals (unknown key, missing ref, ref not in prices.yaml; none without prices), load-time refusal naming the metric,
  unknown ref at run (`unknown_price_ref`), rung/label/chain/needsRpc per asset. RED: 16/16 failed (`unknown adapter: price.token`).
- tests/prices/config.test.ts R11 test: RED `expected [ 'hyperliquid:spot/@107' ] to deeply equal []` (symbol match).
- tests/levels/levels.test.ts circulating_supply-only prefetch: RED with the base YAMLs (12 coingecko price sources).
- tests/checks/evaluate.test.ts price check against price.token_check (ok and breach) and resolution/own-adapter
  refusal: RED 2/2 against the base schema.ts (`neither a metric nor a contract`).
- tests/provenance/adapterOrigins.test.ts: samples for both adapters, plus HYPE's first-party stamp = its rung's origin.
- tests/report/incomeStatement.test.ts: priceBasis source per asset (crv/pump contract_state, hype/lit first_party_api,
  aero unchanged) and sourceTypeOf of price adapters by ref namespace.
Updated: 12 asset ingest tests fake the ref's method reads instead of /coins/markets price (tests/helpers/livePrices.ts
`liveEvmCalls` builds feed/curve/get_dy/v2/Aerodrome/v3/v4 results for a wanted USD; `pumpLiveAccounts`, `hyperliquidMids`,
`lighterBook`) at the same prices (CRV 0.3933, CAKE 2.3, LINK 12.5, UNI 7.5, SKY 0.07, cvxCRV 0.1392, sdCRV 0.1884,
yCRV 0.18345, VVV 26.03, DIEM 1941.6, HYPE 92.36, LIT 3.04, PUMP 0.005); feed/oracle/venue prices still `toBe`, TWAP and
chained products `toBeCloseTo(.., 9-12)`. Plans, cross-check lists (price_usd now checked on crv, sky, ycrv, cvxcrv,
sdcrv, hype; diem_price_usd on vvv), VVV multicall bound (<= 8), HYPE allMids post, PUMP's Ethereum USDC read updated.
tests/helpers/syntheticReport.ts `repoAsset` parses with the repo prices.yaml (so LIT's rung is its method's).

Final runs (after the commit):
- `npx vitest run --maxWorkers=2`: **151 files, 1881/1881 passed** (no load-sensitive timeouts).
- `npm run typecheck`: clean. `npm run lint:promises`: clean. `python3 -m unittest scripts/provision/test/test_orion_remote.py`: 52 OK.
- `npx tsx tools/sources-register/generate.ts --check`: current.

## Self-review / concerns

1. **AERO's hash moves to its config-only hash** (R11 is applied literally: AERO names no price.* ref and scans no token,
   so its prices.yaml entry is no longer in its hash; the Task 1 test "AERO only aero" now expects no asset to move on an
   AERO entry change). Its entry still drives its price history and level rebuild (R21), so a method change there would not
   show as "config" on AERO. If that matters, add AERO's chain.v2_pool_twap_price `token` (or its ref) to entriesFor.
2. **Rung depends on a load-time note**: a price source's rung/chain/needsRpc come from prices.yaml only when the config
   was parsed with it (loadAsset, parseAssetObject(obj, prices)); a hand-built/cloned config falls back to the ref's
   namespace, which mislabels LIT (eip155 ref priced on Lighter) as contract_state. All production paths load with prices.
3. **Cross-check semantics vs prices.yaml**: cvxCRV/yCRV's `consecutive: 2` and LIT's "zero-liquidity hours skipped" are
   writer rules; at fetch time one price.token_check over 3% raises the ordinary cross-check anomaly, and a zero-liquidity
   v4 hour fails the check reading (source note), not a skip. sdCRV's check uses tolerance_pct 0 (inside the band the check
   value equals the primary exactly).
4. **Check id `price_chainlink`** on CAKE/LINK/UNI kept for stored check-row continuity although it now compares the feed
   with the pool check.
5. needsRpc of an EVM price ref on another chain than the asset's still opens the asset's RPC (unused); no repo asset does this.
6. Templates (docs/templates/T*.md) still show a CoinGecko price_usd and a Chainlink price check; docs/ops and the
   ingestion spec are Task 9's. VVV's `external_ids.coingecko_diem` is now unread (R8 drops coingecko ids).
7. RED evidence for the asset/golden re-pins is the base suite's own failures (116 failing before the test updates).

## Fix wave (task-6-findings.md A-G; Ruling R23) — commit 7202a46

`fix(prices): post flow-scan breaches; alert on levels price failures; PUMP burn ensures its hours; levels fills gaps; AERO hash covers its entry; level price cross-checks only where they existed`

RED run (tests written first, code untouched), `npx vitest run tests/daemon/refresh.test.ts tests/daemon/levelsJob.test.ts tests/levels/levels.test.ts tests/assets/pump.ingest.test.ts tests/prices/config.test.ts tests/assets/lit.ingest.test.ts tests/ingest/adapters.price.test.ts --maxWorkers=1`:
`Test Files 7 failed (7); Tests 10 failed | 78 passed (88)` — each new/changed test failed for its own reason (quoted per item). GREEN: the same files pass (with the re-pinned files: 17 files 193/193 after the fixes below).

Per item:
- **A** flow-scan breaches. `FlowScanResult.breaches` (the writer's `w.breaches`); fetchAsset collects them (and C's) into
  `FetchResult.priceBreaches` (absent when none, so no JSON byte moves), deduped by ref|hour|check, sorted; the refresh job
  posts each once via `formatPriceBreach` (`RefreshJobResult.breaches`, undelivered kept). Test: tests/daemon/refresh.test.ts
  "a breach the nightly scan's own price write reports is posted once" (writer fake returns the breach on every call; one
  post `ORION WATCH dev price MINI 2026-09-18T05:00:00.000Z: +2.50% vs chain:chainlink`, no cross_check_mismatch). RED:
  `expected [] to deeply equal [ Array(1) ]`. GREEN.
- **B** levels price failure alert. src/daemon/jobs/levels.ts: when the price summary has errors (prices.yaml unreadable,
  writer threw, writer chain errors) one `ORION ALERT <env> levels prices: <reasons joined by "; ">` (slackClean) is posted;
  reads, onLevels/snapshot_push and the dead-man rule unchanged (an undelivered alert withholds the ping like any post).
  Test: tests/daemon/levelsJob.test.ts "a price write that throws or reports chain errors posts one ORION ALERT ..." (throw:
  `ORION ALERT dev levels prices: rpc down`, ping sent, snapshot_push enqueued, rows 5; two chain errors: one line
  `eip155:1: timeout; eip155:56: refused`; clean: no post; undelivered: deadman false). RED `expected [] to deeply equal [ Array(1) ]`. GREEN.
- **C** PUMP burn ensures its hours. run.ts `ctx.chainHourPrices` now first calls the run's price writer (priceWriterOf:
  injected or writeChainPrices) for the whole hours of the asked range with `{ dryRun }`, notes writer chain errors on the
  running batch, keeps its breaches (A), and reads with the dry run's rows ranked in (CHAIN_DRY_RUN_SOURCE, R19). Skipped
  (stored rows only) when there is no injected writer and the ref is not in the asset's prices.yaml. solana.ts unchanged
  (it already asks [windowStart, todayStart)). Test: tests/assets/pump.ingest.test.ts "a burn day with no stored PUMP
  prices ..." (no seeded prices; dry run: writer called dryRun with [PUMP ref] to todayStart, `prices` table empty, 7 days
  at 5M USD in `written`; real run: writer called, 7 stored days at 5M). RED `expected 0 to be greater than 0`. GREEN.
- **D** levels fills gaps. `recentPriceHours` now returns from the earliest hour of the last 48 h (from each ref's
  valid_from) that any ref lacks under its primary's source, to the top of the hour; null when complete. The writer skips
  stored hours per ref, so a never-writable ref costs only its own hours (doc comment says so). Tests: tests/levels/levels.test.ts
  "recentPriceHours: from the earliest hour ... (a gap inside the window included)" (gap 10 h back -> from TO-10h; cap; a
  valid_from after the window asks nothing) and "runLevels: a gap 10 h back inside the window is filled" (every ref stored
  but one hour; one writer call [TO-10h, TO); the hour is written). RED `expected null to ...` (both). GREEN. (Test refs A/B now
  picked among refs valid before the window: LIT, AERO, HYPE, PUMP start after the harness NOW.)
- **E** entriesFor adds the asset's own `token` contract's ref (on its ingest chain) when prices.yaml has it. Hash diff over
  all 13 assets with only E applied: **aero only** (3c413feb4fbd… -> 035327b9eec2…, its pre-6b value). Tests:
  tests/prices/config.test.ts (entriesFor(aero) = [AERO]; own token adds CRV+crvUSD, an unpriced token adds nothing; the R11
  cases run with the token removed so each shows what it adds) — RED `expected [] to deeply equal [ Array(1) ]`;
  tests/config/load.test.ts (an AERO entry edit moves ['aero']; every asset's hash now differs from its config-only hash). GREEN.
- **F** R22. Removed `price.token_check` cross_checks from price_usd of crv, cvxcrv, hype, sdcrv, sky, ycrv and VVV
  diem_price_usd (comment line before `source:`; a comment after the last key broke tests/config/edit.test.ts round-trip, so
  it sits before). CAKE/LINK/LIT/PUMP/UNI/VVV price_usd keep theirs at prices.yaml tolerance (2/2/3/2/2/2). LIT zero
  liquidity: `NoReading` (src/ingest/types.ts) thrown by price.token_check when the check's `skipped` is `zero_liquidity`;
  the adapter source returns `{ ok: false, noReading: true }`; the level cross-check step notes
  `<metric>: cross-check skipped, the check has no reading this run: ...` and does not mark the source failed (no anomaly,
  no streak); a primary with no reading still fails. Tests: tests/ingest/adapters.price.test.ts "price.token_check is a
  cross-check on CAKE, LINK, LIT, PUMP, UNI and VVV price_usd only, each at its prices.yaml check tolerance" (RED: 12 found
  vs 6) and "a check ... zero in-range liquidity ... is no reading (NoReading)" (RED: NoReading undefined);
  tests/assets/lit.ingest.test.ts "a zero-liquidity v4 check pool gives no check reading (R22)" (3 runs: all sources ok,
  no crossChecks, one skip note naming zero_liquidity, no anomaly rows) (RED: source failed). GREEN.
  Updated expectations (cross-check lists/plans back to no price check): crv, hype, lockers (cvxcrv, sdcrv), sky, vvv
  (diem), ycrv ingest tests; adapters.price rung test and provenance/adapterOrigins HYPE test read the check as
  price.token_check of the same ref (no cross-check left to take it from).
- **G** assets/pump.yaml burn comment reflowed (and says the fetch ensures the hours). No hash move (comment only).

Hash re-pins (all 13 hashed before/after by script; moved exactly aero + F's 7):
| asset | old | new | why |
|---|---|---|---|
| aero | 3c413feb4fbd… | 035327b9eec2… | E |
| crv | 9787bef1f28e… | c25e74237267… | F |
| cvxcrv | e2ba388d44ea… | 5df3f84495c0… | F |
| hype | af6d3b0124f2… | 74c59b28b4d6… | F |
| sdcrv | 357ee9ca0f15… | 09a7ff1a81fd… | F |
| sky | be03451c4a2e… | 215dfdf1f070… | F |
| vvv | b9e654a8fe83… | 359d286886b9… | F (diem) |
| ycrv | 908f12e73f67… | 9d7e62d3b7b0… | F |
Pins in tests/assets/{aero,crv,hype,lockers,sky,vvv,ycrv}.ingest.test.ts and tests/config/load.test.ts (vvv, hype, aero).
RED before re-pin: 8 files, 22 failed (hash pins + cross-check lists).

Goldens (flattened old vs new; scratch golden_diff.py; values that are JSON strings parsed):
- tests/agent/golden/packs-13.json (UPDATE_GOLDEN=1 packGolden only): 26 changed paths, all under
  `<asset>.adapter_params[i]` of crv, cvxcrv, hype, sdcrv, sky, ycrv, vvv (the removed price.token_check entries; vvv's
  index shift). Script check: removing exactly the R22 entries (price.token_check on F's assets, vvv's diem_price_usd)
  from the old pack gives the new pack for all 13 assets: 0 mismatches. No value path moved.
- tests/report/golden/v1-report-13.json, v2-report-13.json: unchanged (v2Golden + parity pass without update).
- docs/ops/sources-register.md regenerated (the removed cross-check uses drop from the Ethereum RPC and Hyperliquid rows); `--check` current.

Final runs:
- `npx vitest run --maxWorkers=2`: 151 files, **1887/1888**; the one failure tests/push/gitPublisher.test.ts "a moved remote
  is refused, alerted once, outbox kept" timed out at 5000 ms (load); alone at `--maxWorkers=1`: 7/7 passed. (First full run
  had 3 real failures, fixed: tests/config/edit.test.ts VVV round-trip x2 -> comment moved before `source:`;
  adapterOrigins HYPE check source.)
- `npm run typecheck`: clean. `npm run lint:promises`: clean. `python3 -m unittest scripts/provision/test/test_orion_remote.py`: 52 OK.
- `npx tsx tools/sources-register/generate.ts --check`: current.

Concerns:
1. C runs the real writer inside any fetch that prices a burn (PUMP's 7-day window, or the backfill window on a first
   adapter-flow fetch: up to backfill_days of hours, clipped by PUMP's valid_from 2026-10-12; stored hours skipped). Asset
   tests that give no writer now exercise writeChainPrices over their fakes (pump: chain errors noted, stored rows used).
2. A breach from a CLI `orion fetch` (no notify) is in FetchResult.priceBreaches but not printed by fetchSummary.
3. NoReading is honoured only for level cross-checks (flow cross-checks keep failing on any error); only `zero_liquidity`
   maps to it.
