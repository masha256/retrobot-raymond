# Task 6b report: price_usd from chain/first-party methods on 12 assets; CoinGecko price reads removed

Status: DONE. Commit `661bf9c feat(prices): price_usd from chain/first-party methods on 12 assets; CoinGecko price reads removed`
(base 7063c22, 58 files, +1531/-284).

## What changed

1. **Adapters `price.token { ref }` / `price.token_check { ref }`** (src/ingest/adapters/price.ts, registered).
   - EVM ref: `priceHourEvm` (evmMethods.ts) over the ref plus its quote refs (primary and check, transitively; all on
     its chain), at `HourBlocks { start: first block at or after run block - 1 h (only when a v2/Aerodrome cumulative
     TWAP is among them, else the run block), end: run block }`. On the asset's ingest chain it uses the run's own RPC
     and block; another chain is read at that price chain's head through `ctx.priceDeps.rpcFor`. A ref with no price
     (quote missing, failed call) fails the reading naming the reason; a stale quote is never used.
   - Off-chain ref (HYPE, LIT, PUMP): `livePriceOffchain` (offchainMethods.ts), observedAt = the fetch time.
   - One read per run per ref (WeakMap on the SourceContext), shared by price.token and price.token_check, and one
     BlockReadCache per run (DIEM's read reuses VVV's calls). A failed read is not cached.
   - price.token_check: the check's USD from the same read; for `bound` (sdCRV) the primary itself inside the band and the
     nearer bound x the quote's USD outside it, so the cross-check gap (tolerance 0) is the distance outside; the detail
     names the primary in CRV, the band and the prices.yaml gap. A check not read (zero liquidity, error) fails the reading.
   - validateParams refuses any key but `ref`, a missing ref, and (when the loader has a non-empty prices.yaml) a ref not
     in it. `AdapterDef.validateParams(params, ctx?)` gained the optional `{ prices }` context, passed by parseAssetObject.
   - Stamp: `api` on a first-party venue (HYPE, LIT primaries), `onchain` otherwise, matching the rung.
2. **Rung / chain / RPC need per ref** (src/prices/venue.ts): EVM and Solana methods `contract_state`, Hyperliquid and
   Lighter candles `first_party_api`. parseAssetObject (given prices) notes each price source's venue on the parsed
   source object (a WeakMap; config and hash untouched); unnoted sources fall back to the ref's namespace.
   `typeOfSource` (sourceTypes.ts, `adapterSourceType`), `chainOfSource` (locator.ts) and `needsRpc` read it.
   `AdapterDef.needsRpc` may now be a function of the source (`adapterNeedsRpc`, used by plan.ts, run.ts, levels.ts):
   HYPE/PUMP/LIT's price.token need no asset RPC; LIT's check (v4 on Ethereum) does.
   ADAPTER_SOURCE_TYPES + ADAPTER_ORIGINS gain both names (contract_state / onchain as the no-ref default).
3. **Wiring**: SourceContext gains `prices` and `priceDeps` (run.ts: `makePriceDeps(env, { rpcFactory: priceRpcFactory ??
   rpcFactory, prices: loaded.prices, http: the run's cached http })`). New `FetchDeps.priceRpcFactory`: levels.ts and
   daemon/jobs/refresh.ts pass the unwrapped factory so a price read's Ethereum head never overwrites the fetch's
   block_number capture (refresh.ts: one-line change outside the file list).
4. **YAML** (12 assets; aero untouched): price_usd -> price.token + one price.token_check cross-check at the prices.yaml
   tolerance (CRV 1.5, cvxCRV 3, sdCRV 0, yCRV 3, SKY 2.5, LINK/UNI/CAKE 2, VVV 2, HYPE 2, LIT 3, PUMP 2); VVV
   diem_price_usd the same with the DIEM ref (cross-check added). Replaced checks: CAKE/LINK/UNI Chainlink contract_read,
   LIT orderBookDetails http_json, PUMP Jupiter http_json, VVV Venice vvv_stats price. CAKE/LINK/UNI `type: price` checks
   `against: price.token_check` (check id `price_chainlink` kept: stored check rows key on it); the `chainlink_*_usd`
   contract entries removed (nothing else referenced them). Comments updated.
5. **Checks** (src/checks/schema.ts): a `type: price` `against` may name the adapter of exactly one adapter cross-check
   of `level` (resolved as `{ kind: 'cross_check', contract: <name>, sourceId }`); the primary's own adapter is refused.
