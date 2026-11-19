# R3 scoping: SKY and LIT circulating supply on chain

All **measured** figures: Ethereum block 26,449,747 (2026-11-19 14:32:35 UTC) unless stated otherwise. Prices used for $
effects are prod's own report prices: SKY $0.050308 (`report-sky.json`, day 2026-11-18), LIT $2.88527 (`report-lit.json`,
day 2026-11-17). CoinGecko figures are **dev-only reference** (`prod/coingecko-markets-devonly.json`, 2026-11-19 14:29Z).

## Summary

**SKY**
1. Proposed circulating **23,372.85M SKY** = totalSupply − Pause Proxy balance − MkrSky converter `take()` (fee SKY owned by the protocol).
2. vs CoinGecko 23,412.90M (dev-only): **−0.17%**. CoinGecko's figure is exactly totalSupply − Pause Proxy, to within 0.06M over four dates.
3. vs prod's stored 23,414.15M (2026-11-19 00:46Z): **−0.18%** (−$2.0M of market cap).
4. Method: `chain.view_sum` with 3 terms; the existing adapter covers it, with one new `contracts:` entry (`mkr_sky`). Plain views, so history at archive blocks back to 2025-10-13 works.
5. Open decisions: lsSKY stays in circulating (rec: yes; it can be withdrawn at any time with a 0% exit fee, unlike veAERO; excluding it is −74.5%, −$876M); MKR-backed SKY stays in (rec; strict exclusion is −8.5%); optional 5% delayed-upgrade-penalty haircut (−0.42%).

**LIT**
1. Proposed circulating **245.11M LIT** = (1B − dead) − ecosystem reserve − team/investor locked (500M by cited schedule) − buyback wallet.
2. vs CoinGecko 250M (dev-only, static airdrop figure): **−1.95%**.
3. vs prod's stored 250M (2026-11-19 00:45Z): **−1.95%** (−$14.4M of market cap).
4. Method: `chain.view_sum` (total, −dead, −reserve, −buyback) plus a cited locked-schedule term (Lighter's post: 500M, 1y lock and 3y linear vesting; Orion's terms: 36 monthly tranches from 2027-01-29). This needs one small extension (a `locked:` param on view_sum, or a `derived` minus), because view_sum cannot subtract a schedule. On-chain check: the 262 allocation wallets hold exactly 500.000M today.
5. Open decisions: after the cliff, use the schedule or the wallet balances (rec: schedule, with the wallets as a monitor); the L2 treasury's 2.02M LIT (rec: leave in, since it is API-only and has no history); staked LIT stays in circulating (rec).

---

# SKY

