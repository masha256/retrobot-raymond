# Task 4 report: first-party and Solana price methods

Status: DONE. Commit `27a6ff1 feat(prices): Hyperliquid, Lighter and PumpSwap price methods` (on a4d49c7).

## What
- **`src/prices/offchainMethods.ts`** (new):
  - `priceHourOffchain(deps, entries, hourMs, usdcUsd, checks?)` returns `{prices, missing, calls}` (the R15 shape). `usdcUsd` is a number, null, or the writer's chain-1 `feedUsd` map, looked up by each method's `usd_feed` (R5). When there is no value it returns `quote_missing` and reads nothing.
  - **HYPE**: the `candleSnapshot` close of `@107` (`{coin, interval:'1h', startTime, endTime}`) × USDC/USD. The check is the perp `HYPE` candle close, labelled `first_party:hyperliquid:same_venue`. A missing spot candle gives `no_candle`. A missing perp candle leaves the check unread (`skipped: no_candle`).
  - **LIT**: the close of Lighter `/api/v1/candles?market_id=2049&resolution=1h&start_timestamp&end_timestamp&count_back` (≤500 a call; `/candlesticks` is never called) × USDC/USD. The check is the v4 `MethodRead` the writer already reads on chain 1 and passes in `ctx.checks` (writer.ts had that wiring already, with a test). Zero liquidity gives `skipped: zero_liquidity`.
  - **Per-run candle cache.** It is a WeakMap keyed by the deps object, which the writer makes once per run. An hour that is not covered fetches back from it as far as one request reaches: 5,000 h on Hyperliquid, 500 h on Lighter, never before `valid_from`. So the writer's hour-by-hour walk costs 1 request per coin per run on HYPE, and ceil(hours/500) on LIT.
  - **PUMP (M5)**, for the bucket [H, H+1h):
    1. `slotAt(H+1h)` (the first produced slot at or after it), then `blockSignature(slot)` as the seek cursor.
    2. `getSignaturesForAddress(quote_vault, {before: seek, limit: 100})`, paging back with `before` = the last signature of the page (at most 10 pages). Failed signatures are skipped without being fetched.
    3. `getTransaction(sig, {encoding:'json', maxSupportedTransactionVersion: 1})`.
    4. Price = USDC vault / PUMP vault, from `postTokenBalances`. Keys are resolved through the static keys plus `loadedAddresses`, and the vault mints are checked.
    5. `last_swap_age_s` goes in detail. The hour is refused (`stale_swap`) once the signatures reach more than 6 h before H+1h, and the age is known from the signature list, so no transaction is fetched for that. `no_swap` is returned when the history or the read budget (8 tx) runs out. An hour past the finalized head gives `no_block_yet`.
    6. The Meteora check reads pair `9SMp…KoZj` the same way from the same seek signature. Its price is the execution price from the reserve deltas of the token accounts the pair owns (fee included). A non-swap tx (both deltas the same sign) is skipped. At most 6 tx are read; after that `no_swap` is returned and the check is unread.
  - `priceRangeOffchain(deps, entry, from, to, usdAt(feed, hourMs), checkAt?)` returns `{prices: Map<hourMs, HourPrice>, missing, calls}`. It covers the candle venues only: HYPE takes 1 request per coin per 5,000 h, LIT 9 calls for 183 days.
  - **`livePriceOffchain(deps, entry)`** reads the Ethereum head with one `priceHourEvm` multicall, which gives the USDC/USD feed and also LIT's v4 check. The levels are:
    - HYPE: `allMids['@107']` (check `allMids.HYPE`).
    - LIT: the order-book mid from `/orderBookOrders?market_id=2049&limit=1`.
    - PUMP: one `getMultipleAccounts([base_vault, quote_vault, pair])`. The check is Meteora's active bin, (1+bin_step/1e4)^active_id, read from the lb_pair bytes (active_id@76, bin_step@80, token_x_mint@88, token_y_mint@120); the mints are verified and the price inverted if the pair is reversed.
- **`src/ingest/transport/solana.ts`** extended (it already had a reusable JSON-RPC client, so no `solanaRpc.ts`):
  - `SolanaRpcError` carries the RPC code. The message is unchanged, so the existing tests still pass.
  - `SOLANA_SLOT_SEC = 0.215`.
  - `solanaPriceTransport(http, url)` refuses a `*.pump.fun` host (`forbidden_price_host`, R8) and counts `stats.requests`.
  - `slotAt` makes a first estimate at 0.215 s from the nearest known slot, re-estimates from the measured spacing, then interpolates and bisects. It steps over skipped slots (-32007/-32009), returns null past the finalized head (-32004), and remembers its probes as anchors for later hours.
- **`src/prices/types.ts`**: `SolanaPriceTransport` is narrowed, with typed results, `slotAt` returning `number | null`, an optional `stats`, and **one added method, `blockSignature(slot)`**. That method is needed for the "signature from the block at the hour" step.
- **`src/prices/writer.ts`**:
  - Registers `hyperliquid`, `lighter` and `solana` (one `offchainChain` wrapper).
  - `makePriceDeps` now builds the Solana transport over `f.http` from `ORION_SOL_RPC_URL`, with no public fallback (R8). With http but no URL, every Solana read refuses `no_rpc_url`. With no http it still gives `no_price_transport`, as before.

