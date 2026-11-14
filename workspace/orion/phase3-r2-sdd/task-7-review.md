# Task 7 review: 6373b45 (R24) + 6c0b54e (prices backfill job + remote verb), range 7202a46..6c0b54e

### Spec Compliance

- ✅ **Spec compliant**, judged against the brief with the R25 departures accepted: the refusal lives in the loader, the ref regex allows upper case, dates use `[0-9]`, op prices gets 3 attempts, a stopped chain fails the job with an ALERT, there is no start line, and progress lives in result_json.
  - Params `{op:'prices', from, to?, refs?}` are a union member (src/db/jobs.ts BackfillPricesParams). The job's asset is null. The run lock is `'prices'` (src/daemon/jobs/backfill.ts:37, 307).
  - The budget is 20 min (`PRICES_BACKFILL_BUDGET_MS`). A run that uses it defers with `untilMs: now` (backfill.ts:324-329), and done carries the summary (backfill.ts:331-348).
  - `backfillWaitUntil` is applied unchanged on every run (backfill.ts:297).
  - CLI `job run-now backfill-prices --from D [--to D] [--refs a,b]` is in src/cli/commands/job.ts. An unknown ref is refused at enqueue (tests/cli/job.cli.test.ts).
  - The remote verb is in orion-remote `v_job`. The verb appears in docs/ops/deploy.md:44-49 and in the orion-remote help text.
  - Every brief Step-1 test exists: lease loss mid-day, nightly-window defer, priority 70 with levels claimed between runs, unknown ref at enqueue, op fetch unchanged.
- ✅ **R24:** a CoinGecko `price` or `market_cap` source is refused at three points:
  - at load (src/config/load.ts parseAssetObject; tests/config/sources.test.ts loadAsset case)
  - at filing (src/agent/tools/write.ts:306 with `ctx.loaded.prices`; tests/agent/tools.test.ts)
  - at approve (src/app/proposals.ts:185 parses with `loadPrices(configRoot)`; tests/app/proposals.test.ts, both fields).

  `circulating_supply` and `total_supply` still load (sources.test). No file under assets/ uses `field: price` (grep).
- ⚠️ **Cannot verify from the diff:** typecheck and lint:promises (not re-run; the reported results are trusted). The real rebuild size against the 30-minute deploy drain wait needs the Task 10 measurement (Minor 3).

### Checks run (worktree rev-t7 at 6c0b54e, removed after)

- vitest, the 9 touched or related files (backfill, job.cli, sources, tools, proposals, combinedHash, levelsJob, refresh, release/orionRemote) at `--maxWorkers=1`: 153/153, output clean.
- `python3 -m unittest scripts/provision/test/test_orion_remote.py`: 66 OK, including a reviewer probe class I added.
  - Probes that exit 64 before Orion runs, with the log line free of arguments:
    - `-- --yes`, `-- --from D`
    - `--refs -x`, `--refs -`
    - `--refs=a`, `--from=D`, `--to=--yes`
    - Arabic-Indic and full-width digits in `--from`, an Arabic-Indic digit in a ref, `é` in a ref
    - a quoted trailing `\n` in `--refs`, single and double quotes
    - a 500-char ref, 41 refs, a ref with a space
    - stray `--by`, `--json`, `--force`, a stray positional, `backfill --from`
  - A bare backslash-newline is refused earlier, by `split_command` (exit 64, generic log line).
  - A 120-char ref using every allowed character class passes through.
  - REF_RE and DAY_RE use explicit ASCII classes, and every check uses `fullmatch`.
- Probe for named risk 1: a queued `refresh` at the newest nightly slot (2026-11-06T00:45Z), run at 12:00Z, defers by `BACKFILL_NIGHTLY_RECHECK_MS` with no writer call. The job gate holds for op prices, not only the clock.
- Probe: a writer result with `stoppedByBudget` and `errors` → `{status:'deferred'}`, no post, the error not logged (Minor 1).
- Daemon path, read from daemon.ts:
  - `record` handles `deferred` with `deferJob` (attempts − 1, priority untouched).
  - A `failed` outcome without `retryAfterMs` is final.
  - The scheduler enqueues every 30 s on its own timer (daemon.ts:541), so the hourly `levels` job is queued while a budget runs and is claimed first after the deferral.
  - A lost lease aborts `ctx.signal` and the result is dropped (daemon.ts:398).
  - Restarts post `ORION RESTARTED … re-queued/failed (lease_expired)` (daemon.ts:223-224), so the third interruption is not silent.
  - A drain does not abort the running job (daemon.ts:476-479): it finishes the current run (Minor 3).

### Named risks

1. **Nightly window / single worker:** pass.
   - Every run re-checks `backfillWaitUntil`: the clock windows are tested, and the job gate is covered by my probe.
   - A run starts at the latest 4 h before the nightly and lasts about 20 min plus one chain-day.
   - A budget deferral returns `untilMs: now`. `deferJob` refunds the attempt and keeps priority 70. The test claims a due `levels` job before the same job id (backfill.test "stopped by its budget").
2. **Double-run / lost work:** pass, with one Important and Minors 2-3.
   - The lease-loss test uses the real writer and fakeRpc: 2026-11-05 is committed, the reap re-queues the job, and the second run makes 25 multicalls, none for 11-05, ending at 48 rows.
   - Runs cannot overlap: the `prices` run lock, plus `run_in_progress` → 30 min defer (tested).
   - Progress is written only on a budget stop, before `deferJob`. A run whose lease was lost adds nothing, and rows come from a DB count, so nothing is counted twice.
   - A drain ends a run at the budget's chain-day boundary, not on the drain itself (Minor 3).
