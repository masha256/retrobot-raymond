# Phase 3 R2 scoping: on-chain hourly USD prices for VVV, DIEM (Base) and CAKE (BNB)

Measured on 2026-11-13 (~16:40Z) through Orion's own `.env` RPC endpoints (both Alchemy). Everything was read-only, and no repo file was touched.
Base head at measurement: 56,952,571. BNB head: 133,369,509. Calls used: 1,053 on Base and 436 on BNB.
The raw numbers are in `base-bnb-raw.json` next to this file.

Labels: **M** = MEASURED (the block/date is given or is the column date). **C** = CLAIMED (the source is named).
"Hour" = the first block at or after HH:00:00Z. "TWAP" = 1 h. CoinGecko figures are a **DEV-ONLY REFERENCE**, not a check. They come from the public `market_chart/range` endpoint at the same hour and are often rate-limited (429).

Dates used: 2026-05-13 00Z (rebuild start), 06-15 12Z, 08-15 12Z, 10-15 12Z, NOW (= the head block above). 2026-05-01 00Z was also read once to check archive depth.

## 1. Per-token summary

| | VVV (Base) | DIEM (Base) | CAKE (BNB) |
|---|---|---|---|
| Token | 0xacfe6019ed1a7dc6f7b508c02d1b04ec88cc21bf | 0xF4d97F2da56e8c3098f3a8D538DB630A2606a024 (`contracts.diem` in assets/vvv.yaml) | 0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82 |
| **Primary method** | Spec tier 2: pool TWAP x Chainlink | Spec tier 2, **chained**: DIEM/VVV TWAP x VVV USD | Spec tier 1: Chainlink CAKE/USD at the hour block |
| Primary pool / feed | Aerodrome v2 volatile **VVV/WETH** `0x01784ef301D79e4B2DF3a21ad9a536d4cF09A5Ce`. This is vvv.yaml's `aerodrome_pool`; factory 0x420DD381…40Da; token0 = WETH. | Aerodrome v2 volatile **DIEM/VVV** `0xbb345d35450bf9ee76f3d2ce214e8e7ac5e1071d` | `0xB6064eD41d4f67e353768aA239cA86f4F73665a1` "CAKE / USD", 8 decimals (M) |
| Quote token, USD feed | WETH -> **Chainlink ETH/USD on Base `0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70`, 8 decimals** (M), **not** the USDC feed | VVV -> VVV's own chain price (above) -> ETH/USD | n/a |
| Depth NOW (M) | 171,978 VVV + 1,693 WETH ≈ **$6.67M** | 2,318 DIEM + 188,464 VVV ≈ **$7.31M** | Feed. Deepest pool for reference: PCS v2 CAKE/WBNB 0x0ed7e529…4fD0 ≈ $18.3M |
| Depth history (M, reserves) | 05-13: 298k VVV/2,146 WETH. 06-15: 283k/2,625. 08-15: 399k/2,499. 10-15: 347k/3,303 | 05-13: 2,247 DIEM/194.6k VVV. 06-15: 2,119/206.3k. 08-15: 1,950/224.2k. 10-15: 2,410/181.3k | n/a |
| TWAP at a past block | **Yes** (M). `currentCumulativePrices()` at hour-1 h and at the hour gives dt = 3,600 s at all five dates and at 05-01. This is the same math as `chain.v2_pool_twap_price`. | **Yes** (M), same | Feed `latestRoundData` at the hour block works at all dates and at 05-01 (M) |
| Feed freshness at the hour (M) | ETH/USD age 530–970 s (05-13: 788, 08-15: 704, NOW: 35; max over 12 hours of 09-01: 970). USDC/USD age up to 84,066 s (a ~24 h heartbeat cadence). | same feeds | CAKE/USD age 9–65 s at the five dates. On 09-01 (24 hours): max 63 s, median 32 s. Round spacing is 65–67 s at every date. The heartbeat itself was not looked up. |
| **Independent check** | Uniswap v3 **VVV/USDC 0.3%** `0x67a11022b7b6ed66f81233f6c8ed6e48f7826530`: `observe([3600,0])` 1 h TWAP x **USDC/USD** `0x7e860098F58bBFC8648a4311b374B1D669a2bc6B` (8 decimals). A different pool, quote and feed. ≈ $0.88M NOW. Cardinality was 360 in May–Aug and 2,000 from Oct (M). | Slipstream (legacy) **DIEM/USDC** tick spacing 100 `0xbc3231036ee1eca03e5f67fecedc640d21610823`: `observe` 1 h TWAP x USDC/USD. It does not touch VVV or the primary pool. Thin: ≈ $0.12M NOW. | PancakeSwap v3 **CAKE/USDT 0.25%** `0x7f51c8aaa6b0599abd16674e2b17fec7a9f674a1`: `observe` 1 h TWAP x Chainlink USDT/USD `0xB97Ad0E74fa7d920791E90258A6E2085088b4320` (8 decimals). ≈ $5.2M NOW. |
| First-party | Venice `vvv_stats.price` = 19.346 NOW vs 19.402 TWAP (−0.29%) (M). Live only, with no history, so it cannot check the rebuild. | Venice `diem_stats.price` returns **"0"** (M), so it is unusable | none |

