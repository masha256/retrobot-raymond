# R3 scoping: HYPE (Hyperliquid) and PUMP (Solana) owned circulating supply

Measured 2026-11-19 14:32-14:38 UTC. Prod price basis = `prod/report-<a>.json` `.price` (HYPE $69.9613, PUMP $0.00281254).
CoinGecko figures are a **dev-only reference** (`prod/coingecko-markets-devonly.json`, fetched 14:30Z), never a source or check.
Probes: scratch `$TMPDIR/r3hp/` (tokenDetails reply, PUMP largest accounts, custodian ledger). ~25 Hyperliquid info calls; ~1,450
Solana RPC calls (most of them a one-off: the custodian's full 424-tx ledger and two distribution vaults' ledgers; the
production method needs 1 + N calls). No pump.fun host was contacted.

## Summary

**HYPE**
1. Proposed circulating **237,935,863 HYPE** = Hyperliquid's own `circulatingSupply` (301,558,028) less the Hyper Foundation budget wallet and the community-grants wallet (spot + staked).
2. vs CoinGecko (dev-only) 237,704,287: **+0.10%**.
3. vs prod stored 237,707,639 (2026-11-19 00:45Z): **+0.10%** (market cap +$16.0M at $69.96, $16.630B -> $16.646B).
4. Method: new adapter `hype.circulating_supply` (spotMetaAndAssetCtxs `@107.circulatingSupply`, which the total_supply read already fetches, minus `spotClearinghouseState` + `delegatorSummary` for 2 named addresses; 5 small requests, no 5 MB tokenDetails). Check: `tokenDetails.circulatingSupply` (same issuer, other endpoint), weekly.
5. Open decision: foundation + grants out (recommended; matches CoinGecko to 0.1%) or Hyperliquid's raw figure (+26.9%, +$4.47B). History starts on release day.

**PUMP**
1. Proposed circulating **592.51B PUMP** = mint supply 821.776B less pump.fun's Squads "Token Custodian" vault Cfq1ts1i… (229.262B), the vault that received the entire 1T supply at genesis and holds the still-locked team/investor tokens.
2. vs CoinGecko (dev-only) 457.53B: **+29.5%**.
3. vs prod stored 457.65B (2026-11-19 00:46Z): **+29.5%** (market cap +$379M at $0.0028125, $1.287B -> $1.666B).
4. Method: new adapter `solana.supply_less_owners` {mint: token, subtract: [token_custodian]} = getTokenSupply − Σ owner balances (the existing `ownerBalance` transport). Check: the cited Blockworks schedule (220.0B still locked) must sit below the custodian balance (gap 9.26B, 4%). No first-party figure exists.
5. Open decision: CoinGecko excludes ~135B more than the custodian, most likely some of the dormant pump.fun Squads vaults (80B, 35B, 25B, 25B, 24B, untouched since 2025-07-14), which no source names. Recommend custodian-only until pump.fun discloses them. History: from the release day (or from 2026-10-16 by backfilling the custodian ledger against stored on-chain totals).

---

# HYPE

## 1. Today's numbers

| figure | value (HYPE) | status | vs prod |
|---|---|---|---|
| Hyperliquid totalSupply (`spotMetaAndAssetCtxs` @107, 14:32:52Z) | 998,720,634.94 | measured | |
| Orion `total_supply` (total − Assistance Fund − 0x0 − 0x…dead) | 949,627,663 | measured (prod level 14:15Z: 949,628,182) | |
| Hyperliquid `circulatingSupply` (same reply) | 301,558,027.93 | measured | +26.86% |
| CoinGecko circulating (dev-only) | 237,704,287 | reference | −0.00% |
| prod stored circulating (CoinGecko, 2026-11-19T00:45Z) | 237,707,639 | prod DB | — |
| **proposed** (Hyperliquid circ − Foundation − grants) | **237,935,863** | measured | **+0.10%** (+0.10% vs CoinGecko) |

The proposed figure is 25.1% of Orion's total (CoinGecko 25.0%).

Hyperliquid's own identity (tokenDetails, 14:32:39Z, verified to the unit):
`circulatingSupply 301,558,033.81 = totalSupply 998,720,640.82 − nonCirculatingUserBalances 287,368,344.52 − futureEmissions 409,794,262.49`.

