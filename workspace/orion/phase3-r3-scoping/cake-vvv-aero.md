# R3 scoping: CAKE (BNB), VVV (Base), AERO (Base, measure-only)

Measured 2026-11-19 ~14:40Z over our RPCs (BNB block 134,520,638 at 14:38:27Z; Base block 59,544,605 at 14:41:36Z for
VVV, 59,544,968 at 14:42:49Z for AERO). CoinGecko figures are **dev-only reference** (`prod/coingecko-markets-devonly.json`,
fetched 14:30Z). Prices for $ effects: prod latest_levels 14:15Z (CAKE $1.61587, VVV $23.0876, AERO $0.433834).
Scratch probes: `$TMPDIR/r3/` (rpc.py, cake_samples.json, vvv_now.json, aero_now.json, burnstats.json, vvv_holders.json).

## Summary (5 lines per asset)

**CAKE**
1. Proposed circulating **315,730,969** = Orion total 334,248,327 − legacy CAKE pool balance 13,373,184 − veCAKE balance 5,144,174 (measured).
2. vs CoinGecko (dev-only) 332,221,883: **−4.96%**; but CoinGecko counts the ~15.4M minted-not-yet-burned CAKE in MasterChef v2/burner (its harvest spikes, up to 377M on 11-10); ex that transit CoinGecko is 316,791,813 and we are **−0.33%**.
3. vs prod stored 332,221,883 (latest_levels 14:15Z, CoinGecko): **−4.96%** ($536.8M → $510.2M mcap).
4. Method: `chain.view_sum`, existing adapter, 6 plain `balanceOf`/`totalSupply` terms; archive-readable (2026-08-20: 319,758,328).
5. Open decision: legacy pool + veCAKE out (rec., B), or only total (A, +5.9% vs B), or also MasterChef v1's 7.25M dormant stakes (C, −2.3% vs B). No first-party circulating check exists.

**VVV**
1. Proposed circulating **49,295,213** = total 81,267,051 (totalSupply − zero) − 3 Venice Safes (20,710,447 + 8,709,008 + 1,582,470) − Sablier LockupLinear 969,913.
2. vs CoinGecko (dev-only) 49,031,992: **+0.54%** (CoinGecko also nets a second Sablier contract, 262,818 VVV: with it the match is 0.00%).
3. vs prod stored 49,031,992 (latest_levels 14:15Z; circ_latest 00:46Z 49,028,841): **+0.54%** ($1,132.0M → $1,138.1M).
4. Method: `chain.view_sum` (existing adapter) reproduces Venice's `vvv_stats.circulatingSupplyCryptoBaseUnit` **exactly** (49,295,213.30 vs 49,295,213.30 at the same minute); keep Venice's figure as the http_json check at 0.5%.
5. Open decision: option (a) view_sum primary + Venice check (recommended) vs (b) Venice primary; staked sVVV stays circulating (7-day cooldown), recommend not extending the veAERO precedent.

**AERO (measure-only)**
1. On-chain circulating today **777,905,250** (total 2,145,974,541 − sAERO 1,079,094,329 − aero_migration 278,263,599 − velo_migration 10,711,363).
2. vs CoinGecko (dev-only) 767,559,978: **+1.35%**, fully explained: CoinGecko uses a frozen total 2,135,578,125 minus the same three live balances (reproduces it to 0.007%).
3. vs prod latest_levels 777,906,035 (14:15Z): **−0.0001%** (re-read at the 14:15:13Z block: 777,906,037, +1.4 AERO).
4. Method unchanged (`chain.view_sum`); the sAERO subtraction (50.3% of total) is justified (6-month to 4-year locks, no early exit); without it circulating would be 1,857.0M (+139%, $805.6M vs $337.5M).
5. The 45 old CoinGecko rows (09-24..11-10) cannot be rebuilt with today's terms: the token has no code before 2026-10-16, and before ~11-09 the view_sum measures only the migrated float (99.4M on 10-23 vs CoinGecko 856.5M). Keep them as labelled market_data history; do not backfill.

---

# CAKE (BNB Chain)

## 1. Today's numbers (block 134,520,638, 2026-11-19 14:38:27Z)

