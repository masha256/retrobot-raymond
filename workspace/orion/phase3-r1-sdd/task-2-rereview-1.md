# Task 2 re-review, fix round 1 (8e3304f..de7f7e4)

### Finding Verdicts

- **I-1: fsync the export file's directory (and $ORION_HOME when `purged/` is first created) inside the try; a failure is `purge_export_failed` before any delete** — ADDRESSED. `src/db/purge.ts:237-244` `fsyncDir` (open 'r' + fsync + close); `:262` keeps the `mkdirSync` return (first created dir); `:267-272` syncs `dir`, then each created level's parent up to `dirname(created)`. I traced it: an existing home gives `[home/purged, home]`; `a` existing with `a/b/c` new gives `[a/b/c, a/b, a]`; the loop stops at the root. All of it runs inside the `try` (`:256-275`), so a failure throws `purge_export_failed` (`:274`) before the UPDATE/DELETE at `:110-113`. Seam `syncDir` at `:68`, `:106`. Test `tests/db/purge.test.ts:263-286`: first purge syncs `[exportDir, home]`, a later purge syncs `[exportDir]`, and a failing seam gives `purge_export_failed` with counts unchanged.
- **Minor 1: config-only refusals before the run lock** — ADDRESSED. `checkConfigured` (`src/db/purge.ts:131-152`) is called at `:87`, before the dry-run/apply branch and `withRunLock` (`:92`). It is called again in `planPurge` (`:159`), so the in-transaction re-plan still checks. `invalid_source_type` and `purge_no_metric` were already pre-lock (`:83-86`). The ruling lists "unknown metric", but the code has no unknown-metric refusal: an unconfigured metric is an orphan, `continue` at `:136`. So nothing needed to move, and the implementer's note is correct. Test `tests/db/purge.test.ts:301-325`: a `running` agent run stays `running` after refused `--yes`, and with another lock holder both dry run and `--yes` return the config code.
- **Minor 2: test the `live === null` branch** — ADDRESSED. `tests/db/purge.test.ts:288-299` uses `legacy_level` = total_supply (no `source`) + `fetcher: 'scripted'`, so `sourceTypeOf` returns null (`src/report/sourceTypes.ts:111`). `sourceType` is `third_party`, so the equality branch cannot fire and only the null branch is exercised. Checked for both apply=false and apply=true, with counts unchanged and no export dir.
- **Minor 3: CLI refusals also without --yes, same code** — ADDRESSED. `tests/cli/purge.cli.test.ts:105-111` runs all five refusal cases with `['--yes']` and with `[]`, then checks obs count and that no `purged/` dir exists.
- **Minor 4: test run_in_progress** — ADDRESSED. `tests/db/purge.test.ts:327-342`: with `tryAssetRunLock('purg', ...)` held, `--yes` gives `run_in_progress`, the dry run still counts 3, counts are unchanged and no export dir is written.
- **Minor 5: cap export name `<asset>-<first metric>[+N]-<UTCstamp>.json`** — ADDRESSED. `src/db/purge.ts:231-235`. Unit and 40-metric applied test at `tests/db/purge.test.ts:344-358`: the JSON still lists every metric. The CLI expectation was updated (`tests/cli/purge.cli.test.ts:85`).

### New Breakage in the Fix Diff

- Minor: when the directory fsync fails (`src/db/purge.ts:272`), the export file has already been written and fsynced, so it stays in `purged/` even though nothing was deleted. The error says "nothing was deleted", which is true, but the file is not removed or named in the message as stale. This is the same class as the commit-failure case the report already notes. Optional: best-effort `unlinkSync(file)` in the catch, or a note in the message. Not blocking.

No Critical or Important breakage.

### Out-of-Scope Observations

- DB-dependent refusals (`purge_open_anomaly`, `purge_dangling_reference`) still run under the lock, so a refused `--yes` on those can still `abandonRunningRuns`. That is outside the Minor 1 ruling, which covers config-only refusals.

### Checks run

- Read the diff package and `de7f7e4:src/db/purge.ts`, `src/report/sourceTypes.ts`, `tests/db/purge.test.ts` (fixture) via `git show`. Traced the `toSync` loop by hand. Re-ran no tests: the fix report shows RED (4 failed/18) → GREEN (18/18 focused, 1712/1712 full) and names the covering tests, and the code raised no specific doubt.

### Verdict

**Fix round:** All findings addressed, no new Critical/Important breakage. 1 new Minor.
