# Task 4 report: circulating supply on chain for 12 assets; CoinGecko refused in every field

Worktree `/home/hermes/git/orion/.worktrees/phase3-r3`, branch `feat/phase3-r3-supply`, BASE 5a68aff.

## Commits
- `94c6d04` feat(ingest): derived level_gap_pct and solana.owners_balance (R3 N5 checks)
- `596245b` feat(assets): circulating supply on chain for 12 assets; CoinGecko refused in every field

## What was built

### (a) 94c6d04: derived `level_gap_pct` (Ruling R3) and `solana.owners_balance` (Rulings R4/R10)
- `src/ingest/derived.ts`: `level_gap_pct` added to `DERIVED_NAMES`/`DerivedName`; `levelGapPct(a, b)` = (a/b - 1) x 100,
  null when b = 0; `levelGapIssues()` (the load-time rules). `derivedFunction('level_gap_pct')` throws (no flow window).
- Load-time validation (`src/config/schema.ts` superRefine, only for `name: level_gap_pct`, so other derived kinds are
  untouched): params exactly `{a, b}` (unknown keys refused), each a level metric of the asset with a non-derived source,
  not the gap metric itself, a != b, and the gap metric itself a `monitor_only` level (my addition: it is a check, never
  report data).
- `src/ingest/run.ts` derived pass: for `level_gap_pct`, takes this run's latest written reading of a and b, writes the gap
  at the later of the two observedAt, every run (like a level read, so `watch: outside` fires on every fetch while out of
  band). A side with no reading this run: a note `"<key>: skipped, <m> gave no reading this run"`, no write, source ok.
  b = 0: source failed `"<key>: level_gap_pct: <b> is 0; no gap"`. Provenance: `formula level_gap_pct@1`, inputs
  `[{metric, at, value}]`; if either input is an API reading the row carries `input_origin: api` (R10.7) and reads back as
  api. Detail: `derived level_gap_pct(<a> <va> / <b> <vb>)`.
- `src/report/sourceTypes.ts` `derivedInputs` also returns `a`/`b` (locator metrics, third-party inheritance).
- run.ts failure streaks: derived requests now count in `metricsOfSource`, so a failing derived source over monitor-only
  metrics raises no streak (existing derived metrics are not monitor-only: unchanged).
- `solana.owners_balance` {mint, owners, rpc_url_env?}: the sum of the owners' balances (what supply_less_owners
  subtracts), 0 allowed, same R8 rule (pump.fun host refused before any request). Registered in ADAPTER_SOURCE_TYPES
  (contract_state), ADAPTER_ORIGINS (onchain), ADAPTER_ENDPOINTS (solRpc), adapterOrigins sample, origin.test PROD list.
  Task 3 code touched minimally: its loop/host check/validation were extracted into shared helpers (`ownersIssues`,
  `ownRpcUrl`, `ownersHeld`) so both adapters use the same reads; Task 3's tests pass unchanged.

### (b) 596245b: refusal, YAML sweep, register, templates, re-pins
- `src/config/sources.ts`: `coingeckoPriceIssues` -> `coingeckoIssues`, every field refused (`COINGECKO_FIELDS` =
  price, market_cap, circulating_supply, total_supply). Price fields keep their R2 message; supply fields:
  `coingecko field "<f>" is refused: no CoinGecko read (Phase 3 R3); a supply comes from the chain or the issuer (...)`.
  Callers: `src/config/load.ts` (same R32(b) gate: roots with prices.yaml entries), `tests/config/templates.test.ts`.
  `src/agent/tools/write.ts` needed no change: filing (and approve) parse through `parseAssetObject` with the run's /
  home's prices, so the refusal applies there; pinned by the new filing and approve tests.
- `src/levels/levels.ts`: `coingeckoIds` exported; pinned [] for all 13 assets (tests/config/sources.test.ts,
  tests/levels/levels.test.ts: runLevels makes no CoinGecko call).
