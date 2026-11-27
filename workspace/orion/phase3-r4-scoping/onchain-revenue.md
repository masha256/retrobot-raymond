# Aero exchange revenue on chain: re-measurement + on-chain USD pricing (R4 scoping, RET-20)

Written 2026-11-27 (RPC work 18:35-19:05 UTC, outside both quiet windows) by a read-only subagent. Every on-chain number is
**MEASURED** (block numbers per chain/day in `onchain-revenue-data/<day>.json`, fields `block_start`/`block_end`).
`*_devonly` = coins.llama.fi historical price at day end, **dev-only reference**. `DL fees / DL rev` = **CLAIMED**
api.llama.fi `summary/fees/aero-protocol` (children "Aero Slipstream" + "Aero Basic"; the API chart row stamped D covers
UTC day D, verified: Ink 11-01 tape $788 vs row 11-01 $787 vs row 11-02 $2,295). Prod rows: the stored row stamped D+1
equals DL `dailyHoldersRevenue` (all children) for day D (11-15: 282,283.66 vs 282,283).
RPC key never printed or written (checked: no file under this dir contains it).

## Answer

- **The tape method works on all 7 chains and on an 8th Aero chain the brief does not list: Elysium** (Aero docs list it,
  CLAIMED https://app.aero.xyz/docs/security; CLFactory 0xEfd7…2891 has 31 CL pools; `clPoolTape()` = 0x27D5…35a4;
  Alchemy `elysium-mainnet` answers, chainId 99901). Elysium was **$9.3K of the $297K gross on 11-26 (3.1%)**. DL already counts it.
- **Gross fees** (tape `accumulators` delta, all pools) and **allocator accrual** (Δ pool gauge pending + `FeesCollected`)
  match DL to **−2.4%…+2.3% per chain-day** from 10-23 on, once the incentives streamed by the VRMs are added (DL counts
  them inside both fees and revenue). The exceptions are the 10-22 launch day, Arc fees (Aero Lite, +2…+21%; Arc revenue
  matches) and Elysium 11-26 (+4.7%).
- **Allocator share of gross: 88.5-95.2% per day** (all chains). Ungauged pools and V2 unstaked LPs keep the rest.
- **Pricing without CoinGecko/DefiLlama: recommended = Chainlink tier-A anchors → deepest-pool graph (anchor-side depth
  ≥ $10K, ≤ 3 hops, day-end spot) → pool-local fallback → unpriced.** Measured over 45 chain-days:
  **99.99% of the DL-priced fee value priced; chain-day total vs the dev-only reference within −0.2%…+3.6%**
  (Robinhood up to +3.6%, everything else within −0.2…+0.6%). Top-30-token price error: fee-weighted mean 0.14%,
  median 0.14%. Worst token with ≥ $1K/day of fees: 5.4% (NVDA on Robinhood, 11-26 Thanksgiving: the Chainlink feed and
  the on-chain market disagree). Worst overall: 65% on AMC (Robinhood, $48 of fees, thin-pool fallback).
  AERO itself (Base, deepest AERO/USDC pool): ≤ 1.04% vs reference.
- **Cost: ~130 Multicall3 eth_calls (≈21K inner calls) + 17 eth_getLogs + ~100 block-header reads per day for all
  8 chains, ~52 s wall.** A 45-day backfill is ≈ 6K multicalls + 0.8K getLogs + 4.5K header reads, ≈ 40 min.
  No throttling. The only provider limit hit: Ink caps eth_getLogs at 10,000 blocks (9-10 calls/day there).

## 1. Daily totals, all chains (MEASURED, USD at the recommended on-chain price)

`incentives $ (ub)` = Σ over every VRM `incentive(id)` of `rate × overlap(day) / 1e18`. It is an upper bound: zero-supply
seconds are not removed (DL removes them, which is why 10-22, a day with almost no allocations yet, is +54%).

| day | gross $ | allocator $ | alloc/gross | incentives $ (ub) | DL Aero fees | DL Aero rev | (gross+inc)/DL fees | (alloc+inc)/DL rev | prod row (D+1) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-10-22 | 110,205 | 99,287 | 90.1% | 76,199 | 120,916 | 113,136 | +54.2% | +55.1% | 145,005 |
| 2026-10-23 | 163,657 | 148,055 | 90.5% | 92,657 | 261,308 | 246,059 | -1.9% | -2.2% | 246,065 |
| 2026-11-01 | 131,635 | 125,350 | 95.2% | 10,971 | 142,501 | 136,049 | +0.1% | +0.2% | 136,051 |
| 2026-11-15 | 316,832 | 285,582 | 90.1% | 2,331 | 313,046 | 282,272 | +2.0% | +2.0% | 282,284 |
| 2026-11-25 | 345,954 | 306,597 | 88.6% | 3,276 | 342,445 | 304,143 | +2.0% | +1.9% | 304,151 |
| 2026-11-26 | 297,386 | 263,084 | 88.5% | 3,588 | 302,283 | 267,509 | -0.4% | -0.3% | 270,768 |

Reading the table:
- **10-22 (launch day)** doesn't reconcile, for two reasons. DL had **no price for the new AERO** that day, so its
  reference misses $16.0K of Base AERO fees (our on-chain total is +20% vs the DL-priced reference). And most
  incentive seconds had zero allocation supply.
- 10-23 to 11-26 reconcile to −2.2%…+2.0% for both fees and revenue.
- Incentives were large at launch ($93K/day on 10-23) and are ~$3K/day now.
- Legacy pools (not sAERO, excluded; CLAIMED from DL children):
  - Aerodrome V1 + Slipstream: fees $31-39K/day since 11-01 ($143K on 10-22). Revenue $2.5-5K/day; holders revenue 0 since 10-23.
  - Velodrome: $0.2-0.5K/day.
  - Data: `legacy-dl-claimed.json`.

## 2. Per chain per day

Columns:
- `priced` = share of the dev-only-reference fee value priced by: Chainlink tier-A anchors alone / + pool graph (floor
  $10K) / + pool-local fallback (the recommended method).
