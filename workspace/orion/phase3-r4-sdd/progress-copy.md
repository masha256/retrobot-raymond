# SDD ledger — plan: docs/superpowers/plans/2026-11-27-orion-phase3-r4-aero-pool-scan.md
Linear: RET-20
Execution: subagent-driven (Mike, 2026-11-27). Spec docs/superpowers/specs/2026-11-27-orion-phase3-r4-aero-pool-scan-design.md. Baseline d422944: 156 files / 2032 tests, typecheck clean. Controller notes also in ~/.hermes/profiles/raymond/workspace/orion/phase3-r4-sdd/ledger.md.

## Preflight scan
| pair / task | produces -> consumes | finding |
|---|---|---|
| T1/T2 | types.ts SourceContext, viemRpc.ts, run.ts: T1 adds rpcFor; T2 adds multicallData/getLogs/storedFlowDays/warnings | sequential, no conflict |
| T2/T4 | multicallData + getLogs -> ChainReader | consistent signatures |
| T4/T5 | ChainDayScan -> priceDay/valueScan | consistent; pricing does its own reserve/slot0/observe reads via ChainReader |
| T4/T6 | ChainReader, blocks -> incentives | consistent |
| T5 self | pricedPct definition circular (no reference value on chain) | Ruling below |
| T2/T7 | storedFlowDays, warnings -> adapters | consistent |
| T3/T8 | in_holder_flow, below-line started -> aero.yaml | consistent |
| T7/T9 | max_scan_days + backfill job -> r4-backfill.sh | plan said one --metric | Ruling below |
| T1..T10 self | each task's tests vs its code/files | consistent |