| Figure | Value | Kind |
|---|---|---|
| `totalSupply()` | 5,874,225,836 | measured |
| dead `0x…dEaD` | 5,524,547,439 | measured |
| burner `0xceba…0a4e` | 1,308,301 | measured |
| masterchef_v2 `0xa5f8…7652` | 14,121,769 | measured |
| **Orion total_supply** (ts − dead − burner − mcv2) | **334,248,327** | measured (prod 14:15Z: 334,248,327) |
| CoinGecko circulating (dev-only) | 332,221,883 | reference; total 343,746,988 |
| Prod stored circulating | 332,221,883 (latest_levels 2026-11-19 14:15Z; circ_latest 00:45Z 332,221,878) | prod |
| **Proposed circulating (B)** | **315,730,969** | measured |

Proposed vs CoinGecko −4.96%; vs prod −4.96%; vs Orion total −5.54%. Orion total vs CoinGecko +0.61% (coincidental, see §4).

## 2. Proposed method

`chain.view_sum`, existing adapter, no new code. Add to `assets/cake.yaml` `contracts:`

```yaml
  cake_pool: "0x45c54210128a065de780C4B0Df3d16664f7f859e" # legacy CAKE pool (CakeVault v2), closed since veCAKE; holds the delegations locked forever
  vecake: "0x5692DB8177a81A6c6afc8084C2976C9933EC1bAB"    # veCAKE, retired 2025-04-23 (Tokenomics 3.0); unredeemed stakes only
```

```yaml
  circulating_supply:
    source:
      type: adapter
      name: chain.view_sum
      params:
        terms:
          - { contract: token, function: totalSupply }
          - { contract: token, function: balanceOf, args: [ dead ], sign: -1 }
          - { contract: token, function: balanceOf, args: [ burner ], sign: -1 }
          - { contract: token, function: balanceOf, args: [ masterchef_v2 ], sign: -1 }
          - { contract: token, function: balanceOf, args: [ cake_pool ], sign: -1 }
          - { contract: token, function: balanceOf, args: [ vecake ], sign: -1 }
```

The first four terms are exactly `total_supply`'s netting, so circulating ≤ total always and it inherits the smooth series (no
harvest spikes). Option C adds `balanceOf(masterchef_v1 0x73feaa1eE314F8c655E354234017bE2193C9E24E)`.

## 3. Exclusion list

| Address | Label / what | Balance now | Citation | Moves? |
|---|---|---|---|---|
| dead `0x000…dEaD` | burn address | 5,524,547,439 | already in total_supply (asset YAML) | rises weekly (Monday burn) |
| burner `0xceba60280fb0ecd9a5a26a1552b90944770a4a0e` | weekly burn staging | 1,308,301 | already in total_supply; burn-stats.pancakeswap.com burn table: every burn is `from 0xceba…0a4a0e to …dead` | swings 0 to ~50M around harvests |
| masterchef_v2 `0xa5f8c5dbd5f286960b9d90548680ae5ebff07652` | minted CAKE awaiting re-burn + farm float | 14,121,769 | already in total_supply (asset YAML comment) | swings 0.4M to 44M |
| **cake_pool** `0x45c54210128a065de780C4B0Df3d16664f7f859e` | legacy CAKE pool (CakeVault v2). `totalLockedAmount()` 10,629,083; `available()` 13,373,184 | **13,373,184** | PancakeSwap blog 2025-04-21 ("Implementation of CAKE Tokenomics 3.0"): "The **5.29 million CAKE** delegated from the CAKE Pool is now **permanently** locked in the original CAKE pool (burned and irrecoverable by any party)". Docs (cake-tokenomics): "CAKE locked forever in the legacy CAKE pool is also considered burned as it is irretrievable." veCAKE FAQ: "the CAKE staking pool will be deprecated and no longer accepts any further CAKE extension or deposits." | falls slowly as old positions withdraw: 13,454,559 (08-20) → 13,373,184 (−0.6% in 3 months) |
| **vecake** `0x5692DB8177a81A6c6afc8084C2976C9933EC1bAB` | veCAKE escrow, retired. `supply()` 6,190,023 (includes ~1.05M of CAKE-pool positions proxied in) | **5,144,174** | Blog 2025-04-21: "Starting April 23, 2025 … veCAKE and Gauges Voting will officially be retired … all CAKE and veCAKE staking will be unlocked"; rewards end 2025-05-07; voting proposal: "After this 6-month period users can still withdraw … directly from the veCAKE contract." | falls slowly: 5,841,862 (08-20) → 5,144,174 |
| (option C) masterchef_v1 `0x73feaa1eE314F8c655E354234017bE2193C9E24E` | pool 0 (manual CAKE) deposits; v1 still mints 40 CAKE/block into v2 | 7,253,979 | poolInfo(0).lpToken = CAKE (measured); Dune third-party dashboard calls it "V1 pool … no longer active … tokens staked in this pool are forgotten/lost" (not first-party) | 7,282,743 (08-20) → 7,253,979 |
| treasury `0x5ebc62b5c6d92cf6e6d0f9166cb3ac60e9c4ac84` | converters' treasury EOA | 0 | asset YAML: "an EOA that forwards it on" | pass-through; nothing to exclude |