- `vs DL-priced ref` = our USD total ÷ (same token amounts × coins.llama.fi price) − 1.

| day | chain | gross fees $ | allocator $ | incentives $ (ub) | priced: anchors-A / +graph10k / +fallback | vs DL-priced ref | DL fees | DL rev | (gross+inc)/DL fees | (alloc+inc)/DL rev |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 10-22 | base | 95,524 | 86,220 | 62,633 | 71 / 99.5 / 100.0% | +20.1% | 103,701 | 96,801 | +52.5% | +53.8% |
| 10-22 | ethereum | 3,878 | 3,837 | 5,961 | 86 / 99.7 / 100.0% | -0.1% | 6,072 | 6,042 | +62.0% | +62.2% |
| 10-22 | optimism | 980 | 919 | 877 | 95 / 98.9 / 100.0% | +0.1% | 1,320 | 1,277 | +40.7% | +40.6% |
| 10-22 | arbitrum | 548 | 546 | 1,408 | 72 / 99.9 / 100.0% | +0.1% | 1,166 | 1,165 | +67.8% | +67.7% |
| 10-22 | ink | 25 | 12 | 0 | 71 / 70.9 / 100.0% | +0.0% | 14 | 4 | +78.6% | +200.0% |
| 10-22 | robinhood | 6,930 | 6,862 | 4,945 | 62 / 96.9 / 100.0% | +3.5% | 7,127 | 7,082 | +66.6% | +66.7% |
| 10-22 | arc | 2,320 | 891 | 375 | 81 / 100.0 / 100.0% | +0.1% | 1,516 | 765 | +77.8% | +65.5% |
| 10-23 | base | 141,266 | 127,311 | 78,077 | 64 / 99.0 / 100.0% | -0.1% | 224,501 | 210,437 | -2.3% | -2.4% |
| 10-23 | ethereum | 7,384 | 7,170 | 6,276 | 83 / 99.6 / 100.0% | -0.2% | 13,763 | 13,544 | -0.7% | -0.7% |
| 10-23 | optimism | 1,350 | 1,265 | 1,290 | 94 / 99.1 / 100.0% | +0.0% | 2,653 | 2,571 | -0.5% | -0.6% |
| 10-23 | arbitrum | 948 | 943 | 1,469 | 73 / 100.0 / 100.0% | +0.0% | 2,430 | 2,424 | -0.5% | -0.5% |
| 10-23 | ink | 50 | 21 | 0 | 89 / 88.7 / 100.0% | +0.0% | 50 | 21 | +0.0% | +0.0% |
| 10-23 | robinhood | 10,391 | 10,147 | 5,155 | 70 / 95.9 / 100.0% | +2.2% | 15,712 | 15,464 | -1.1% | -1.0% |
| 10-23 | arc | 2,268 | 1,198 | 390 | 82 / 100.0 / 100.0% | -0.1% | 2,199 | 1,598 | +20.9% | -0.6% |
| 11-01 | base | 103,751 | 98,450 | 5,984 | 60 / 99.0 / 99.8% | -0.2% | 109,652 | 104,161 | +0.1% | +0.3% |
| 11-01 | ethereum | 13,308 | 13,004 | 1,829 | 84 / 99.9 / 100.0% | -0.0% | 15,144 | 14,840 | -0.0% | -0.0% |
| 11-01 | optimism | 905 | 859 | 641 | 82 / 99.7 / 100.0% | -0.0% | 1,544 | 1,502 | +0.1% | -0.1% |
| 11-01 | arbitrum | 2,002 | 1,988 | 2,517 | 89 / 99.0 / 100.0% | -0.0% | 4,510 | 4,491 | +0.2% | +0.3% |
| 11-01 | ink | 788 | 536 | 0 | 88 / 100.0 / 100.0% | -0.0% | 787 | 535 | +0.1% | +0.2% |
| 11-01 | robinhood | 10,491 | 10,247 | 0 | 72 / 95.5 / 100.0% | +0.2% | 10,498 | 10,254 | -0.1% | -0.1% |
| 11-01 | arc | 390 | 266 | 0 | 79 / 100.0 / 100.0% | -0.1% | 366 | 266 | +6.6% | +0.0% |
| 11-15 | base | 262,447 | 233,484 | 1,778 | 73 / 99.2 / 100.0% | -0.1% | 258,614 | 230,018 | +2.2% | +2.3% |
| 11-15 | ethereum | 15,139 | 14,753 | 0 | 82 / 99.2 / 100.0% | -0.1% | 15,078 | 14,691 | +0.4% | +0.4% |
| 11-15 | optimism | 3,419 | 3,264 | 553 | 94 / 99.6 / 100.0% | +0.0% | 3,952 | 3,800 | +0.5% | +0.4% |
| 11-15 | arbitrum | 4,445 | 4,383 | 0 | 90 / 99.6 / 100.0% | +0.0% | 4,419 | 4,356 | +0.6% | +0.6% |
| 11-15 | ink | 723 | 622 | 0 | 85 / 100.0 / 100.0% | +0.0% | 720 | 618 | +0.4% | +0.6% |
| 11-15 | robinhood | 25,978 | 25,318 | 0 | 80 / 94.3 / 100.0% | +2.9% | 25,728 | 25,070 | +1.0% | +1.0% |
| 11-15 | arc | 1,978 | 1,141 | 0 | 83 / 100.0 / 100.0% | +0.0% | 1,865 | 1,137 | +6.1% | +0.4% |
| 11-15 | elysium | 2,703 | 2,617 | 0 | 86 / 100.0 / 100.0% | +0.1% | 2,670 | 2,582 | +1.2% | +1.4% |
| 11-25 | base | 278,042 | 241,077 | 2,720 | 70 / 99.6 / 100.0% | +0.1% | 274,936 | 239,053 | +2.1% | +2.0% |
| 11-25 | ethereum | 25,230 | 24,426 | 0 | 82 / 99.8 / 100.0% | +0.0% | 24,886 | 24,082 | +1.4% | +1.4% |
| 11-25 | optimism | 2,253 | 2,103 | 556 | 94 / 99.9 / 100.0% | +0.0% | 2,770 | 2,627 | +1.4% | +1.2% |
| 11-25 | arbitrum | 3,139 | 3,024 | 0 | 89 / 99.5 / 100.0% | -0.0% | 3,146 | 2,971 | -0.2% | +1.8% |
| 11-25 | ink | 857 | 593 | 0 | 84 / 100.0 / 100.0% | -0.0% | 845 | 583 | +1.4% | +1.7% |
| 11-25 | robinhood | 31,858 | 31,038 | 0 | 68 / 97.3 / 100.0% | -0.0% | 31,348 | 30,542 | +1.6% | +1.6% |
| 11-25 | arc | 1,076 | 854 | 0 | 81 / 100.0 / 100.0% | -0.2% | 1,055 | 843 | +2.0% | +1.3% |
| 11-25 | elysium | 3,499 | 3,482 | 0 | 72 / 99.4 / 100.0% | +0.6% | 3,459 | 3,442 | +1.2% | +1.2% |
| 11-26 | base | 241,793 | 209,333 | 3,033 | 66 / 99.7 / 100.0% | +0.1% | 246,354 | 213,389 | -0.6% | -0.5% |
| 11-26 | ethereum | 17,455 | 16,497 | 0 | 82 / 100.0 / 100.0% | -0.0% | 17,543 | 16,604 | -0.5% | -0.6% |
| 11-26 | optimism | 1,838 | 1,758 | 555 | 93 / 99.9 / 100.0% | -0.0% | 2,400 | 2,319 | -0.3% | -0.3% |
| 11-26 | arbitrum | 2,228 | 2,177 | 0 | 86 / 99.4 / 100.0% | +0.0% | 2,239 | 2,187 | -0.5% | -0.5% |
| 11-26 | ink | 530 | 419 | 0 | 84 / 99.8 / 100.0% | +0.1% | 533 | 420 | -0.6% | -0.2% |
| 11-26 | robinhood | 23,601 | 23,122 | 0 | 68 / 96.8 / 100.0% | +0.3% | 23,694 | 23,216 | -0.4% | -0.4% |
| 11-26 | arc | 689 | 574 | 0 | 85 / 99.9 / 100.0% | -0.1% | 680 | 577 | +1.3% | -0.5% |
| 11-26 | elysium | 9,252 | 9,204 | 0 | 73 / 98.9 / 100.0% | -0.0% | 8,840 | 8,797 | +4.7% | +4.6% |

