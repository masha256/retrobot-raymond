# Phase 3 R2 scoping: on-chain prices for cvxCRV, sdCRV, yCRV (CRV liquid-locker wrappers)

Read-only scoping, 2026-11-13. Spec: §3.1 (method 2: Curve wrapper/CRV pool x CRV price, one independent check) and §4.
Tags: **MEASURED** = read on chain by me (block/date given). **CLAIMED** = from a third party (source given).
CoinGecko figures are a **DEV-ONLY REFERENCE** (`api.coingecko.com` public `market_chart/range`, hourly) and must not go into live code.

Blocks used (12:00 UTC on each date, by binary search on block timestamps):

| date | block |
|---|---|
| 2026-05-01 | 24,999,953 |
| 2026-05-13 (rebuild start) | 25,086,074 |
| 2026-06-15 | 25,322,760 |
| 2026-08-15 | 25,760,304 |
| 2026-10-15 | 26,197,772 |
| now (2026-11-13 14:40Z) | 26,406,702 |

There was also a series of 66 points, one every 3 days (21,600 blocks) from 24,999,953 to 26,403,953. Each point is one Multicall3 `aggregate3`
eth_call with 15 reads. Scratch data: `~/.hermes/profiles/raymond/cache/scratch/wrappers_series.json`, `wrappers_probe.json`, `cg_series.json` (it is pruned after 24 h).

## 1. What the refs price (from the YAMLs)

- `price_usd` on cvxcrv/sdcrv/ycrv: `coingecko` convex-crv / stake-dao-crv / yearn-crv, read as a level.
- `coingecko:yearn-crv` in the `prices` table is **yCRV/USD**. ycrv.yaml uses it in `flow_usd.yearn_styc_fee`: st-yCRV shares x `st_ycrv.pricePerShare()` x yCRV. So the yCRV level and this ref are the same chain price.
- `coingecko:crvusd` is **crvUSD/USD**. It prices the yvcrvUSD-2 shares (`share_price: yv_crvusd.pricePerShare`) in `flow_usd.fees` and `yearn_revenue`, plus the crvUSD flows of all three wrappers. It is not a wrapper price. Chainlink **CRVUSD / USD** `0xEEf0C605546958c1f899b6fB336C20671f9cD49F` exists and reads at every block back to 2026-05-01 (MEASURED: 0.99930 on 05-01, 0.99718 now). Its check belongs to the CRV/crvUSD scoping task.
- Both share-price reads are already on chain and archive-readable back to 2026-05-01 (MEASURED). `yv_crvusd.pricePerShare` was 1.14076 on 05-01 and 1.16835 now. `st_ycrv.pricePerShare` was 2.44375 on 05-01 and 2.66749 now. Nothing new is needed for them.
- CRV/USD in all figures below is Chainlink **CRV / USD** `0xCd627aA160A6fA45Eb793D19Ef54f5062F20f33f` (8 decimals, `latestRoundData`). It is assumed from the CRV scoping task; I did not vet it. Its `updatedAt` lag at the sample blocks ran from about 1 min to 6.6 h (MEASURED; 05-01: 6.6 h). The CRV task should state the heartbeat and deviation.

## 2. Pools (MEASURED unless marked)

Pools were discovered via the Curve API `getPools` and GeckoTerminal (dev-only discovery). Interfaces and balances were then read on chain.
All three primary pools are minimal proxies of the same implementation `0xc629a01ec23ab04e1050500a3717a2a5c0701497`, labelled **StableSwap2EMAOracle** on Blockscout. This is the old (2022-23) Curve factory plain 2-coin stableswap with an EMA oracle, **not stableswap-ng**. Coins: `coins(0)` = CRV, `coins(1)` = the wrapper. `price_oracle()` takes no argument and returns the wrapper in CRV, which I confirmed against `get_dy(1,0,·)`. The `price_oracle(uint256)` and `last_price(uint256)` variants revert.

