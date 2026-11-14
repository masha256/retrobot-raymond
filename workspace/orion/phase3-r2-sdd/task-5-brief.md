### Task 5: The chain-only view and the report basis

**Files:**
- Modify: `src/db/pg/migrations/0008_chain_prices.sql` (append the view), `src/db/prices.ts` (`listFlowUsd`, `priceBasisOf`, `compareUsd`), `src/report/incomeStatement.ts` (priceBasis labels), `src/report/parity.ts`
- Test: `tests/db/prices.test.ts`, `tests/report/*` goldens

**Interfaces:**
- Produces: `CREATE VIEW flow_usd_chain_v` with `flow_usd_v`'s columns, the price lateral restricted to
  `(starts_with(pr.source, 'chain:') OR starts_with(pr.source, 'first_party:'))`, `ORDER BY pr.ts DESC`, the 6-hour
  rule, and basis `daily_mean` (`hourly_amounts` null, `amount` not null, 24 chain hours priced in the day:
  usd = amount x avg). `type PriceBasis = 'hourly' | 'daily_mean' | 'usd_native' | 'legacy'`; `priceBasisOf(usdBasis: string): PriceBasis`
  (gate removed; `HOURLY_SERIES_DAYS` and `pricedHourlyAtIngest` deleted).

- [ ] **Step 1: Failing tests**: a row with CoinGecko rows only reads `legacy_unpriced` in the new view and `hourly` in
  the old one (old view untouched); with chain rows it reads `hourly` at the chain price; a CoinGecko row newer than the
  chain row is ignored; PUMP-style row with 24 chain hours -> `daily_mean`, with 23 -> `legacy_no_hourly`. Report
  goldens: priceBasis text and `source` show the method (`chain:chainlink` etc.); re-pin only the price-basis keys.
- [ ] **Step 2-4: FAIL, implement, PASS** (full suite: goldens may move only on priceBasis keys; any other key is a stop).
- [ ] **Step 5: Commit** `feat(prices): chain-only flow USD view (0008) and the report basis without the ingest gate`.

