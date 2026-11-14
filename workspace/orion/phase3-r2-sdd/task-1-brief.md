### Task 1: `prices.yaml`, its schema, loader and config-hash wiring

**Files:**
- Create: `prices.yaml`, `src/prices/config.ts`
- Modify: `src/config/load.ts` (hash), `src/config/schema.ts` (transfer_flow `share_price.underlying`; `price_coingecko_id` kept optional until Task 6 removes its users)
- Test: `tests/prices/config.test.ts`, `tests/config/load.test.ts`

**Interfaces:**
- Produces: `type PriceMethod` (discriminated on `kind`: `chainlink {feed}`, `curve_oracle {pool, index?, quote_ref}`,
  `curve_get_dy {pool, i, j, quote_ref}`, `v2_twap {pool, flavor: 'uniswap' | 'aerodrome', quote_ref?, usd_feed?}`,
  `v3_twap {pool, seconds: 3600, quote_ref?, usd_feed?}`, `v4_spot {state_view, pool_id, quote_ref?, usd_feed?}`,
  `hyperliquid_candle {coin}`, `lighter_candle {market_id}`, `solana_vaults {base_vault, quote_vault, usd_feed}`,
  `meteora_dlmm {pair, usd_feed}`, `bound {min_in_quote, max_in_quote, quote_ref}`);
  `interface PriceEntry { ref: string; symbol: string; decimals: number; chain: 'eip155:1' | 'eip155:56' | 'eip155:8453' | 'solana' | 'hyperliquid'; validFrom: string; primary: PriceMethod; check: PriceMethod & { tolerancePct: number; consecutive: number; label?: 'same_venue' | 'no_independent_check' } }`;
  `loadPrices(rootDir: string): Map<string, PriceEntry>`; `entriesFor(asset: AssetConfig, prices: Map<string, PriceEntry>): PriceEntry[]` (the refs the asset uses plus their quote refs, transitively);
  `methodSource(m: PriceMethod): string` -> `chain:<kind>` or `first_party:<venue>`.