## Tests (TDD)
- RED: `npx vitest run tests/prices/offchainMethods.test.ts --maxWorkers=1` failed with "Cannot find module '../../src/prices/offchainMethods.js'" (Test Files 1 failed, no tests).
- GREEN: 18/18 in `tests/prices/offchainMethods.test.ts`:
  - **HYPE**: 89.035/89.372 gives a gap of +0.3785%. A 4,431-hour range takes 2 requests (one per coin), with the gap hour and the unread perp check. `quote_missing` is returned with no fetch. The live `allMids` read works.
  - **LIT**: 3.354 against v4 3.3573. The zero_liquidity and not_read cases. 183 days take exactly 9 `/candles` calls. The live book mid (3.3547/3.3577) against v4 at the head takes 1 multicall.
  - **Solana transport**: `slotAt` is exact against a brute-force first slot. The fake chain's true slot is 0.2148 s and every 53rd slot is skipped. Each search takes ≤14 requests, a time past the head gives null, and `stats` equals the HTTP count. A pump.fun host is refused.
  - **PUMP 0.0035042 (33 s lag) against DLMM 0.0035093** (+0.146%):
    - The seek block is exactly the first slot at or after 14:00. Both cursors use its signature, the swaps after the hour are excluded, and failed signatures are never fetched.
    - Every `getTransaction` uses version 1. The fake answers -32015 otherwise, as measured.
    - A swap 2 h old is priced with its age. One older than 6 h gives `stale_swap` with 0 getTransaction.
    - Paging: `before` = the 100th signature of a page full of bot failures.
    - A DLMM with no swap leaves the check unread (`no_swap`). The `no_block_yet` and `quote_missing` cases.
    - The live vaults and the active bin take 1 getMultipleAccounts.
  - **Registry**: the three entries are present. 3 hours of HYPE take 2 requests in total (the run cache). `calls` is reported. Solana returns `quote_missing` when there is no feed.
  - **makePriceDeps**: `ORION_SOL_RPC_URL` is wired, and `no_rpc_url` is returned without it.
  - **R8**: an `afterAll` asserts that no request in any fake HTTP transport of the file went to a pump.fun host.
- Mutation checks. Each of these failed at least one test:
  - maxSupportedTransactionVersion 0 (4 failed);
  - page size 50 (1);
  - no 6 h refusal (1);
  - slot estimate 0.4 s (1, the request bound);
  - failed signatures not skipped (3);
  - non-swap DLMM tx accepted (2);
  - no run cache (1);
  - no pump.fun guard (1);
  - Lighter 1,000 per call (4).

  A no-op control kept 18/18.
- Focused: tests/prices plus the Solana adapter and PUMP ingest tests, 94/94. **Full suite `npx vitest run --maxWorkers=2`: 1827/1827 (150 files)** = 1809 + 18, with no load timeouts. `npm run typecheck` and `npm run lint:promises` are clean. `python3 -m unittest scripts/provision/test/test_orion_remote.py`: OK.

## Departures (please rule)
1. `SolanaPriceTransport` gains `blockSignature(slot)`, and `slotAt` returns `number | null`. The brief's 4-method interface cannot reach the "signature from the block at the hour" step without the first, and null means no finalized slot yet.
2. `priceHourOffchain` and `priceRangeOffchain` return `{prices, missing, calls}`, not a bare Map, as R15 does for the registry. `priceRangeOffchain` takes `usdAt(feed, hourMs)` and `checkAt?`, because USD conversion needs the feed of each hour.
3. PUMP signatures are read on the **quote vault** (`68Vd…dr8t`), not on the pool account `2uF4…oiSd`. Every swap writes the vault, prices.yaml carries no pool field, and config.ts is not in my file list. Liquidity adds and removes on the vault keep the ratio, so they price correctly too.
4. `livePriceOffchain(deps, entry)` reads USDC/USD itself at the Ethereum head (no parameter), together with LIT's v4 check, in one multicall.

## Concerns
- **The Lighter `/api/v1/candles` reply shape and the unit of its query timestamps are not in hype-lit-pump.md.** The code sends ms and accepts `c[]{t,c}` (the compact shape) or `candlesticks[]{timestamp,close}`; a t in seconds is scaled. It assumes `t` is the candle start. If Lighter stamps the candle end, every LIT hour would shift by 1 h. The same applies to `/orderBookOrders` (`bids[0].price`/`asks[0].price`). Both are unverified until Task 10's live proof. A one-request check on the prod host would settle them.
- The Meteora check finds the pair's reserve accounts by `owner == pair` in the token balances. That holds for DLMM reserves, but it is not measured in the scoping file.
- The candle cache is keyed on the deps object. A long-lived caller that reuses one `PriceDeps` across days keeps closed hours cached, which is harmless (they are immutable) but grows by about 1 entry per hour per coin.
- The writer still reports `missing` without its `detail` (writer.ts collect keeps reason only). So `stale_swap`'s `last_swap_age_s` reaches the WriteResult only as the reason. For priced rows the age is stored in the row's detail.
