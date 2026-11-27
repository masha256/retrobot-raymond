# R4 scoping: code and data plumbing for an on-chain `pool_scan` AERO revenue source

Read-only, 2026-11-27. Repo `/home/hermes/git/orion` at main `2635cae`. No RPC, no network, no DB. Every claim is
backed by a `file:line` citation in this repo (MEASURED in code). Facts about chains that come from the vendored viem
package or the earlier scoping files are marked CLAIMED. Sizes: **S** < 50 LOC + tests, **M** 50-300, **L** > 300.

## Answer table

| # | Question | Answer | Code change? | Size |
|---|---|---|---|---|
| 1a | How an adapter `flow` is fetched and backfilled | The adapter returns `{kind:'daily_series', points: DailyPoint[], detail, token?}`. `fetchAsset` hands it to `writeApiFlow`, which writes one row per completed UTC day under cursor `adapter:<name>>metric`. It re-reads REVISION_DAYS=3 (the DefiLlama-only 30 does not apply) plus gap days. `--backfill-days` / a `backfill` job sets `ctx.backfillDays` and `rescan`. | No (reuse) | – |
| 1b | Existing USD-daily-on-chain adapter to copy | `solana.supply_burn_daily` is the only on-chain daily series that prices itself (it returns USD `value` + token `amount`). `lit.exchange_fees_daily` is first-party USD (`token: USD_TOKEN`). `transfer_flow` is not an adapter (it has its own scanner, flow.ts). | – | – |
| 1c | Pricing in v2 / `priceBasis` | The report re-prices each row from `flow_usd_chain_v`: `hourly` (tokens x hourly chain prices), `daily_mean` (amount x mean of 24 chain hours), `usd_native` (token_ref `usd`), else `legacy` = the stored `value`. A multi-token pool-fee USD sum has no single token_ref, so today it would show **`legacy`**, or `usd_native` if it is stamped `token: usd`. Both labels are wrong for "on-chain USD computed by the adapter". | Yes, a label: a new basis for pool_scan rows (TS-only) or a documented reuse of usd_native | S |
| 1d | Can an adapter store USD with an on-chain origin? | The rung `pool_scan` already exists (sourceTypes.ts:14, 22; purge SOURCE_TYPES; originOf → `onchain`). **But** `writeApiFlow` stamps every row `SERIES_ORIGIN='api'` and treats rows of any other origin as foreign conflicts. A pool_scan series would read back as `onchain`, see its own rows as conflicts and stall, and the adapterOrigins test fails. run.ts:621 also stamps derivations over adapter flows `api`. | **Yes**: make the series writer's origin come from the provenance | S-M |
| 2 | Multi-chain | CHAINS has Base, Ethereum and BNB only; viem has the same three. RPC is per asset (`ingest.rpc_url_env`). An adapter can already reach other EVM chains through `ctx.priceDeps.rpcFor('eip155:N')` (env map `PRICE_RPC_ENV`). Smallest design: add 5 CHAINS rows + 5 viem chains + 5 `PRICE_RPC_ENV` entries (or a shared `CHAIN_RPC_ENV`), and let pool_scan get its transports via `rpcFor`. No per-metric RPC config. | Yes | S-M |
| 3 | Block search, archive call, multicall | `firstBlockAtOrAfter` is interpolating and bracketing (rpc.ts:111-161; Base 2 s→0.2 s test at rpc.test.ts:77). Archive eth_call goes through `rpc.multicall(calls, block)` (evm.ts `readAt`). Each call returns **one uint** (`pickValue`), so `accumulators(pool)` costs one call per field. `readAll` / `readAt` send everything as **one** eth_call (viem `batchSize 100_000` bytes, 20 s HTTP timeout) with no chunking. `fakeRpc({callsAt})` gives per-block overrides keyed `addr.fn(args)[pick]`. | Yes: a chunked multicall helper; optionally struct reads | S |
| 4 | Income statement shape | Config-only shape that works today: **two revenue lines** (`voter_rev` = allocator share, `lp_rev` = gross − allocator), each `started: 2026-10-22`, with cost `lp_fees: of lp_rev` and holders `voter_fees: of voter_rev`. This is the CRV precedent (two revenue lines, each passed on whole), so unreconciled is exactly 0. A "revenue = gross metric, cost = own metric" shape loads, but cost and holder lines get **no `started` zero-fill or run-rate weight**, so they are null until 91 days exist. Below the line, a `metric` bribes line has the same problem and nulls holder flow. | Config for revenue/cost/holders. **Code** (S) for `started` on below_line lines, or keep bribes not_measured until 2027-01-21 | S |
| 5 | Short history | `started` zero-fills the revenue metric before the start, annualizes over own days (`W/n`), sets `daysMeasured` and `isNew` (<180 d). Growth: the prior window is all zeros → `change` = null, note "not meaningful". Once the prior window is partly filled (2027-01-21..04-22) growth is **inflated, and nothing labels it**. `growthExNew` = "every line is new". There is no explicit "shorter window" flag. Without `started` the line is null (windowSum needs every day). | Partly: growth guard + label | S |
| 6 | Deleting DefiLlama rows | `data purge aero --metric flow_usd.fees --source-type third_party --yes` deletes by stored `source_type` after a durable export to `$ORION_HOME/purged/`. It is refused on the live rung, an open anomaly, or a kept row whose `superseded_by` points into the set. The 2 `derived` rows (`manual_mean_of_neighbours@1`) are **not** caught by third_party. **Cleanest path: give the new series new metric keys.** `flow_usd.fees` then becomes a retired metric, and one `data purge aero --metric flow_usd.fees --yes` (no `--source-type`) deletes all 308 rows, both derived rows, and the DefiLlama cursor. There is no `rebuild_from` analogue for flows. | No | – |
| 7 | New-adapter checklist | Register in the adapters registry, `ADAPTER_SOURCE_TYPES` (`pool_scan`), `ADAPTER_ENDPOINTS` + regenerate `docs/ops/sources-register.md` (that test pins it), `validateParams`/`paramsDoc` (load-time), adapterOrigins test, aero hash pins ×2, packGolden aero holder-flow pin, v2 golden aero entries, rpc.test chain table. levels does **not** run flows. Jobs have **no wall timeout** (lease renewal), only the 20 s per-HTTP-request timeout, the nightly report's 3 h wait, and backfill gates (400 days, 1 attempt, nightly clearance). | Yes (checklist) | M |
| 8 | Proof tooling and carried items | flatdiff + per-release allowlist (R1-R3 pattern), `prod_copy.py`/`reports.sh`/`compare.py`. Release R4 items carried forward: the DefiLlama revenue series (r2-followups:286), dead API cursor (phase3-followups:169-171), purge export retention (:172-178), open anomalies keyed to removed sources (:179-182), the R43 growth-allowlist lesson, and the AERO parts of the phase2 check backlog (`coverage` check type unbuilt for pool_scan; report `coverage: null`). | New `r4-allowlist.json` + scripts | M |

