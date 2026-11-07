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
Task 0: re-review: I1 I2 I3 M1 M5 ADDRESSED, no new C/I. Task 0: complete (commits d614b08..ecfbe55, review clean after 2 fix rounds).
Task 0: minor (deferred): coverage check doesn't require the 13 named assets to be present in the run; get_path can't address ids containing '.'.
Task 1: review: spec compliant, quality approved, 0 C / 0 I / 5 M. Ruling R11: fix all 5 minors (M3 capture_rule required on measured to-holders below_line, M4 paid_metric double-read guard are behaviour; M1/M2/M5 test strength) before Task 3 relies on the schema — costs one small commit.
Task 2: implementer NEEDS_CONTEXT, nothing committed: disclosure.e2e LIT_HASH pin. Ruling R10: re-pin LIT_HASH (LIT's own asset pin; fixture unchanged).
Dispatch: one implementer, commit A = Task 1 minors fix (BASE eca4c4d), commit B = Task 2 (worktree changes kept) with R10 + crv capture_rule.
Task 1: fix round 2/5 committed 511c27d (M1-M5; mutation-tested 16 checks). Scoped re-review dispatched (eca4c4d..511c27d).
Task 2: committed 8f4cdc2 (suite 114/1250; assets/config/e2e 19/201 verified by controller; assets diff 0 removed lines; fixtures unchanged; only LIT_HASH line changed in disclosure.e2e).
Task 2 Step 5 (controller): built dist at 8f4cdc2, reports vs release f5f36fa on p2proof_20261104t214336z, D=2026-11-02: 13/13 legacy identical + anomalies + proposals PASS; asset validate crv/lit ok. Task 2: review dispatched (511c27d..8f4cdc2). Task 3: dispatched (BASE 8f4cdc2).
Task 1: re-review all M1-M5 ADDRESSED, no new breakage. Task 1: complete (commits ca1bc8e..511c27d incl. fc5587b, eca4c4d, 511c27d; review clean after 2 fix rounds).
Task 1: minor (deferred): paid_metric guard untested for share_metric/run_rate readers (both levels; unreachable by a flow).
Task 2: review spec OK, quality approved, 3 M. Task 2: complete (commits 511c27d..8f4cdc2, review clean).
Task 2: minor (deferred): statementShape tests pin ids/of only (parity proof covers values); disclosure.e2e preApprovalLitYaml replaces only first NOTE_NOW (latent).
G1 QUESTION for Mike (from Task 2 review M2): yCRV revenue (splitter gross) includes auctioned third-party vote incentives (~74% of yCRV flow per ycrv.yaml header), while sdCRV bribes go below the line under rule 3 — inconsistent; raise at G1 with figures.
Task 3: implementer DONE_WITH_CONCERNS b3b423d (suite 116/1303; parity.json 262 pairs).
Ruling R12: accept SKY 'protocol' pair excluded from parity (v1 residue ~-1e-10 vs v2 exact 0; rel tolerance can't compare) — costs nothing as long as SKY protocol is 0 by construction; reviewer to confirm.
Ruling R13: accept lit.unlocks_next_year -> third_party (reads DefiLlama emissions) — correct per rule 1.
Task 3 choices (perToken on net holder flow, dilution per token in USD, remainder/unreconciled = revenue - measured costs when a cost is n/m, below-line toHolders sums measured lines only) go to the reviewer as named risks and to Mike's G1 table notes.
R4 carry to Task 4 (consumers of report yield JSON / the in-process report): src/app/tick.ts -> summarizeHolderYield (in-process; must keep legacy fields), src/push/body.ts (legacy:true, P2), tools/import-sqlite/reports.ts (cutover proof compares report yield --json bytes across releases: needs --legacy on a v2 release or stays a pre-Phase-2 tool — document), docs/ops/deploy.md:136-148 (stage vs ref report yield cmp, same release both sides: fine, but update text), docs/ops/daemon.md:135 (orion-remote read-only verb list), docs/ops/hermes-daily-job.md (main/SQLite only; untouched).
Task 3: review dispatched (8f4cdc2..b3b423d). Task 4: dispatched (BASE b3b423d).
Task 3: review spec issues, quality needs fixes (0 C / 4 I / 8 M); rulings in task-3-findings.md (fix I1-I4, M1-M6, M8; M7 -> G1 note). Real-data check by reviewer: all 262 parity pairs bit-equal on p2proof schema, 5 days x 10 assets.
Task 4: implementer DONE_WITH_CONCERNS 30e3bde (suite 116/1329). Rulings task-4-rulings.md: C1-C3 accepted, C4 fix (catch v2 errors; alert line).
Task 3: fix round 1/5 + Task 4 C4 fix dispatched to one implementer (two commits, BASE 30e3bde). Task 4: review dispatched in parallel (b3b423d..30e3bde), findings go into a later round.
Early proof (controller) on 30e3bde (pre-fix), detached worktree, D=2026-11-02: 13/13 legacy identical + parity (262 pairs) + reclass PASS. v2 table saved v2-table-30e3bde-D20261102.tsv (AERO belowLine 0.00 -> null after I3).
Task 3: fix round 1/5 committed a66da00 (I1-I4, M1-M6, M8; parity 361 pairs). Task 4: review spec OK, quality approved, 3 M. C4 fix committed c7eed0e. Suite 117/1375, typecheck + lint clean (implementer).
Task 4 Step 5 (controller) on c7eed0e, detached worktree, D=2026-11-02, schema p2proof_20261104t214336z: 13/13 legacy identical + 361 parity pairs + 3 reclass PASS; no incomeStatementError. Checked: VVV revenue growth 11.83 (was null), AERO belowLine.toHolders null + notMeasured [bribes], CRV fromBelowLine 7.12. Table v2-table-c7eed0e-D20261102.tsv.
Task 4: minor (deferred): M2 Slack yields/multiples lines mix sources; M3 fragile CLI text assertion (cli.test.ts:1089).
ROLLOUT ITEM (controller-owned, outside repo): ~/.hermes/profiles/raymond/scripts/orion-stage-soak.py pick() reads legacy keys (flows, holderFlowGrowth, income.revenue) from orion-remote `report yield --json` — must pass --legacy (or read incomeStatement) before Phase 2 reaches staging (after cutover, P4). Task 4 M1.
G1 data: yCRV gross 91d via splitter = $560,940 crvUSD: voter (veCRV fees) 140,085 = 25%, fee_burner (auctioned vote incentives) 420,855 = 75% (Alchemy transfers, 93 days to head). Consistent-with-sdCRV treatment would make yCRV revenue ~0.56 $M/yr and move ~1.69 below the line.
Task 3+4 fixes: scoped re-review dispatched (30e3bde..c7eed0e).
Task 3/4 re-review: all ADDRESSED, no new C/I. Task 3: complete (commits 8f4cdc2..a66da00, 1 fix round). Task 4: complete (commits b3b423d..c7eed0e incl. 30e3bde, C4 fix).
Task 3/4: minor (deferred): M-a ratioOf drops disclosed growth for estimate/of lines on it (unreachable); M-b sourceLabelOf not given asset metrics (latent label); M-c listingBar uses third_party inheritance (consistent with M4); M-d 'missing day' flag also fires on a null cost level.
Controller rerun at c7eed0e: vitest 117/1375, typecheck ok, lint:promises ok, 0 leftover t_ schemas.
Task 4 Step 6: G1 table committed to followups note 2ae7416.
STOP at Gate G1 (R5). Proof schema p2proof_20261104t214336z and /home/hermes/.hermes/profiles/raymond/cache/scratch/p2rel kept for the next proof; cleanup.py after G2 work or if abandoned.
G1 (Mike 2026-11-04): go Tasks 5, 6, 7 (+ Step 5 rehearsal outside 05:00-06:30 PT), 7b yCRV option A, 9; stop at G2. R6 stands; listing bar as built; Task 3 defaults accepted.
Ruling R14: Task 7b apportions ybs_payout/treasury between revenue and below-line by the window's sender mix (derived) — per-source splitter ratios differ (87.3 vs 78.0 to YBS) — from-revenue holder flow slightly understated; error measured and noted.
Order: T5 -> T6 -> T7 -> T7b -> T9 -> final review -> G2.
Task 5: dispatched (BASE 32b42c5)
Task 5: implementer DONE_WITH_CONCERNS f5c62a3 (suite 1391/1392; the 1 failure = tools/disclosure-watcher test_final_wave clock-dependent, inherited from feat/daemon f5f36fa, fixed upstream in feat/daemon 48dcf2d "pin watch_since"; controller reproduced it on this branch).
Task 5 Step 4 (controller): fresh live snapshot -> p2proof_20261105t220843z (migrated by f5c62a3 dist, incl. 0003); reports old release vs f5c62a3, D=2026-11-03: 13/13 legacy identical + parity + reclass + anomalies + proposals PASS.
Task 5 checks evaluated read-only over the 91 days to 2026-11-03 (t5-checks-eval-D20261103.json): crv splitter 91 ok (max gap 0.00%); ycrv splitter 91 ok (0.03%); lit fees_core_revision 91 ok; cvxcrv crv_paid two_path 91 ok (max 2.77% < 5%); sdcrv crv_fee 90 ok + 1 BREACH 2026-08-31 (lhs $0.046 dust vs parts 0, gap 100%); price checks ok where readings exist (cake max 0.30%, link 0.41%, uni 0.94%), incomplete before ~10-10/10-15 (cross-check readings start then); lit parameter ok 12 / incomplete 79 (rh_revenue_share_app starts 10-23); link reserve_balance 91 incomplete (SQLite-era readings ~12:05 UTC, outside the 6 h boundary window: works only with the daemon's hourly levels after cutover).
DATA FINDING for Mike (G2): sdCRV dust breach ($0.05). Tolerance not loosened (plan stop rule); recommendation at G2: tolerance_abs $1 on sum checks.
Ruling R15: don't stop the run for the dust breach — it's a $0.05 data finding, not a code fault — record and raise at G2 — costs one advisory anomaly on that day if live before a decision.
NOTE: feat/daemon moved to f1d2a23 (48dcf2d watcher test pin; f1d2a23 load-prod --stdin, stagingRefresh.ts). Overlaps Task 4/5 files (docs/ops/daemon.md, deploy.md, tests/daemon/stagingRefresh.test.ts). Ruling R16: rebase feat/data-strategy onto the feat/daemon tip once, after Task 9 / before G2 report, then full suite + proof — avoids repeated conflict work mid-plan — costs one conflict-resolution pass (reviewed).
Task 5: review dispatched (32b42c5..f5c62a3). Task 6: dispatched (BASE f5c62a3).
Task 5: review spec OK, quality needs fixes (0 C / 2 I / 7 M). Rulings in task-5-findings.md: fix I1, I2 (days=3), M1, M5, M6, M7; defer M2, M3; M4 -> G2.
Task 5: minor (deferred): M2 price cross-check record matched by sourceId+label not contract; M3 UNI/LINK/CAKE price checks duplicate existing cross-check.
Task 6: implementer DONE_WITH_CONCERNS b594222 (suite 1415/1416, same inherited watcher test). Concerns: data set requires --citation; backfill rules beyond correction 1 (source_changed unmapped); latest_levels gain sourceType/locator; tx_count bigint.
Task 5: fix round 1/5 dispatched (BASE b594222). Controller: Task 6 Step 4 in detached worktree at b594222.
Release extract moved to durable /home/hermes/git/orion/.worktrees/rel-2026.11.04.2 (scratch copy was pruned after 24h); path in $TMPDIR/p2-rel.
Task 6 Step 4 (controller), detached worktree at b594222: fresh snapshot p2proof_20261105t224216z (migrated to 0004 by the new dist), reports old release vs b594222 D=2026-11-03: 13/13 legacy identical + parity + reclass PASS. db backfill-provenance --dry-run: 26,222 of 26,240 rows mapped (174 metric keys), 18 unmapped, all source=manual without citation: AERO flow_usd.fees 2026-09-10 (ids 11831 confirmed, 515 rejected: Mike's DefiLlama-artifact correction, mean of neighbours); VVV 16 rows from the 2026-09-18 research pass (ids 1-16; 5 burn rows rejected, 11 confirmed seeds of levels read on chain / Venice API / blog).
STOP-RULE item (plan Task 6): unmapped non-empty -> a rule for Mike, never a guess. Proposed rules (raise at G2; Task 7 doesn't depend on them, G3 NOT NULL is far later): (a) AERO correction rows -> method derived, formula 'manual_mean_of_neighbours@1', inputs = the 2026-09-09/11 rows, note kept; (b) pre-v2 manual seeds -> method disclosed, source_type disclosure, locator {note: source_detail, legacy_seed: true}, quoted_text = source_detail, citation_url null allowed only for code_version 'pre-v2'; (c) rejected rows mapped the same way (never read).
Ruling R17: continue to Task 7 with the 18 unmapped rows open as a G2 decision — no task depends on them before G3 — costs nothing if Mike picks different rules (backfill is re-runnable).
Task 6: review dispatched (f5c62a3..b594222).
Task 6: review spec OK, quality needs fixes (0 C / 1 I / 7 M). Rulings: fix I1 (bounded tx), M1, M2, M3, M4 (historical llama.fi api rows -> third_party), M5, M7; defer M6. data set --citation -> G2 sign-off.
Task 6: minor (deferred): M6 after a rollback N-1's latest_levels upsert leaves stale provenance.
Task 6 fix round queued behind the running Task 5 fix (no parallel implementers).
Task 5: fix round 1/5 committed dc1bfa6 (36/36 focused; suite 1421/1422 known watcher test). Scoped re-review dispatched (b594222..dc1bfa6). Task 6: fix round 1/5 dispatched (BASE dc1bfa6).
Task 5: re-review all ADDRESSED, no new C/I. Task 5: complete (commits 32b42c5..dc1bfa6, 1 fix round).
Task 5: minor (deferred): circular rule doesn't follow mixed derived-of-adapter chains (no wired check affected).
Task 6: fix round 1/5 committed 4a6540e (suite 1440/1441 known watcher test).
Task 6 Step 4 (controller) at 4a6540e on p2proof_20261105t224216z: REAL backfill-provenance ran: 26,222 mapped, 18 unmapped (same manual rows, G2); observations count+md5 over (id,value,source,source_detail,status) identical before/after (values unchanged); 0 locators matching key patterns; distribution measured/log_scan 17,739, measured/third_party 3,141, contract_state 2,254, first_party_api 1,400, market_data 714, disclosed/constant 598, derived 369, disclosure 7, null 18. Then reports (basis 'observations' path live): 13/13 legacy identical + parity + reclass PASS. Provenance shares e.g. LIT measured 1.0 first_party_api; HYPE measured 0.973 / derived 0.027, third_party api.llama.fi; VVV disclosed 1.0.
Task 6: scoped re-review dispatched (dc1bfa6..4a6540e). Task 7: dispatched (BASE 4a6540e).
Task 6: re-review all 7 ADDRESSED, no new C/I. Task 6: complete (commits f5c62a3..4a6540e, 1 fix round).
Task 6: minor (deferred -> final fix wave, security-cheap): scrub no longer covers x_cg_demo_api_key / x_cg_pro_api_key / x-api-key / auth_token / access_key / password / auth / authorization query names, object keys access_token / privateKey / apiToken, string-valued auth/headers keys (no current code produces them); 0x hex segment after /vN/ kept off keyed hosts; coingecko slice is a rebuilt {id, field} object.
Task 7: implementer DONE_WITH_CONCERNS e801bf3 (suite 1456/1457 known watcher test). Concerns: flow_usd_v uses prices <= 6 h old (accepted); yCRV vault-share members stored in underlying under coingecko:<id> ref (accepted, note); USD-native pre-0005 rows not backfilled (Ruling R18: fill amount=value, token_ref 'usd' in the final fix wave — trivial, keeps compare-usd honest); beyond-hourly = > 90 d before fetched_at (accepted).
Task 7 Steps 4+5 (controller) launched in background (proof-e801bf3, script $TMPDIR/p2-t7-rehearsal.sh): fresh snapshot at 0005, proof, backfill-tokens x13 one at a time (stops if a prod run is seen), compare-usd x13, proof again, scratch .env reduced. Started ~23:40 UTC (16:40 PT), clear of the 12:05-13:05 UTC prod window.
Task 7: review dispatched (4a6540e..e801bf3).
Task 7: review spec OK, quality needs fixes (0 C / 1 I / 7 M). I1 = flow_usd_v hour starts depend on session TimeZone (make_interval days=>1; DST day off by 1 h in non-UTC sessions). Local orion_dev TimeZone = UTC, so the running rehearsal's numbers are unaffected; prod/staging TZ not assumed. Rulings in task-7-findings.md (fix I1 + 6 minors + R18; accept unverified no-twin members).
Task 7: fix round 1/5 dispatched (BASE e801bf3) while the rehearsal runs on proof-e801bf3.
Task 7: fix round 1/5 committed 14f020e (I1 TZ fix reproduced RED: usd 215 vs 131 under America/Los_Angeles; suite 1466/1467 known watcher test). 0005 edited in place -> schemas migrated with the old 0005 are refused; the final rehearsal needs a fresh schema.
Task 7 Step 5 rehearsal (first attempt, e801bf3): proof PASS on fresh 0005 snapshot; backfill-tokens vvv (Base) ran ~19 min and reached 102 of ~220 days before the controller stopped it: Ruling R19: stop the rehearsal on superseded code and run ONE full rehearsal on the final commit (after 7b + rebase), outside the prod window — avoids spending Alchemy/Base RPC and keyless CoinGecko quota twice — costs nothing (no result from the partial run is used except timing: Base ~11 s/day for VVV's 3 members). Scratch .env reduced back to 2 lines; no backfill process left.
Task 7: scoped re-review dispatched (e801bf3..14f020e). Task 7b: dispatched (BASE 14f020e).
Task 7: re-review all ADDRESSED (I1, 6 minors, R18), no new C/I. Task 7: complete (commits 4a6540e..14f020e, 1 fix round).
Task 7: minor (deferred): backfillPrices may refetch an id for a ref with no day to fill; one contiguous range refetches stored hours between gaps; R18 uses current config's usdNative for history (same class as accepted M3).
Task 7b: implementer DONE_WITH_CONCERNS 54d3a47 (suite 1485/1486 known watcher test; apportion tests 18/18; python 43 OK).
Ruling R20: accept count_from [voter]/[fee_burner] on yearn_gross's scan instead of separate from_allowlist scans — fees + incentives = yearn_gross by construction (one scan, one pricing pass) — cost: a --metric backfill of the new flows rewrites yearn_gross rows; FIX in the final fix wave: `data fetch --metric` writes only the listed metrics even when the scan is shared (so the rollout backfill can't touch yearn_gross).
Accepted: apportioned growth uses the current window's mix for both windows (note for Mike); new series null until backfilled (rollout step: backfill both new flows, 100 days).
Task 7b: review dispatched (14f020e..54d3a47). Task 9: dispatched (BASE 54d3a47).
Task 7b: review spec OK, quality needs fixes (0 C / 1 I / 4 M). I-1: a below_line apportioned line could take a revenue metric as `by` (user-paid share below the line). Rulings: fix I-1, M-1..M-4.
Task 9: implementer DONE_WITH_CONCERNS cbf91c1 (templates 31/31, register 5/5; suite 1521/1522 known watcher test; nothing under src/ or assets/). Concerns -> followups/G2 notes: holder_flows still required (zero-payout protocols wait for Task 11), T3 Solana launchpad deferred until balance_delta (P3), register copies adapter default URLs, 13 of 15 sources' terms unknown (block only Phase 5 export).
Task 7b: fix round 1/5 dispatched together with R20 (--metric writes only listed metrics), two commits, BASE cbf91c1. Task 9: review dispatched (54d3a47..cbf91c1).
Task 9: review spec OK, quality approved, 0 C / 0 I / 6 M. Task 9: complete (commits 54d3a47..cbf91c1, review clean).
Task 9: minor (deferred): no drift test on copied adapter URLs; unknown adapter/derived names pass template test; no-URL test checks TERMS not generated output; fallback hosts (Base/Solana public RPC, pro-api.coingecko.com) not rows; CoinGecko note wording; 'date checked' on quoted rows. Plus T5 template line 37 contradicts 7b M-2 (gross_by_sender is an invariant guard) -> final fix wave.
Task 7b: fix round 1/5 committed b671400 (I-1, M-1..M-4; no pin moved: comment-only YAML) + R20 ad7ca84 (--metric writes only listed metrics; one test rewritten; suite 1524/1526: known watcher + gitPublisher timeout, passes alone 7/7).
Task 7b+R20: scoped re-review dispatched (cbf91c1..ad7ca84).
Rebase (R16): trial rebase of ad7ca84 onto feat/daemon f1d2a23 clean (28 commits); trial suite 131 files / 1527 tests ALL pass (watcher test fixed upstream), typecheck + lint ok. Applied to feat/data-strategy: ad7ca84 -> c9c51a1 (identical tree to the trial). Old shas in the ledger refer to the pre-rebase history (objects kept).
Task 7b: re-review all ADDRESSED (I-1, M-1..M-4, R20), no new C/I. Task 7b: complete (commits 14f020e..ad7ca84 pre-rebase, 1 fix round + R20).
Task 7b: minor (deferred): no test of an incremental --metric run on a group with a cursor; ycrv R20 test step 3 doesn't check listed members' active row count.
Final whole-branch review dispatched (f1d2a23..c9c51a1, 28 commits, 169 files) with ledger extract for minor triage.
Final review: ready for the G2 rehearsal; 0 C / 2 I / 7 M; triage table of all deferred minors in final-review-findings.md (must-fix: I1, I2, M5, two 7b tests; R15 + R17 -> G2). Controller rulings appended: fix I1, I2, M1 (note), M3, M4, M5, the two 7b tests, and the Task 6 scrub-coverage minors (missed by the extract); M2 = rehearsal parameter --backfill-days 183.
Final fix wave dispatched (BASE c9c51a1).
Final fix wave committed a8b937f + bec8a3d (suite 132 files / 1537 tests all pass, typecheck + lint clean; no YAML changed).
G2 items from it: orion-remote has no verbs for backfill-provenance / data fetch / backfill-tokens / compare-usd and its report yield doesn't pass --legacy -> runbook uses `sudo -iu orion-<env>`; decision for Mike: add remote verbs before release 2 or not. Soak script must read v2 fields over ssh. yCRV YAML comment still says 'by construction' (minor, followups).
Final scoped re-review dispatched (c9c51a1..bec8a3d). Final rehearsal launched in background on bec8a3d (script $TMPDIR/p2-final-rehearsal.sh; stops if a prod run is seen or after 11:30 UTC).
Final re-review: all FIX items ADDRESSED; M4 verified equal to v1 default days for all 13 (tsx comparison vs f1d2a23). Residual Important: docs/ops/deploy.md:249 runbook `O='... $HOME ...'` single-quoted, used unquoted -> every Phase 2 runbook command fails loudly (exit 1).
Parked — Ruling R21: no second fix wave (skill rule); the deploy.md quoting bug is a docs-only, loud-failing, must-fix-before-merge item surfaced to Mike at G2 (one-line fix: define O in double quotes or as a function) — costs nothing before merge; nothing deploys before the cutover (P4).
Parked: ycrv.yaml comment still says 'by construction' (comment only; followups).
2026-11-07 01:15 UTC: Mike: prod cutover done + other fixes deployed. origin/main = 895c8a1 (feat/daemon merged; prod releases orion-2026.11.05.1 = f1d2a23, orion-2026.11.07.1 = 895c8a1 Base 0.2 s block-time fix).
Final rehearsal (bec8a3d) died mid-run (process gone; last: backfill-tokens cvxcrv in progress). Results so far: ycrv by-sender fetch 183 d ok (193 s); backfill-tokens vvv rc=1 "could not locate the first block at or after 2026-11-06" = the Base block-time bug fixed in 895c8a1, not Phase 2; cake ok 890 s; crv ok 881 s. Scratch .env still held the 4 RPC lines after the crash -> reduced to 2 lines by controller now.
Rebased feat/data-strategy onto origin/main 895c8a1: bec8a3d -> f64d76b, clean; suite 132 files / 1538 tests all pass, typecheck + lint ok. P4 lifted (cutover done). Next: proof old side = orion-2026.11.07.1; deploy.md quoting fix (R21); rerun rehearsal.