- 12 YAMLs per task-4-values.md (all 56 addresses in that file verified present byte-exact in the YAMLs by script):
  - CAKE view_sum 6 terms (+cake_pool, vecake). CRV view_sum 7 terms (+circ_contract, community_fund, vest_prelp,
    minter) + `curve_circulating` (contract_read circ_contract circulating_supply, decimals 18, monitor-only) +
    `circulating_gap_curve` (level_gap_pct a=circulating_supply b=curve_circulating, watch outside [-1.5, 0.5], R10).
  - cvxCRV view_sum 2 terms (wrapper.balanceOf(convex_treasury)); sdCRV 2 (+sd_governance, gauge.balanceOf); yCRV 3
    (+yearn_treasury_vault; two st_ycrv.balanceOf terms with `times: {st_ycrv, pricePerShare, 18}`).
  - HYPE `hype.circulating_supply` subtract [hyper_foundation, community_grants] (+both contracts).
  - LINK view_sum 34 terms (+nc_01..nc_33 in task-4-values order) + `chainlink_circulating` (http_json
    https://supply.chain.link/supply circulatingSupply decimals 18, monitor-only) + `circulating_gap_chainlink` (watch
    outside [-0.5, 0.5]).
  - LIT view_sum 4 terms + `locked_schedule {500000000, "2027-01-29", 36, 1, https://x.com/Lighter_xyz/status/2005862687331303804}`.
  - PUMP `solana.supply_less_owners` subtract the six owners (+token_custodian, dormant_a..e) + `reserved_balance`
    (`solana.owners_balance` same six, monitor-only, watch change_pct 1).
  - SKY view_sum 3 terms (+mkr_sky take()). UNI 5 (+uf_grants, aera_incentives). VVV 6 (+venice_safe_b, venice_safe_c,
    sablier_linear), Venice check kept at 2%.
  - Every new contract has a one-line citation/evidence comment from its scoping file; existing subtracted entries (ve,
    curve_treasury, convex_treasury, yearn_treasury, ecosystem_reserve, buyback_wallet, pause_proxy, VVV treasury) got
    their citation appended. Each circulating comment rewritten (what is subtracted and why, the 2026-11-20 figure,
    staking-with-exit stays circulating). LINK/SKY header lines that said "except the circulating supply (CoinGecko)" fixed.
- Register: `supply.chain.link` TERMS row added (first_party_api, Chainlink, commercial unknown); the
  `api.coingecko.com` TERMS row **removed** (the generator refuses a row no asset reads). Regenerated.
