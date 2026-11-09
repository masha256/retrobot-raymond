# AERO scoping (b): the incentive market under Predictive Allocation, Foundation vs third-party

Read-only scoping, 2026-11-09 (Base head 55,335,579 at 2026-11-09 20:51 UTC). No Orion code or DB was touched.
Labels: **MEASURED** means a block, tx or call on Base, read via the Alchemy Base RPC (`ORION_BASE_RPC_URL`). **CLAIMED** means a quote with its URL.
USD values use DefiLlama `coins.llama.fi` spot prices from 2026-11-09 as a **reference only** (AERO $0.5703, RSGP $0.001144, USDC $1.00, VVV $21.61, TLOS $0.01419). That price basis is a scoping shortcut, not a proposal.
Raw data in scratch, which is pruned after 24 h: `cache/scratch/aero_programs.json` holds all 231 decoded Base programs, and `aero_incentive_logs*.jsonl` holds the raw logs.

## 1. How incentives are deposited now

- **Contract.** Each gauge has one `VotingRewardsManager` (VRM), created by `VotingRewardsFactory.createRewards`. The VRM inherits `FeeDistribution` (Exchange Revenue to allocators) and `IncentiveStreaming` (incentives).
  - Source: Dromos-Labs/metadex-public, `V3/src/rewards/{VotingRewardsManager,IncentiveStreaming}.sol`.
  - Base factory `0x8fbAaC4dbF170687ce6c3078f29556d97d197110` (`deployment-addresses/gaugestack-base.json`). LeafVoter `0x382409fad8503FbCdbB27A4211551fa03e884078`. Root Voter `0x49d7d4f17Ec56Ef8fA04E464AF5D1A4942CC31e6` (from `VotingEscrow.VOTER()`). TokenRegistry `0x5646…A7E1`.
  - **MEASURED:** 313 VRMs were created on Base between 2026-10-20 and 11-09, mostly through `0x8fbaac…`.
- **Function.** `createIncentiveProgram(token, amount, start, duration)`.
  - Anyone can call it (permissionless). The token must be listed on the TokenRegistry; `start >= block.timestamp`; `duration >= LeafVoter.minIncentiveDuration()`; `amount >= duration` (in wei).
  - The full amount is pulled from `msg.sender` at creation. A program is immutable: no top-up, edit or cancel.
  - The creator can call `sweep(programId)` after the program ends, which recovers only the tokens that streamed while nobody was allocating to the pool.
  - **MEASURED:** `minIncentiveDuration()` = 172,800 s, i.e. **2 days on chain**. The docs UI says 7 days.
- **Event.** `IncentiveCreated(uint256 indexed programId, address indexed token, address indexed creator, uint256 amount, uint48 start, uint48 duration)`, topic0 `0x71ea36ae…f9c6`. `IncentiveSwept(uint256 indexed, address indexed creator, uint256)` has topic0 `0xbd15095a…1d1e`.
- **State reads.** Per VRM: `incentiveCount()`, `incentive(id)` (which returns token, amount, rate, start, end, creator), `incentivesByCreator(creator, i, j)`, `remainingAmount(id)` and `sweptAmount(id)`.
  - **MEASURED:** the sum of `incentiveCount()` over all factory VRMs is 230. My log scan found 231 events; the extra one is a VRM that predates the scan window. Log scan and state therefore agree exactly.
- **Streaming.** The rate is amount / duration per second. It accrues continuously to the sAERO "Token Operators" allocated to that pool, pro rata to Allocation Power × time. LPs are not paid.
  - CLAIMED, https://app.aero.xyz/docs/guides/creating-incentive-program: "Incentives pay Token Operators, not liquidity providers."
  - CLAIMED, https://app.aero.xyz/docs/features/incentive-programs: "Creation is permissionless: any address can fund a program."
  - I found no LP-direct incentive function in the gauge contracts. The Voter's `donate()` buffer, which backs emissions, has 0 on every chain (**MEASURED** `donatedBuffer(8453/10/1/42161/57073)` = 0).