6. **R11** entriesFor: refs from price.token/price.token_check params (primaries and cross-checks), transfer_flow
   scanned tokens and `share_price.underlying`, plus quote refs; the symbol match and the every-contract scan are gone.
7. **levels.ts**: no code change to the prefetch (it already took every remaining coingecko id); comment updated; test
   pins that the 13 repo assets prefetch exactly the 9 circulating_supply ids and no asset names a CoinGecko price.
8. **Sources register**: ADAPTER_ENDPOINTS for both (by the ref's method in the repo prices.yaml: the price chain's RPC;
   Hyperliquid info / Lighter API / Solana RPC + the Ethereum RPC for USDC/USD); the Jupiter TERMS row removed (no reader);
   CoinGecko note now "circulating supply only"; docs/ops/sources-register.md regenerated, `--check` current.
9. prices.yaml header comment updated to the R11 rule (comment only; no hash moved by it).

## Hash re-pins (combined hash, `loadAsset`)

| asset | old | new | why |
|---|---|---|---|
| aero | 035327b9eec2… | 3c413feb4fbd… | R11: names no ref now (config-only hash) |
| cake | 86359b56c1c1… | e863393a2a48… | YAML + R11 |
| crv | 2cbf746088a8… | 9787bef1f28e… | YAML + R11 |
| cvxcrv | f1a2f4bafa91… | e2ba388d44ea… | YAML + R11 |
| hype | 2ec7d2cefc9b… | af6d3b0124f2… | YAML |
| link | 4479e2426ded… | 5fc85808ea63… | YAML + R11 |
| lit | 300863b835e7… | 7864c2836741… | YAML + R11 |
| pump | a616f10dacc9… | 9c0237adfb21… | YAML |
| sdcrv | db7ef33f45e5… | 357ee9ca0f15… | YAML + R11 |
| sky | 48c23f259234… | be03451c4a2e… | YAML + R11 |
| uni | 7ece78194e01… | 5c1d9cf48fe8… | YAML + R11 |
| vvv | b32ee86f97fe… | b9e654a8fe83… | YAML + R11 |
| ycrv | 7f6c53a1d473… | 908f12e73f67… | YAML + R11 |

