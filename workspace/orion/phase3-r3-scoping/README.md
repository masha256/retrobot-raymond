# R3 scoping summary (2026-11-19, measured 14:30-15:00Z; controller re-measured the load-bearing figures 15:05Z)

Files: `code-and-data.md` (what circulating feeds, CoinGecko reads left, stored rows, rebuild feasibility),
`crv-wrappers.md`, `link-uni.md`, `sky-lit.md`, `cake-vvv-aero.md`, `hype-pump.md` (per-asset: numbers, method,
exclusions with citations, CoinGecko reconciliation, check, history, options). Raw prod pulls: `prod/`. Baseline:
`baseline.json`; table: `table.json`. CoinGecko = dev-only reference throughout.

Controller re-check (one probe each, 15:05Z): CAKE total 334,248,327 - pool 13,373,184 - veCAKE 5,144,174 = 315,730,969;
CRV Curve `circulating_supply()` 1,588,069,374 (= CoinGecko); VVV 4-address view_sum 49,295,261.32 = Venice
`vvv_stats` 49,295,261.32 exactly; HYPE `spotMetaAndAssetCtxs` @107 circ 301,557,370 - foundation 60,642,286 - grants
2,979,878 = 237,935,206; PUMP mint 821,771.9M - Token Custodian 229,261.9M = 592,510.1M; LINK `supply.chain.link`
circulating 766,849,970.42 (= proposal); LIT 981,909,280 - eco 231,809,274 - 500M - buyback 4,987,096 = 245,112,910.
All reproduce the subagents' figures (HYPE within 0.0003%, block drift).

Key finding: **no yield reads circulating** (yields divide by total/staked/locked supply). R3 moves `marketCap`,
`multiples.mcapTo*`, `perToken.*` (per circulating token) and the snapshot/tick copies of them; nothing else.

## Per-asset table (recommended method; prod report day 2026-11-17/18 prices)

| asset | prod (CoinGecko*) | proposed | vs prod | vs CoinGecko | mcap old -> new | mcap/HF | HF yield on mcap |
|---|---|---|---|---|---|---|---|
| AERO | 777.22M (chain) | 777.91M (no change: view_sum) | +0.09% (drift) | +1.35% | $336.0M -> $336.3M | 3.8 -> 3.8 | 26.46% -> 26.43% |
| CAKE | 332.22M | 315.73M | -4.96% | -4.96% | $525.1M -> $499.1M | 9.5 -> 9.0 | 10.55% -> 11.11% |
| CRV | 1,587.84M | 1,582.34M | -0.35% | -0.36% | $317.4M -> $316.3M | 25.8 -> 25.7 | 3.88% -> 3.89% |
| cvxCRV | 425.64M (chain) | 420.78M | -1.14% | n/a | $34.6M -> $34.2M | 6.2 -> 6.1 | 16.08% -> 16.27% |
| HYPE | 237.71M | 237.94M | +0.09% | +0.10% | $16,631M -> $16,646M | 15.0 -> 15.0 | 6.67% -> 6.66% |
| LINK | 766.85M | 766.85M | 0.00% | 0.00% | $6,979M -> $6,979M | 130.1 -> 130.1 | 0.77% -> 0.77% |
| LIT | 250.00M | 245.11M | -1.95% | -1.95% | $721.3M -> $707.2M | 16.7 -> 16.3 | 6.00% -> 6.12% |
| PUMP (B) | 457.89B | 403.51B | -11.88% | -11.81% | $1,287.8M -> $1,134.9M | 4.2 -> 3.7 | 23.84% -> 27.05% |
| PUMP (A) | 457.89B | 592.51B | +29.40% | +29.50% | $1,287.8M -> $1,666.5M | 4.2 -> 5.4 | 23.84% -> 18.43% |
| sdCRV | 119.05M (chain) | 117.44M | -1.35% | n/a | $12.7M -> $12.6M | 4.7 -> 4.6 | 21.42% -> 21.71% |
| SKY | 23,414.15M | 23,372.84M | -0.18% | -0.17% | $1,177.9M -> $1,175.8M | 18.6 -> 18.6 | 5.36% -> 5.37% |
| UNI | 607.49M | 607.45M | -0.01% | -0.00% | $3,139.0M -> $3,138.9M | 22.3 -> 22.3 | 4.49% -> 4.49% |
| VVV | 49.03M | 49.30M | +0.54% | +0.54% | $1,070.8M -> $1,076.6M | 90.4 -> 90.9 | 1.11% -> 1.10% |
| yCRV | 71.96M (chain) | 69.55M | -3.35% | n/a | $7.6M -> $7.4M | 4.4 -> 4.2 | 22.88% -> 23.67% |

*prod stores CoinGecko's figure for the 9 CoinGecko assets; AERO and the wrappers are already on chain.
"HF yield on mcap" = holder flow net / market cap = 1 / `mcapToHolderFlow.total` (not a stored field). Every stored
yield (`yields.*`, on total/staked supply) is unchanged.

Methods (exact terms and addresses in the per-asset files):
- AERO: unchanged view_sum (total - veAERO - 2 migration reserves). CoinGecko = same terms on a frozen total.
- CAKE: Orion total - old CAKE pool 0x45c5... - retired veCAKE 0x5692... (view_sum, 6 views). Gap to CoinGecko =
  CoinGecko counts minted CAKE pending the weekly burn (the R0 blind spot). No first-party check.
- CRV: total - veCRV - Curve's own non-circulating list (community fund, LP vesting, token, minter) - Curve Treasury
  (view_sum). Check: Curve's on-chain `circulating_supply()` 0x14139EB6... (differs by the treasury, 0.36%).
- cvxCRV / sdCRV: totalSupply - the protocol treasury's staked balance (view_sum). yCRV: - Yearn treasuries' st-yCRV
  x pricePerShare (needs a view_sum `times` term).
- HYPE: Hyperliquid `spotMetaAndAssetCtxs` circulatingSupply - Hyper Foundation 0xd57e... - grants 0xa20f... (spot +
  staked) (new adapter `hype.circulating_supply`). No independent check (same venue).
- LINK: total - Chainlink's 33 listed non-circulating wallets (view_sum). Check: `supply.chain.link/supply`
  circulatingSupply (first-party, http_json).
- LIT: total - dead - ecosystem reserve - buyback wallet - team/investor locked by the cited schedule (500M; 36 monthly
  tranches from 2027-01-29) (view_sum + new `locked_schedule`). Monitor: the 262 allocation wallets hold 500.000M.
- PUMP: mint supply - Token Custodian Cfq1ts1i... (A) [- 5 dormant custodian-funded vaults, 189.0B (B)]
  (new adapter `solana.supply_less_owners`). Check: custodian >= Blockworks still-locked schedule.
- SKY: total - Pause Proxy - MKR/SKY converter `take()` (penalty fees) (view_sum). No first-party figure.
- UNI: total - dead - Timelock - UF grants wallet - Aera incentives vault (view_sum). No first-party figure.
- VVV: total - 3 Venice Safes - Sablier LockupLinear (view_sum) = Venice `vvv_stats` exactly; Venice stays the check.

Assets without a clean on-chain definition (Mike's flag): wrappers (clean: totalSupply less treasury-held; yCRV needs
`times`), HYPE (first-party API, not chain; two wallets identified by genesis amounts only), LIT (half the
exclusion is a cited schedule, not a balance), PUMP (locks are off chain; vault purposes uncited).
