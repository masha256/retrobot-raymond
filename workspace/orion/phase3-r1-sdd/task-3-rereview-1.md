# Task 3 re-review, fix round 1 (69caa3f..6f97c21)

### Finding Verdicts

- **I-1 (rollback note: no drain verb; 30-min drain aborts on a running backfill)**: ADDRESSED. docs/ops/deploy.md:449-453 (6f97c21) says there's no drain verb and the 30 min wait times out, then `rollback` aborts (exit 1, nothing switched). It says to run `ssh orion-<env> jobs` and wait until no `backfill` is `running`. A queued backfill fails "no handler" with no retry, and the note says to re-queue it with `job run-now backfill ...` after rolling forward. "drain the daemon" is gone. The note matches the code: orion-remote:886-902 `drain()` passes `--wait 30m`, and on a non-zero exit it undrains and raises `Failed`.
- **M-1 (trailing newline accepted by `$`)**: ADDRESSED. orion-remote:269 `pattern()` (shared), :277 `count()` and :291 `metric_list()` all use `fullmatch`. :772 `prune()` TAG_RE also uses `fullmatch`. New test `test_trailing_newline_refused` (test_orion_remote.py ~:986-994) covers `flow_usd.burn\n`, `3\n` (both --backfill-days and --days), `third_party\n`, an asset and a job kind. The report says the tightening applies to every verb that goes through `pattern()`, as the ruling allows.
  - **Specific check: does fullmatch refuse any legitimate value?** No. All ten regexes are anchored at both ends: orion-remote:101-110 (TAG, SHA, ID, ASSET, METRIC, WHO, DAY, ISO, COUNT, RUNG) and the inline job-kind regex at :500. No regex lacks `$` or relied on `match` accepting a prefix. For a `^...$` regex, `fullmatch` differs from `match` only on a value ending in one `\n`, which is never a legitimate value. RUNG_RE and the job-kind regex wrap their alternation in `^(...)$`, so `fullmatch` cannot split on `|`. The ISO regex has its optional groups (T, seconds, `.mmm`, `Z`/`±hh:mm`) nested inside the anchors, so it accepts the same values as before. In `prune()` the names come from the directory listing, and a release dir never ends in `\n`. No other `re.match`/`.match(` calls remain (grep).
- **M-2 (sizing note: the 2 h nightly window and unfinished refresh/report jobs)**: ADDRESSED. deploy.md:445-448 now has the under-4 h deferral, the "nightly began under 2 h ago (waits until slot + 2 h)" deferral and the unfinished refresh / nightly_report jobs. The prod example (queued at 00:50, starts at 02:45 at the earliest) checks out: 00:45 + 2 h = 02:45.
- **M-3 (pin RUNGS against TS)**: ADDRESSED. tests/release/orionRemote.test.ts:8 imports `SOURCE_TYPES` from src/db/purge.ts, and :37-40 compares the parsed multi-line `RUNGS` tuple with it in order. `[^)]*` spans the newline. src/db/purge.ts:28-30 at 6f97c21 has the same nine values in the same order. The report includes the mutation RED.
- **M-4 (heading-less ssh-verb block)**: ADDRESSED. deploy.md:459 adds `## The ssh verbs (any release)`, placed after the `<!-- release block: Task 8 -->` marker, so the Task 8 block stays inside "Phase 3 R1 release" (:401).
- **M-5 (redaction assertion vacuous for quoted args)**: ADDRESSED. test_orion_remote.py `assert_refused` (~:910-925) splits with `shlex`. It asserts the tail is exactly `<verb> <argc> refused` (the strong check) and that no argument value appears in it. The report includes the mutation RED (4 refusal tests fail on the new assertion).

### New Breakage in the Fix Diff

None Critical/Important.
- Minor: in `assert_refused`, the per-word `assertNotIn(word, tail)` does a substring check against a tail like `job 10 refused`. A short numeric argument (`1`, `0`) that is a substring of argc but not equal to it would fail the assertion, even though nothing leaked. This is a test-brittleness risk only. The exact-equality check on the tail already proves no value leaked, so the per-word loop adds nothing. It is not triggered today: I ran it.

Check run: detached worktree at 6f97c21, `python3 -B -m unittest scripts/provision/test/test_orion_remote.py`, which ran 52 tests, OK (skipped=1). The worktree was then removed.

### Out-of-Scope Observations

None.

### Verdict

**Fix round:** all findings addressed, no new Critical/Important breakage. Minors: 1.
