# R3 scoping: CRV + liquid-locker wrappers (cvxCRV, sdCRV, yCRV)

## Summary (5 lines per asset)

**CRV**
1. Proposed circulating: **1,582,336,065 CRV** (measured, block 26,449,750, 2026-11-19 14:33:11Z).
2. vs CoinGecko (dev-only) 1,588,037,101: **-0.36%**. CoinGecko is Curve's own on-chain figure (`circulating_supply()` on 0x14139EB6…, 1,588,067,884), within 0.002%.
3. vs prod stored 1,587,843,720 (2026-11-19 00:45Z): **-0.35%** (-$1.10M at $0.19990).
4. Method: `chain.view_sum` (no new adapter): `totalSupply − balanceOf(ve, community_fund, vest_prelp, token, minter)`, which copies Curve's contract term for term, then `− balanceOf(curve_treasury)`. Check: Curve's `circulating_supply()`.
5. Open decisions: veCRV stays out (recommended; counting it adds +53%, +$168M); Curve Treasury out (recommended, -0.36%); unvested grant escrows (-0.28%, recommend leaving them in).

**cvxCRV**
1. Proposed circulating: **420,775,187** (total 425,637,222 − 4,862,035 stkcvxCRV held by Convex's TreasuryFunds).
2. vs CoinGecko: n/a (CoinGecko reports 0; its total_supply 425,637,222 matches the chain).
3. vs prod stored 425,636,521 (= totalSupply): **-1.14%** (-$395K at $0.08128).
4. Method: `chain.view_sum`: `token.totalSupply − wrapper.balanceOf(convex_treasury)` (plain views, existing adapter).
5. Open decision: exclude the treasury's 1.14% (recommended; it is just over the 1% bar and hasn't moved since at least 2025-10-13) or keep total-as-circulating.

**sdCRV**
1. Proposed circulating: **117,441,415** (total 119,049,987 − 1,608,572 sdCRV-gauge held by Stake DAO Governance/Treasury 0xF930…).
2. vs CoinGecko: n/a (CoinGecko reports 0; its total_supply of 22,975,526 is stale or wrong, the chain has 119.05M).
3. vs prod stored 119,049,987: **-1.35%** (-$172K at $0.10707).
4. Method: `chain.view_sum`: `token.totalSupply − gauge.balanceOf(sd_governance)` (plain views, existing adapter).
5. Open decision: exclude the Stake DAO treasury's 1.35% (recommended) or keep as is.