## 1. Flow metric plumbing

**Fetch path.**
- `fetchAsset` (src/ingest/run.ts:209) builds the plan. Adapters are batched by `adapter:<name>` (sourceId.ts:23-24), but `adapterSource.fetch` runs `def.run` **once per request** (src/ingest/sources/adapter.ts:7-22).
  - So three metrics on one adapter means three full scans unless the adapter memoizes per run. Only HTTP has a run cache (`withRunCache`, run.ts:253). RPC has none.
- A primary that returns `daily_series` on a flow goes to `writeApiFlow` (run.ts:341-357), keyed `${batch.sourceId}>${metricKey}`.
- `revisionDays` is set only for `defillama` (run.ts:347). Adapters fall back to `REVISION_DAYS = 3` (apiFlow.ts:23).
- `backfillDays` precedence (run.ts:346):
  1. `--backfill-days`;
  2. otherwise the asset's `ingest.backfill_days` (aero: 100, assets/aero.yaml:23), but only when no cursor exists yet (`firstAdapterFlow`, run.ts:243-252);
  3. otherwise the default of 90.
- The adapter sees the window only as `ctx.backfillDays` (types.ts:124, run.ts:282). It never sees the cursor.

**writeApiFlow (src/ingest/apiFlow.ts:89-230).**
- It writes completed UTC days only. Each row is `observedAt` = day end with `periodDays 1` (196-206).
- It writes days `[cursor − revisionDays + 1 .. yesterday]` plus each gap day in the backfill window (106-119).
- A day missing from `points` is skipped, never zero-filled (180-183).
- **An empty `points` throws** (94). The adapter must therefore return at least one day every run, e.g. re-read yesterday.
- An unchanged value is left alone; a changed one supersedes the row (193-197).
- Conflicts: `findFlowConflicts(..., SERIES_ORIGIN)` (132) treats any active row whose origin is not `api` as a conflict (flow.ts:41-49).
  - Only `manual` conflicts are adoptable.
  - On a routine run, a manual row inside the revision window is honoured (133-140).

**Per-day interface.**
- `DailyPoint { day; value; slice?; amount? }` (src/ingest/types.ts:20-26).
- `SourceValue` `{ kind: 'daily_series'; points; detail; token?: TokenInfo }` (types.ts:48-53).
- `AdapterDef { name, needsRpc, paramsDoc?, validateParams?, run, computedFrom?, usdNative? }` (src/ingest/adapters/registry.ts:15-38). It is registered at registry.ts:80.

**Adapters to copy.**
- `solana.supply_burn_daily` (src/ingest/adapters/solana.ts:188-275, registered :294):
  - computes days itself and prices them from `ctx.chainHourPrices` (daily mean of 24 chain hours);
  - returns `value` = USD with `amount` = tokens and `token` = the mint ref (:268-274).
  - It is rung `contract_state` with `ADAPTER_ORIGINS: 'api'` (origin.ts:55), precisely so that it agrees with `SERIES_ORIGIN`.
- `lit.exchange_fees_daily` returns first-party USD with `token: USD_TOKEN` (lit.ts:310-311, usdNative :476).
- `transfer_flow` is not an adapter. `scanFlowGroup` (flow.ts) writes tokens + `hourly_amounts` and gets the `dayBlocks` cache (run.ts:492-496). Adapters get no day-block cache: `SourceContext` (types.ts:109-141) has no `dayBlocks`.