## 2. Proposed method

`chain.view_sum` can't express it (HyperCore, no EVM). The existing `hype.total_supply` can't be reused as-is: its `balanceAt` reads spot balances only, and both excluded wallets hold almost everything **staked** (0xd57e spot = 0.00000044 HYPE, staked 60.64M). New adapter:

```yaml
contracts:
  hyper_foundation: "0xd57ecca444a9acb7208d286be439de12dd09de5d"  # Hyper Foundation budget (genesis 60,000,000)
  community_grants: "0xa20fcfa0507fe762011962cc581b95bbbc3bbdba"  # community grants (genesis 3,000,000)
circulating_supply:
  source: { type: adapter, name: hype.circulating_supply, params: { subtract: [hyper_foundation, community_grants] } }
```

`hype.circulating_supply`: one `spotMetaAndAssetCtxs` (300-370 KB; the pair context for HYPE/USDC `@107` carries `circulatingSupply` next to `totalSupply`, so share the run cache with `hype.total_supply`), then per address `spotClearinghouseState` (HYPE `total`) + `delegatorSummary` (`delegated + undelegated + totalPendingWithdrawal`). Value = circulatingSupply − Σ. 5 requests. Refuse if the result is ≤ 0 or above `total_supply`.

The 5.2 MB `tokenDetails` reply (94,023 genesis rows; fetched here in 1.1 s, but the YAML notes slow links can't finish it) is **not needed**: `spotMetaAndAssetCtxs.circulatingSupply` is the same figure (301,558,027.93 vs 301,558,033.81 thirteen seconds earlier; the 5.9 HYPE gap is fund buybacks in between). `spotMeta` (143 KB) carries no supply fields.

## 3. Exclusion list

Already excluded inside Hyperliquid's circulatingSupply (`tokenDetails.nonCirculatingUserBalances` + `futureEmissions`):

| address | label | what | balance now (measured) | moves? |
|---|---|---|---|---|
| 0x43e9abea1910387c4292bca4b94de81462f8a251 | HypurrScan "HyperLabs"; Hyperliquid lists it non-circulating | core contributors 23.8% (genesis 238,000,000 exactly) | 238,275,372.86 staked + 0.003 spot | yes: pays 375K tranches out (unlocks, e.g. 2026-10-07), takes staking rewards |
| 0xfefe…fefe | Assistance Fund | buybacks; already out of Orion's total | 49,091,295.15 spot | rises daily |
| 0x0…0, 0x…dead | burn | already out of Orion's total | 1,673.79 / 2.72 | rarely |
| (no address; genesis 0xdddd…dddd held 428,062,211) | futureEmissions | future emissions and community rewards (38.888% + unclaimed genesis) | 409,794,262.49 (tokenDetails only) | falls as staking rewards are paid (~10M/yr) |

Added by the proposal (the gap to CoinGecko):

| name | address | what | balance now (measured) | citation | moves? |
|---|---|---|---|---|---|
| hyper_foundation | 0xd57ecca444a9acb7208d286be439de12dd09de5d | Hyper Foundation budget 6% | 60,642,286.11 staked (17 validators) + 0.00000044 spot | genesis balance exactly 60,000,000 (tokenDetails.genesis.userBalances); Hyper Foundation genesis post https://hyperfnd.medium.com/hype-genesis-1830a4dc2e3f: "60,000,000 HYPE are allocated to the Hyper Foundation budget, 3,000,000 HYPE to grants"; HypurrScan label "Hyper Foundation" | slowly: 50K-1M spends (to 0x5440…ede1a9 etc.), + staking rewards |
| community_grants | 0xa20fcfa0507fe762011962cc581b95bbbc3bbdba | community grants 0.3% | 2,874,877.37 staked + 105,001.00 spot = 2,979,878.37 | genesis balance exactly 3,000,000 (same post, same quote). No explorer label found: the match is by genesis amount (claimed) | slowly (grant payouts) |

## 4. Reconciliation with CoinGecko (dev-only)

Hyperliquid 301,558,028 − Foundation 60,642,286 − grants 2,979,878 = 237,935,863 vs CoinGecko 237,704,287: residual **231,576 HYPE (0.10%)**, unexplained (the HIP-2 Hyperliquidity 120K, or a CoinGecko figure lagging Foundation spends/rewards). CoinGecko therefore appears to use Hyperliquid's definition plus the Foundation and grants wallets out. CoinGecko keeps **staked HYPE in** (staked 438.4M exceeds circulating, so it can't be out) and keeps the Assistance Fund **out** of circulating (Hyperliquid lists it non-circulating). CoinGecko's series is hand-stepped: 222,445,714 flat 2026-10-02 to ~10-26, 239,406,814 to 11-13, 237,707,639 now (prod `circ_daily_90d.txt`), so our read will move daily where it moved in steps. The YAML comment "222M vs 299M" is the same two definitions at the earlier date.