Notes on the per-chain table:
- **Arc fees +6…+21% vs DL, revenue matches.** The Arc **Aero Lite** stack is a separate PoolTape 0x8Da0…6c25,
  CLPoolTape 0x967f…5Ee9 and CLFactory 0xb89D…1d03 with 35 CL pools and no gauges. Its fees were 56% of Arc gross on
  10-22 and $12/day by 11-25. DL estimates the Lite fees from Swap logs × a sampled `fee()`; we read the Lite tape.
- **Elysium +4.7% on 11-26** with the reference within 0.0%. So it is not pricing: DL's window or lite logic differs
  (DL starts Elysium on 11-08).
- Robinhood's `vs ref` +2…+3.6% comes from thin stock/meme pools priced by fallback (§3).

## 3. Pricing: design, test, recommendation

### 3.1 Method tested (all MEASURED at the day-end block of each chain)
1. **Anchors (tier A)**: canonical USD stables, ETH and BTC wrappers with a Chainlink `<X>/USD` feed on the same chain.
   For each feed, `description()` was read on chain (all matched) and `latestRoundData()` at every day-end block.
   - 8 on Base, 8 Ethereum, 6 OP, 6 Arbitrum, 4 Ink, 3 Robinhood, 3 Arc.
   - Tier B (93 other feeds, e.g. VIRTUAL, OP, ARB and 22 Robinhood stock feeds) was tested separately.
   - **Elysium has no Chainlink feeds.** USDC, WHYPE and UBTC are cross-chain-anchored to Base feeds: USDC/USD
     0x7e86…bc6B, HYPE/USD 0xEdB5…DcA and BTC/USD 0x32F5…CAbc.
2. **Graph**: every unpriced token takes the spot price of its deepest Aero pool against an already-priced token.
   - Pools qualify on actual `balanceOf(pool)` of the priced side × its price ≥ floor.
   - Up to 3 hops (99%+ resolve in hop 1).
   - Spot price: V2 volatile r1/r0; V2 stable marginal price of x³y+xy³; CL sqrtPriceX96².
3. **Pool-local fallback**: a fee token still unpriced is valued at its own pool's spot price against the pool's other
   side, if that side is priced. This is "value each pool's fees through its anchor side".
4. Everything else is **unpriced** and reported as coverage.

### 3.2 Results (45 chain-days; coverage = share of DL-priced fee value; `vs ref` range excludes Base 10-22)
| method | $-weighted coverage | worst chain-day coverage | chain-day total vs ref |
|---|---:|---|---|
| anchors tier A only | 69.9% | 60.0% (Base 11-01) | −40…−5% |
| anchors A+B (all feeds) | 79.1% | 70.1% | −30…0% |
| graph A, floor $10K (no fallback) | 99.15% | 70.9% (Ink 10-22), 88.7% (Ink 10-23) | −29…+0.4% |
| graph A, floor $50K | 96.8% | 70.9% (Ink), 76.0% (Robinhood 10-22) | −29…+0.1% |
| graph A, floor $250K | 88.9% | 62.3% (Robinhood 10-22) | −38…+0.1% |
| graph A+B, floor $50K, CL 30-min TWAP instead of spot | 97.9% | — | same as spot ±0.05% |
| graph A, tape-VWAP (Δvolume1/Δvolume0) instead of spot | 99.15% | — | −29…+1.3%, per-token errors 2-17% (worse) |
| pool-local only (each pool via its own anchor side, no global price) | 99.95% | 99.8% | −1.6…+3.5% |
| **recommended: graph A floor $10K + pool-local fallback** | **99.99%** | 99.8% (Base 11-01) | **−0.2…+3.6%** |
| same, floor $50K | 99.99% | 99.8% | −0.6…+3.5% |
| same, floor $250K | 99.97% | 99.8% | −1.6…+3.5% |