**Pricing in v2.**
- Stored `value` is the USD the writer computed. The report's statement series re-prices from view `flow_usd_chain_v` (src/db/pg/migrations/0008_chain_prices.sql:37-87; basis CASE :49-56).
  - `usd_native`: token_ref `usd`.
  - `hourly`: `hourly_amounts` and every hour priced.
  - `daily_mean`: amount, no hourly buckets, all 24 chain hours of the token priced.
  - `legacy_*`: everything else (`value` kept).
- These fold to `PriceBasis = 'hourly'|'daily_mean'|'usd_native'|'legacy'` (src/db/prices.ts:222-228; listFlowUsd :235-245).
- In the report (src/report/incomeStatement.ts:508-518), each line's `priceBasis` is the set of bases over 2W days → one label or `mixed`. A row without token columns is `legacy`.
  - Prod today: AERO's `fees` line is `"priceBasis": "legacy"` (prod/report-yield-aero-2026-11-27.json).
- Pool fees arrive in hundreds of pool tokens (scoping a-revenue-settlement.md §3: 224 tokens on Base, CLAIMED). One row holds **one** `token_ref`, so per-token amounts cannot be stored.
  - The adapter must price inside the scan and store USD directly.
  - That gives `legacy` (no token) or `usd_native` (if stamped `USD_TOKEN`). The `usd_native` comment says "a first-party API's dollars" (prices.ts:218, incomeStatement.ts:42), so it would be mislabelled.
  - **Change (S):** a fifth label, e.g. `onchain_usd`, chosen in `listFlowUsd` by `source_type = 'pool_scan'`. That is TS-only, no migration. An alternative is to stamp `USD_TOKEN` and amend the comments. It is Mike's call (open question O3).

**Provenance and origin.**
- Rungs: `contract_state, log_scan, first_party_api, pool_scan, disclosure, derived, constant, market_data, third_party` (src/report/sourceTypes.ts:10-19).
  - `pool_scan` is already a listing rung (:22). It is in purge's SOURCE_TYPES (purge.ts:38) and in the 0004 CHECK.
- `ADAPTER_SOURCE_TYPES` (sourceTypes.ts:31-63) has no pool_scan adapter yet. A missing entry makes `fetchedProvenance` throw `no_provenance` (locator.ts:122-123).
- `originOf` (src/provenance/origin.ts:68-89): `measured` + `pool_scan` → `onchain` (:78-80). `ADAPTER_ORIGINS` (:39-58) is consulted **only** for `contract_state`.
- **Conflict:** `writeApiFlow` stamps `source: SERIES_ORIGIN` = `'api'` (origin.ts:61; apiFlow.ts:208), and its stored-day lookup filters `o.source === SERIES_ORIGIN` (apiFlow.ts:77).
  - A pool_scan series' own rows would read back `onchain`: never "stored", always conflicts, non-adoptable → `skipped` with "nothing was written".
  - `tests/provenance/adapterOrigins.test.ts` (stampOf :39-49, mismatches :52-62) fails it.
- Required fix (S-M):
  1. `writeApiFlow` takes `own = originOf(fetchedProvenance(...))` for its stamp, its stored-day filter and `findFlowConflicts`;
  2. run.ts:621-625 counts an adapter input as `api` only when its origin is `api`;
  3. adapterOrigins' `stampOf` follows the same rule.
- Also `chainOfSource` (locator.ts:72-81) returns `null` for a pool_scan adapter (only `contract_state` gets the EVM chain). That is acceptable for a 7-chain read: put the chain list in the locator/slice.
- Per-day blocks: `writeApiFlow` writes `responseDigest(point.slice)` only (apiFlow.ts:204). Provenance `blockFrom/blockTo` (provenance/types.ts:34-35) needs a per-point extra if each row should cite its boundary blocks (S). Otherwise the blocks go in `slice` and `detail`.

## 2. Multi-chain

**Current rows.** `ChainInfo { id, name, maxLogRange, blockTimeSec, defaultRpcUrl, confirmations }` (src/ingest/transport/chains.ts:7-18).

| id | Chain | maxLogRange | blockTimeSec | Keyless default URL | Confirmations | Line |
|---|---|---|---|---|---|---|
| 8453 | Base | 2000 | 0.2 | mainnet.base.org | 9000 | :26 |
| 1 | Ethereum | 10000 | 12 | none | 64 | :28 |
| 56 | BNB | 50000 | 0.45 | none | 2000 | :34 |

- viem knows only `{base, mainnet, bsc}` (viemRpc.ts:7). Any other id throws `unsupported_chain` (:46-49).
- The RPC URL is per asset: `deps.env[ingest.rpc_url_env] ?? DEFAULT_RPC_URLS[chain_id]` (run.ts:229-233; IngestSchema src/config/sources.ts:132-137). There is one `ctx.rpc` per run.
- Escape hatches that exist:
  - (a) adapter params naming their own env var: solana `rpc_url_env` (solana.ts:17-19). Solana adapters set `needsRpc: false` and read over HTTP.
  - (b) **`ctx.priceDeps.rpcFor('eip155:N')`** (types.ts:140; makePriceDeps writer.ts:526-546), which resolves `PRICE_RPC_ENV[N]` (writer.ts:500: 1 ETH, 56 BNB, 8453 BASE) and caches one transport per chain.
  - `priceDeps` is set only when the asset loaded a prices.yaml (run.ts:281). The refresh job passes an unwrapped `priceRpcFactory` (run.ts:59-63).

