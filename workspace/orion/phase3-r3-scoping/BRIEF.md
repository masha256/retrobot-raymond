# R3 scoping brief (shared by every per-asset scoping subagent)

You are scoping ONE part of Orion Phase 3 R3: "circulating supply on chain". Read-only work. Write your findings to the
file named in your task, under `/home/hermes/.hermes/profiles/raymond/workspace/orion/phase3-r3-scoping/`.

## Background
Orion (repo `/home/hermes/git/orion`, worktree `/home/hermes/git/orion/.worktrees/phase3-r3` = GitHub main 02f39e3, read
it, never edit or commit) is a token-data pipeline. Each asset's `circulating_supply` level is the market-cap basis
(marketCap = price x circulating; FDV = price x total_supply). Today 9 assets read it from CoinGecko `/coins/markets`
(CAKE, CRV, HYPE, LINK, LIT, PUMP, SKY, UNI, VVV); the wrappers cvxCRV/sdCRV/yCRV use the on-chain ERC-20
`totalSupply()`; AERO already uses `chain.view_sum` (total - veAERO locked - two migration-contract reserves; see
`assets/aero.yaml`). R3 replaces every CoinGecko circulating read with an owned method:
1. `chain.view_sum` (EVM, one chain per asset, signed sum of uint256 views at the run block: `totalSupply` minus
   `balanceOf(<named contract>)` terms, `supply()` etc.; see `src/ingest/adapters/evm.ts` validateViewSum), or
2. the asset's own contract reads / first-party API (Hyperliquid `info`, Venice `outerface.venice.ai` vvv_stats,
   Lighter API), or
3. a cited disclosure (issuer docs/blog with a quote) for a fixed allocation that sits in addresses we can then read.
Each excluded address must be named, read on chain, and justified with a citation (issuer docs, explorer label,
contract name/source). Where the protocol publishes its own circulating figure, that first-party figure is the
proposed CHECK, never CoinGecko.

Rules:
- CoinGecko and DefiLlama are allowed ONLY as a "dev-only reference" figure for comparison, labelled so. Never propose
  them as a source or check. At most ONE keyless CoinGecko call per asset if you need more than the provided file.
- Read-only. No ssh, no writes to any DB, no paid APIs. Do not touch `~/.hermes` skills or memory (off limits); write
  only your findings file (and scratch probes under `$TMPDIR`).
- RPC URLs are in `/home/hermes/git/orion/.env` (`ORION_ETH_RPC_URL`, `ORION_BNB_RPC_URL`, `ORION_BASE_RPC_URL`,
  `ORION_SOL_RPC_URL`). They contain API keys: load them in Python (parse the file, never `source` it into a shell that
  runs other commands), never print them, never write them to any file. Keep RPC volume modest (hundreds of calls,
  not thousands). A helper: `exec(open('/home/hermes/.hermes/profiles/raymond/skills/janus/orion/scripts/onchain_probe.py').read())`
  gives `call(addr, sig, args, block)`, `transfers(...)`, `io(...)`, `name(addr)` (Blockscout label) for Ethereum;
  check what env it reads first. Prefer raw JSON-RPC `eth_call` with selectors you compute (`balanceOf(address)` =
  0x70a08231, `totalSupply()` = 0x18160ddd) for other chains.
- Mark every figure **measured** (you read it, with block/slot and time) or **claimed** (from docs/explorer labels).
- Explorer labels / top-holder lists: Etherscan HTML is often blocked; Blockscout APIs (`eth.blockscout.com/api/v2/tokens/<token>/holders`,
  `base.blockscout.com`, BscScan alternatives) and the issuer's docs work. Solana: `getTokenLargestAccounts` + `getAccountInfo` (owner) over our RPC.

## Inputs already pulled (read them)
- `prod/circ_latest.txt` (prod's newest stored circulating_supply per asset, with locator), `prod/supply_latest.txt`
  (total/staked), `prod/circ_obs_summary.txt` (row counts), `prod/report-<asset>.json` (prod's `report yield` v2 JSON).
- `prod/coingecko-markets-devonly.json` (CoinGecko, dev-only reference, fetched today).

## Deliverable per asset (sections, in this order)
1. **Today's numbers**: on-chain total (as Orion's `total_supply` defines it, read live), CoinGecko circulating (dev-only),
   prod's stored circulating (value + date), and your proposed on-chain circulating, with % differences between them.
2. **Proposed method**: the exact `chain.view_sum` terms (contract names you would add to the YAML `contracts:` map with
   addresses, functions, signs) or the adapter/API needed if view_sum can't express it. Say whether existing adapters
   suffice or a new one is needed (and its minimal params).
3. **Exclusion list**: each address: label, what it is, balance now (measured), citation URL + short quote or explorer
   label, and whether its balance moves (vesting releases, buybacks, treasury spends).
4. **Reconciliation with CoinGecko** (dev-only): what CoinGecko seems to exclude that you don't, or vice versa, and the
   residual gap. A large unexplained gap is a finding, not a failure.
5. **Check**: the first-party figure that can serve as the check (endpoint + path + value now), or "none" and why.
6. **History**: can the method be read at an archive block (EVM: yes if all terms are plain views) back to 2025-10-13?
   One archive sample at ~2026-08-20 to prove it (value + block). For non-EVM, say what history is possible.
7. **Open questions / options for Mike**: anything that is a judgement call (e.g. "does staked count as circulating?",
   "treasury: in or out?"), each with a recommendation and the market-cap effect of each option (in % and $ at prod's price).

Convention to apply (Mike, 2026-10-12 and Orion's own definitions): `total_supply` = on-chain supply less burned (FDV
basis). Circulating = total less tokens that cannot be sold today: unvested team/investor allocations, protocol
treasury/reserve/ecosystem wallets that are not distributed, migration/upgrade reserves, pending-burn balances.
Staked/locked-by-holders tokens (veCRV, veAERO is the exception AERO made: it subtracts ve supply) need an explicit
recommendation: AERO's precedent subtracts veAERO (permanent/long locks); say whether that precedent should extend or not.

Finish with a 5-line summary at the top of your file: proposed circulating, vs CoinGecko %, vs prod %, method, open
decision (if any). Return that summary as your final answer.