Pins updated in tests/assets/*.ingest.test.ts, tests/config/load.test.ts (lit, vvv, hype, aero), tests/agent/disclosure.e2e.test.ts (LIT_HASH).

## Goldens (flattened old vs new, script scratch/golden_diff.py)

- **v2-report-13.json**: inputs unchanged (all 65 input hashes identical). In the 60 entries of the 12 assets exactly two
  paths moved: `incomeStatement.priceBasis.source` (`market_data:coingecko` -> `contract_state:price.token`; hype, lit ->
  `first_party_api:price.token`) and `incomeStatement.priceBasis.sourceType` (`market_data` -> `contract_state` /
  `first_party_api`). aero's 5 entries unchanged. **Report value paths outside the allowlist: 0** (no revenue, cost,
  holder-flow, yield, dilution, grade or price value moved).
- **packs-13.json**: aero unchanged; each of the 12 gains the `adapter_params` entries of price_usd's price.token and
  price.token_check (VVV also diem_price_usd's), with their paramsDoc (lit/pump: the inserted entries shift indexes).
  With the `price.*` entries removed every pack is identical to the old one (checked by script). No value moved.
- v1-report-13.json, parity: unchanged (parity.test passes on the new v2 golden).

## Tests (TDD)

New (RED recorded against the base code by stashing the src/assets changes):
- tests/ingest/adapters.price.test.ts (16): feed (LINK 12.5 vs v3 TWAP check, one multicall for both), Curve x CRV ref x
  crvUSD chain (cvxCRV), a missing quote fails naming quote_missing, Uniswap v2 TWAP over [run-1h, run] (SKY, start block
  asserted), Aerodrome TWAP x ETH/USD (VVV), chained DIEM via VVV, a ref off the asset's chain at that chain's head
  (CAKE), sdCRV bound inside (gap 0 at tolerance 0) and above (1.0 CRV bound, breach, gap 10%), Hyperliquid allMids
  (api stamp), Lighter mid with the v4 check (api / onchain), PumpSwap vaults with the Meteora check, validateParams
  refusals (unknown key, missing ref, ref not in prices.yaml; none without prices), load-time refusal naming the metric,
  unknown ref at run (`unknown_price_ref`), rung/label/chain/needsRpc per asset. RED: 16/16 failed (`unknown adapter: price.token`).
- tests/prices/config.test.ts R11 test: RED `expected [ 'hyperliquid:spot/@107' ] to deeply equal []` (symbol match).
- tests/levels/levels.test.ts circulating_supply-only prefetch: RED with the base YAMLs (12 coingecko price sources).
- tests/checks/evaluate.test.ts price check against price.token_check (ok and breach) and resolution/own-adapter
  refusal: RED 2/2 against the base schema.ts (`neither a metric nor a contract`).
- tests/provenance/adapterOrigins.test.ts: samples for both adapters, plus HYPE's first-party stamp = its rung's origin.
- tests/report/incomeStatement.test.ts: priceBasis source per asset (crv/pump contract_state, hype/lit first_party_api,
  aero unchanged) and sourceTypeOf of price adapters by ref namespace.
Updated: 12 asset ingest tests fake the ref's method reads instead of /coins/markets price (tests/helpers/livePrices.ts
`liveEvmCalls` builds feed/curve/get_dy/v2/Aerodrome/v3/v4 results for a wanted USD; `pumpLiveAccounts`, `hyperliquidMids`,
`lighterBook`) at the same prices (CRV 0.3933, CAKE 2.3, LINK 12.5, UNI 7.5, SKY 0.07, cvxCRV 0.1392, sdCRV 0.1884,
yCRV 0.18345, VVV 26.03, DIEM 1941.6, HYPE 92.36, LIT 3.04, PUMP 0.005); feed/oracle/venue prices still `toBe`, TWAP and
chained products `toBeCloseTo(.., 9-12)`. Plans, cross-check lists (price_usd now checked on crv, sky, ycrv, cvxcrv,
sdcrv, hype; diem_price_usd on vvv), VVV multicall bound (<= 8), HYPE allMids post, PUMP's Ethereum USDC read updated.
tests/helpers/syntheticReport.ts `repoAsset` parses with the repo prices.yaml (so LIT's rung is its method's).

Final runs (after the commit):
- `npx vitest run --maxWorkers=2`: **151 files, 1881/1881 passed** (no load-sensitive timeouts).
- `npm run typecheck`: clean. `npm run lint:promises`: clean. `python3 -m unittest scripts/provision/test/test_orion_remote.py`: 52 OK.
- `npx tsx tools/sources-register/generate.ts --check`: current.

## Self-review / concerns

1. **AERO's hash moves to its config-only hash** (R11 is applied literally: AERO names no price.* ref and scans no token,
   so its prices.yaml entry is no longer in its hash; the Task 1 test "AERO only aero" now expects no asset to move on an
   AERO entry change). Its entry still drives its price history and level rebuild (R21), so a method change there would not
   show as "config" on AERO. If that matters, add AERO's chain.v2_pool_twap_price `token` (or its ref) to entriesFor.
2. **Rung depends on a load-time note**: a price source's rung/chain/needsRpc come from prices.yaml only when the config
   was parsed with it (loadAsset, parseAssetObject(obj, prices)); a hand-built/cloned config falls back to the ref's
   namespace, which mislabels LIT (eip155 ref priced on Lighter) as contract_state. All production paths load with prices.
3. **Cross-check semantics vs prices.yaml**: cvxCRV/yCRV's `consecutive: 2` and LIT's "zero-liquidity hours skipped" are
   writer rules; at fetch time one price.token_check over 3% raises the ordinary cross-check anomaly, and a zero-liquidity
   v4 hour fails the check reading (source note), not a skip. sdCRV's check uses tolerance_pct 0 (inside the band the check
   value equals the primary exactly).
4. **Check id `price_chainlink`** on CAKE/LINK/UNI kept for stored check-row continuity although it now compares the feed
   with the pool check.
5. needsRpc of an EVM price ref on another chain than the asset's still opens the asset's RPC (unused); no repo asset does this.
6. Templates (docs/templates/T*.md) still show a CoinGecko price_usd and a Chainlink price check; docs/ops and the
   ingestion spec are Task 9's. VVV's `external_ids.coingecko_diem` is now unread (R8 drops coingecko ids).
7. RED evidence for the asset/golden re-pins is the base suite's own failures (116 failing before the test updates).
