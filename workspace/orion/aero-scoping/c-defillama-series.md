# C. DefiLlama `aerodrome` fees/revenue series: what it contains (read-only scoping)

Pulled **2026-11-09 20:45Z**. "M" = MEASURED (API URL + this pull). "C" = CLAIMED (source file and line, at
dimension-adapters commit `6006b527`, 2026-11-09). DefiLlama is used here as a reference only: its terms bar
commercial reuse and republishing, and the adapter repo has **no LICENSE file** (M: the repo root of the clone has no LICENSE*).
Two more points bear on that. Every Aero adapter starts with "Changes to this adapter's revenue methodology require further approval
before merging: a Trueo market depends on this data" (C: `dexs/aero-lite/index.ts:1-2`, `dexs/aero-v2/utils.ts:2-3`,
`dexs/aerodrome/utils.ts:1-2`), so a third party settles money on this series. Also, the series is revised
hourly and backfilled (`pullHourly: true`).

## 1. Identity: the slug is now the whole Aero parent, history included (M)
- `https://api.llama.fi/summary/fees/aerodrome?dataType=dailyHoldersRevenue` returns `id: parent#aero-protocol`, `name: Aero`,
  `slug: aero`, previousNames `[Aerodrome, Velodrome, Aero Protocol]`. Its `totalDataChart` is **byte-identical** to the one for slug `aero`, and to the one for slug
  `velodrome` (M, same dataTypes).
