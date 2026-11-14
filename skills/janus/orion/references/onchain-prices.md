# On-chain and first-party prices (no CoinGecko): methods, checks, traps

Use when adding or changing a token's price in `prices.yaml`, building a price reader, or explaining a price gap.
Orion's rule: no live CoinGecko/DefiLlama read; CoinGecko only as a labelled dev-only reference in probes.

## Picking the method (per token ref, one primary + one check)
1. Chainlink `<token>/USD` feed (`latestRoundData`, 8 decimals) when its heartbeat is short (1 h) or the token is a tight stable.
2. Feeds with a 24 h heartbeat / 1-2% deviation (CRV, CVX, SKY) give a STEPPED hourly series: make the deepest pool primary
   and the feed the check (pool medians sit ~2x closer to the market).
3. Wrappers (cvxCRV/sdCRV/yCRV): Curve wrapper/CRV pool `price_oracle()` (EMA) x the CRV ref.
4. Pools quoted in WETH/another token: TWAP x that quote's feed (Aerodrome VVV/WETH x ETH/USD), or chained through
   another ref (DIEM/VVV x VVV). Chained refs are priced in dependency order in the same hour's read; a missing quote
   = no price, never a stale quote.
5. Off-chain: Hyperliquid spot candle, Lighter spot candle, PumpSwap vault reserves; each x Ethereum USDC/USD of the
   same hour (price chain 1 first each hour and hand its feed values to the other chains).
- The check must not be computed from the primary's own pool/feed. When the primary becomes the Chainlink feed, an old
  "price vs Chainlink" check turns circular: move it to a pool.
- A token with no second venue of real depth (sdCRV: ~$430 pool) gets a sanity bound in quote units, labelled
  `no_independent_check`; a same-venue check (HYPE perp vs spot) is labelled `same_venue`. Tell Mike both labels.
- `valid_from` = the first hour Orion needs (oldest flow row / oldest price_usd row to rebuild), not the method's
  birth: history on Solana costs ~8-15 requests per hour. But it can never be earlier than the first hour every
  contract the method reads exists: find the token's and each pool's creation block (binary-search `eth_getCode`
  non-empty between two blocks) before setting it. An asset's history start is not its pool's: after a token
  migration the priced address and its pools can be weeks younger than the asset's oldest rows, so every hour before
  creation is a `call_failed` re-read on every run, and those older price levels cannot be rebuilt (refused rows stop
  the release). Raise those to Mike as a decision (keep/delete/price the predecessor token) before the release.
- Never estimate a historical block as `head - days x blocks_per_day`: chains change block time (Base sped up), so the
  estimate lands at the wrong date. Read the block's timestamp, or use the stored `hour_blocks` row.
- Measure archive reach before promising a history horizon: one multicall per chain at the horizon's first hour
  reading every primary, check and feed (non-zero answers).

## Check outcomes never open anomalies
A level `cross_checks` mismatch opens a `cross_check_mismatch` anomaly, which starts a paid triage run on prod. So hourly
price checks are stored on the `prices` row (`check_gap_pct`) and alerted as `ORION WATCH <env> price ...` lines; keep
level price cross-checks only where the asset already had one, and make "no reading" (e.g. zero liquidity) a skip,
not a source failure (which would build a failure streak).

## Hour semantics
Row `ts = H` prices [H, H+1h) and is read at B(H+1h) = first block at or after H+1h; v2 TWAP between B(H) and B(H+1h).
Pass one block-read cache across consecutive hours (B(H+1h) of hour h = B(H) of hour h+1), so a v2 chain costs N+1
multicalls for N hours, not 2N. Search each hour's block from the previous hour's block with a first-guess step
(Base: 2 s blocks before block 53,556,128, 0.2 s after; a nominal-rate search costs ~21 getBlock per hour).