**What each new chain needs.**
1. A CHAINS row. Fields:
   - `maxLogRange`: irrelevant to pool_scan (no getLogs).
   - `blockTimeSec`: only the block search's first estimate.
   - `confirmations`: the reorg-safe depth if `finalized` fails.
   - `defaultRpcUrl`: null (archive needed).
2. A viem chain in `VIEM_CHAINS`.
3. An env var.
4. The `rpc.test.ts` table tests (:106, :122).

If prices on that chain are ever written, also add `prices/config.ts` CHAINS (:89) and `PRICE_CHAIN_METHODS` (writer.ts:77-84).

The vendored viem 2.56.8 has `optimism` (10), `arbitrum` (42161), `ink` (57073), `robinhood` (**4663**) and `arc` (**5042**) (node_modules/viem/chains/index.ts:32, 36, 309, 469, 534; CLAIMED from the package). Re-measure `eth_chainId` before pinning. multicall3 is `0xca11…ca11` on all of them, with `blockCreated` OP 4286263 and Arbitrum 7654707, which are harmless for 2026 blocks.

Robinhood runs ~819k blocks/day, i.e. ~0.105 s blocks (a-revenue-settlement.md table, CLAIMED). Proposed values:

| Chain | Env var | blockTimeSec | Confirmations |
|---|---|---|---|
| OP (10) | `ORION_OP_RPC_URL` | 2 | 900 (~30 min) |
| Arbitrum (42161) | `ORION_ARB_RPC_URL` | 0.25 | 7200 |
| Ink (57073) | `ORION_INK_RPC_URL` | 1 | 1800 |
| Robinhood (4663) | `ORION_ROBINHOOD_RPC_URL` | 0.1 | 18000 |
| Arc (5042) | `ORION_ARC_RPC_URL` | measure | measure |

Ethereum is already present (`ORION_ETH_RPC_URL`). All of these need `.env` entries on stage and prod, i.e. a Mike action.

**Smallest design.**
- Keep `ingest` = Base (the run block, the levels).
- Give pool_scan per-chain transports through `ctx.priceDeps.rpcFor` after adding the 5 envs to `PRICE_RPC_ENV`. Better: rename it to a shared `CHAIN_RPC_ENV` used by both prices and adapters (S).
- The adapter takes `chains: [{ chain_id, factory, cl_factory, ... }]` in params, with contract names per chain (`contracts` is a flat name→address map: schema.ts:108).
- No per-metric `rpc_url_env`, and no schema change to `ingest`.
- `ADAPTER_ENDPOINTS` lists one `rpc` endpoint per chain/env (generate.ts:31, :62-64 pattern).

## 3. Block search, archive reads, multicall

- `firstBlockAtOrAfter(rpc, ts, anchor, latest, blockTimeSec)` (src/ingest/transport/rpc.ts:111-161):
  - the first probe is estimated from the anchor;
  - then it interpolates between bracket blocks on their own rate;
  - it steps back ≥2x after two probes past the target, bisects when a step does not halve the bracket, and allows 64 probes at most.
  - Fix commit 895c8a1 (Base 2 s→0.2 s) tests the change in tests/ingest/rpc.test.ts:77-97; there are irregular-chain cases at :65.
- `findHourBlock` (prices/writer.ts:96-121) is a 2-4 call variant from a neighbouring hour. `hour_blocks` stores B(H) per chain, and B(00:00) = the day boundary for Base.
- The flow scanner caches day boundaries in `day_blocks` (src/db/dayBlocks.ts:9-29) and caches only boundaries older than 3600 s (flow.ts:21, :251-256). Adapters cannot reach either cache (see §1). Add `dayBlocks?(chainId)` to SourceContext (S), or search 2 boundaries × 7 chains per run.
- Archive eth_call:
  - `evm.ts readAt(ctx, block, calls)` (:51-58) and `blockAt` (:74-77) are the pattern; `chain.counter_rate` reads `then`/`now` (:119-140).
  - `readAll` (adapters/chain.ts:19-26) does the same at the run block.
  - Both send **all calls in one** `rpc.multicall` → viem `client.multicall({allowFailure:true, blockNumber, batchSize: 100_000})` (viemRpc.ts:78-97). That is one eth_call up to ~100 kB of calldata, and the HTTP timeout is 20 s with 3 retries (:51).
  - **Chunk explicitly** (e.g. 300-500 calls). A ~1.9k-call snapshot for 934 Base pools × fee0/fee1 is plausibly heavy for one archive eth_call.
- Return shape: every call returns one unsigned integer (`CallResult`, rpc.ts:17-18). For a tuple return, `pick: i` selects the i-th value (rpc.ts:13-14; `pickValue` viemRpc.ts:21-29). Negative values are refused.
  - So `accumulators(pool)` → one call per field. viem's multicall decodes per call, so each `pick` is a separate sub-call: 2 fields = 2× calls.
  - Optional (S): a `multicallTuple` that returns all words.
  - `allPools(i)` / `allPoolsLength()` / `token0()` are fine. An address comes back as uint (evm.ts `side`, :95-101, compares addresses read as uint).
