# R3 scoping: LINK and UNI (Ethereum) circulating supply on chain

## Summary

**LINK**
1. Proposed circulating: **766,849,970.42 LINK** (measured, block 26,449,807, 2026-11-19 14:45 UTC).
2. vs CoinGecko (dev-only) 766,849,970.42: **0.000%**. CoinGecko mirrors Chainlink's own API to the wei.
3. vs prod stored 766,849,970.42 (2026-11-19): **0.000%**.
4. Method: `chain.view_sum` = `totalSupply` − `balanceOf` of the **33 wallets Chainlink lists as non-circulating** (chain.link/circulating-supply; 9 hold 233.15M, 24 are drained). Check: Chainlink's first-party `supply.chain.link/supply` `.circulatingSupply`. This needs one small new HTTP adapter.
5. Open: staked v0.2 LINK (42.57M) **in** (recommended); Reserve (6.68M) **in** (recommended, matches the issuer); the Chainlink-run rewards Safe and RewardVault (13.42M) **in**. Excluding all three: −8.1%, −$0.57B.

**UNI**
1. Proposed circulating: **607,453,895.88 UNI** (measured, block ~26,449,750, 2026-11-19 14:33 UTC).
2. vs CoinGecko (dev-only) 607,457,895.88: **−0.0007%** (4,000 UNI of burns between the two reads).
3. vs prod stored 607,485,895.88 (2026-11-19 00:46): **−0.005%** (burn timing).
4. Method: `chain.view_sum` = `totalSupply` − `balanceOf(dead)` − `balanceOf(timelock)` − `balanceOf(uf_grants)` − `balanceOf(aera_incentives)`. Existing adapter. Check: none (Uniswap publishes no first-party circulating figure).
5. Open: treasury **out** (recommended; including it adds +43.2%, +$1.36B). The UF grants wallet and Gauntlet's Aera incentives vault are also **out** (recommended; together −2.6%, $82.7M). CoinGecko only started excluding both on 2026-11-02/03.

Prices used for the $ effects come from prod's `report yield` for 2026-11-18: LINK $9.1003, UNI $5.1672.

---

# LINK

## 1. Today's numbers
| figure | value | note |
|---|---|---|
| On-chain total (`totalSupply`, Orion `total_supply`) | 1,000,000,000 | measured, block 26,449,807 (2026-11-19 14:44:59 UTC); dead holds 110 LINK, not subtracted (link.yaml) |
| CoinGecko circulating (dev-only reference) | 766,849,970.424884 | `coingecko-markets-devonly.json`, 2026-11-19 14:29 |
| Prod stored circulating | 766,849,970.424884 | 2026-11-19 00:45 (CoinGecko); unchanged since 2026-10-16 |
| Chainlink first-party API | 766,849,970.424883961240529443 | `GET https://supply.chain.link/supply` `.circulatingSupply` (wei) |
| **Proposed on-chain** | **766,849,970.424884** | measured: total − Σ 33 listed wallets (233,150,029.575116) |

Proposed vs CoinGecko 0.000%, vs prod 0.000%, vs Chainlink API 0 wei.

## 2. Proposed method
`chain.view_sum` on chain 1 using the existing adapter, with 34 terms: `{contract: token, function: totalSupply}` plus 33 ×
`{contract: token, function: balanceOf, args: [cl_nc_NN], sign: -1}`. validateViewSum puts no limit on the number of
terms, and they all read at the run block.

YAML `contracts:` additions are `cl_nc_01` … `cl_nc_33`, in the order the API returns them (list below). The full list is
needed for two reasons. It reproduces Chainlink's figure exactly, because the drained legacy wallets still hold 29.56 LINK
of dust. And it keeps history correct, because the Safes drained since 2025-10 held the earlier releases. Dropping the 24
drained wallets would overstate circulating by 29.6 LINK today, and by the released amounts at any earlier block.

The check needs one new adapter. Nothing in `src/ingest/adapters/` reads a generic HTTP JSON level; vvv/hype/lit are
asset-specific. Minimal option: `link.supply_api` with params `{ url: "https://supply.chain.link/supply", field:
circulatingSupply, decimals: 18 }`, or a generic `http.json_level { url, path, decimals }` that SKY/others could reuse.
Tolerance: 0.01% (the two should match exactly at the same block; the slack covers API cache lag on release days).

