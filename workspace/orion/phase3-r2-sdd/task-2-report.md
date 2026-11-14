# Task 2 report: EVM price-method readers

Status: DONE. Commit `1d8e9bd feat(prices): EVM price methods read in one multicall per chain-hour` (on 7b75080).

## What
- `src/prices/types.ts` (Ruling R3): `HourPrice`, `PriceDeps`, `SolanaPriceTransport` (interface only; results typed `unknown` for Task 4 to narrow), `WriteResult` (the plan's Task 3 shape).
- `src/prices/evmMethods.ts`:
  - Pure decoders: `sideOf`, `reserveTwap` (Aerodrome `currentCumulativePrices`), `sqrtPriceInQuote` (moved out of evm.ts), plus `uniV2Cumulatives` (UQ112x112 counterfactual fold from `blockTimestampLast` via `getReserves`, uint32 time, mod 2^256), `uniV2Twap`, `toSigned`.
  - `callsFor(m, at, ctx): HourCall[]`: each call carries `at: 'start' | 'end'`. `decode(m, raw, at, ctx, quoteUsd, feedUsd): MethodRead` returns `{usd, detail}` or `{usd: null, reason, detail}`. Reasons: `call_failed`, `quote_missing`, `zero_liquidity`, `bad_read`, `not_positive`. Every EVM kind in prices.yaml is covered: chainlink, curve_oracle (with/without index), curve_get_dy (dx, `/(1-fee)`), v2_twap uniswap and aerodrome, v3_twap, v3_spot, v4_spot, bound.
  - `priceHourEvm(rpc, entries, at, opts?: { feeds?, cache? })` returns `{ prices, feedUsd, checks, missing }`.
    - One multicall at B(H+1h) holds every primary, check and feed. When a v2 TWAP is present, the same call set is also read at B(H). With a shared `BlockReadCache`, the older hour then finds its end block already read, so the cost is 1 multicall per chain-hour (tested).
    - Refs are resolved in quote order. A missing quote gives no row and `missing` reason `quote_missing` (Review Focus 2).
    - `feedUsd` holds every feed read, keyed by the lowercased address. `opts.feeds` adds extra feeds (Ruling R5).
    - `checks` holds the EVM check reads of entries whose primary is off-chain (LIT v4_spot).
  - `withCheck(entry, primary, checkRead): HourPrice` is exported so Task 3/4 can combine LIT's Lighter primary with its v4 check. The gap is (check-primary)/primary*100. For `bound`, it is the distance outside [min,max] as % of the bound, 0 inside. A check that was not read gives `checkGapPct: null` and `detail.check.skipped = <reason>`. The `check` label is `methodSource(check)` plus `:<label>` when the check has one (e.g. `chain:bound:no_independent_check`).
  - Feed age: `detail.feed_age_s = end.timestamp - updatedAt`. A stale feed is still priced (Review Focus 3).
- `src/ingest/adapters/evm.ts`: `side`, `v2TwapPrice` and `clSpotPrice` now call the moved decoders. Error messages and detail strings are unchanged, and the AERO/evm adapter tests are unchanged and green.

## Tests (TDD)
- RED: `npx vitest run tests/prices/evmMethods.test.ts` failed with "Failed to load url ../../src/prices/evmMethods.js" (Test Files 1 failed, no tests).
- GREEN: 16/16 in tests/prices/evmMethods.test.ts.
  - CAKE 1.74948 with the v3 check (negative tick cumulatives that cross zero), 1 multicall.
  - cvxCRV 0.41377 x 0.2335 = 0.09662 through crvUSD -> CRV, plus the get_dy check.
  - SKY Uniswap v2 TWAP with the fold: 0.055. Without the fold it would be 0.0317.
  - The token1 side via price1Cumulative.
  - VVV 19.4017 via Aerodrome x ETH/USD, then DIEM quoted in VVV.
  - DIEM with VVV's call failing: neither is in the map.
  - Cache: 3 multicalls over 2 hours.
  - LIT v4: value 3.3573, and zero liquidity gives skipped `zero_liquidity` with null gap.
  - sdCRV bound: +5% above, -16.67% below, 0 inside.
  - LINK feed 23,760 s old: priced, `feed_age_s` 23760.
  - Every usd_feed pool method in prices.yaml has a quote token.
  - AERO v2 + slot0 check.
- Mutation checks: disabling the v2 fold fails 2 tests. Dropping the signed decode of tick words fails the CAKE test.
- Focused: tests/prices + tests/assets/aero.ingest + tests/ingest/adapters.evm: 55/55.
- Full suite: `npx vitest run --maxWorkers=2`: **1785/1785 (147 files)**, i.e. 1769 + 16. Nothing failed, so nothing needed a rerun. `npm run typecheck` is clean. `npm run lint:promises` is clean.

## Self-review / design decisions (please check)
1. **Quote tokens for usd_feed pool methods.** The v2, v3 and v4 decoders need the quote token's decimals, and v4 also needs its address for currency ordering. prices.yaml names only the feed. I added a code table `QUOTE_TOKENS` keyed by (chain id, feed) for the 6 feeds in use: WETH/USDC/USDT on Ethereum, USDT (18 dec) on BNB, WETH/USDC on Base.
   - The addresses are canonical deployments from my own knowledge. Only Base USDC is confirmed elsewhere in the repo; no network was used.
   - For v2 and v3, the pool's `token0()`/`token1()` are read in the same multicall every hour and must match the priced token and that quote, otherwise the read is `bad_read`. A wrong table row therefore prices nothing rather than mispricing.
   - v4 cannot verify its currencies (StateView exposes no pool key), so LIT's side relies on address order against the table's USDC.
   - A usd_feed pool method with no table row is refused with an `OrionError invalid_price_config`, and a test checks that every one in prices.yaml has a row. The alternative was a `quote_decimals`/`quote_token` field in prices.yaml, which is Task 1's file.
2. **v3 `observe`.** The transport returns one non-negative integer per call, and `observe` returns `(int56[], uint160[])`. I read it with an 8 × uint256 signature: the raw ABI words, with tickCumulatives[0..1] at words 3 and 4. The signed values are recovered by two's complement. This needs no change to rpc.ts or viemRpc.ts, but it depends on the exact ABI layout of two length-2 dynamic arrays. The mean tick is used as a float (not floored as OracleLibrary does); the difference is ≤0.01%.
3. **Signatures differ from the brief's sketch.**
   - `callsFor` and `decode` take a `MethodCtx` (chain id, token address, decimals, quote-ref decimals).
   - `decode` returns a miss object with a reason rather than `null`.
   - `priceHourEvm` returns `{prices, feedUsd, checks, missing}`: R5's shape plus `checks` and `missing`.
   - Feeds are 8 decimals as prices.yaml documents. `decimals()` is not read.
4. **B(H) reads.** Whenever a chain has a v2 TWAP, the full call set is also read at B(H). Without a cache that costs 2 multicalls per hour on Ethereum and Base. The writer (Task 3) should pass a `BlockReadCache` across consecutive hours and prune it to the last block, because the cache keeps every block it is given.
5. **Data-derived failures are misses, not throws**: a reverted call, zero reserves, or a wrong pool lists the ref in `missing` and leaves the other refs of that chain-hour unaffected. Config errors throw (`OrionError`).
6. `curve_get_dy` takes the decimals of coin i from the priced entry and those of coin j from the quote ref's entry.

## Concerns
- The QUOTE_TOKENS table (decision 1): its addresses were not checked on chain in this task. A controller probe or a prices.yaml field would settle it.
- The raw-word decode of `observe` (decision 2) has not been run against a live RPC. A one-call probe at a real block would confirm it, together with viem's decoding of the 8-word signature.