### Gaps, primary vs independent check (M; positive = primary is higher)

| Date | VVV primary $ | vs v3 VVV/USDC TWAP | vs legacy Slipstream VVV/WETH TWAP (extra) | CoinGecko DEV-ONLY | DIEM primary $ | vs Slipstream DIEM/USDC TWAP | vs v3 DIEM/WETH 1% spot (extra) | CoinGecko DEV-ONLY | CAKE feed $ | vs v3 CAKE/USDT TWAP | vs v3 CAKE/WBNB 0.25% TWAP x BNB/USD (extra) | CoinGecko DEV-ONLY |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 05-01 00Z | 8.5395 | n/m | n/m | n/m | 1,073.9 | −0.15% | n/m | n/m | 1.44779 | −0.08% | n/m | n/m |
| 05-13 00Z | 16.3573 | −0.15% | +0.00% | 16.2990 (+0.36%) | 1,419.17 | −0.06% | +0.66% | 429 | 1.54297 | −0.28% | −0.07% | 429 |
| 06-15 12Z | 16.2888 | **+0.60%** | −0.05% | 16.3904 (−0.62%) | 1,585.51 | **+0.59%** | +0.08% | 1,594.72 (−0.58%) | 1.40252 | +0.13% | −0.02% | 429 |
| 08-15 12Z | 11.7447 | +0.00% | −0.01% | 11.7733 (−0.24%) | 1,350.47 | −0.24% | −0.86% | 1,349.62 (+0.06%) | 1.43304 | −0.03% | −0.06% | 429 |
| 10-15 12Z | 22.2993 | −0.13% | −0.02% | 22.4515 (−0.68%) | 1,677.53 | −0.08% | −0.17% | 1,684.16 (−0.39%) | 2.18406 | −0.19% | −0.18% | 2.1858 (−0.08%) |
| NOW | 19.4017 | +0.03% | −0.01% | 429 | 1,577.44 | −0.05% | −0.08% | 1,570.29 @−320 s (+0.46%) | 1.74948 | −0.09% | +0.27% | 1.7446 @−180 s (+0.28%) |

All primary-vs-check gaps are ≤ 0.60%, inside the 2% tolerance that the cross-checks use. The two 0.6% rows (06-15, VVV and DIEM) share one VVV-side move. DIEM's primary is chained through VVV, so a VVV-side move appears in both rows.
Orion DB, DEV-ONLY (`observations`, CoinGecko-sourced, 2026-10-15T12:05Z): VVV 22.38 and DIEM 1,684.23. Both are within 0.4% of the 12:00Z chain values.

### Other pools found (M, depth NOW; factories: Aerodrome v2, Slipstream, Slipstream-2, the post-merger Aero CL factory 0x9cb22058…7a76, Uniswap v3)

- VVV: **Aero (new) CL VVV/WETH tick spacing 100 `0xdebaebe5b2729f7d62072b2ea40472d78d2c1626`** ≈ $5.1M. Its in-range liquidity L is 2.43e24, about 140x the v2 pool's sqrt(xy) of ≈1.7e22, so it is the deepest by in-range depth now. Cardinality is 990. It **did not exist at the 10-15 block**: it came with the 2026-10-22 Aero launch. Uniswap v3 VVV/WETH 1% 0x1d2bdb71… ≈ $1.0M. Aero CL VVV/WETH tick spacing 200 0x9f11c9e8… ≈ $0.64M. Legacy Slipstream VVV/WETH tick spacing 100 0x7ec6c9d9… ≈ $0.37M, but in May its L was 8.9e22 vs ≈2.5e22 for v2. Uniswap v4 PoolManager (0x498581ff…) appears in VVV/DIEM transfers, and **v4 pools were not measured**.
- DIEM: Aero CL DIEM/VVV tick spacing 100 0x8fc836d9… ≈ $4.2M (new, post-merger). Aero CL DIEM/USDC tick spacing 100 0xf69cd40b… ≈ $0.21M (new). Uniswap v3 DIEM/WETH 1% 0x80d99518… ≈ $0.12M, cardinality 10 until Oct. **No deep DIEM/USDC pool exists, so "TWAP x USDC feed" from the spec cannot be the primary for DIEM.**
- CAKE: PCS v2 CAKE/WBNB ≈ $18.3M (deepest). PCS v3 CAKE/USDT 0.25% ≈ $5.2M. PCS v3 CAKE/WBNB 0.25% 0x133b3d95… ≈ $3.9M. PCS v2 CAKE/USDT ≈ $0.81M.