- `fakeRpc({ genesisTs, latest, blockTimeSec?, timestampOf?, calls, callsAt })` (tests/helpers/fakeRpc.ts:3-24, :94-103):
  - `callsAt(blockNumber)` returns per-block overrides keyed `callKey(addr, fn, args)` + `[pick]`;
  - `stats.multicall` / `getBlock` count calls.
  - It serves one chain. A multi-chain adapter test needs a `rpcFor` fake per chain.

## 4. Income statement v2: expressing AERO

**Schema** (src/config/incomeStatement.ts):
- Revenue line (:39-50): one of `metric` / `derived` / `disclosed` / `estimate` / `not_measured`, with optional `settlement` and `started`. `started` is allowed only with `metric`/`derived` (:246-248).
- Use lines, for cost (:83, `to`) and holders (:72-80): one of `metric` / `of` / `estimate` / `not_measured` (:260). `share` is constant (`share_metric` is a level, informational only: the report uses `u.share`, incomeStatement.ts:441).
- below_line (:89-103): one of `metric` / `run_rate` / `not_measured`, plus `to`. A measured line to holders needs `bucket`, `haircut`, `recipient_base` and `capture_rule` (:300-306).
- Validation:
  - a use line may not read a revenue metric directly: it must use `of` (:263-264);
  - a below_line metric may not be a revenue metric (:295);
  - no series is read twice (:197-201).

**Report arithmetic** (src/report/incomeStatement.ts):
- `of` → the revenue line's value × share, inheriting its `started` run-rate weight (:438-445; resolveUse :444-455).
- The holders `of` amount is the **whole revenue line × share**, never "minus costs". Gross profit = revenue − costs (:562-563).
- Unreconciled is exactly 0 when every use passes a revenue line on whole (:617-636).
- `started` zero-fill and `youngWeight` apply **only to revenue lines** (:354-375, :396). Cost, holder and below-line `metric` terms are `w: 1` (:443, :702). `windowSum` returns null on any missing day (holderYield.ts:123-135).

**Vote-incentive precedents.**
- CRV: `below_line vote_incentives { run_rate: vote_incentive_run_rate_usd, to: holders, bucket: cash, haircut: 0.03, recipient_base: locked, capture_rule: programmatic }` (assets/crv.yaml:200). It is a level from llama.box (:148-154), third_party.
- yCRV: a metric line apportioned by sender mix with a tight partition sum check (ycrv.yaml:202-215).
- sdCRV: a plain `metric: flow_usd.bribes` below_line line (sdcrv.yaml:221).

**Proposed AERO block. Config-only except `started` on below_line.**
```yaml
revenue:
  - { id: voter_rev, label: "pool fees to sAERO allocators (gauge accrual; PoolTape/CLPoolTape)", metric: flow_usd.voter_fees, started: "2026-10-22" }
  - { id: lp_rev,    label: "pool fees kept by LPs and ungauged pools (tape gross - allocator share)", metric: flow_usd.lp_fees, started: "2026-10-22" }
cost_of_revenue:
  - { id: lp_fees, to: lps, of: lp_rev }
holders:
  - { id: voter_fees, of: voter_rev, bucket: cash, haircut: 0.02, recipient_base: locked, capture_rule: contractual }
below_line:
  - { id: bribes, to: holders, metric: flow_usd.incentives, started: "2026-10-22",   # `started` here = code change (S)
      bucket: cash, haircut: 0.02, recipient_base: locked, capture_rule: programmatic, note: "VRM incentive programs streamed, third parties" }
  - { id: foundation_incentives, to: holders, metric: flow_usd.incentives_foundation, ... }   # optional: Foundation-funded programs held apart
checks:
  - { id: tape_gross, type: sum, total: [ flow_usd.pool_fees_gross ], parts: [ voter_rev, lp_rev ], tolerance_pct: 0.000001, tolerance_abs: 1 }
```
- Revenue = voter + LP = gross tape fees. Gross profit = voter share. Payout ratio is measured, and `scope` could become `complete`.
- `flow_usd.pool_fees_gross` (monitor-only, same scan) feeds only the sum check.
- Each part is its own metric from **one** scan (memoized, §1), like yCRV's `count_from` members.
- What needs code:
  - (i) `started` (or zero-fill + run-rate) on below_line, and on use lines with their own metric, if that shape is preferred (S: schema key + the same fill loop + tests).
  - (ii) Without (i), the bribes line must stay `not_measured` until ~2027-01-21. Otherwise `holderFlow.gross/net` go null: a measured below-line line with a null gross makes `sumOrNull(units)` null (:825-826).
  - The same applies to the optional foundation line.
- Holder-flow metrics change (`holderFlowMetrics`, incomeStatement.ts config :401-417) to `[flow_usd.voter_fees, flow_usd.incentives…]`. `tests/agent/packGolden.test.ts:93` pins aero to `['flow_usd.fees']` and must be re-pinned on purpose.

## 5. Short history

Behaviour with `started: 2026-10-22` (src/report/incomeStatement.ts):
- Days before `started` are filled with 0 over 2W (:356-365).
- `annualized` = windowSum × W/n, a run rate over its own days (:366-375, :396).
- Line out: `started`, `daysMeasured` (`measuredDays` = window days with a `measured` row when provenance is loaded, :503-507, :539), and `isNew` = age < `NEW_STREAM_DAYS` 180 (holderYield.ts:69; :540).
- `growthExNew` is null with no new line, else "every line is new" (:550-552).

