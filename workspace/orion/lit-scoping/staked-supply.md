# LIT staked supply: source scoping (read-only, 2026-10-23)

Status: scoping only. Nothing was written to the Orion repo or `orion.db`. Each value is marked **[measured]** (read by me from a first-party API or the chain on 2026-10-23) or **[claimed]** (an issuer statement or a third party).

## Answer

- **Where staking happens: inside the Lighter L2.** There is no L1 staking contract. Stakes go into one protocol account on the L2, the "LIT Staking Pool" (account type 4, a public-pool-style account). The pool's LIT balance is the staked total. [measured]
- **Staking pool index:** `281474976624800`, published by Lighter itself in `GET /api/v1/systemConfig` → `staking_pool_index`. The same response gives `staking_pool_lockup_period: 259200000` ms, i.e. a 3-day unstake lockup, which matches the docs. [measured]
- **Today's value: 110,921,555.98 LIT staked**, read 2026-10-23T23:34:31Z. [measured] That is 11.3% of total supply (981.91M) and 72.8% of all LIT on the L2 (152.31M, below).
- **Total-staked endpoint:** none that returns the number as a single field. `publicPoolsMetadata?filter=stake` returns `[]` for every index/limit I tried. Use the pool account's asset balance instead:
  `GET https://mainnet.zklighter.elliot.ai/api/v1/account?by=index&value=281474976624800`
  → `accounts[0].assets[]` where `symbol == "LIT"` (`asset_id` 2) → `balance`.
  The value is a decimal string already in LIT units: the L2 uses 8 decimals (`assetDetails?asset_id=2`: `decimals: 8`, `l1_decimals: 18`), so no scaling is needed. Today `assets` holds only LIT, so `accounts.0.assets.0.balance` resolves to it. `pending_unlocks` is `[]`, and `shares[]` and `total_asset_value` are 0/empty because USD pool accounting doesn't apply here.

## Comparison with 109.8M at 2026-09-30

- The issuer's figure from the Q3 call ("109.8 million LIT is currently staked") is **[claimed]**.
- The API gives the balance for today only. Today's 110.92M is +1.0% above the claim.
- **A point-in-time check for 09-30 is possible [measured]:** since 2026-07-07, the daily reward equals exactly 6%/365 of the staked balance (see Rewards below). The 2026-09-30 reward of 18,042.66 LIT implies 18,042.66 × 365 / 0.06 = **109.76M staked on 2026-09-30**, which matches 109.8M.
- The same estimator on today's 18:00Z reward (18,328.37 LIT) gives 111.50M, against the 110.92M balance read 5.5 h later (0.5% apart). So the estimator tracks the balance to within about 1%, with timing/unstake drift.
- Third-party reference only: litdash.xyz showed 115.44M on 2026-10-21. The estimator gives 114.52M for that day. [claimed]

## Rewards: rate and flow

- **Rate:** Lighter's docs (docs.lighter.xyz/about-lighter/lit-utility) say stakers "currently earn a fixed 6% APR", with the LIT for rewards bought from `0xADbE1265C0df1B623A56d324De494Bcb8e8914Ff`. [claimed]
- **Measured check:** 18,328.37 × 365 / 110.92M = 6.03%. [measured]
- The `pool_info.annual_percentage_yield` field (163%) is a USD share-price return driven by the LIT price. It is not the staking APR, so ignore it.
- **Flow [measured, L1 via Alchemy + L2 via explorer]:**
  1. Treasury account 0 buys LIT on the L2. Per the existing Orion notes, the bought LIT is withdrawn to buyback wallet `0x1a51…160d`, which holds 10,257,144.50 LIT on L1 today.
  2. `0x1a51…160d` sends LIT to `0xADbE…14Ff` (an EOA) about weekly, 100k–150k LIT each time. Recent sends: 10-19 150k, 10-12 137k, 10-05 130k, 09-28 105k+50k, …
  3. `0xADbE…14Ff` deposits the same amount on L1 into the Lighter bridge `0x3b4d…5ca7` within minutes. Before 2026-08-27 it went via Relay's `RelayRouterV3` `0xb92f…ff4f`. Each deposit is credited on the L2 to account `733613` (L1DepositV2).
  4. Account `733613` (71,430.71 LIT left today) sends one L2Transfer per day at about 18:00Z to the staking pool. Recent amounts: 18.3k–18.8k LIT.
  - Before 2026-07-13 the daily reward came from L2 account `711044`. Its amounts were fixed until 2026-07-06: 27,400/day (Jan–Apr) and 13,700/day (May–Jul 6). From 2026-07-07 the amount varies with the balance, i.e. the 6% APR rule.