Maintenance: Chainlink rotates releases through new Safes. If it moves LINK into a wallet that is not yet listed, the
view_sum rises while the API does not, so the check breaches. That is the signal to add the address, which the API's
`balances[]` returns. The existing `released_hub`/`release_rewards` flows keep showing the dilution.

## 3. Exclusion list (non-circulating; source: Chainlink)
Citation: https://chain.link/circulating-supply, "Non-Circulating Supply Wallets — Legacy Wallet Addresses / New Wallet
Addresses" (33 addresses). The machine-readable copy is the `balances[]` array at https://supply.chain.link/supply. The page
says: "Token release schedule is currently 7% of the total supply per year." Blockscout labels 0x7594…43e4 "Chainlink:
Noncirculating Supply 3". All balances below are measured at block 26,449,807 and match the API to the wei.

| address | type | LINK now | moves? |
|---|---|---|---|
| 0x9BBb46637A1Df7CADec2AFcA19C2920CdDCc8Db8 | Safe | 30,000,000.0016 | untouched in the 420 days scanned |
| 0x8652Fb672253607c0061677bDCaFb77a324DE081 | Safe | 30,000,000.0016 | untouched |
| 0x76287e0F7b107d1C9f8f01D5aFac314Ea8461a04 | Safe | 30,000,000.0016 | untouched |
| 0x7594Eb0ca0a7f313bEFD59AfE9e95c2201a443e4 | Safe ("Noncirculating Supply 3") | 30,000,000.0016 | untouched |
| 0x5A8e77bC30948cc9A51aE4E042d96e145648BB4C | Safe | 30,000,000.0016 | untouched |
| 0xe0b66bFc7344a80152BfeC954942E2926A6FcA80 | Safe | 29,400,000.0016 | released 0.6M on 2026-10-09 |
| 0x0DFfD343C2D3460a7EAD2797a687304Beb394ce0 | Safe | 28,750,000.0016 | released 1.25M on 2026-10-09 |
| 0x157235A3cc6011d9C26A010875c2550246aAbcCA | Safe | 22,000,000.0016 | untouched |
| 0x5Eab1966D5F61E52C22D0279F06f175e36A7181E | Safe | 3,000,000.0016 | untouched |
| 0x98C63b7B319dFBDF3d811530F2ab9DfE4983Af9D | legacy | 26.9962 | dust |
| 0xe0362f7445e3203a496f6f8b3d51cbb413b69be2 | legacy | 1.6983 | dust |
| 0x75398564ce69B7498dA10a11ab06Fd8fF549001c | legacy | 0.7778 | dust |
| 0x959815462EeC5fFf387A2e8a6871d94323D371de | listed | 0.0778 | dust |
| 0x35a5dc3F…, 0xa42D0A18…, 0x4a87ecE3…, 0xfB682b0d…, 0x9c17f630…, 0x37398A32…, 0x8d34d66b… | drained release Safes | ≤0.002 each | each emptied into the release wallets, 2025-10-10 … 2026-10-09 |
| 0x5560d001…, 0xbe6977e0…, 0xdAD22a85…, 0x276F695b…, 0xb9b012ca…, 0x3264225f…, 0x57Ec4745…, 0xD3219482…, 0x55b0ba19…, 0xD48133C9…, 0xa71bbBd2…, 0xEc640A90…, 0x2a6AB3B0… | listed, empty | 0 | — |
| **Σ** | | **233,150,029.575116** | falls by ≈70M/yr in quarterly steps |

The full checksummed addresses are in the API response; copy them from there into the YAML.

Release history (measured, transfers of ≥1,000 LINK into `release_hub` 0x9b1c…cde9 and `release_rewards` 0xD50f…78Af):
2025-10-10 18.75M, 2025-12-19 11.25M, 2026-04-03 19.0M, 2026-06-19 21.0M, 2026-10-09 18.75M. Each release came from the
listed Safes. The circulating series reproduces them exactly (section 6).

