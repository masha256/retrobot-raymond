# Range review 176c45a..ca3be1d (0b4132e Task 4 fixes, dc051b0 R14, 14f521a Task 6, ca3be1d R15 + Task 5 M2 tests)

Requirements: plan Task 6, task-4-findings.md 1-4, progress.md R14-R17. Reports: task-4-fix-report.md, task-6-report.md,
task-7pre-fix-report.md. Read-only review: no edits or git state changes. The probes below ran in the scratch dir.

### Spec Compliance

- ❌ Issues found (one, docs only): the followups note does not have ruling R16 (R17 came after ca3be1d; see Important 1).
  Everything else in the brief is present: findings 1-4 (I1 later narrowed by R14; M1 is a test plus a comment, since
  withRunCache already dedupes the reads; M3 comments; M4 refusal), R14, the Task 6 block, scripts s0-s4 with `--fake`
  tests, the followups note, the spec Status line, and R15 with the Task 5 M2 tests.
- ⚠️ Cannot verify from the diff:
  - Section 7 asks for counts "measured on the proof copy (and on stage, for prod's block)". The table has the prod
    2026-11-19 scoping figures and a stage total only (437, deploy.md:1071). Task 7 (controller) should add the
    prod-copy per-asset counts and stage's s0 lines before prod runs.
  - The spec Status still says "Rulings R1-R14" (spec:15). R17 leaves that to the controller at the closing commit.
  - The real-mode ssh quoting depends on the forced command passing SSH_ORIGINAL_COMMAND straight to orion-remote's
    shlex. orion-remote:236-268 and 697-710 show that path. The implementer's stub-ssh check is not in the repo.

### Named risks

1. **deploy.md R3 block vs section 7: PASS.** The table (deploy.md, "Expected artifacts (section 7)") lists every
   artifact with its measured counts ("measured, not pinned: the scripts read step 1's file"), the step that clears
   it, and a re-check with no exemption:
   - `latest_levels` market_data 9: step 4 pre-check; cleared by the first hourly run; re-checked to 0 at step 4 post
     and again at step 8.
   - market_data rows (428, per asset): seen at step 5; cleared by steps 6 and 7; re-checked at step 5 after `--yes`
     and at step 8 (0).
   - The wrappers' old-locator rows (39 x3): cleared by step 6; re-checked to 0.
   - HYPE/PUMP/AERO-pre-11-10 rows: named as the only rows left after `--yes` (step 1's counts); cleared by step 7;
     step 8 shows 0.
   - VVV's kept disclosure row: every later check expects exactly step 1's count (1).
2. **Scripts: PASS, with test gaps (Minor 2) and one race (Minor 1).**
   - Counts: every count comes from expected.json. Only configuration is typed into the scripts: the asset list,
     CURRENT, NEVER_REBUILDABLE, REBUILD_FROM (r3_check.py:36-56). CURRENT matches all 13 YAMLs and sourceTypes.ts:34,39,52.
   - STOPs: each STOP exits 1 at once, in both the shell (`|| exit 1` / `stop`) and r3_check (`Stop` -> 1).
   - Pipes: there is no pipe of any kind, and test_r3_scripts.py:196 enforces "no `| head`".
   - s2 and s3 run dry -> checks -> `--yes` -> yes==dry -> re-checks in one script (r3-s2.sh:14-37, r3-s3.sh:15-35).
     test :115 asserts that all 13 dry runs come before the first `--yes`.
   - Quoting: `R sql-ro "'$q'"` (r3-lib.sh:76) reaches orion-remote as `sql-ro '<q>'`, one shlex argument. Queries use
     only `$$` literals, contain no backslash and no `;`, and are 504 chars, under MAX_COMMAND 8192.
   - Remote output: orion-remote appends `--json` to report, data purge, rebuild and jobs (orion-remote:442-484).
     Plain `status` prints `current: <readlink>`, which c_status parses.
   - D: s0 computes it once (c_days keeps an existing days.json, r3_check.py:171-183), and s4 reads it (r3-lib.sh:84-90).
   - s4 stops when `--tools` is missing or not a dir (r3-lib.sh:24), when flatdiff.py or r3-allowlist.json is missing
     (r3-s4.sh:12-15), and when a before/ file is missing.
   - Test run: `python3 -m unittest discover -s tools/phase3-proof -p 'test_*.py'`: Ran 65, OK.
   - Fixture coverage of the STOPs the block names:
     - Covered: md count at step 5; kept row not recorded (step 5 and the rebuild); refused rebuild; withoutReplacement
       mismatch; global market_data after the purge; latest_levels market_data after the hourly run; no levels run;
       signed file missing; allowlist missing; unallowed flatdiff path; expected.json / days.json missing; s0 rerun.
     - NOT covered: the step-4 pre-check count or asset mismatch; the wrappers' old-locator mismatch (step 5, and the
       re-check after `--yes`); leftovers at the step-5 re-check after `--yes`; the purge refusal (`error` JSON);
       latest_levels at step 8; yes != dry (rebuild and purge); the second dry run rebuilding > 0; ±2% vs signed;
       a failed levels job or failed source; s0's unlisted kind; the N6 usage64 / whoami checks; deploy, status, logs
       and migrations.
     - I ran r3_check directly on mutated fixtures (scratch) for: levels-pre with 8 rows, ycrv old-locator 1 at
       "rebuilt", purge `error`, same-rebuild mismatch, rebuild-again 40, cake +5% vs signed, s0 unlisted
       contract_state kind. All STOP with exit 1 and a correct message, so the gap is in the tests, not the behaviour.
