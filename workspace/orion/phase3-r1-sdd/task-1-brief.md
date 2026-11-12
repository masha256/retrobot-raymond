### Task 1: `backfill` job kind (migration 0007, params, handler, CLI)

**Files:**
- Create: `src/db/pg/migrations/0007_job_params.sql`, `src/daemon/jobs/backfill.ts`, `tests/daemon/backfill.test.ts`,
  `tests/cli/job.cli.test.ts`
- Modify: `src/db/jobs.ts` (JOB_KINDS, JOB_PRIORITY, MAX_ATTEMPTS, NewJob/Job `params`), `src/daemon/daemon.ts`
  (`defaultHandlers`), `src/cli/commands/job.ts`, `src/daemon/schedule.ts` (only if no next-slot helper exists)

**Interfaces:**
- Produces: `JobKind` gains `'backfill'`. `NewJob.params?: BackfillParams | null`, `Job.params: Json | null`.
  `type BackfillParams = { op: 'fetch'; metrics: string[]; backfillDays: number }`.
  `backfillHandler: JobHandler` in `src/daemon/jobs/backfill.ts`. `BACKFILL_CLEARANCE_MS = 4 * 3_600_000`,
  `BACKFILL_DEFER_AFTER_MS = 2 * 3_600_000`, `BACKFILL_MAX_DAYS = 400`.

- [ ] **Step 1: Migration test.** In `tests/db/daemonSchema.test.ts` (and the migration-list pin under `tests/db/pg/`), assert
  0007 applies on a schema at 6, that `jobs.params_json` is `jsonb` and nullable, that an insert with kind
  `'backfill'` succeeds, that kind `'nope'` is rejected, and that 0007 is not marked `-- breaking`.
- [ ] **Step 2: Write 0007.** `ALTER TABLE jobs ADD COLUMN params_json jsonb;`, then drop and re-add the kind CHECK
  with `'backfill'` added (find the constraint name with `\d jobs` on the test DB). Schema-unqualified, with a header
  comment in the style of 0004.
- [ ] **Step 3: Handler tests** in `tests/daemon/backfill.test.ts`, using the fake fetch deps from
  `tests/daemon/refresh.test.ts`:
  - `runs fetchAsset with the job's metrics and backfillDays under the asset run lock`: the result's `fetchLines`
    equal `fetchSummary(result)`, and `status: 'done'`.
  - `defers when the next nightly slot is under 4 h away`: clock 22:00Z, nightly at 00:45Z, so `deferred` until
    02:45Z.
  - `fails without retry on a fetch error`: `status: 'failed'`, no `retryAfterMs`, and one Slack post naming the
    asset, the metrics and the error's first line.
  - `refuses params that don't parse`: a missing `op`, an unknown metric, a non-flow metric, or `backfillDays` 0 or 401
    each fail with `invalid_backfill_params`, and nothing is fetched.
  - `run_in_progress` (lock held) defers 30 min, like refresh's `REFRESH_LOCKED_RETRY_MS`.
- [ ] **Step 4: Daemon ordering tests** in `tests/daemon/daemon.test.ts`. With a `backfill` and a nightly `refresh`
  job queued at the same slot, `claimNextJob` returns the refresh first. A `backfill` whose lease expires with
  `attempts = max_attempts = 1` is failed by `reapExpired`, not re-queued.
- [ ] **Step 5: Implement.** In `jobs.ts`, `backfill` gets priority 70 and max attempts 1, and `enqueueJob` writes
  `params_json`. The handler validates the params against the loaded asset (each metric configured, `type: flow`),
  runs `withRunLock(db, asset, lockHolder('daemon backfill'), ...)` around
  `fetchAsset(db, loaded, now, deps, { metrics, backfillDays })`, posts one Slack line on done (rows written per metric)
  and on failure, and returns `{ fetchLines, written }` as `result`.
- [ ] **Step 6: CLI.** `job run-now backfill <asset> --metric <k> (repeatable) --backfill-days <n>`. Both are required
  for `backfill` and refused for every other kind (`invalid_option`). Validate the same way as the handler, so a bad
  request never reaches the queue. The asset needs no `active` state, because a backfill is an operator action.
  Test in `tests/cli/job.cli.test.ts`; `tests/db/jobs.test.ts` covers `params` round-tripping.
- [ ] **Step 7: Run** the three test files, then the full suite and typecheck. Expected: green, and no hash pin moves.
- [ ] **Step 8: Commit** `feat(daemon): backfill job kind (0007 jobs.params_json, expand-only); job run-now backfill`.