Growth (`growthOf`, holderYield.ts:137-156):

| Period | Prior window | Growth shown |
|---|---|---|
| Release to ~2027-01-21 | all zeros | `change: null`, `annualized: null`, note "not meaningful: a window is zero or negative" (:153) |
| ~2027-01-21 to ~04-22 | partly pre-start zeros | **finite and inflated, unlabelled** |

The R43 lesson (phase3-proof README :150-156) bites here too.

- Without `started`, every figure is null ("needs 2W complete days", :151; windowSum :130).
- `provisional` is for periodic lines only (:484-489, :994). It does not apply.
- Tests:
  - tests/report/revenueStreams.test.ts:98-110 (young line annualized over own days, `daysMeasured 6`);
  - :68-96 (`isNew`, `excludedFromExNew`, `growthExNew.change 0`, prior includes pre-start zeros);
  - :158-174 (periodic started, `daysMeasured 5`, `isNew`);
  - tests/report/incomeStatement.test.ts:258-266 (`daysMeasured` from provenance).
- "Labelled shorter window" is partly there: the per-line `started` and `daysMeasured` exist. Missing (S):
  - a statement flag, e.g. `revenue window: 37 of 91 days (since 2026-10-22)`;
  - nulling or noting growth while the prior window overlaps pre-start days;
  - the same for holder-flow and below-line lines.

## 6. Deleting the DefiLlama rows

How `data purge` works (src/cli/commands/data.ts:288-304 → `purgeMetrics`, src/db/purge.ts:93-136):
- It is a dry run unless `--yes`.
- `--yes` takes the asset run lock + a tx, writes a fsynced export `$ORION_HOME/purged/<asset>-<metric>[+N]-<stamp>.json` (mode 600) **before** deleting, then deletes by stored `source_type` (:279-281). Superseded rows are included.
- Refusals:

| Code | Condition | Line |
|---|---|---|
| `purge_configured_metric` | configured metric without `--source-type` | :246-251 |
| `purge_live_source` | `--source-type` equal to the live rung | :252-261 |
| `purge_open_anomaly` | the metric has an open anomaly | :270-273 |
| `purge_dangling_reference` | a kept row `superseded_by` a deleted row | :318-326 |
| `purge_unreplaced_*` | `market_data` price/supply only | – |

- Side state (`latest_levels`, `watch_state`, cursor `…>metric` via NAMES_METRIC :236) is deleted only when the metric is **not configured and no row is left** (:294, :131-135).

The 2 rows (ids 11831 / 515, 2026-09-10, `formula manual_mean_of_neighbours@1`, source_type `derived`; phase2-followups.md:505):
- `--source-type third_party` does not catch them.
- They matter: prod's AERO provenance shows `derived` 1.14% of revenue today. The `started` zero-fill only fills days **without** a row (:362), so a leftover 09-10 row would be counted.

**Recommended sequence (no code change).**
1. Ship the new series under new keys (`flow_usd.voter_fees`, `flow_usd.lp_fees`, …).
2. `data purge aero --metric flow_usd.fees` (dry run, then `--yes`). The metric is retired, so no `--source-type` is needed, and every row goes: 306 third_party + 2 derived, superseded included. The DefiLlama cursor `defillama:aerodrome:dailyHoldersRevenue>flow_usd.fees` goes too.

The **purge must come before** relying on the report day. `lastCompleteReportDay` reads only configured revenue metrics (report/load.ts:131-143), so the leftover rows only matter if the key is kept.

If the key `flow_usd.fees` is kept instead:
1. Switch the source first (the live rung becomes `pool_scan`).
2. Purge `third_party`, then `derived`. If the 09-10 DefiLlama row is `superseded_by` the derived row, purging derived first trips `purge_dangling_reference`. Verify the chain direction on the prod copy.
3. Rows of other origins inside the backfill range would be non-adoptable conflicts for the new series (apiFlow.ts:142-153). So purge before the backfill.

There is no flow `rebuild_from` analogue (that is a level key for `circulating_supply`, assets/aero.yaml:61). On-chain history simply starts on 10-22.

## 7. New adapter checklist (repo conventions)

1. Code in `src/ingest/adapters/aero.ts` or a generic `pool.ts`. Register at registry.ts:80, with `needsRpc: true`, `paramsDoc` and `validateParams`. `validateParams` runs at load: config/load.ts:104 (refuses config proposals too).
2. `ADAPTER_SOURCE_TYPES[name] = 'pool_scan'` (sourceTypes.ts:31). Not `ADAPTER_ORIGINS` (contract_state only). Apply the origin fix from §1.
3. `ADAPTER_ENDPOINTS[name]` (tools/sources-register/generate.ts:82-119; a missing entry throws :267-268). Then `npx tsx tools/sources-register/generate.ts` to regenerate `docs/ops/sources-register.md`, which tests/tools/sourcesRegister.test.ts:9 pins.
4. Tests:
   - adapter unit tests on `fakeRpc({callsAt})` per chain;
   - `tests/provenance/adapterOrigins.test.ts` (every registered adapter is run there);
   - `tests/assets/aero.ingest.test.ts`: plan batches :127-131, a fake for `api.llama.fi` :70 to drop, the hash pin :101;
   - `tests/config/load.test.ts:367` (hash pin);
   - `tests/agent/packGolden.test.ts` (aero pack + :93);
   - `tests/report/v2Golden.test.ts` / `golden/v2-report-13.json` (aero entries);
   - `tests/ingest/rpc.test.ts:106-130` (chain table);
   - `tests/assets/r1-third-party.test.ts` stays green.
