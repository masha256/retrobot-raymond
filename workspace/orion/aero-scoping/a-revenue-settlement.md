# Aero exchange revenue: where it settles (scoping A)

Read-only scoping, 2026-11-09. Sources: Aero docs, the `dromos-labs/metadex-public` and `metadex-slipstream-public` source plus their `deployment-addresses/*.json`, and archive reads on all 7 chains through the Alchemy key. DefiLlama appears only as a reference figure.

## Answer in one line
Revenue does **not** settle in one Base contract. It accrues **per pool, per chain** and is paid **on the chain where it was earned**, in the **pool's own tokens**. Each gauged pool has its own `VotingRewardsManager` (VRM). Nothing is bridged to Base. Base only sends the allocation and claim *messages* (Hyperlane).

## 1. Contract graph (MEASURED by eth_call on Base at head ~55.33M unless noted)
- `VotingEscrow` 0xBF79…3915 (sAERO, 23,768 NFTs): `VOTER()` = Voter 0x49d7…31e6 and `TOKEN()` = AERO 0x3f5b…a4Ee. There is no `voter()` getter. The new contracts use UPPERCASE immutables.
- `Voter` (root, Base): `VOTING_ESCROW()`, `MINTER()` = 0x5926…9C97 and `ORCHESTRATOR()` = RootMessageOrchestrator 0x4F34…6194. `Voter.claimRewards(tokenId, params[])` does not pay anything. It dispatches a `ClaimRewards` message per chain (source `V3/src/voter/Voter.sol` L297).
- `LeafVoter` 0x3824…4078 is at the **same address on every chain, Base included**. Base is a leaf of itself through `RootLocalAdapter`. Its getters: `FACTORY_REGISTRY()` = 0x7b2A…8F3E, `GAUGE_MANAGER()` = 0xbF23…b183 and `EMISSIONS_HANDLER()` = 0x8C37…22C3. `claimRewards()` is callable only by the orchestrator or the tokenId's operator.
- Pool → gauge → VRM (source `VotingRewardsManager.sol`, `V2Gauge.sol`, `Pool.sol`, `CLPool.sol`):
  - **V2 pools** move each swap fee into a per-pool `PoolFees` contract. The gauge's LP share is credited through `Pool.claimable[gauge]`.
  - **CL pools** keep the staked share plus the unstaked-fee cut in `gaugeFees` inside the pool.
  - A claim calls `gauge.collectFees()`, which transfers the fees pool/PoolFees → VRM and emits `FeesCollected`. The VRM then pays `ClaimFees(tokenId, recipient, token, amt)`.