No team vesting, investor or ecosystem-reserve wallet exists to exclude: CAKE had no presale/team allocation; emissions are
minted on schedule by MasterChef (already covered). A third-party summary (Coinoptica) mentions "an ecosystem growth fund
holds about 3.5M CAKE" (claimed, address not identified; ecosystem growth emission is minted and distributed, not held).

## 4. Reconciliation with CoinGecko (dev-only)

* **CoinGecko's circulating is fitted exactly** by `totalSupply − dead − cake_pool.totalLockedAmount() − vecake.supply() − 637,4xx`
  over 4 blocks (10-20, 11-12, 11-17, now): residual constant 637.0k–637.4k (sd 0.2k CAKE). That is PancakeSwap's
  historical homepage formula (total − burned − locked CAKE), with a constant 0.64M we could not attribute.
* CoinGecko does **not** net MasterChef v2 or the burner, so its circulating jumps after every MasterChef v1 harvest: prod's
  stored series reads 317.6M (11-11) → 376.96M (11-10) → 365.2M (11-16) → 317.8M (11-17) → 332.2M today. Today's 0.6% gap
  between Orion total and CoinGecko is coincidence (15.43M of transit sits in v2/burner right now). Netting the transit,
  CoinGecko = 316,791,813 and our B = 315,730,969 (−0.33%); the residual is that CoinGecko uses `totalLockedAmount`+`supply()`
  (16.82M, double-counting ~1.05M proxied positions) where we use the two contracts' actual CAKE balances (18.52M), plus the 0.64M constant.
* CoinGecko total 343,746,988 = ts − dead − 5,931k: the same "locked forever counts as burned" netting PancakeSwap's
  burn-stats uses (burn-stats.pancakeswap.com/data.json 11-17: total_burn 5,530,478,848 vs dead 5,524,547,439 → 5,931,409).

## 5. Check

**None for circulating.** PancakeSwap publishes no circulating figure (homepage no longer shows one; docs list no REST API).
`https://burn-stats.pancakeswap.com/data.json` (first-party, undocumented, weekly; feeds pancake.xyz/burn-dashboard) gives
`total_supply` 329,355,688 at 2026-11-17 = `total_mint − total_burn` (counts the forever-locked CAKE as burned, does not net
transit). It could be a weekly loose check on `ts − dead` (≈2% tolerance, refused on harvest weeks), not on circulating.

## 6. History

All terms are plain views on contracts live since 2021–2023 → archive-readable back to 2025-10-13 and earlier.
Sample **2026-08-20 00:00Z, block 116,940,448**: total 339,054,750; cake_pool 13,454,559; vecake 5,841,862; **B = 319,758,328**.

## 7. Open questions for Mike

1. **Legacy pool + veCAKE: in or out?** Recommend **out (B)**: both contracts are closed (no deposits since 2025-04-23, no rewards
   since 2025-05-07), balances only drain slowly (~0.3%/month), the pool holds ≥5.29M CAKE PancakeSwap itself calls "burned and
   irrecoverable", and B tracks CoinGecko's transit-free level to 0.3%. Counter-argument: ~12–13M of it is redeemable today
   by its owners. Effects at $1.61587: A (total, nothing out) 334.25M / $540.1M (+5.9% vs B); **B 315.73M / $510.2M**;
   C (also MasterChef v1) 308.48M / $498.5M (−2.3% vs B). Prod today $536.8M.
