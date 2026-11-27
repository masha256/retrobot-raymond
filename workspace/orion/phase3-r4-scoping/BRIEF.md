# Phase 3 R4 scoping brief: AERO revenue on chain (pool_scan pilot) — RET-20

Written 2026-11-27 by the controller (Raymond). Read this first. Everything here is read-only scoping for a plan that
Mike will review; nothing is built until he approves the plan.

## Goal of R4 (spec `docs/superpowers/specs/2026-11-09-orion-phase3-third-party-removal-design.md` §4 AERO, §5, D6)
Replace AERO's DefiLlama revenue series `flow_usd.fees` (`defillama` source, slug `aerodrome`, `dailyHoldersRevenue`)
with an owned on-chain read (`pool_scan`): `PoolTape` / `CLPoolTape` `accumulators(pool)` at UTC day-boundary blocks
over every `factory.allPools()` pool on the 7 Aero chains, plus VotingRewardsManager (VRM) `incentive(id)` programs for
the incentives. History: delete the DefiLlama rows; backfill on chain to the merger (Aero launched 2026-10-22 00:00Z).
The 91-day window fills ~2027-01-21; growth (182 d) ~2027-04-22. Until then the report shows a shorter window, labelled.

## Hard rules (Mike)
- No live Orion code may read CoinGecko or DefiLlama (licensing), not even as a cross-check. You MAY use them during
  scoping as a **dev-only reference** (label it so). Every number you report is marked MEASURED (block/tx/call cited)
  or CLAIMED (URL quoted).
- Method ladder: contract state reads > single-address log scans / first-party API > fixed pool-list scans with stated
  coverage > licensed query engine. No indexer.
- Prices: on chain only. Existing Orion methods: `chain.v2_pool_twap_price` (pool TWAP x Chainlink stable/USD feed) and
  `chain.cl_pool_spot_price` (slot0) as the independent check; Chainlink `<token>/USD` feeds where they exist.
- Read only. Never write to any DB, never ssh anywhere, never deploy. Never print or write the RPC key (mask URLs as
  `https://<chain>.g.alchemy.com/v2/***`). Do not edit any skill, memory, or file outside your own output file(s) under
  `~/.hermes/profiles/raymond/workspace/orion/phase3-r4-scoping/`. Do not commit to git.
- RPC quota is shared with prod (Mike's Alchemy key). Batch calls (Multicall3 / JSON-RPC batches). Do no RPC work between
  16:30 and 17:15 PT (prod nightly 00:45Z) nor 05:00-06:30 PT. Stop and report if the provider throttles hard.

## Inputs
- Repo (read only): `/home/hermes/git/orion` (main = GitHub main 2635cae = release orion-2026.11.21.1, live on prod+stage).
- RPC: `/home/hermes/git/orion/.env` holds `ORION_BASE_RPC_URL` (Alchemy Base) and `ORION_ETH_RPC_URL` (Alchemy mainnet).
  The same key works on `opt-`, `arb-`, `ink-`, `robinhood-`, `arc-mainnet.g.alchemy.com/v2/<key>` (swap the subdomain).
  Load it in Python without printing it.
- Probe helper: `exec(open('/home/hermes/.hermes/profiles/raymond/skills/janus/orion/scripts/onchain_probe.py').read())`
  (read it first; adapt as needed). Base moved to 0.2 s blocks ~2026-11-05 18Z: find day-boundary blocks by
  timestamp search, never by block-time arithmetic.
- Earlier scoping (2026-11-09; re-measure, don't trust): `~/.hermes/profiles/raymond/workspace/orion/aero-scoping/`
  `a-revenue-settlement.md` (contract graph, tapes, per-chain pool counts, 11-07 one-day measurement),
  `b-incentives.md` (incentive programs, Foundation wallet 0x7269…9dDb), `c-defillama-series.md`.
- Contract addresses: GitHub `dromos-labs/metadex-public` and `dromos-labs/metadex-slipstream-public`,
  `deployment-addresses/*.json`; Aero docs https://app.aero.xyz/docs/security. Copy addresses from there or from the
  earlier scoping files and re-read them on chain; never type one from memory.
- Current AERO config: `/home/hermes/git/orion/assets/aero.yaml` (revenue line `fees` -> holders `voter_fees` cash 2%
  haircut; `lp_fees` cost not_measured; `bribes` below_line not_measured).
- Prod reference (pulled read-only by the controller 2026-11-27): `prod/report-yield-aero-2026-11-27.json` and
  `prod/aero-fees-rows-since-1015.json` (stored DefiLlama daily rows; a row stamped D 00:00Z covers UTC day D-1).
  Prod: 306 `third_party` rows 2026-03-27..2026-11-27 + 2 `derived` rows (the 2026-09-09 manual correction).
  Revenue annualized $91.8M, 91-day window sum $22.89M.

## Output
Write your file(s) into this directory. Lead with a short answer table, then evidence, then open questions. Keep the
measured/claimed labels. End with the exact list of addresses (chain, role, address, how verified).
