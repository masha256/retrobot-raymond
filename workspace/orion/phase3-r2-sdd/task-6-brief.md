### Task 6: Writers switch: flows, levels, `price_usd`, PUMP burn

**Files:**
- Modify: `src/ingest/flow.ts` (drop `loadPrices`/`priceAt`/series; `value` = Σ hourly_amounts[h] x chain price(h)),
  `src/ingest/tokenBackfill.ts` (price part deleted), `src/ingest/adapters/solana.ts` (`supply_burn_daily` USD =
  tokens x the day's mean chain price; no `market_chart`), `src/levels/levels.ts` (after the level reads, `writeChainPrices`
  for the hours since the newest stored hour, capped at 48 h, every ref in `prices.yaml`; `/coins/markets` only for
  `circulating_supply` ids), `src/daemon/daemon.ts` (`sharedHttpCache` removed), `assets/*.yaml` (12 assets + AERO's ref)
- Create: adapters `price.token` and `price.token_check` (in `src/ingest/adapters/price.ts`, registered; `ADAPTER_SOURCE_TYPES` rung + `ADAPTER_ENDPOINTS` line, regenerate `docs/ops/sources-register.md`)
- Delete: `src/prices/coingeckoHourly.ts`
- Test: `tests/ingest/flow*.test.ts`, `tests/levels/*.test.ts`, every asset test, `tests/agent/golden/*`, `tests/report/golden/*`

**Interfaces:**
- Consumes: Tasks 1-5.
- Produces: `price.token { ref }` (live price by the ref's primary at the run block or live first-party read) and
  `price.token_check { ref }` (its check), used as each asset's `price_usd` source and cross-check; VVV
  `diem_price_usd` the same with the DIEM ref. `type: price` checks of CAKE/LINK/UNI point at `price.token_check`.
  `transfer_flow` members: `price_coingecko_id` removed from the schema (refused by name, three-place test as in the
  skill's "Retiring a config key"); a share-priced member names `share_price.underlying: <contract>`.

- [ ] **Step 1: Failing tests**: a nightly scan with chain prices for every hour writes `value` = the bucket sum; a
  missing hour withholds the day (as today's missing CoinGecko point); the scan makes no CoinGecko request (fake http
  asserts none); levels writes the last completed hour for every ref and alerts once per breach run; `price_coingecko_id`
  refused at load, at proposal filing and at approve; PUMP burn USD = tokens x mean of 24 chain hours, refused if fewer.
- [ ] **Step 2-4: FAIL, implement, PASS.** Re-pin asset hashes and goldens: values may move only on USD figures and
  priceBasis/provenance keys; list every moved golden key in the report.
- [ ] **Step 5: Commit** `feat(prices): flows, levels and price levels read chain prices; CoinGecko price reads removed`.

