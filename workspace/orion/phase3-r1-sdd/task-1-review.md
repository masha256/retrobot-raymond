# Task 1 review: `backfill` job kind (e61d663..a6c78d2)

File:line references for `src/daemon/jobs/backfill.ts` are file lines (diff line − 183). The diff was read in one pass. Code outside the diff was read only for the named risks; each check is listed under its risk.

## Spec Compliance

- ✅ **Spec compliant.** Every file the brief lists has its hunk:
  - 0007 (`0007_job_params.sql:6-10`): `ADD COLUMN params_json jsonb`, then drop and re-add `jobs_kind_check` with `backfill`. It has no `-- breaking` line and is schema-unqualified, with a header in 0004's style.
  - `jobs.ts`: kind, priority 70, max attempts 1, `BackfillParams`, `NewJob.params`/`Job.params`, and `enqueueJob` writes `params_json`.
  - `backfill.ts`: the three constants (lines 16-20), `parseBackfillParams` (46-70), and `withRunLock(…, lockHolder('daemon backfill'), …)` around `fetchAsset(db, loaded, now, deps, { metrics, backfillDays })` (134-136). It posts one Slack line on done (146) and one on failure (162). The result is `{ fetchLines, written }`.
  - `daemon.ts`: `defaultHandlers().backfill`.
  - CLI: `job.ts:60-70, 95-96, 104`. It is required for backfill and refused for other kinds (`invalid_option`), validated the same way as the handler, and the asset needs no registry state.
  - `schedule.ts` is unchanged, which is allowed: `newestSlot`/`nextSlot` already exist.
  - Every test the brief names is present: backfill.test (all 5 named cases), daemon.test (ordering, and the reap with max_attempts 1), daemonSchema 0007, migrate pin, jobs round-trip, and job.cli.
- Extras, all accepted by the controller:
  - The "< 2 h after the slot" guard: R9.
  - The four out-of-list pin edits: R8.
  - A refused-params ALERT post. It is consistent with "failure posts a line", so it is not a finding.
- ⚠️ **Cannot verify from the diff:**
  - Task 3 must drop the `backfill` exclusion in `tests/release/orionRemote.test.ts:1319-1321` (R8 carry).
  - Task 3's deploy.md must say to drain or finish backfills before a rollback (R10).

## Strengths

- The migration is genuinely expand-only. The test (`daemonSchema.test.ts:1118-1155` in the diff) proves it:
  - a pre-0007 row survives;
  - `backfill` is refused before 0007;
  - an insert in the old shape works after it;
  - `nope` is still refused;
  - the constraint is still named `jobs_kind_check`.
- One validator (`parseBackfillParams`) is shared by the CLI and the handler. The handler re-runs it on the release that executes the job, and it runs before the window check, so a bad request fails at once instead of deferring.
- Deferral uses `deferJob`, which gives the attempt back. So max_attempts 1 is spent only on a real run, and a lease loss can never re-run the job. Both are tested through `reapExpired` and through the next daemon's `start()`.
- The tests exercise real behaviour against the test DB: the real lock holder is read inside the fetch, and the real `fetchAsset` runs over the harness. There is very little mocking.

## Named risks

### 1. Rollback safety (orion-2026.11.11.1 on schema 7): **SAFE**

Checked in `git show e61d663:src/db/jobs.ts`, `src/daemon/daemon.ts` and `src/db/pg/migrate.ts`:
- **Inserts.** `enqueueJob` names its columns (old `jobs.ts:92`), so the nullable `params_json` defaults to NULL. Every old kind is still in the CHECK.
- **Reads.** `getJob`/`listJobs`/`claimNextJob` use `SELECT *`/`RETURNING *`, and the old `fromRow` ignores the extra column.
- **Writes.** `finishJob`/`retryJob`/`deferJob`/`reap` are UPDATEs by named columns. The retention DELETE is by kind-agnostic status.
- **Start-up.** The old daemon refuses only when `pending.length > 0` (old `daemon.ts:221-223`). `migrationStatus` reports schema 7 as `ahead`, not `changed` (old `migrate.ts:71-75`), and `db.cli` already pins "a command on a schema ahead runs".
- **A queued backfill under the old release.** It is claimed and failed `no handler for job kind backfill` (old `daemon.ts:409`). It is not retried and posts no Slack line. This is accepted under R10, and it is a job-row trace only (see the R10 carry above).