2. **Total supply** (outside R3, flag only): PancakeSwap and CoinGecko both treat the forever-locked ~5.93M as burned; Orion's
   total does not (FDV +1.8%). Reading it exactly needs CakePool `userInfo(delegator)` struct fields, which view_sum can't decode.
3. **Precedent**: do not extend veAERO's subtraction to CAKE on "locked" grounds — nothing is locked any more; the exclusion is
   justified as dormant/irrecoverable sunset contracts instead.

---

# VVV (Base)

## 1. Today's numbers (block 59,544,605, 2026-11-19 14:41:36Z)

| Figure | Value | Kind |
|---|---|---|
| `totalSupply()` | 115,235,591 | measured |
| zero `0x000…000` (burn_sink) | 33,968,539 | measured |
| **Orion total_supply** | **81,267,051** | measured (prod 14:15Z 81,266,970; Venice totalSupply 81,267,051) |
| Venice `vvv_stats.circulatingSupplyCryptoBaseUnit` | 49,295,213.30 (read twice around the block) | first-party |
| CoinGecko circulating (dev-only) | 49,031,992 | reference |
| Prod stored circulating | 49,031,992 (latest_levels 14:15Z); 49,028,841 (circ_latest 00:46Z) | prod (CoinGecko) |
| **Proposed circulating** | **49,295,213.30** (Venice − proposed = 0.0 VVV) | measured |

Proposed vs CoinGecko +0.54%; vs prod +0.54%; vs Venice 0.000%.

## 2. Proposed method

`chain.view_sum`, existing adapter. Add to `assets/vvv.yaml` `contracts:` (treasury already there):

```yaml
  venice_safe_b: "0x4665883F3Adb708F301BA75764D39AD0cD2a4D84" # Venice Safe (same 6 owners as treasury/buyback_safe), 3-of-6
  venice_safe_c: "0xb3c89592D84ae6Adb6A1aa41515ac14eC822B175" # Venice Safe (same owners), 3-of-6
  sablier_linear: "0x4CB16D4153123A74Bc724d161050959754f378D8" # Sablier V2 LockupLinear (shared Sablier contract): team vesting streams
```

```yaml
  circulating_supply:
    source:
      type: adapter
      name: chain.view_sum
      params:
        terms:
          - { contract: token, function: totalSupply }
          - { contract: token, function: balanceOf, args: [ burn_sink ], sign: -1 }
          - { contract: token, function: balanceOf, args: [ treasury ], sign: -1 }
          - { contract: token, function: balanceOf, args: [ venice_safe_b ], sign: -1 }
          - { contract: token, function: balanceOf, args: [ venice_safe_c ], sign: -1 }
          - { contract: token, function: balanceOf, args: [ sablier_linear ], sign: -1 }
    cross_checks:
      - { tolerance_pct: 0.5, source: { type: http_json, url: "https://outerface.venice.ai/api/app/vvv/vvv_stats", path: circulatingSupplyCryptoBaseUnit, decimals: 18 } }
```

## 3. Exclusion list

