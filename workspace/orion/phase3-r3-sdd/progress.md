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