## 1. Today's numbers
| figure | value (SKY) | vs proposed | basis |
|---|---|---|---|
| on-chain total (`totalSupply`, Orion's `total_supply`) | 23,452,431,916 | +0.34% | measured |
| CoinGecko circulating (dev-only) | 23,412,904,591 | +0.17% | 2026-11-19 14:29Z |
| prod stored circulating | 23,414,153,680 | +0.18% | 2026-11-19 00:46Z (CoinGecko /coins/markets) |
| **proposed on-chain circulating** | **23,372,844,722** | 0 | measured |

Market cap at $0.050308: proposed $1,175.8M; prod $1,177.9M.

## 2. Proposed method
`chain.view_sum` on chain 1 (the existing adapter is enough):
```yaml
contracts:
  mkr_sky: "0xA1Ea1bA18E88C381C724a75F23a130420C403f9a"   # new: MkrSky converter (Sky chainlog MKR_SKY)
  # token, pause_proxy already in sky.yaml
circulating_supply:
  source:
    type: adapter
    name: chain.view_sum
    params:
      terms:
        - { contract: token, function: totalSupply }
        - { contract: token, function: balanceOf, args: [ pause_proxy ], sign: -1 }
        - { contract: mkr_sky, function: take, sign: -1 }     # MkrSky.take(): accumulated SKY fee, protocol-owned
```
(`take()` is a public `uint256` on MkrSky, per its verified source: "accumulated SKY fee available for collection".)

## 3. Exclusion list
| address | label | what it is | balance now (measured) | citation | moves? |
|---|---|---|---|---|---|
| 0xBE8E3e3618f7474F8cB1d074A26afFef007E98FB | MCD_PAUSE_PROXY | Sky governance treasury: receives the flapper's buyback SKY and pays the reward vests (dss-vest id 18 → VestedRewardsDistribution → SKY farm) | 39,602,953 | Sky chainlog `https://chainlog.sky.money/api/mainnet/active.json`: `"MCD_PAUSE_PROXY": "0xBE8E…98FB"`; Blockscout name DSPauseProxy | yes, daily: buybacks in, weekly vest drips out (sawtooth 24–40M) |
| 0xA1Ea…3f9a `take()` | MKR_SKY (MkrSky) | 5% delayed-upgrade-penalty fees kept from MKR conversions, collectable by governance via `collect(to)` | 39,984,240 (of a 2,023.90M converter balance) | chainlog `"MKR_SKY": "0xA1Ea…3f9a"`; MkrSky source: `uint256 public take; // accumulated SKY fee available for collection`; penalty: https://upgrademkrtosky.sky.money/ "reduces the amount of SKY received per MKR upgraded by a rate of 1%. The reduction will increase by an additional 1% every three months"; 5% since the 2026-09-10 spell (https://forum.skyeco.com/t/delayed-migration-penalty-update-september-10th-spell/28218) | grows with each conversion (2.30M on 2025-10-13 → 34.37M on 2026-08-20 → 39.98M) |

**Kept in circulating (measured, with reasons):**
- **MKR-backed SKY in the converter: 1,983,919,174** (= MKR totalSupply 82,663.30 × 24,000, which reconciles exactly with converter balance − take). MKR still trades and can be converted on demand. Holders get 95% today: on conversion, 5% (99.2M) moves into `take` and the method then removes it automatically.
- **lsSKY: 17,415,660,062** (LockstakeEngine 10,282.36M + delegated SKY in Chief/MCD_ADM 7,133.35M). LockstakeEngine `fee()` = 0, so it can be withdrawn at any time with no exit fee. See §7.
- **SKY farm (REWARDS_LSSKY_SKY) 0xB44C…40Fc: 96.69M.** Only 4.18M is unearned (rewardRate 1.106M/day × time to periodFinish 2026-11-23). The rest is earned-but-unclaimed and belongs to stakers.
- **USDS→SKY farm (REWARDS_USDS_SKY) 0x0650…0275: 19.54M.** periodFinish was 2026-01-26, so all of it is earned and owed to depositors.
- **treasury_safe 0xca51…22a0: 37.69M.** A 3-of-6 Safe that is not in Sky's chainlog. It cycles SKY in and out of LockstakeEngine (640.7M in, 753.0M out) and sent the 500M top-up to the Pause Proxy on 2025-11-03. Its ownership is unclear and there is no citation that it is protocol-owned, so it stays in (CoinGecko also counts it).
- Splitter 0, flapper 0, USDS farm 0 SKY, dead 0, SKY's own contract balance 0: nothing to exclude.

## 4. Reconciliation with CoinGecko (dev-only)
CoinGecko's SKY circulating = totalSupply − Pause Proxy balance, almost exactly (measured at the block of each stored row):

| CoinGecko row | block | total − PP | CoinGecko | residual |
|---|---|---|---|---|
| 2026-10-16 18:05Z | 26,206,776 | 23,428.036M | 23,428.082M | +0.046M |
| 2026-11-16 00:45Z | 26,424,078 | 23,412.212M | 23,412.273M | +0.061M |
| 2026-11-17 00:45Z | 26,431,263 | 23,417.940M | 23,418.004M | +0.064M |
| 2026-11-19 00:46Z | 26,445,629 | 23,414.088M | 23,414.154M | +0.065M |

So CoinGecko is live (its daily sawtooth tracks the Pause Proxy). The only difference from our method is the converter's `take` (40.0M, −0.17%): CoinGecko counts it, we don't. The residual 0.05–0.07M is unexplained and immaterial (0.0003%). Testing the alternative "total − take" as CoinGecko's method fails: it misses by 0.2–15M.

## 5. Check
**None first-party.** Sky publishes no circulating-supply figure or endpoint. sky.money and the chainlog list contracts, not supply. Tokenomist and CoinGecko are third-party. Proposal: no live check. The method's parts are Sky's own canonical contracts (chainlog-named), and `take` is recomputable as converter balance − MKR.totalSupply × rate (exact today). That identity could be a dev-time consistency probe, not a check against an independent source.

## 6. History
All terms are plain views, so the method reads at archive blocks. Measured:
- **2026-08-20 00:00Z (block 25,792,601):** total 23,462.665M − PP 36.027M − take 34.368M = **23,392.270M**.
- 2025-10-13 00:00Z (block 23,565,080): total 23,462.665M − PP 61.718M − take 2.302M = 23,398.645M (MkrSky has code at that block, so `take()` reads).

## 7. Open questions / options for Mike (market cap at $0.050308; base = proposed 23,372.85M = $1,175.8M)
| option | circulating | vs proposed | $ effect | rec |
|---|---|---|---|---|
| A. total − Pause Proxy (CoinGecko's method) | 23,412.83M | +0.17% | +$2.0M | no: `take` is protocol-owned SKY |
| **B. A − converter `take` (proposed)** | **23,372.85M** | 0 | 0 | **yes** |
| B′. B − 5% penalty on MKR-backed SKY (99.2M) | 23,273.65M | −0.42% | −$5.0M | no: it needs a product term view_sum can't express, and the penalty only bites if holders convert (it rises 1pt per quarter) |
| C. strict "SKY in hand": exclude the whole converter balance | 21,388.93M | −8.49% | −$99.8M | no: MKR is convertible on demand and trades |
| D. AERO precedent: also exclude lsSKY | 5,957.19M | −74.51% | −$876.2M | **no**: lsSKY has no lock term and a 0% exit fee (`LockstakeEngine.fee()` = 0). veAERO is a long or permanent lock, so the precedent doesn't extend |
| E. also exclude treasury_safe 37.69M | 23,335.16M | −0.16% | −$1.9M | no, unless Sky confirms it is protocol-owned |
| F. also exclude unearned SKY-farm rewards (4.18M) | 23,368.67M | −0.02% | −$0.2M | no: immaterial, and it can't be expressed as views (rewardRate × time left) |

---

# LIT

## 1. Today's numbers
| figure | value (LIT) | vs proposed | basis |
|---|---|---|---|
| on-chain total (Orion `total_supply` = 1B − dead 18,090,720) | 981,909,280 | +300.6% | measured |
| CoinGecko circulating (dev-only) | 250,000,000 | +2.0% | static since TGE |
| prod stored circulating | 250,000,000 | +2.0% | 2026-11-19 00:45Z (CoinGecko) |
| **proposed on-chain circulating** | **245,112,910** | 0 | measured + cited schedule |

Market cap at $2.88527: proposed $707.2M; prod $721.3M (−$14.4M, −1.95%).

## 2. Where the supply sits (measured trace of the mint)
The mint: 1,000,000,000 LIT to 0x0778…1891 (a small contract) on 2025-10-27. Its 10 outgoing transfers are the whole allocation:

| date | to | amount | what (matches Lighter's split) |
|---|---|---|---|
| 2025-12-20 | 0x98e7…2b5f (distributor 1) | 250M | team/investor |
| 2025-12-22 + 12-30 | 0xb305…19e4 (distributor 2) | 150M + 100M | team/investor |
| 2025-12-30 | 0x3B4D…5ca7 **ZkLighter** (the L2 bridge) | 250M | airdrop (25%), credited on L2 |
| 2026-01-07 | 0xe554…9D62 ecosystem reserve | 250M | remaining ecosystem 25% |

- The two distributors fanned 500M out to **261 beneficiary wallets** (EOAs; D1 also sent 74.44M to D2) between 2025-12-24 and 2026-08-17. Measured now: **the 261 wallets hold 463,883,556 and D2 holds 36,116,444, total 500,000,000.0 exactly.** Only one wallet ever moved tokens (0xc4f1…816b, 1.268M), and it sent them back to D2 on 2026-01-30. On 2026-08-20 the same set held 500.0M. So the unvested team/investor tokens are on chain, untouched, in plain EOAs (no vesting contract).
- The ecosystem reserve: 250M in; out 0.1M (2026-07-03, to 0x5e52…), 15.639M (2026-07-10) and 2.452M (2026-10-09) to burn_safe for the burns. Now 231.809M.
- **The bridge (ZkLighter 0x3B4D…5ca7, Etherscan label "Lighter: ZkLighter")** holds 136.80M LIT: all LIT on Lighter's L2. The airdrop went there. The L2 split (Lighter API, measured 2026-11-19 ~14:35Z):
  - staking pool (systemConfig `staking_pool_index` 281474976624800): 98.47M, holders' stakes (operator shares 0.1%)
  - treasury/fee account 0: **2.017M** (bought LIT not yet withdrawn)
  - fee collector 281474976496476: 72 LIT
  - LLP, funding-rebate and MM-incentive accounts: 0
  - the rest (~36M) sits in user accounts

  **How to tell them apart:** Lighter-owned L2 balances are the system accounts named by `GET /api/v1/systemConfig` (staking pool, LLP, fee collector, funding rebate, MM incentive) plus account 0 (treasury). Each one's LIT is `GET /api/v1/account?by=index&value=<i>` → `accounts[0].assets[symbol=LIT].balance`. Everything else in the bridge belongs to users. The staking pool is a public pool of holders' shares, not a Lighter reserve. Only account 0 (2.02M) and the fee collector are Lighter's. Neither has history (live reads only).

## 3. Proposed method
```yaml
contracts:   # dead, ecosystem_reserve, buyback_wallet already in lit.yaml
circulating_supply:
  source:
    type: adapter
    name: chain.view_sum
    params:
      terms:
        - { contract: token, function: totalSupply }
        - { contract: token, function: balanceOf, args: [ dead ], sign: -1 }
        - { contract: token, function: balanceOf, args: [ ecosystem_reserve ], sign: -1 }
        - { contract: token, function: balanceOf, args: [ buyback_wallet ], sign: -1 }
      locked:            # NEW param: subtract tokens still locked at the run date by a cited schedule
        citation: { url: "https://x.com/Lighter_xyz/status/2005862687331303804", quote: "The team and investors all have a 1-year unlock and 3-year linear vesting after. The breakdown is 26% team, 24% investor." }
        schedules:       # identical to unlocks_next_year's (one source of truth: share the parsed block)
          - { label: team, tokens: 260000000, tranches: { first: 2027-01-29, every_months: 1, count: 36 } }
          - { label: investors, tokens: 240000000, tranches: { first: 2027-01-29, every_months: 1, count: 36 } }
```
- view_sum can't express this today: it only sums views. The minimal addition is an optional `locked` param: locked(t) = Σ tokens × (tranches after the run date / count), which reuses `schedule.ts`'s tranche parser. It must carry the citation onto the row, like the disclosure rung. Alternative: a new `schedule.locked_now` level plus a derived `level_minus`. That's more machinery, so it isn't recommended.
- Locked today = 500M (the first tranche is 2027-01-29). It then falls 13.89M a month to 0 on 2029-12-29: 486.1M on 2027-01-29, 333.3M on 2027-12-29.
- **Optional monitor (recommended, monitor-only):** a `chain.balance_sum`-style read of the 262 allocation wallets (D2 + 261 beneficiaries, list in a data file). It flags any wallet that moves before its tranche and shows post-cliff unlocked-but-held tokens. This would be a new adapter (params: `token`, `holders_file`). It is too many terms for named `contracts:`.

## 4. Exclusion list
| address | label | what | balance now (measured) | citation | moves? |
|---|---|---|---|---|---|
| 0x…dEaD | dead | burns | 18,090,720 | already netted in total_supply | +each quarterly burn |
| 0xe554dcb002e4f3546d67e6deed84323eed989d62 | ecosystem_reserve | undistributed ecosystem 25% (future points seasons, partnerships, staking rewards); burns are drawn from it | 231,809,274 | Lighter, https://x.com/Lighter_xyz/status/2005862687331303804: "The remaining 25% of the ecosystem allocation will be used for future points seasons and, to a lesser degree, partnerships and growth initiatives."; Lighter "Tokenomics Update" 2026-06-30 (https://x.com/Lighter_xyz/status/2072004429717307732): "we will begin using remaining ecosystem tokens to support staking rewards … out of the 250 million LIT remaining"; funded 250M by the minter on 2026-01-07 (measured) | falls with burns and reward funding |
| D2 0xb3058a7f…19e4 + 261 beneficiary EOAs | team/investor allocation | 26% team + 24% investors, 1y lock + 3y vest | 500,000,000 (36.12M + 463.88M) | same post: "26% team, 24% investor"; The Block 2025-12-30: "both subject to a one-year lock and three-year linear vesting schedule"; measured trace §2 | excluded via the schedule (constant 500M until 2027-01-29) |
| 0x1a51016fad47de690d1f48adf2f6407f3cdc160d | buyback_wallet | bought LIT withdrawn from L2, pays staking rewards / goes to Coinbase Prime via the pass-through | 4,987,096 | lit.yaml comment and onboarding note (2026-10-16): "the bought LIT, withdrawn from the L2; funds staking rewards" | yes (14.75M on 2026-08-20 → 4.99M) |

Kept in: the bridge's user and staking-pool LIT (holders'); burn_safe and prime_passthrough (both 0 now; they pass tokens through).

## 5. Reconciliation with CoinGecko (dev-only)
CoinGecko's 250M is the TGE airdrop, never updated. Ours = 250M airdrop − 0.1M + net changes. The reserve's reward payouts and the 0.1M outflow added to circulating, while the buyback wallet's holdings and the L1 burns subtracted. Net residual −4.89M (−1.95%), explained term by term: 1000 − 18.09 dead − 231.81 reserve − 500 locked − 4.99 buyback = 245.11. In other words, CoinGecko is stale, not differently defined. It will be badly wrong from 2027-01-29, when 13.9M a month starts unlocking.

## 6. Check
No live first-party figure: Lighter's API exposes accounts and the staking pool, not a supply or circulating endpoint. **One-off first-party anchor:** Lighter's 2026-06-30 Tokenomics Update says "~15.5 million LIT … representing ~6.3% of the circulating supply", which implies about 246M circulating then. **Measured** at the post's time (block 25,431,883, 2026-06-30 17:08Z): reserve 249.999995M, buyback wallet 0, dead 0, so our method gives **250.0M**, and 15.5/250 = 6.2%. That is consistent with "~6.3%". The ~4M gap fits Lighter netting the bought LIT then still held on L2. Proposed check: none live. Cite this as a dev-time sanity anchor, plus the 262-wallet monitor (§3) as an on-chain consistency check on the locked term.

## 7. History
All on-chain terms are plain views and the schedule depends only on the date, so archive reads work. LIT was minted 2025-10-27 and launched 2025-12-30, so there is no history at 2025-10-13: before TGE, circulating is 0, or undefined while everything sat with the minter. Measured **2026-08-20 00:00Z (block 25,792,601):** total 1,000M − dead 15.639M − reserve 234.261M − buyback 14.749M − locked 500M = **235.351M** (the wallet set held 500.0M at that block, matching the schedule). The L2 treasury balance (if added) has no history.

## 8. Open questions / options for Mike (price $2.88527; base = proposed 245.11M = $707.2M)
| option | circulating | vs proposed | $ effect | rec |
|---|---|---|---|---|
| L0. total − reserve only (allocation counted, "minted and sellable") | 750.10M | +206% | +$1,457M | no: the allocation is contractually locked |
| L1. total − reserve − locked (keep buyback wallet in) | 250.10M | +2.03% | +$14.4M | no: the buyback wallet is undistributed treasury |
| **L2. L1 − buyback wallet (proposed)** | **245.11M** | 0 | 0 | **yes** |
| L3. L2 − L2 treasury account 0 (2.02M, Lighter API) | 243.10M | −0.82% | −$5.8M | no for now: API-only, no history, small. Revisit if it grows |
| L4. AERO precedent: also exclude the staking pool (98.47M) | 146.64M | −40.2% | −$284.1M | **no**: a 3-day unstake lockup (`staking_pool_lockup_period` 259,200,000 ms), not a long lock |
| Post-cliff: wallet balances instead of the schedule | equal now; diverges after 2027-01-29 if holders don't sell | n/a | n/a | schedule (the convention is "cannot be sold today"); wallets as monitor |

Judgement calls: (a) Orion's tranche timing (first 2027-01-29) comes from the Q3 call, applied by proposal #3; Lighter's post only says "1-year unlock". (b) Whether reserve-funded staking rewards should count as circulating once paid: yes, they then sit in holders' L2 accounts and are counted automatically.