- [ ] **Step 1: Failing tests** `tests/prices/config.test.ts`: loading the committed `prices.yaml` gives the 17 refs of
  the table; every `quote_ref` resolves; no cycle (`DIEM -> VVV` ok, a self-reference refused); an unknown key, a
  tolerance <= 0, an address that isn't 20 bytes, or a ref whose chain prefix contradicts `chain` is refused by name;
  `entriesFor(ycrv)` contains yCRV, CRV and crvUSD. `tests/config/load.test.ts`: changing a `prices.yaml` entry moves the
  hash of exactly the assets that use it (crvUSD moves crv, cvxcrv, sdcrv, ycrv; AERO's hash moves only on its own entry).
- [ ] **Step 2: Measure `valid_from`** (controller, not the implementer: needs RPC): for each ref, the read at the
  2025-10-13T01:00Z block for primary and check (one multicall per chain, `onchain_probe.py`). Ones that fail get the
  first working day as `validFrom`. Record results in the ledger; any ref later than 2025-10-14 for a ref that has flow
  rows before then is a stop for Mike (rows that can't be re-priced).
- [ ] **Step 3: Implement** with zod strict nodes; the hash input is the asset config plus `entriesFor` sorted by ref.
- [ ] **Step 4: Run** the two test files, then the full suite: every asset's hash moves (new hash input), so re-pin the
  asset tests' hashes in this commit (`grep -rl <old hash> tests`) and nothing else.
- [ ] **Step 5: Commit** `feat(prices): central prices.yaml with one method and one check per token ref`.


## The price table (from the plan; binding content of prices.yaml)

Refs are lowercased. Feeds are Chainlink, 8 decimals, read with `latestRoundData` (answer, updatedAt).

| ref (symbol) | primary | check (tolerance) |
|---|---|---|
| eip155:1/0xd533…cd52 CRV | Curve TriCRV 0x4eBdF703948ddCEA3B11f675B4D1Fba9d2414A14 `price_oracle(1)` (CRV in crvUSD) x crvUSD ref | feed CRV/USD 0xCd627aA160A6fA45Eb793D19Ef54f5062F20f33f (1.5%) |
| eip155:1/0x4e3f…2b CVX | Curve cvxeth 0xB576491F1E6e5E62f1d8F26062Ee822B40B0E0d4 `price_oracle()` x ETH/USD 0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419 | feed CVX/USD 0xd962fC30A72A84cE50161031391756Bf2876Af5D (2.5%) |
| eip155:1/0x5607…79 SKY | Uniswap v2 SKY/USDS 0x2621CC0B3F3c079c1Db0E80794AA24976F0b9e3c cumulative TWAP x USDS ref | feed SKY/USD 0xee10fE5E7aa92dd7b136597449c3d5813cFC5F18 (2.5%) |
| eip155:1/0x5149…ca LINK | feed LINK/USD 0x2c1d072e956AFFC0D435Cb7AC38EF18d24d9127c | Uniswap v3 LINK/WETH 0xa6Cc3C2531FdaA6Ae1A3CA84c2855806728693e8 1 h `observe` x ETH/USD (2%) |
| eip155:1/0x1f98…f984 UNI | feed UNI/USD 0x553303d460EE0afB37EdFf9bE42922D8FF63220e | Uniswap v3 UNI/WETH 0x1d42064Fc4Beb5F8aAF85F4617AE8b3b5B8Bd801 1 h `observe` x ETH/USD (2%) |
| eip155:1/0xf939…4e crvUSD | feed CRVUSD/USD 0xEEf0C605546958c1f899b6fB336C20671f9cD49F | Curve crvUSD/USDT 0x390f3595bCa2Df7d23783dFd126427CCeb997BF4 `price_oracle()` x USDT/USD 0x3E7d1eAB13ad0104d2750B8863b489D65364e32D (0.5%) |
| eip155:1/0xdc03…4f USDS | feed USDS/USD 0xfF30586cD0F29eD462364C7e81375FC0C71219b1 | feed DAI/USD 0xAed0c38402a5d19df6E4c03F4E2DceD6e29c1ee9 (0.5%) |
| eip155:1/0x62b9…aa7 cvxCRV | Curve 0x971add32Ea87f10bD192671630be3BE8A11b8623 `price_oracle()` (cvxCRV in CRV) x CRV ref | Curve 0x9D0464996170c6B9e75eED71c68B99dDEDf279e8 `get_dy` spot (3%, 2 consecutive) |
| eip155:1/0xd1b5…b5 sdCRV | Curve 0xCA0253A98D16e9C1e3614caFDA19318EE69772D0 `price_oracle()` x CRV ref | bound 0.3-1.0 CRV, `no_independent_check` |
| eip155:1/0xfcc5…5b yCRV | Curve 0x99f5aCc8EC2Da2BC0771c32814EFF52b712de1E5 `price_oracle()` x CRV ref | Curve 0x453D92C7d4263201C69aACfaf589Ed14202d83a4 `get_dy` spot (3%, 2 consecutive) |
| eip155:56/0x0e09…82 CAKE | feed CAKE/USD (BNB) 0xB6064eD41d4f67e353768aA239cA86f4F73665a1 | PancakeSwap v3 CAKE/USDT 0x7f51c8aaa6b0599abd16674e2b17fec7a9f674a1 1 h `observe` x USDT/USD (BNB) 0xB97Ad0E74fa7d920791E90258A6E2085088b4320 (2%) |
| eip155:8453/0xacfe…bf VVV | Aerodrome v2 VVV/WETH 0x01784ef301D79e4B2DF3a21ad9a536d4cF09A5Ce cumulative TWAP x ETH/USD (Base) 0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70 | Uniswap v3 VVV/USDC 0x67a11022b7b6ed66f81233f6c8ed6e48f7826530 1 h `observe` x USDC/USD (Base) 0x7e860098F58bBFC8648a4311b374B1D669a2bc6B (2%) |
| eip155:8453/0xf4d9…a024 DIEM | Aerodrome v2 DIEM/VVV 0xbb345d35450bf9ee76f3d2ce214e8e7ac5e1071d cumulative TWAP x VVV ref | Slipstream DIEM/USDC 0xbc3231036ee1eca03e5f67fecedc640d21610823 1 h `observe` x USDC/USD (2%) |
| AERO (aero.yaml's `token`) | aero.yaml's existing `price_pool` TWAP x `usdc_usd_feed` | aero.yaml's `price_check_pool` spot (2%) |
| HYPE (`hyperliquid:spot/@107`) | Hyperliquid spot `@107` hourly candle close (live: `allMids["@107"]`) x USDC/USD (Ethereum feed 0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6) | Hyperliquid perp `HYPE` candle close (2%), labelled `same_venue` |
| eip155:1/0x232c…4ee2 LIT | Lighter spot market 2049 `/api/v1/candles` hourly close (live: order-book mid) x USDC/USD | Uniswap v4 LIT/USDC pool (per `hype-lit-pump.md`) `getSlot0` via StateView, skipped when in-range liquidity is 0 (3%) |
| solana:mainnet/pumpCm…Dfn PUMP | PumpSwap PUMP/USDC vaults (per `hype-lit-pump.md`): USDC vault / PUMP vault x USDC/USD | Meteora DLMM PUMP/USDC bin-20 (2%) |

The implementer copies exact pool ids/addresses for HYPE, LIT, PUMP and AERO from the named files; nothing else is
looked up. Each entry also states `valid_from` (Task 1 measures it, Step 2). HYPE and LIT get hourly rows too (M6 still
holds: no flow reads them), because M7's level rebuild needs a price at each past `price_usd` row (from 2026-10-02); their
`valid_from` is their candle reach (HYPE `candleSnapshot` ~2026-04-19, a rolling 5,000 hours; LIT market launch
2025-12-30), about 10 requests in all. USDC/USD (Ethereum) 0x8fFf…18f6 was re-read on chain 2026-11-13 ("USDC / USD").