## Venue facts and traps (re-verify with one probe before relying on them)
- **Uniswap v3 `observe([3600,0])`** returns 8 words: offsets 64/160, len 2, tickCumulatives at words 3-4 (int56,
  two's complement as uint256). Mean tick -> 1.0001^tick, mind token0/token1 side and decimals. Low-cardinality pools
  revert on 1 h observe at some hours.
- **Uniswap v4** has no oracle: read `getSlot0(poolId)` / `getLiquidity(poolId)` via StateView
  (Ethereum 0x7fFE42C4a5DEeA5b0feC41C94C136Cf115597227); skip the check when in-range liquidity is 0 (a zero-liquidity
  pool shows a stale price ~99% off).
- **Lighter** `/api/v1/candles?market_id=&resolution=1h&start_timestamp=<ms>&end_timestamp=<ms>&count_back=N` ->
  `{c:[{t,o,h,l,c,v,...}]}`; `t` is the candle START and the newest candle is the still-open hour: price closed candles
  only (t + 1h <= now). `/candlesticks` is 403. Live mid from `/api/v1/orderBookOrders` (price strings, best ask/bid).
- **Hyperliquid** `candleSnapshot` serves only the newest ~5,000 hourly candles (rolling): write any history you need
  before it falls out of the window.
- **PumpSwap**: price = USDC vault / PUMP vault. The PUMP mint and vault are **Token-2022** (programId TokenzQd...).
  Past hours: slot at the hour (slots ~0.215 s), a signature from that block as the `before` cursor of
  `getSignaturesForAddress` on the quote vault, `getTransaction(..., {maxSupportedTransactionVersion: 1})`, reserves from
  the first swap's `postTokenBalances` (accountIndex resolves over accountKeys + loadedAddresses). Read only our own
  Solana RPC, never a pump.fun endpoint (its terms bar automated access).
- **Meteora DLMM** LbPair (904 bytes): active_id i32 @76, bin_step u16 @80, token_x_mint @88, token_y_mint @120,
  reserve_x @152, reserve_y @184. The pair OWNS spam token accounts (a second USDC account), so take reserves from the
  LbPair's reserve keys, never "owner == pair". Live price = active-bin price (1 + bin_step/1e4)^active_id x
  10^(dec_x - dec_y), NOT the reserve ratio; history = a swap's execution price from the reserve deltas.
- Any check priced from ONE swap's execution (Meteora history, last-trade checks) needs a minimum notional: dust
  swaps (a few raw USDC units) round to absurd prices and give check gaps of 10^5 %, i.e. false WATCH breaches. Skip
  to the previous qualifying swap, or no reading when none is in the window.
- Finding a Solana pool address: `getProgramAccounts` with memcmp on the mint is refused by the provider (scan limit);
  look the address up once from a pool directory as a dev-only reference, then verify owner program, mints and bin
  step on chain.
- Decimals and quote-token addresses an implementer "knows" must be read on chain (decimals(), symbol()) before review.

## Proving a price swap on the prod copy (before the release)
1. Copy `prices.yaml` into BOTH proof homes from each side's own config source (see `subagent-execution.md`).
2. Old and new homes share ONE schema: save the old release's baseline reports (D, D-91, default day) BEFORE writing
   any chain price, and diff old vs new at that point too; it isolates the method change (per-transfer vs hourly view)
   from the price-source change. Expect zero numeric diffs there.
3. Smoke one day for all refs first, then size the full rebuild from its per-chain call counts; plan estimates were
   ~3x low (BNB/Base block search dominates). Run the full rebuild with a stop time clear of prod's nightly (shared
   RPC key); a driver that calls `writeChainPrices` in 10-min budgets resumes for free (stored hours are skipped).
   Per-run `missing` lists repeat across resumed runs: count from the DB, not by summing them.
4. Read the result from the DB: per ref rows, check-gap median/p99/max, over-tolerance counts, and chain vs CoinGecko
   (dev-only reference) by month. A month where CoinGecko diverges while both independent chain sources agree is a
   CoinGecko fact to report, not a reader bug (confirm `hour_blocks.block_ts` is on the hour first). A ref with few
   rows -> check contract creation (valid_from rule above); a giant max gap -> look at the check's `detail` for dust.
5. Dry runs for every asset (compare-usd, reprice, rebuild-price-levels, purge-prices), then `pg_dump -n <schema>`
   before any `--yes`, so the apply can be redone after fixes. Report per-metric old->new sums, refused, skipped by
   reason, remaps, derived recomputes and inactive CoinGecko rows.

## Re-pricing stored history (release side)
Adding chain prices does not change stored `value`: re-value in place from the chain-only view (`data reprice`), with an
export first, derived rows (e.g. VVV usage_index) recomputed over every repriced day (not only days whose value changed
in this run: an interrupted run otherwise leaves derived rows stale for good), a non-zero exit when rows are refused, and
the CoinGecko token refs remapped to address refs before pricing. Tell DefiLlama-era rows apart by the adapter's own rule
(PUMP: days before the first stored supply reading), and skip them with a reason rather than refusing them.