- Ruling: T5 pricedPct = priced USD / (priced + unpriced valued by a floorless 6-hop graph, coverage only) — the plan's text referenced final_eval.py's DEV-REF denominator, which live code cannot use — if wrong, coverage reads too high on fully off-graph dust pools (sizes ~$0-100/day in scoping).
- Ruling: T9 backfill passes all five metrics (job --metric is repeatable) and verifies by sql-ro row count instead of parsing run detail — if wrong, the script needs one more loop; no data risk.
- Ruling: stale anchor feed keeps spec behaviour (drop anchor, token falls to graph) plus an advisory warning — graph re-prices major anchors through others (USDC via WETH/USDC) — if wrong, a day with all stable anchors stale would price through ETH only (still bounded by the 95% gate).
Task 1 (RET-196): dispatched, BASE 0de5eb4
Task 1 (RET-196): implementer DONE_WITH_CONCERNS 289589e (2038 tests, typecheck clean). Concerns noted (observations): PRICE_RPC_ENV now 9 chains (no prices.yaml ref there); Elysium nativeCurrency placeholder; supplyLevels ctx lacks rpcFor (out of scope). Review dispatched (0de5eb4..289589e).
Task 1: review: spec OK, quality needs fixes. Important (plan-mandated) I1: rpcFor built on deps.rpcFactory, which callers wrap to record the fetch block -> another chain's latestBlock would overwrite block_number.
- Ruling: T1 rpcFor uses `deps.priceRpcFactory ?? deps.rpcFactory` (overrides the plan's "same factory" wording) — the plan's intent was the test seam, not block recording; the spec requires every other asset's stored values unchanged — if wrong, tests injecting only priceRpcFactory need the fallback (kept).
Task 1: minor (deferred): rpcFor duplicates makePriceDeps.rpcFor logic (drift risk)
Task 1: minor (deferred): rpcFor(assetChain) resolves CHAIN_RPC_ENV while ctx.rpc uses asset rpc_url_env (two transports)
Task 1: minor (deferred): new chain names lowercase vs 'Base' display names; viem 'Elysium' vs chains 'elysium'
Task 1: minor (deferred): Elysium nativeCurrency placeholder
Task 1: minor (deferred): PRICE_RPC_ENV now accepts 6 new chains silently; note it in writer.ts comment
Task 1: minor (deferred): run.test.ts registerAdapter at module load (beforeAll cleaner)
Task 1: fix round 1/5 (1 addressed, 0 open; commits 289589e..6eb0e96)
Task 1: complete (commits 0de5eb4..6eb0e96, review clean)
Task 2 (RET-197): dispatched, BASE 6eb0e96
Task 2: implementer DONE_WITH_CONCERNS 1172202 (2052 tests). Concerns: fakeRpc.logs dual shape; viem retries -32005 ~7s before halving; derived step origin via provenance throws no_provenance for rung-less adapter (none exist); range error regex. Review dispatched.
Task 2: review: spec OK, quality Approved, 0 Critical/Important.
Task 2: minor (deferred, FINAL REVIEW SHOULD FIX): M-1 rpc.ts:372 range-error regex also matches 429/rate-limit -> halving hides cause; anchor + test
Task 2: minor (deferred, FINAL REVIEW SHOULD FIX): M-2 run.ts:218 warnings dedupe per request not per run (chain-level key raised once per metric)
Task 2: minor (deferred): M-3 getLogs no guard on empty address list
Task 2: minor (deferred): M-4 adapterOrigins daily-series mismatch check tautological (real guard SERIES_API pin)
Task 2: minor (deferred): M-5 run.apiFlows afterAll leaves test adapter registered
Task 2: minor (deferred): M-6 seriesOriginOf throws no_provenance for rung-less adapter (stricter)
Task 2: minor (deferred): M-7 aggregate3 ABI defined twice (viemRpc, fakeRpc)
Task 2: minor (deferred): M-8 stray double blank lines
Task 2: complete (commits 6eb0e96..1172202, review clean)
Task 3 (RET-198): dispatched, BASE 1172202
Task 3: implementer NEEDS_CONTEXT (no commit): guard keyed on lines' started moves HYPE (reserve_yield started 2026-08-26) and LIT (robinhood started 2026-06-26) goldens: growth, holderFlow growth, pegTrailing -> null; window field on HYPE. TSV task-3-guard-golden-diff.tsv.
- Ruling: window label + growth guard opt-in via new optional statement key `history_start` (AERO sets 2026-10-22; HYPE/PUMP at R5/R6); without it statement byte-identical. Spec+plan amended (commit below) — spec's byte-identical constraint is binding and Q5's case is a whole statement starting at the merger, not one young line inside a full history (growthExNew already covers that) — if wrong, HYPE/LIT keep showing growth that includes a young line's ramp (today's behaviour), fixable by setting history_start or a per-line rule later.
Task 3: implementer DONE f5e63a8 (2062 tests, 65 goldens identical). Silent-brief choices for review: toHolders excludes in_holder_flow:false; such lines may omit bucket/haircut/...; below-line started refused with apportion; disclosed-level growth unguarded; history_start not checked vs started. Review dispatched.
Task 3: review: spec OK, quality Approved, 0 Critical/Important. Controller resolved ⚠️: (1) monitor_only via holderFlowMetrics skipping in_holder_flow:false lines — intended (protocol_subsidy is not holder flow); (2) only renderer of the statement header is src/cli/commands/report.ts statementLines (grep) — covered; (3) parity.ts aero pairs reference v1 'fees'/'voter_fees' -> carry to Task 8 (re-pair AERO parity; check toHolders = vote_incentives only).
Task 3: minor (deferred): guard note text duplicated report.ts:15 vs holderYield.ts:138
Task 3: minor (deferred): daysMeasured inline arithmetic incomeStatement.ts:1011
Task 3: minor (deferred): hs! non-null assertion incomeStatement.ts:567
Task 3: minor (deferred): missing tests: started+apportion refusal; pool_scan row with token columns
Task 3: minor (deferred): history_start doc should say disclosed-level growth unguarded
Task 3: complete (commits f102eb3..f5e63a8, review clean)
Task 4 (RET-199): dispatched, BASE f5e63a8
Task 4: implementer DONE_WITH_CONCERNS 0b7963f (2084 tests). Carry to T8: set Base log_range (else 216 getLogs/day at maxLogRange 2000); list Arc Lite V2 factories 0x9bc8…/0xaed2… (tape 0x8da0…) or factory drift daily. Carry to T7: checkRootChains needs Base day e-1 block. Choice for review: negative per-pool delta clamped to 0 + drift (not a failure). Gauge map via gaugeToTarget. Review dispatched.
Task 4: review: spec OK, quality needs fixes. I1: null reads (revert/decode) become benign values (s-1 accumulator null -> whole lifetime in one day; null allowedCaller -> unregistered silently; null s-1 pending -> 0; null gaugeToTarget -> gauge dropped) — violates "any RPC failure fails".
- Ruling: tape read = the factory's live poolTape()/clPoolTape() getter (spec §4.1 "the factory's own"), drift warn when it differs from config — reading config's tape after a migration would give stale/zero gross with only a warning — if wrong, a malicious/broken factory getter could point at a junk tape (still drift-warned, and Task 7 coverage/bound gates apply).
- Ruling: Task 7 fails the chain-day on negative_allocator and negative_gross (engine reports them as drift kinds; adapter treats as failures) — accumulators are monotonic and a negative allocator means missing logs — if wrong, a one-off tape reset day fails the run and needs a manual look (visible, not silent).
- Ruling: Task 8 sets log_range 1_000_000 for every chain except Ink (10_000) — scoping measured 1 getLogs/day on Base at full-day spans; Alchemy probe accepted >=1M on 5 chains — if wrong, getLogs halving recovers at the cost of extra requests.
Task 4: minor (deferred): two gauges on one pool overwrite (scan.ts:136-140)
Task 4: minor (deferred): CL factory hook optional -> hook drift skipped if omitted (types.ts:28)
Task 4: minor (deferred): rpc.requests assumes default chunk (scan.ts:38)
Task 4: minor (deferred): empty '0x' log data -> bare SyntaxError (scan.ts:270)
Task 4: minor (deferred): checkRootChains doesn't assert reader chain 8453 (scan.ts:224)
Task 4: minor (deferred): trim.py hard-coded home path
Task 4: minor (deferred): only allPoolsLength failure tested; negative_gross path untested
Task 4: fix round 1/5 (2 addressed, 0 open; commits 0b7963f..a8513af)
Task 4: minor (deferred, FINAL REVIEW SHOULD FIX): failed s-1 allPoolsLength still treated as 0 (scan.ts:92) -> all pools 'mid-day' -> s-1 pending null accepted for gauged unregistered pools; require s-1 length
Task 4: minor (deferred): report note on mid-day tape switch overstated (new tape deployed mid-day -> scan fails, safe)
Task 4: minor (deferred): failed swap-hook read shows as hook drift instead of failing (no number impact)
Task 4: complete (commits f5e63a8..a8513af, review clean)
Task 5 (RET-200): dispatched, BASE a8513af
Task 5: implementer DONE_WITH_CONCERNS a2f4d5f (2109 tests). Base 11-26 grossUsd 241,773.40 (-0.008% vs scoping spot; = Python TWAP ref). Choices for review: fake USDCs/LINK unpriced on real day (graph proven synthetic); e-1 ts via Multicall3 getCurrentBlockTimestamp; fallback uses TWAP; decimals()/balanceOf revert -> unpriced/zero depth (not fail); extra PriceBook fields. Review dispatched.
Task 5: review: spec OK, quality Approved, 0 Critical/Important.
- Ruling: tokenized-stock guard lives in Task 7 validateParams: an anchor's description must be one of a fixed allowlist of crypto/stable feed descriptions (ETH / USD, BTC / USD, WBTC / USD, CBBTC / USD, USDC / USD, USDT / USD, DAI / USD, USDS / USD, USDG / USD, EURC / USD, HYPE / USD) — pricing.ts trusts cfg.anchors and the spec forbids stock feeds as anchors — if wrong, adding a new legit anchor needs a code change (cheap, reviewed).
Task 5: minor (deferred): fallback off a slot0-spot edge not flagged (pricing.ts:211-218)
Task 5: minor (deferred): anchorsDropped token only; Task 7 builds text from config feed (pricing.ts:195)
Task 5: minor (deferred): spot used whenever observe() null, doc comment (pricing.ts:153-156)
Task 5: minor (deferred): balanceOf revert -> zero depth untested (pricing.ts:167)
Task 5: minor (deferred): test name says graph-priced while first half asserts unpriced (pricing.test.ts:37)
Task 5: minor (deferred): depth tie depends on pool order, comment (pricing.ts:229-241)
Task 5: complete (commits a8513af..a2f4d5f, review clean)
Task 6 (RET-201): dispatched, BASE a2f4d5f
Task 6: implementer DONE_WITH_CONCERNS d73cce9 (2122 tests). 11-26 class token amounts = program_days.json; USD = daily.json within $0.011. For T7: discoverVrms(+block), streamedDay(+subsidyCreators), result has ambiguous + rpc (ambiguous -> warning); registry mismatch fails discovery. Review dispatched.
Task 6: review: spec OK, quality needs fixes. I1: zero-supply branch of Z ignores the contract's lazy weekly backfill (supply hits 0 at a week boundary w on lock expiry; until a later checkpoint, Z counts [pt.ts,w) as zero) -> day w can exceed 86,400 zero-seconds -> pool_scan_inconsistent fails a legit state; start-bound overcount not flagged ambiguous; "e-1 is final" comment wrong. Fix round 1: mirror backfill with supplyAt(t_i - 1) per skipped week boundary.
Task 6: minor (deferred): dayStartSec/lc copied from scan.ts; `need` closure repeated (incentives/pricing/scan)
Task 6: minor (deferred): rpc.requests assumes default chunk; discoverVrms/programs report no rpc counts
Task 6: minor (deferred): blocks.s unused (incentives.ts:118)
Task 6: minor (deferred): 11-26 protocol_subsidy USD test compares 0 to 0
Task 6: minor (deferred): synthetic checkpoint ts -> real-data tests exercise t - pt.ts only on one OP point
Task 6 carry to T7: programs() once per run at latest day's e-1 shared by all streamedDay; pass scan.subsidy_creators; ambiguous -> warning.
Task 6: fix round 1/5 (1 addressed, 0 open; commits d73cce9..7588217)
Task 6: minor (deferred): failed-boundary-read test hits round-1 read first (run on day(w+86400)) (incentives.test.ts:342-347)
Task 6: minor (deferred): comment incentives.ts:29-33 overstates ambiguous-flag coverage
Task 6: complete (commits a2f4d5f..7588217, review clean)
- Ruling: Task 7 emits engine-level warnings (drift, coverage 95-99%, dropped anchors, spot_fallback) only from `pool.tape_fees_daily` with field `gross` (flow_usd.pool_fees_gross), and incentive `ambiguous` warnings only from class `vote_incentives` — Task 2's warning dedupe is per request (deferred M-2), so emitting from every metric would post each chain warning up to five times — if wrong, a warning shows only on the monitor metric's run (still in the nightly anomaly post).
Task 7 (RET-202): dispatched, BASE 7588217
Task 7: implementer DONE_WITH_CONCERNS 9fc9809 (2153 tests). Added param `since` (T8 must set since: 2026-10-22 on all five). needsRpc false (reads only via rpcFor). Chain-day with fees but zero priced fails. Missing window capped 90 d w/o --backfill-days. LP floored 0. Unpriced incentive tokens skipped+counted, no warning. Review dispatched.
Task 7: review: spec OK, quality Approved, 0 Critical/Important.
Task 7: minor (deferred, FINAL REVIEW SHOULD FIX): m1 pool.ts:236-241 days covered by a foreign (manual) row never count as stored -> rescanned every run; >=7 fill the cap and revision days never scanned (series freezes, source ok). Fix: exclude days any active row covers, or keep revision days outside the cap.
Task 7: minor (deferred): m2 'no fee priced' fails only at exactly $0 priced gross (pool.ts:188)
Task 7: minor (deferred): m3 programs re-read when a later metric's latest day is later (pool.ts:200)
Task 7: minor (deferred): m4 test comment vs assertion (programs block) adapters.pool.test.ts:68-70
Task 7: minor (deferred): m5 LP floor -> gross != alloc + lp by up to margin (pool.ts:342)
Task 7: minor (deferred): m6 double blank line
- Ruling: unpriced incentive tokens stay skipped (never imputed, spec §7) and the vote_incentives metric raises an advisory warning `pool_scan:incentives_unpriced:<chain>` when any are present; folded into final-review fix list — incentives are below the line (~$4K/day), so a low total is not a published-revenue risk, but it must be visible — if wrong, it's one more advisory anomaly.
Task 7 carry to T8: since: 2026-10-22 on all five metrics; sources-register TERMS rows for the six new chain RPC envs; re-check register regen.
Task 7: complete (commits 7588217..9fc9809, review clean)
Task 8 (RET-203): dispatched, BASE 9fc9809
Task 8: implementer DONE_WITH_CONCERNS f64cd38 (2154 tests; config hash 4f3d7c2f -> 41d417dd; only 5 aero v2 golden entries + aero pack moved). Concerns: parity AERO now shape test (v1 equality impossible); tier-A anchors only (Base HYPE left out); hook on main CL factories (+1 read/pool/day); AERO ingest test no 8-chain shaped scan; edits outside brief incl. syntheticReport.ts below-line started. Review dispatched.
Task 8: review: spec OK, quality Approved, 0 Critical/Important; scripted address check clean (104 addresses traced; factories = registries on 8 chains; anchors tier A, allowlisted, no stock feeds).
Task 8: minor (deferred): compare.py:52 still lists aero (fails by design); drop or mark expected-diff
Task 8: minor (deferred): '10 unchanged assets' wording parity.ts:405, parity.test.ts:2908
Task 8: minor (deferred, FINAL REVIEW SHOULD FIX): aero.yaml:90-91 cites ~/.hermes path; generator task-8-gen-scan.py uncommitted -> commit it under tools/phase3-proof/ and cite repo paths
Task 8: minor (deferred): aero.ingest test title overstates registry check
Task 8: minor (deferred): Base HYPE anchor excluded (revisit if Base coverage low at soak)
Task 8: minor (deferred): flaky daemonSchema timeout under load
Task 8: complete (commits 9fc9809..f64cd38, review clean)
Task 9 (RET-204): dispatched, BASE f64cd38
Task 9: implementer DONE 76bf9ee (2154 tests + live skipped; py 122 + 67 OK). Notes: acceptance --dl-stamp (raw api.llama.fi chart stamps D; prod stored rows stamp D+1 — controller measured both 2026-11-27); acceptance reads rows only; r4-backfill runs after deploy (purge refuses a configured metric).
- Ruling: rollout order = deploy, then export+purge flow_usd.fees, then backfill, then verify (overrides spec §6 order) — data purge refuses a still-configured metric; between deploy and purge the old rows are unread (no AERO metric reads flow_usd.fees) — if wrong, the AERO report for that window shows 0 days measured until the backfill's first chunk lands (minutes; stage first).
Review dispatched.
Task 9: review: spec OK, quality Approved w/ 1 Important (brief-mandated): r4_acceptance --dl-stamp default 'end' wrong for the raw api chart the docs say to save (stamps D) -> one-day shift, false FAIL.
- Ruling: --dl-stamp becomes required (no default), deploy.md names it with both conventions; live test's pricedPct assertion lowered to the adapter's fail gate (>= 95) — the D+1 default was my ruling from prod-stored rows, which this release purges; scoping Robinhood coverage 96.8% would fail a >= 99 assert while values are in tolerance — if wrong, an operator must type one flag.
Task 9: minor (deferred): tolerance is max(0.5%, $1) (noted)
Task 9: minor (deferred): deploy.md:128-130 timing parenthetical reads backwards
Task 9: minor (deferred): r4-backfill.sh:1082 ssh blip while polling -> rerun queues redundant job
Task 9: minor (deferred): r4-gen-scan.py bare asserts, module-level, open files
Task 9: minor (deferred): r4_acceptance.py mode 100644
Task 9: fix round 1/5 (1 Important + 2 folded minors addressed, 0 open; commits 76bf9ee..e73bcba)
Task 9: complete (commits f64cd38..e73bcba, review clean)
Controller: T9 Step 1 live golden run 2026-11-28 05:09Z (21:09 PT, outside forbidden windows): PASS 1/1 in 34 s, 8 chains; max |gap| Elysium gross -0.229% (9230.85 vs 9252); all others <= 0.15%. Log workspace/orion/phase3-r4-sdd/live-golden-2026-11-26.log (key masked).
Final review (2635cae..e73bcba): With fixes. C1 Elysium scanned from 10-22 but contracts deployed later -> first backfill chunk and every nightly fail. I1 incentives_unpriced warning never written. I2 FeesCollected keyed by VRM not indexed _gauge (latent double count). Triage: 0 MUST, 6 SHOULD, 51 LEAVE, 2 fixed.
Controller measurement 2026-11-28 ~05:25Z (eth_getCode binary search at each chain's 2026-10-22 s-1): every configured address on base/ethereum/optimism/arbitrum/ink/robinhood/arc (incl. Arc Lite, 14 addrs) has code at 10-22. Elysium: FactoryRegistry 0xdd17 first code 2026-11-07T13:07:42Z, LeafVoter 13:07:48Z, PoolTape 13:08:35Z, V2 factories 13:09:13-19Z, CLFactory 13:15:16Z, CLPoolTape 13:15:21Z, hook 13:15:29Z. Log workspace/orion/phase3-r4-sdd/chain-start-probe.log.
- Ruling: per-chain `since` in ChainScanSchema; Elysium since 2026-11-08 (first full UTC day after the 11-07 13:07-13:15Z deploy; DefiLlama also starts Elysium 11-08); chain-days before since count 0, recorded in the slice as not live; no null-s-1 exception anywhere (allPoolsLength at s-1 must be non-null) — keeps the T4 fail-closed rule simple — if wrong, Elysium fees for 11-07 13:15Z-24:00Z (pools hours old) are not counted.
- Ruling: T2 M-2 LEAVE (final reviewer: single emitting metric per key + cross-run dedupe); SHOULD list = M-1 rate-limit regex, two-gauges-one-pool drift, negative_gross adapter test, storedFlowDays foreign-row coverage, deploy.md timing wording; plus C1, I1, I2. One fix dispatch.
Final fix wave: 06d4d0b (8 items; 2165 tests; config hash 41d417dd -> 8b035228; packs-13 aero params_doc only; v2 golden unchanged). Scoped re-review dispatched.
Controller live probe at 06d4d0b, 2026-11-28 05:36-05:41Z (21:36 PT), adapters on AERO config with since=day: 10-22 gross 110,173.51 / alloc 99,259.23 (scoping 110,205 / 99,287), 10-23 163,605.46 / 148,010.93 (scoping 163,657 / 148,055); every chain within 0.1% of scoping; Elysium live:false before 11-08; 11-07 and 11-08 scan OK (Elysium live 11-08 with gross 0: all 8 gauged pools unregistered that day). ~25-29 s per day for 8 chains. Warnings: 14 Base gauged_unregistered (11-07/11-08; 0 by 11-26 per scoping), 8 Elysium gauged_unregistered (11-08), chain:8453:99901 (11-08, before root Voter listed Elysium) — advisory anomalies expected in the backfill. Allocator on Base gauged-unregistered pools: $8 (11-07), $6 (11-08), $0 (11-26): immaterial. Logs: workspace/orion/phase3-r4-sdd/live-days-probe.jsonl (+ probe scripts).
Final fix wave re-review: all 9 addressed, no new Critical/Important (2 minor doc nits: run.ts:287-288 storedFlowDays comment stale; scan.ts awkward sentence -> LEAVE, follow-up). Final review clean.
Task 10 (RET-205): proof started 2026-11-28 05:42Z: old = .worktrees/proof-old-2635cae (tag orion-2026.11.21.1, built), new = .worktrees/proof-new-06d4d0b (built); script workspace/orion/phase3-proof/r4/r4-proof.sh (copy, reports D/D-91, DL export dev-only, purge, backfill 5 metrics, reports, flatdiff empty allowlist, acceptance --dl-stamp end). Log proof-run.log.
Task 10 proof run 1 (copy p2proof_20261128t054207z, 195,157 rows/22 tables, sums equal): reports old/newpre ok; DL export ok; purge ok (fees rows 0); backfill FAILED all 9 runs: "chain 42161 2026-10-26: allocator $2534.38 exceeds gross $2189.50" (bound gate). Also harness bug: fetch exits 0 with outcome failed -> script must check outcome.
Diagnosis (controller probe, workspace/orion/phase3-r4-sdd/arb-1026-pools.json): 7 Arbitrum pools created 10-26, 6 gauged but NOT yet registered on the tape at e-1: tape gross 0, allocator $362 (205+61+40+37+19). Registration lags pool creation; fees before registration never reach the tape, but the gauge accrues its share. Registered pools: allocator == tape to the wei.
- Ruling: for a gauged pool unregistered at e-1, the day's gross = its allocator accrual (the measured lower bound of its fees; LP share of those fees unmeasured, counted 0), recorded per chain in the slice as `unregisteredAllocatorUsd`; the allocator<=gross bound then applies unchanged (it can only trip on registered pools) — spec §4.1 assumed unregistered pools carry no gauge fees; holder flow must keep the allocator's real fees and gross must not sit below them — if wrong, gross understates those pools' LP share (on 10-26 Arbitrum: unknown LP part of ~$362; $0 by 11-26).
T10 fix fddaa14 (allocatorAsGross in scan.ts; slice unregisteredAllocatorUsd; 2171 tests). Scoped re-review dispatched.
T10 fix re-review: ADDRESSED, no new Critical/Important. Out-of-scope: a pool registered mid-day whose gauge took fees before registration can still trip the bound (watch in proof re-run).
T10 proof run 2 (copy p2proof_20261128t061530z, 195,180 rows, sums equal): 10-26 now passes; backfill run 1 FAILED on Arbitrum 2026-10-27: allocator $2654.70 > gross $2021.99. Probe (arb-1027-pools.json): the same 5 pools were registered during 10-27; allocator includes their pre-registration fees (e.g. 0x14ce tape 141 vs allocator 538); every pool registered all day: allocator == tape (+-0.02).
- Ruling: extend the T10 rule to every gauged pool not registered at s-1 (registered during D, or still unregistered at e-1): its gross per token = max(tape delta, allocator accrual); pools registered at both s-1 and e-1 keep the tape and the bound — keeps the double-count guard meaningful for steady-state pools while crediting fees the tape never saw — if wrong, those pools' pre-registration LP share is uncounted (a few hundred $/day on Arbitrum 10-26/27; 0 once registered).
T10 fix 2: 112b441 (max(tape, allocator) for gauged pools not registered at s-1; preRegistrationCreditUsd; 2177 tests). Re-review + proof run 3 in parallel.
T10 fix 2 re-review: ADDRESSED, no new Critical/Important (minors: s-1 read uses e-1 tape; slice field rename; deregistered-mid-day unseen).
T10 proof run 3 PASS (copy p2proof_20261128t063741z, new 112b441, 06:37-07:07Z): backfill 6 runs ok, 37/37 days x 5 metrics; flatdiff empty allowlist: 12 other assets 0 diffs at D (2026-11-26) and D-91, both before and after the backfill; AERO 264 paths at D, 232 at D-91 (pre-merger AERO revenue now 0 by decision 1). Acceptance vs stored DL rows (--dl-stamp end): PASS 34/34 days 10-23..11-26, max |gap| 2.98% (10-29); 10-22 exempt (+21%). AERO at D: revenue 91.79M -> 99.45M (gross), holders 91.79M -> 90.11M (-1.8%), cash yield 20.70% -> 20.72% (vote incentives 0.41% added), protocol_subsidy 3.14M shown (not holder flow), window 36/91, growth + pegTrailing null (Q5). 61 advisory anomalies (50 gauged_unregistered, 9 spot_fallback, 1 chain:99901, 1 incentives_unpriced 0xb755... on Base 11-25..27). Allowlist fill waits for Mike's signature (test pins the skeleton).