### 2. Never delay or double-run the nightly: **PARTLY SAFE, one hole (Important I-1)**

- **Queued at the nightly slot.** Priority 70 > 10/20, and `claimNextJob` orders by priority before run_after and id. This is tested with an older run_after and a lower id (`daemon.test.ts` diff 967-991). Safe.
- **Lease reaped while running.** max_attempts 1 means `reapExpired` fails the job (`lease_expired`) and never re-queues it. The next daemon's `start()` fails it with the RESTARTED line. Both are tested (diff 993-1015). No double run. Safe.
- **Drain during a switch.** The worker finishes the current job and claims nothing more (diff 1017-1036). Safe.
- **The run lock vs the nightly refresh.** The daemon has a single worker, so a backfill and a refresh of the same DB never run at the same time inside the daemon. An outside holder (a CLI tick) gives `run_in_progress`, which defers 30 min (tested). Safe.
- **Hole.** The window guard is time-based only (`backfill.ts:79-87`), and it reopens at slot + 2 h. The nightly itself may legitimately still be unfinished then:
  - `nightly_report` waits for its refreshes until slot + `NIGHTLY_WAIT_MS` = 3 h, deferring 5 min at a time (`nightlyReport.ts:19-21, 154-159`).
  - Refresh retries come 10 min later (`REFRESH_RETRY_MS`), or 30 min later when the asset is locked (`refresh.ts:21-23`).
  - So in that gap the backfill is the only due job: a refresh retry or a deferred report has `run_after` in the future, and the backfill is claimed. It then holds the single worker for hours. The retry and the report run after it, past their 3 h cut. That delays the nightly, which is what P1 forbids. See I-1.
- **Out of scope for this risk (plan P1, Minor M-3).** A backfill that starts with ≥ 4 h of clearance but runs longer than 4 h also delays the nightly. Nothing bounds its run time.

### 3. Silence means broken: **MOSTLY SAFE, the partial judgement is Important I-2**

| Outcome | Job row | Slack | Where |
|---|---|---|---|
| done | `done` + `{fetchLines, written}` | `ORION BACKFILL … done` | `backfill.ts:142-149` |
| failed (throw or all sources failed) | `failed` + error `code: first line`, with fetchLines when there are any | ALERT | 151-165 |
| refused params, or a missing or unknown asset | `failed invalid_backfill_params` / `asset_not_found` | ALERT | 124-126, 158 |
| deferred (window or lock) | queued with a later run_after | none; the daemon logs `deferred until` (`daemon.ts:450`) | none |
| aborted | `aborted`; reaped `lease_expired` | RESTARTED line on the next start | none |

Every terminal outcome leaves a trace.

**Judgement on `partial`.** With `--metric`, `buildPlan` runs only the requested metrics' primaries and their check sources (`ingest/run.ts:191`, `plan.ts:67`). So a `partial` outcome always means a source serving a requested metric failed. When that source is the primary, the operator's request was not done. Yet the row says `done` with `last_error` NULL, and `job list` shows success. The only signal is `; partial: X failed` in the Slack line, and that branch is untested. A partial in which a requested metric's primary failed should be `failed`. See I-2.

### 4. Value equality with `data fetch --metric --backfill-days`: **EQUAL**

- The handler passes exactly `{ metrics, backfillDays, onProgress }` (`backfill.ts:134-136`). The CLI passes `{ metrics, backfillDays, adopt, dryRun, onProgress }` (`cli/commands/data.ts:164-166`). Without `--adopt`/`--dry-run` both are false/undefined, which is the handler's default.
- `parseBackfillParams` returns a copy of exactly the requested keys (line 69). The test asserts that the fetch got `metrics: [METRIC], backfillDays: 3`.
- The cursor behaviour is the same, because it is fetchAsset's own: `rescan: opts.backfillDays !== undefined` (`run.ts:288`), and the members of a shared scan are written only when listed.
- One difference: the daemon adds `dayBlocks: dbDayBlocks` (as refresh does). That is a block-number cache, so values are unchanged and the only extra write is cache rows in `day_blocks`.
- `sharedHttpCache` is not passed. That has no effect on values.