3. **R14: PASS.**
   - run.ts:699-708: `exempt(k) = monitor_only && !watchedSides.has(k)`. watchedSides holds only the a/b of a
     `level_gap_pct` that has a `watch`.
   - LIT and PUMP have no `level_gap_pct` (only crv.yaml:88 and link.yaml:145 do). Their watchedSides is therefore
     empty, and the predicate reduces exactly to 176c45a's `keys.every(monitor_only)`.
   - The `derived:level_gap_pct` source writes the gap metric, which is not a side, so it is exempt again as on 176c45a.
   - Tests: derived.test.ts "raises none for a watched monitor-only metric that is no side of a watched gap" covers
     the LIT/PUMP class (`change_pct` watch, no gap) plus a watched side of an unwatched gap. The LINK-style positive
     case and the no-watch control are also there.
   - There is no asset-level LIT/PUMP streak test. None is needed, since the rule reduces to 176c45a's for them.
   - Focused vitest: derived, pump.ingest, supplyLevels, supplyLevels.cli, purge: 5 files, 79/79 passed.
4. **R15: PASS.**
   - supplyLevels.ts:107,165-168: TARGET_RUNGS = {market_data, contract_state}. Any other non-current row goes to
     `kept`, is never planned, and is untouched.
   - The VVV test asserts: kept on dry and on `--yes`; the row stays active at 48,350,000 as `disclosure`; both
     market_data rows are rebuilt; a rerun has the same kept list. The CLI test asserts the KEPT line, the JSON and the
     untouched row.
   - purge.ts is unchanged and only targets `--source-type market_data`, so it cannot touch kept rows.
   - r3_check's `kept` rule (r3_check.py:120-124) matches supplyLevels'. The scripts are stricter on contract_state
     rows of an unknown kind (they STOP), per R17.