| Address | Label / what | Balance now | Citation | Moves? |
|---|---|---|---|---|
| zero `0x0000…0000` | burn sink (unclaimed airdrop burn + monthly buyback burns) | 33,968,539 | already in total_supply; The Block via Datawallet: "32.6 million tokens were burned on March 12, 2025" | rises with burns |
| treasury `0x2D8CB8DC596daD0e1E34E2042E7ae6Df93B11524` | Venice SafeL2, 4-of-6 | 20,710,447 | Owner set identical to buyback_safe `0x35FB…7DC57` (the YAML's documented Venice buyback Safe) and the two Safes below; Venice launch post: "35 million (35%) granted to Venice.ai"; Blockworks filing: "Venice.ai, Inc. received 35 million VVV … The separate 10 million VVV Venice Incentive Fund is controlled by Venice" | slow drift: 21.92M (2025-10-13) → 20.78M (08-20) → 20.71M |
| venice_safe_b `0x4665883F3Adb708F301BA75764D39AD0cD2a4D84` | Venice SafeL2, 3-of-6 (same owners) | 8,709,008 | same owner set (measured `getOwners()`); Blockscout: SafeProxy, no label | rises: 6.74M (2025-10) → 8.71M (receives VVV, e.g. Venice's 20% take on DIEM-locked stake) |
| venice_safe_c `0xb3c89592D84ae6Adb6A1aa41515ac14eC822B175` | Venice SafeL2, 3-of-6 (same owners) | 1,582,470 | same owner set (measured) | 1.67M → 1.54M → 1.58M |
| sablier_linear `0x4CB16D4153123A74Bc724d161050959754f378D8` | Sablier V2 LockupLinear (Blockscout tag "SablierV2 : LockupLinear"; shared contract, nextStreamId 94,569) | 969,913 | Launch post: "10m (10%) granted to Team, 25% unlocked upfront and remainder streaming over 24 months" (ends Jan 2027) | falls: 6.05M (2025-10-13) → 2.19M (08-20) → 0.97M; reaches ~0 by 2027-01 |
| *not excluded*: Sablier Lockup `0xe261B366f231B12FCB58D6BbD71e57fAEE82431D` | newer Sablier Lockup, 262,818 VVV | 262,818 | none found (stream sender not identified) | CoinGecko excludes it, Venice does not |
| *not excluded*: staking `0x321b…40Ff` (sVVV) | 34,151,352 held; `totalSupply()` 33,286,395 staked, `totalLockedStakedVVV()` 8,620,666 | — | `cooldownDuration()` = 604,800 s (7 days, measured) | holders' tokens |
| *not excluded*: EOA `0x0810A411…f043` (1,745,143), buyback_safe (8,295) | unlabelled EOA; buyback Safe pending burn | — | Venice does not exclude them | — |

Result: Venice's figure = total − treasury − venice_safe_b − venice_safe_c − sablier_linear, **exact to the wei-rounding at the
same minute** (unique among 2–5-address combinations within 0.3M).

## 4. Reconciliation with CoinGecko (dev-only)

CoinGecko = Venice's set **plus** Sablier Lockup `0xe261…431D` (262,818): that gives 49,032,395 vs CoinGecko 49,031,992 (0.001%).
Archive check 2026-09-20: Venice-set 48,358,039 vs CoinGecko-set 48,060,532 vs prod's CoinGecko row 48,067,238 (0.01%) and
prod's 2026-09-18 Venice disclosure row 48,350,000 (0.02% from Venice-set). Residual gap to CoinGecko: 0.54%, all `0xe261`.

## 5. Check

**Venice first-party**: `GET https://outerface.venice.ai/api/app/vvv/vvv_stats` → `circulatingSupplyCryptoBaseUnit` (18 dp) =
49,295,213.30 now; already wired as a 2% http_json cross-check. Proposed tolerance 0.5% (it matches to 0.000%; Sablier
releases ~0.4M/month move both sides identically). Undocumented endpoint, no history.

## 6. History

All terms are plain views; all contracts predate 2025-10-13 → archive-readable.
Sample **2026-08-20 00:00Z, block 50,197,326**: total 80,820,401; treasury 20,778,581; safe_b 8,638,142; safe_c 1,540,360;
sablier_linear 2,192,296 → **47,671,022**. 2025-10-13 (block 36,762,126): 39,557,301. Venice's API has no history, so the
check can only run live.

## 7. Open questions for Mike

1. **(a) view_sum primary + Venice check, or (b) Venice primary + view_sum check?** Recommend **(a)**: owned, archive-readable,
   every term named; Venice's API is undocumented (the YAML's own rule: "it only ever appears as a cross-check"). A new Venice
   exclusion would fire the 0.5% check rather than silently move the number.
2. **Staked sVVV**: recommend **in** (7-day cooldown, Venice and CoinGecko both count it). Effects at $23.0876: proposed 49.30M / $1,138.1M;
   minus DIEM-locked 8.62M → 40.67M / $939.1M (−17.5%); minus all staked → 16.01M / $369.6M (−67.5%). veAERO's precedent rests on
   6-month+ locks; VVV's lock is a 7-day cooldown, so it should not extend.
3. **Sablier Lockup `0xe261…`**: add it (match CoinGecko, −0.53%, $6.1M) only if its stream sender is shown to be Venice;
   recommend leaving it out and matching Venice (first-party).
4. **Shared Sablier contract**: `sablier_linear` holds every project's VVV streams; today all of it is Venice's per Venice's own
   figure. Risk is low (a third party streaming VVV) and the Venice check would catch a divergence.

---

# AERO (Base, measure-only; on chain since orion-2026.11.09.1)

## 1. Today's numbers (block 59,544,968, 2026-11-19 14:42:49Z)

| Figure | Value | Kind |
|---|---|---|
| token `totalSupply()` | 2,145,974,541 | measured |
| ve `supply()` (sAERO; equals ve's AERO balance) | 1,079,094,329 | measured |
| aero_migration balance | 278,263,599 | measured |
| velo_migration balance | 10,711,363 | measured |
| **On-chain circulating** | **777,905,250** | measured |
| Prod latest_levels | 777,906,035 (14:15:13Z); re-read at block 59,536,691 = 777,906,037 | prod / measured |
| CoinGecko (dev-only) | 767,559,978; total 2,135,578,125 | reference |

vs CoinGecko +1.35%; vs prod −0.0001% (time drift only).

## 2. Method

Unchanged `chain.view_sum` (assets/aero.yaml). No change proposed.

## 3. Exclusions (already live)

sAERO (ve `0xBF79…3915`): app.aero.xyz/docs/products/staking: "AERO is staked for an amount and a duration from 6 months to 4
years … Perpetual Stake"; troubleshooting: "A Perpetual Stake carries a four-year minimum commitment by design, so there's no
early exit." Rising (897.0M 10-23 → 1,079.1M). Migration reserves: falling as holders upgrade (1,054.4M + 76.5M on 10-23 → 278.3M + 10.7M).

## 4. Reconciliation with CoinGecko (dev-only)

CoinGecko = its total 2,135,578,125 − the same live sAERO and migration balances = 767,508,833 (vs 767,559,978, 0.007%). So
CoinGecko's definition is the same as ours (it **also** subtracts sAERO); the 1.35% gap is entirely CoinGecko's frozen total,
10.4M below today's totalSupply (emissions minted since; `emissionsMinted()` 18,460,308). **Concern**: none on definition.
The sAERO subtraction is a big lever: 1,079.1M = 50.3% of total. Without it circulating = 1,856,999,579 (+139%; $805.6M vs
$337.5M at $0.433834). Justified by the 6-month minimum lock; the only caveat is sAERO is a transferable ERC-721, so locked
positions can be sold OTC at a discount.

## 5. Check

None first-party (Aero publishes no circulating figure that we found); CoinGecko is dev-only. No change.

## 6. History

* New token has no code at 2026-10-16 00:00Z (block 52,702,926 window) and has code by 10-17 → the view_sum reverts/zeroes
  before creation. Pre-mint 2,127,000,000 from creation to launch (10-22 00:00Z: totalSupply 2,127,000,000).
* Readable from creation, but before the upgrade wave the value is only the migrated float: 10-23 **99.4M** (CoinGecko row
  856.5M), 11-01 168.9M (CoinGecko 805.4M), 11-09 690.2M (CoinGecko 305.3M). These do not compare with the old rows.
* **The 45 market_data rows (2026-09-24..2026-11-10)**: rows before 10-22 refer to the legacy token `0x9401…8631`; a legacy
  view_sum is possible at archive (legacy totalSupply − legacy_ve supply: 09-24 block 51,712,266 = 936.9M vs CoinGecko row
  996.5M, −6.0%), but it is a different token and definition. Recommend keeping the 45 rows as labelled CoinGecko history
  (or retiring them under R8) and **not** backfilling with today's terms.
* 2026-08-20 archive sample: not possible for the new token (did not exist).

## 7. Open questions for Mike

1. Keep the sAERO subtraction (recommended; CoinGecko does the same, locks ≥6 months). If the rule became "only unsellable":
   it stays (no early exit).
2. Old CoinGecko rows: keep as history (recommended) vs delete in R8; a rebuild would need legacy terms and would still
   differ ~6% from what was stored.
