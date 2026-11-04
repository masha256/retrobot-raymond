# SDD ledger — plan: docs/superpowers/plans/2026-11-04-orion-phase2-data-strategy-income-v2.md

Setup 2026-11-04: worktree .worktrees/data-strategy @ d614b08 (feat/daemon f5f36fa + spec/plan). Card t_1697d7dc archived. npm ci in worktree (own node_modules, not the daemon symlink).
Ruling: own node_modules via npm ci instead of symlinking .worktrees/daemon/node_modules — daemon worktree belongs to the 1.5 cutover and may be removed — costs ~1 min per setup if wrong.
Baseline: vitest 113 files / 1207 tests passed (148 s, with ORION_TEST_DATABASE_URL); typecheck clean.

## Pre-flight scan (2026-11-04)
| Pair / task | Shared file or interface | Finding |
|---|---|---|
| T1 -> T2 | IncomeStatementDef schema -> 13 YAML blocks | T2 mapping uses of/paid_metric/run_rate/estimate/not_measured/capture_rule; all in T1 interface. OK |
| T1 -> T5 | src/config/incomeStatement.ts (T5 adds per-type check shapes) | T1 must leave IsCheck extensible (type + tolerance_pct + passthrough of per-type fields refused until T5?). Ruling R2 |
| T2 -> T3 | line ids per asset -> PARITY map | ids fixed by T2 table. OK |
| T2 Step 1 | st-yCRV probe needs RPC + .env | controller step. Ruling R3 |
| T2 Step 5, T4 Step 5, T5 Step 4, T6 Step 4, T7 Step 5 | cross-release proof (live .backup, proof schemas) | controller steps (plan Execution). OK |
| T3 -> T4 | incomeStatementV2 -> report/tick/format/body | OK |
| T3 -> T5/T6 | src/report/incomeStatement.ts edited again (checks, provenance) | sequential; OK |
| T4 | report yield --json default drops legacy keys | any in-repo consumer of the JSON (tools/disclosure-watcher, push body, scripts, docs/ops) must ask --legacy or use the in-process object. Named risk for T4 review. R4 |
| T6 -> T7 | flow.ts, apiFlow.ts, observations.ts written by both | sequential; T7 must keep T6 provenance on rows. OK |
| T0 | harness reads live .backup | implementer writes scripts + unittests only; controller runs Step 4 dry run. Ruling R1 |
| T8, T10, T11 | gated (G2/G3/G4) | not dispatched without Mike's go. Execution stops at G1 after T4. |
| Each task self-consistency | T1 hash pin c8cc4642... for MINI_ASSET_YAML must be verified present in tests | check at T1 verification |

Ruling R1: Task 0 code (scripts, test_compare.py) is written by an implementer with no live access; controller runs Step 4 (snapshot/import/reports dry run, cleanup) — keeps live .backup and proof schemas out of subagents — costs one extra round if the scripts fail on real data.
Ruling R2: Task 1's IsCheck accepts only the `sum` shape now (moved from reporting.income.checks, needed by T2 for crv/sdcrv/ycrv); other types are added by Task 5 — avoids T1 inventing T5 shapes — costs a small schema edit in T5 if wrong.
Ruling R3: T2 Step 1 (st-yCRV probe) is run by the controller before dispatching T2; the implementer gets the verdict — keeps RPC keys out of subagents — costs nothing if wrong (verdict is data).
Ruling R4: Task 4 reviewer gets named risk "every consumer of report yield --json that reads legacy keys passes --legacy" — D9 keeps legacy one release — a missed consumer silently loses fields.
Ruling R5: Stop at Gate G1 after Task 4 (Mike reviews the v2 table); T5-T7 proceed only on his go; T8/T10/T11 are separate gates — plan text — none.
Task 0: dispatched (BASE d614b08)
Ruling R6: st-yCRV fee probe = INSIDE YBS payouts (StrategyYBSFarmer holds 67% of YBS, takes 70% of distributor payouts); yCRV v2 revenue = yearn_gross only, styc fee left out of the v2 statement (no line), holder flow unchanged — see ycrv-styc-probe.md — if Mike prefers spec's alt (holders -0.10/protocol +0.10) it's a one-line YAML change + parity tweak.
Task 0: implementer DONE_WITH_CONCERNS 1735e10 (26/26 unittest; suite 113/1207). Controller dry run: snapshot+import proof ok (schema p2proof_20261104t214336z); reports FAILED 0/13 — old release side needs ORION_ENV_FILE. Task 0: fix round 1/5 dispatched (BASE 1735e10). Proof schema left in place for the rerun.
Task 0: fix round 1/5 done ca1bc8e (27/27 unittest). Controller dry run (old = release orion-2026.11.04.2 f5f36fa, new = branch dist, D=2026-11-02, schema p2proof_20261104t214336z): import proof ok, compare 13/13 identical + anomalies + proposals PASS. expected.py on old side: sdCRV rev 1.912, payout 0.471; LIT rev 51.894 cost 9.007 GP 42.886; yCRV rev 2.249, unreconciled -0.105.
Carry to Task 3/4 proof: expected.py's yCRV unreconciled uses legacy protocol incl. styc_fee; under R6 the v2 protocol excludes it, so expected yCRV unreconciled = revenue - ybs_payout - treasury (≈ -0.005). Fix expected.py in the Task 3 or 4 dispatch.
Note: figures on D=2026-11-02 differ from the spec's 2026-10-27 (LIT 49.27 -> 51.89 etc.): newer window, not an error.
Task 0: review dispatched (d614b08..ca1bc8e)
Task 1: dispatched (BASE ca1bc8e)
Task 0: review: spec FAIL, quality needs fixes (0 C / 3 I / 8 M); findings + rulings in task-0-findings.md.
Ruling R7: parity map = dotted-path pairs read by compare.py from both JSONs (Task 3 writes parity.json) — makes the proof check the actual report — costs a path-map file to maintain.
Task 0: minor (deferred): M2 only 2 .env lines compared; M3 $TMPDIR trusted; M4 out/homes not confined to $TMPDIR; M6 proof ok read by grep; M7 refusal paths untested; M8 P2_OLD_CONFIG unrequested.
Task 1: implementer DONE_WITH_CONCERNS fc5587b (20 new tests; suite 114/1227; no pin moved — verified tests/config+assets 18/167).
Ruling R8: strict unique line ids across sections (spec §6); Task 2 suffixes colliding revenue ids with `_rev` — keeps check parts unambiguous — costs renaming ~8 revenue ids in Task 2's table.
Task 0 fix round 2/5 + Task 1 fix (R8) dispatched to one implementer, two commits (BASE fc5587b).
Task 0: fix round 2/5 committed ecfbe55 (39 unittests OK); scoped re-review dispatched (ca1bc8e..ecfbe55).
Task 1: fix (R8) committed eca4c4d (21/21; tests/config+assets 18/168, no pin moved; suite 114/1228). Review dispatched (ca1bc8e..eca4c4d, src+tests).
Task 2: dispatched (BASE eca4c4d) in parallel with both reviews; rulings in task-2-rulings.md (R3/R6 probe done, R8 _rev renames).
Ruling R9: Task 2 runs in parallel with Task 1's review — schema findings get their own fix commit after — costs a possible re-touch of a few YAML lines if the review changes a key.