5. Hourly levels job:
   - It reads only level/schedule metrics (`levelMetricKeys`, src/levels/levels.ts:95-101; job src/daemon/jobs/levels.ts), so **no pool_scan RPC runs hourly**.
   - It also runs the chain price writer for every prices.yaml ref. Each new EVM ref costs ~1 multicall per chain-hour plus the hour-block search (2-4 getBlock), per evmMethods.ts:9-11 and writer.ts:96-121.
   - If pool_scan prices its own long tail, the hourly cost is unchanged.
6. Daemon: nightly `00:45Z`, levels `:15` hourly, retention 03:30 (schedule.yaml). One worker (daemon.ts:29-34).
   - Jobs have **no wall-clock timeout**: a 3 min lease renewed every 60 s (jobs.ts:55; daemon.ts:100, :462-483).
   - `refresh` gets 2 attempts with a 10 min retry (refresh.ts:21; jobs.ts:24-26).
   - The nightly report waits ≤ 3 h for refreshes (`NIGHTLY_WAIT_MS`, nightlyReport.ts:19).
   - So a slow AERO scan delays every later asset's refresh on the single worker. The binding limits are viem's per-request 20 s × 3 retries (viemRpc.ts:51) and the report's 3 h.
   - The routine daily cost is about 2 boundary snapshots: Base ≈ 2.5k + others ≈ 1.2k calls/day (a-revenue-settlement.md:80, CLAIMED). At ~300-500 calls per eth_call that is ~10-25 eth_calls, seconds of work.
7. Backfill job (`job run-now backfill <a> --metric … --backfill-days N`, cli/commands/job.ts:46-56 → daemon/jobs/backfill.ts):
   - only `op: fetch` on flow metrics, ≤ `BACKFILL_MAX_DAYS` 400 (:33, :80-103);
   - priority last (jobs.ts:16);
   - `max_attempts 1`; a lease lost on deploy fails it (jobs.ts:19-26);
   - it may not start within 4 h before or 2 h after the nightly, nor while that slot's refresh/report is unfinished (backfill.ts:20-29, :160-176).
   - The full 37-day backfill is one `fetchAsset` with `backfillDays` → the adapter scans all days in one run: ~38 snapshots × ~1.9k (Base) + others ≈ 100k+ eth_call sub-calls, minutes to tens of minutes. There is no budget/defer like the prices op (`PRICES_BACKFILL_BUDGET_MS`, :43); acceptable if chunked.
   - `data fetch aero --metric … --backfill-days N` (data.ts:239-256) is the same thing from the CLI.

## 8. Proof tooling and carried items

**Tooling.**
- `tools/phase3-proof/flatdiff.py <old> <new> --allow <allowlist> --asset <a>` flattens two reports and allows listed paths. Bounds: `rel`/`abs`/`ratio`, pins: `old`/`new`/`absent`. The README covers the format, the R2 classes (a)-(d), the R43 lesson, and R3 class S/L.
- Allowlists: r1 (AERO had no entry, `cmp`-identical), r2 (AERO class (a) only), r3 (AERO none).
- R3 release scripts: r3-s0..s4.sh, r3_check.py with `--fake` fixtures.
- `tools/phase2-proof/`:
  - `prod_copy.py` copies prod read-only into a `p2proof_*` schema over `sql-ro`;
  - `reports.sh` runs `report yield --day D --json` old/new;
  - `compare.py` gives byte parity (rel 1e-12) for the other 12 assets;
  - `cleanup.py` drops the schema.
- R4 needs:
  - `r4-allowlist.json`: the other 12 assets get none (cmp/compare parity). AERO is a before/after table, not an allowlist, since every revenue path changes.
  - AERO's before/after over D and D−91 is per spec §5 (spec :205-209).

**Carried to R4 / relevant open items (grep `R4`, `AERO`, `pool_scan`).**
1. "R4-R7: the DefiLlama revenue series (AERO R4 …) untouched by R2 (rows `skipped`, not repriced)" (docs/superpowers/notes/2026-11-13-orion-phase3-r2-followups.md:286-287).
2. Dead API cursor after a third_party purge of a still-configured metric. Suggested drop in R8 (phase3-followups.md:169-171). Avoided if the metric is retired (§6).
3. Purge export files per env have no retention or verb (phase3-followups.md:172-178). R4 adds one more per env.
4. Open anomalies keyed to removed sources need a manual sweep (phase3-followups.md:179-182). Check for AERO `flow_usd.fees` / defillama anomalies before the purge (`purge_open_anomaly`).
5. The R43 growth lesson: every growth entry needs abs AND rel (phase3-proof README :150-156; r3 plan :100). AERO's growth goes from 0.636 to "not meaningful".
6. Phase 2 check backlog: a `coverage` check (listed pools vs a protocol total) is "Phase 3"; the type exists (checks/schema.ts:53, evaluate.ts:112). The report has the field `coverage: null` "pool_scan lines, Phase 3: null today" (incomeStatement.ts:94-95, :539).
7. Spec §4 AERO requires coverage stated per chain (spec :166-172). Today there is nowhere to put it except `detail`/`slice` → small code or the coverage check.
8. R2 followup R21: AERO keeps its own `price_usd` adapters plus a prices.yaml entry (r2-followups:78-79). This is relevant if pool_scan prices AERO-denominated fees from `chainHourPrices('eip155:8453/0x3f5b…')`: `valid_from` 2026-10-22 (r2-followups:125-128) matches the history start.
9. AERO price history starts 2026-10-22 (r2-followups:301-304) and market cap 2026-11-10 (aero.yaml:58-61). Both are consistent with a 10-22 revenue start.
10. Phase 2 followups listed `pool_scan` among the "Phase 3 types" (phase2-followups.md:452). The "AERO 2026-09-09 manual day" correction remains (:241, :505).