- Templates: every `coingecko` circulating source replaced by the template's own total_supply read plus a comment on how to
  subtract the non-circulating holders; the `coingecko field: total_supply` cross-checks **also removed** (the loader
  refuses them now, so the templates' prices.yaml load test would fail otherwise); "circulating from CoinGecko" text and
  the README supply/refusal paragraphs updated. T5 comment updated.

## Tests (RED -> GREEN)
- (a) RED: `npx vitest run tests/ingest/derived.test.ts` -> 5 failed / 23 passed (`unknown derived source "level_gap_pct"`,
  `levelGapPct` not exported). solana: 1 failed (`expected [...] to include 'solana.owners_balance'`); after registering,
  adapterOrigins 2 failed (no sample) -> added. GREEN: derived 28/28, solana+provenance 118/118.
- (b) RED: sources/proposals/tools -> 5 failed (filing accepted a coingecko circulating source, approve resolved instead of
  rejecting, parse returned '', loadAsset did not throw, `coingeckoIssues is not a function`). GREEN after the refusal; the
  "every shipped asset" pin went GREEN after the YAML sweep.
- Asset tests: each asserts its circulating adapter name and term count (or subtract list); the fixtures gained the new
  terms' values (task-4-values / scoping 2026-11-19/20 balances) and each fetch test asserts the computed circulating
  (fixture total less the live term figures), no CoinGecko call, and for CRV/LINK/PUMP the N5 metric values and an empty
  `watch` (CRV gap -0.363%, LINK ~0, PUMP first read). LINK/LIT report marketCap expectations moved to the on-chain basis
  (allowed: circulating feeds marketCap).
- Full suite: after (a) 2005/2005 (154 files), typecheck clean. After (b) first run 2003/2007: 3 real failures
  (tests/agent/context.test.ts LIT adapter_params list, tests/levels/levels.test.ts CoinGecko-ids test,
  tests/provenance/locator.test.ts circulating locator) fixed; tests/assets/sky.ingest.test.ts "reports both halves..."
  failed under load, passed alone (load-sensitive list). Final full run 2007/2007 (154 files); typecheck clean;
  `python3 -m unittest scripts/provision/test/test_orion_remote.py` 65 OK.

## Hash pins (only these moved; aero 80c32373... unchanged, verified before/after for all 13)
| asset | old | new | files |
|---|---|---|---|
| cake | e863393a | a4da1200 | tests/assets/cake.ingest.test.ts |
| crv | c25e7423 | 55b52e1f | tests/assets/crv.ingest.test.ts |
| cvxcrv | 5df3f844 | f792c7ab | tests/assets/lockers.ingest.test.ts |
| hype | 74c59b28 | d0142eb0 | tests/assets/hype.ingest.test.ts, tests/config/load.test.ts |
| link | 5fc85808 | f0994df5 | tests/assets/link.ingest.test.ts |
| lit | 7864c283 | 4f2495ba | tests/assets/lit.ingest.test.ts, tests/agent/disclosure.e2e.test.ts, tests/config/load.test.ts (3 hits) |
| pump | 9c0237ad | e5f4f6ac | tests/assets/pump.ingest.test.ts |
| sdcrv | 09a7ff1a | bb3a58da | tests/assets/lockers.ingest.test.ts |
| sky | 215dfdf1 | 33fda125 | tests/assets/sky.ingest.test.ts |
| uni | 5c1d9cf4 | 78c1f3e0 | tests/assets/uni.ingest.test.ts |
| vvv | 359d2868 | e3cc0536 | tests/assets/vvv.ingest.test.ts, tests/config/load.test.ts |
| ycrv | 9d7e62d3 | a3b3aa21 | tests/assets/ycrv.ingest.test.ts |
`grep -rl <old hash> tests` is empty for all 12 afterwards. No fixture file moved.

## Goldens
- tests/report/golden/v2-report-13.json: **did not move** (no report byte, no input hash).
- tests/agent/golden/packs-13.json moved; compared keyed by (metric, observed_at) / (metric, adapter), ids ignored:
  - adapter_params added: (circulating_supply, chain.view_sum) x10 assets, (circulating_supply, hype.circulating_supply)
    x1, (circulating_supply, solana.supply_less_owners) x1, (reserved_balance, solana.owners_balance) x1. No existing
    adapter_params entry changed.
  - observations_in_force added (seeded rows of the new monitor-only metrics): chainlink_circulating 1,
    circulating_gap_chainlink 1, circulating_gap_curve 1, curve_circulating 1, reserved_balance 1.
  - observations_in_force ids/order shifted in 3 assets (crv, link, pump) as a consequence of those rows; no existing row
    changed value, metric, time, status or source. Raw index-based flat diff: 374 leaf paths (194 `.id`, the rest the
    same rows shifted by index), all explained by the above.

## Concerns / for the controller
1. TERMS `api.coingecko.com` row removed from tools/sources-register/generate.ts (required by the generator once no asset
   reads it); the coingecko source type and `COINGECKO_API` code stay (R8).
2. Templates: the total_supply CoinGecko cross-checks were removed too (beyond "circulating examples"), else the loader
   refuses the templates in the repo root.
3. Test helper `PRICED_INGEST_ASSET_YAML` / `forPricedRoot` (tests/helpers/ingestAsset.ts) now also swaps the mini asset's
   CoinGecko circulating for `erc20_supply token - burn_sink`; tests/cli/ingest.cli.test.ts expectations moved from the
   `coingecko` source to `chain_levels`. `INGEST_ASSET_YAML` itself (no prices root) still carries CoinGecko sources.
4. Hourly load: circulating_supply is a non-monitor level, so the hourly levels job now reads it per asset instead of one
   batched /coins/markets call: HYPE 5 info posts (spotMetaAndAssetCtxs ~300 KB + 2x2 wallet reads), PUMP 7 Solana calls
   plus 6 for the watched `reserved_balance` (13/hour), LINK one 34-term multicall, the rest one multicall each.
5. level_gap_pct semantics chosen: writes every run (no dedupe), skip-with-note when a side is missing (no failure, so a
   missing check is visible only via the side's own source failure), extra rule that the gap metric be monitor_only.
6. Fixture realism: asset-test totals are the older recorded fixtures; the subtracted terms use 2026-11-19/20 figures, so
   the asserted circulating is fixture arithmetic, not a dated live figure. VVV: on-chain figure vs the captured Venice
   check (2026-09-19) is 1.4% apart, inside the kept 2% tolerance. LINK per-wallet values are the 2-dp figures (sum
   233,150,029.56 vs the file's 233,150,029.58 rounding).
7. Task 1-3 code: only the solana.ts helper extraction (behaviour unchanged, tests green); no evm.ts/hype.ts change.