| wrapper | primary pool | A / fee | balances now (CRV / wrapper) | TVL now | EMA `ma_exp_time` | others with any depth |
|---|---|---|---|---|---|---|
| cvxCRV | `0x971add32Ea87f10bD192671630be3BE8A11b8623` "cvxCrv/Crv" | 50 / 0.15% | 2,298,900 / 58,594,590 | ~$6.3M (MEASURED: balances x price) | 2597 s (τ; half-life ~30 min) | `0x9D0464996170c6B9e75eED71c68B99dDEDf279e8` old cvxCRV/CRV factory plain, no oracle, 56,098 / 1,432,443, ~$0.27M. `0x31c325A01861c7dBd331a9270296a31296D797A0` cvxCRV/crvFRAX factory **crypto** pool with its own `price_oracle()`, 61,330 cvxCRV / 5,844 crvFRAX, ~$12-17K. Uni v3 `0xa5ae4fba…` cvxCRV/CRV 1%, ~$14K (CLAIMED, GeckoTerminal); its `slot0` was **frozen from 05-01 to 08-15**, so it is unusable. |
| sdCRV | `0xCA0253A98D16e9C1e3614caFDA19318EE69772D0` "sdCRV/CRV" | 37 / 0.25% | 409,311 / 7,040,601 | ~$0.96M | **865 s** (half-life ~10 min) | `0xf7b55C3732aD8b2c2dA7c24f30A69f55c54FB717` factory plain, no oracle, **217 CRV / 3,096 sdCRV (~$430)**. The asdCRV/sdCRV stableswap-ng pools hold 0. The Uni v4 / DODO pools hold < $2K (CLAIMED, GeckoTerminal). |
| yCRV | `0x99f5aCc8EC2Da2BC0771c32814EFF52b712de1E5` "yCRV" | 50 / 0.15% | 386,113 / 7,803,045 | ~$1.04M | 2600 s (half-life ~30 min) | `0x453D92C7d4263201C69aACfaf589Ed14202d83a4` factory plain, no oracle, 2,333 / 46,984 (~$6K). Uni v4 yCRV/USDT pool id `0x58254fd7…dda4` (read via StateView `0x7fFE42C4…7227` `getSlot0`), ~$7K (CLAIMED, GeckoTerminal), live from block ~25,280,753 (≈2026-06-09). |

Every pool is heavily one-sided: wrapper is 94-96% of each primary pool. `ma_exp_time` was the same on 2026-05-01 (MEASURED).

### Pricing read and manipulation resistance (MEASURED now, 2026-11-13)

Three reads are available on every primary pool: `price_oracle()`, `last_price()` and `get_dy`.
- **`price_oracle()`** is the EMA, time-decayed to the block it is read at. It is the read to use for a 1 h price.
- `last_price()` is the post-trade spot of the last swap.
- `get_dy` is the executable spot; it includes the fee.
- `ema_price()` is the stored EMA as of the last update. Do not use it, because it is stale between trades.

Agreement between the EMA and the same pool's own `get_dy(100)/(1-fee)`, over the 66-point series:

| pool | median abs gap | p90 | max |
|---|---|---|---|
| cvxCRV | 0.03% | 0.30% | 4.9% |
| sdCRV | 0.01% | 0.17% | 0.77% |
| yCRV | 0.03% | 0.44% | 1.08% |

The cvxCRV max (+4.9%) was at block 25,583,153 (~2026-07-21). It was a real move, not an outlier: the second pool showed the same +4.94%. The EMA lagged the move. Any check tolerance has to absorb this kind of lag.

Price impact relative to the EMA, now. Each figure is the average execution price, fee included:

| pool | sell 100K wrapper | sell 1M wrapper | buy with 50K CRV | buy with 200K CRV |
|---|---|---|---|---|
| cvxCRV | -1.1% | -9.8% | +1.4% | +4.9% |
| sdCRV | -6.1% | -47% | +5.5% | +18% |
| yCRV | -6.4% | -49% | +5.8% | +19% |

On manipulation:
- The EMA ignores same-block spot, so a one-block sandwich cannot move `price_oracle()`.
- To shift the hourly read by X%, someone must hold the pool skewed for about τ: 43 min for cvxCRV and yCRV, but only 14 min for sdCRV.
- For sdCRV and yCRV, about 50K CRV (≈$12K) moves the price about 5%. That is cheap, but the attacker carries arbitrage losses while holding it.
- Orion is a valuation pipeline and nothing liquidates on its price, so the incentive to manipulate is low. The real risk is thin-pool noise, not attack.
- I did not verify whether this implementation caps `last_price` the way stableswap-ng does.