Release-number-"R4" hits in the R3 followups (:22, :52, :65, :79) are **ruling** R4 (PUMP), not release R4.

## Proposed `pool_scan` layout

`src/ingest/adapters/pool.ts` (generic, rung `pool_scan`; asset-agnostic like `evm.ts`):
- **`pool.tape_fees_daily`**: a daily series (USD) for one `field` of one scan.
  - Params:
    - `chains: [{ chain_id, factory, cl_factory?, tape, cl_tape?, voter? }]`: contract names per chain;
    - `field: gross | allocator | lp | mev`;
    - `pricing`: `{ method: stable_pairs, quotes: [usdc_<chain>…], usd_feed }` or a list of refs;
    - `min_coverage_pct?`;
    - `days?` (default 3, the routine window).
  - Run:
    1. for each chain, find the day-boundary blocks with `firstBlockAtOrAfter` (or a `dayBlocks` cache);
    2. read `allPoolsLength`/`allPools(i)` at the end block (pools created mid-day read 0 at the start);
    3. chunked multicall `accumulators(pool)` [fee0, fee1] at both boundaries, plus gauge accrual for `allocator`;
    4. price each token on chain; the unpriced share is stated as coverage in `detail`/`slice`.
  - Returns ≥1 day always. Memoizes the scan per `SourceContext` keyed by params-minus-`field`, so the 3-4 metrics cost one scan.
- **`pool.vrm_incentives_daily`**: VRM `incentive(id)` programs streamed per day (USD). Params: `chains`, `exclude_payers?` / `only_payers?` (Foundation wallet held apart → a second metric with `only_payers: [foundation]`).
- Shared: `src/ingest/adapters/multichain.ts` with `rpcFor(ctx, chainId)` (over `ctx.priceDeps.rpcFor` / `CHAIN_RPC_ENV`), `chunkedMulticall(rpc, calls, block, size=400)`, and `dayBoundaries(ctx, chainId, days)`.
- Core changes:
  - chains.ts (+5 rows), viemRpc.ts (+5 viem chains);
  - `PRICE_RPC_ENV` → `CHAIN_RPC_ENV` (+5);
  - apiFlow/run origin fix;
  - the report basis label;
  - `started` on below_line;
  - the growth/short-window flag;
  - optionally `SourceContext.dayBlocks` and a struct-read multicall.
- Metrics (assets/aero.yaml), all `flow`/`usd`/daily:
  - `flow_usd.voter_fees` (critical) and `flow_usd.lp_fees`;
  - `flow_usd.pool_fees_gross` (monitor_only, check only);
  - `flow_usd.incentives`, and optionally `flow_usd.incentives_foundation`.
  - Remove `flow_usd.fees`, `external_ids.defillama` (R8 removes identifiers; leave it if R8 wants it) and the comment at aero.yaml:8.

## Open questions

- O1: Revenue = gross (voter + LP, the shape above) or allocator share only (+ incentives)? (scoping a-revenue-settlement.md:100). The answer decides `scope` and whether the LP line exists.
- O2: Keep key `flow_usd.fees` (two-step purge, cursor and conflict care) or new keys (one-step purge; packGolden/hash re-pins)? I recommend new keys.
- O3: Price-basis label for adapter-computed on-chain USD: new `onchain_usd` vs reusing `usd_native`/`legacy`.
- O4: Pricing method for ~224 long-tail tokens. Stable-pair routing inside the scan vs top-N tokens with stated coverage. What coverage threshold fails a day?
- O5: Bribes before 2027-01-21: build `started` on below_line (S) or keep `not_measured` until the window fills?
- O6: Should growth be nulled or labelled while its prior window overlaps pre-start zeros (2027-01-21..04-22)? This affects the report's headline.
- O7: Chain ids and block times for Robinhood (4663?) and Arc (5042?) must be MEASURED (eth_chainId, 1-day block span) before pinning. Stage/prod `.env` gets 5 new RPC vars (Mike).
- O8: One backfill run of ~37 days × 7 chains has no budget/defer. Is one long `backfill` job acceptable, or should the adapter cap days per run?
- O9: Where does per-chain coverage live: a `coverage` check (needs a "total" metric), the report's `coverage` field (code), or `detail` only?
- O10: The supersede direction between the 09-10 DefiLlama row and the derived corrections (11831, 515) matters only if the key is kept. Verify it on the prod copy.