Per-token error (recommended method, the top 30 tokens by fee value per chain-day: 869 token-days):
- **Fee-weighted mean 0.137%, median 0.139%.** For the 673 non-anchor token-days the fee-weighted mean is 0.345%.
  27 of them are off by more than 5%, and together they carry 0.24% of the fee value.
- Worst with ≥ $1K/day of fees:
  - NVDA 5.4% (Robinhood 11-26, graph)
  - RSGP 4.2% (Base 11-15)
  - REI 1.2%
  - AERO 1.04% (Base 11-15)
  - cbZEC 0.9%
- Worst overall: AMC 65% ($48 fee), DJT 46% ($0), RBLX 32% ($0), TAROT 29% ($0). All thin-pool fallback.
- Full list: `price-errors-top30-recommended.json`.

Findings that shaped the recommendation:
- **Chainlink tokenized-stock feeds are not good anchors.** The Robinhood "<TICKER> / USD" feeds were stale
  48-52 h on Sunday 11-01 (44 reads older than 26 h over the 6 days). Off-hours they differ from the on-chain market by 3-17% (CRCL 16.8% on 11-15,
  COIN 10%, INTC 13.6%, USO 8.8% on Thanksgiving). Use them as a cross-check only. Tier B adds ~nothing once the graph
  runs: 99.25% vs 99.15% coverage.
- **Symbol matching is unsafe; anchors must be a curated address list.**
  - Base has 6 tokens named USDC. One "USDC" (0x584f…49c4) holds $2.1M of "balance" in Aero pools, and DL has no price for it.
  - The Base token with the most LINK liquidity is "Ztaysmile Chainlink LINK".
  - There are two Base USDTs (0x3ea5…ba67 "USDT" vs 0xfde4…9bb2 "Tether USD").
  - For this scoping I picked the address whose DL price matched the feed (dev-only, once). Production needs a reviewed
    per-chain address table in YAML (§10).
- **The floor matters on small chains.** At $50K, 11-29% of Ink and 6-27% of Robinhood fee value falls to the fallback
  (PONS/USDG holds $16K of USDG). The $10K graph plus the pool-local fallback keeps the fallback at ≤ 5.5% everywhere,
  except Ink on 10-22 (29% of $25) and 10-23 (11% of $50).
- **TWAP vs spot**: a 30-min CL `observe()` TWAP changes totals by ≤ 0.05%. It costs one extra inner call per CL pool,
  so keep it for manipulation resistance on the graph edges.
- The **tape VWAP** (day Δvolume ratio, state only) is worse per token (2-17% on single tokens) and is not recommended.
- The **pool-local method alone** is almost as good in aggregate. But a token is then priced differently in each pool,
  and a thin pool's end-of-day spot price can be pushed. The global graph with a floor prices the dominant fee tokens;
  pool-local only mops up the tail.

## 4. Contract set re-verification and pool growth (MEASURED)

Checks at head (2026-11-27 ~18:35Z; Base block ≈ 63.07M):
- Every chain: `stablePoolFactory.poolTape()` = `volatilePoolFactory.poolTape()` = PoolTape
  **0x34bdD64B19D8631F936c2D07F19AAa6B83515992**, with `poolTapeGasLimit` = 200,000.
- `CLFactory.clPoolTape()` = CLPoolTape **0x27D5EB73e7406675F6B0CbD037490ec3dba935a4**.
- `defaultSwapHook()` = DynamicSwapFeeHook **0xC0ed888AfE87ed1AcF01D9f19bB850159e3ce434**. Its `FACTORY()` = that
  chain's CLFactory and `recordCallGasLimit()` = 250,000.
- Every CL pool's `getPoolSwapHook(pool)` = that hook.
- The same getters at the **2026-10-22 00:00Z block** returned the same tapes on all 7 chains, so archive reads work
  (blocks: Base 52,918,927; ETH 26,244,425; OP 158,514,212; ARB 517,064,902; Ink 59,128,789; Robinhood 94,682,515;
  Arc 27,194,601). Elysium starts 2026-11-08 (DL).

`allPoolsLength()`:

| chain | at 10-22 00:00Z (V2s/V2v/CL) | 11-09 scoping | now (V2s/V2v/CL) | gauged 11-09 → now |
|---|---|---:|---|---|
| Base | 18/194/406 = 618 | 934 | 28/325/710 = **1,063** | 310 → **321** (4 with emissionCap 0) |
| Ethereum | 0/0/56 | 109 | 1/5/123 = **129** | 59 → 62 |
| OP | 21/32/30 | 108 | 22/38/57 = **117** | 32 → 32 |
| Arbitrum | 0/0/30 | 67 | 0/5/78 = **83** | 36 → 56 |
| Ink | 0/1/14 | 21 | 0/4/36 = **40** | 13 → 28 |
| Robinhood | 0/0/72 | 95 | 0/4/116 = **120** | 70 → 81 |
| Arc | 0/0/6 (+35 Lite CL) | 15 | 1/6/12 = **19** (+35 Lite CL, 1 Lite gauge, cap 0) | 6 → 7 |
| Elysium | — | — | 0/3/31 = **34** | — → 8 |

**New finding, the tape registration gap.**
- A pool's swaps reach the tape only after the tape owner calls `setAllowedCallerAndInitializePool`. Until then
  `record()` reverts `Unauthorized` and the fail-open `excessivelySafeCall` swallows it.
- Unregistered (`allowedCaller(pool)` = 0) now: Base 345 of 1,063, ETH 43, OP 18, ARB 23, Ink 8, Robinhood 23, Arc 40
  (29 of them Lite), Elysium 16.
- **Only one is gauged** (Ethereum). Its fees still reach allocators through `gaugeFees`, but they are missing from the tape gross.
- Sized from Swap logs for 11-26 (`unregistered-pools-2026-11-26.json`): Base 67 pools / 1,154 swaps / ≈ $55; Elysium
  $39; Ink $8.5; others < $1. That is **≈ $105/day, 0.04% of gross**. CL fees are estimated with `fee()`, V2 fees from
  `Fees` events.
