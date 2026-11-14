# Task 6b review (7063c22..661bf9c)

Reviewed in passes: src/assets/docs via `git diff`, the goldens by a flattening script (old vs new, every path), tests by
diff. Items E (AERO hash) and F (R22 cross-check scope, LIT zero-liquidity) are being fixed in parallel and are not re-raised.

### Spec Compliance

- ✅ Spec compliant for 6b (Ruling R18): `price.token` / `price.token_check` exist and are registered
  (src/ingest/adapters/price.ts:150-167, registry.ts:80). All 12 assets' `price_usd` now use `price.token`, plus VVV
  `diem_price_usd` (assets/*.yaml). CAKE/LINK/UNI `type: price` checks point at `price.token_check`
  (cake.yaml:147, link.yaml:148, uni.yaml:126). AERO is unchanged (R21). entriesFor builds from refs
  (src/prices/config.ts:268-283) and the symbol match is gone. The `ADAPTER_SOURCE_TYPES` / `ADAPTER_ORIGINS` /
  `ADAPTER_ENDPOINTS` entries are in, and the sources register is regenerated.
- ⚠️ Cannot verify from the diff: whether the parallel E/F fix wave keeps the bound-check semantics below once sdCRV's
  level cross-check is removed (R22 makes sdCRV's bound check writer-only).

### Named risks (each checked)

1. **Live price math: pass.** Every method family goes through `priceHourEvm` (EVM) and `livePriceOffchain`
   (off-chain). Nothing is reimplemented in price.ts (price.ts:86, :98).
   - Quote refs are closed transitively on the same chain (price.ts:57-68).
   - A cumulative TWAP starts at `firstBlockAtOrAfter(run block − 1 h)` (price.ts:81-82). Aerodrome is `v2_twap`
     flavor `aerodrome`, so it is covered.
   - Chained refs share one BlockReadCache per run.
   - **Probe I wrote** (rev worktree, `tests/review/t6bParity.test.ts`, copy in scratch/t6b/): it runs `price.token`
     at a run block exactly at H+1h and `writeChainPrices(..., [ref], H, H+1h, { dryRun: true })` on identical fake
     chains, and asserts `toBe` (bit-equal). All 6 cases pass with the same doubles:

     | Case | Value |
     |---|---|
     | LINK (feed) | 12.5 |
     | cvxCRV (Curve → CRV → crvUSD) | 0.09659999999999799 |
     | SKY (v2 TWAP) | 0.05840000000008762 |
     | VVV (Aerodrome TWAP) | 19.40169999999 |
     | DIEM (via VVV) | 417.13654999978496 |
     | sdCRV (Curve, bound) | 0.18680000000000002 |

   - Off-chain (HYPE allMids, Lighter book mid, PumpSwap reserves now) differs from the writer's candle close by
     design (R16), so no equality is expected there.
2. **Golden integrity: pass.**
   - v2-report-13: all 65 `input` strings are identical. Report JSON, flattened: exactly 2 paths moved in 60
     entries (12 assets × 5 variants):
     - `incomeStatement.priceBasis.source`: `market_data:coingecko` → `contract_state:price.token`
       (cake, crv, cvxcrv, link, pump, sdcrv, sky, uni, vvv, ycrv) or `first_party_api:price.token` (hype, lit).
     - `incomeStatement.priceBasis.sourceType`: `market_data` → `contract_state` / `first_party_api` (same split).
   - aero: 0 moves. No revenue, cost, holder-flow, yield, dilution, grade or price value moved.
   - v1-report-13: 0 paths moved.
   - packs-13: with the `price.*` adapter_params rows removed, all 13 packs are byte-identical to the old ones. The
     added rows are price_usd ×2 per asset, plus 2 more for vvv diem_price_usd. The 15 "changed" paths are index
     shifts in lit/pump.
3. **Provenance and rungs: pass.**
   - EVM and Solana methods map to `contract_state`; Hyperliquid and Lighter candles map to `first_party_api`
     (src/prices/venue.ts:31-44). LIT (an eip155 ref, chain `lighter`) gets `first_party_api` from its method, and the
     golden shows it.
   - The stamp follows the rung (price.ts:115). `originOf` maps first_party→api and contract_state→ADAPTER_ORIGINS
     `onchain`, so it agrees with the stamp for all 12 assets.
   - ADAPTER_ENDPOINTS (generate.ts:105-133) match the methods: LIT primary is Lighter + Eth RPC, its check is Eth RPC;
     PUMP is Solana + Eth; HYPE is Hyperliquid + Eth. The Jupiter TERMS row is gone.
   - `git grep 'type: coingecko' assets/` returns 9 lines, all `field: circulating_supply`.
4. **Checks: pass.**
   - CAKE/LINK/UNI compare the feed primary with their prices.yaml pool check (v3 TWAPs: CAKE/USDT, LINK/WETH,
     UNI/WETH). That is not circular.
   - The primary's own adapter is refused (schema.ts:389, tested).
   - sdCRV bound: inside the band, the check value is the primary exactly (gap 0 at tolerance 0). Outside, it is
     bound × quote USD, so the gap is the distance outside (price.ts:136-142; the probe and the existing test agree).
   - validateParams refuses unknown keys, a missing ref, and a ref not in prices.yaml (price.ts:41-46). There is a gap
     at proposal filing; see Minor 1.

### Strengths

- No duplicated price math. My probe confirms the live read equals the writer's stored value to the bit for every EVM
  family.
- Golden discipline is exact: two label paths, inputs untouched, packs identical modulo the new adapter rows.
- The rung comes from a load-time WeakMap note (venue.ts:68-88). That keeps the config hash and YAML untouched and still
  labels LIT correctly.
- `priceRpcFactory` stops a price read's other-chain head from overwriting the levels/refresh block capture
  (run.ts:57-62, levels.ts:207, refresh.ts:120).
- The tests use real decoders over fakeRpc results built per method (tests/helpers/livePrices.ts), not mocks of the
  adapter. RED evidence is recorded.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)

1. **src/agent/tools/write.ts:306: proposal filing does not refuse an unknown ref.** A config proposal is filed with
   `parseAssetObject(applyEditsToObject(raw, edits))` and no prices map. `price.token { ref: <typo> }` therefore passes
   at filing and is refused only at approve (src/app/proposals.ts:185 passes `loadPrices`). This breaks the contract in
   registry.ts:24 ("a config proposal and its approve refuse bad params"), and a human reviews a proposal that cannot
   be approved.
   - Fix: pass `ctx.loaded.prices`, and add a filing-refusal test.
2. **src/ingest/adapters/price.ts:111 (comment at :104): the "a later adapter retries" claim is false for EVM calls.**
   A failed read is dropped from READS, but the per-run BlockReadCache (price.ts:84-85) keeps the failed call results
   (Task 2's deferred minor). price.token_check's "retry" therefore re-decodes the cached failure without a new call.
   The behavior is harmless, but the comment and the report (§1) overstate it.
   - Fix: correct the comment, or skip `ok: false` entries in the cache.
3. **price.ts:84-85: one BlockReadCache per run, keyed by block number alone.** It is shared across chains (a ref read
   at another chain's head goes into the same map). A cross-chain collision needs the same block number and the same
   address and call, so it is unlikely, but the cache is not chain-safe. No repo asset hits this.
   - Fix: key the WeakMap by chain (`Map<chain, BlockReadCache>`).
4. **price.ts:99: off-chain `observedAt` is the run start (`ctx.nowIso`), not the fetch time.** The report (§1) says it
   is the fetch time. Either fix the code or the report.
5. **src/config/sources.ts:8: the schema still accepts `type: coingecko, field: price`.** Global constraint: "no code
   path reads a CoinGecko price". No asset uses it now, but a config proposal could reintroduce it and it would load.
   Dropping the `coingecko` type is R8 (out of scope); a cheap guard now is refusing `field: price` (with a test).
   Controller's call.
6. **sourceId is the adapter name, so VVV's `price_usd` and `diem_price_usd` share `adapter:price.token` (and
   `adapter:price.token_check`).** The cross-check anomaly keys include metricKey, so those are fine. But
   `source_failure_streak` (run.ts:627, `metricKey: ''`, `dedupeKey: sourceId`) merges a DIEM-only failure with VVV's,
   and its detail does not name the ref. Same pattern as other multi-metric adapters. Worth a note in the detail text.
7. **LIT's `price.token_check` reads its v4 check at the Ethereum head through priceDeps**
   (offchainMethods.ts:521-525), not at the run's `ctx.block`. Its venue still reports `rpc: true`. The check is
   therefore read at a slightly different block than the run's other LIT chain reads. This is acceptable, but the
   paramsDoc says EVM reads are "at the run block".

### Assessment

**Task quality:** Approved

**Reasoning:** The adapters reuse the writer's methods and give bit-identical prices for every EVM family at H+1h. The
goldens move only on the two priceBasis label paths (packs only on the new adapter rows). Rungs, origins, endpoints and
the register agree. The remaining items are a filing-time validation gap, comment and claim accuracy, and cache keying.