## 5. Check

`POST https://api.hyperliquid.xyz/info {"type":"tokenDetails","tokenId":"0x0d01dc56dcaaca66ad901c959b4011ec"}` → `.circulatingSupply` = 301,558,033.81 now (5.2 MB; weekly or monitor-only, 2% tolerance against the adapter's pre-subtraction figure). It is the same issuer through a different endpoint, so it catches a parsing/pair error, not a definition change; the identity `totalSupply − nonCirculatingUserBalances − futureEmissions` from the same reply is a stronger internal check. Also worth a monitor-only alert if `nonCirculatingUserBalances` gains or loses an address.

## 6. History

None from the API: `info` reports the present only (no block/height parameter), and `futureEmissions` has no history. The two wallets' past balances could be rebuilt from `userNonFundingLedgerUpdates` + `delegatorHistory`, but Hyperliquid's circulatingSupply itself can't, so **history starts on release day**. No archive sample is possible. Prod's stored CoinGecko series (≈ the same definition, 0.1% away since 11-13) stays as the pre-release history if Mike accepts it; it carries the hand steps above.

## 7. Open questions for Mike

| option | circulating | vs prod | market cap at $69.96 |
|---|---|---|---|
| A. Hyperliquid raw `circulatingSupply` | 301,558,028 | +26.86% | $21.097B (+$4.467B) |
| **B. A minus Foundation + grants (recommended)** | 237,935,863 | +0.10% | $16.646B (+$16.0M) |

- **Foundation/grants in or out?** Recommend out: undistributed treasury per the 2026-10-12 convention, and it matches CoinGecko within 0.1%, so the switch is invisible in the report. A alone is cheaper (zero extra requests) but counts a treasury budget as circulating.
- **Staked HYPE (438.4M, 46% of total)?** Recommend in (don't extend AERO's veAERO precedent): HYPE staking is a 1-day delegation lock plus a 7-day unstaking queue, not a multi-year lock; both Hyperliquid and CoinGecko count it. Subtracting it would turn circulating negative against B (staked > B), because the contributor and Foundation wallets are themselves staked.
- **0x43e9 attribution**: Hyperliquid's API names it non-circulating, and its genesis amount equals the 23.8% contributor bucket; it pays out unlocks, so its balance (not a schedule) is the unlocked amount. Nothing to decide, just recorded.

---

# PUMP

## 1. Today's numbers

| figure | value (PUMP) | status | vs prod |
|---|---|---|---|
| mint supply = Orion `total_supply` (getTokenSupply, slot 471,372,192, 2026-11-19 14:38Z) | 821,775,605,322 | measured | |
| CoinGecko circulating (dev-only) | 457,525,853,406 | reference | −0.03% |
| prod stored circulating (CoinGecko, 2026-11-19T00:46Z) | 457,649,429,223 | prod DB | — |
| **proposed** (supply − Token Custodian) | **592,513,747,140** | measured | **+29.47%** (+29.50% vs CoinGecko) |
| variant: also − the two distribution vaults | 573,171,180,090 | measured | +25.24% |
| (b) cited schedule: supply − team/investor still locked (220.0B, monthly steps) | 601,775,605,322 | claimed schedule | +31.49% |

Proposed = 72.1% of total (CoinGecko 55.7%). The 827.6B in the brief is the 2026-10-16 figure; the mint is now 821.78B after burns.

## 2. Proposed method

Needs a small new Solana adapter (no EVM, so no view_sum). Everything it needs exists in `src/ingest/transport/solana.ts` (`tokenSupply`, `ownerBalance` = getTokenAccountsByOwner summed over all the owner's token accounts):

```yaml
contracts:
  token_custodian: "Cfq1ts1iFr1eUWWBm8eFxUzm5R3YA3UvMZznwiShbgZt"  # pump.fun Squads vault "Token Custodian" (Solscan/Arkham)
circulating_supply:
  source: { type: adapter, name: solana.supply_less_owners, params: { mint: token, subtract: [token_custodian] } }
```

`solana.supply_less_owners` {mint, subtract: [contract names], rpc_url_env?}: `tokenSupply(mint)` − Σ `ownerBalance(owner, mint)`, one finalized read each (1 + N calls), detail naming each owner and slot; refuse a result ≤ 0. Subtract owners (wallets/vaults), not token accounts, so a new ATA under the same vault is still counted. Optional report-only `token_custodian_pump` level via the existing `solana.owner_balance` to show unlock outflows.

## 3. Exclusion list

| name | owner (token account) | what | balance now (measured, slot 471,372,190) | citation | moves? |
|---|---|---|---|---|---|
| token_custodian | Cfq1ts1iFr1eUWWBm8eFxUzm5R3YA3UvMZznwiShbgZt (7AN6avKCJPMkXkW8kPwMuHmaWvJeHH69e8rKpLf9rdfk) | genesis custody multisig; holds the still-locked team/investor tokens | 229,261,858,182 | Solscan label "Pump.fun: Token Custodian" (https://solscan.io/account/Cfq1ts1iFr1eUWWBm8eFxUzm5R3YA3UvMZznwiShbgZt); Arkham "pump.fun: Squads Vault 'Token Custodian'"; on chain: it received 1,000,000,000,000 PUMP (the whole supply) from Doa8F9eu… on 2025-07-10 13:35Z and every outflow since is a Squads v4 (`SQDS4ep…`) execution; BlockBeats: "post-TGE, all $PUMP was moved to a multisig custody wallet for distribution" | yes, in steps: −62.2B 2026-06-25 and −74.0B 2026-09-08/13 to the two distribution vaults below (the post-cliff team/investor releases) |

Not subtracted (variant / open question):

| owner | balance now | what we can show | citation |
|---|---|---|---|
| GsM3emTijQshDHrWRRhSQhqG1zYC9BNnAuah7ZPEu6ya (RBcsEReE…) | 5,480,748,240 | Squads vault; got 54.2B (2026-06-25) + 54.0B (09-13) from the custodian (plus ~7.0B from elsewhere; 115.2B in), paid 146 transfers from 2026-07-14 (the cliff payout; Blockworks: "On 15 July 2026 pump.fun distributed 57,279,000,000 PUMP … across 121 wallets") | on-chain flow only; no label |
| ESRc4ce6jpyRyvGJ9Gjgtmwc7wEtR1ZPaQPnh9kWZM67 (F6yfKLkv…) | 13,861,818,810 | same pattern: 8.0B (06-25) + 20.0B (09-08) from the custodian plus one ~3.0B inflow from elsewhere (31.0B in), 31 payouts from 2026-07-14 | on-chain flow only |
| dormant Squads vaults funded by the custodian 2025-07-14, unchanged since: 8UhbNo… 80.0B, 9pkFKC… 35.0B, BBvQte… 25.0B, GTeSSw… 25.0B, AvqFxK… 24.0B (sum 189.0B) | 189.0B | System-owned accounts created inside the custodian's Squads txs (probably Squads vaults; none has made an outflow, so this is unproven); 16 months without a PUMP outflow | none: pump.fun never published which bucket each wallet holds (BlockBeats: "the pump.fun official team has never disclosed the wallet addresses corresponding to the funds of each part") |
| 85WTuj…, 96HiV4…, ERRGqu… (20.0B + 15.33B + 11.33B) | 46.67B | funded 30/23/17B from the custodian 2025-08-21; each pays exactly 1/48 of its grant a month to 6HuD7aQk… (a 4-year monthly vest, 16 of 48 paid) | none (pattern only) |

No vesting program holds PUMP among the top 20: every owner is a System-owned account (wallet or Squads vault PDA); the only program-level vesting seen is Streamflow (`strmRq…`) instructions touching the two distribution vaults. Locks are therefore enforced off chain; no lock end/cliff can be decoded on chain.

Allocation (pump.fun's own post, https://x.com/Pumpfun/status/1942947291083493495, 2025-07-09): "33% will be sold in the Initial Coin Offering 24% reserved for community and ecosystem initiatives 20% to the team 2.4% to the ecosystem fund 2% for the foundation 13% to existing investors 3% for livestreaming 2.6% for liquidity + exchanges". Vesting (Blockworks Token Transparency filing, compiled by Blockworks, the citation Orion already uses): team 20% + investors 13% "locked for 12 months from 12 July 2025 and then vest linearly over three years to July 2029 … leaving 247,500,000,000 PUMP locked" after the cliff. As of 2026-11-19: 220.0B still locked with monthly steps (4 of 36 paid), 218.1B if continuous. The custodian's 229.26B exceeds that by 9.26B (4%), consistent with it holding exactly the locked pool plus a small residue of other buckets.

## 4. Reconciliation with CoinGecko (dev-only)

CoinGecko excludes total − circ = **364.25B**; the custodian explains 229.26B, leaving **~135B unexplained**. CoinGecko's figure is total minus a near-fixed set (364.84B on 2026-10-16, 364.25B now: it falls by the burns, so it is computed from current supply), but it moved a lot earlier: Blockworks quotes CoinGecko at 396.95B circulating on 2026-08-28 (440.1B excluded), so CoinGecko reclassified ~75B between 08-28 and 10-16. Several subsets of the dormant vaults sum to ~135B (e.g. 80 + 35 + 20.0), so the subset can't be identified from balances. Likely CoinGecko also excludes part of the 24% community/ecosystem + ecosystem fund + foundation + livestream buckets (the dormant vaults). This is a finding: a 29.5% gap that no public source explains.

## 5. Check

**None first-party**: pump.fun publishes no circulating figure or vesting schedule (its hosts are off limits anyway, terms §21(h)). Proposed check: the cited schedule's still-locked amount (`schedule.unlocks_next_year` already carries the Blockworks schedule: 247.5B linear from 2026-07-12 over 3 years) must be ≤ the custodian balance; alert if the custodian falls below the schedule (tokens released early) or sits > 10% above it (a new bucket parked there). Today 229.26B vs 220.0B: passes.

## 6. History

Solana has no balance-at-slot read (no archive `getTokenAccountBalance`). But the custodian's token account has only **424 signatures** since genesis, so its balance series is cheap to rebuild once (getSignaturesForAddress + getTransaction pre/post token balances: done here, ~430 calls, the ledger closes exactly at the live 229.26B). Sample: custodian balance on **2026-08-20 = 303,261,858,182** (between the 2026-06-25 and 2026-09-08 outflows; `$TMPDIR/r3hp/pump_treasury_flows.json`). The limit is the total: there is no past mint supply either, and prod's on-chain `total_supply` series starts 2026-10-16. So the method can be backfilled **from 2026-10-16** (stored totals − rebuilt custodian ledger); before that only with a reconstructed supply (~9k burns a day, not feasible) or a third-party total. Default: **history starts on release day**; offer the 2026-10-16 backfill as a one-off.

## 7. Open questions for Mike

Market cap at prod price $0.0028125 (prod now $1.287B on 457.65B):

| option | circulating | vs prod | market cap |
|---|---|---|---|
| **A. supply − Token Custodian (recommended)** | 592.51B | +29.47% | $1.666B (+$379M) |
| A'. A − the two distribution vaults | 573.17B | +25.24% | $1.612B (+$325M) |
| B. supply − cited locked schedule (220.0B) | 601.78B | +31.49% | $1.693B (+$405M) |
| C. A − the five dormant vaults (189B), uncited | 403.51B | −11.83% | $1.135B (−$152M) |

- **Custodian only, or also the distribution vaults?** Recommend A: one named, labelled address, measured, consistent with the cited schedule. The distribution vaults hold already-unlocked tokens in transit to recipients (A' is defensible; −3.3pp).
- **Dormant vaults (189B)**: CoinGecko evidently excludes some of them; no citation names them, so per the brief's rule they stay in until pump.fun (or a filing) names their purpose. Mike may accept on-chain behaviour (16 months untouched, funded by the custodian) as the justification: that is option C, and the market cap would then sit 12% under today's.
- **Staked**: not applicable (PUMP has no staking).
- The switch moves PUMP's reported market cap +29.5% overnight; flag it in the release notes.