- No fees showed up on the tape in pools created during the measured days, so first-day fees of new pools are lost
  until registration.

## 5. Tape semantics (source: dromos-labs/metadex-public V3/src, metadex-slipstream-public contracts)

**`PoolTape.accumulators(pool)`** (public mapping) returns 10 words:
- fields: `cumulativeFee0, cumulativeFee1, cumulativeVolume0, cumulativeVolume1, cumulativeMevVolume0,
  cumulativeMevVolume1, cumulativeMevFee0, cumulativeMevFee1` (uint128, raw token units), then `lastSwapTimestamp`,
  `swapCount` (uint48).
- Written from `Pool.swap()` → `PoolFactory.recordPoolTape()`.
- `_validateGasLeft` reverts the swap if gas ≤ limit, so a starved swap reverts rather than skipping the tape.
- Then `excessivelySafeCall(200k)` to `PoolTape.record`, **fail-open** if the tape reverts.
- `fee0 = amount0In × fee / 10,000`, where `fee` = base + MEV fee (`PoolFactory.getFee`: `_fee += _mevFee`). This is the
  **full fee** sent to `PoolFees`, all LPs. The staked share is the gauge's LP balance share.

**`CLPoolTape.accumulators(pool)`** returns a 20-word struct:
- fields in order: `lastSwapTimestamp, lastObservationTimestamp, swapCount, lastTick, intervalMaxTick, intervalMinTick,
  intervalOpenTick, volatilityCorrob, cumulativeVolume0, cumulativeVolume1, intervalSwapCount, cumulativeFee0 (word 11),
  cumulativeFee1 (12), ringHead, ringCount, cumulativeMevVolume0, cumulativeMevVolume1, nOver, cumulativeMevFee0 (18),
  cumulativeMevFee1 (19)` (uint120 amounts).
- Written by the **swap hook**, not by the pool: `DynamicSwapFeeHook.afterSwap` calls `excessivelySafeCall(250k)` to
  `CLPoolTape.record`, fail-open, and only if `FACTORY.clPoolTape() ≠ 0`.
  - `fee = inputAmount × (dynamicFee + mevFee) / 1e6`, rounded up, on the input token, recorded in fee0 or fee1.
  - So it is the **total swap fee before the pool's staked/unstaked/gauge split**, MEV included (`cumulativeMevFee` is
    the MEV part of it; do not add it again).
- Consequence: **a CL pool moved to another hook would silently stop recording.** Check `getPoolSwapHook` daily.
- Registration seeds the accumulator with 1-wei sentinels (`cumulativeFee0 = 1`, swapCount = 1) and the first swap
  overwrites them. A snapshot whose `lastSwapTimestamp == 0` must count as 0.

**Block convention**: eth_call at block N returns the state *after* N. The tape delta between the two boundary blocks
covers blocks (s, e]. Read at `s−1` and `e−1` to cover [s, e) exactly. The 1-hour check below showed ±1 swap per pool
from this. The day files use s / e, which is one block off at each end (negligible: 1 of 432K blocks on Base).

**MEV**: `cumulativeMevFee` across all pools was $0-83/day (MEASURED, DL-priced); 11-07 was ≈ $4.

**1-hour spot check** (Base, 2026-11-26 12:00-13:00Z, blocks 62,520,122-62,538,122;
`spotcheck-base-2026-11-26T12.json`). Every pool's tape delta was compared with its Swap/Fees logs (21,238 logs,
8 getLogs):
- **718 registered pools: swap counts equal in all but 8 pools, each ±1** (the block boundary). Volumes are equal except in the same boundary-shifted pools.
- **V2: Σ`Fees` events = tape Δfee exactly in all 26 pools with swaps**, e.g. WETH/VVV 0xcfc7…b2a5: 71 swaps, effective
  rate 30.00 bps on both sides.
- Busiest CL, WETH/cbBTC 0xec3c…74c2: 1,514 swaps on both sides; Δvolume0/1 equal to Σ|amount| from logs to the wei;
  fee / input = **8.500 bps** on both tokens. That rate is the hook's dynamic fee; the event carries no fee field.
- No swap of a registered pool was missing from the tape. 31 swaps in 8 unregistered pools were absent, as expected.

## 6. Allocator accrual

- Recommended: `alloc = Δ raw pending + Σ FeesCollected(gauge, token, amt)` over the day.
  - Raw pending is CL `pool.gaugeFees()` and V2 `pool.pendingFees(gauge)`.
  - `FeesCollected` is emitted by the VRM. One eth_getLogs per chain per day (address = all VRMs, topic0 only).
    Base 2.1K-9.5K logs/day; Ink needs 9-10 calls (10K-block cap).
  - The gauge's own `pendingFees()` returns 0 when emissionCap = 0 or the gauge is not activated, so read the pool side.
  - Measured raw − gated difference: ≤ $1/day. The 4 Base cap-0 gauges and 1 Arc cap-0 gauge accrue ≈ $0-1/day.
  - No negative per-pool accruals on any chain-day.
- **State-only alternative tested and rejected**: Δ`VRM.feeRewardPerVotingPower().feeReward_i` × `totalSupply()/1e24`
  + Δ`bufferedFees` + Δ(pending − `lastPendingFees`).
  - It matched within ~3% on some days but blew up by 10³-10¹⁷× on chain-days where a VRM's voting supply was near zero
    or changed intraday. The accumulator increment uses the supply at notify time, which a two-snapshot read cannot recover.
  - No cumulative per-gauge fee counter exists in V2Gauge, CLGauge or VRM. `GaugeTape` records emissions
    `rewardPerToken` only.
  - So the allocator share needs one log scan per chain-day: rung 2 of Mike's ladder, a multi-address log scan.
- A cheaper gauge list: `FactoryRegistry.gaugeFactories()` → `factoryToGauges(gf)` → `gaugeToTarget` / `gaugeToRewards`
  (DL uses this). It replaces 4 calls per pool with ~3 calls per gauge.