3. **Silence means broken:** pass on the main paths.
   - The done line, the ALERT on a stopped chain, catch-all failures (bad params, lock errors) and the WATCH cap of 20 plus one summary line are all posted and tested.
   - Gaps: Minor 1 (a chain error in a run that also hit its budget) and Minor 4 (a rollback to R1 fails the queued job without a post).
4. **orion-remote verb:** pass. All the requested probe forms exit 64 (above). The verb is in deploy.md's verb reference.
5. **R24:** pass (above). The template carry list in progress.md is incomplete (Minor 9).

### Strengths

- The Review Focus 4 test is real, not mocked. It aborts at a chosen multicall inside a chain-day, asserts the committed day by SQL, reaps through `reapExpired`, and counts the second run's multicalls. It pins "never rewrites a committed chain-day" directly.
- Resuming from `prices` itself, plus `saveJobProgress` used only for the counts, is a small and correct design. `rows` comes from a DB count, so a lost-lease run's committed rows still appear in the done line.
- `ref_list` refuses an item with a leading `-` on its own, so an item cannot pose as an option. Using `[0-9]` instead of `\d` closes the Unicode-digit hole.
- The R24 refusal names the exact path, including cross-checks. The shared fixture `PRICED_INGEST_ASSET_YAML` guards itself against drift (tests/helpers/ingestAsset.ts:1922).
- The 20-min runs mean levels, `snapshot_push` and the prod dead-man ping no longer wait behind a multi-hour backfill.

### Issues

#### Critical (Must Fix)

None.

#### Important (Should Fix)

1. **An open-ended job is re-validated against a moving "today" on every run, and the 400-day cap collides with M4.**
   - Where: src/daemon/jobs/backfill.ts:296 (re-parse with `now`) and :124 (`days` with `to` absent = today).
   - Problem 1: a job queued without `--to` and within 400 days fails mid-rebuild, with an `invalid_backfill_params` ALERT, as soon as a later run's UTC day pushes the span to 401.
   - Problem 2: the documented release command `job run-now backfill-prices --from 2025-10-13` (deploy.md:49; M4 full history from R2's valid_from) spans 398 days today (2026-11-14). From **2026-11-17** it is refused at enqueue. A job queued on 11-15 or 11-16 fails at its first run on or after 11-17.
   - Fix: check the span at enqueue only, or have the CLI pin `to` at enqueue (the handler then never sees an open range). Then either raise the cap for op prices or document the split (two jobs with `--to`) in Task 9's release block.

#### Minor (Nice to Have)

1. **A chain error is silent when the same run also hits its budget.** backfill.ts:324-330 checks `stoppedByBudget` before `errors`. My probe returned `deferred`, with no post and no log. It eventually surfaces, because the run that finishes without a budget stop reports it. Until then, an intermittently failing chain is invisible. Fix: log or post `w.errors` in the deferral branch.
2. **A failure before the writer erases the saved progress.** `result` starts as `null` (runPricesBackfill, `let result = null`). A later run that fails on params, the lock or the DB before the writer then calls `finishJob` with `result: null`, overwriting result_json's earlier runs, calls and work time. Fix: start from `progressOf(job.result)`.
3. **The drain is invisible to the handler.** A deploy's `daemon drain --wait 30m` (orion-remote:88) waits for the current run: 20 min, plus a cold chain-day overrun, plus up to 21 posts (each may retry during a Slack outage). Nothing ties `PRICES_BACKFILL_BUDGET_MS` to `DRAIN_WAIT`, and deploy.md does not say a switch can wait about 20+ min behind a prices run. Document it, or pass the drain to the writer as a stop at the next chain-day.
4. **A rollback to R1 fails the queued job without a post.** The prices job sits `queued` between nearly all runs. Under orion-2026.11.12.1 it fails with "a backfill job needs an asset" (8f50ac6 backfill.ts:146) and nothing is posted. deploy.md:459-463 only covers a `running` backfill and "no handler". Carry to Task 9: after rolling forward, re-queue it (it resumes).
5. **Permanently missing hours are re-read on every run.** Each run walks the whole range newest-first, and the writer re-reads every still-missing hour (backfill.ts:302; writer days loop). Those reads count as `worked` and toward the budget. This costs RPC calls once per run; it is harmless if such hours are rare. Watch it in the Task 10 measurement.
6. **R24 covers only the `coingecko` source type.** An `http_json` cross-check at `api.coingecko.com/.../simple/price` still loads (no host rule in src/config/sources.ts). This is outside R24's letter. Note it for R8, which drops the type.
7. **The lock name shares the asset run-lock namespace.** `PRICES_LOCK = 'prices'` (backfill.ts:37) lives where asset ids do, and ASSET_RE `[a-z0-9-]{1,32}` admits an asset named `prices`. That asset would share the lock. A non-asset-shaped name such as `price-backfill:` would avoid it.
8. **One `saveJobProgress` path is untested.** Its `false` return when the lease is gone (src/db/jobs.ts:203-209) has no test.
9. **The template carry list is incomplete.** All **10** templates use `coingecko … field: price` (docs/templates T1-T10, grep). progress.md:150 and the report list only "T3-T8, T10". T1, T2 and T9 must be in Task 9's carry too. Per the dispatch this is not a Task 7 finding; it is noted for the controller.

### Assessment

**Spec compliance:** ✅ (R24, R25 applied).

**Task quality:** Needs fixes.

**Reasoning:** The resumable job, lock, deferral and priority mechanics are correct and are pinned by real-writer tests. The forced-command verb withstands every injection probe. One fragile behavior remains: an open-ended job re-validated against a moving today can fail mid-rebuild. Together with the 400-day cap, this blocks the documented full-history command from 2026-11-17. That should be fixed, or the split decided, before Task 9 writes the release block.
