# Task 6 report (R14 + release block, stage scripts, followups)

BASE 0b4132e. Two commits on `feat/phase3-r3-supply`:

- `dc051b0` fix(ingest): only watched gap sides leave the monitor-only streak exemption (R14)
- `14f521a` docs: Phase 3 R3 release block, stage scripts s0-s4, followups

## Commit A: R14 (TDD)

`src/ingest/run.ts`: `exempt(k) = monitor_only && !watchedSides.has(k)`. The `watch === undefined` clause from 0b4132e is
gone, so only a side (a or b) of a `level_gap_pct` that has a watch leaves the monitor-only exemption. The comment names
LIT's app_fee_share and PUMP's reserved_balance as staying exempt.

`tests/ingest/derived.test.ts` (the "failure streak of a source that feeds a watched check" block):
- kept: the LINK-style test (a side of a watched gap failing 3 runs raises the advisory streak on the third run);
- kept: the no-watch control (none);
- replaced 0b4132e's "own watch raises it" with `raises none for a watched monitor-only metric that is no side of a
  watched gap (Ruling R14)`. It covers (a) a watched monitor-only metric with no gap metric at all (base YAML plus the issuer
  metric with `watch: { change_pct: 1 }`): `[[], [], []]`, which is 176c45a's behaviour; and (b) its own watch on a side of
  an unwatched gap: also none.

RED, before the run.ts change: `× raises none for a watched monitor-only metric ... (Ruling R14)`. It expected
`[[],[],[]]` and got a third run with `"http_json:https://issuer.test/supply advisory"` (1 failed / 30 passed).
GREEN: derived + pump/link/lit ingest + run tests 71/71.
Full suite: 2024/2025 (156 files). The one failure is `tests/db/daemonSchema.test.ts > 0002_daemon > schema: every 0002
table exists in schema orion`, the known environmental failure (the controller's leftover probe schema). Typecheck clean.

## Commit B: docs and scripts

1. `docs/ops/deploy.md`: new "## Phase 3 R3 release", placed after R2's block and before "The ssh verbs". It has:
   - the prerequisites: Task 7 signed, and the tag carries `r3-allowlist.json` and `r3-signed-circulating.json`. N6: stage
     sql-ro has existed since 2026-11-20 (`orion_stage_ro`), and one more orion-host.sh re-run adds
     `data rebuild-supply-levels`. Its check is exit 64 plus the usage line, and `sql-ro select current_user`. Then merge
     and tag, and stage first;
   - the timing: the PT window and each env's nightly -4h/+2h; no nightly between s0 and the switch; D = today-2 saved
     once; staging_refresh; the stage 6-hourly levels slots;
   - the s0-s4 commands, plus prod's go rule (one go per script, and dry-run checks run before any `--yes`);
   - an artifacts table in section 7 form. It lists the latest_levels market_data rows (9), the market_data rows (aero 45,
     cake 40, crv 43, hype 55, link 37, lit 38, pump 37, sky 36, uni 40, vvv 57 = 428; stage 437 at 2026-11-20) and the
     wrapper old-locator rows (cvxcrv/sdcrv/ycrv 39). For each it gives the check that sees and exempts it, the step that
     clears it, and the unexempted re-check. All are marked "measured, not pinned: the scripts read step 1's file";
   - steps 0-10 grouped as in the plan, then the soak and rollback per the plan.
   - The verb reference already had `data rebuild-supply-levels` (Task 5) and `data purge`, so nothing was added there.
2. Scripts in `tools/phase3-proof/`:
   - `r3-s0.sh` .. `r3-s4.sh` (bash, `set -u`, `<env>` plus `--fake <dir>`; s1 takes `<tag> --tools <dir>`, s4 takes
     `--tools <dir>`);
   - `r3-lib.sh`, the shared part: argument parsing, `R` (ssh with the env key), `Q` (sql-ro with the query passed as one
     single-quoted argument and `$$` literals), and fake mode. The slug rule is in its header comment: words joined by
     `_`, characters outside `[A-Za-z0-9._=-]` turned into `-`, and a sql-ro call becomes `sql-ro_<query name>`. Per-call-
     number and per-script override files are allowed, plus `.exit` files. Calls are logged to calls.log, and `R3_NOW`
     fixes "now";
   - `r3_check.py`: the checks, one subcommand each, stdlib only. Expected counts come only from `expected.json`.
   - Work dir is `~/r3-<env>/{before,after,dry,yes}`. s0 writes `days.json` once and `expected.json`, and refuses a second
     run. s2 and s3 run dry runs plus their checks, then `--yes`, then yes==dry and the re-checks, all in one script.
   - s4 runs flatdiff from `--tools <dir>/tools/phase3-proof/` and stops if `r3-allowlist.json` is missing. There is no
     `| head` anywhere, and a test enforces that. I checked real-mode quoting with a stub ssh that shlex-splits the way
     orion-remote does: sql-ro arrives as exactly one argument.
3. `tools/phase3-proof/test_r3_scripts.py`: 17 tests over `fixtures/r3/`. `happy/` holds the fixtures, `stop-*/` the
   overlays, and `generate.py` rewrites them.
   - Happy path for each of s0-s4.
   - STOP cases, one per artifact: latest_levels still holds 9 market_data rows after the hourly run (s1); a market_data
     count at s2 differs from step 1's (s2, no rebuild call made); a refused rebuild row (s2, no `--yes` made); a wrong
     withoutReplacement count (s3, no `--yes` made); global market_data != 0 after s3.
   - Further STOP cases: no levels run finishes; the signed file is missing (s1 makes no call); an unallowed flatdiff path
     (s4); the allowlist is missing (s4 makes no call); expected.json or days.json is missing; s0 is run twice.
4. `docs/superpowers/notes/2026-11-19-orion-phase3-r3-followups.md`: rulings R1-R14, one line each with cost-if-wrong
   ("assessed here" for R10 and R13, which state none); all 13 `minor (deferred)` lines; N1-N6; and open items, including
   the brief's watched-monitor-only item.
5. The spec's Status has one new R3 bullet. `tools/phase3-proof/README.md` has table rows for the new files.

Tests before commit B: vitest 2024/2025 (only daemonSchema fails, environmental), typecheck clean.
`python3 -m unittest tools/phase3-proof/test_r3_scripts.py tools/phase3-proof/test_flatdiff.py` passed 63; orion-remote passed 67.

## Self-review / concerns

1. **VVV's `disclosure` circulating row (2026-09-18, 48.35M, "keep" in scoping code-and-data.md §3).** If it is still
   active, R12's target rule (a different source_type) makes the rebuild target it. VVV's `rebuilt` would then be
   market_data + 1, and the plan's step-6 expectation ("vvv = step 1's market_data count") would be wrong. The scripts
   treat it as an unlisted stale kind, so s0 STOPs on it. Task 7's prod-copy dry run will show whether it applies, and
   Mike or the controller needs to rule on it. I put it in the deploy block and in the followups open items.
2. **New Task 7 artifact.** s1's ±2% check needs the signed circulating values in a file. I named it
   `tools/phase3-proof/r3-signed-circulating.json` (`{"<asset>": tokens}`), read from `--tools`, and s1 stops without it.
   Task 7 has to create it alongside `r3-allowlist.json`, or the controller can pick another source.
3. **The levels wait on stage can last up to 6 h.** levels runs every 6 h on stage (schedule.yaml), so s1 polls up to 78 ×
   300 s on stage and 15 × 300 s on prod. On stage, deploy shortly before a :15 slot, or run s1 in the background. The
   block says so.
4. **Pre-check skip.** If the first levels run on the tag already finished before step 4's pre-check (the scheduler can
   run right after the restart), the pre-check prints a note and skips. The unexempted re-check still runs.
5. **staging_refresh window.** The plan says "between the stage switch and prod's step 6". I wrote "until the end of
   prod's s3 (steps 7-8)", because prod holds CoinGecko rows until its purge. That is a small departure from the plan
   text; the redo path is a fresh s0, then s2-s4.
6. The step-3 log check flags any line with `ORION ALERT` or ` error`. It is conservative, so a benign log line containing
   "error" would cause a false STOP. Purge `observations` is compared with step 1's market_data *total* (all statuses;
   the purge deletes superseded rows too). Scoping says they are all active on prod.

Files: src/ingest/run.ts, tests/ingest/derived.test.ts (A); docs/ops/deploy.md,
docs/superpowers/notes/2026-11-19-orion-phase3-r3-followups.md, docs/superpowers/specs/2026-11-09-...-design.md,
tools/phase3-proof/{README.md, r3-lib.sh, r3-s0..s4.sh, r3_check.py, test_r3_scripts.py, fixtures/r3/**} (B). There was no
network, ssh, live DB or .env use, and node_modules was not staged.