## 7. Costs (MEASURED per chain-day, recommended method incl. pricing reads at the end block; `rpc_cost` in each day file)

| chain | pools | gauged | multicall eth_calls | inner calls | eth_getLogs | HTTP requests | wall s |
|---|---:|---:|---:|---:|---:|---:|---:|
| Base | 1,059 | 321 | 58 | 12,555 | 1 | 12 | 13.8 |
| Ethereum | 128 | 62 | 13 | 1,894 | 1 | 8 | 5.0 |
| OP | 117 | 32 | 11 | 1,337 | 1 | 8 | 4.6 |
| Arbitrum | 82 | 56 | 10 | 1,476 | 1 | 8 | 5.6 |
| Ink | 40 | 28 | 7 | 734 | 10 | 17 | 8.3 |
| Robinhood | 119 | 81 | 13 | 2,135 | 1 | 8 | 5.8 |
| Arc | 54 | 8 | 8 | 518 | 1 | 8 | 4.0 |
| Elysium | 33 | 8 | 7 | 365 | 1 | 8 | 4.7 |
| **all (11-26)** | | | **127** | **21,014** | **17** | **77** | **52** |

Breakdown of the per-pool load:
- Inner calls per pool: 2 tape reads (both boundaries) + 5 pricing reads at the end block. Each gauged pool adds 16
  (8 per boundary, including the VRM state needed only for the rejected state-only test; drop to 2 per boundary in production).
- Block search: first block with ts ≥ boundary, timestamp-interpolated bisection. 10-18 `eth_getBlockByNumber` per
  boundary per chain (Robinhood 18, ~800K blocks/day; Base 10).
- Incentive programs: +923 inner calls per day (all chains).
- Enumeration (allPools, tokens, gauges): ~5 multicalls per chain, once, then incremental from `allPoolsLength`.

A **backfill 2026-10-22 → release (~45 days)** shares the day boundaries, and Elysium only starts 11-08:
- ≈ 45 × 130 ≈ **5.9K multicall eth_calls (~0.95M inner calls)**, **~800 eth_getLogs** and **~4.5K header reads**.
- ≈ 40 min at the measured pace, in batches of 10 multicalls per HTTP request.
- Multicall chunks of 200-250 inner calls went through everywhere. CL accumulators return 640 bytes each.

Provider behaviour: no 429s and no archive gaps on any chain back to 10-22. The only error class seen was Ink's
`eth_getLogs ... up to a 10000 block range` (handled by windowing). Robinhood (~800K blocks/day), Arc (~170K/day) and
Elysium (~400K/day) served a full-day VRM-filtered getLogs in one call.

## 8. Edge cases (MEASURED; `edge-cases.json`)

- **Pools created mid-day**: 0-42 per chain-day (Base 42 on 10-22). They are absent at the start block and taken as 0;
  they had $0 of tape fees on all measured days (see the registration gap).
- **Killed gauges** (emissionCap 0): 4 on Base, 1 on Arc Lite. Fees still accrue to `gaugeFees` but are not collectible
  (`collectFees` no-ops) until reactivation or `flushFees`. Measured ≤ $1/day.
- **Fee-on-transfer / rebasing**:
  - No V2 pool with > $100 reserves had `balanceOf` ≠ reserves by > 0.1% on any day.
  - The V2 tape fee equals the `Fees` events to the wei.
  - CL pools cannot be checked this way. A rebasing token's fee in CL accrues in the pool without changing
    `cumulativeFee`, so the tape stays the swap-time amount (correct for "fees paid").
- **Fail-open tape**: see §5; no drops among registered pools in the hourly sample. Unregistered pools are the real gap
  (≈ $105/day).
- **Arc Lite** (separate tape, no gauges) is in DL's Aero fees but is not allocator revenue. Keep it as a gross-only line,
  or drop it (≤ $12/day now).
- **Stable pools**: `stable()` reverts on these pools (the curve is per factory). Use the factory to decide the curve.
  Before this fix, msUSD on OP read 52% off.
- **Legacy Aerodrome V1/Slipstream, Velodrome**: separate contracts, not sAERO. $31-39K/day of fees, of which $2.5-5K is DL
  revenue (gauges locked since 10-15, Foundation reclaim). Exclude.

## 9. Open questions

1. **Add Elysium as the 8th chain** (Aero docs and DL both have it, 3% of fees). It has no Chainlink feeds: is the
   cross-chain anchor (Base USDC/HYPE/BTC feeds for Elysium USDC/WHYPE/UBTC) acceptable?
2. Which number is the revenue line: **gross tape fees** (+ incentives), or **allocator accrual** (+ incentives)? They
   are 88.5-95% apart, and DL's `dailyHoldersRevenue`, the current prod series, is allocator + incentives. Incentives were
   $93K/day at launch and ~$3K/day now. Counting them follows DL; the CRV precedent puts them below the line.
3. Curated anchor table: who signs off the per-chain addresses (§10)? Should tokenized-stock feeds be excluded (recommended)?
4. Ask Aero, or monitor: the tape owner registers pools by hand. Do they plan to register all pools? Monitor the
   unregistered count and whether a gauged pool is unregistered (one on Ethereum now).
5. Read at `s−1`/`e−1` (exact [s, e)). DL does the same.
6. DL has no price for some launch-day tokens (AERO on 10-22). The on-chain method has none of that gap, so the
   historical series will differ from the stored DL rows on 10-22.

## 10. Addresses (chain, role, address, how verified)

All chains (same address everywhere; the getter result is MEASURED at head and at 10-22 00:00Z, and the address matches
the deployment JSONs and the Aero docs):
- PoolTape 0x34bdD64B19D8631F936c2D07F19AAa6B83515992: `poolTape()` of both V2 factories.
- CLPoolTape 0x27D5EB73e7406675F6B0CbD037490ec3dba935a4: `CLFactory.clPoolTape()`.
- StablePoolFactory 0x78589E876edcEbdce72ee3436ab3c9AD3a7cEF2D and VolatilePoolFactory 0x8E6a9FCd1d638CC760Ffba397605Fe3355dE76D2:
  `allPoolsLength()`/`allPools(i)`.