## 3. Per-wrapper table

Notes for the table:
- "Gap" is check / primary − 1, over the 66-point series from 2026-05-01 to 2026-11-13.
- get_dy reads are divided by (1 − fee) to get the spot.
- USD = `price_oracle()` x Chainlink CRV/USD.

| | cvxCRV | sdCRV | yCRV |
|---|---|---|---|
| **Primary read** | `0x971a…8623.price_oracle()` x CRV/USD | `0xCA02…72D0.price_oracle()` x CRV/USD | `0x99f5…E1E5.price_oracle()` x CRV/USD |
| **Independent check (best available)** | `get_dy(1,0,100e18)` on old pool `0x9D04…79e8` (~$0.27M) | `get_dy(1,0,10e18)` on `0xf7b5…B717` (**~$430: not a real check**) | `get_dy(1,0,10e18)` on `0x453D…83a4` (~$6K). Alternative: Uni v4 yCRV/USDT `getSlot0` (~$7K; USD route, independent of CRV) |
| **Gap: median / p90 / max abs** | 0.12% / 0.42% / 4.94% (max at the 07-21 EMA lag). Signed mean +0.02% | 1.43% / 3.10% / 6.00%. **Biased: signed mean -1.40%** | 0.46% / 1.03% / 1.75%. v4: 1.14% / 1.95% / 2.66% (n=53, from 06-09) |
| **Second check (optional)** | cvxCRV/crvFRAX crypto pool: crvFRAX `get_virtual_price` (`0xDcEF…41A2`) / pool `price_oracle()` = cvxCRV in USD, independent of the CRV feed. Gap vs primary USD: 0.93% / 1.62% / 3.46%, signed +0.90% (about $1.016 FRAXBP vs a USD peg, plus thin depth) | none | — |
| **Archive OK to 2026-05-01** | yes: primary, old pool and FraxBP pool all read at 24,999,953 | yes: both pools | primary and small pool yes. **v4 no**: the pool did not exist before ~06-09 |
| **Calls per hourly point** | 1 eth_call: Multicall3 with `price_oracle` + check `get_dy` (+ CRV feed). Without multicall: 2 (+1 CRV) | same | same |
| **Gap at the 4 dates: check vs primary** (MEASURED) | 06-15 −0.08%. 08-15 −0.05%. 10-15 +0.07%. now −0.21% | 06-15 −1.74%. 08-15 −0.55%. 10-15 −1.50%. now −1.42% | 06-15 −0.69%. 08-15 −0.35%. 10-15 −0.30%. now +0.18% |
| **Chain USD at the dates** (05-13 / 06-15 / 08-15 / 10-15 / now) | 0.10924 / 0.09617 / 0.11188 / 0.14173 / 0.09770 | 0.17471 / 0.13728 / 0.13716 / 0.18904 / 0.12302 | 0.17208 / 0.14877 / 0.15388 / 0.19035 / 0.12144 |
| **CoinGecko vs chain at the same hour (DEV-ONLY REFERENCE)** | −1.87% / −0.38% / −0.70% / −0.15% / +1.15%* | −0.41% / −0.59% / −0.25% / −0.11% / +0.46%* | −0.22% / +0.43% / −1.25% / +0.30% / +0.30%* |
| **CoinGecko over the 66-point series (DEV-ONLY)** | median 0.65%, p90 1.55%. **Two CoinGecko glitches**: ~2026-06-21 and ~06-24 CoinGecko showed $0.21 / $0.19 vs chain $0.087 / $0.080 (+144%) | median 0.46%, p90 0.96%, max 2.76%. Signed +0.15% | median 0.79%, p90 1.65%, max 3.45% |

\* For "now", the CoinGecko point is 41 min before the chain read.

On chain over the window (`price_oracle`):

| wrapper | in CRV, 2026-05-01 → now | in USD, range |
|---|---|---|
| cvxCRV | 0.400 → 0.414 | 0.072 to 0.169 |
| sdCRV | 0.615 → 0.521 | 0.106 to 0.207 |
| yCRV | 0.639 → 0.514 | 0.112 to 0.216 |

