# SDD ledger — plan: docs/superpowers/plans/2026-11-19-orion-phase3-r3-circulating-supply.md

Go: Mike 2026-11-20 #orion-dev "all recommendations" (N1-N6, subagent-driven). Base 84cc9d2 (= GitHub main 06955e0 + plan docs).
Baseline at 84cc9d2 (npm ci in the worktree; no matching node_modules elsewhere): vitest 1977/1977 (154 files), typecheck clean.

## Pre-flight scan
| pair / task | shared | finding | ruling |
|---|---|---|---|
| T1/T2/T3 | sourceTypes.ts, sources-register generate.ts | same layer (ingest adapters), disjoint adapter files | R1 |
| T1-3 -> T4 | adapter names/params | T4 YAML consumes view_sum times/locked_schedule, hype.circulating_supply, solana.supply_less_owners | ok (Interfaces) |
| T4 N5 checks | derived metrics | no derived kind computes a gap between two levels (DERIVED_NAMES = burn_momentum, flow_annualized) | R3 |
| T4 PUMP check | schedule floor | needs schedule math vs a balance; dormant-vault movement is the sharper signal for option B | R4 |
| T4 values | addresses | scoping files elide PUMP vaults and LINK's 33 wallets | task-4-values.md (controller, verified) |
| T5 | source runner at a past block | SourceContext.block is the run block; rebuild must set it per row | R5 |
| T4 <-> T5 | rebuild_from YAML key | T5 adds `rebuild_from` under circulating_supply; AERO's value 2026-11-10 set in T5 (its YAML) | R6 |
| T6 | deploy.md, tools/phase3-proof | docs + stage scripts after T5's verb exists | ok, serial |
| T7 | controller | flatdiff ratio bound + proof | ok |