5. **Followups note: FAIL (R16 missing).**
   - R1-R15 are present, and so are all 13 `minor (deferred)` lines (6 + 2 + 5, matched by hand: backticks differ).
   - N1-N6 are recorded, and the open item "A watched monitor-only read that fails is silent" is present (note:11-16).
   - R16 (Task 6 concerns accepted: Task 7 creates r3-signed-circulating.json, the 6 h stage poll, the staging_refresh
     hold until prod's s3, the strict log check) was ruled before the ca3be1d fix wave but is not in the note.
   - R17 postdates ca3be1d and is also absent.

### Strengths

- The I1 / R14 rule is a small pure predicate with a clear comment (run.ts:687-708). Its tests pin the positive case,
  the R14 negatives and the control, with the RED evidence recorded.
- R15 is minimal: one set and one branch. `kept` carries a reason, and the CLI, the JSON and the scripts all surface
  it. The Task 5 M2 tests are real DB tests: the conflict rollback, an interrupted `--yes` finished by rerun, LIT's
  block-time schedule, and PUMP with no RPC opened. The fix report records the mutation checks.
- The scripts are disciplined:
  - one `r3_check.py` subcommand per check, each documented;
  - expected counts only from step 1;
  - the `--fake` slug and override scheme lets each STOP be a fixture overlay;
  - every STOP test asserts that no `--yes` (or no call at all) was made;
  - no pipes, so there is no SIGPIPE risk.
- The deploy block's artifacts table is the clearest section-7 table so far, and it names the clearing step for each
  row.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
1. docs/superpowers/notes/2026-11-19-orion-phase3-r3-followups.md:56-86: rulings R16 and R17 are missing. R16 was
   ruled before ca3be1d was dispatched. The note claims to be the per-ruling record ("Source of every line below: the
   SDD ledger"), and R16 holds release-relevant choices: who creates r3-signed-circulating.json, the stage poll
   length, the staging_refresh hold, the strict log check. Fix: add the R16 and R17 lines, each with its cost if
   wrong, at the closing commit along with the spec Status "R1-R17" (spec:15).

#### Minor (Nice to Have)
1. The step-4 pre-check can race the first levels run (tools/phase3-proof/r3-s1.sh:40-42; r3_check.py:248-286).
   - `jobs` is read before `latest_levels`, and levels_job counts only ended jobs. So a levels run that is running,
     or that ends between the two reads, has already overwritten some rows, and the check STOPs (a false STOP, after
     the deploy).
   - deploy.md:1045 advises deploying stage "shortly before one of those slots", which makes this likelier.
   - It fails safe, but there is no documented way to resume s1 after a step-4 STOP: a rerun would deploy again.
   - Fix: skip the pre-check when any levels job on the tag has *started* (not only ended), or read jobs again after
     the levels query. Also document "after a step-4 STOP: run the post re-check by hand".
2. tools/phase3-proof/test_r3_scripts.py has no fake fixtures for these STOPs:
   - the step-4 pre-check;
   - the wrappers' old-locator count (step 5 pre, and the re-check after `--yes`);
   - leftovers at the re-check after `--yes`;
   - a purge `error` refusal;
   - latest_levels at step 8;
   - yes != dry (rebuild and purge);
   - the second dry run rebuilding > 0;
   - ±2% vs signed;
   - a failed levels job or a failed source;
   - s0's unlisted kind;
   - the N6 checks, deploy, status and migrations.

   The plan asks for "each artifact's exempt-then-zero path". The happy path covers each pass path, but for the
   wrappers' and the notRebuildable leftovers there is no STOP fixture. I checked that the code STOPs correctly
   (see risk 2). Add overlays for at least the three artifact STOPs.
3. docs/ops/deploy.md:1020-1021 says "s1 and s4 stop when either file is missing". In fact s1 checks only
   r3-signed-circulating.json (r3-s1.sh:13) and s4 checks only r3-allowlist.json (r3-s4.sh:15). Reword to say which
   script needs which file.
4. Neither deploy.md nor the scripts say how to resume after a STOP partway through s2's or s3's `--yes` loop. After
   a STOP there, a rerun of the same script STOPs at its first check, because step 1's counts no longer hold (correct,
   but a dead end). Add one line per script: what to run by hand, or "Mike decides; s0 again is not valid
   mid-release".
5. docs/superpowers/notes/2026-11-19-orion-phase3-r3-followups.md:101 still lists the Task 5 "no tests for the
   rebuild conflict path, ..." minor as deferred, but ca3be1d added all four tests. Mark it as done in ca3be1d.
6. r3_check.py:235: the `" error"` substring test on `logs 30` is strict (accepted by R16). Recorded only so the
   operator knows a benign "error" word causes a STOP.

### Assessment

**Task quality:** Approved (after Important 1, which is doc-only)

**Reasoning:** The R14 and R15 code changes are minimal, correct and proven by real-DB tests. The scripts honour every
named rule: counts from step 1, a STOP at the first deviation, one script per stage, the quoting, D saved once, and
s4's guards. The gaps are the followups note's missing R16/R17 and several STOP paths that the code handles correctly
but no fake test covers.