## 2. Block-by-time

- **Base (M):** the last 2 s block is **53,556,127** (2026-11-05T18:00:01Z). From **53,556,128** blocks are 0.2 s apart and share integer-second timestamps, 5 blocks per second.
  - Before the switch, `ts = 1,686,789,347 + 2n` exactly. This was verified at 05-01, 06-15, 08-15 and 10-15, and at the switch. After the switch, ts = 1,793,901,601 + 0.2·(n − 53,556,128), within 1 s at 11-12 and NOW. So the hour block is **closed-form** with 1 getBlock (+1 for n−1) to confirm it.
  - chains.ts's comment says "~53,556,072 at 17:58Z". The measured switch is 56 blocks later, at 18:00:01Z. This is a doc nit only.
- **Port of `firstBlockAtOrAfter` (rpc.ts), probes per lookup (M):**
  - Head-anchored, as `blockAt` does from a far run block: Base 27–29 probes (May–Oct), 17 at 11-05 17Z, 6 after the switch. BNB 15–19 probes (7 at 06-15).
  - Walking hour to hour (anchor = previous hour's block): BNB mean **4.3** (08-15), **4.6** (09-01, 24 hours) and **2.7** (11-05). Base before the switch: **21 every hour**. With a 0.2 s nominal rate the first guess overshoots 10x. Interpolation then lands exactly on the answer, which is `hi`, so the remaining bracket is bisected down. Base after the switch: 2 probes.
  - Every lookup returned the exact first block at or after the hour (BNB at HH:00:00, Base before the switch at HH:00:01).
- In `chain.v2_pool_twap_price` the TWAP start is `blockAt(run.timestamp − 3600)` anchored at the run block. In an hourly rebuild **the start block is the previous hour's block**, so it costs nothing extra if the writer reuses it.

## 3. Archive and cost

- Archive (M): `eth_call` at historical blocks works on both endpoints back to 2026-05-01 00Z. This covers v2 cumulative reads, `observe`, Chainlink `latestRoundData` and `getRoundData`. No pruning errors were seen.
- Alchemy CU (C, alchemy.com/docs/reference/compute-unit-costs, read 2026-11-13): `eth_call` 26, `eth_getBlockByNumber` 20, `eth_blockNumber` 10, `eth_getLogs` 60. Batches cost the sum of their parts. The table shows no archive surcharge.
- Points: 183 d x 24 = **4,392 hours** (from 05-13). From 05-01 it is 195 d = 4,680.

| Plan | Base (VVV + DIEM, one multicall per hour) | BNB (CAKE) | Total one-time |
|---|---|---|---|
| **A. Sequential writer.** Closed-form Base block; BNB walk anchored on the previous hour. One Multicall3 `eth_call` per hour holds the primary + check pools + feeds. The cumulative start is reused from the previous hour. | ~2 calls/hour (1 getBlock check + 1 eth_call) = 46 CU -> **8.8k calls, 0.20M CU** | ~5.6 calls/hour (4.6 getBlock + 1 eth_call) ≈ 118 CU -> **24.6k calls, 0.52M CU** | **~33k calls, ~0.72M CU** |
| **B. Adapters as written, run once per hour** (`side` + 2 cumulative + feed multicalls; check = side + slot0 + feed). The hour block and the TWAP-start block are each searched head- or run-anchored. | ~28 probes (hour) + 2 x (21 probes + ~6 eth_call) ≈ 82 calls ≈ 1.7k CU/hour -> **~360k calls, ~7.5M CU** | ~17 probes + 3 eth_call ≈ 20 calls ≈ 420 CU/hour -> **~88k calls, ~1.8M CU** | **~450k calls, ~9.3M CU** |

- Daily ongoing for these three refs under plan A: 24 x (2 + 5.6) ≈ **180 calls/day** (≈ 4k CU/day).
- The spec's D3 estimate ("~52.7k archive calls" = 12 refs x 4,392 x 1) assumes 1 call per point. That holds for Base only with closed-form blocks. BNB needs ~5x for the block search.

## 4. Open questions

1. **Spec wording, VVV.** The spec says "VVV: TWAP x USDC feed". The deepest VVV pool quotes **WETH**, and VVV/USDC is only ≈ $0.88M. Primary = VVV/WETH x **ETH/USD** feed? The USDC path would then become the check.
2. **Spec wording, DIEM.** DIEM's depth is in DIEM/VVV, so DIEM USD = DIEM/VVV TWAP x VVV's chain price. That is a dependency between token refs: the writer must price VVV first. The only DIEM/USDC pools are $0.1–0.2M. Is a chained price acceptable as "tier 2"? Or should the thin DIEM/USDC Slipstream TWAP be the primary and the chain the check?
3. **"Deepest pool" definition.** By TVL the legacy v2 pool leads for VVV. By in-range liquidity, the legacy Slipstream tick-spacing-100 pool led May–Oct and the new Aero CL pool leads now (140x). For one pool across the whole window, v2 VVV/WETH and v2 DIEM/VVV are the only deep pools present from 05-01 to NOW. Aero's new CL pools start ≈ 10-22. Switching pools mid-history needs a dated pool list in config.
4. **Uniswap v4.** VVV and DIEM trade through the v4 PoolManager. v4 depth was not measured, so the "deepest pool" claim excludes v4.
5. **Base block search.** The interpolating search costs 21 probes per hour before the switch, because of the 0.2 s nominal rate and bisecting when the guess lands on `hi`. Options: probe `hi−1` when the interpolation hits `hi`; per-era `blockTimeSec`; or Base closed form. Should the rebuild writer bypass `firstBlockAtOrAfter` for Base?
6. **Feed heartbeats** (ETH/USD Base, USDC/USD Base, CAKE/USD BNB, USDT/USD BNB) were not looked up on data.chain.link. Only the observed cadence is above. A staleness guard needs the published heartbeat and deviation figures.
7. **USDC/USD on Base** was up to 23.4 h old at the hour (normal for a 24 h heartbeat). Is that acceptable for the check, or should 1.0 be assumed with a peg guard?
8. **CoinGecko DEV-ONLY reference coverage:** 7 of 15 cells returned 429. The prod `prices` table (not present in the local orion.db) has hourly CoinGecko rows for VVV and CAKE (not DIEM) for a fuller side-by-side, if that is wanted before release.

## 5. Recommendation

- **CAKE:** primary = Chainlink CAKE/USD `latestRoundData` at the hour block (tier 1; age ≤ 66 s). Check = PCS v3 CAKE/USDT 0.25% `observe` 1 h TWAP x Chainlink USDT/USD. One Multicall3 call per hour; BNB hour block by a walk anchored on the previous hour.
- **VVV:** primary = Aerodrome v2 VVV/WETH 0x01784e… 1 h TWAP (`chain.v2_pool_twap_price`, `quote_decimals: 18`, `usd_feed` = **ETH/USD 0x71041d…**). Check = Uniswap v3 VVV/USDC 0.3% `observe` TWAP x USDC/USD. That needs a small new `cl_pool_twap_price`, or `chain.cl_pool_spot_price` (slot0) as AERO does. Both exist across the whole window. Revisit the primary after deciding question 3; the Aero CL tick-spacing-100 pool has been deepest since 10-22.
- **DIEM:** primary = Aerodrome v2 DIEM/VVV 0xbb345d… 1 h TWAP x VVV's chain price for the same hour. This needs a "quote priced by another token ref" option in place of a feed. Check = legacy Slipstream DIEM/USDC tick spacing 100 `observe` TWAP x USDC/USD, which is independent of VVV. Drop the Venice `diem_stats` idea (price = 0).
- **Rebuild writer:** use plan A (sequential hours, closed-form Base blocks, previous hour as the TWAP start, one multicall per chain-hour). It costs ≈ 33k calls / 0.72M CU for these three refs, about 13x cheaper than running the adapters per point (≈ 9.3M CU). Live code can keep the adapters (one point/hour).
