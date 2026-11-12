# Task 1 report: `backfill` job kind (0007, params, handler, CLI)

Status: DONE_WITH_CONCERNS (see Concerns: three test files outside the brief's list changed; one guard goes beyond the brief).
Commit: `a6c78d2 feat(daemon): backfill job kind (0007 jobs.params_json, expand-only); job run-now backfill` on
feat/phase3-third-party (parent e61d663). Not pushed.

## What was built
- `src/db/pg/migrations/0007_job_params.sql` (expand-only: no `-- breaking` line). It runs `ALTER TABLE jobs ADD COLUMN params_json jsonb`, then
  drops `jobs_kind_check` and re-adds it under the same name with `'backfill'` added. Old kinds are kept, so a release
  before 0007 still inserts its own jobs (tested). It is schema-unqualified, with a header comment in 0004's style.
- `src/db/jobs.ts`:
  - `JOB_KINDS` gains `'backfill'`, with `JOB_PRIORITY.backfill = 70` and `MAX_ATTEMPTS.backfill = 1`.
  - New `BackfillParams = { op: 'fetch'; metrics: string[]; backfillDays: number }`.
  - `NewJob.params?: BackfillParams | null`; `Job.params: Json | null`, read from `params_json` (jsonb, which node-postgres parses).
  - `enqueueJob` writes `params_json`.
- `src/daemon/jobs/backfill.ts`:
  - Constants `BACKFILL_CLEARANCE_MS = 4 h`, `BACKFILL_DEFER_AFTER_MS = 2 h`, `BACKFILL_MAX_DAYS = 400`.
  - `parseBackfillParams(raw, asset)` is shared with the CLI. It refuses with `invalid_backfill_params`:
    - params that are not an object, or that carry unknown keys;
    - an op other than `fetch`;
    - empty metrics, or a metric listed twice;
    - an unknown metric, a metric that isn't `type: flow`, or a flow with no source (entered by hand);
    - `backfillDays` that isn't a whole number in 1..400.
  - `backfillWaitUntil(ctx, now)` reads the env's nightly entry from `loadSchedule(configRoot, env)` (stage overrides apply) and uses the existing `newestSlot`/`nextSlot`. No schedule.ts change was needed.
  - `makeBackfillHandler({ fetchDeps?, fetch? })` / `backfillHandler`:
    - It loads the asset (no registry-state requirement) and validates the params.
    - It defers while the nightly window is closed (see below).
    - It runs `fetchAsset(db, loaded, now, deps, { metrics, backfillDays })` inside `withRunLock(db, asset, lockHolder('daemon backfill'), now, …)`, with the day-block cache.
    - When the lock is held (`run_in_progress`), it defers `REFRESH_LOCKED_RETRY_MS` (30 min) without using up an attempt.
    - Done posts `ORION BACKFILL <env> <SYM> done (<N> days): <metric> <n> rows, …`, plus `; partial: <sources> failed` when the fetch was partial.
    - A failure posts `ORION ALERT <env> backfill <SYM> <metrics> failed: <code>: <first line>`. It returns `failed` with no `retryAfterMs`.
    - The result is `{ fetchLines: fetchSummary(fetch), written: { metric: rows } }`.
- `src/daemon/daemon.ts`: `defaultHandlers().backfill = backfillHandler`.
- `src/cli/commands/job.ts`: `job run-now backfill <asset> --metric <k> (repeatable) --backfill-days <n>`.
  - `backfill` is a per-asset kind (`asset_required`).
  - Both options are required for backfill and refused for every other kind (`invalid_option`).
  - Before anything is queued, the request is validated with `parseBackfillParams` against `loadAsset(configRoot, asset)`.
  - The text output adds `: <metrics>, <N> days`.

## Tests (TDD)
RED (before implementing), focused at `--maxWorkers=1`:
- The migration pins failed with `applied [1..6]` vs `[1..7]`, and the 0007 test failed with `expected undefined to match object { id: 7, name: 'job_params' }` (9 failures in daemonSchema/migrate/db.cli).
- `tests/daemon/backfill.test.ts` failed to load: `Cannot find module '../../src/daemon/jobs/backfill.js'`.
- `tests/cli/job.cli.test.ts` failed 3/3 with `CommanderError: unknown option '--metric'`.
- `tests/db/jobs.test.ts` failed on the constants (`JOB_KINDS` lacks backfill), on the defaults (`params` missing) and on the params round-trip.
- `tests/daemon/daemon.test.ts` failed on the 3 new backfill tests. Two later tests in the file failed only as a knock-on: a failed new test left a daemon holding the lock (`another orion daemon holds this database`).

GREEN:
- The same 8 files (backfill, job.cli, jobs, daemon, daemonSchema, migrate, db.cli, daemon.cli): 90/90 passed at `--maxWorkers=1`.
- Full suite, first run (`--maxWorkers=2`): 1689/1692 passed. The 3 failures were all pins on the migration count or job-kind list:
  - `tests/daemon/stagingRefresh.test.ts` "schema mismatch is refused before any restore command": "staging 6" is now 7.
  - `tests/tools/importSqlite.test.ts` "a carried weekly run without transcript still shows": `applied [6]` is now `[6, 7]`.
  - `tests/release/orionRemote.test.ts` "compiles, and its job kinds are JOB_KINDS".
- After fixing those three, the three files passed alone (29/29).
- Full suite, final run (`--maxWorkers=2`): **1692/1692 passed (140 files)**. Baseline was 1677/1677 (138 files), so the change adds 15 tests and 2 files. No load-sensitive file failed.
- `npm run typecheck`: clean. `python3 -m unittest scripts/provision/test/test_orion_remote.py`: 43 OK.
- No asset hash pin moved: `tests/assets` is untouched and no asset YAML changed.

New and extended tests:
- `tests/daemon/backfill.test.ts` (7 tests):
  - The constants, and that `defaultHandlers().backfill` is the handler.
  - It runs `fetchAsset` with the job's metrics and backfillDays while `daemon backfill pid N` holds the asset lock. `fetchLines` equals `fetchSummary(result)` and status is `done`. The Slack line is checked, and the lock is released afterwards.
  - Deferral:
    - At 22:00Z, with the nightly at 00:45Z, it defers until 02:45Z.
    - At 01:30Z (inside the running nightly) it defers until 02:45Z.
    - On stage (nightly 02:45Z) it runs at 22:00Z, and at 23:00Z it defers until 04:45Z.
    - The edges run: exactly 4 h before the slot, and exactly 2 h after it.
  - A fetch error: a throw, or an all-sources-failed outcome, gives `failed` with no `retryAfterMs` and one Slack line naming the asset, the metrics and the error's first line.
  - 11 bad param shapes each fail with `invalid_backfill_params` and nothing is fetched. These include no op, op `prices`, an unknown metric, a level metric, empty or duplicate metrics, 0, 401, 2.5, and an extra key. The validator is also checked directly for the 400-day cap and for a manual flow with no source.
  - With the run lock held, it defers 30 min.
  - A job with no asset fails.
- `tests/daemon/daemon.test.ts`, new "daemon backfill jobs" block:
  - A backfill queued earlier, with a lower id and an older run_after, is still claimed after the nightly `refresh` at the same slot.
  - Through the worker, the order is refresh, refresh, nightly_report, levels, backfill.
  - A backfill whose lease expires (deploy switch) is failed by `reapExpired` with `attempts = max_attempts = 1`, never re-queued.
  - A dead daemon's running backfill is failed at the next daemon's start, with the RESTARTED line, and is not run.
  - A drain during a backfill waits for it, then claims nothing.
- `tests/db/jobs.test.ts`: the constants include backfill 70/1; params round-trip through enqueue, get, list and claim; other kinds get `params: null`; the stored value is a jsonb object.
- `tests/db/daemonSchema.test.ts`, block 0007:
  - 0007 is not breaking and applies on a schema at 6.
  - `params_json` is `jsonb` and nullable.
  - `backfill` is refused before 0007 and accepted after it; an old-style insert still works; `nope` is still refused; the constraint is still named `jobs_kind_check`.
- `tests/cli/job.cli.test.ts` (3 tests):
  - It queues the job with params, priority 70 and max attempts 1, for an asset that is not in the registry.
  - Every bad request is refused with the right code and nothing is queued.
  - The options are refused on refresh, levels and nightly_report.

## Files
Created:
- `src/db/pg/migrations/0007_job_params.sql`
- `src/daemon/jobs/backfill.ts`
- `tests/daemon/backfill.test.ts`
- `tests/cli/job.cli.test.ts`

Modified, as in the brief:
- `src/db/jobs.ts`, `src/daemon/daemon.ts`, `src/cli/commands/job.ts`
- `tests/db/daemonSchema.test.ts`, `tests/db/pg/migrate.test.ts`, `tests/db/jobs.test.ts`, `tests/daemon/daemon.test.ts`

Modified, outside the list (pins that 0007 or the new kind necessarily move):
- `tests/cli/db.cli.test.ts`: the migration list, codeRequires 7, and the "ahead" test now inserts id 8.
- `tests/daemon/stagingRefresh.test.ts`: the schema-mismatch texts, 7/8.
- `tests/tools/importSqlite.test.ts`: `applied [6, 7]`.
- `tests/release/orionRemote.test.ts`: see concern 1.

## Self-review
- Expand-only: a pre-0007 insert (no params_json) works on schema 7 (tested), so orion-2026.11.11.1 runs on schema 7.
- `retention`'s `deleteJobsBefore` treats a finished backfill like any other job.
- The handler never retries. A deferral uses `deferJob`, which gives the attempt back, so a deferred backfill still has its one attempt.
- After the lock wait it may run as late as the next clear window.
- Slack text goes through `slackClean`.

## Concerns
1. **orion-remote.** `tests/release/orionRemote.test.ts` pins orion-remote's `JOB_KINDS` tuple to `src/db/jobs.ts JOB_KINDS`.
   - I left `scripts/provision/files/orion-remote` alone, since it is Task 3's file, and changed the test to compare against `JOB_KINDS` minus `backfill`, with a comment naming Task 3.
   - When Task 3 adds `backfill` to orion-remote, this test goes red until the exclusion is removed. Task 3 must drop it.
   - The other option was a one-line edit adding 'backfill' to orion-remote now. Remote `job run-now backfill <a>` would then reach Orion and be refused with `invalid_option`.
2. **Extra guard beyond the brief.** As well as "the next nightly is under 4 h away", the handler also defers while `now < newest nightly slot + 2 h`, until that slot + 2 h.
   - Without it, a backfill claimed at e.g. 00:46Z could start before the scheduler's next 30-second tick has queued that night's refreshes, and then block the nightly for hours. The brief's rule alone would let it run, because the next slot is ~24 h away.
   - Its effect is that a run-now between 00:45Z and 02:45Z on prod waits until 02:45Z. It is tested. Say if it should be dropped.
3. **Rollback.** An `orion-2026.11.11.1` daemon running on schema 7 that claims a queued `backfill` job fails it with "no handler for job kind backfill", which ends it without retry. Nothing breaks, but drain or finish backfills before a rollback.
4. **Partial outcome.** A `partial` fetch (some source failed, e.g. a cross-check source) is reported as `done`, with `; partial: <sources> failed` in the Slack line and the fetch lines in the result. Only an all-failed fetch or a throw counts as `failed`. Say if a partial fetch should fail the job.
5. The CLI's text output now appends `: <metrics>, <N> days` for backfill only; other kinds print the same as before.


---

## Fix round 1 (I-1, I-2, M-3) — on b31c224

### What changed (`src/daemon/jobs/backfill.ts` only; no `src/db/jobs.ts` change: `listJobs({ slot })` sufficed)
- **I-1.** `backfillWaitUntil` is now async. The clock guards are kept as they were: the 4 h pre-nightly clearance,
  and slot + 2 h. Past them, it also defers while any `refresh` or `nightly_report` job of `newestSlot(nightly)` is
  `queued` or `running` (a queued retry counts). It looks again after the new `BACKFILL_NIGHTLY_RECHECK_MS` = 15 min,
  measured from now, not from a fixed slot + 2 h. Jobs of older slots and other kinds don't count.
- **I-2.** `fetchFailure(r, primaries)`: `primaries` = `sourceId(def.source)` of each requested metric.
  - `outcome: failed`: `fetch_failed` (unchanged).
  - `partial` with a failed source in `primaries`: `fetch_partial: <sourceId>: <first line>`. The job fails with the
    ALERT line and no `retryAfterMs` (max attempts 1).
  - `partial` where only cross-check sources failed: stays `done`, and the done line ends `; partial: <ids> failed`.
- **M-3.** Once the asset lock is held, before the fetch, it posts `ORION BACKFILL <env> <SYM> started: <metrics>, <n> days`.
  - Done line: `ORION BACKFILL <env> <SYM> done in <dur> (<n> days): ...`.
  - A failure after the start: `ORION ALERT <env> backfill <SYM> <metrics> failed after <dur>: ...`.
  - `<dur>` comes from the exported `fmtDuration`: `N min` or `H h MM min`.
  - A refusal before the start (params, asset) posts no start line and keeps its ALERT unchanged.
  - A deferral posts nothing.
  - No code bound. The deploy.md sentence is Task 3's.

### Tests (`tests/daemon/backfill.test.ts`)
- New: `waits while a refresh or the report of the newest nightly slot is unfinished, past the slot's 2 h`.
  - At slot + 2 h 30: a queued refresh retry (run_after 03:25Z) plus a running report defers to now + 15 min.
  - With the retry failed and the report still running, it still defers.
  - A queued refresh of the previous slot doesn't hold it.
  - Once every slot job is done, failed or skipped, it runs.
- New: `a partial fetch whose failed source is a requested metric's primary fails the job; a failed check alone does not`.
  - It runs the real fetch, then marks one real source failed. The test asserts that the source was in the run.
  - Primary failed: `failed`, `fetch_partial: transfer_flow:...: eth_getLogs: 429 ...`, the start line plus the ALERT,
    and no retry.
  - Only the defillama check of `flow_usd.fees` failed: `done`, and the line ends `; partial: defillama:mini:dailyHoldersRevenue failed`.
- Updated for M-3:
  - The done test: the start line is posted before the fetch runs, and a 65 min scan gives `done in 1 h 05 min`.
  - The failure test: start line plus `failed after 2 min`, and `after 0 min` for the all-sources-failed case.
  - The refusal and deferral tests are unchanged: no start line.

### Evidence
`export ORION_TEST_DATABASE_URL='postgresql://orion_dev@/orion_test?host=/var/run/postgresql'`
- RED (`npx vitest run tests/daemon/backfill.test.ts --maxWorkers=1`): `Tests 4 failed | 5 passed (9)`.
  - done: no start line (`expected [ [] ] to deeply equal [ Array(1) ]`).
  - failure: one post, not two.
  - nightly wait: `BACKFILL_NIGHTLY_RECHECK_MS` undefined.
  - partial: `expected { status: 'done' ... } to match object { status: 'failed' }`.
- GREEN, same command: `Tests 9 passed (9)`.
- `backfill` + `daemon` + `job.cli` at `--maxWorkers=1`: 3 files, `40 passed (40)`.
- Full run (`npx vitest run --maxWorkers=2`): `Test Files 142 passed (142)`, `Tests 1707 passed (1707)`. That is 1705
  plus the 2 new tests, with no failures this run (the migrate OID race didn't recur).
- `npm run typecheck`: clean.

### Concerns
- The ruling wrote the start line as `ORION BACKFILL <asset> started: ...`. I kept `<env>` before the symbol to match
  the done line and every other daemon line (`ORION BACKFILL dev MINI started: ...`).
- The recheck is "now + 15 min", so while a report waits until slot + 3 h the backfill is claimed and deferred about
  4 times. Each deferral is cheap: no attempt used, no post.
- `primaries` is per requested metric only. A sibling scan member pulled in by `buildPlan` shares the same
  `transfer_flow` sourceId, so it is covered too.
