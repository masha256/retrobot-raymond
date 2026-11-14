## Global Constraints

- No live read of CoinGecko or DefiLlama is added. After this release no code path reads a CoinGecko **price**
  (`/coins/markets` stays only for `circulating_supply`, which is R3). CoinGecko in tests/probes only as "dev-only reference".
- Migration 0008 is expand-only (no `-- breaking` line): `orion-2026.11.12.1` must still run on schema 8. `flow_usd_v`
  is not altered; the new view has a new name.
- Nothing CoinGecko-derived is kept after the release block runs: `prices` rows with `source = 'coingecko'`, the
  `coingecko:*` token refs, `market_data` `price_usd`/`diem_price_usd` rows, and `value` of every re-priceable flow row.
  A row that cannot be re-priced is listed, never silently kept (Task 9 dry run; Mike decides).
- Value moves allowed: USD figures move by the chain-vs-CoinGecko gap and the per-transfer -> hour-bucket method gap
  only. Token amounts, supply, grades and every non-USD field are unchanged. The proof (Task 10) is a signed per-asset
  table over both growth windows; anything outside it is a stop.
- Out of scope: `circulating_supply` (R3), the DefiLlama revenue series (AERO R4, HYPE R5, PUMP history R6, CRV R7),
  dropping `tokens.coingecko_id` and the `coingecko` source type (R8).
- Tests: `export ORION_TEST_DATABASE_URL='postgresql://orion_dev@/orion_test?host=/var/run/postgresql'`;
  `npx vitest run --maxWorkers=2`, load-sensitive files rerun alone at `--maxWorkers=1`; `npm run typecheck`;
  `python3 -m unittest scripts/provision/test/test_orion_remote.py`. RPC in tests only through `fakeRpc({ callsAt })`
  and a fake Solana/HTTP transport; no network in any test.
- Commit with explicit `git add <paths>`; never `-a`. Implementers never use the network, ssh, a `.env`, or a live DB.

## Plan decisions (Mike's "All recommendations", 2026-11-13; his go on the plan covers P1-P6)

Mike's decisions (#orion-dev 2026-11-13), recorded in the spec Status:
- **M1** CRV, CVX, SKY: the deep pool is the hourly primary, the Chainlink feed its check (24 h heartbeat feeds step).
  LINK, UNI, CAKE, crvUSD, USDS stay feed-primary.
- **M2** sdCRV: no independent check exists (second pool ~$430); a sanity bound 0.3-1.0 CRV, labelled `no_independent_check`.
- **M3** VVV = Aerodrome v2 VVV/WETH 1 h TWAP x ETH/USD, check Uniswap v3 VVV/USDC; DIEM = Aerodrome v2 DIEM/VVV TWAP x
  VVV's chain price, check Slipstream DIEM/USDC. The pool list is fixed (no dated switch to the Aero CL pools in R2).
- **M4** Re-price the full flow history (hours from 2025-10-13), not 183 days.
- **M5** PUMP: re-price its 21 on-chain burn days from PumpSwap swap transactions; the 369 DefiLlama-era days wait for R6.
- **M6** HYPE and LIT: current price; no flow needs history.
- **M7** CoinGecko `price_usd`/`diem_price_usd` level rows: rebuild each from the new prices, then purge.
- **M8** Terms: proceed; Hyperliquid/Lighter exclude US persons (noted in the spec), PUMP read only through our own
  Solana RPC, never a pump.fun endpoint.
- **M9** PUMP check = Meteora DLMM PUMP/USDC bin-20 (amends D9's "Raydium").
- **M10** Check tolerances: CRV 1.5%, CVX 2.5%, SKY 2.5%, LINK 2%, UNI 2%, CAKE 2%, stables 0.5%, cvxCRV/yCRV 3% for 2
  consecutive hours, VVV/DIEM 2%, HYPE 2%, LIT 3% (zero-liquidity hours skipped), PUMP 2%. CAKE/LINK/UNI checks move
  off their own feed onto pools.

Plan decisions (from `code-and-data.md` §4):
- **P1 Central `prices.yaml`** (repo root, beside `schedule.yaml`), keyed by token ref; asset YAMLs name refs, never
  methods. An asset's config hash includes the `prices.yaml` entries of every ref it uses (so a method change shows as
  "config" on that asset's provenance). Why not per-asset blocks: crvUSD is used by 4 assets, CRV by 3.
- **P2 Hour semantics.** A `prices` row with `ts = H` is the price of the bucket [H, H+1h), written once H+1h has a block.
  Every method reads at `B(H+1h)` = the first block at or after H+1h: a feed's answer, a Curve EMA, a v3 `observe`
  1 h TWAP ending there, a v2/Aerodrome cumulative TWAP between `B(H)` and `B(H+1h)`. First-party: the hourly candle
  of H (close). Solana: the pool reserves after the last swap before H+1h.
- **P3 New view, chain-only.** `flow_usd_chain_v` (same columns as `flow_usd_v`) reads only `chain:%` / `first_party:%`
  rows, newest at or before the hour start, no more than 6 h old; adds basis `daily_mean` (amount without hourly buckets,
  all 24 of the day's hours priced: amount x mean). The report reads it; the `pricedHourlyAtIngest` gate is removed.
- **P4 Re-price in place** (`data reprice`): `UPDATE observations SET value` per active flow row whose new view basis
  is `hourly` or `daily_mean`, one transaction per asset-day under the asset lock, old rows exported first, provenance
  `locator.repriced = { at, release, basis }`. The `coingecko:crvusd` refs become the crvUSD address ref and
  `coingecko:yearn-crv` the yCRV address ref (new `tokens` row, decimals 18) in the same pass. Stored `derived` rows
  computed from re-priced rows (VVV `usage_index`) are recomputed in the same transaction.
- **P5 Check outcomes are stored, alerted, never anomalies.** Each `prices` row carries `check_gap_pct` and `check`
  (the check's label); a breach (|gap| > tolerance for `consecutive` hours) is posted by the job that wrote it as
  `ORION WATCH <env> price <symbol> <ts>: <gap>% vs <check>` through `ctx.notify`. An anomaly would start a paid triage run.
- **P6 Writer cost.** One multicall per chain-hour, hour blocks cached in a new `hour_blocks` table and searched from the
  previous hour's block. Measured estimate (scoping): ~50k calls, ~1.1M Alchemy CU for the full rebuild; the proof
  (Task 10) measures the real count on the prod copy before the release block runs on stage.

## Review Focus

1. **A hour with no block yet / a chain halt / Base's 0.2 s switch (2026-11-05 block 53,556,128)**: the hour-block
   search must return the first block at or after H+1h on both sides of the switch and never write a row for an hour
   whose B(H+1h) does not exist yet. Pinned in Task 3.
2. **A ref whose quote ref has no price for the hour** (DIEM before VVV; cvxCRV before CRV; a feed outage): the dependent
   ref gets no row for that hour rather than a stale-quote row. Pinned in Task 2.
3. **A feed answer older than its heartbeat** at B(H+1h) (CRV/USD up to 6.6 h stale measured): stored with its age in
   the row's detail; it is a check input, never refused, because the feed is only primary where its heartbeat is 1 h or
   its peg is tight. Pinned in Task 2.
4. **A backfill interrupted by a deploy or lease loss**: re-queued job resumes from `prices` itself, never rewrites a
   committed chain-day, and never runs into the nightly window. Pinned in Task 7.
5. **A re-price over a row with a gap hour** (one hour missing among 24): the row is refused and listed, keeps its old
   `value`, and the dry run counts it. Pinned in Task 8.

---