- **Incentives** ("Liquidity/Launch Payments", bribes) are streamed programs inside the same VRM: `createIncentiveProgram(token, amount, start, duration)` stores `incentive(id)` = {token, amount, rate (×1e18), start, end, creator} and pays out through `ClaimIncentives`.
- **MEV capture** is not a separate stream. `PoolFactory.getFee` adds `_mevFee` to the swap fee (`_fee += _mevFee`, `PoolFactory.sol` L303), so it lands in the same pool fees. MEASURED 2026-11-07: about $4 of MEV fee across all chains (PoolTape `cumulativeMevFee*`), so it is negligible today.
- **`VoterPaymentsModule` 0xBe8e…AA79 is NOT a revenue contract.** It charges a fee in *sAERO stake* on `depositIntoNFT`/`withdrawToNFT` (merging or splitting stakes) into the tokenId-0 accumulator (`VoterPaymentsModule.sol` L146-167). Its `getFee` reverted for the default caller (NotRegistered: restricted mode).
- Other flows that are not allocator revenue: the Relay/Autopilot rake goes to `RelayFactory.rakeTreasury()` = 0x4225…4ce0 (MEASURED; the same address as the governance/admin constructor arg). Metarouter has no fee code. The Splitter only handles team emissions.
- **Per-chain stat tapes (the useful find):** `PoolTape` 0x34bd…5992 and `CLPoolTape` 0x27D5…35a4 are at the same address on all 7 chains (deployment JSON, CLAIMED: https://app.aero.xyz/docs/security). They expose `accumulators(pool)` with cumulative fee0/fee1, volume and MEV fee for every pool, updated on every swap.

## 2. Per chain or bridged?
Per chain, paid locally. CLAIMED: "runs continuously on every network Aero supports" (https://app.aero.xyz/docs/guides/understanding-predictive-allocation/). MEASURED on Ethereum: VRM 0x067a…f65d emitted `ClaimFees` in tx 0x61aa5c9c…02de (block 26,359,277), whose `to` is the Hyperlane Mailbox 0xc005dc82…d239. So the claim is triggered from Base and paid on Ethereum. On 2026-11-07 Ethereum had 195 `ClaimFees` and 111 `FeesCollected` logs. No bridge leg is involved.

| chain | Aero pools | gauged pools / VRMs | log calls/day (2000-block range) |
|---|---|---|---|
| Base | 934 (23 stable, 309 volatile, 602 CL) | 310 | 216 |
| Ethereum | 109 | 59 | 4 |
| OP | 108 | 32 | 22 |
| Arbitrum | 67 | 36 | 145 |
| Ink | 21 | 13 | 44 |
| Robinhood | 95 | 70 | 410 (~819k blocks/day) |
| Arc | 15 | 6 | 86 |

All counts MEASURED with `allPools()`, then `GaugeFactory.computeGaugeAddress` + `isGauge`, then `gauge.votingRewardsManager()`. The per-chain factory addresses come from the deployment JSONs. The Alchemy key answers on `eth-`, `opt-`, `arb-`, `ink-`, `robinhood-` and `arc-mainnet` (eth_chainId MEASURED).

## 3. Tokens and the single-address question
- Revenue is paid in **pool tokens**: whatever the pair holds. It is not USDC or AERO by default.
  - Base top tokens on 2026-11-07: USDC $29.6K, WETH $24.6K, AERO $19.3K, cbBTC $12.0K, then a long tail including tokenized stocks (SNDKc, MSTRc…).
  - Robinhood: USDG/WETH plus memecoins. Ethereum: WETH/USDT/USDC.
  - Incentives are paid in whatever token the payer streams (USDC, USDT, WETH, RSGP…).
  - The Autopilot "USDC Maxi" only converts after the claim (CLAIMED, same guide).
- **No single address carries the inbound total.** On Base, fees flow into 310 VRMs, from 934 pools or their PoolFees contracts.
- Even per VRM, inbound transfers are **lazy**: fees only move when someone claims. MEASURED on Base, 2026-11-07: $54.9K of `ClaimFees` was paid out, against $116.8K of fees accrued to gauges. So daily transfer logs ≠ daily revenue.
- The closest thing to a single address is the **two tape contracts per chain**. One contract holds the cumulative fees for every pool, read by state, not logs.

## 4. 2026-11-07 UTC measured (MEASURED; token amounts on chain, USD via DefiLlama coins historical at 12:00Z as reference pricing)
Window: Base blocks 54,096,122-54,528,121 (432,000 blocks; ts 1794009600 → 1794096000). The other chains used the same UTC window via block search.

Columns:
- **Tape gross fees**: state delta of `accumulators(pool)` between the two blocks (all LPs, MEV included).
- **Gauge fee accrual** (allocators' fee share): Δ`gauge.pendingFees()` plus Σ`FeesCollected` logs, filtered to that chain's VRM address list.
- **Incentives streamed**: Σ over `incentive(id)` of rate × overlap with the day.

| chain | tape gross fees $ | gauge fee accrual $ | incentives streamed $ | DL fees (ref) | DL revenue (ref) |
|---|---|---|---|---|---|
| Base | 128,242 | 116,793 | 4,380 | 132,842 | 121,399 |
| Ethereum | 8,406 | 8,204 | 1,863 | 10,256 | 10,055 |
| Robinhood | 10,603 | 10,203 | 0 | 10,427 | 10,033 |
| Arbitrum | 1,422 | 1,409 | 2,572 | 3,984 | 3,968 |
| OP | 750 | 732 | 629 | 1,373 | 1,355 |
| Ink | 277 | 240 | 0 | 275 | 241 |
| Arc | 171 | 139 | 0 | 175 | 139 |
| **Total** | **149,871** | **137,720** | **9,444** | ~159K (Aero only) | ~147K |

- **Allocator exchange revenue on 11-07 ≈ $147.2K** (fees $137.7K + incentives $9.4K), and 79% of it is on Base. Gross pool fees plus incentives come to ≈ $159.3K.
- DefiLlama's "fees" for these chains equals tape fees + incentives within 0.2-0.6%: Base 132,622 vs 132,842; ETH 10,269 vs 10,256; Arbitrum 3,994 vs 3,984. Its "revenue" equals gauge accrual + incentives (Base 121,173 vs 121,399). So DL counts incentives inside fees.
- The **~$250-300K/day figure doesn't hold for 11-07.** DL's all-entity total that day is ~$185K, and ~$26K of it is the **legacy** contracts: Aerodrome V1 $7.5K + Aerodrome Slipstream $17.9K on Base, and Velodrome V2/V3 ~$0.2K. Those pools still trade, but only ~$4K of that goes to old voters (DL revenue), not to sAERO.
- Pricing coverage: 181 of 224 Base gauge tokens were priced. The unpriced ones are ~81 alUSDb plus dust (<$100). No symbol fallback was needed off Base.
- Saved data:
  - `$TMPDIR/aero_allchain_20261107.json` (per-chain summary)
  - `$TMPDIR/aero_base_vrm_logs_20261107.json` (18,007 Base VRM logs)
  - `$TMPDIR/aero_base_gauges.json` (pool→gauge→VRM)
  - Scratch is pruned after 24 h.

## Options (Mike's ladder)
1. **Contract state: tape accumulators + VRM incentive programs.** Top rung; possible on all 7 chains.
   - Gross fees: `PoolTape`/`CLPoolTape.accumulators(pool)` at the two day-boundary blocks, for every pool from `factory.allPools()`.
   - Incentives: `VRM.incentiveCount()` + `incentive(id)`, rate × overlap.
   - Cost per day, as batched eth_calls: Base ≈ 2×934 tape + ~310 + programs ≈ 2.5K calls (~25 HTTP batches). The other six chains ≈ 1.2K calls combined. No getLogs.
   - Coverage: 100% of Aero (MetaDEX03) pools.
   - It measures **gross** fees, which is the coinrevs "gross user-paid fees" basis. The allocator share was 91-99% of it per chain on 11-07. The gap is fees kept by unstaked LPs (V2) or ungauged pools, which is a cost-of-revenue line.
   - Risks:
     - The tape write is a fail-open, gas-capped `excessivelySafeCall` (`PoolFactory.recordPoolTape`), so a reverting tape silently drops fees. Read `factory.poolTape()`/`clPoolTape()` daily and alert on change.
     - The CL tape fee field is assumed to be the total fee, which the DL match supports. I didn't trace the CL record call site.
     - Programs whose creator swept the zero-supply intervals overstate incentives slightly.
2. **Allocator fee share exactly: state delta + multi-address log scan.**
   - Δ`gauge.pendingFees()` (state) + `FeesCollected` getLogs filtered to the chain's VRM address list (one topic, address array).
   - Cost per day: Base 216, Robinhood 410, Arbitrum 145, Arc 86, Ink 44, OP 22, ETH 4 getLogs, plus 2×G eth_calls.
   - Coverage: 100% of gauged pools.
   - It is not single-address, because the address list has 310 entries on Base. The VRM list has to be refreshed from the factories as gauges are added.
   - Risk: `flushFees` on gauge suspension and buffered remainders are second-order.
3. **Fixed pool list scan.** Not needed: options 1 and 2 already cover every pool from factory state.
4. **Single-address inbound Transfer scan.** **Not possible.** No such address exists, and VRM inflows are claim-timed rather than accrual-timed.

Per chain: options 1 and 2 are possible on Base, Ethereum, OP, Arbitrum, Ink, Robinhood and Arc, all with the same contract set. Every chain needs archive eth_call. Robinhood and Arc RPC are on the Alchemy key; Orion's `chains.ts` has no rows for OP, Arbitrum, Ink, Robinhood or Arc yet. Legacy Aerodrome/Velodrome pools would be a separate, shrinking stream that doesn't pay sAERO.

## Open questions
- **USD pricing without DefiLlama.** The revenue is a long tail of pool tokens: 224 tokens on Base alone, including tokenized stocks. Options: price via the tape itself (volume ratios against stable pairs), or value just the top-N tokens and state the coverage (USDC, WETH, AERO and cbBTC made up 73% of Base gauge fees).
- Is the coinrevs "revenue" for AERO the gross tape fees + incentives (gross user-paid), or the allocator share (gauge accrual + incentives)? The two differ by ~8%.
- Should incentives (third-party payments to allocators) count as revenue or sit below the line? Orion's CRV/yCRV precedent treats vote incentives as not holder revenue / below the line, and DL counts them inside fees.
- The CL tape fee semantics need confirming: trace `CLPoolTapeData.fee0` in `CLPool.sol`/libraries, and spot-check one pool against `Swap` logs.
- The "REV Engine" streams (internal MEV auctions, Metaswaps bridge/aggregator fees, veNFT marketplace) were CLAIMED in the FAQ (https://aero.xyz/articles/aero-predictive-allocation-faq). On chain today the MEV fee is ≈ $0 and the Metarouter has no fee. Watch for new modules: `MODULE_ADMIN_ROLE` "payments" registration.
- The 11-07 measurement is one day. Re-run 2-3 more days, and one pre-11-05 day (2 s Base blocks), before quoting a run rate.
