# Task 3 findings (fix round 1) — controller rulings binding

Source: task-3-review.md against e88130f. Note: HEAD is now 69caa3f (Task 4 landed after Task 3); your fix is its own commit on top.

- I-1 (fix, docs/ops/deploy.md rollback note): the deploy keys have no drain verb and `rollback` drains with a 30-min wait that a running backfill outlasts (rollback then aborts, exit 1). Rewrite the note: before `rollback` past this release, run `ssh orion-<env> jobs` and wait until no `backfill` job is running (a running one holds the worker; `rollback` would time out its drain and abort); a QUEUED backfill under the older release fails "no handler" with no retry — re-queue it with `job run-now backfill ...` after rolling forward again. Remove "drain the daemon".
- M-1 (fix, security nit): METRIC_RE / COUNT_RE / RUNG_RE (and any new pattern this task added) must reject a trailing newline: use `re.fullmatch` or `\Z` anchors for the values this task validates. Test: `flow_usd.burn\n`, `3\n`, `third_party\n` refused (exit 64). Don't change pre-existing verbs' behaviour beyond the shared helper if it is shared; if `pattern()` is shared by older verbs, tightening it for all is acceptable (stricter), say so in the report.
- M-2 (fix, docs): the sizing note also names the deferral while a nightly began < 2 h ago and while that nightly's refresh/report jobs are unfinished (R9, Task 1 I-1).
- M-3 (fix): add a test that pins orion-remote's RUNGS against the TS list (`SOURCE_TYPES` in src/db/purge.ts or the SourceType list in src/report/sourceTypes.ts) the same way tests/release/orionRemote.test.ts pins JOB_KINDS.
- M-4 (fix, docs): give the pre-existing heading-less ssh-verb block at the end of deploy.md its own heading (or move the new section after it) so it doesn't read as part of "Phase 3 R1 release".
- M-5 (fix, test): make the log-redaction assertion fail for quoted arguments too (assert none of the argument values appear in remote.log).
- The ⚠️ (example purge of `lit unlocks_next_year --source-type third_party`): valid — after Task 6 LIT's current source is `disclosure`, so purging `third_party` rows of it is the intended use. No change.
