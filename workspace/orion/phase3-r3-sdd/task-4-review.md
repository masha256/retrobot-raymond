# Task 4 review (94c6d04 + 596245b on 5a68aff)

Read per file with `git diff 5a68aff..596245b -- <path>` (src/, assets/, tests/, docs/, tools/), in passes. Focused run:
derived, config/sources, adapters.solana, levels: 89/89 (`--maxWorkers=1`).

### Spec Compliance

- ✅ Spec compliant. Every file the plan's Task 4 lists has its hunk except `src/agent/tools/write.ts`. No change was
  needed there: filing and approve parse through `parseAssetObject` with prices, and the new tests pin that
  (tests/agent/tools.test.ts:357-360, tests/app/proposals.test.ts:286-298). R3 (`level_gap_pct`), R4 and R10 (bands
  [-1.5, 0.5] and [-0.5, 0.5], `solana.owners_balance`, change_pct 1) are built as ruled.
- ⚠️ Cannot verify from the diff: the live values (the controller's dry run already covers them). I also could not
  verify whether a `failed` status on CRV's shared `chain_levels` source (when `curve_circulating` reverts) affects
  anything beyond the streak. The same behaviour already exists for CRV's monitor-only `ve_power.*` reads.

### Named risks

1. **PASS.** All 22 named addresses and the 33 LINK wallets were compared by script against task-4-values.md: byte-exact.
   `nc_01`..`nc_33` are in order and are the only `nc_` keys. The YAML's 33 `-balanceOf(nc_NN)` terms are in order
   (link.yaml circulating_supply). `convex_treasury` is unchanged. The term lists match the values file asset by asset:
   - CAKE: 6 terms. CRV: 7 terms in the stated order. cvxCRV `wrapper.balanceOf`; sdCRV `gauge.balanceOf`.
   - yCRV: two `times: pricePerShare` terms. HYPE: subtract [hyper_foundation, community_grants]. LIT: 4 terms plus the
     locked_schedule, citation exact.
   - PUMP: six owners on both metrics. SKY: `mkr_sky.take`. UNI: 5 terms. VVV: 6 terms, check kept at 2%.

   Every new contract has a citation or evidence comment, and the existing subtracted entries got citations appended.
2. **PASS.** No `type: coingecko` is left in assets/ or docs/templates. The remaining mentions are `external_ids`,
   identifier-only notes and historical comments. Each refusal point has a test:
   - load: sources.test.ts:190-208
   - filing: tools.test.ts:357
   - approve: proposals.test.ts:286, both supply fields
   - cross-check: sources.test.ts:195
   - all 13 shipped assets, `coingeckoIds` = [] for both the hourly keys and every sourced metric: sources.test.ts:211-219
   - no CoinGecko call from runLevels: levels.test.ts:106-118
3. **PASS with a finding (I1).** Monitor-only is enforced (derived.ts:70). Each side must be a non-derived level metric
   and different from the other (derived.ts:72-82). Skip-with-note is acceptable for one run. But a side that fails
   every run is silent for LINK; see I1.
4. **PASS.** `supplyLessOwners` keeps Task 3's order: mint, then the subtract check, then name resolution before any
   request, then the host check, then supply, then owners (solana.ts ~90-100). Task 3's tests are unchanged and green.
   `owners_balance` uses the same `ownRpcUrl` (pump.fun refused before any request, tested) and `rpcUrl` (only
   `ORION_SOL_RPC_URL` or `rpc_url_env`). A 0 reading is allowed by run.ts:116 (monitor-only tokens).
5. **PASS.** Exactly the 12 old hashes were replaced. AERO's hash is not in the diff, and none of the 12 old hashes is
   still in src/ or tests/ at 596245b. v2-report-13.json is untouched.

   packs-13.json was compared keyed and with ids ignored: only additions, nothing removed or changed.
   - 13 `adapter_params` entries: the 12 circulating ones plus `reserved_balance`.
   - 5 seeded `observations_in_force` rows of the new monitor-only metrics (crv 2, link 2, pump 1).

   The ingestAsset.ts change is needed: a priced root now refuses the mini asset's CoinGecko circulating. The helper
   guard now also throws if `type: coingecko` survives. The CLI test now asserts `chain_levels` plus `not coingecko`.
   That is not weaker. The CoinGecko code path is still covered via `INGEST_ASSET_YAML` (unpriced root).
6. **PASS.** `levelMetricKeys` (levels.ts:95-100) drops derived and unwatched monitor-only metrics.
   - Hourly: the 12 circulating reads, plus PUMP `reserved_balance` (watched).
   - Nightly only: `curve_circulating`, `chainlink_circulating` and both gaps.

   Nothing is read twice through two sources, except that PUMP's six owners are read by both `supply_less_owners` and
   `owners_balance` (M1). That matches the report's 13 calls per hour. HYPE shares `spotMetaAndAssetCtxs` with
   total_supply (hype.ingest.test.ts post list).

### Strengths

- `level_gap_pct` is small and fully checked at load: unknown keys, missing or unknown sides, flow sides, derived sides,
  self-reference, a == b, and a non-monitor gap all have a test (derived.test.ts). The b = 0 case fails instead of
  writing Infinity.
- The gap carries provenance (`level_gap_pct@1` with both inputs) and is stamped `api` when either input is an API
  reading.
- The solana refactor extracts shared helpers without changing behaviour.
- The asset tests now assert computed circulating values, N5 values and an empty `watch`, not just shapes.
- The packs golden move is explained and checked keyed, not only by index.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
- **I1. LINK's N5 check can die silently (risk 3).** Needs a controller ruling.
  - Why it is silent:
    - `chainlink_circulating` is the only metric on source `http_json:https://supply.chain.link/supply`, and it is
      monitor-only. run.ts:696-701 therefore raises no failure streak for it.
    - The gap then skips with a note while its own source stays `ok` (run.ts:577-580).
    - The gap is monitor-only too, so even a failed gap raises no streak.
    - `staleness_days` is enforced nowhere: in src/ it appears only in schema.ts:12.
  - Effect: an API outage or a field rename means no WATCH and no anomaly, ever. The only trace is
    `fetch_runs.detail` and a `partial` outcome.
  - CRV is not affected the same way. `curve_circulating` shares `chain_levels` with non-monitor metrics, so 3 failures
    in a row raise a `source_failure_streak`. For PUMP, `reserved_balance` failures go with `supply_less_owners`
    failures (same owners), and those do streak.
  - Fix options: count a source as non-monitor in the streak rule when it feeds a watched metric or an input of a
    watched `level_gap_pct`. Or have a skipped gap mark its source failed, and stop exempting watched metrics from
    streaks. Either way, add a test: the side fails 3 runs in a row and a streak or WATCH is raised.

#### Minor (Nice to Have)
- **M1.** pump.yaml (`circulating_supply` + `reserved_balance`): the six `getTokenAccountsByOwner` reads happen twice
  per run, so 6 redundant calls an hour. This is cheap. A per-run owner-balance cache in solana.ts would drop it to 7.
- **M2.** R4 names the metric `pump_reserved_balance`; pump.yaml has `reserved_balance`. Either is fine; record it in
  the ledger.
- **M3.** The gap watches are evaluated only at the nightly run: derived metrics are excluded from the hourly keys
  (levels.ts:97). The crv.yaml/link.yaml N5 comments and report item (a) say it is written "every run" so the watch
  "fires on every fetch". That is true only for nightly fetches. Worth one clarifying word.
- **M4.** derived.ts:79 accepts a `constant` source as a gap side. It is harmless, but "read this run" suggests
  otherwise.
- **M5.** solana.ts `ownersBalance` resolves owners with a silent `typeof n === 'string' && …` guard before the host
  check. `supplyLessOwners` validates first. The asymmetry is harmless because `validateParams` refuses it at load.
- **M6.** schema.ts:3 is a config→ingest import (`levelGapIssues`). There is a precedent (load.ts:5), and derived.ts
  has no heavy dependencies.

### Assessment

**Task quality:** Approved (with I1 to be ruled on: fix now or log as a follow-up)

**Reasoning:** The values are exact, the CoinGecko refusal is complete and tested at all three points, and the pins and
goldens moved only as allowed. The one real gap is operational: a persistently failing first-party side of a
monitor-only check (LINK) produces no signal, because the monitor-only exemption from failure streaks also covers
watched checks.
