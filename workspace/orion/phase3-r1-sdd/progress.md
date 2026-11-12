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