- **Tokens.** Any TokenRegistry-listed token can be used.
  - **MEASURED** on Base since launch: 26 distinct tokens. AERO is used by the Foundation and a few projects; the rest are USDC, WETH, RSGP, VEIL, TLOS, IDRX, VVV and others.
  - CLAIMED policy (https://app.aero.xyz/docs/guides/incentive-guidelines): only Connector-paired pools qualify, and each pool is capped at the lower of 15× the previous 48 h fees and 5% of Connector TVL.
- **Orion relevance.** These are still third-party payments to stakers (the old "bribes"). They do not change the existing Orion rule: book them below the line as `vote_incentives`, not as holder flow.

## 2. The Foundation's migration incentives: how to identify them

- **Depositor (MEASURED).** All Foundation-subsidy programs on Base have creator **`0x7269de76188E6597444D0859C4e5c336D3c39dDb`**.
  - It is a Gnosis Safe, 2-of-5.
  - CLAIMED, Blockworks transparency filing (https://blockworks.com/api/transparency-report/aerodrome-2026-h1-b2-initial): "Liquid AERO at TGE (Incentives) — Liquid AERO minted at TGE for voter and genesis liquidity incentives only — Base 0x7269de76188E6597444D0859C4e5c336D3c39dDb".
  - This matches the hub's "liquid incentive budget it received at Aerodrome's launch".
- **Distinguishing feature.** An `IncentiveCreated` event with topic3 (creator) = `0x7269…9dDb` and topic2 (token) = new AERO `0x3f5b…a4Ee`. You can filter on the creator topic alone; the token check is a guard.
- **What it did (MEASURED).**
  - 119 programs, 304,752.66 AERO, across 97 pools. All were created on 2026-10-22, between blocks 52,919,989 and 52,956,614 (first tx `0x6f9ade10…71a3`).
  - 50 programs (149,208 AERO) run 2 days from 10-22 01:00 UTC.
  - 69 programs (155,545 AERO) run 7 days from 10-22 21:00 UTC.
  - **The last program ended 2026-10-29 21:00 UTC.**
  - The wallet had no other AERO outflows. It upgraded 29,246,313 old AERO to new on 10-22.
- **Value.** About $174k at today's spot, or about $207k at the 10-29 price of $0.679 (DefiLlama reference). That is roughly 10% of one old-Aerodrome epoch of voter fees: the last two Q3 epochs paid $1.59M and $1.79M (CLAIMED, Blockworks Q3 report, below).
- **Daily split, Base, 2026-11-03..11-08 (MEASURED; USD at spot).** "Streamed" = Σ rate × seconds of the UTC day; "deposited" = new programs created that day.

| UTC day | Foundation TGE wallet: streamed / deposited | Foundation-signer Safe (RSGP, see below): streamed | Third-party: streamed / deposited (n) |
|---|---|---|---|
| 11-03 | $0 / $0 | $2,451 | $2,615 / $1,003 (4) |
| 11-04 | $0 / $0 | $2,451 | $2,468 / $0 (0) |
| 11-05 | $0 / $0 | $2,451 | $1,960 / $337 (4) |
| 11-06 | $0 / $0 | $2,451 | $1,557 / $7,254 (7) |
| 11-07 | $0 / $0 | $2,451 | $1,602 / $0 (0) |
| 11-08 | $0 / $0 | $2,451 | $1,598 / $2 (1) |

For contrast, 10-23 to 10-28 (MEASURED): the Foundation streamed about $12.7–55k/day and third parties about $3.8–6.3k/day.

- **Ambiguous case: `0x80f7153d9bc853a9bf8bc21f2517c0acee2fdf75`.**
  - It is a 2-of-5 Safe with the **same 5 owners as `0x7269…`** (MEASURED `getOwners()`).
  - It created one 30,000,000 RSGP program: 14 days, 10-29 15:00 → 11-12 15:00 UTC, on VRM `0x4ad4…021f`, tx `0x277e1a28…c6a8`.
  - The RSGP was funded by `0x1ae605b51bb36be453de15cad9a63ebd2cf8ac82`: 37.5M RSGP on 10-27, probably the RSGP issuer.
  - So the Foundation's signers administer it, but the money is a project's own token. Economically it is a third-party launch incentive (CLAIMED, https://x.com/aeroxyz/status/2115218845338382801: "Incentives are already scheduled to stream on Aero to support the TGE").
  - It is worth about $34k at spot (about $77k at the 10-29 price). It makes up about 50–60% of all Base incentives streaming on 11-03..11-08.
  - I classified it **third-party-funded**, but flagged it separately.
- **Other chains (partial, MEASURED).**
  - `0x7269…` has no code on OP, Ethereum, Arbitrum or Ink, so the AERO subsidy is Base-only from this wallet.
  - Ethereum had 17 programs since 10-21. 16 come from Safe `0x42255e3c2d0b71a0b006243148fdf1a71d054ce0` (7 owners; it shares 1 owner each with the Foundation multisig `0xBDE0…EA5a` and the Public Goods Safe), in WETH/USDT, about $11–13k per weekly batch on 10-22, 10-26 and 10-31. The 17th is a $2 USDG program from another address.
  - OP had 13 programs, mostly USDC/alETH from projects. Ink had 0. Arbitrum, Robinhood and Arc were not scanned.
  - I did not identify `0x42255…`; see Open questions.

## 3. When does the subsidy end?

- **CLAIMED, the hub (https://aero.xyz/aero-upgrade/):** "The Aero Foundation is depositing liquid AERO as incentives from the liquid incentive budget it received at Aerodrome's launch to support Aero's migration. The value of liquid AERO earmarked for incentives is roughly equivalent to the final voting rewards accrued on Aerodrome and Velodrome locked in gauges during the upgrade. These incentives are distributed over the course of several weeks. To recoup the value fronted as incentives, The Aero Foundation plans to reactivate the gauges at a later date in order to reclaim locked fees."
  - The same page also says: "The Aero Foundation is depositing AERO incentives on Aero pools over the weeks after launch."
- **CLAIMED, economic case (https://aero.xyz/articles/aero-economic-case):** "the Aerodrome Foundation will incentivize initial allocations and liquidity formation with something close to the amount of fees veAERO and veVELO voters would have received the last epoch … These rewards will start streaming at 0:00:00 UTC of the Thursday following the last epoch." It also mentions an "opening week stream of rewards from the foundation".
- **No dated end or condition is published.** I searched X, the docs and the forum and found only "several weeks" and "opening week".
- **On chain (MEASURED), the Base subsidy has already ended.**
  - The last Foundation program ended **2026-10-29 21:00 UTC**.
  - There have been no new `IncentiveCreated` events from `0x7269…` since block 52,956,614 (10-22).
  - The wallet's AERO balance has been **28,941,560.3 AERO and flat at every daily block from 10-23 to 11-09** (`balanceOf` at the day-start blocks).
  - Unclaimed: Σ `remainingAmount` over its 119 programs = 54,571.5 AERO. That is allocator claims still outstanding plus the sweepable no-allocator share. `sweptAmount` = 0.
- **Signals to watch for a restart or the end of the subsidy:**
  - `balanceOf(0x7269…)`: 1 call/day; a drop means new deposits.
  - `IncentiveCreated` filtered on topic3 = `0x7269…`.
  - `incentiveCountByCreator(0x7269…)` per VRM.
  - `IncentiveSwept` by `0x7269…`: the Foundation recouping unallocated budget.
  - Old-Aerodrome gauge revivals on Voter `0x16613524…80A5`: the planned "reactivate the gauges … to reclaim locked fees" recoup.
  - The 28.9M AERO left (about $16.5M) is far more than this subsidy used, so the balance alone doesn't bound the end date.

## 4. Size of the organic market vs old Aerodrome

- **New, Base, measured.**
  - Third-party streaming is about **$1.6–2.6k/day** on 11-03..11-08, about $2.0k/day on average, or about $0.73M/yr annualized.
  - Adding the RSGP Safe (+$2.45k/day, until 11-12) gives about **$3.6–5.1k/day**.
  - Since launch, 111 third-party programs from 65 creators were deposited, worth about $65.8k at spot (excluding RSGP-Safe, unpriced tUSD1234 and PYPLc).
  - The biggest are a USDC creator `0xb398…9e23` (about $19.5k over 7-day programs), VVV ($4.3k) and AERO from `0x24e9…c401` ($6.5k).
- **New, other chains (measured, partial).** Ethereum is about $1.7k/day from `0x42255…` batches. OP is about $1–1.5k/day.
- **Old Aerodrome (CLAIMED, Blockworks Q3 2026 tokenholder report, https://blockworks.com/api/investor-report/aerodrome-token-holder-report-q3-2026/pdf):** "Outside the LAPTOP entry, voting incentives totaled about $2.2M in Q3 against $4.3M in Q2."
  - That is about **$24k/day in Q3** (92 d) and about **$47k/day in Q2**. The single LAPTOP entry was $4.2M.
- **Read.** Organic third-party incentives on Base now run at about **5–10% of the Q3 old-bribe rate**, or about 20% if the RSGP launch program is counted.
  - This is early: the first three weeks after launch, with the 2-day minimum and Connector-pair caps in force.
  - Caveat: the prices are spot, not at stream time, and most of the small-token programs (RSGP, VEIL, TLOS) have fallen since deposit.

## Options for recording incentives in Orion

All options keep incentives below the line (`vote_incentives`), never as holder flow. Each splits the series into `foundation_subsidy` (creator ∈ {`0x7269…9dDb`}) and `third_party` (everything else, with the RSGP-Safe class flagged).

1. **State-read daily (recommended).** Keep a VRM list, then multicall `incentiveCount()` + `incentive(id)` for every program. Store per-day *streamed* USD per class, computed from rate × overlap; this is what allocators actually earn.
   - VRM discovery: a single-address log scan of the factory `0x8fbaac…` for `VotingRewardsCreated` (~216 getLogs/day at the 2,000-block range, the same budget as the existing Base transfer scan). Alternatively, an incremental cursor.
   - Program reads: about 6 multicalls/day at today's 313 VRMs and 231 programs.
   - Backfill is free from state: programs are immutable and still readable after they end.
   - Cost: ~220 calls/day.
2. **Topic scan of `IncentiveCreated` across all addresses.** Store per-day *deposited* USD per class from the creator topic.
   - Same ~216 calls/day. Simpler, but "deposited" ≠ "earned", because 7–14-day programs are front-loaded.
   - It sits a rung below state reads on Mike's ladder (an all-address topic scan is not a single-address scan).
3. **Foundation-only watch (cheap add-on).** A `monitor_only` level `balanceOf(0x7269…)` plus `incentiveCountByCreator` reads: 1–2 calls/day. It alerts if the subsidy restarts. With Option 1 or 2 it is enough to tag the Foundation, so no separate series is needed.
4. **Claims basis.** Scan `ClaimIncentives` on the VRMs for what was actually paid. That is an all-VRM log scan for no clear gain over Option 1. Not recommended.

Price basis: CRV uses `price_basis: spot`. Options are the price at stream day or at deposit day; Mike to pick.
Multi-chain: Ethereum is in reach via `ORION_ETH_RPC_URL` (factory `0x6BFC…Ec2C`). OP, Arbitrum, Ink, Robinhood and Arc need new chain rows.

## Open questions

1. Is the Foundation's "several weeks" Base-only and already over (as measured: last end 10-29), or are more tranches coming from another wallet or chain? No end date is published. Is it worth asking Aero directly?
2. Who controls Safe `0x42255e3c…` (WETH/USDT weekly batches on Ethereum and OP)? It could be Foundation or Velodrome-side migration support paid in non-AERO tokens, which would change the split.
3. Should the RSGP program run from the Foundation-signer Safe `0x80f7…` count as third-party (the issuer's tokens; my default) or as Foundation?
4. Docs vs chain: the docs say the minimum duration is 7 days; on chain it is 2 days (`minIncentiveDuration` = 172,800).
5. The Foundation's AERO (304,753, about $0.2M) is far below "roughly equivalent to the final voting rewards". Was the rest paid elsewhere (other chains, other tokens), or did "locked in gauges" mean only a subset?
6. Arbitrum, Robinhood and Arc incentive programs were not scanned.
