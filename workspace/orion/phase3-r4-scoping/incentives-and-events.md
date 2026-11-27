# R4 scoping: Aero incentive programs on chain, the Foundation split, and imminent protocol events

Read-only. Measured 2026-11-27 18:35–18:55Z (10:35–10:55 PT), outside the forbidden windows. Heads: Base 63,071,332 ·
Ethereum 26,508,386 · OP 160,102,937 · Arbitrum 528,084,688 · Ink 62,306,246 · Robinhood 124,460,491 · Arc 33,459,375 ·
Elysium 11,744,912. RPC: `https://<chain>.g.alchemy.com/v2/***` (Orion's key; it also answers on `elysium-mainnet`).
Labels: **M** = MEASURED (call/block/tx cited, raw file in `incentives-data/`). **C** = CLAIMED (URL). **DEV-REF** =
DefiLlama/CoinGecko, used only as a dev-time reference, never as an input.

## 0. Answer table: average streamed USD/day, 2026-11-13..11-26 (14 UTC days) (M)

"Streamed" = allocated-streamed (see §3): Σ rate × (overlap with the UTC day − the VRM's zero-allocation seconds), priced at
the day-end (D+1 00:00Z) block. 100% of the streamed USD in this window is priced on chain: 48% via Chainlink, 52% via the
deepest Aero pool against USDC, WETH or AERO.

| chain | foundation_subsidy (creator 0x7269…9dDb) | foundation-signer Safe 0x80f7… | protocol-governance Safe 0x4225…4ce0 | third_party | total |
|---|---|---|---|---|---|
| Base | 0 | 1,379 | 0 | 2,187 | **3,566** |
| OP | 0 | 0 | 0 | 542 | **542** |
| Ethereum | 0 | 0 | 0 | 0 | 0 |
| Arbitrum | 0 | 0 | 0 | 0 | 0 |
| Ink | 0 | 0 | 0 | 0 | 0 (no program ever) |
| Robinhood | 0 | 0 | 0 | 0 | 0 |
| Arc | 0 | 0 | 0 | 0 | 0 |
| Elysium (8th chain, §5) | 0 | 0 | 0 | 0 | 0 (no program ever) |
| **all** | **0** | **1,379** | **0** | **2,729** | **4,108** |

- Over the whole window, 10-22..11-26 (36 days), the total is **$490.4k**: foundation_subsidy $219.8k (Base AERO, 10-22..10-29 only),
  the 0x4225… Safe $89.7k (WETH/USDT on ETH, Arbitrum, Robinhood, OP and Arc, 10-22..11-09 only), the 0x80f7… Safe $59.4k (RSGP, then INFI), and
  third parties $121.5k. Daily series: `incentives-data/daily.json`.
- Biggest lines in the 11-13..11-26 window ($/day): Base USDC third-party 1,735 (mostly creator 0xb398…9e23's weekly batches plus
  one 10k-USDC two-day program on 11-22..11-24) · INFI (0x80f7) 972 · RSGP (0x80f7) 407 · OP alETH 300 · Base AERO third-party 298 · OP USDC 241 · TLOS 129.
- Context: this is about **1.6% of DefiLlama's Base Aero holders revenue** (DEV-REF, ~$213–290k/day on 11-22..11-26).
- **0x4225… is not a Foundation-signer Safe.** It is a 3-of-7 Safe v1.5.0 with the same 7 owners on all 8 chains, and it shares **0 owners**
  with 0x7269 or 0x80f7 (M `getOwners`, `safe_owners.json`). On chain it is Aero's **protocol governance multisig**: it is Base
  CLFactory `owner()`, `swapFeeManager()` and `unstakedFeeManager()`, and VolatilePoolFactory `feeManager()` and `poolTapeManager()` (M, at
  Base block 52,962,127 and at head). It is the "Protocol governance multisig" in the docs' manager table (C, https://app.aero.xyz/docs/security).
  - Its programs are protocol-run launch subsidies on the non-Base chains, not third-party money.
  - Recommendation: book them as `foundation_subsidy`, or as a separate `protocol_subsidy`, not as `third_party`. All of them ended 2026-11-09 03:00Z.

## 1. Discovery by state only (no logs) (M; `discovery.json`, `elysium_discovery.json`)

Method per chain, all eth_calls through Multicall3 (`0xcA11…CA11`, which has code on all 8 chains):
1. `LeafVoter(0x3824…4078).FACTORY_REGISTRY()` → `FactoryRegistry.gaugeFactories()` and `targetFactories()`.
2. **Path A (pools):** for every target (pool) factory, `allPoolsLength()` and then `allPools(i)`. For every pool × every gauge factory,
   `computeGaugeAddress(pool)` and then `isGauge(gauge)`.
3. **Path B (registry):** `FactoryRegistry.factoryToGauges(gaugeFactory)`.
4. `gauge.votingRewardsManager()` and then `VRM.incentiveCount()`; also `LeafVoter.isActivated(gauge)`.

`VotingRewardsFactory` keeps **no registry**. Its only state is the immutables `voter`, `wrappedNative` and `FACTORY_REGISTRY` (source
`V3/src/rewards/VotingRewardsFactory.sol`). The registry is therefore `FactoryRegistry.factoryToGauges`. Paths A and B agree exactly on every chain:

| chain | pools (V/S/CL) | gauges A = B | VRMs | VRMs with programs | programs | gauge factories (VRF) |
|---|---|---|---|---|---|---|
| Base | 1,063 (325/28/710) | 321 = 321 | 321 | 121 | **259** | 3 (VRF 0x8fbA…7110) |
| Ethereum | 129 | 62 = 62 | 62 | 12 | **17** | 3 (0x6BFC…Ec2C) |
| OP | 117 (38/22/57) | 32 = 32 | 32 | 6 | **19** | 3 (0xa91C…1502) |
| Arbitrum | 83 | 56 = 56 | 56 | 10 | **17** | 3 (0x5614…f5Cd) |
| Ink | 40 | 28 = 28 | 28 | 0 | **0** | 3 (0xCCe2…98Cd) |
| Robinhood | 120 | 81 = 81 | 81 | 10 | **11** | 3 (0x7F83…9751) |
| Arc | 54 (incl. 35 Aero-Lite CL) | 8 = 8 (7 activated) | 8 | 4 | **4** | **6**: 3 standard (0x0c6b…ad1a), 3 Lite-upgrade (0x87e5…ea8c) |
| Elysium | 34 (3 V, 31 CL) | 8 = 8 | 8 | 0 | **0** | 3 |
| **total** | 1,640 | 596 | 596 | 163 | **327** | |

- Base went from 230 programs on 11-09 (earlier scoping) to 259 now. Ethereum is unchanged at 17. OP went from 13 to 19.
- Every `incentive(id)` decodes, and the identity `rate·(end−start)/1e18 = amount` holds for all 327 (M).
- 78 distinct creators. Decoded programs: `programs.json`.
- Blind spot of path B: a gauge factory removed from the registry would drop its gauges. None was added or removed between 10-23 and now on any chain (M, `factory_tape_snapshots.json`).
  Path A is independent of the registry and catches that case, so run A weekly and B daily.

## 2. Per-program state, daily series, pricing (M)

- Fields per program: `incentive(id)` → (token, amount, rate, start, end, creator), plus `remainingAmount(id)` and `sweptAmount(id)`.
  All are read at head, because programs are immutable once created.
- Zero-allocation seconds are read from VRM state:
  - Per (VRM, t): `getPriorSupplyIndex(t)`, then `globalRewardPointHistory(idx).zeroSupplySeconds`, plus `(t − pt.ts)` if `supplyAt(t−1) == 0`.
  - This mirrors `RewardsLogicLibrary._zeroSupplySecondsInRange`, the function `sweep()` uses.
  - It took 1,904 (VRM, t) points. Zero ambiguous cases, i.e. no zero-supply point whose last checkpoint still had supply.
  - Raw file: `zero_supply_cum.json`.
- Day-boundary blocks come from a timestamp secant search, then an exact bracket check (`ts(b) ≥ T > ts(b−1)`). That is 118 boundaries over 6 chains with 0 failures. No block-time arithmetic is used (`day_blocks.json`).
- **Prices (on chain only).** Each is read at the day-end block.
  - **Chainlink** (`description()` checked on chain; `feed_prices.json`):
    - Base: USDC/USD 0x7e86…bc6B (Orion's feed), ETH/USD 0xa425…36Ed, plus MORPHO, WELL, VIRTUAL and VVV.
    - Ethereum: ETH 0x5f4e…8419, USDT 0x3E7d…e32D, USDG 0x14f0…d311.
    - OP: ETH 0x13e3…08c5, USDC 0x16a9…E0f3.
    - Arbitrum: ETH 0x639F…a612, USDC 0x5083…4aD3.
    - Robinhood: ETH 0x78F3…D3A9, USDG 0x61B7…9aD2.
    - Arc: ETH 0x50FC…D364.
  - **AERO:** volatile AERO/USDC pool 0xf634…b18e reserves × Chainlink USDC. It was the deepest AERO pool every day ($10.9–12.1M USDC side).
    Cross-check: Chainlink "AERO / USD" 0x4EC5…cfF0 tracks it within 0.0–0.7% from 10-24 on. On day 1 the gap was 5.5%.
  - **Other tokens:** the deepest Aero pool by quote-side balance against USDC, WETH or AERO, chosen each day.
    - The read is slot0 for CL pools, reserves for volatile pools, and `getAmountOut` for the one stable pool (OP alETH/WETH).
    - Covered: RSGP, INFI, TLOS, VEIL, BRS, WOO, B3, fBOMB, CHIP, DRV, MAMO, cbMEGA, WHUF, BLUECHIP, tokenized stocks (PYPLc, SPCXc, TTWOc), FX stables (jEUR, tGBP, CADD, ZARP, IDRX) and alETH.
    - The FX stables match Chainlink EUR, GBP, CAD, ZAR and IDR within about 0.5%.
    - **Coverage: 41 of 41 program tokens priced on every streaming day. Unpriced streamed amount: 0.**
  - **Error check (DEV-REF, coins.llama.fi, 2026-11-21 00:00Z; `price_errorcheck_devref.json`):**
    - AERO +0.31%, INFI +1.04%, RSGP +1.17%, TLOS −1.81%, VEIL −1.04%, BRS +0.29%, IDRX +0.08%, CADD +0.07%, tGBP +0.07%, ZARP +0.03%, VVV +0.14%, alETH +1.23%.
    - All within ±2%. Spot at the boundary block is noisier for thin pools (VEIL had about $13k of quote depth). A pool TWAP, as Orion's `v2_pool_twap_price` does, would reduce that.
- Consistency with the 11-09 scoping on 11-07:
  - Ethereum $1,862 vs $1,863; Arbitrum $2,564 vs $2,572; OP $628 vs $629.
  - Base $4,088 vs $4,380. The gap is because that run used 11-09 spot prices.
- **Foundation TGE wallet (M):** `AERO.balanceOf(0x7269…)` = 28,941,560.34 at every sampled day block, 10-23 → head, so the subsidy has not restarted.
  Its 119 programs are the only ones it ever created (`incentive().creator` across all 327 programs).

## 3. Is the zero-allocation sweep material? What should "streamed" mean? (M)

- **`sweptAmount` = 0 on all 327 programs on all chains.** Nobody has ever swept.
- Zero-allocation streaming over 10-22..11-26 was **$5.84 in total** out of $490.4k (0.001%), across 5 programs:
  - 2 OP USDC programs from 0x5c1e…, $2.14. One of them ran with zero allocation for its entire 2 days.
  - 3 ETH/Arbitrum WETH programs from 0x4225…, a few minutes each at the start, $3.7.
  - On those OP programs `remainingAmount` equals exactly the zero-allocation amount. That cross-checks the state method: everything allocated was claimed, and only the sweepable part remains.
- **Definition to use:** allocated-streamed = `rate × (overlap seconds − zero-supply seconds of that VRM within the overlap)`.
  - It is the accrual that allocators can claim: the contract's claim math and `computeSweep` partition every program second into exactly these two parts.
  - It is accrual-timed, not claim-timed, so it does not depend on when people claim.
  - DefiLlama's adapter uses the same definition (`allocatedSeconds`, DEV-REF `dexs/aero-v2/utils.ts` L88–149).
  - Today raw rate × overlap gives the same number to within 0.001%. Keep the zero-supply term anyway: it costs one multicall per chain per day, and it matters for launch programs placed on unallocated pools.
- **Unclaimed (M, `remainingAmount`):**
  - 0x7269: 40,505 AERO is still unclaimed, 4 weeks after its programs ended. It is not sweepable, because zero-allocation seconds = 0.
  - Third parties: about 17.9k USDC and 18.6k AERO, mostly programs still running.
  - These are not "unearned": `remainingAmount` mixes future streams with allocator claims that are earned but not yet claimed.

## 4. Cost (M, counted during this run)

| step | HTTP requests (all chains) | sub-calls inside them | cadence |
|---|---|---|---|
| Registry path B + `votingRewardsManager` + `incentiveCount` | ~2–3 per chain → **~20** | ~1.2k | daily |
| Pool path A cross-check (allPools × gauge factories × 2) | 75 for 7 chains (+~15 for Elysium) | ~13k | weekly |
| Decode new programs (`incentive(id)`; append-only) | ≤1 per chain → **≤8** | a few to ~30 | daily |
| `remainingAmount`/`sweptAmount` on live programs (optional sweep monitor) | ~1 per chain | ~100 | daily |
| Zero-supply points for VRMs with a live program (2 rounds) | ~2 per chain with programs → **~6** | ~100–300 | daily |
| Day-end prices (feeds + pools, 1 multicall per chain) | **~8** | ~150 | daily |
| Day-boundary block search (secant + bracket check) | 3–6 per chain → **~35** | — | daily |
| **Daily total** | **≈ 80 HTTP requests/day** (≈ 2k CU) | ≈ 2k | |

- **Backfill is nearly free from state.** Programs are immutable and stay readable after they end, and zero-supply history is cumulative VRM state, so both are read once at head.
- Only prices and day-boundary blocks need historical (archive) reads.
- This run's full backfill for 10-22..11-26 used about **680 HTTP requests** in total. Of those, 362 were block search for 118 boundaries, 130 were feeds, 75 pool prices, 75 discovery, 19 programs and 18 zero-supply.
- There is no getLogs anywhere, so this is the top rung of Mike's ladder (contract state).
- One single-address first-party call was used for context only: `alchemy_getAssetTransfers` on 0x80f7.

## 5. Imminent / recent protocol events that change what R4 wires

| # | event | date | evidence | impact on R4 |
|---|---|---|---|---|
| 1 | **8th chain: Elysium** (Kinetiq L2 on HyperEVM, chain 99901) | registered in the root Voter **2026-11-09 20:10:48Z** (Base block 55,323,363) | **M:** Base Voter 0x49d7…31e6 `chains()` = [8453, 10, 1, 42161, 57073, 4663, 5042, **99901**], none suspended (binary search on `chains().length`). Elysium: `LeafVoter.chainStatus()` = 1, FactoryRegistry 0xdd17…2239, CLFactory 0xEfd7…2891 (31 pools), volatile 3 pools, same tapes 0x34bd…5992/0x27D5…35a4, 8 gauges/VRMs, 0 programs. **C:** "Aero has landed on @Enter_Elysium" https://x.com/aeroxyz/status/2119898132268114360 (11-09). Docs list the Elysium addresses (https://app.aero.xyz/docs/security). aero.xyz lists "Supported chains: … Elysium". **Not** in `metadex-public/deployment-addresses` (no commit since 11-04). DEV-REF: DefiLlama added Elysium on 11-09 (adapter commit 6006b527) and shows about $4.3k/day of fees there on 11-23. | **R4 must add an 8th chain row** (Alchemy subdomain `elysium-mainnet`, Multicall3 present) or it will under-count against DL. Watch the root `Voter.chains()` daily for chain 9. |
| 2 | **Arc Aero-Lite tapes differ** | Lite deployed 09-16. Lite-upgrade gauge factory present now. | **M:** the Arc FactoryRegistry targets include the Lite factories: CL 0xb89D…1d03 (35 pools) → `clPoolTape()` = **0x967f…5Ee9**; V2 0x9bc8…F9a5 / 0xaEd2…CC16 (0 pools) → `poolTape()` = **0x8Da0…6c25**. One Lite pool (0xd945…2782) already has a gauge (0x9fce…9012, factory 0xa02d…848C, VRF 0x87e5…ea8c), **not yet activated**. **C:** `cllitelaunch-arc.json`, `clliteupgrade-arc.json`. | R4 must read `factory.poolTape()`/`clPoolTape()` per factory, not assume 0x34bd/0x27D5. If that gauge activates, Lite revenue starts going to allocators. |
| 3 | Tapes / factories unchanged since launch | 10-23 → 11-27 | **M:** `targetFactories`, `gaugeFactories`, every `poolTape()`/`clPoolTape()` and every `gaugeTape()` are identical at the 10-23 boundary block and at head on all 7 launch chains (11-14 → head on Elysium) (`factory_tape_snapshots.json`). | None, but alert on change. |
| 4 | MEV tax roll-out | OP pilot 10-30; "rolling out" 11-02 | **C:** https://x.com/aeroxyz/status/2116217979616756219 and https://x.com/aeroxyz/status/2117380101738525029. Docs: "The tax works the same as other swap fees" (https://app.aero.xyz/docs/products/trading). **M:** a MEV tax module is configured per factory (`pools-*.json`; 0 on Ethereum and Robinhood). | Already inside the tape fee (`cumulativeMevFee*`). No wiring change. |
| 5 | Legacy-gauge reactivation to "reclaim locked fees" | **no date**; not happened | **C:** "plans to reactivate the gauges at a later date" (https://aero.xyz/aero-upgrade). **M:** legacy Base Voter 0x1661…80A5: **0 of 2,013** gauges `isAlive` at 10-22 00:00Z, 11-19 and head (949 were alive about 5 days before launch). OP Voter 0x41C9…bf3C: 0 of 846. | Foundation recoup on legacy contracts, not sAERO revenue. Watch `isAlive` counts weekly (about 3k sub-calls). DL already books these locked fees as ProtocolRevenue. |
| 6 | Fee switch / protocol share | no announcement | **C:** "Token Operators also keep a portion of the fees generated by fee-earning deposits … set by protocol governance" (https://app.aero.xyz/docs/faq/token-operators). **M:** Base CLFactory `defaultUnstakedFee()` = 50,000 (5%), unchanged 10-23 → head. No treasury/protocol fee getter in the pool factories. | Unstaked-fee changes move revenue between LPs and allocators. The tape is gross either way. |
| 7 | REV engine: Metaswaps fee, MEV auctions, sAERO marketplace | "near-term", undated | **C:** "Fees net of fixed costs will be used to support the Aero token" (https://aero.xyz/articles/aero-economic-case/); "Aero can add a fee to Metaswaps beyond what covers fixed costs … buybacks and burns" (https://aero.xyz/articles/the-aero-economy). The Metaswaps docs say fees flow as pool trade fees (https://app.aero.xyz/docs/features/metaswaps). | Any Metaswap fee would be a new contract, outside the tapes and outside the VRMs. Watch `MODULE_ADMIN_ROLE` module registrations and the Metarouter. |
| 8 | **0x80f7 Safe received 4.2M GEN** | **2026-11-27 01:24Z** | **M:** tx 0x6d4eef70…8bf (from 0xc258…8d1a). Same pattern as RSGP (funded 10-27 → program 10-29) and INFI (funded 11-14 → programs 11-17, 2 × 150k). No GEN program exists yet. | A GEN launch program is likely within days (inference). The 0x80f7 class keeps going. |
| 9 | Foundation Momentum Fund buyback | 11-11 | **C:** "The Momentum Fund has acquired and staked 294K $AERO" https://x.com/aeroxyz/status/2120573719806644691 | A buyback line, not revenue. Relevant if Orion tracks buybacks. |
| 10 | Integrations (no contract change) | 11-10 Arcadia ALM "coming weeks"; 11-20 Revert Lend; 11-24 1inch "across 8 chains"; 11-24 Velora | **C:** https://x.com/aeroxyz/status/2120233799921623192, …/2123579327547912592, …/2125227965281870311, …/2125250599512105347 | Volume only. |
| 11 | GitHub `dromos-labs` | — | **M:** the org has 2 public repos. `metadex-public`'s last commits are 2026-11-04 2ce1816 ("chore: update versions", v1.2.0 = relay leaf modules) and 10-30 957b256 (relay public release). `metadex-slipstream-public`'s last commit is 2026-10-21. **No commit since 11-01 touches tapes, factories or rewards.** | None. Their deployment JSONs lag the chain: no Elysium, no Arc Lite-upgrade VRF. |
| 12 | Docs changelog / forum | — | None found. Governance runs through X (@aerogovernance), e.g. the "AERO Rewards Date/Allocation Proposal". Phishing clones exist (proposals-aero.fun, distribution-aero.icu). | None. |

## 6. Does DefiLlama's "holders revenue" include incentives? (DEV-REF)

- **Yes, by source.** `dexs/aero-v2/utils.ts` `addBribes` reads `incentiveCount`/`incentive(id)` and the VRM global points
  (`allocatedSeconds`), then adds the allocated-streamed amount to both `dailyFees` (label "External Bribes Rewards") and
  `dailyRevenue` (= HoldersRevenue, "External Bribes Revenue"). Both `aero-lite` (Slipstream) and `aero-v2` (Basic) call it.
  That is the same definition as §3.
- **The numeric check is inconclusive at this size.** I computed Base gross tape fees over all 1,063 pools from `accumulators()` state
  (fees valued through each pool's own price against USDC, WETH or AERO; 926 pools valued, 1–2 unpriced pools with fees)
  (`base_tape_gross_1123_1125.json`):
  - 11-23: DL Base Aero fees $333,180 − tape $323,230 = **+$9,950**; our incentives were $7,626.
  - 11-25: $274,936 − $277,810 = **−$2,874**; our incentives were $2,722.
  - The fee-pricing difference (±1–3% of $250–330k ≈ ±$3–9k/day) swamps a $3–8k incentive line. One day's residual therefore cannot isolate incentives.
  - The earlier 11-07 check (aero-scoping/a) matched DL fees = tape + incentives within 0.2–0.6%.
  - The tape-based allocator share (gauge accrual) was not computed. It needs `FeesCollected`/`Claim` logs or `pendingFees` deltas, so it is not cheap.
- **Practical consequence:** an owned series must add the incentives line, which is about $3.6k/day on Base now, to the tape/gauge fee line to match DL's holders revenue.
  Following Orion's existing rule, it should sit below the line as `vote_incentives`, split by class.

## Open questions

1. How to book 0x4225… (protocol governance multisig: $89.7k of WETH/USDT launch subsidy on 5 non-Base chains, 10-22..11-09)? I recommend `foundation_subsidy`/`protocol_subsidy`, not `third_party`.
2. 0x80f7 (Foundation signers, issuer tokens: RSGP, INFI, next GEN): count it as third-party money or foundation-administered? It is now 34% of 11-13..11-26 incentives.
3. Price basis: day-end spot (used here) or a TWAP? Spot is within ±2% of DEV-REF on 11-21 but noisy on thin pools.
4. Elysium: add it to R4 now (8 gauges, a small but nonzero fee base that DL counts) or label it "not covered"?
5. Arc Lite: does R4 cover the 35 Lite pools (separate tape 0x967f…) now that one has a gauge, or only once it activates?

## Files (all in `incentives-data/`)

- Discovery: `discovery.json`, `elysium_discovery.json`
- Program data: `programs.json` (327 decoded programs), `program_days.json` (per program-day tokens, price and source), `daily.json` (per chain per day, USD by class, streamed and allocated)
- Supply and blocks: `zero_supply_cum.json`, `day_blocks.json`
- Prices: `feed_prices.json`, `pool_prices.json` (with the chosen pool per token-day), `price_errorcheck_devref.json`
- Safes and events: `safe_owners.json`, `rsgp_safe_transfers_since_1107.json`, `factory_tape_snapshots.json`, `legacy_gauges_alive.json`
- DL comparison: `base_tape_gross_1123_1125.json`, `defillama_devref_breakdown_1118plus.json`
- Scripts: `scripts/aero_rpc.py` (multicall, keccak, no key output), `scripts/aero_blocks.py` (timestamp search)

## Addresses (chain, role, address, how verified)

| chain | role | address | verified |
|---|---|---|---|
| all 8 | LeafVoter | 0x382409fad8503FbCdbB27A4211551fa03e884078 | docs + code on every chain; `FACTORY_REGISTRY()` answers |
| Base | root Voter | 0x49d7d4f17Ec56Ef8fA04E464AF5D1A4942CC31e6 | docs; `chains()` read |
| all 8 | VolatilePoolFactory / StablePoolFactory | 0x8E6a9FCd1d638CC760Ffba397605Fe3355dE76D2 / 0x78589E876edcEbdce72ee3436ab3c9AD3a7cEF2D | in each chain's `FactoryRegistry.targetFactories()` |
| all 8 | PoolTape / CLPoolTape | 0x34bdD64B19D8631F936c2D07F19AAa6B83515992 / 0x27D5EB73e7406675F6B0CbD037490ec3dba935a4 | `factory.poolTape()`/`clPoolTape()` at 10-23 and head |
| all 8 | CLGaugeFactory | 0xf437f62053ACB121665b8fDBfeA8F214FB8E589d | `gaugeFactories()` on every chain |
| Base | FactoryRegistry · CLFactory · VRF | 0x7b2A2c12dC5Ea2a31455952a05031C3E4BB28F3E · 0x9CB220581b91b0C83223012FE69688b92aD07a76 · 0x8fbAaC4dbF170687ce6c3078f29556d97d197110 | LeafVoter → registry; gauge factory `VOTING_REWARDS_FACTORY()` |
| Base | gauge factories V/S | 0x9FBCf2Df0DC553ce40Ef63963Bff465b76792B7E / 0x1e0f776E88649285f99e65Fa599aD6e0f9D97800 | registry |
| Ethereum | FactoryRegistry · CLFactory · VRF | 0xdd1705e23762F4D6e44D8C31BD8Ea80c54612239 · 0xF4Fd2E6c5B60c5b365cd1B96DD6245E6D60414c2 · 0x6BFC9D4C3A1CfD937dE04a5b817eAe424E85Ec2C | as above |
| OP | FactoryRegistry · CLFactory · VRF | 0xb6F9705A631CC1C0E8570FFde48882C95E2Df408 · 0xfeaB42D90055db3a0616249f76B6002D72266778 · 0xa91Cded49F48b7b26F8464339D6E7b39d20a1502 | as above |
| Arbitrum | FactoryRegistry · CLFactory · VRF | 0x9E635b2c689fC52201DF7eF1C9FA607c2F58f666 · 0x88a60ee77392577c355C0acb2A8d476D5a4EC03a · 0x5614AA98a8DAF9Ec71c3829ccbE8A365A742f5Cd | as above |
| Ink | FactoryRegistry · CLFactory · VRF | 0xdd1705e23762F4D6e44D8C31BD8Ea80c54612239 · 0x7660BF2aDefC687C22906112ca323d60A00358cF · 0xCCe24256a8a6070A9E308f23E044C87C343F98Cd | as above |
| Robinhood | FactoryRegistry · CLFactory · VRF | 0xdd1705e23762F4D6e44D8C31BD8Ea80c54612239 · 0xc63d7338c178e805c544B8f897066bD3BBcBE136 · 0x7F83235643181E440433400a027618Cd50879751 | as above |
| Arc | FactoryRegistry · CLFactory · VRF | 0xCe44907DC45D3BFa3f5f6035B0e6E8B22D780A42 · 0x7F83235643181E440433400a027618Cd50879751 · 0x0c6bad5CaACD26aF5B6E2013D9F8bF9589d5ad1a | as above |
| Arc | Lite CL factory → Lite CL tape | 0xb89Df768aF2CFE637ceB352c587Fe8edAf491d03 → 0x967f5352A6448e22D7361E149103350c49345Ee9 | registry target; `clPoolTape()` |
| Arc | Lite V2 factories → Lite pool tape | 0x9bc8b3F60D349d687Fb44A018967025E3741F9a5, 0xaEd253F1aD84d99f2165256D701b2b481DD4CC16 → 0x8Da07EfaBCF124B61671Df449BC73292D4B56c25 | registry targets; `poolTape()` |
| Arc | Lite-upgrade gauge factories → VRF | 0x70b8ea088922b0dce67d04a74c3d6c906831854d, 0x1c7e01c4184966609362f9af338c6b711511623b, 0xa02d1F4E4243ff0d350F478c44B0Fd37c7bF848C → 0x87e57c6c26e769a77ea8f8a32a3542e0b36aea8c | `gaugeFactories()`; `VOTING_REWARDS_FACTORY()` (not in the docs; the last is in `clliteupgrade-arc.json`) |
| Elysium | FactoryRegistry · CLFactory · gauge factories | 0xdd1705e23762F4D6e44D8C31BD8Ea80c54612239 · 0xEfd7A089D3057F05189B05f74Ffcf30610c42891 · 0xf2e6db898840e0ae91c44e1bddea16b50a369862, 0xb89df768af2cfe637ceb352c587fe8edaf491d03, 0xf437…589d | LeafVoter → registry (docs list the same) |
| Base | AERO token | 0x3f5bF3EdAc59d650D8fDf9657a71F2f904A3a4Ee | docs; incentive token |
| Base | AERO/USDC price pool (volatile) | 0xf634058dc94e6bf8e828e27621320c423bc8b18e | Orion `aero.yaml`; deepest AERO pool by USDC side every day |
| Base | Foundation TGE wallet (2-of-5 Safe 1.3.0) | 0x7269de76188E6597444D0859C4e5c336D3c39dDb | `getOwners`; creator of 119 programs; no code on the other chains |
| Base (+OP same owners) | Foundation-signer Safe (2-of-5, 1.4.1) | 0x80f7153d9bc853a9bf8bc21f2517c0acee2fdf75 | `getOwners` = the same 5 as 0x7269 on Base and OP. On ETH, Arbitrum, Ink, Robinhood and Arc it is a different 2-of-4 (2 shared owners, nonce 0) |
| all 8 (code on 7; none on Elysium) | Protocol governance multisig (3-of-7, Safe 1.5.0) | 0x42255e3c2d0b71a0b006243148fdf1a71d054ce0 | `getOwners` identical on all 7 chains with code; 0 shared with 0x7269/0x80f7; CLFactory `owner()`/fee managers on Base |
| Base / OP | legacy Aerodrome / Velodrome Voter | 0x16613524e02ad97eDfeF371bC883F2F5d6C480A5 / 0x41C914ee0c7E1A5edCD0295623e6dC557B5aBf3C | DEV-REF adapter source; `length()`/`isAlive()` answer |
| each | Chainlink feeds used | see §2 | `description()` + `decimals()` on chain; directory https://reference-data-directory.vercel.app/feeds-*.json |
| all 8 | Multicall3 | 0xcA11bde05977b3631167028862bE2a173976CA11 | `eth_getCode` non-empty |