- DynamicSwapFeeHook 0xC0ed888AfE87ed1AcF01D9f19bB850159e3ce434: `defaultSwapHook()` and `getPoolSwapHook(pool)` for
  every CL pool; `FACTORY()` = the chain's CLFactory.
- CLGaugeFactory 0xf437f62053ACB121665b8fDBfeA8F214FB8E589d: `computeGaugeAddress` + `isGauge`.
- LeafVoter 0x382409fad8503FbCdbB27A4211551fa03e884078: `isActivated(gauge)`.
- Multicall3 0xcA11bde05977b3631167028862bE2a173976CA11: `eth_getCode` on all 8 chains.

Per chain: CLFactory / V2 GaugeFactory (stable, volatile). From the deployment JSONs (Elysium: Aero docs) and used on chain.

| chain | CLFactory | GaugeFactory stable | GaugeFactory volatile |
|---|---|---|---|
| Base | 0x9CB220581b91b0C83223012FE69688b92aD07a76 | 0x1e0f776E88649285f99e65Fa599aD6e0f9D97800 | 0x9FBCf2Df0DC553ce40Ef63963Bff465b76792B7E |
| Ethereum | 0xF4Fd2E6c5B60c5b365cd1B96DD6245E6D60414c2 | 0xCCe24256a8a6070A9E308f23E044C87C343F98Cd | 0x7F83235643181E440433400a027618Cd50879751 |
| OP | 0xfeaB42D90055db3a0616249f76B6002D72266778 | 0x3924b18EDd37267dab6eDd99a3Bb339bf2b668fD | 0x1B5D13975371806D699dC616A96D15B8eD26e5Ca |
| Arbitrum | 0x88a60ee77392577c355C0acb2A8d476D5a4EC03a | 0x94AF9F874e92F05F42aE55FfC793b9F4f5FFc135 | 0xBbdDdd5ac17a672B360D2dBAa996468aDBEF8692 |
| Ink | 0x7660BF2aDefC687C22906112ca323d60A00358cF | 0xd9eF1acdca62010e93370f5932E3deD127E65396 | 0x1733cD126a227066963E9B636Ad49898d1224741 |
| Robinhood | 0xc63d7338c178e805c544B8f897066bD3BBcBE136 | 0x1733cD126a227066963E9B636Ad49898d1224741 | 0xCCe24256a8a6070A9E308f23E044C87C343F98Cd |
| Arc | 0x7F83235643181E440433400a027618Cd50879751 | 0x9520C671C767B170c9f04e523B4e68c5d537779b | 0xBDcB4929b19EBcfEE5eFE100B829c9B35C16d8F8 |
| Elysium | 0xEfd7A089D3057F05189B05f74Ffcf30610c42891 | 0xb89Df768aF2CFE637ceB352c587Fe8edAf491d03 | 0xf2E6DB898840e0ae91C44E1BDDEA16B50a369862 |

Elysium FactoryRegistry 0xdd1705e23762F4D6e44D8C31BD8Ea80c54612239 (`CLFactory.factoryRegistry()` MEASURED, = docs).

Arc Aero Lite: PoolTape 0x8Da07EfaBCF124B61671Df449BC73292D4B56c25, CLPoolTape 0x967f5352A6448e22D7361E149103350c49345Ee9,
CLFactory 0xb89Df768aF2CFE637ceB352c587Fe8edAf491d03, hook 0xaAf164008441F112eB2858d9F7A2dB1B84b1E415, CLGaugeFactory
0xa02d1F4E4243ff0d350F478c44B0Fd37c7bF848C. Source: `cllitelaunch-arc.json`, `arclitelaunch-arc.json`, `clliteupgrade-arc.json`;
the factory getters were read on chain.

Tier-A Chainlink anchors: token → feed proxy, `description()` read on chain. The token address was cross-checked once
against the dev-only price.