**yCRV**
1. Proposed circulating: **69,552,313** (total 71,963,003 − 2,410,690 yCRV in st-yCRV held by Yearn's two treasuries). Yearn's protocol-owned liquidity (3.11M yCRV, 4.32%) is left in.
2. vs CoinGecko: n/a (CoinGecko reports 0; its total_supply of 3,709,597 is stale or wrong).
3. vs prod stored 71,963,003: **-3.35%** (-$256K at $0.10609); excluding the POL as well: -7.67% (-$586K).
4. Method: view_sum can't do it today. st-yCRV shares have to be multiplied by `pricePerShare()` (2.68 now), so it needs a small `chain.view_sum` extension: a term-level `times: { contract, function, decimals }`.
5. Open decisions: (a) build `times` and exclude the treasury st-yCRV (recommended), or keep as is; (b) POL in or out (recommend in).

---

All figures are **measured** at Ethereum block **26,449,750 (2026-11-19 14:33:11Z)** unless marked otherwise. Prices are prod `report-<asset>.json` `.price` (CRV 0.199896, cvxCRV 0.081282, sdCRV 0.107070, yCRV 0.106090). CoinGecko figures are a **dev-only reference** (`prod/coingecko-markets-devonly.json`, last_updated 2026-11-19T14:29:56Z). Probes: `$TMPDIR/crv*.py`, `$TMPDIR/w*.py` (raw JSON-RPC eth_call, Blockscout v2 for holder lists).

---

# CRV

## 1. Today's numbers
| figure | value | vs proposed |
|---|---|---|
| on-chain total (`CRV.totalSupply()`, Orion `total_supply`) | 2,435,541,062.87 | — |
| Curve first-party `circulating_supply()` (0x14139EB6…) | 1,588,067,883.59 | +0.36% |
| CoinGecko circulating (dev-only) | 1,588,037,101 | +0.36% |
| prod stored circulating (2026-11-19T00:45Z, CoinGecko) | 1,587,843,720 | +0.35% |
| **proposed** (Curve's terms − Curve Treasury) | **1,582,336,064.59** | — |

Curve's figure vs CoinGecko: +0.002%. Curve's figure vs prod: +0.014% (prod read 14 h earlier, while emissions run at about 0.33M/day).

## 2. Proposed method (existing `chain.view_sum`, no new adapter)
Add these to `contracts:` (`token`, `ve`, and `curve_treasury` already exist):
```yaml
  circ_contract: "0x14139EB676342b6bC8E41E0d419969f23A49881e" # Curve's CRV Circulating Supply contract (the check)
  community_fund: "0xe3997288987E6297Ad550A69B31439504F513267" # Community Fund (VestingEscrowFactory), unallocated reserve
  vest_prelp: "0x575CCD8e2D300e2377B43478339E364000318E2c" # VestingEscrow: pre-CRV LPs (vest ended 2021-08-13)
  minter: "0xd061D61a4d941c39E5453435B6345Dc261C2fcE0" # Minter (dust)
```
```yaml
  circulating_supply:
    source:
      type: adapter
      name: chain.view_sum
      params:
        terms:
          - { contract: token, function: totalSupply }
          - { contract: token, function: balanceOf, args: [ ve ], sign: -1 }            # 841,816,658.49
          - { contract: token, function: balanceOf, args: [ community_fund ], sign: -1 } # 845,144.19
          - { contract: token, function: balanceOf, args: [ vest_prelp ], sign: -1 }    # 4,731,148.57
          - { contract: token, function: balanceOf, args: [ token ], sign: -1 }         # 78,040.05 (CRV sent to the token: stuck)
          - { contract: token, function: balanceOf, args: [ minter ], sign: -1 }        # 2,187.98
          - { contract: token, function: balanceOf, args: [ curve_treasury ], sign: -1 } # 5,731,819.00
```
- The first six terms reproduce Curve's `circulating_supply()` exactly: measured diff 0.00 CRV at three blocks (now, 2026-08-20, 2025-10-13).
- The use `CRV.balanceOf(ve)` rather than `ve.supply()` to match Curve. The two differ by 2,066 CRV (CRV sent straight to the escrow, never locked).
- Curve's contract also lists 12 more cached addresses (team, investor and employee VestingEscrows, `0x2b6509…`, `0xa44552…`, `0x81930D…`, `0x629347…`, `0x967E92…`, `0xf049ae…`, `0x730E9a…`). All are **0.00 CRV** at all three blocks, so they are left out. Adding them would only cost reads.

## 3. Exclusion list
| label | address | what it is | balance now (measured) | citation | moves? |
|---|---|---|---|---|---|
| veCRV (VotingEscrow) | 0x5f3b5DfE…e2A2 | CRV locked by holders for up to 4 years | 841,816,658 (34.6% of total) | Curve circ contract: `# veCRV`. docs.curve.finance deployed contracts: "Voting Escrow 0x5f3b5…" | yes: locks and unlocks (850.8M on 2026-08-20, 865.2M on 2025-10-13) |
| Community Fund | 0xe3997288…3267 | DAO reserve; grants leave only via ≥1-year VestingEscrowSimple | 845,144 | docs.curve.finance/user/dao/community-fund-treasury: "Community Fund is deployed on Ethereum at 0xe399…". Curve circ contract: `# community fund` | yes, on DAO grants (24.55M on 2025-10-13) |
| pre-CRV LP VestingEscrow | 0x575CCD8e…8E2c | Early-user allocation. Fully vested 2021-08-13 (`end_time` 1628893048, `lockedSupply()` = 0), so this is vested but unclaimed | 4,731,149 | Curve docs table: "pre-CRV Liquidity Providers 0x575c…". Curve circ contract: `# LPs` | yes, falling as it is claimed (11.28M → 10.30M → 4.73M) |
| CRV token contract | 0xD533a949…cd52 | CRV sent to the token address; it can't be recovered | 78,040 | Curve circ contract: `# crv token` | slowly up |
| Minter | 0xd061D61a…fcE0 | dust | 2,188 | Curve circ contract: `# token minter` | no |
| **Curve Treasury** (not in Curve's contract) | 0x6508ef65…290b | DAO treasury (FeeAllocator's 10%). It got 6.3M CRV from the Grant Council multisig around block 25.895M (Sept 2026) and sent out 568K | 5,731,819 | docs.curve.finance/developer/deployments: "Ethereum, Core, treasury, 0x6508ef65…". Already `curve_treasury` in crv.yaml | yes: 0 on 2026-08-20 |

Considered, **not** excluded (options in §7):
- Community-fund grant escrows (VestingEscrowSimple proxies, admin = DAO Agent 0x4090…). Measured `lockedSupply()` (unvested):
  - 0xd347ce96…: 1,914,487 (17.45M grant, 2025-12-29 to 2026-12-29)
  - 0xa94bec73…: 1,553,607 (3.75M, 2026-04-19 to 2027-04-19)
  - 0x9f8a1a29…: 906,806 (2.5M, 2026-04-01 to 2027-04-01)
  - Total **4,374,900 (0.28%)**. Nine other grant escrows hold 0.
- Curve Grant Council multisig 0xc420c9d5… (Etherscan label "Curve: Grant Council Multisig"): 1,468,902 CRV (12.05M on 2025-10-13). It is an active grant-spending wallet. 0.09%.

## 4. Reconciliation with CoinGecko (dev-only)
CoinGecko 1,588,037,101 equals Curve's `circulating_supply()` 1,588,067,884 to 0.002%. That gap is about 2 hours of emissions, since CoinGecko updated at 14:29:56Z and the block is 14:33:11Z. So **CoinGecko = total − veCRV − vesting/reserve leftovers**: it excludes veCRV and does not exclude the Curve Treasury. Proposed vs CoinGecko is -5,700,000, which is the treasury term. There is no unexplained residual.

## 5. Check
First-party: `circ_contract.circulating_supply()` (0x14139EB676342b6bC8E41E0d419969f23A49881e). Value now 1,588,067,883.59. Curve's FAQ (resources.curve.finance/crv-token/faq) lists it: "The on-chain contract (0x14139EB6…) which shows the circulating supply, net of locked or otherwise vested tokens."
- Our value should equal it minus `balanceOf(curve_treasury)`. Proposed check: `contract_read circ_contract circulating_supply` with tolerance about 1.5%, wide enough to absorb treasury moves.
- Caveat (from reading the source): `add_contract` writes to `contracts[num_contracts]` with `num_contracts` starting at 18, but the sum loop starts at `contracts[0]` and stops at the first empty slot. Any contract Curve adds is therefore never counted, so the list is frozen at the 18 cached addresses. Measured: `num_contracts` = 18, `contracts(0)` = `contracts(18)` = 0x0, so nothing has been added.

## 6. History
All terms are plain views, so the method can be read at any archive block back past 2025-10-13. Samples:
- **2026-08-20, block 25,792,602** (00:00:11Z): total 2,411,296,472; Curve circ 1,549,264,696; mirror terms 1,549,264,696 (diff 0.00); treasury 0. **Proposed 1,549,264,696.**
- 2025-10-13, block 23,565,081: total 2,312,989,934; Curve circ 1,411,923,391; mirror 1,411,923,391 (diff 0.00); treasury 0. Proposed 1,411,923,391.
- The grant escrows did not exist before Dec 2025, so `lockedSupply()` terms on them would fail on a backfill through `readAt`. That is one more reason to leave them out.

## 7. Open questions / options for Mike (price $0.199896; prod mcap 1,587,843,720 → $317.40M)
| option | circulating | vs prod | mcap | Δ$ |
|---|---|---|---|---|
| A. Copy Curve's contract (veCRV out, treasury in) | 1,588,067,884 | +0.01% | $317.45M | +$0.04M |
| **B. A − Curve Treasury (recommended)** | 1,582,336,065 | -0.35% | $316.30M | -$1.10M |
| C. B − unvested grant escrows | 1,577,961,165 | -0.62% | $315.43M | -$1.98M |
| D. C − Grant Council multisig | 1,576,492,263 | -0.71% | $315.13M | -$2.27M |
| E. veCRV counted as circulating (A + veCRV) | 2,429,884,542 | +53.0% | $485.72M | +$168.3M |

- **veCRV: keep it out (extend the AERO precedent).**
  - veCRV locks can't be sold, last up to 4 years, and the lockers relock permanently.
  - Curve's first-party figure and CoinGecko both exclude it.
  - About 616M of the 842M veCRV is re-issued as cvxCRV, sdCRV and yCRV, which Orion prices as separate assets. Counting veCRV as circulating CRV would count that market value twice.
- **Treasury: out (B)**, per the convention ("protocol treasury … not distributed"). It is one named contract already in the YAML, and it makes Orion's figure slightly stricter than Curve's.
- **Grant escrows: leave them in (B, not C).**
  - They total 0.28%, shrink to 0 by Apr 2027, and the set of addresses changes with each grant.
  - Before they were deployed (Dec 2025) a `lockedSupply()` read fails, which breaks a backfill.
  - The Community Fund that feeds them is almost empty (845K), so few new ones can appear.
- **vest_prelp (4.73M, vested but unclaimed):** Curve excludes it, so we do too, to stay equal to the check. Strictly it is claimable. Counting it as circulating would add +0.30%.

---

# Wrappers: shared notes
The prod stored circulating figure for each wrapper is its ERC-20 `totalSupply()` (`contract_state`, `subtract_balances: {}`). CoinGecko reports 0 circulating for all three. I measured Blockscout's top 25 holders of each token and then looked through the containers: stkcvxCRV, the BaseRewardPool, the sdCRV gauge, YBS, st-yCRV, the Curve LP tokens and their gauges, and lp-yCRV v2. Treasuries checked in every container: Convex TreasuryFunds 0x1389…, Convex multisig 0xa3c5…, Stake DAO Governance 0xF930… and TreasuryRecipient 0x9ebb…, Stake DAO LiquidityFeeRecipient 0x576d…, Yearn ychad 0xFEB4…, Yearn Treasury Vault 0x93A6… and SimpleTreasuryVault 0x044f….
- None of the protocol treasuries holds the bare wrapper token: all are 0 except ychad's 831 cvxCRV.
- What they do hold sits inside staking containers, as listed per asset below.
- The lockers' own LP gauge positions (Convex VoterProxy and the Stake DAO/Yearn voters holding cvxCRV/CRV and sdCRV/CRV gauge LP) belong to their depositors. I didn't trace them further.

# cvxCRV

## 1. Today's numbers
- On-chain total: 425,637,221.86.
- CoinGecko (dev-only): circulating 0; total_supply 425,637,222 (matches the chain).
- Prod stored: 425,636,520.78 (2026-11-19 00:45Z).
- **Proposed: 420,775,187**, which is -1.142% vs prod.

## 2. Method
Existing `chain.view_sum`. The `wrapper` and `convex_treasury` contracts are already in cvxcrv.yaml.
```yaml
terms:
  - { contract: token, function: totalSupply }
  - { contract: wrapper, function: balanceOf, args: [ convex_treasury ], sign: -1 }  # stkcvxCRV, 1:1 cvxCRV
```

## 3. Exclusions / top holders
- **Convex TreasuryFunds** 0x1389388d…bb7: **4,862,035 stkcvxCRV (1.142%)**.
  - Citation: Booster `treasury()` returns 0x1389388d01708118b497f59521f6943be2541bb7 (measured); cvxcrv.yaml labels it "TreasuryFunds: the Booster's platformFee".
  - Unchanged at 2025-10-13, 2026-08-20 and now: it doesn't move.
- Kept as circulating (each under 1%, or a user product):
  - ConvexRewardPool 357.3M (83.95%, the stake container) and cvxCRV/CRV pool 58.5M (13.75%, the Curve LP, 99.8% in its gauge, held by the lockers for depositors).
  - stkcvxCRV top holders are EOAs plus stkCvxCrvStrategy (13.4M, a user vault).
  - CvxLockerV2 219K (vlCVX rewards waiting to be paid, 0.05%).

## 4. Reconciliation
No CoinGecko circulating figure. CoinGecko's total matches.

## 5. Check
None. Convex publishes no cvxCRV circulating figure, and CoinGecko is 0.

## 6. History
Plain views. **2026-08-20, block 25,792,602:** total 423,563,824, treasury 4,862,035, so proposed **418,701,789**. On 2025-10-13: 420,925,202 − 4,862,035.

## 7. Options (price $0.081282; mcap at total $34.60M)
- **Exclude the treasury (recommended):** -1.14%, -$395K.
- Keep as is: 0.

It is only just material, but it costs one plain view term on contracts already in the YAML.

# sdCRV

## 1. Today's numbers
- On-chain total: 119,049,986.63.
- CoinGecko (dev-only): circulating 0; total_supply 22,975,526 (stale or wrong).
- Prod stored: 119,049,986.63.
- **Proposed: 117,441,415**, which is -1.351% vs prod.

## 2. Method
Existing `chain.view_sum`. Add `sd_governance: "0xF930EBBd05eF8b25B1797b9b2109DDC9B0d43063"`; `gauge` already exists.
```yaml
terms:
  - { contract: token, function: totalSupply }
  - { contract: gauge, function: balanceOf, args: [ sd_governance ], sign: -1 }  # sdCRV-gauge, 1:1 sdCRV
```

## 3. Exclusions / top holders
- **Stake DAO Governance / Treasury Safe** 0xF930…3063: **1,608,572 sdCRV-gauge (1.351%)**.
  - Citation: docs.stakedao.org/treasury: "The Stake DAO treasury holds protocol-owned assets … Ethereum `0xf930ebbd05ef8b25b1797b9b2109ddc9b0d43063`". Etherscan label "Stake DAO: Governance".
  - It moves rarely: 1,000,001 on 2025-10-13, 1,608,572 on 2026-08-20 and now.
- Kept:
  - The gauge (89.8%, the stake container) and the sdCRV/CRV pool (5.93%, its LP in Curve and Stake DAO gauges held by lockers for depositors).
  - Gauge top holders: EOA 0x5243 18%, proxy 0x1c0D 16%, several Safes 3–12%. None is listed as Stake DAO's treasury, but I didn't attribute them, which leaves a small residual risk.
  - MultiMerkleStash 110K (claims waiting to be paid, 0.09%).

## 4–5. Reconciliation / check
No CoinGecko circulating figure. Check: none (no first-party figure).

## 6. History
Plain views. **2026-08-20, block 25,792,602:** total 119,049,916 − 1,608,572 = **117,441,344**.

## 7. Options (price $0.107070; mcap $12.75M)
- **Exclude (recommended):** -1.35%, -$172K.
- Keep as is: 0.

# yCRV

## 1. Today's numbers
- On-chain total: 71,963,003.43.
- CoinGecko (dev-only): circulating 0; total_supply 3,709,597 (stale or wrong).
- Prod stored: 71,963,003.43.
- **Proposed: 69,552,313**, which is -3.350% vs prod.

## 2. Method
Not expressible in today's `chain.view_sum`, because the treasury holds st-yCRV shares (yVault 0.4.3, which has no `convertToAssets`). The term has to be `balanceOf × pricePerShare / 1e18`.
- **Minimal extension:** add an optional term-level `times: { contract, function, decimals }` to `validateViewSum` and `viewSum`. The same block's read multiplies the term.
- Add `yearn_treasury_vault: "0x93A62dA5a14C80f265DAbC077fCEE437B1a0Efde"`. `st_ycrv` and `yearn_treasury` (SimpleTreasuryVault 0x044f…) already exist.
```yaml
terms:
  - { contract: token, function: totalSupply }
  - { contract: st_ycrv, function: balanceOf, args: [ yearn_treasury_vault ], times: { contract: st_ycrv, function: pricePerShare, decimals: 18 }, sign: -1 }
  - { contract: st_ycrv, function: balanceOf, args: [ yearn_treasury ], times: { contract: st_ycrv, function: pricePerShare, decimals: 18 }, sign: -1 }
```

## 3. Exclusions / top holders (st-yCRV `pricePerShare` = 2.679887)
- **Yearn Treasury Vault** 0x93A6…Efde (treasury.ychad.eth): **624,209 st-yCRV = 1,672,810 yCRV (2.32%)**.
  - Citation: docs.yearn.fi/developers/addresses/core-contracts: "Treasury | treasury.ychad.eth | 0x93A62dA5…". Etherscan label "Yearn: Treasury Vault".
  - Shares: 593,709 on 2025-10-13, 624,209 since 2026-08-20. The yCRV value grows with pps.
- **Yearn SimpleTreasuryVault** 0x044f…defc: **275,340 st-yCRV = 737,880 yCRV (1.03%)**.
  - Citation: ycrv.yaml (`yearn_treasury`: receives the splitter's 20% and the Receiver's 10%) and the YCrvRevenueSwapper note.
  - It moves: 0 on 2025-10-13, 318,764 on 2026-08-20, 275,340 now. The swapper sells these fee shares.
- **Not excluded (POL, an option):** the Treasury Vault holds 1,635,663 lp-yCRV v2 (0x6E94…, pps 1.7743). That is 38.6% of the yCRV/CRV pool's LP, or **2,999,737 yCRV + 157,415 CRV**. SimpleTreasuryVault holds 59,512 lp-yCRV v2 shares, about 109K yCRV. POL total **3,108,878 yCRV (4.32%)**.
- Kept:
  - YBS 63.1M (87.7%, the stake container; st-yCRV's yCRV sits here through its strategy).
  - yCRV pool 7.78M (10.8%).
  - EOAs at 0.26% or less.
  - Deprecated pool 0x453D 46.8K.

## 4–5. Reconciliation / check
No CoinGecko circulating figure. Check: none.

## 6. History
Plain views (pps is a view), so archive reads work once `times` exists. **2026-08-20, block 25,792,602:** total 71,831,624; treasury shares (624,209 + 318,764) × pps 2.583989 = 2,436,632, so proposed **69,394,992**.

## 7. Options (price $0.106090; mcap $7.63M)
| option | circulating | vs prod | Δ$ |
|---|---|---|---|
| keep as is | 71,963,003 | 0 | 0 |
| **treasury st-yCRV out (recommended; needs `times`)** | 69,552,313 | -3.35% | -$256K |
| + treasury POL out (needs pool-share math: shares × pps / LP supply × pool yCRV balance; a bigger extension) | 66,443,436 | -7.67% | -$586K |

- Recommend keeping POL in. It is working market liquidity, and no other Orion asset subtracts POL.
- If the `times` extension isn't wanted in R3, keeping as is is defensible. It overstates yCRV market cap by 3.35%.
