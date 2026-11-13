# Phase 3 R2 scoping: prices in code and data (on-chain hourly prices + 183-day rebuild)

Read-only scoping, 2026-11-13. Code: `.worktrees/phase3` at 8f50ac6 (= prod release orion-2026.11.12.1).
Data: prod `sql-ro`, 17 queries, measured 2026-11-13 ~14:30Z. "Measured" = from prod SQL or code read here;
"proposed" = my design, not built. Raw query results: `cache/scratch/r2_measure.json` (scratch, pruned after 24 h).

## 0. Headlines

1. **No job writes hourly prices on its own.** The `prices` table is filled as a side effect of every nightly
   `transfer_flow` scan (it re-upserts CoinGecko's whole 90-day hourly market_chart per id, every night: all 12 refs
   have `last_fetch` 00:45-00:47Z today) and by the one-time `data backfill-tokens`. R2 must add a writer of its own.
2. **`value` (legacy USD) is CoinGecko-priced on every `log_scan` USD flow row**, priced per transfer at write time:
   10,906 `hourly` + 309 `legacy_unpriced` rows over all time (6,188 within 182 days). The view re-prices them from
   `prices`, but `value` itself stays CoinGecko-derived, and three things still read it: the report (for 2,112 rows in the
   182-day window, see 3), the stored derived rates (`flow_annualized`/`burn_momentum`, e.g. VVV `usage_index`, 183 rows),
   and the rows' own history. D3 "no CoinGecko-derived USD kept" therefore needs a **re-value of `value`**, not just new
   `prices` rows.
3. **The report already ignores the view for 2,112 of 6,185 `hourly` rows in the 182-day window**: rows backfilled with
   daily CoinGecko points (`pricedHourlyAtIngest` false, src/db/prices.ts:169-171) are folded to `legacy` and read
   `value` (prices.ts:182-185, :199-200). R2 must drop that gate once every hour is chain-priced.