- So 0x1a51's bought LIT does fund the staking rewards, as already assumed. That is consistent with keeping `staked_supply` at constant 0 for valuation.

## LIT on the L2 (context)

- The Lighter L1 bridge/rollup contract `0x3B4D794a66304F130a4Db8F2551B0070dfCf5ca7` (a proxy; implementation `0xE16c…E5A7` per Blockscout) holds **152,313,686.05 LIT** (`LIT.balanceOf`, block 0x190acdf, 2026-10-23T23:36Z). [measured]
- Staked LIT is 72.8% of that.

## History availability

- **Level series:** not available from the API. `account` returns the balance now only. `pool_info.share_prices` gives a daily USD price per share since 2026-01-14, but `total_shares` is current-only, so it can't be turned into staked LIT history.
- **Exact replay from stake/unstake events:** not practical. The pool's own log (`https://explorer.elliot.ai/api/accounts/281474976624800/logs`) contains only the reward L2Transfers. `pub_data_type=L2StakeAssets` and `UnstakeAssets` both return `[]` for the pool, because stake/unstake events sit on each staker's account.
- **Backfillable estimate:** reward-implied staked = daily reward × 365 / 0.06, for 2026-07-07 onward. The explorer logs go back to 2026-01-28: 271 transfers over 3 pages of `limit=100&offset=N&pub_data_type=L2TransferV2`. This holds only while the 6% rule stands.
  - Estimates: 07-07 108.7M, 08-31 116.5M, 09-30 109.8M, 10-21 114.5M.
  - Raw rewards: `staking-rewards-2026.tsv` (date, sender account, LIT) next to this file.
  - Before 07-07 the rewards were fixed amounts and say nothing about the staked balance.
  - The explorer API is a separate host (explorer.elliot.ai) and undocumented beyond apidocs' `logs` page. It is first-party but not the main API.

## How Orion would read it

- **Recommended: config-only, existing `http_json` source, as a `monitor_only` level (e.g. `staked_lit`).** `staked_supply` stays a constant 0 as decided.
  ```yaml
  staked_lit:
    type: level
    unit: tokens
    staleness_days: 3
    monitor_only: true
    source: { type: http_json, url: "https://mainnet.zklighter.elliot.ai/api/v1/account?by=index&value=281474976624800", path: accounts.0.assets.0.balance }
  ```
  - `readPath` indexes arrays by numeric segment and `toFiniteNumber` parses the string. The schema defaults (`scale: 1`, `decimals: 0`, `src/config/sources.ts`) give LIT directly.
  - Risk: the path is positional. If the pool ever holds a second asset, `assets.0` could become a different asset and the read would be silently wrong.
- **Sturdier option: a small `lit.ts` adapter (`staking_pool`).** It would:
  - read `systemConfig.staking_pool_index`, so a pool move is followed automatically;
  - pick `assets[]` by `symbol == "LIT"`;
  - optionally fail if `pending_unlocks` is non-empty;
  - optionally also return the daily reward/APR from the explorer log, so the "fixed 6%" claim is checked daily and an alert fires if it changes (Mike's rule: read rate parameters from the protocol).
- No `contract_read` or `erc20` balance fits, because staking isn't on L1. An `erc20` balance of `0x3b4d…5ca7` would give total LIT on the L2 (152.3M), which could be a second monitor line.
- History starts on the go-live day (level metrics have no backfill path). A reward-implied backfill from 07-07 would need a one-off manual import or adapter support. Flag it as an estimate if it is done.
- No DefiLlama needed: every figure here is first-party (Lighter API, Lighter explorer API, Ethereum).

## Sources

- `GET https://mainnet.zklighter.elliot.ai/api/v1/systemConfig`, `/account?by=index&value=281474976624800`, `/account?by=index&value=733613`, `/accountsByL1Address?l1_address=0xADbE…`, `/assetDetails?asset_id=2`, `/publicPoolsMetadata?filter=stake&index={0,1}&limit=…` (empty)
- `GET https://explorer.elliot.ai/api/accounts/{281474976624800,733613}/logs?limit=100[&offset=N][&pub_data_type=…]`
- Ethereum: `alchemy_getAssetTransfers` (LIT, from/to 0xADbE…), `LIT.balanceOf` for 0x3b4d…, 0xb92f…, 0xADbE…, 0x1a51…
- Docs: https://docs.lighter.xyz/about-lighter/lit-utility (6% APR, 0xADbE… reward buyer, 3-day lockup); https://apidocs.lighter.xyz/reference/publicpoolsmetadata.md (filter=stake)
- Q3 call transcript: `disclosure-watcher/transcripts/lit/2113065839352336774.txt` [11:41]