**Not excluded (in Chainlink's circulating, and so CoinGecko's):**
- CommunityStakingPool 0xBc10f2E862ED4502144c7d632a3459F49DFCDB5e: 40,875,543.64 (measured). OperatorStakingPool
  0xa1d76a7ca72128541e9fcacafbda3a92ef94fdc5: 1,698,961.49. Unstakable: "28-day cooldown period … seven-day claim window"
  (https://chain.link/economics/staking).
- Chainlink Reserve 0x9A709B7B69EA42D5eeb1ceBC48674C69E1569eC6 (RBACTimelock): 6,675,852.54, growing weekly. "We do not
  expect any withdrawals from the Reserve for multiple years" (https://blog.chain.link/chainlink-reserve-strategic-link-reserve).
- RewardVault 0x996913c8c08472f584ab8834e925b06D0eb1D813 (staking rewards, not yet earned): 3,102,097.43.
- `release_rewards` Safe 0xD50f074Ec5c7997cE1DaacB513Ec194C480878Af (Chainlink-run, drips ≈0.5M/week): 10,322,499.00.
- `release_hub` 0x9b1c…cde9: 0 (it forwards to Binance within hours).

## 4. Reconciliation with CoinGecko (dev-only)
CoinGecko's figure equals Chainlink's API exactly, so CoinGecko simply republishes the issuer's number. Residual: 0.
CoinGecko's step changes are Chainlink's quarterly releases.

## 5. Check
`GET https://supply.chain.link/supply` → `.circulatingSupply` (wei string, 18 dp). Value now:
766849970424883961240529443 = 766,849,970.42 LINK. The response also returns `totalSupply` and the 33 per-wallet
`balances`. This is a first-party check (Chainlink), not CoinGecko.

## 6. History
Every term is a plain view, so the method can be read at any archive block back to 2025-10-13 (measured):
| date (00:00 UTC) | block | proposed circulating |
|---|---|---|
| 2025-10-13 | 23,565,081 | 696,849,970.45 |
| 2026-03-01 | 24,558,868 | 708,099,970.45 |
| **2026-08-20** | **25,792,602** | **748,099,970.42** |
| 2026-10-16 | 26,201,365 | 766,849,970.42 (= prod's first stored CoinGecko value) |

The steps match the releases above (+11.25M Dec, +19M Apr, +21M Jun, +18.75M Oct). The API has no history; the check is
live only.

## 7. Open questions / options for Mike
Base market cap: 766.85M × $9.1003 = **$6.979B**.
1. **Staked v0.2 LINK (42.57M): circulating?** Recommendation: **in**. It can be unstaked after 28+7 days, and Chainlink and
   CoinGecko both count it. AERO's veAERO precedent covers multi-year locks that cannot be undone; a 4-week cooldown is not
   comparable, so the precedent should not extend to it. Option out: −5.55%, −$387M.
2. **Chainlink Reserve (6.68M): circulating?** Recommendation: **in**, consistent with Mike's 2026-10-16 decision not to
   treat the hold as removed. That also keeps the first-party check exact. Arguments for out: the Reserve is
   timelocked and the issuer expects no withdrawals "for multiple years", which fits the "protocol reserve not distributed"
   rule. Option out: −0.87%, −$60.8M, and the check becomes API − `balanceOf(reserve)`.
3. **Chainlink-run reward balances (`release_rewards` Safe 10.32M + RewardVault 3.10M = 13.42M):** both are already released
   by Chainlink's definition but not yet in holders' hands. Recommendation: **in** (issuer parity). Option out: −1.75%,
   −$122M.
4. All three out together: 704.18M, −8.17%, −$570M.

---

# UNI

## 1. Today's numbers
| figure | value | note |
|---|---|---|
| On-chain total (Orion `total_supply` = 1e9 − dead) | 885,714,418.79 | measured ~block 26,449,750 (2026-11-19 14:33 UTC); dead 114,285,581.21 |
| CoinGecko circulating (dev-only reference) | 607,457,895.88 | 2026-11-19 14:29; CoinGecko total 885,718,418.79 (4,000 fewer burned) |
| Prod stored circulating | 607,485,895.88 | 2026-11-19 00:46 (CoinGecko) |
| **Proposed on-chain** | **607,453,895.88** | total − Timelock − UF grants wallet − Aera incentives vault |

Proposed vs CoinGecko −0.0007%, vs prod −0.005%; both gaps are burn timing (≈30–40k UNI a day reach dead).

## 2. Proposed method
`chain.view_sum` on chain 1 using the existing adapter:
```yaml
contracts:
  uf_grants: "0x5069A64BC6616dEC1584eE0500B7813A9B680F7E"       # Uniswap Foundation budget wallet (Prop 83, 20.32M UNI)
  aera_incentives: "0x7c8406384f7a5c147a6ADd16407803BE146147E4" # AeraVaultV2 "Uniswap Incentives", owner = Timelock
circulating_supply:
  source: { type: adapter, name: chain.view_sum, params: { terms: [
    { contract: token, function: totalSupply },
    { contract: token, function: balanceOf, args: [ dead ], sign: -1 },
    { contract: token, function: balanceOf, args: [ timelock ], sign: -1 },
    { contract: token, function: balanceOf, args: [ uf_grants ], sign: -1 },
    { contract: token, function: balanceOf, args: [ aera_incentives ], sign: -1 } ] } }
```
`dead` and `timelock` are already in uni.yaml. No new adapter is needed. `total_supply` stays as it is (Timelock inside,
per Mike 2026-10-11).

## 3. Exclusion list (measured ~block 26,449,750)
| address | label | UNI now | citation | moves? |
|---|---|---|---|---|
| 0x…dEaD | burn | 114,285,581.21 | Blockscout "Null: 0x00...dEaD / Burn"; already netted in `total_supply` | rises daily (Firepit burns) |
| 0x1a9C8182C09F50C8318d769245beA52c32BE35BC | DAO Timelock (treasury) | 262,247,996.31 | Blockscout "Uniswap V2: UNI Timelock"; uni.yaml | falls by 5M a quarter (UNIVesting to Labs; 20M allowance left, last pull 2026-10-01) and by governance spends |
| 0x5069A64BC6616dEC1584eE0500B7813A9B680F7E | Uniswap Foundation grants/ops wallet (EOA) | 13,314,112.21 | Proposal 83 "Uniswap Unleashed": `transfer(0x5069…f7e, 20,320,405 UNI)`, "$95.4M into the UF grants budget, and $25.1M to fund operations, for the next 2 years" (https://www.tally.xyz/gov/uniswap/proposal/83) | falls as UF pays grants (it sent 3.25M on 2026-11-04/05 and took 1.75M back on 11-06) |
| 0x7c8406384f7a5c147a6ADd16407803BE146147E4 | AeraVaultV2 "Uniswap Incentives" | 2,698,414.40 | `owner()` = Timelock (measured); Proposal 82 "Unichain and Uniswap v4 Liquidity Incentives" (`acceptOwnership`, `approve(0x7c84…, 7,588,532 UNI)`); app.aera.finance lists "Uniswap Incentives 0x7c84...47e4" | falls as Gauntlet pays incentives |

**Not excluded:**
- UNIVesting 0xca046a83edb78f74ae338bb5a291bf6fdac9e1d2: holds 0. It pulls from the Timelock with `transferFrom`, so the
  unvested 20M allowance is already inside the Timelock term.
- Its recipient 0xaba63748c4b4def4a3319c3a29fe4829029d926f (Uniswap Labs): 0 now (it held 14.0M on 2026-08-20). Vested UNI
  is Labs' to spend, so it counts as circulating, as CoinGecko also treats it.
- Original 2020 four-year team/investor vesting: fully vested by Sept 2024 (claimed). It was not held in a public vesting
  contract that I could identify, and CoinGecko excludes nothing for it. Treat it as circulating.
- UNIfication contracts (TokenJar/Firepit, uni spec §1): they hold fee tokens, not UNI, and burns go straight to dead.
  Nothing to subtract.

## 4. Reconciliation with CoinGecko (dev-only)
CoinGecko's daily series (prod `circ_daily_90d`) works out as follows:
- **Until 2026-11-01**, CoinGecko = total − Timelock. Prod 10-16: 624,800,422 vs our total − TL 624,822,422; 11-01:
  624,114,422 vs 624,126,422. Gaps of 12–22k are burn timing.
- **2026-11-02**: −2.71M, which is CoinGecko starting to exclude the Aera vault (2.698M).
- **2026-11-03**: −14.85M, which is CoinGecko starting to exclude the UF wallet (14.81M then). No ≥0.5M transfers on those
  days explain the moves, so they are methodology changes.
- Confirmation: the UF wallet's 3.25M outflow on 11-04/05 shows as +3.24M in CoinGecko on 11-05, and its 1.75M inflow on
  11-06 shows as −1.75M on 11-07. CoinGecko tracks the wallet's live balance.

Today's residual is 4,000 UNI (burn timing). CoinGecko's full exclusion set is therefore {dead, Timelock, UF wallet, Aera
vault}, which is identical to this proposal.

## 5. Check
**None.** Uniswap Labs/Foundation publish no circulating-supply endpoint (none found). CoinGecko/DefiLlama may not be a
check. The Timelock's balance is already a `treasury_uni` monitor, and the UF and Aera balances could be added as
monitor-only levels for display.

## 6. History
All terms are plain views, so the method can be read at an archive block back to 2025-10-13 (measured):
| date (00:00 UTC) | block | total | Timelock | UF | Aera | proposed circulating |
|---|---|---|---|---|---|---|
| 2025-10-13 | 23,565,081 | 999,950,423 | 369,669,472 | 14,880,125 | 2,963,798 | 612,437,029 |
| 2026-03-01 | 24,558,868 | 898,526,420 | 264,634,857 | 14,880,125 | 2,666,144 | 616,345,294 |
| **2026-08-20** | **25,792,602** | **891,020,420** | **267,247,996** | **14,837,405** | **2,698,414** | **606,236,604** |
| 2026-10-16 | 26,201,365 | 887,070,419 | 262,247,996 | 14,825,810 | 2,698,414 | 607,298,198 |

Caveat: before 2026-11-02 prod's stored CoinGecko series sat ≈17.5M higher, because CoinGecko excluded only the Timelock
then. Backfilling with the new method lowers past market caps by about 2.8%. The method is consistent and the old
CoinGecko series was not. 2025-10-13 predates the 100M Timelock burn (2025-12-27), which leaves circulating unchanged.

## 7. Open questions / options for Mike
Base market cap: 607.45M × $5.1672 = **$3.139B**.
1. **Timelock treasury: in or out of circulating?** Recommendation: **out**. It is undistributed treasury that only
   governance can spend, CoinGecko excludes it, and Orion's convention excludes "protocol treasury … not distributed".
   That leaves `total_supply` (FDV) with it inside, as decided on 2026-10-11. Option in: 869.70M, +43.2%, +$1.355B.
2. **UF grants wallet (13.31M) and Aera incentives vault (2.70M):** Recommendation: **out**. Both are governance-granted
   budgets waiting to be distributed, CoinGecko has excluded them since 11-02/03, and the Aera vault is owned by the
   Timelock. Option in: +2.64%, +$82.7M (UF +$68.8M, Aera +$13.9M). Risk: UF is an EOA, and if it moves the budget to a new
   wallet the view_sum will over-count it with no check to catch it. Mitigation: a monitor-only level on `uf_grants`, so
   an unexpected drop to ~0 is visible.
3. **Labs vest:** unchanged. It stays report-only dilution, and its pending 20M sits inside the Timelock term.
4. Staking precedent: UNI has no staking, so there is nothing to decide.

---
Measurement notes: reads used `ORION_ETH_RPC_URL` (archive, batched `eth_call`), Blockscout holders for discovery, and one
read each of `supply.chain.link/supply` and `chain.link/circulating-supply`. No CoinGecko call was made beyond the provided
file. Scratch: `$TMPDIR/lu_common.py`, `cl_supply.json`, `uni_big.json`.
