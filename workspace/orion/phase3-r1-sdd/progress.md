# SDD ledger — plan: docs/superpowers/plans/2026-11-12-orion-phase3-r1-third-party-removal.md

Spec: docs/superpowers/specs/2026-11-09-orion-phase3-third-party-removal-design.md
Worktree: /home/hermes/git/orion/.worktrees/phase3 (branch feat/phase3-third-party). Base for code: e61d663 (plan commit) on main 763868e.
Mike's go: 2026-11-12 #orion-dev thread 1794489604.892539 ("Yep use sub agents"). Stop point: after Task 8, before tag/merge/deploy.
node_modules: `npm ci` in the worktree (live checkout's lock is older, no pg).

## Pre-flight scan

| Pair / task | Produces vs consumes | Finding |
|---|---|---|
| T1 -> T3 | `job run-now backfill <a> --metric (repeatable) --backfill-days n` vs remote `--metrics a,b` expanded to repeated `--metric` | consistent |
| T2 -> T3 | `data purge <a> --metric.. [--source-type] [--yes] [--json]` vs remote verb | consistent; remote must append `--json` like the other `data` verbs (R3) |
| T2 vs T4 | T2's test names `schedule.unlocks_next_year` (built in T4, later) | conflict -> R2 |
| T3 vs T8 | both edit deploy.md "Phase 3 R1 release" | overlap -> R4 |
| T4 Step 1 | needs web research (PUMP citation) | controller -> R5 |
| T4 -> T6 | adapter params vs LIT/PUMP YAML | consistent (tranches LIT, linear PUMP) |
| T5 -> T6 | `volume: { not_measured }` vs CAKE/UNI YAML | consistent |
| T6 vs T2 | rows to purge: LIT/PUMP unlocks rows are `third_party` today (ADAPTER_SOURCE_TYPES lit.unlocks_next_year) | consistent with `--source-type third_party` |
| T7 | needs prod over ssh + RPC-free scratch home | controller-run -> R6 |
| T8 Step 1 | profile script outside repo | controller -> R7 |
| T1 self | Step 4 "reapExpired fails a 1-attempt job" is existing behaviour; test pins it | ok |
| T1 self | "next nightly slot" needs the env's schedule; handler ctx carries env/paths | implementer finds the schedule source (src/daemon/schedule.ts) |
| T2 self | export dir `$ORION_HOME/purged` vs ctx paths | use ctx paths (home) | 
| T6 self | removed checks: no Phase 2 `checks` entry reads a removed metric (grep 2026-11-12: only volume + VVV cross_check reference them) | ok |

## Rulings

- Ruling R1: Code lands on `feat/phase3-third-party` itself (spec+plan branch), not a new branch — the Phase 2 pattern (spec, plan and code on one branch). Costs if wrong: none (branch rename at merge).
- Ruling R2: Task 2's tests use a synthetic fixture asset whose configured metric has a non-third-party source (e.g. `constant` or `contract_read`) to exercise `purge_live_source`; they do not depend on Task 4's adapter. Costs if wrong: none.
- Ruling R3: orion-remote's `data purge`/`data compare-usd` append `--json` (same as every other `data` verb). Costs if wrong: human-readable output over SSH instead of JSON.
- Ruling R4: Task 3 writes deploy.md "Phase 3 R1 release" with the one-time `orion-host.sh` re-run and the verb reference; Task 8 appends the per-env release block to the same section. Costs if wrong: none.
- Ruling R5: Task 4 Step 1 (PUMP citation research) is done by the controller; the implementer gets the url/quote in the dispatch. Costs if wrong: none.
- Ruling R6: Task 7 split — an implementer writes `flatdiff.py`, its tests and the allowlist skeleton (no execution against prod); the controller runs Steps 3-8 (prod copy, fetches, comparisons, purge and backfill rehearsal). Costs if wrong: none.
- Ruling R7: Task 8 Step 1 (profile parity file, soak cron prompt) is the controller's; the implementer does Steps 2-3 docs. Costs if wrong: none.

## Progress
- Baseline e61d663: vitest 1677/1677 (138 files) at --maxWorkers=2, typecheck clean, test_orion_remote 43 OK.
- Task 1: dispatched (BASE e61d663)
- Task 1: implementer DONE_WITH_CONCERNS a6c78d2 (1692/1692, 140 files; tc clean). Controller verify: 6 focused files 58/58.
- Ruling R8: Task 1 edits to tests/cli/db.cli.test.ts, tests/daemon/stagingRefresh.test.ts, tests/tools/importSqlite.test.ts, tests/release/orionRemote.test.ts accepted (migration count / kind-list pins 0007 forces). Carry to Task 3: remove the `backfill` exclusion in tests/release/orionRemote.test.ts when orion-remote gains the kind. Costs if wrong: none.
- Ruling R9: the extra guard (backfill also defers while a nightly began < 2 h ago, until slot + 2 h) is kept: it closes the hole where a backfill claimed at 00:46Z blocks that night's refreshes. Cost if wrong: a run-now between 00:45Z and 02:45Z waits until 02:45Z.
- Ruling R10: a queued backfill on a rollback to orion-2026.11.11.1 fails "no handler" with no retry: acceptable; deploy.md (Task 3) says drain/finish backfills before a rollback. Costs if wrong: one failed job row.
- Task 2: dispatched (BASE a6c78d2), in parallel with Task 1 review (review fixes get their own commit)
- Task 1: review: spec ✅, quality needs fixes: I-1 (guard reopens at slot+2h while nightly can still be pending), I-2 (partial fetch of a requested metric recorded as done). Findings + rulings in task-1-findings.md.
- Task 1: minor (deferred): M-1 message/codeOf copied from refresh.ts — export one copy
- Task 1: minor (deferred): M-2 ctx.signal not passed into fetch (lease loss keeps running; same gap as refresh)
- Ruling R11: M-3 (backfill run time unbounded) handled by documenting sizing in deploy.md (Task 3) + duration in the Slack line, no code bound — a hard timeout would discard a partly-written backfill. Cost if wrong: an oversized backfill delays one nightly.
- Ruling R12: Task 1 fix round 1 waits until Task 2's implementer finishes (one implementer in the worktree at a time); it lands as its own commit after Task 2's. Cost if wrong: none.
- Task 1: minor (deferred): M-4 job.ts:68 trim() checked but untrimmed string converted (correct result)
- Task 2: implementer DONE b31c224 (13 new tests; full 1704/1705, the 1 = tests/db/pg/migrate.test.ts OID race under load, 11/11 alone x2). Controller verify below.
- Ruling R13: Task 2's purgeMetrics taking OrionDb (src/db -> src/app/lock import) accepted: the lock must wrap the delete transaction; no cycle. Cost if wrong: a layering nit.
- Task 1: fix round 1 dispatched (BASE b31c224), Task 2 review dispatched in parallel (read-only).
- Task 1: fix round 1/5 (I-1, I-2, M-3 fixed; commit 8e3304f; backfill 9/9, full 1707/1707). Scoped re-review dispatched.
- Ruling R15: start line keeps the env prefix (`ORION BACKFILL <env> <SYM> started: ...`) like every daemon line, not the findings' exact text. Cost if wrong: a cosmetic mismatch.
- Task 2: review: spec ✅, quality needs fixes: I-1 export dir not fsynced. Findings + rulings in task-2-findings.md (minors 1-5 folded into the round).
- Ruling R14: latest_levels left after a third_party purge of a configured metric is handled by order (refresh before purge) in the release block (Task 8). Cost if wrong: a stale third-party level shown until the next hourly levels job.
- Task 2: minor (deferred): M-6 dead API-flow cursor (`defillama:...>metric`) of a configured metric kept after a third_party purge — note in followups
- Task 2: minor (deferred): M-7 tests/db/pg/migrate.test.ts "could not open relation with OID" flake under --maxWorkers=2 (passes alone) — known flake
- Task 2: fix round 1 dispatched (BASE 8e3304f)
- Task 1: re-review 1: I-1, I-2, M-3 ADDRESSED; no new breakage.
- Task 1: minor (deferred): RR-1 an orphaned unfinished refresh/report row of the newest slot defers every backfill silently until the next nightly
- Task 1: minor (deferred): RR-2 derived requested metric: an input source failure doesn't fail the job unless the derived source fails (no current config hits it)
- Task 1: complete (commits e61d663..8e3304f, review clean after 1 fix round)
- Task 2: fix round 1/5 (I-1 + M1-M5 fixed; commit de7f7e4; purge 18/18, full 1712/1712). Scoped re-review dispatched.
- Task 3: dispatched (BASE de7f7e4). Carries: R3 (--json), R4 (section skeleton), R8 (drop backfill exclusion in tests/release/orionRemote.test.ts), R10 (drain/finish backfills before rollback), R11 (sizing sentence).
- Task 2: re-review 1: I-1, M1-M5 ADDRESSED; no new breakage.
- Task 2: minor (deferred): RR-1 export file left in purged/ when the dir fsync fails (nothing deleted) — best-effort unlink
- Task 2: minor (deferred): RR-2 DB-dependent refusals (open anomaly, dangling ref) still run under the lock; a refused --yes may abandon orphaned agent runs
- Task 2: complete (commits 8e3304f..de7f7e4, review clean after 1 fix round)
- Task 3: implementer DONE e88130f (py 51/51, orionRemote 2/2, full 1712/1712, tc clean). Review dispatched; Task 4 dispatched in parallel (BASE e88130f).
- Task 3: minor (deferred): the nine-rung list in orion-remote is not pinned against TS SourceType (JOB_KINDS is)
- Task 3: review: spec ✅, quality needs fixes: I-1 rollback note (no drain verb; a running backfill makes rollback abort). Minors 1-5 folded into the round (task-3-findings.md).
- Task 4: implementer DONE 69caa3f (22 new; full 1735/1735; tc clean). Review dispatched with Task 3 fix round in parallel.
- Ruling R16: Task 4's 180 days (not the plan's "182") for linear start 2026-07-12 / 3y at now 2029-01-12 is correct under the plan's own rule (start + years x 365 d = 2029-07-11, 2028 leap); the plan's 182 was a controller arithmetic slip. Cost if wrong: none (test pins the rule).
- Carry to Task 6: tools/sources-register TERMS needs entries for x.com (Lighter's own post, first party) and blockworks.com (third party, compiled by Blockworks) once LIT/PUMP switch.
- Task 4: review: spec ✅, quality Approved; 0 Critical/Important; 7 minors.
- Task 4: minor (deferred): M1 the "tranche on now+365d counts; on now does not" test also passes with swapped window ends (only month-end test catches it) — strengthen
- Task 4: minor (deferred): M2-M7 originOf condition could be tighter; tranche loop duplicated with lit.ts (lit adapter retires in R8); a few validation tests missing; billions print as 50000.00M in detail; one test monkeypatches the shared registry; schedule_steps path has no citation guard (hypothetical)
- Carry to Task 7: on the prod copy, `select count(*) from observations where method='disclosed' and locator ? 'adapter'` must be 0 (Task 4 reviewer's prod-side check; my sql-ro attempt timed out on approval, not retried).
- Task 4: complete (commits e88130f..69caa3f, review clean)
- Task 3: fix round 1/5 (I-1, M1-M5; commit 6f97c21; py 52 OK, vitest 1735/1735, flake tests/push/gitPublisher.test.ts timeout once under load, 7/7 alone). Scoped re-review dispatched; Task 5 dispatched in parallel (BASE 6f97c21).
- Task 3: minor (deferred): flake tests/push/gitPublisher.test.ts "a moved remote is refused..." timed out once at --maxWorkers=2 (load-sensitive)
- Task 3: re-review 1: I-1, M1-M5 ADDRESSED; no new breakage.
- Task 3: minor (deferred): assert_refused per-word substring check could false-fail on short numbers (e.g. '1' inside argc '10')
- Task 3: complete (commits de7f7e4..6f97c21, review clean after 1 fix round)
- Task 5: implementer DONE 6a1c55f (6 new; full 1741/1741; tc clean; all 13 reports cmp-identical before/after). Review dispatched; Task 6 dispatched in parallel (BASE 6a1c55f).
- Ruling R17: Task 5's one-line `as string[]` cast in tests/assets/lockers.ingest.test.ts accepted (type widening). Cost: none.
- Carry to Task 6 (binding): drop the CAKE/UNI volume pairs from PARITY_PATHS (src/report/parity.ts) and regenerate tools/phase2-proof/parity.json; TERMS rows for x.com and blockworks.com; hash pins to re-pin (12 assets): cake 2f7d698f (tests/assets/cake.ingest.test.ts), crv 02417b36, hype f7dcfeec (+ tests/config/load.test.ts), link 6bc20338, lit a3e049f1 (+ tests/agent/disclosure.e2e.test.ts HASH, tests/config/load.test.ts), pump 3a2f142b, sky cef8a54b, uni e6316937, vvv fa05d392 (+ tests/config/load.test.ts), ycrv d594acfc, cvxcrv e9ecdb0d + sdcrv 0583401d (tests/assets/lockers.ingest.test.ts). AERO 3c413feb must not move. disclosure e2e: re-pin its LIT HASH constant only; fixtures must stay byte-unchanged (`git diff --quiet -- tests/fixtures`).
- Task 5: review: spec ✅, quality Approved; 0 C/I; 5 minors.
- Task 5: minor (deferred): refusal tests use bare .toThrow(); no committed mixed-form test; list typos give vaguer "Invalid input"; whitespace-only reason accepted (as statement lines); no doc of the new form
- Task 5: complete (commits 6f97c21..6a1c55f, review clean)
- Task 6: implementer DONE 35333a6 (1744/1745, the 1 = gitPublisher flake 7/7 alone; r1 test 6/6; register --check current). An orphaned earlier run showed context.test + packGolden red; controller rerun at 35333a6: 16 files / 275 tests incl. both, green. Full suite rerun in background.
- Ruling R18: Task 6's goldens rewrite (tests/report/golden/v2-report-13.json, tests/agent/golden/packs-13.json) accepted pending review: the R1 config change is MEANT to move CAKE/UNI volume, VVV cross-check and third-party provenance entries; the reviewer must confirm every moved path is in that set. Cost if wrong: a golden that hides an unintended move (Task 7's prod-copy proof is the second net).
- Ruling R19: Task 6's disclosure e2e rebuild of the 2026-10-23 lit.yaml (re-adds the old unlock adapter line and the two DefiLlama series in the test's copy) keeps the fixture's historical config; fixtures byte-unchanged. Cost if wrong: none.
- Task 6: controller full suite at 35333a6: 1745/1745 (144 files), exit 0.
- Task 7 (controller part): old side extracted to .worktrees/rel-2026.11.11.1/orion-2026.11.11.1 (sha256 202921ce.. ok, lock identical, node_modules symlinked to phase3). prod_copy started 22:23Z into $(cat workspace/orion/phase3-r1-sdd/copy-dir.txt); log workspace/orion/phase3-proof/r1/prod_copy.log.
- Task 7 (controller): prod_copy FAILED at the old release's `db migrate --json`: migration_breaking (0006 is `-- breaking`; prod_copy.py:241 migrates a fresh scratch schema without --breaking). Harness gap since 0006; nothing copied (fails before any read). Cleaned up (schema dropped, dir removed).
- Ruling R20: fix prod_copy.py to pass `--breaking` to the old release's migrate (the target is always a fresh p2proof_* scratch schema prod already passed), in a separate tools commit with a unit test, dispatched after the Task 7 tooling implementer returns. Cost if wrong: none (scratch only).
- Task 6: review: spec ✅, quality Approved; 0 C/I; 6 minors. Golden moves only cake/uni volume, lit buyback-check flag/provenance, vvv cross-check entries; packs: LIT/PUMP unlock adapter + seeded ids. (Reviewer saw suite log mid-run; the controller's run finished 1745/1745 exit 0.)
- Task 6: minor (deferred): misplaced doc comment parity.ts; one mis-indented test line; x.com register row keyed by host; comment rewrites dropped some calibration facts; a replay comment overclaims; coverage gap in r1-third-party.test.ts
- Carry to Task 7 (controller): CAKE/UNI/VVV default report day may move (no longer waiting on removed DefiLlama series) — run default-day `report yield` (no --day) old vs new on the copy and report the day per asset.
- Task 6: complete (commits 6a1c55f..35333a6, review clean)
- Task 7 tooling: implementer DONE 61e0425 (flatdiff 22/22; golden smoke: 9 assets 0 diffs).
- Ruling R21: LIT's +0.066% unlock change legitimately flows into yields.dilution, yields.netShareholder, holderFlow.netOfDilution, perToken.dilution, perToken.holderFlow.netOfDilution, perTokenFdv.*, and the unlocks line's yield / dilution.pct / dilution.tokensPerYear: all get rel 0.0007 entries (PUMP: same paths, rel 1e-12); supply.netPerYear gets abs 100000 tokens (a difference of two terms, LIT delta ~92k). Add a todo placeholder for incomeStatement.checks[...] too. Cost if wrong: a bound too loose by <0.07% on LIT dilution-derived fields.
- Tools fix dispatched: R20 (prod_copy --breaking) + R21 allowlist entries, one commit (BASE 61e0425).
- Tools fix: DONE 811d33f (py 120 OK). Ruling R22: the perTokenFdv.* glob is left unbounded-by-path at rel 0.0007; the controller reads every diff path flatdiff prints and treats any perTokenFdv revenue/grossProfit/holderFlow.total move as a stop (FDV doesn't move in R1). Cost if wrong: none (manual check).
- Task 7 (controller): build + prod_copy re-run started ~22:31Z.
- Task 7 tooling review (35333a6..811d33f) + Task 8 docs dispatched (BASE 811d33f).
- Task 8: implementer DONE_WITH_CONCERNS f0074f9 (release block; followups note with R1-R22 + 16 minors; spec Status bullet). Concerns: export-name wording in Task 3's verb reference (fix in tools round); no `db status` ssh verb (block checks deploy report applied [7] + deploys.log migrations=7) — Ruling R23: accepted. Cost: none.
- Task 7 tooling review: spec ✅, quality needs fixes: I-1 LIT dilution.* unbounded. Findings in task-7-findings.md.
- Task 7 tooling: minor (deferred): id-keyed list reorder / dict key reorder show no diff in flatdiff
- Task 7 tooling: fix round 1 dispatched (BASE f0074f9).
- Task 7 (controller) RESULTS on prod copy p2proof_20261112t223129z (120,316 rows / 21 tables, sums equal), D=2026-11-11, old = orion-2026.11.11.1, new = 811d33f dist (+0007 applied):
  - carry check: disclosed rows with an adapter locator = 0.
  - AERO cmp-identical. crv, cvxcrv, hype, link, sdcrv, sky, ycrv: 0 differing paths.
  - CAKE (9 paths) / UNI (6): only incomeStatement.volume.* (annualized -> null, notMeasured reason).
  - PUMP: 16 dilution-derived paths at rel <= 1.3e-14 (float: 82500000000.00008 -> 82500000000).
  - LIT: unlocks 138,796,789.02 -> 138,888,888.89 (+0.0664%); dilution-derived fields +0.066%; net-of-dilution fields +0.0729%; flags/provenance drop "holders.buyback.cross_checks". No revenue/holder flow/yield/price path moved; perTokenFdv revenue/grossProfit/holderFlow.total unchanged (R22 check passed).
  - VVV: business crossCheck removed; flags[3] + provenance sources[2] (third_party:api.llama.fi) + thirdParty entries removed. Nothing else.
  - default report day old == new for all 13 (carry from Task 6 closed).
  - new-home fetch: lit unlocks 138888888.8888889 disclosure/disclosed cited x.com; pump 82500000000 disclosure/disclosed cited blockworks.
  - purge rehearsal: dry-run counts = prod (cake 398/398, lit 191/191, uni 191, vvv 345, lit unlocks third_party 31, pump 29); --yes x6 exit 0; 6 export files; all 13 reports byte-identical before vs after the purge.
- Ruling R24: LIT net-of-dilution fields (4) bounded at rel 0.0008 and the real provenance/flags paths listed exactly; other assets' todo placeholders deleted (steered into the tools fix round). Cost: none.
- Ruling R25: brief Step 7 (local daemon backfill rehearsal) skipped: a scratch daemon would enqueue the schedule's newest slots (refreshes over the network, disclosure_watch -> possible paid analyst run, publish). The handler path is covered by Task 1's tests (claim/defer/fail/done); its first real run is on staging right after the deploy: 'ssh orion-stage job run-now backfill hype --metrics flow_usd.af_buys_direct --backfill-days 3' (keyless Hyperliquid). Cost if wrong: a backfill bug found on staging instead of the copy.
- Ruling R26: Task 8 Step 1: the soak script's parity compares only holder.gross/net, holder-flow growth and revenue.annualized (v2 vs v2), none of which R1 moves, so orion-phase2-parity.json needs no change; only the soak cron's "known queue" line gets updated on deploy day. Cost: none.
- Tools fix round 1 DONE ee295f6 (py 130 OK, -W error clean). Final flatdiff on the real copy outputs with the committed allowlist: all 12 exit 0 (cake 9/9, lit 20/20, pump 16/16, uni 6/6, vvv 8/8, others 0 diffs), aero cmp identical. Results in workspace/orion/phase3-proof/r1/out/. Copy cleaned up (schema dropped).
- Task 7: complete (tooling 35333a6..ee295f6; proof run by controller; scoped re-review of ee295f6 folded into the final review).
- Task 8: complete (f0074f9; concerns ruled R23; wording residue in followups note:16 + plan:48 -> final fix wave).
- Final whole-branch review dispatched (e61d663..ee295f6).
- Final review: ready-to-merge-with-fixes; 0 Critical; Important I-1 (release block order breaks step 6), I-2 (LIT abs bounds date-fragile), I-3 (unlock purge nulls past-day dilution), I-4 (default-day evidence incomplete in log); 3 minors to fix; 17 deferred minors fine to defer; R1-R26 sound (R21/R22 superseded).
- Ruling R27: the release block purges only the 4 orphan pairs by default; the LIT/PUMP third_party unlock purge is a separately gated step on Mike's pick (now, past-day dilution null ~4 weeks; or keep to R8). Cost if wrong: 60 third_party rows kept a while longer.
- Final fix wave dispatched (BASE ee295f6), findings in final-findings.md.
- Final fix wave DONE c0e4750 (py 134 OK; flatdiff on real outputs 12/12 exit 0, aero cmp identical). No src/assets/tests change since 35333a6 (suite 1745/1745 stands). Scoped re-review dispatched.
- Final re-review: all ADDRESSED, 0 new C/I; N1-N4 wording minors -> followups note (e95550d). Branch pushed: GitHub feat/phase3-third-party = e95550d (ls-remote confirmed). STOP point: no tag/merge/deploy.
- RELEASE (Mike 2026-11-12 "Recommendations approved, go for next step"; R27 = (b) keep LIT/PUMP third-party unlock rows until R8):
  - 8f50ac6 (docs N1-N4 + R27 decided) pushed: GitHub main = feat/phase3-third-party = 8f50ac6 (ff from 763868e; ls-remote confirmed); origin/gh main update-ref'd.
  - tag orion-2026.11.12.1 (annotated cbc9859 -> 8f50ac6) pushed, ls-remote confirmed.
  - build.sh: 1745/1745 (144 files) = ledger baseline at 35333a6; tgz sha256 3135b60b...; RELEASE schema 7.
  - provision snapshot /home/hermes/orion-provision-8f50ac6 (git archive scripts/provision) for Mike's orion-host.sh re-run.
  - stage step 0 (before/) saved 23:29Z; deploy.sh stage orion-2026.11.12.1 23:30Z: migrations applied 7, registry no change; status current 2026.11.12.1, daemon heartbeat on tag.
  - stage step 3: aero cmp identical; 12 assets flatdiff exit 0 (cake 9, lit 4, uni 6, vvv 8 allowed; others 0).
  - soak cron e2fb64f34263 resumed, catch_up false, next 2026-11-13 06:30 PT; prompt "Known queue" updated for R1.
  - BLOCKED: step 5 `job run-now refresh lit/pump` command timed out on approval (not run, not retried). Waiting on Mike: approve step 5; orion-host.sh re-run (steps 4, 6 need the new verbs); purge --yes go after dry-run counts.
- 2026-11-13: Mike re-ran orion-host.sh (--hostname venus --pg-datadir ... --ssh-from 192.168.0.0/24 --ssh-from 100.64.0.0/10 --with-watcher --enable-backups; no deploy-key/recipient/deadman flags: persisted): SELF-CHECK 57/0. Its daemon restart at 06:15:30Z cut stage levels job 425661 (lease_expired, ORION RESTARTED line); 12:15Z levels done. New verbs confirmed (backfill bad metric -> exit 64).
- Stage soak: nightly 2026-11-13T02:45Z on orion-2026.11.12.1 done, no failed sources (status soak line). The nightly's LIT/PUMP refresh did step 5: lit unlocks 138888888.8888889 cited x.com, pump 82500000000 cited blockworks (data show).
- Step 4 smoke backfill: job 443162 hype flow_usd.af_buys_direct 3 days: started 14:22:13Z, done 14:22:21Z, written 0 (no revised day). mid/ saved after it.
- Step 6 stage purge dry runs: cake fees 396 / llama_revenue 396; lit 192/192; uni swap_fees 189; vvv revenue_proxy 343 (all orphans; 1 cursor each). Waiting on Mike's --yes go.
- Mike "both approved" (stage purge --yes + prod deploy).
- Stage purge --yes x4 14:24-14:25Z: cake 396+396, lit 192+192, uni 189, vvv 343 deleted = dry runs; exports ~/home/purged/{cake-flow_usd.fees+1-20261113T142455Z (sha 5a9831a4..), lit-flow_usd.fees+1-20261113T142500Z (c3f201ce..), uni-flow_usd.swap_fees-20261113T142503Z (b0282b10..), vvv-flow_usd.revenue_proxy-20261113T142506Z (20fd3b02..)}.json on stage. Step 9: all 13 reports identical to mid/.
- PROD: step 0 before/ 14:25Z; deploy.sh prod orion-2026.11.12.1 14:26Z: SOAK OK (stage nightly 2026-11-13T02:45Z, no failed sources), migrations applied 7, registry no change; daemon on tag. Step 3: aero cmp identical; 12 flatdiff exit 0 (cake 9, lit 4, uni 6, vvv 8, others 0). Soak cron e2fb64f34263 paused (stage == prod).
- Prod step 5: refresh lit 321937 / pump 321938 done; lit unlocks 138888888.89 cited x.com, pump 82500000000 cited blockworks; mid/ saved.
- Prod step 6 dry runs: cake 400/400, lit 192/192, uni 194, vvv 347. Waiting on Mike's prod --yes go.
- Mike "prod purge ok". Prod purge --yes x4 14:31Z: cake 400+400, lit 192+192, uni 194, vvv 347 deleted = dry runs; exports on prod ~/home/purged/{cake-flow_usd.fees+1-20261113T143128Z (1065be95..), lit-flow_usd.fees+1-20261113T143134Z (25251a40..), uni-flow_usd.swap_fees-20261113T143137Z (a86cec61..), vvv-flow_usd.revenue_proxy-20261113T143139Z (5a2c78c6..)}.json. Step 9: all 13 prod reports identical to mid/. R1 RELEASE COMPLETE on both envs. Open: watch prod's first nightly on the tag (2026-11-14 00:45Z) and first levels/snapshot_push; next plan = R2 (price swap).