4. **The view's priority rule must change** (migration 0008): `ORDER BY CASE WHEN source='coingecko' THEN 0 ELSE 1 END,
   ts DESC` (0005:86) makes a CoinGecko row up to 6 h old beat a chain row at the exact hour.
5. **History reaches back further than 183 days.** Flow rows with tokens start 2025-10-14 (396 days); CoinGecko prices
   start 2025-11-17/18 (8 refs) or 2026-03-26 (UNI, CVX, sdCRV, VVV). 4,721 `hourly` + 306 `legacy_unpriced` rows are
   older than 182 days. A 183-day rebuild leaves them on CoinGecko `value`; see decision R2-D4.
6. **Two token refs are CoinGecko ids** (`coingecko:crvusd`, 628 rows; `coingecko:yearn-crv`, 395 rows; yCRV only).
   They must be re-pointed to address refs, since a chain writer keys by address.
7. **PUMP has no hourly history to rebuild, and Solana can't read past state.** It has no `prices` rows; its 21
   on-chain burn days were priced at CoinGecko's daily mean. Its 369 older days are DefiLlama dollars whose
   `flow_tokens` twin = USD / CoinGecko price.

## 1. Map: every place a price is fetched, stored or read (file:line)

### 1.1 Fetchers (CoinGecko HTTP)
| Where | What | R2 change |
|---|---|---|
| src/ingest/sources/coingecko.ts:75-99 | base URL / plan / key headers (`api.coingecko.com`, `pro-api`) | stays until R8 (still serves `circulating_supply` until R3); no price reader left after R2 |
| src/ingest/sources/coingecko.ts:101-128 | `coingecko` source type: `/coins/markets` `current_price` for `price_usd` (12 assets) and VVV `diem_price_usd` | YAML: every `price_usd` / `diem_price_usd` source moves to a chain/first-party method |
| src/levels/levels.ts:17-56 | hourly `levels` job prefetches `/coins/markets` for every coingecko id (`coingeckoIds`, `prefetchMarkets`) | after R2 it fetches only `circulating_supply` ids (R3 removes the rest) |
| src/daemon/daemon.ts:77 | per-slot shared cache of CoinGecko market_chart replies (nightly refreshes) | goes with flow.ts loadPrices |
| src/ingest/flow.ts:81-91 `loadPrices` | `market_chart?days=90` (hourly) + `days=N` (daily beyond 90 d) per `price_coingecko_id` | replaced by a read of `prices` (chain rows) |
| src/prices/coingeckoHourly.ts:9, 16-24, 47-69 | `COINGECKO_PRICE_SOURCE`, `hourlyPriceRows`, `fetchHourlyRange` (market_chart/range, 89-day windows) | file deleted; replaced by `src/prices/chainHourly.ts` (proposed) |
| src/ingest/adapters/solana.ts:108-125 | `solana.supply_burn_daily`: `market_chart?days=min(365,days+1)`, `dailyMeanPrice` | read the day's chain prices from `prices` (or a Solana method), see 2.6 |

### 1.2 Writers of `prices` / `tokens`
| Where | What |
|---|---|
| src/db/pg/migrations/0005_tokens_prices.sql:10-29 | `tokens(token_ref PK, symbol, decimals, peg, coingecko_id)`, `prices(token_ref, ts, price_usd, source, fetched_at)`, PK (token_ref, ts, source); comment already anticipates `'chainlink:<feed>' \| 'pool:<addr>'` sources |
| src/db/prices.ts:38 | `coingeckoTokenRef(id)` = `coingecko:<id>` |
| src/db/prices.ts:56-64 | `upsertToken`: fills `coingecko_id` once (COALESCE) |
| src/db/prices.ts:76-92 | `upsertPrices(db, ref, source, rows, fetchedAt)`: top-of-hour check, ON CONFLICT replace. Reusable as-is for chain rows |
| src/db/prices.ts:98-106 | `storedPriceHours(refs, source, from, to)`: hours present under every ref; the natural resume cursor for a rebuild |
| src/ingest/flow.ts:211-223 `memberToken` | token of a member: share-priced member gets `coingecko:<price_coingecko_id>`; else the scanned token with `coingeckoId` |
| src/ingest/flow.ts:476-491 | nightly: loads series per id, `upsertToken`, upserts every hourly point under every ref sharing the id (`COINGECKO_PRICE_SOURCE`) |
| src/ingest/tokenBackfill.ts:254-267, 311-335 | `backfillPrices`: market_chart/range for hours not stored, upserts under each ref |
| src/ingest/adapters/solana.ts:184 | PUMP token row with `coingeckoId: priceId` |
| src/ingest/periodic.ts:5, apiFlow.ts:6, adapters/hype.ts:1, lit.ts:1 | `upsertToken` / `USD_TOKEN` only (usd-native, no price) |

### 1.3 Per-transfer pricing (the `value` column)
- src/ingest/plan.ts:22, :137: `priceCoingeckoId` from YAML `price_coingecko_id`.
- src/ingest/flow.ts:77-79 `priceAt` (newest hourly point at/before the transfer, else daily); :390-402 `amount *= price`
  per transfer; a missing price withholds the day. :478 requires `price_coingecko_id` on every `unit: usd` member.
- :529-536: `value` = the per-transfer CoinGecko sum; `amount`/`hourly_amounts`/`token_ref` beside it.
- YAML users of `price_coingecko_id` (measured by grep): cake (2), crv (3, crvusd), cvxcrv (7: crvusd, curve-dao-token,
  convex-finance), link (1), sdcrv (10: crvusd, curve-dao-token, stake-dao-crv), sky (2: usds, sky), uni (1), vvv (2),
  ycrv (6 incl. 3 share-priced: `yv_crvusd` → crvusd, `st_ycrv` → yearn-crv, ycrv.yaml:100-101, 123-124, 140-141).

### 1.4 Readers
| Where | What |
|---|---|
| 0005:43-50, 52-90 `flow_usd_v` | hour h price = newest row at/before hour start, **coingecko first** (:86), **≤ 6 h old** (:85); bases `hourly`, `usd_native`, `legacy_unpriced`, `legacy_no_hourly`, `legacy_no_tokens` (:58-69) |
| src/db/prices.ts:160-171 | `HOURLY_SERIES_DAYS = 90`, `pricedHourlyAtIngest` (observed_at−1 d ≥ fetched_at−90 d) |
| src/db/prices.ts:182-185 `priceBasisOf` | `hourly` only if view says hourly AND hourly at ingest; else `legacy` |
| src/db/prices.ts:192-203 `listFlowUsd` | report's per-row USD: view `usd` or `legacy_usd` (= `value`) |
| src/db/prices.ts:228-265 `compareUsd` | `data compare-usd`: within vs beyond split on the same rule |
| src/report/load.ts:80-116 `statementSeries`, :91 | v2 daily series from `listFlowUsd`; periodic streams `legacy` |
| src/report/load.ts:224 | `price` = `price_usd` level at the report's as-of |
| src/report/holderYield.ts:216-234 | header: price, marketCap = price × circulating, fdv = price × total; yields on price |
| src/report/incomeStatement.ts:508-516 `basisOf`, :639, :887, :1016-1021 | per-line `priceBasis`; statement `priceBasis` block (price, metric, sourceType, source, the "G2-signed days" flows text) |
| src/report/parity.ts:51 | soak parity reads `priceBasis.price` |
| src/push/body.ts:83-86 `levelsBody` | publishes every `latest_levels` row, so **today's CoinGecko `price_usd` and `diem_price_usd` reach the site's data repo hourly** (snapshot_push after each `levels`) |
| src/ingest/derived.ts:5-39 | `flow_annualized` / `burn_momentum` read stored rows (`value`): VVV `usage_index` = burn_momentum of `flow_usd.burn_programmatic` (vvv.yaml:136-138), 183 stored rows, CoinGecko-derived |
| src/checks/evaluate.ts:143-160; cake.yaml:146, link.yaml:147, uni.yaml:125 | `type: price` checks of `price_usd` against the Chainlink feed: **circular once the Chainlink feed is the method** |
| src/daemon/jobs/stagingRefresh.ts:25 | the weekly staging refresh restores prod's `tokens` and `prices` into stage |

## 2. What R2 must change, and the smallest design (proposed)

### 2.1 Chain price writer (replaces src/prices/coingeckoHourly.ts)
- `src/prices/chainHourly.ts`: `writeChainPrices(db, deps, refs, fromHourMs, toHourMs)`. For each chain, group every ref
  on that chain. Per hour H, resolve the block at H (and at H+1h for a TWAP); a block-per-hour cache next to
  `day_blocks` is worth adding. Then make **one multicall per chain-hour** reading every feed / pool cumulative / pool
  slot0 / share price the chain's refs need. Upsert with `upsertPrices` (prices.ts:76), `source = 'chain:<method>'`
  (e.g. `chain:chainlink`, `chain:twap`, `chain:wrapper`, `chain:peg`, `first_party:hyperliquid`), keyed by address ref.
  Idempotent; resume = `storedPriceHours` per source.
- Semantics to pin in the plan: row ts = H is the price for the bucket [H, H+1h) (the view picks `ts ≤ hour_start`).
  For a TWAP that is the TWAP over [H, H+1h), written once H+1h has passed. For a feed, the answer at the last block
  ≤ H (or ≤ H+1h; pick one and keep it for every method).
- Call cost, proposed vs spec: the spec's 52.7k (12 × 24 × 183) counts a call per ref-hour. Batching by chain gives
  ≈ 3 chains (mainnet, BNB, Base) × 24 × 183 ≈ **13.2k multicalls**, plus the hour-block lookups. That is an estimate;
  the plan must measure Alchemy compute units on a sample day. With R2-D4 = full history (396 days): ≈ 28.5k.
- Who calls it, in the smallest design:
  1. the flow writer, before it scans (flow.ts:473-491): `writeChainPrices` for the scan's hours, then read them back
     from `prices` (replaces `loadPrices`/`priceAt`). This keeps the nightly self-sufficient: a missing hour withholds the
     day exactly as a missing CoinGecko point does today (:397-400).
  2. the backfill `op: 'prices'` (2.7);
  3. optionally, the hourly `levels` job: writes the last completed hour for every ref, so `prices` stays current for
     the site even for refs with no flow (HYPE, LIT, cvxCRV, DIEM). It isn't required for the reports.
- `value` from then on = Σ_h hourly_amounts[h] × chain price(h) (hour-bucket pricing, the view's own rule) instead of a
  per-transfer price. This is a methodology change of ±0.1-0.2% per asset (see the view-vs-legacy gaps in 3.2): state it
  in the plan's value-change table.

### 2.2 Config shape (decision R2-D1)
Token refs are shared across assets: crvUSD is used by crv, cvxcrv, sdcrv and ycrv; CRV by cvxcrv and sdcrv (1,830 /
2,013 rows in 183 d). Options:
- **(a) Central `prices.yaml` at the config root** (beside schedule.yaml), keyed by token ref: one method per ref, its
  check, decimals, and the earliest hour the method is valid. The asset YAML's `transfer_flow` drops
  `price_coingecko_id` (the ref is the scanned token's address). A share-priced member names its underlying contract
  (`share_price: { ..., underlying: crvusd }`) instead of a CoinGecko id. Load-time check: every ref a `unit: usd`
  member needs has an entry. Cost: the asset config hash must include the entries its refs use, or provenance can't see
  a price-method change. Re-pin every asset test.
- (b) Per-asset `prices:` block keyed by contract name. That means crvUSD in 4 files and CRV in 3, and drift between
  copies needs a cross-asset consistency check.
- *Recommend (a)*. The `price_usd` level stays a per-asset metric with its own chain adapter (as AERO's
  `chain.v2_pool_twap_price` + `chain.cl_pool_spot_price` check, aero.yaml:34-41). A new source
  `{ type: adapter, name: chain.token_price, params: { ref } }` could read the same `prices.yaml` method at the run
  block. That gives one definition per token, and the level and hourly series can't disagree.

### 2.3 `flow_usd_v` (migration 0008, decision R2-D2)
- Replace the CoinGecko-first order (0005:86) with **chain sources only**:
  `WHERE ... AND (starts_with(pr.source,'chain:') OR starts_with(pr.source,'first_party:'))`, then `ORDER BY ts DESC`.
  During the rebuild, a day without chain prices reads `legacy_unpriced` (= today's `value`), so no figure mixes the two
  sources silently, and CoinGecko rows become inert (purgeable at leisure). The alternative "chain first, CoinGecko
  fallback" mixes bases inside one window while the rebuild runs.
- Keep the 6-hour staleness rule: a feed answer is stored per hour regardless of its round age, so it never triggers
  for feeds; it only bites on writer gaps.
- Add a `daily_mean` basis for `amount` without `hourly_amounts` (PUMP's supply drop, today `legacy_no_hourly`):
  amount × mean of the day's 24 chain prices, when all 24 are present.
- A view change is a migration, but expand-only (CREATE OR REPLACE VIEW with the same columns, new basis value). The
  report must accept a new `usd_basis` value. prices.ts:182 maps unknown bases to `legacy`, so an old release reading
  the new view stays safe.

### 2.4 Report basis
- `priceBasisOf` (prices.ts:182-185) / `listFlowUsd` (:192-203): drop the `pricedHourlyAtIngest` gate once `value` is
  re-valued (2.5). Otherwise 2,112 rows in the window keep `value` regardless.
- `compareUsd` (:228-265) keeps the within/beyond split only as a proof tool. `HOURLY_SERIES_DAYS` is CoinGecko-specific.
- incomeStatement.ts:1016-1021: the flows text and `source` label change (priceBasis.source from `coingecko` to the
  chain method). parity.ts:51 and the soak parity file expect a moved price on 12 assets.

### 2.5 Existing data (decisions R2-D3, R2-D4, R2-D5)
- **`prices` coingecko rows** (12 refs, 91,199 rows, measured below): after the rebuild and the re-value, export then
  delete (the 0005 comment says the table is "deletable as a unit if a licence lapses"). `data purge` (src/db/purge.ts)
  covers observations only, so this needs a `prices` mode (`--prices --source coingecko`, dry run default, export file
  first, the same rules as purge.ts:10-25). Keeping them labelled (spec D3-B) is the rejected option.
- **`value` of flow rows** (D3-A "re-price stored flows"). Options:
  - (i) in place: `UPDATE observations SET value = <view usd>` per active `log_scan` USD row whose hours are all
    chain-priced, one transaction per day under the asset lock, old values exported first. Precedent: the in-place
    `fillObservationTokens` (src/db/observations.ts:351-359). Provenance needs a marker (e.g. `locator.repriced_at` /
    `code_version`).
  - (ii) supersede: insert a re-valued copy and set `superseded_by`. That is append-only but adds ~6.2k rows (183 d) or
    ~11.2k (all), new ids, and a provenance `method` for "re-priced".
  - *Recommend (i)*: smallest; ids are stable; the derived rates and the report read the same figure as the view. Then
    re-derive VVV `usage_index` (183 rows) and any `flow_annualized` USD rate (none stored on USD flows today: the 4
    stored derived rates are token-unit, measured below).
- **R2-D4 horizon:** rebuild 183 days (spec) or back to the oldest tokenised flow row, 2025-10-14 (396 days, ≈ 2.2×
  the calls). With 183 days, 4,721 `hourly` + 306 `legacy_unpriced` rows older than 182 days keep CoinGecko `value`:
  they would need deletion (outside every report window) to meet "nothing CoinGecko-derived stored". *Recommend
  full history*: every one of those rows has hourly buckets, so it re-prices fully, and nothing has to be deleted.
- **`price_usd` / `diem_price_usd` level rows from CoinGecko:** 482 + 51 `market_data` rows on 13 assets (AERO's 45
  pre-rebuild rows included). Once each YAML's source moves, `data purge <a> --metrics price_usd --source-type
  market_data` is allowed: purge.ts refuses only the live source's type. Consequence: `report yield --day D` for a
  past D before R2 then has no price level, and history starts on the release day (no level backfill path). Option:
  write daily `price_usd` level rows for past days from the rebuilt `prices` table (new small verb). Mike's call
  (R2-D5).
- **`legacy_no_tokens`:** AERO/HYPE/PUMP DefiLlama rows (R4-R6 scope, not CoinGecko). PUMP specifics in 2.6.
- **Token refs:** `UPDATE observations SET token_ref` from `coingecko:crvusd` (628 rows) to
  `eip155:1/0xf939e0a03fb07f59a73314e73794be0e57ac1b4e` (already a ref), and from `coingecko:yearn-crv` (395 rows) to
  yCRV `eip155:1/0xfcc5c47be19d06bf83eb04298b026f81069ff65b` (new tokens row, decimals 18). Then delete the two tokens
  rows (after their 8,641 + 8,444 price rows) and the `coingecko_id` values. Keep the column (expand-only) or drop it
  in R8.

### 2.6 PUMP / Solana
- Measured: no PUMP `prices` rows. Since 0005, `flow_usd.buyback` has 4 rows with `amount` (`legacy_no_hourly`, from
  2026-11-10) and 17 chain days without (2026-10-24 to 11-09, `legacy_no_tokens`, their tokens in the `flow_tokens`
  twin). Those 21 days are CoinGecko daily-mean priced (solana.ts:121-125, :157). There are 369 DefiLlama-history days
  (2025-10-20 to 2026-10-23): USD from DefiLlama, `flow_tokens.buyback` = USD / CoinGecko price, so **the token
  counts are CoinGecko-derived too**.
- Solana RPC has no historical account-state read, so a "pool reserves at slot" history can't be read backward. A past
  hour must come from swap transactions (signatures on the pool + parsed balances), which costs a lot per hour. Smallest:
  PUMP chain prices start on the release day (written hourly by the levels job). Re-price the 21 chain days from swap
  txs only if the per-token scoping shows it's cheap; otherwise mark them `legacy`, labelled. The 369 history days
  belong to R6 (deleted with the DefiLlama history).

### 2.7 Daemon / ops: today and the proposed `op: 'prices'`
- **Today:** schedule.yaml has `nightly` 00:45Z (stage 02:45Z), `levels` hourly :15 (stage every 6 h), retention 03:30Z,
  disclosure_watch 16:40Z, staging_refresh Sun 10:30Z (stage). Hourly prices are written only inside `refresh` jobs
  (transfer_flow, flow.ts:484-491). The `levels` job writes `latest_levels.price_usd` from `/coins/markets`, and the
  nightly writes a `price_usd` observation. One serial worker, lowest `priority` first (jobs.ts:15-17: refresh 10, nightly_report
  20, snapshot_push 30, levels 40, ..., backfill 70), claim order priority, run_after, id (jobs.ts:122-132).
- **`backfill` today** (src/daemon/jobs/backfill.ts): per asset (`assetId` required, :146), params `{op:'fetch', metrics,
  backfillDays}` only (:52-76; `BackfillParams` jobs.ts:28-33), under the asset run lock (:163), never retried
  (MAX_ATTEMPTS 1). Guard `backfillWaitUntil` (:86-98): closed from nightly−4 h (`BACKFILL_CLEARANCE_MS`) to nightly+2 h
  (`BACKFILL_DEFER_AFTER_MS`), then waits in 15-min steps while that slot's refresh/nightly_report are unfinished.
  Deferral is free: `deferJob` re-queues with `attempts − 1` (jobs.ts:181-188; daemon.ts:450-452). The comment at
  :136-137 says a backfill "must be sized to finish inside the 4 h clearance; nothing bounds it in code".
- **Proposed `op: 'prices'`:** params `{ op: 'prices', from: 'YYYY-MM-DD', to: 'YYYY-MM-DD', refs?: string[] }`, job
  `assetId` null (prices are cross-asset), so `parseBackfillParams` / `BackfillParams` become a discriminated union and
  the handler branches before `loadAsset`. Lock: a dedicated run-lock name `prices` (not an asset lock), so asset
  refreshes are not blocked. Their own `writeChainPrices` calls are idempotent upserts on the same PK.
  - **Resumable chunks:** the job works newest day first in a **time budget** (e.g. 20 min or N chain-days). It
    commits each chain-day (24 h × refs) in one transaction, then returns `{ status: 'deferred', untilMs: now }`. The
    same job re-queues at priority 70 behind any due `levels`/`snapshot_push`/`refresh`, so the hourly levels never wait
    more than one budget. Progress lives in `prices` itself (`storedPriceHours` per chain source), so a lost lease or
    a deploy (which fails a backfill, MAX_ATTEMPTS 1) loses at most one chain-day, and a re-queued job resumes.
    `backfillWaitUntil` applies unchanged, so it never runs across the nightly window. The `done` line reports rows
    per ref, the oldest hour reached, and failures (a pool or feed that didn't exist yet).
  - **Re-value as a separate verb**, run after coverage is complete: `data reprice <asset|--all> [--from] [--yes]`
    (dry run default, export first), queued as `op: 'reprice'` or run by the operator. Order in the release block:
    deploy 0008 → `job run-now backfill-prices --from 2025-10-13` (orion-remote: comma lists, no repeated flags) →
    `data compare-usd` per asset (proof: 0 `legacy_unpriced` on chain) → `data reprice --yes` → prices purge of
    `coingecko` → `data purge <a> --metrics price_usd[,diem_price_usd] --source-type market_data` (on Mike's go).
  - Stage first. While stage is on 0008 and prod on 0007, the Sunday `staging_refresh` refuses (different migrations),
    which protects stage's chain rows. After prod ships, a refresh brings prod's rows to stage. Size: ≈ 13k-28k
    multicalls, at a guessed 0.3-0.5 s each ≈ 1-4 h per env (estimate; measure on stage with a 3-day run first).

## 3. Measured on prod (2026-11-13)

### 3.1 `prices` per token ref and source (all `coingecko`; no other source exists)
| token_ref | symbol / cg id | rows | min ts | max ts | hours in last 183 d (of 4,392) |
|---|---|---|---|---|---|
| coingecko:crvusd | crvusd | 8,641 | 2025-11-18 | 2026-11-13 00:00 | 4,378 |
| coingecko:yearn-crv | yearn-crv | 8,444 | 2025-11-18 | 2026-11-13 | **4,181** (gaps → 3 `legacy_unpriced` yCRV rows) |
| eip155:1/0x1f98…f984 | UNI / uniswap | 5,569 | 2026-03-26 | 2026-11-13 | 4,378 |
| eip155:1/0x4e3f…2b | CVX / convex-finance | 5,569 | 2026-03-26 | 2026-11-13 | 4,378 |
| eip155:1/0x5149…ca | LINK / chainlink | 8,641 | 2025-11-18 | 2026-11-13 | 4,378 |
| eip155:1/0x5607…79 | SKY / sky | 8,641 | 2025-11-18 | 2026-11-13 | 4,378 |
| eip155:1/0xd1b5…b5 | sdCRV / stake-dao-crv | 5,554 | 2026-03-26 | 2026-11-13 | 4,363 |
| eip155:1/0xd533…52 | CRV / curve-dao-token | 8,641 | 2025-11-18 | 2026-11-13 | 4,378 |
| eip155:1/0xdc03…4f | USDS / usds | 8,641 | 2025-11-18 | 2026-11-13 | 4,378 |
| eip155:1/0xf939…4e | crvUSD / crvusd | 8,648 | 2025-11-17 17:00 | 2026-11-13 | 4,378 |
| eip155:56/0x0e09…82 | CAKE / pancakeswap-token | 8,641 | 2025-11-18 | 2026-11-13 | 4,378 |
| eip155:8453/0xacfe…bf | VVV / venice-token | 5,569 | 2026-03-26 | 2026-11-13 | 4,378 |
Total 91,199 rows (the spec's 90,335 was 2026-11-10; the nightly upsert keeps a rolling set). `tokens` also has
LIT (no cg id), PUMP (`pump-fun`, no price rows), `usd`. All `last_fetch` 2026-11-13 00:45-00:47Z (the nightly).

### 3.2 `flow_usd_v` bases, observed in the last 182 days (rows)
| asset | hourly | of which daily-priced at ingest (report → legacy) | usd_native | legacy_unpriced | legacy_no_hourly | legacy_no_tokens | view vs legacy, hourly rows |
|---|---|---|---|---|---|---|---|
| aero | | | | | | 182 (181 DefiLlama + 1 derived) | |
| cake | 364 | 122 | | | | | +0.126% |
| crv | 546 | 180 | | | | | −0.000% |
| cvxcrv | 1,274 | 419 | | | | | −0.133% |
| hype | | | 48 | | | 362 (DefiLlama af_buyback + revenue_proxy) | |
| link | 182 | 65 | | | | | −0.100% |
| lit | | | 683 | | | | |
| pump | | | | | 4 | 360 (178 buyback supply_burn_daily + 182 llama_revenue) | |
| sdcrv | 1,820 | 599 | | | | | −0.073% |
| sky | 364 | 130 | | | | | −0.009% |
| uni | 182 | 61 | | | | | +0.083% |
| vvv | 364 | 122 | | | | | +0.237% |
| ycrv | 1,089 | 414 | | 3 | | | −0.003% |
| **total** | **6,185** | **2,112** | **731** | **3** | **4** | **904** | |
- The "view vs legacy" column is (Σ view usd / Σ value − 1) over the hourly rows. Both sides are CoinGecko; this is the
  per-transfer vs hour-bucket method gap, not the chain gap.
- CoinGecko-priced at write time, in the window: all 6,185 `hourly` + 3 `legacy_unpriced` rows (`log_scan`,
  `price_coingecko_id`); the 4 `legacy_no_hourly` + 17 PUMP chain days (CoinGecko daily mean). Not CoinGecko: 731
  `usd_native` (Lighter/Hyperliquid dollars), DefiLlama `legacy_no_tokens` (R4-R6).
- All time: hourly 10,906 (4,721 older than 182 d), legacy_unpriced 309 (306 older, before the prices start), usd_native
  1,077, legacy_no_tokens 1,645, legacy_no_hourly 4. Oldest tokenised flow row: 2025-10-14.

### 3.3 `price_usd` level observations (all active)
| asset | market_data (CoinGecko) rows | first – last | other |
|---|---|---|---|
| aero | 45 | 2026-09-24 – 11-10 | 4 `contract_state` (on chain since 11-10) |
| cake 34, crv 37, cvxcrv 36, hype 49, link 31, lit 32, pump 31, sdcrv 36, sky 30, uni 34, ycrv 36 | | 2026-10-02…16 – 11-13 | |
| vvv price_usd | 51 | 2026-09-20 – 11-13 | 1 disclosure (09-18) |
| vvv diem_price_usd | 51 | 2026-09-20 – 11-13 | 1 disclosure (09-18) |
Total `market_data`: price_usd 482 (13 assets), diem_price_usd 51, circulating_supply 374 (10 assets, R3).
`latest_levels.price_usd`: 12 assets `api/market_data` (CoinGecko), AERO `onchain/contract_state`; published hourly.

### 3.4 Other
- `coingecko:` token refs on observations: ycrv `flow_usd.fees` 232 (crvusd), `flow_usd.yearn_revenue` 396 (crvusd),
  `flow_usd.yearn_styc_fee` 395 (yearn-crv).
- Flow rows per ref (active, all time / 183 d): crvUSD 3,049 / 1,830 (crv, cvxcrv, sdcrv, ycrv); CRV 4,025 / 2,013
  (cvxcrv, sdcrv); CAKE 788 / 366; VVV 464 / 366; LINK, SKY, USDS 390 / 183; UNI, CVX, sdCRV 232 / 183; PUMP 4 / 4.
- Stored derived rates in 183 d: link `released_rate` 34, lit `routed_to_prime_rate` 103, sky `treasury_net_payout` 34
  (all tokens_per_year, not priced), vvv `usage_index` 183 (USD, from CoinGecko-priced `flow_usd.burn_programmatic`).

## 4. Decisions to bring to Mike (proposed, with recommendation)
- **R2-D1 config home:** central `prices.yaml` by token ref (rec.) vs per-asset `prices:` block.
- **R2-D2 view rule:** chain-only with `legacy_unpriced` fallback (rec.) vs chain-first with CoinGecko fallback.
- **R2-D3 stored `value`:** re-value in place with an export (rec.) vs supersede rows vs leave `value` (fails D3-A).
- **R2-D4 horizon:** full history back to 2025-10-13 (rec.; ≈ 28.5k multicalls est.) vs 183 days plus deleting the
  5,027 older rows.
- **R2-D5 CoinGecko `price_usd` level rows:** purge (history of the level restarts on the release day) vs purge plus
  synthesize daily `price_usd` rows from chain `prices` for past report days.
- **R2-D6 PUMP:** chain prices from the release day; 21 chain days re-priced from swap txs or labelled legacy; history
  days wait for R6.
- **R2-D7 price checks:** where the method is the Chainlink feed (CAKE, LINK, UNI, probably CRV/CVX/crvUSD/USDS), the
  `type: price` check against that same feed becomes circular. Replace it with a pool spot (`chain.cl_pool_spot_price`).

## 5. Risks
- **Silent mixed basis** if the view keeps a CoinGecko fallback while the rebuild runs (avoid with R2-D2 chain-only).
- **Value moves outside the window:** growth reads 2 × 91 days, so the sign-off table must cover both windows and every
  priced line (skill lesson: Task 8 moved the prior window by 0.3-1.9%).
- **Method gap:** per-transfer → hour-bucket pricing changes `value` by up to ±0.24% (3.2) on top of the chain-vs-
  CoinGecko gap. Report both separately in the proof.
- **Thin pools / depegs:** a TWAP on a thin pool, or a Curve wrapper pool (cvxCRV/sdCRV/yCRV) trading at a discount,
  is a real price, but it differs from CoinGecko's aggregate. Feeds with 24 h heartbeats give step prices. Each needs
  an independent check and a stated depth.
- **Pre-existence:** pools and feeds may not exist at the rebuild's start (e.g. the CVX, UNI, sdCRV, VVV CoinGecko
  series only start 2026-03-26 here). Each ref needs its earliest valid hour; earlier hours stay `legacy_unpriced` or
  use a second method.
- **Solana** has no past state (2.6).
- **Archive cost / Alchemy quota** is shared with prod's nightly scans. Run outside 05:00-06:30 PT and the
  nightly−4 h/+2 h window (the guard does this).
- **Config hash:** a central `prices.yaml` must feed each asset's config hash, or a method change escapes provenance.
- **staging_refresh** copies prod's `prices` into stage: after the R2 prod deploy, check it doesn't bring back
  CoinGecko rows that stage already purged (order the purges per env).
- **A deploy fails a running backfill** (MAX_ATTEMPTS 1, lease lost). Chunked commits make that cheap, but the
  operator must re-queue it.
- **Site licence:** `latest_levels.price_usd` (CoinGecko) is published hourly today. R2 is the release that stops it.

## 6. What each per-token scoping must supply (method config fields)
For each token ref: CRV, CVX, crvUSD, USDS, SKY, UNI, LINK, sdCRV, yCRV (replacing `coingecko:yearn-crv`), CAKE (BNB),
VVV (Base), PUMP (Solana). Level-only refs: HYPE, LIT, cvxCRV, DIEM, and AERO (done).
1. `token_ref` (CAIP chain/address, lowercased), symbol, decimals, chain id, and whether a flow uses it (rows in 183 d
   from 3.4).
2. `method`: `chainlink` | `peg_feed` (stable, the feed of its peg) | `pool_twap_x_feed` | `wrapper_pool_x_ref`
   (cvxCRV/sdCRV/yCRV: wrapper/CRV pool × CRV ref) | `share_price_x_ref` (yv/st vaults) | `first_party` (HYPE
   candles, Lighter) | `solana_pool`.
3. Feed: address, decimals, heartbeat, deviation threshold, the function (`latestRoundData` / `latestAnswer`), and
   whether it reads through Multicall3 (SKY's Chronicle pip reverts).
4. Pool: address, type (Uniswap v2 / v3, Aerodrome v2 / Slipstream, Curve stableswap-ng / cryptoswap, PancakeSwap v3,
   PumpSwap), base/quote side or Curve indices i/j, the read (`currentCumulativePrices`, `observe`, `price_oracle()`,
   `get_dy`, `last_price`, `slot0`), TWAP seconds, quote token and its USD ref/feed, depth (TVL, date measured).
5. Earliest valid hour (pool creation / feed launch block) against the rebuild start (2025-10-13, or 2026-05-14 for 183 d).
6. Independent check: a different pool or feed, never the same pool; tolerance %.
7. Archive availability and the measured call cost for one day (24 hours) on our RPC, and compute units if Alchemy.
8. Dev-only reference: gap vs CoinGecko's stored hourly rows on a sample of hours (median and p90 %), labelled
   dev-only.
9. For share-valued members: the underlying contract name (`share_price.underlying`) that replaces
   `price_coingecko_id`.
10. Known traps: depeg history, a pool migration in the window, rebasing, a fee-on-transfer token, a Chronicle/Multicall
    revert, and Base's 0.2 s blocks for the hour-block lookup (chains.ts `blockTimeSec`).
