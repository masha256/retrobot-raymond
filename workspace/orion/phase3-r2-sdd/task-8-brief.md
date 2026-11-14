### Task 8: `data reprice`, `data rebuild-price-levels`, `data purge-prices`

**Files:**
- Create: `src/db/reprice.ts`, `src/db/priceLevels.ts`
- Modify: `src/db/purge.ts` (prices mode), `src/cli/commands/data.ts`, `scripts/provision/files/orion-remote` (+ tests), `docs/ops/deploy.md`
- Test: `tests/db/reprice.test.ts`, `tests/db/priceLevels.test.ts`, `tests/db/purge.test.ts`, CLI tests

**Interfaces:**
- Produces: `repriceAsset(db, loaded, { from?: string; yes: boolean; now: Date }): Promise<RepriceResult>` with per-metric
  `{ rows, repriced, refused: { id, day, reason }[], oldSum, newSum }`; `--yes` exports first to
  `$ORION_HOME/repriced/<asset>-<UTCstamp>.json` (fsynced, as purge), then one transaction per asset-day under the asset
  lock; remaps `coingecko:crvusd` / `coingecko:yearn-crv` token refs (P4); recomputes the stored derived rows whose inputs moved.
  `rebuildPriceLevels(db, loaded, { yes })`: per `market_data` `price_usd`/`diem_price_usd` row, a new row at the same
  `observed_at` from the newest chain/first-party price with `ts <= observed_at - 1h`, method `derived`, locator
  `{ from: 'prices', token_ref, ts, source }`; refused (listed) where none exists.
  `purgePrices(db, { source: 'coingecko'; yes })`: export, delete those `prices` rows, then the `coingecko:*` `tokens`
  rows with no remaining reference; refuses while any active observation still has a `coingecko:*` ref.
  CLI `data reprice <a> [--from D] [--yes]`, `data rebuild-price-levels <a> [--yes]`, `data purge-prices --source coingecko [--yes]`; remote the same.

- [ ] **Step 1: Failing tests**: Review Focus 5: a row with 23 of 24 hours priced is refused, keeps its value, and is
  counted; dry run writes nothing (row counts equal); `--yes` twice is a no-op the second time; the export holds every
  old row byte-for-byte; `usage_index` rows recomputed equal `derived.ts` on the new values; `purgePrices` refuses
  before the remap and succeeds after it; `rebuildPriceLevels` then `data purge --source-type market_data` leaves every
  report day with a price level.
- [ ] **Step 2-4: FAIL, implement, PASS.**
- [ ] **Step 5: Commit** `feat(data): reprice stored flows, rebuild price levels, purge CoinGecko prices`.