The USD ranges are the min and max over the 66 three-day samples (MEASURED).

Other CoinGecko comparisons over the series (DEV-ONLY):
- CoinGecko CRV vs Chainlink CRV: median 0.37%, max 2.73%.
- CoinGecko ratio vs pool ratio, which removes the CRV feed from the comparison: sdCRV median 0.21%, max 0.97%; yCRV median 0.65%, max 2.64%.
- **The sdCRV YAML claim that CoinGecko ran "+2 to +16% over the sdCRV/CRV pool in 2026-10" is CLAIMED** (sdcrv.yaml comment). It was **not reproduced** at hourly points: the 10 October samples ran −0.14% to +1.55%. It may come from CoinGecko's daily or `simple/price` value at ingest rather than the hourly series.
- The task brief says "+2..+6% over DefiLlama". That was not measured; DefiLlama is out of scope.

## 4. Cost

- One hourly point for all three wrappers is **one Multicall3 eth_call**. It carries 3 x `price_oracle` + 3 check reads (+ the CRV feed, if the CRV task bundles it).
- Rebuild of 183 days x 24 h = **4,392 eth_calls in total for the three wrappers** if bundled, or 4,392 per wrapper if each ref is fetched on its own.
- Live: 24 calls a day.
- Multicall3 `aggregate3` at archive blocks back to 2026-05-01 worked: 66 of 66 points (MEASURED).
- Probe volume this task: about 600 RPC calls.

## 5. Open questions

1. **sdCRV has no independent venue.** The only other sdCRV/CRV pool holds about $430 and reads 1.4% low on average (max −6%). Every other venue is < $2K. Options:
   - (a) Use `0xf7b5` with a wide tolerance (~7%) and a liveness guard, and label it weak.
   - (b) Record a documented exception, "no independent check", for Mike to approve.
   - (c) Add a bound check only: 0 < sdCRV/CRV ≤ 1. sdCRV is minted 1:1 from CRV, so its price can't sustain above 1. This is cheap, but it only catches gross breakage.

   The spec's "never computed from the same pool" rules out comparing the pool's own spot with its EMA.
2. **yCRV's check pools are thin** ($6K stableswap, $7K Uni v4 from 06-09). They track within 1.75% / 2.66% max. Should the check use the stableswap pool, which has full archive coverage, and keep v4 as a dev cross-read?
3. **Check tolerance and EMA lag.** During a real move (cvxCRV 2026-07-21, +4.9%), spot on both pools runs ahead of the EMA by ~5% for under an hour. Suggestion: flag a breach only when |gap| > tolerance on 2 consecutive hours. Suggested tolerances: cvxCRV 3%, yCRV 3%, sdCRV per option 1.
4. **Primary read choice.** I recommend `price_oracle()` (EMA). The other option is a TWAP built from hourly `get_dy` samples. Pool `price_oracle()` is already TWAP-like and costs one read.
5. **CRV/USD feed staleness** (lag up to 6.6 h seen) flows straight into all three wrappers' USD. The CRV scoping task should confirm the heartbeat and deviation threshold, and whether a stale CRV read voids the wrapper points.
6. The cvxCRV FraxBP USD route runs +0.9% high on average, because FRAXBP's virtual price is about 1.017 and FRAX/USDC is not exactly $1. It is only good as a secondary sanity read.

## 6. Recommendation

- **Primary, all three:** `price_oracle()` on the StableSwap2EMAOracle pool x Chainlink CRV/USD at each hour's block, all in one Multicall3 per hour. The archive is fine back to 2026-05-01.
- **cvxCRV check:** `get_dy` on the old pool `0x9D04…`, which is a real second venue at ~$0.27M. Tolerance 3%, two-hour persistence.
- **yCRV check:** `get_dy` on `0x453D…` (~$6K). Tolerance 3%, two-hour persistence. Mark it a thin check.
- **sdCRV:** needs Mike's decision (question 1). My lean is (a) plus (c): the tiny pool with a 7% tolerance, plus the ≤ 1 CRV bound, labelled a weak check.
- **`coingecko:yearn-crv`** becomes the yCRV chain price. **`coingecko:crvusd`** becomes Chainlink CRVUSD/USD, which belongs to the other task. The share prices are already on chain.
