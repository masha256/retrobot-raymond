# Task 1 re-review, fix round 1 (b31c224..8e3304f)

### Finding Verdicts

- **I-1: the guard was clock-only and reopened at slot + 2 h while the nightly could still be running.** ADDRESSED.
  - `src/daemon/jobs/backfill.ts:86-97`: `backfillWaitUntil` is async now. The clock guards are kept: slot + 2 h at :91, and the 4 h pre-nightly clearance at :93.
  - :94-96: it then lists jobs with `slot = newestSlot(nightly)`. `listJobs` compares `slot` as a timestamptz, so the ISO format matches. If any `refresh` or `nightly_report` of that slot is `queued` (a queued retry included, because retries are re-queued per jobs.ts:167) or `running`, it returns `now + BACKFILL_NIGHTLY_RECHECK_MS` (15 min, :24).
  - Handler call site: `await` at :157.
  - Test `tests/daemon/backfill.test.ts:206-234` covers:
    - at slot + 2 h 30, a queued retry plus a running report -> deferred to now + 15 min;
    - retry failed, report still running -> deferred;
    - an older slot's queued refresh is ignored;
    - all jobs done, failed or skipped -> runs.
- **I-2: a partial fetch whose failed source is a requested metric's primary must fail the job (ALERT, no retry). A partial with only failed cross-checks stays done.** ADDRESSED.
  - `backfill.ts:120-128`: `fetchFailure(r, primaries)` returns `fetch_partial` when a failed source is in `primaries`.
  - :173: `primaries` = `sourceId(def.source)` of each requested metric. `source!` is safe because `parseBackfillParams` (:69) rejects a source-less metric.
  - The failure path at :195-201 posts the ALERT and returns `failed` with no `retryAfterMs`.
  - A cross-check-only failure takes the done path with `; partial: ... failed` (:174-183).
  - Test `backfill.test.ts:236-275` covers both cases against the real fetch's source ids.
- **M-3: start line, duration on the done/failed line, deploy.md sentence.** ADDRESSED for Task 1's scope.
  - Start line: `backfill.ts:163-168` posts `ORION BACKFILL <env> <SYM> started: <metrics>, <n> days` once the lock is held, before the fetch. Ruling R15 keeps the env prefix.
  - Durations come from `fmtDuration` (:100-104):
    - done: `done in <dur>` at :181;
    - failed after the start: `failed after <dur>` at :197-198.
  - Before the start, refusals and deferrals post nothing (tests unchanged).
  - The deploy.md sentence is Task 3's file, per the ruling. Verify it in Task 3.

### New Breakage in the Fix Diff

No Critical or Important issues.

- Minor 1, `backfill.ts:94-96`: a refresh or report of the newest slot that stays `queued` or `running` (e.g. an orphaned row) holds every backfill until the next slot rolls over, for up to about 1 day. Each 15-min deferral is silent: a log line only, no post. The operator only sees "started" never arriving. Acceptable, but worth a note in deploy.md or the followups.
- Minor 2, `backfill.ts:173`: `primaries` covers the requested metrics' own `source` only. For a requested flow whose source is `derived:`, a failed input source of that derived source does not count as a primary failure unless the derived source's outcome is itself `failed`. Not exercised by any current flow config; noting it only.

### Out-of-Scope Observations

None.

### Checks run

- Read the diff file, the brief, the findings, R15, and the fix report.
- Read code at 8e3304f: `src/db/jobs.ts` (`listJobs`, re-queue and defer SQL), `src/ingest/sourceId.ts`, and `parseBackfillParams`.
- No tests re-run: no specific doubt arose that the reported RED/GREEN runs (`9 passed (9)`, full `1707 passed`) don't answer.

### Verdict

**Fix round:** All findings addressed, no new Critical/Important breakage.