## Issues

### Critical (Must Fix)

None.

### Important (Should Fix)

**I-1. `src/daemon/jobs/backfill.ts:79-87`: the window reopens before the nightly is guaranteed finished.**
- **What's wrong.** `BACKFILL_DEFER_AFTER_MS` (2 h) is less than `NIGHTLY_WAIT_MS` (3 h, `nightlyReport.ts:19`). A refresh retry (+10 min) or a lock deferral (+30 min) that lands after slot + 2 h leaves the backfill as the only due job. It is claimed, and it holds the single worker for hours. The retry and the `nightly_report` then run late, and the report misses its own 3 h cut, posting with what it has.
- **Why it matters.** It breaks P1's "never delay the nightly" in the exact case where the nightly is already struggling.
- **Fix.** Keep the constants and add a state check. While any `refresh` or `nightly_report` job of `newestSlot(nightly)` is not terminal (`listJobs(db, { slot })`), defer, for example by `NIGHTLY_DEFER_MS`, or to the earliest such run_after. Alternatively, make the reopening `max(slot + 2 h, slot + NIGHTLY_WAIT_MS)`. Either way, add a test: at slot + 2 h 05 min, with a refresh of the slot queued at slot + 2 h 10 min, the backfill defers.

**I-2. `src/daemon/jobs/backfill.ts:140-150`: a `partial` fetch whose failed source is a requested metric's primary is recorded as `done`.**
- **What's wrong.** The job row reads as success (`status: done`, no `last_error`) while the requested re-scan did not happen. `job list` and `orion-remote jobs` hide it.
- **Fix.**
  - Fail the job, with the ALERT line and error `fetch_partial: <source>: <first line>`, when a failed source is the primary of a requested metric (for example, its `metricKey:`-prefixed error or a `written[m] === 0` alongside a failed source). Keep `done` + `; partial` only when nothing but a check source failed.
  - The partial branch (142-145) has no test. Add one for each case.

### Minor (Nice to Have)

- **M-1. `src/daemon/jobs/backfill.ts:89-96`.** `message` and `codeOf` are copied verbatim from `refresh.ts:52-59`. Export one copy, for example from `refresh.ts` or a small `jobs/util.ts`. `aborted` is already copied per handler, as the file's existing pattern.
- **M-2. `src/daemon/jobs/backfill.ts:134-136`.** `ctx.signal` is not passed into the fetch. After a lease loss while the daemon lives (a DB hiccup over 3 min), the fetch keeps the worker and the asset lock for the rest of the scan, and its rows are written while the job row says `lease_expired`. Refresh has the same gap, so the limit is shared. Consider an abort check between batches in a later task.
- **M-3. Plan P1 (`backfill.ts:79-87`).** Nothing bounds a backfill's run time.
  - One that starts 4 h before the slot and takes 5 h delays the nightly anyway.
  - Hourly `levels`, `disclosure_watch` and stage's weekly `staging_refresh` wait for the backfill's whole duration.
  - Suggest at least a start line in Slack (`ORION BACKFILL … started`), so a long-running job is visible. A time budget, or a check-in between metrics, could follow later. This is a plan-level limitation; the human decides.
- **M-4. `src/cli/commands/job.ts:68`.** It tests `opts.backfillDays.trim()` but converts the untrimmed string. `Number(' 30 ')` is 30, so the result is correct; using `trim()` once would read more clearly.

## Assessment

**Task quality:** Needs fixes

**Reasoning:**
- What works: the migration is clean and verifiably expand-only; the validator is shared; the no-retry and lease handling are correct; the tests are thorough and real.
- What needs fixing: the nightly guard is time-only and reopens an hour before the nightly report's own wait ends (I-1), and a partial fetch of a requested metric's primary is recorded as success (I-2). Both are small, local fixes in `backfill.ts`, each with a test.