- **The redefinition is retroactive.** The chart now starts **2022-06-01** (Velodrome V1's launch), not 2023-08-28, and every
  pre-10-22 day includes the Velodrome chains. So the series did not just change on 2026-10-22: the whole past was rewritten. (M)
- **15 chains:** OP Mainnet, Base, Lisk, Mode, Fraxtal, BOB, Unichain, Soneium, Ink, Swellchain, Celo, Arc, Arbitrum, Ethereum,
  Robinhood Chain. The adapters also already configure **Elysium** from 2026-11-08 (C: `aero-lite/index.ts:36`, `aero-v2/index.ts:28`),
  but it is not in the API's chain list yet (M).
- **7 child protocols** (`childProtocols`, M), with their adapters and live ranges:

| child (defillamaId) | adapter | chains | holder-revenue period |
|---|---|---|---|
| Aerodrome V1 (3450) | `dexs/aerodrome` | Base | to 10-15 (fees), to 10-21 (bribes) |
| Aerodrome Slipstream (4524) | `dexs/aerodrome-slipstream` | Base | to 10-15 (fees), to 10-21 (bribes) |
| Velodrome V1 (1799) | `fees/velodrome` | OP | legacy, ~$0-8/day |
| Velodrome V2 (3302) | `dexs/velodrome-v2` | OP, Mode, BOB, Lisk, Fraxtal, Ink, Soneium, Unichain, Swell (dead 06-30) | per-chain end (below) |
| Velodrome V3 = Velodrome Slipstream (4249) | `dexs/velodrome-slipstream` | OP, Mode, Lisk, Ink, Soneium, Fraxtal, Unichain, Swell, Celo | per-chain end |
| **Aero Slipstream** (8691) | `dexs/aero-lite` | Base, OP, Arbitrum, Ethereum, Ink, Robinhood, Arc (+Elysium) | from 2026-10-21 (Arc's Aero Lite from 09-16, LP-only) |
| **Aero Basic** (9172) | `dexs/aero-v2` | the same 7 chains (+Elysium) | from 2026-10-21 |

  "Aero Lite" is not a separate child. It is the original Arc-only deployment, folded into Aero Slipstream, with no gauges, so 100% of its fees go to LPs and
  $0 to holders (C: `aero-lite/index.ts:18-21,57-88`).
- **dataTypes:** `dailyFees`, `dailyRevenue`, `dailyHoldersRevenue`, `dailyProtocolRevenue` and `dailySupplySideRevenue` return 200 (M).
  `dailyBribesRevenue` and `dailyTokenTaxes` return **400** ("not found") for `aerodrome`, `aero` and every child slug (M). They were
  removed as dataTypes on 2026-06-16 (C: commit `05219338` "rug dailyBribesRevenue and dailyTokenTax"). Bribes now exist only as a
  *label* inside Fees, Revenue and HoldersRevenue. `hasLabelBreakdown: true`, but the public summary endpoint ignores
  `breakdownByLabel`, `breakdown=label`, `groupBy=label` and `labels=true` (M). **So bribes cannot be separated from swap fees through the free API.**

## 2. What each dataType counts (C, from adapter source)
**Legacy Aerodrome/Velodrome (to 10-22).**
- Fees = swap fees + bribes (`NotifyReward` on each gauge's bribeVotingReward, valued when deposited).
- HoldersRevenue = the staked-LP fee share + bribes:
  - V1 basic pools: fee × `balanceOf(gauge)/totalSupply`, snapshotted at the cron block (C: `aerodrome/index.ts:84-88,145-148,198-200`).
  - Slipstream: Δ`gaugeFees()` + `CollectFees` = staked-LP fees + the unstaked-LP rake (C: `aerodrome-slipstream/index.ts:60-66,114-117,275`).
  - Velodrome V3: stakedShare + (1−stakedShare)·unstakedFee (C: `velodrome-slipstream/index.ts:116-117`).
- Bribes go to holders (C: `aerodrome/utils.ts:42`).
- After each chain's last fee distribution (`VOTER_FEES_END`: Base/OP/Ink 2026-10-15; Unichain/Fraxtal/Soneium/Celo 09-24;
  Lisk 07-16; Mode 06-18), the staked-LP share moves from Holders to **ProtocolRevenue**, labelled "Staked-LP Fees Locked In Deactivated Gauges"
  (it waits for the Aero Foundation to reclaim it). Bribes stop for days ending after 2026-10-22 00:00Z (C: `aerodrome/utils.ts:15-45`). This gating landed in
  commit `b577160e` on **2026-10-22 14:06Z**.
- Ignition launch tokens: bribes paid in a token that does not trade yet are valued at a hand-set price (C: `aerodrome/utils.ts:48-138`).
  `$LAPTOP` (0xb095…) is priced at **$1.86 until 2026-09-10** (commit `a8abafb3`, 2026-09-10).

**Aero (from 10-21).**
- Fees = swap fees + bribes ("Liquidity Payments", counted as they stream).
- HoldersRevenue = Revenue = the fees accruing to the gauges + bribes (C: `aero-lite/index.ts:180`, `aero-v2/index.ts:127`).
  - Slipstream: Δ`gaugeFees()` + `CollectFees` (C: `aero-lite/index.ts:90-98,156`).
  - Basic: Δ`pendingFees(gauge)` + `Claim(account=gauge)` (C: `aero-v2/index.ts:38-42,92-106`).
- SupplySide = the rest of the swap fee, which fee-earning LPs keep.
- ProtocolRevenue is not emitted for the Aero children (M: 0).

| question | answer |
|---|---|
| Swap fees | yes, in every dataType (Holders = the gauge/staked share only) |
| Gauge-staked share | yes, the core of HoldersRevenue (legacy to 10-15; Aero from 10-21) |
| **MEV / hook fees** | **yes, from 10-21 on Aero pools.** Slipstream fee = the tape `cumulativeFee` "MEV tax included" (`cumulativeMevFee` is a subset and is not re-added). Basic = the `Fees` event "MEV tax included" (C: `aero-lite/index.ts:90-93`, `aero-v2/index.ts:38-39`). The holder share is whatever accrues to the gauge, so the MEV part is included as far as it is routed there. Legacy pools have no MEV term. |
| **Bribes / incentives** | **yes, inside HoldersRevenue, before and after the merger.** Post-merger this includes "Programs funded by Aero itself … they carry value over from the legacy pools" (C: `aero-v2/utils.ts:126-129`): **protocol-funded incentives count as holder revenue**. |
| Emissions value (AERO rewards to LPs) | no. Nothing values emissions. |
| Locked legacy gauge fees (after 10-15) | in Revenue/ProtocolRevenue, **not** in HoldersRevenue |
| Pricing | AERO/xAERO on every chain is valued at the Base Aerodrome AERO price. Fees in unpriced tokens are converted at the swap rate (C: `aero-v2/utils.ts:16-37,53-64`). Blacklisted and wash pools are dropped. |

**This contradicts Orion's config comment.** `assets/aero.yaml:77-78` says "Incentives (bribes) to lockers have no usable series and are
left out". DefiLlama's `dailyHoldersRevenue` has **always included bribes** for Aerodrome, so Orion's `flow_usd.fees` does include them. The
same goes for 09-09. On that day Base Slipstream Fees were 8,075,704 and Holders 7,864,721, but SupplySide was only 210,982 (normal) (M). An excess that sits
entirely in Holders and not in LP fees fits bribes, not swap fees. The likely cause is $LAPTOP Ignition bribes valued at the hand-set
$1.86 on its launch day (C, inference: commit `a8abafb3` set that price the next day). This revises the 2026-09-24 ruling, which read the excess as Slipstream *fees*.

## 3. Daily values 2026-10-15..11-08 (M, all from `https://api.llama.fi/summary/fees/aerodrome?dataType=<dt>`, `totalDataChartBreakdown`, pulled 2026-11-09 20:45Z; USD)
### All dataTypes, all chains
| day | Fees | Revenue | HoldersRev | ProtocolRev | SupplySide | Holders Base % |
|---|---|---|---|---|---|---|
| 10-15 | 507,119 | 344,336 | 344,336 | 0 | 162,776 | 95.4 |
| 10-16 | 378,463 | 259,346 | 259,346 | 0 | 119,112 | 94.6 |
| 10-17 | 215,517 | 153,577 | 153,577 | 0 | 61,942 | 95.6 |
| 10-18 | 265,361 | 190,273 | 190,273 | 0 | 75,085 | 95.4 |
| 10-19 | 282,297 | 197,279 | 197,279 | 0 | 85,010 | 95.4 |
| 10-20 | 386,133 | 261,823 | 261,823 | 0 | 124,309 | 92.6 |
| 10-21 | 323,870 | 229,335 | 229,335 | 0 | 94,529 | 95.5 |
| 10-22 | 267,808 | 177,905 | 145,005 | 32,899 | 89,899 | 87.8 |
| 10-23 | 369,584 | 278,599 | 246,065 | 32,535 | 90,987 | 85.5 |
| 10-24 | 259,489 | 173,823 | 148,878 | 24,945 | 85,663 | 87.4 |
| 10-25 | 203,398 | 148,121 | 135,527 | 12,594 | 55,269 | 87.1 |
| 10-26 | 335,454 | 257,597 | 243,977 | 13,620 | 77,849 | 84.4 |
| 10-27 | 276,316 | 208,692 | 196,912 | 11,780 | 67,625 | 83.5 |
| 10-28 | 322,594 | 251,119 | 241,262 | 9,857 | 71,471 | 82.1 |
| 10-29 | 526,117 | 396,835 | 378,739 | 18,096 | 129,287 | 74.7 |
| 10-30 | 401,273 | 314,343 | 294,479 | 19,864 | 86,927 | 83.8 |
| 10-31 | 208,899 | 171,521 | 164,597 | 6,924 | 37,394 | 69.8 |
| 11-01 | 174,182 | 141,098 | 136,051 | 5,047 | 33,078 | 76.6 |
| 11-02 | 303,837 | 250,947 | 243,596 | 7,351 | 52,885 | 77.3 |
| 11-03 | 274,285 | 227,822 | 220,637 | 7,184 | 46,473 | 77.3 |
| 11-04 | 476,352 | 380,453 | 366,367 | 14,085 | 95,905 | 81.9 |
| 11-05 | 440,633 | 348,681 | 334,947 | 13,735 | 91,966 | 82.3 |
| 11-06 | 362,946 | 304,139 | 295,092 | 9,047 | 58,803 | 81.3 |
| 11-07 | 184,910 | 151,366 | 147,191 | 4,174 | 33,543 | 82.5 |
| 11-08 | 257,328 | 208,364 | 201,274 | 7,091 | 48,961 | 82.2 |

### HoldersRevenue by chain ("other" = Velodrome-only chains)
| day | total | Base | Ethereum | Robinhood | Arbitrum | OP | Arc | Ink | other | Base % |
|---|---|---|---|---|---|---|---|---|---|---|
| 10-15 | 344,336 | 328,475 | 0 | 0 | 0 | 13,013 | 0 | 2,839 | 9 | 95.4 |
| 10-16 | 259,346 | 245,438 | 0 | 0 | 0 | 12,780 | 0 | 1,123 | 4 | 94.6 |
| 10-17 | 153,577 | 146,831 | 0 | 0 | 0 | 5,931 | 0 | 813 | 2 | 95.6 |
| 10-18 | 190,273 | 181,551 | 0 | 0 | 0 | 7,306 | 0 | 1,412 | 4 | 95.4 |
| 10-19 | 197,279 | 188,141 | 0 | 0 | 0 | 7,823 | 0 | 1,308 | 7 | 95.4 |
| 10-20 | 261,823 | 242,496 | 0 | 0 | 0 | 14,317 | 0 | 4,999 | 11 | 92.6 |
| 10-21 | 229,335 | 219,050 | 0 | 0 | 0 | 8,561 | 0 | 1,718 | 6 | 95.5 |
| 10-22 | 145,005 | 127,249 | 6,042 | 7,082 | 1,165 | 2,434 | 765 | 265 | 3 | 87.8 |
| 10-23 | 246,065 | 210,437 | 13,544 | 15,464 | 2,424 | 2,577 | 1,598 | 21 | 0 | 85.5 |
| 10-24 | 148,878 | 130,127 | 6,893 | 7,698 | 1,140 | 2,107 | 760 | 153 | 0 | 87.4 |
| 10-25 | 135,527 | 118,035 | 6,653 | 7,070 | 984 | 2,048 | 563 | 174 | 0 | 87.1 |
| 10-26 | 243,977 | 205,986 | 13,756 | 15,490 | 4,419 | 3,111 | 1,033 | 182 | 0 | 84.4 |
| 10-27 | 196,912 | 164,457 | 11,927 | 12,287 | 4,573 | 2,707 | 793 | 168 | 0 | 83.5 |
| 10-28 | 241,262 | 197,960 | 15,158 | 17,691 | 6,424 | 2,732 | 1,036 | 261 | 0 | 82.1 |
| 10-29 | 378,739 | 282,995 | 56,137 | 22,587 | 8,227 | 3,916 | 3,879 | 998 | 0 | 74.7 |
| 10-30 | 294,479 | 246,798 | 19,529 | 14,715 | 7,329 | 3,129 | 1,267 | 1,712 | 0 | 83.8 |
| 10-31 | 164,597 | 114,873 | 35,880 | 7,213 | 4,307 | 1,537 | 322 | 465 | 0 | 69.8 |
| 11-01 | 136,051 | 104,161 | 14,840 | 10,254 | 4,491 | 1,504 | 266 | 535 | 0 | 76.6 |
| 11-02 | 243,596 | 188,179 | 23,170 | 19,422 | 6,958 | 3,494 | 652 | 1,721 | 0 | 77.3 |
| 11-03 | 220,637 | 170,476 | 20,812 | 15,310 | 6,494 | 5,925 | 583 | 1,037 | 0 | 77.3 |
| 11-04 | 366,367 | 300,099 | 24,712 | 25,338 | 8,848 | 3,899 | 1,582 | 1,889 | 0 | 81.9 |
| 11-05 | 334,947 | 275,548 | 20,699 | 23,959 | 8,061 | 3,969 | 1,256 | 1,455 | 0 | 82.3 |
| 11-06 | 295,092 | 239,823 | 18,993 | 23,755 | 7,259 | 3,219 | 765 | 1,278 | 0 | 81.3 |
| 11-07 | 147,191 | 121,399 | 10,055 | 10,033 | 3,968 | 1,356 | 139 | 241 | 0 | 82.5 |
| 11-08 | 201,274 | 165,518 | 12,977 | 13,599 | 4,771 | 3,444 | 417 | 548 | 0 | 82.2 |

### HoldersRevenue by child
| day | Aerodrome V1 | Aerodrome Slipstream | Aero Slipstream | Aero Basic | Velodrome V1+V2+V3 |
|---|---|---|---|---|---|
| 10-15 | 32,256 | 296,219 | 0 | 0 | 15,861 |
| 10-16 | 25,524 | 219,914 | 0 | 0 | 13,908 |
| 10-17 | 10,477 | 136,354 | 0 | 0 | 6,746 |
| 10-18 | 18,444 | 163,107 | 0 | 0 | 8,722 |
| 10-19 | 15,640 | 172,501 | 0 | 0 | 9,138 |
| 10-20 | 29,810 | 212,686 | 0 | 0 | 19,327 |
| 10-21 | 18,824 | 200,226 | 0 | 0 | 10,285 |
| 10-22 | 10,031 | 20,417 | 97,268 | 15,868 | 1,422 |
| 10-23 | 0 | 0 | 223,322 | 22,737 | 6 |
| 10-24 | 0 | 0 | 138,585 | 10,288 | 5 |
| 10-25 | 0 | 0 | 123,674 | 11,849 | 4 |
| 10-26 | 0 | 0 | 229,070 | 14,899 | 8 |
| 10-27 | 0 | 0 | 185,612 | 11,296 | 4 |
| 10-28 | 0 | 0 | 228,795 | 12,461 | 6 |
| 10-29 | 0 | 0 | 357,303 | 21,425 | 11 |
| 10-30 | 0 | 0 | 276,147 | 18,321 | 11 |
| 10-31 | 0 | 0 | 156,393 | 8,200 | 4 |
| 11-01 | 0 | 0 | 130,537 | 5,512 | 2 |
| 11-02 | 0 | 0 | 235,278 | 8,313 | 5 |
| 11-03 | 0 | 0 | 212,383 | 8,250 | 4 |
| 11-04 | 0 | 0 | 350,697 | 15,661 | 9 |
| 11-05 | 0 | 0 | 317,245 | 17,694 | 8 |
| 11-06 | 0 | 0 | 282,830 | 12,257 | 5 |
| 11-07 | 0 | 0 | 139,901 | 7,289 | 1 |
| 11-08 | 0 | 0 | 192,399 | 8,870 | 5 |

### Fees by child (legacy pools keep trading after the merger; their fees are now SupplySide plus locked ProtocolRevenue)
| day | Aerodrome V1 | Aerodrome Slipstream | Aero Slipstream | Aero Basic | Velodrome V1+V2+V3 |
|---|---|---|---|---|---|
| 10-15 | 46,712 | 442,246 | 1,707 | 0 | 16,454 |
| 10-16 | 33,691 | 329,318 | 1,099 | 0 | 14,355 |
| 10-17 | 15,551 | 192,563 | 542 | 0 | 6,861 |
| 10-18 | 26,006 | 229,647 | 839 | 0 | 8,869 |
| 10-19 | 23,208 | 248,444 | 1,234 | 0 | 9,411 |
| 10-20 | 40,644 | 323,726 | 1,936 | 0 | 19,827 |
| 10-21 | 29,737 | 282,381 | 1,104 | 0 | 10,648 |
| 10-22 | 30,551 | 112,293 | 104,810 | 16,106 | 4,048 |
| 10-23 | 16,925 | 89,556 | 238,156 | 23,152 | 1,795 |
| 10-24 | 13,972 | 83,548 | 149,701 | 10,503 | 1,765 |
| 10-25 | 12,969 | 45,464 | 132,039 | 11,923 | 1,002 |
| 10-26 | 11,412 | 59,946 | 246,955 | 15,192 | 1,949 |
| 10-27 | 12,749 | 49,796 | 201,518 | 11,422 | 832 |
| 10-28 | 10,223 | 52,443 | 246,123 | 12,627 | 1,178 |
| 10-29 | 16,891 | 72,682 | 412,211 | 21,772 | 2,561 |
| 10-30 | 18,233 | 58,529 | 303,292 | 18,860 | 2,360 |
| 10-31 | 10,374 | 24,344 | 165,223 | 8,587 | 371 |
| 11-01 | 8,436 | 22,894 | 136,718 | 5,783 | 351 |
| 11-02 | 9,981 | 34,863 | 249,426 | 8,843 | 724 |
| 11-03 | 9,331 | 30,770 | 225,289 | 8,400 | 495 |
| 11-04 | 17,122 | 61,503 | 380,096 | 15,892 | 1,740 |
| 11-05 | 20,238 | 50,427 | 350,057 | 18,004 | 1,907 |
| 11-06 | 9,875 | 31,717 | 308,057 | 12,548 | 749 |
| 11-07 | 7,459 | 17,874 | 151,774 | 7,558 | 244 |
| 11-08 | 7,789 | 27,458 | 211,906 | 9,167 | 1,008 |

**A data inconsistency on 10-15..10-22 (M + C).** The current code books Base/OP/Ink staked-LP fees for days ending after 10-15 as ProtocolRevenue.
The API still shows ProtocolRevenue = 0 and Holders = Revenue for 10-15..10-21, and the first locked value (32,899) appears on 10-22. Legacy holders
on 10-15..10-22 total **$1,667,839**. Those days were computed before `b577160e` was deployed (10-22 14:06Z; the job pulls hourly) and have not been refilled.
If DefiLlama backfills them, up to that amount, minus the bribes in it, moves out of HoldersRevenue: about **−$6.7M/yr at most** on a 91-day window
(not splittable through the free API).

**Revision drift (M vs the brief's claim).** The brief says 11-05 = $304K total and $54K non-Base. Today's pull gives 11-05 = $334,947 total and $59,399 non-Base (+10%).

## 4. The 10-22 definition break and Orion's 91-day window (M, holders, window 2026-08-10..11-08)
- Base share of HoldersRevenue: **96.3%** on 08-10..10-21 (non-Base = Velodrome) → **81.0%** on 10-23..11-08 (non-Base = Aero on 6 other chains:
  Ethereum 8.2%, Robinhood 6.6%, Arbitrum 2.3%, OP 1.3%). For Fees: 97.0% → 84.8%.
- Post-merger run rate (10-23..11-08, 17 days): all chains **$85.8M/yr**, Base only **$69.5M/yr**.
- 91-day window, annualized (×365/91), ending 11-08:

| variant | $/yr |
|---|---|
| API as is, all chains (09-09 spike included) | 116.43M |
| all chains, 09-09 → Orion's manual 261,631 | **85.62M** |
| Base only, 09-09 → manual | **78.91M** |
| hybrid: Base only before 10-10, all chains from 10-10 (a guess at Orion's 30-day revision window) | 82.68M |
| Orion's report today | 83.6M (C, from the brief) |

- Non-Base adds **$6.71M/yr (+8.5%)**: $3.68M/yr is Velodrome history before 10-22, which the retroactive rewrite brought in, and $3.11M/yr is Aero on other chains after 10-22.
- Orion's 83.6M lies between Base-only and all-chains, which fits a mix of rows stored under the old and new definitions. I did not verify this, because the DB was not read.
- The window also holds the stale 10-15..10-22 legacy holders ($1.67M, see §3) and leaves out $250,828 of locked ProtocolRevenue.

## Reconciliation recipe (what an on-chain scan must sum to match each series, per chain/day, UTC days)
**Aero Slipstream** (`aero-lite`). Chains: Base, OP, Arbitrum, Ethereum, Ink, Robinhood, Arc, plus Elysium from 11-08. Pools come from `PoolCreated` on each chain's CL factory (`aero-lite:29-36`).
- *Fees*: Δ `clPoolTape.accumulators(pool).cumulativeFee0/1` (end − start, reading the start at fromBlock−1). The tape address is `factory.clPoolTape()`. Plus the bribe streams (below).
- *Holders*: Δ `pool.gaugeFees()` + Σ `CollectFees` amounts, clamped to [0, fee]. Plus the bribe streams.
- *SupplySide*: fee − holders.
- Arc Aero Lite (factory 0xb89D…): Σ swap input × `fee()` sampled every 1000 blocks, all of it SupplySide.

**Aero Basic** (`aero-v2`). Same chains. VolatilePoolFactory is 0x8E6a…, StablePoolFactory is 0x7858….
- *Fees*: Σ `Fees` events.
- *Holders*: Δ `pool.pendingFees(gauge)` + Σ `Claim` where account = gauge. Plus the bribe streams.

**Bribe streams (Aero).** Take gauges and rewards contracts from FactoryRegistry (`gaugeFactories` → `factoryToGauges` → `gaugeToRewards`).
- For every `incentive(i)` program: rate × allocated seconds in the day / 1e18.
- Allocated seconds exclude the zero-supply seconds (`globalRewardPointHistory`, `supplyAt`).
- Count protocol-funded programs too, if you want to match DefiLlama. Tag them separately, because they are not user-paid.

**Legacy Aerodrome V1** (Base, PoolFactory 0x420D…, Voter 0x1661…). Up to 10-15 (fees) and 10-21 (bribes).
- *Fees*: Σ swap amounts × `getFee(pool, stable)`, plus bribes.
- *Holders*: fee × `balanceOf(gauge)/totalSupply`, using a single daily snapshot (an approximation; on chain, the exact figure is the ClaimFees from the FeesVotingReward).
- *Bribes*: Σ `NotifyReward` on bribeVotingReward contracts from `GaugeCreated` (canonical gauge factory only). Price Ignition tokens by DefiLlama's hand-set map.

**Legacy Aerodrome Slipstream** (Base). Four factories, four gauge factories (`aerodrome-slipstream:16-47`).
- Fees = Σ swap × `fee()`.
- Holders = Δ`gaugeFees()` + Σ`CollectFees`.
- Bribes are counted as for V1.

**Velodrome V2/V3** (chains as in §1).
- The same structure as above, using leaf Voter `incentiveVotingReward` on the superchain chains.
- After each chain's `VOTER_FEES_END`, the staked share goes to ProtocolRevenue, not Holders.

**Exclusions.** DefiLlama drops pools on its token blacklist and Dune-flagged wash pools (unless both tokens are established), so the scan must apply the same lists or report the difference.

**Valuation.** AERO and xAERO on any chain are valued at the Base AERO price. Tokens with no price are converted to the pool's other token at the day's swap rate.

## Open questions
1. How large are the bribes inside HoldersRevenue, before and after 10-22? The free API has no label breakdown. Is there a Pro endpoint with labels, or does it need an on-chain `NotifyReward` / `incentive()` scan?
2. How much of the post-merger "bribes" are Aero-funded carry-over programs (self-incentives) rather than third-party payments? DefiLlama counts both as holder revenue (`aero-v2/utils.ts:128`).
3. What share of the MEV tax reaches the gauge (holders) and what share stays with LPs or the protocol? The adapter just takes the gauge's accrual. To settle it, read `DynamicSwapFeeHook` and the tape's `cumulativeMevFee`.
4. Will DefiLlama refill 10-15..10-22 under the gating code? That would move up to $1.67M out of holders.
5. What does Orion actually store per day (old vs new definition)? Checking needs a read-only prod `sql-ro`, which was out of scope here. It decides whether 83.6M is the hybrid figure.
6. Is the 09-09 spike $LAPTOP bribes at $1.86? A `NotifyReward` scan on Base for 2026-09-09, token 0xb095…, would confirm it.
7. Elysium (from 11-08) will add an 8th Aero chain once DefiLlama lists it.
8. Locked legacy gauge fees ($250,828 in the window and still growing) go to holders only if the Aero Foundation reclaims and distributes them. That is not decided.
