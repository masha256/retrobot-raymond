# Owned circulating supply (replacing CoinGecko `circulating_supply`)

Depth for scoping or changing an asset's `circulating_supply` source. Market cap basis only: it feeds `marketCap`,
`multiples.mcapTo*` and `perToken.*` (per circulating token); no `yields.*` field reads it (see
`holder-yield-report.md`). Per-asset measurements and citations live in
`workspace/orion/phase3-r3-scoping/` (README.md = table + methods).

## Scoping procedure (multi-asset)
1. Pull prod read-only first (one script: `sql-ro` row counts per asset/source_type, `latest_levels`, every
   `report yield`, one keyless CoinGecko dev-only call), refusing 05:00-06:30 PT. Write a shared BRIEF.md; one subagent
   per chain group (ETH pairs, BNB+Base, Hyperliquid+Solana) told "read BRIEF.md first" and that skills/memory are off
   limits.
2. For each asset, first look for the protocol's own circulating figure: CoinGecko often republishes it exactly
   (Curve `circulating_supply()` on chain, Chainlink `supply.chain.link/supply`, Venice `vvv_stats`, Hyperliquid
   `spotMetaAndAssetCtxs` per-token `circulatingSupply`). Reproducing it with `view_sum` terms and keeping the
   first-party figure as the check is the cleanest method.
3. Reconcile with CoinGecko (dev-only): a gap is a finding to explain (pending-burn balances, a frozen total, a static
   airdrop figure), not a target to hit. CoinGecko figures that never change across stored rows (LINK, LIT) are
   static, not measurements.
4. Re-measure every load-bearing figure yourself (one probe per asset) before presenting.
5. Price every judgement call as an option with its market-cap % and $, and give a recommendation.

## Standing rules for the definition
- Excluded = cannot be sold today: unvested team/investor (balances or a cited schedule), issuer treasury/reserve
  wallets, migration reserves, pending-burn balances, retired-contract balances.
- Staking rule (recommended to Mike for R3): irrevocable long locks (veCRV, veAERO) are not circulating; staking with
  an exit (cooldown or fee-free withdraw: LINK v0.2, lsSKY, VVV, LIT, HYPE) is circulating.
- Issuer-controlled dormant vaults funded from the issuer's custodian at genesis count as treasury even without a
  label; say the evidence is on-chain provenance, not a citation.
- New first-party checks go in as `watch` lines, never level `cross_checks` (a mismatch opens a paid triage anomaly).

## Method pitfalls
- Hyperliquid wallets: add `delegatorSummary` (delegated + undelegated + pending withdrawal) to the spot balance;
  foundation/grant wallets hold almost everything staked, so a spot-only read gives ~0.
- Wrapper treasuries often hold the staked/vault share (st-yCRV), not the token: multiply by `pricePerShare()`.
- Solana has no archive balance reads and pump.fun locks are off chain: subtract owners (all their token accounts),
  not token accounts; history starts on the release day.
- A `view_sum` term whose contract did not exist at an old block (grant escrows, a post-migration token) makes an
  archive rebuild of that day impossible: list it, never sum the remaining terms.
- History: a report reads the newest level at or before its day, so purging stored rows without a rebuild nulls past
  market caps. EVM view_sum rows can be rebuilt at archive blocks (~1 multicall per row); first-party APIs and Solana
  cannot.
- Release gate: flatdiff `rel` bounds |change| only; a market-cap move needs a direction-aware pin (ratio range),
  and choose report day D = today-2 so no hourly price moves between before and after.