Ruling R1: Tasks 1-3 go to ONE implementer as three commits (one per task), one review over the range — same layer, disjoint files; shared one-line additions to sourceTypes.ts / generate.ts. — cost if wrong: a bigger review package.
Ruling R2: LIT `locked_schedule` is the plan's single-amount form (500M, one date series); the scoping's two-schedule form (team 260M + investors 240M, same dates) is equivalent and not built. — cost if wrong: none (same numbers).
Ruling R3: N5 WATCH checks need a new derived kind `level_gap_pct` {a: metric, b: metric} = (a/b - 1) x 100, monitor-only level, with `watch: { outside: [-tol, tol] }`; added to Task 4 (CRV a = circulating, b = curve_circulating monitor level from circ_contract.circulating_supply(); LINK b = chainlink_circulating via http_json). Gap expected CRV -0.36%, LINK 0.00%. — cost if wrong: small; a later generic check type replaces it.
Ruling R4: PUMP's N5 check is a monitor-only `pump_reserved_balance` level (supply_less_owners' subtracted sum, or a sum of owner balances) with `watch: { change_pct: 1 }`: a move in the custodian or a dormant vault is exactly what invalidates option B. The Blockworks schedule floor is not built (tell Mike). — cost if wrong: no floor alert; the change watch fires first anyway.
Ruling R5: rebuild runs the asset's configured circulating source through the normal source runner with a SourceContext whose `block` = firstBlockAtOrAfter(observed_at) (day_blocks cache), never a bespoke read path, so a rebuilt row = what a fetch at that block writes. — cost if wrong: none.
Ruling R6: `rebuild_from` (optional ISO day under a level metric, no default) is added and validated in Task 5 with AERO 2026-11-10; hash moves only for AERO in Task 5. — cost if wrong: AERO re-pinned twice (T4 doesn't touch AERO, so once).
Ruling R7: locked_schedule month addition = calendar months on the UTC day, clamped to the month's last day when the day does not exist (2027-01-29 + 1 month = 2027-02-28, + 2 = 2027-03-29). — cost if wrong: a tranche a day early in short months.
Tasks 1-3: dispatched as one implementer (BASE 84cc9d2), report task-1-3-report.md.
Tasks 1-3: committed 82dd4e4, 61e4c7d, 5a68aff; reported 1984 / 1991 / 1998 (154 files), typecheck clean. Controller verify: 3 commits on 84cc9d2; focused evm/hype/solana/packGolden 76/76; no hash pin moved; only golden move = packs-13.json AERO view_sum paramsDoc x2 (agent text).
Ruling R8: the packs-13.json paramsDoc move accepted (adapter doc text, no report byte) — cost if wrong: none.
Ruling R9: implementer extras accepted: locked_schedule refused with scale/plus_share; ADAPTER_ORIGINS solana.supply_less_owners onchain (origin.ts, needed by existing tests); HYPE >total refusal not added (plan: <= 0 only) — cost if wrong: a garbled API reply above total passes; WATCH/derived checks later.
Ruling R10: CRV gap watch band [-1.5, 0.5] (steady gap -0.36%, the treasury); LINK [-0.5, 0.5]; PUMP reserved owners via a minimal `solana.owners_balance` sum adapter + change_pct 1 (R4).
Tasks 1-3: review dispatched (review-84cc9d2..5a68aff.diff) in parallel with Task 4 implementer (BASE 5a68aff).
Task 4: dispatched (BASE 5a68aff)
Tasks 1-3: review clean (spec OK, quality Approved; 5 named risks pass; 135/135 focused).
Task 1-3: minor (deferred): solana.ts pump.fun host regex duplicated from the transport, plain Error not OrionError forbidden_price_host
Task 1-3: minor (deferred): isName defined three times (evm, hype, solana)
Task 1-3: minor (deferred): hype detail prints tiny spot balances in JS exponent form
Task 1-3: minor (deferred): solana supply and owner balances read at different slots (detail records each)
Task 1-3: minor (deferred): locked_schedule citation URL not in the sources register
Task 1-3: minor (deferred): view_sum with locked_schedule accepts exactly 0 (hype/solana refuse 0)
Task 1-3: complete (commits 84cc9d2..5a68aff, review clean)
Task 4: committed 94c6d04 + 596245b; reported 2005 / 2007 (154 files), typecheck clean, py 65. Controller verify: 12 old pins gone (cvxcrv 09a7ff1a, sdcrv 5df3f844 incl.), aero.yaml untouched, focused assets/config/levels/derived 344/344.
Controller live check (scratch home, branch src, schema r3probe_1795204385, dry-run fetch, 2026-11-20 19:53Z): all 13 ok, 0 anomalies, 0 watch; vs scoping cake +0.003% crv +0.011% cvxcrv -0.001% hype -0.029% link 0.000% lit +0.001% pump -0.068% sdcrv +0.001% sky -0.074% uni -0.012% vvv +0.148% ycrv -0.004% aero +0.403% (unchanged method, drift). CRV gap -0.3609%, LINK gap 0, PUMP reserved 418.26B. Results: workspace/orion/phase3-proof/r3/live-fetch-20261120/.
Controller: cleanup of the probe home/schema timed out on the approval prompt (not run; not retried; waits for Mike).
Task 4: review dispatched (review-5a68aff..596245b.diff) in parallel with Task 5 implementer (BASE 596245b).
Task 5: dispatched (BASE 596245b)
Task 4: review — spec OK, quality Approved with 1 Important (I1: watched monitor-only source exempt from failure streak -> LINK check silent) + M1-M6; task-4-findings.md items 1-4.
Ruling R11: PUMP watch metric name `reserved_balance` accepted (R4 said pump_reserved_balance) — cost if wrong: none.
Task 4: minor (deferred): ownersBalance resolves owners before validating (load-time check covers it)
Task 4: minor (deferred): schema.ts imports from the ingest layer (precedent in load.ts)
Task 5: committed 176c45a; reported 2021/2022 (156 files; the 1 = daemonSchema, caused by controller's leftover probe schema r3probe_1795204385), typecheck clean, py 67. Controller verify: only AERO pin moved (80c32373 old), focused supplyLevels/purge/cli/aero 39/39, py OK.
Ruling R12: rebuild target rule = row not from the current source when (source_type, locator.adapter, locator.call) differ; a params change inside the same adapter is not a target (AERO rows from 11-10 unchanged) — accepted — cost if wrong: a future same-adapter terms change leaves mixed history; a later release can add a params hash.
Ruling R13: a balanceOf term whose ARG contract did not exist yet reads 0 at an old block (correct: it held nothing); only a call ON a codeless contract is refused — accepted.
Task 4: fix wave dispatched (task-4-findings.md 1-4) in parallel with Task 5 review (review-596245b..176c45a.diff).
Task 5: review clean (spec OK, quality Approved; 5 named risks pass; real classification over 13 assets: 11 EVM rebuildable, HYPE/PUMP never, AERO split 2026-11-10).
Task 5: minor (deferred): rebuild writes midnight day_blocks without flow.ts's 3600 s age check (rebuild rows are past days; boundaries never young)
Task 5: minor (deferred): no tests for the rebuild conflict path, a partly committed --yes finished by rerun, a LIT locked_schedule rebuild at an old block, PUMP notRebuildable
Task 5: minor (deferred): RPC call counter counts 7 named methods only
Task 5: minor (deferred): planRebuild has an unused opts param
Task 5: minor (deferred): CLI NOT REBUILDABLE line says purge deletes it (true only for market_data rows)
Task 5: complete (commit 176c45a, review clean)
Task 4: fix wave committed 0b4132e (I1, M1 test-only: withRunCache already dedupes POSTs, M3 comments, M4); reported 2024/2025 (the 1 = daemonSchema env), typecheck clean. Controller verify: focused run/derived/pump/link 63/63.
Ruling R14 (narrows the I1 fix): un-exempt from the failure streak ONLY the sides (a/b) of a watched level_gap_pct; a plain watched monitor-only metric stays exempt as before. Why: 0b4132e also un-exempts LIT's four watched monitor-only sources (app_fee_share, rh account value, rh fees, staking apr) and PUMP's reserved_balance, an alerting change on assets/metrics R3 doesn't own (LIT); PUMP's owners are already covered by supply_less_owners' streak on the same RPC. The general "a watched read that fails is silent" gap goes to the followups note for Mike. — cost if wrong: LIT's watched sources stay as silent as today.
Task 6: dispatched (BASE 0b4132e) with R14 as its first commit; fix-wave re-review of 176c45a..R14 after.
Task 6: committed dc051b0 (R14, TDD) + 14f521a (deploy.md R3 block, r3-s0..s4.sh + --fake tests, followups, spec Status); reported 2024/2025 (daemonSchema env), typecheck clean, py 63 + 67 OK.
Controller (prod sql-ro 2026-11-20 20:50Z): VVV circulating row id 3 (2026-09-18, 48,350,000, disclosure, confirmed, active, pre-v2 seed without citation_url) — the R12 rule would make it a rebuild target.
Ruling R15 (amends R12): rebuild targets = active circulating rows with source_type market_data, or contract_state rows on the old erc20_supply locator (wrappers); disclosure / manual rows are never targets: listed as `kept` (id, observedAt, reason) and untouched; s0/s2 expect VVV kept 1. Why: Mike's N3 keeps the disclosure row; no CoinGecko data in it. — cost if wrong: one pre-v2 disclosed point inside VVV's on-chain series.
Ruling R16: Task 6 concerns 2-5 accepted as written (Task 7 creates r3-signed-circulating.json; stage levels every 6 h so s1 polls up to 6.5 h, deploy just before a :15 slot; staging_refresh hold until prod's s3; step-3 log check strict).
Task 5 M2 tests to add now (fix wave): conflict path, partly committed --yes finished by rerun, LIT locked_schedule rebuild at an old block, PUMP notRebuildable.
Fix wave (R15 + Task 5 M2 tests) dispatched (BASE 14f521a).
R15 fix wave committed ca3be1d; reported 2030/2031 (daemonSchema env), typecheck clean, py 65 + 67. Mutation checks confirm the M2 tests bite.
Ruling R17: implementer concerns accepted — contract_state targets keep R12's (adapter, call) comparison (only the wrappers on shipped data; scripts STOP on any other); non-target rungs kept, not notRebuildable; spec Status "R1-R14" updated by the controller at the closing commit.
Review dispatched over 176c45a..ca3be1d (Task 4 fix 0b4132e, R14 dc051b0, Task 6 14f521a, R15 ca3be1d).
Range review 176c45a..ca3be1d: quality Approved; spec gap Important (followups lacks R16/R17; spec Status says R1-R14) + M1-M6.
Ruling R18: closing fix wave = Important + M1 (s1 step-4 race: wait for a levels job that STARTED after the switch to finish; ignore running ones; read latest_levels only after it) + M2 (fixtures for the three artifact STOPs: wrapper old-locator count, leftovers after --yes, step-4 pre-check) + M3 (deploy.md: s1 needs the signed file, s4 the allowlist) + M4 (s2/s3 `--resume`: after a STOP mid --yes, rebuilt/purged-so-far + remaining == step 1's counts, documented) + M5 (followups: Task 5 M2 tests done in ca3be1d). M6 accepted as R16. — cost if wrong: none.
Closing fix wave dispatched (BASE ca3be1d).