| chain | anchors (token → Chainlink feed proxy, description() on chain) |
|---|---|
| base | WBTC 0x0555e30da8f98308edb960aa94c0db47230d2b9c → 0xCCADC697c55bbB68dc5bCdf8d3CBe83CdD4E071E (WBTC / USD); USDC 0x833589fcd6edb6e08f4c7c32d4f71b54bda02913 → 0x7e860098F58bBFC8648a4311b374B1D669a2bc6B (USDC / USD); WETH 0x4200000000000000000000000000000000000006 → 0x50015f8b17fb2C290Dde41fDc246ed0dcEE93a8b (ETH / USD); USDT 0xfde4c96c8593536e31f229ea8f37b2ada2699bb2 → 0xf19d560eB8d2ADf07BD6D13ed03e1D11215721F9 (USDT / USD); DAI 0x50c5725949a6f0c72e6c4a641f24049a917db0cb → 0x591e79239a7d679378eC8c847e5038150364C78F (DAI / USD); EURC 0x60a3e35cc302bfa44cb288bc5a4f316fdb1adb42 → 0x9867186e52d2F1C2c565CDA6E747101Fa56501e0 (EURC / USD); USDS 0x820c137fa70c8691f0e44dc420a5e53c168921dc → 0x2330aaE3bca5F05169d5f4597964D44522F62930 (USDS / USD); cbBTC 0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf → 0x10509b4053385b49145Fab2D6B1c58e96Eac5b79 (CBBTC / USD) |
| ethereum | EURC 0x1abaea1f7c830bd89acc67ec4af516284b1bc33c → 0x04F84020Fdf10d9ee64D1dcC2986EDF2F556DA11 (EURC / USD); DAI 0x6b175474e89094c44da98b954eedeac495271d0f → 0xAed0c38402a5d19df6E4c03F4E2DceD6e29c1ee9 (DAI / USD); USDC 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 → 0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6 (USDC / USD); WETH 0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2 → 0x5147eA642CAEF7BD9c1265AadcA78f997AbB9649 (ETH / USD); cbBTC 0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf → 0x7922912AB91eb6A4b0350b01Dd066994BA64f882 (CBBTC / USD); USDT 0xdac17f958d2ee523a2206206994597c13d831ec7 → 0x3E7d1eAB13ad0104d2750B8863b489D65364e32D (USDT / USD); USDS 0xdc035d45d973e3ec169d2276ddab16f1e407384f → 0xfF30586cD0F29eD462364C7e81375FC0C71219b1 (USDS / USD); USDG 0xe343167631d89b6ffc58b88d6b7fb0228795491d → 0x14f0737d6b705259e521EA6E9E3506AC78dBd311 (USDG / USD) |
| optimism | USDT 0x94b008aa00579c1307b0ef2c499ad98a8ce58e58 → 0xECef79E109e997bCA29c1c0897ec9d7b03647F5E (USDT / USD); USDC 0x0b2c639c533813f4aa9d7837caf62653d097ff85 → 0x16a9FA2FDa030272Ce99B29CF780dFA30361E0f3 (USDC / USD); WETH 0x4200000000000000000000000000000000000006 → 0x13e3Ee699D1909E989722E753853AE30b17e08c5 (ETH / USD); WBTC 0x68f180fcce6836688e9084f035309e29bf0a2095 → 0x718A5788b89454aAE3A028AE9c111A29Be6c2a6F (WBTC / USD); DAI 0xda10009cbd5d07dd0cecc66161fc93d7c9000da1 → 0x8dBa75e83DA73cc766A7e5a0ee71F656BAb470d6 (DAI / USD); EURC 0xdcb612005417dc906ff72c87df732e5a90d49e11 → 0xDb2A51a5DD73865F1b0d1c33F99a96E0e7ae742c (EURC / USD) |
| arbitrum | USDG 0x004b506865409877c9fa29bfb1eba929984b9bbc → 0xE9Bd4Ca2CDacb56cd06c9C4C5231e69c33340B3c (USDG / USD); WBTC 0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f → 0xd0C7101eACbB49F3deCcCc166d238410D6D46d57 (WBTC / USD); WETH 0x82af49447d8a07e3bd95bd0d56f35241523fbab1 → 0xe4D040128CFdF03eC221832251caC9b6f0515E3f (ETH / USD); USDC 0xaf88d065e77c8cc2239327c5edb3a432268e5831 → 0x0D0FaDDd42C53fc6d1b933C7ccccCFaF9B79B571 (USDC / USD); DAI 0xda10009cbd5d07dd0cecc66161fc93d7c9000da1 → 0xc5C8E77B397E531B8EC06BFb0048328B30E9eCfB (DAI / USD); USD₮0 0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9 → 0x158B2203D267a50BE9b7930D13d8247A4968D659 (USDT / USD) |
| ink | USD₮0 0x0200c29006150606b650577bbe7b6248f58470c1 → 0x5aF168556BaA3Bd5c232261F7D7C662a2Ed0Db85 (USDT / USD); USDC 0x2d270e6886d130d724215a266106e6832161eaed → 0x89991637dbaCd0999dE1bc8e86330302EAd2CD89 (USDC / USD); WETH 0x4200000000000000000000000000000000000006 → 0x963d5d3aD2Dfd3fe759d376fF62A0963176DBdF5 (ETH / USD); USDG 0xe343167631d89b6ffc58b88d6b7fb0228795491d → 0xdb3B1fa77CF2c9597f9d4871Bed1Df03D096fdf3 (USDG / USD) |
| robinhood | WETH 0x0bd7d308f8e1639fab988df18a8011f41eacad73 → 0x78F3556b67E17Df817D51Ef5a990cDaF09E8d3A9 (ETH / USD); USDG 0x5fc5360d0400a0fd4f2af552add042d716f1d168 → 0x61B7e5650328764B076A108EFF5fa7282a1B9aD2 (USDG / USD); cbBTC 0xcec185eb182c47d1ba1efc84e6959e18cd620be4 → 0x0009cD492adf8167f9eEBf1293556A673530a21a (CBBTC / USD) |
| arc | WETH 0x128cc466b61f542da60c70e3aa11c10e19b84edb → 0x50FCDD99D6762D1C170DC6A9111db944AEE6D364 (ETH / USD); USDC 0x3600000000000000000000000000000000000000 → 0x84EA90AC252Dc437031461836DB5164219147905 (USDC / USD); EURC 0xbef5f6d51cb62b58e6a8f77868681825c6fe21c1 → 0x361b95c10b76Ca3f35C686d423e43A951755Bf23 (EURC / USD) |
| elysium | USDC 0xb47c4c8f73f009cc0c0d3f92b388d13e293f0b65 → base 0x7e860098F58bBFC8648a4311b374B1D669a2bc6B (USDC / USD); WHYPE 0xba876237b0f021a6c6d852d6c26e107997cc5e81 → base 0xEdB56c5DE751eD3182DDa337f7d9ab33cf091DcA (HYPE / USD); UBTC 0xe9c29585eae4b9a55b02a9605aea892b40d972e8 → base 0x32F587986D3fb47601157c19615d568BeD0BCabc (BTC / USD) |

Full addresses of every anchor, feed and tier-B feed: `onchain-revenue-data/anchors-chainlink.json`. Feed proxies come
from Chainlink's reference-data directory (CLAIMED https://reference-data-directory.vercel.app/feeds-*.json) and were
verified by `description()` on chain.

## Files (`onchain-revenue-data/`)
- `<day>.json` (6 days): per chain blocks, pool counts, every pricing method's coverage/error, per-token amounts with
  on-chain and dev-only prices, rpc cost, DL fees/revenue.
- `summary-table.json`: the rows of §2.
- `raw/<day>_<chain>.json` (45): per-pool tape snapshots at both blocks, gauge/VRM state, collected logs, reserves,
  slot0, TWAP tick, balances.
- `price-errors-top30-recommended.json`, `incentives-streamed.json`, `edge-cases.json`, `unregistered-pools-2026-11-26.json`,
  `spotcheck-base-2026-11-26T12.json`, `legacy-dl-claimed.json`, `anchors-chainlink.json`.
- `scripts/`: the measurement code. It reads the key from orion/.env and never prints it.
  Run `run_days.py <days> [chains]`, then `final_eval.py`.
