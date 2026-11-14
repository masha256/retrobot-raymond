# Task 7 report: R24 config fixes + `backfill op: prices` and its remote verb

Status: DONE (two commits, suite green).

## Commits
- `6373b45` fix(config): refuse CoinGecko price sources; proposal filing checks price refs (Ruling R24)
- `6c0b54e` feat(daemon): resumable prices backfill job and its remote verb

## Commit 1 (R24)
- `src/config/sources.ts`: `COINGECKO_PRICE_FIELDS = {price, market_cap}` and `coingeckoPriceIssues(asset)`, which names each
  `metrics.<k>.source` / `metrics.<k>.cross_checks.<i>.source` that reads one:
  `coingecko field "price" is refused: no CoinGecko price is read (Phase 3 R2); a token's USD price comes from prices.yaml (adapter price.token)`.
  `circulating_supply` and `total_supply` still load.
- `src/config/load.ts` parseAssetObject: runs it when the asset is parsed with a non-empty prices map. That covers load
  (loadAsset passes the home's prices.yaml), approve (proposals.ts parses with loadPrices(configRoot)) and filing (below).
  parseAssetObject/parseAssetYaml now take a `ReadonlyMap` (they only read it).
- `src/agent/tools/write.ts:306`: filing parses with `ctx.loaded.prices`, so an unknown price ref (and a CoinGecko
  price) is refused at filing, not only at approve.
- **Departure (where the refusal lives):** the dispatch said "the source schema refuses". Done in the zod schema
  (tried first, measured): 495 failing tests in 49 files, because the two shared fixtures (`INGEST_ASSET_YAML`,
  `AGENT_ASSET_YAML`, used by ~45 files) and 8 onboarding templates (docs/templates T3-T8, T10) use
  `{ type: coingecko, field: price }`. So the rule runs in the loader, gated on prices.yaml being present, the same gate
  the existing R2 "usd flow needs a prices.yaml entry" rule uses. Every production path has prices.yaml; a test home
  without one has no price rules. Four tests that do copy a prices.yaml into a home with the mini fixture now use the
  new `PRICED_INGEST_ASSET_YAML` (the same asset with price_usd entered by hand, no source): combinedHash (2 tests; the
  fetched metric they check is now circulating_supply), levelsJob (2; one row count 5 -> 4), refresh (1).
- **market_cap** is refused as well (CoinGecko price x CoinGecko supply = a CoinGecko price read). No asset uses it.

RED -> GREEN: 4 new tests failed first (sources.test x2, tools.test filing, proposals.test approve: "expected '' to
match", "promise resolved instead of rejecting", "isError false"); then 109/109 in the three files; full suite
1893/1893 (151 files), typecheck clean, lint:promises exit 0.

## Commit 2 (Task 7)
- `src/db/jobs.ts`: `BackfillParams = BackfillFetchParams | BackfillPricesParams` (`{ op: 'prices'; from; to?; refs? }`).
  `PRICES_BACKFILL_MAX_ATTEMPTS = 3` used by enqueueJob for op prices (op fetch stays 1). `saveJobProgress(db, id, owner,
  result)` stores result_json on a running job under its lease (claimNextJob/deferJob leave result_json alone).
- `src/daemon/jobs/backfill.ts`:
  - `parsePricesBackfillParams(raw, prices, now)`: strict keys; real calendar days; from <= to <= today (UTC); span
    (both days counted) <= BACKFILL_MAX_DAYS 400; refs non-empty, unique, each in prices.yaml
    (`ref X is not in prices.yaml`). `invalid_backfill_params`.
  - `runPricesBackfill` (asset null + op prices): backfillWaitUntil unchanged; `withRunLock(db, 'prices', 'daemon backfill
    prices pid N')`; writeChainPrices over [from 00:00Z, min(to + 1 day, top of the current hour)) for refs (default:
    every prices.yaml ref, sorted; valid_from clipping is the writer's), `budgetMs` 20 min (`PRICES_BACKFILL_BUDGET_MS`),
    `signal: ctx.signal`, `clock: ctx.clock`.
  - stoppedBySignal / aborted -> `aborted` outcome, nothing posted or saved. stoppedByBudget -> breach lines posted,
    progress saved on the row, `{ status: 'deferred', untilMs: now }` (deferJob: attempts - 1, priority kept at 70).
    WriteResult.errors (a chain the writer stopped) -> failed, one `ORION ALERT <env> backfill prices failed after X:
    price_chain_stopped: <chain> stopped at <iso>: <err>` (not specified in the dispatch; my choice; re-queueing resumes).
    run_in_progress -> deferred REFRESH_LOCKED_RETRY_MS (as op fetch).
  - done: one line `ORION BACKFILL <env> prices done in <work time> (<from>..<to|now>, N runs): CRV 9000 rows, ...;
    oldest hour <iso|none>; missing <reason n, ...|none>; calls <chain n, ...>; breaches N`. Rows per ref = stored rows
    in range under the ref's primary source (a DB count, so rows committed by a lease-lost run count too); calls,
    breaches, runs and work time accumulate over runs (job row); missing = the final run's (it re-reads every hour still
    missing in the range, so accumulating would double-count).
  - Breaches each run: `formatPriceBreach` lines (as levels/refresh), at most 20 (`PRICES_BACKFILL_WATCH_MAX`) plus
    `ORION WATCH <env> price backfill: N more breaches not posted (M this run); the prices rows carry check_gap_pct`.
  - No start line for op prices (it would repeat on every 20-min run).
- `src/cli/commands/job.ts`: `job run-now backfill-prices --from D [--to D] [--refs a,b]` -> kind backfill, asset null,
  checked by parsePricesBackfillParams against the home's prices.yaml and ctx.now() before enqueue. Refuses an asset
  (`asset_not_allowed`), `--metric/--backfill-days/--slot/--force` (`invalid_option`), a missing --from; and
  `--from/--to/--refs` on any other kind.
- `scripts/provision/files/orion-remote`: verb `job run-now backfill-prices --from D [--to D] [--refs r1,...]`, dates
  `pattern(DAY_RE)` (`^[0-9]{4}-[0-9]{2}-[0-9]{2}$`, fullmatch; `[0-9]` not `\d`, which matches Unicode digits), refs via
  `ref_list`: <= 40 items, no empty item, no item starting with '-', each `REF_RE` fullmatch. Passes `--refs` joined.
  JOB_KINDS unchanged (tests/release/orionRemote.test.ts pins it).
- **Departure (ref regex):** `^[A-Za-z0-9:/._@-]{1,120}$`, not the dispatch's `[a-z0-9:/._@-]`: PUMP's ref is
  `solana:mainnet/pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn` (base58, upper case); the lower-case pattern refuses it.
- `docs/ops/deploy.md`: the verb in the R1 "Verb reference" block beside `job run-now backfill`.

### Tests (RED -> GREEN)
- tests/daemon/backfill.test.ts, 9 new: params; range/refs/budget/signal/lock holder (fake writer); defers in the nightly
  window and on a held `prices` lock with nothing written; **budget defers to now, keeps priority 70, a levels job
  claims first, done after the second run, 48 rows, done line with cumulative calls** (real writer, fakeRpc Base VVV
  chain copied from writer.test); **lease lost mid-day (abort at multicall 28, inside 2026-11-04): 2026-11-05 committed,
  reapExpired re-queues (not fails), second run makes 25 multicalls (none for 2026-11-05), 48 rows** (Review Focus 4);
  signal stop posts nothing; done line + 20 WATCH + summary, no anomaly; chain error -> ALERT; bad params / prices params
  on an asset / fetch without asset.
- tests/cli/job.cli.test.ts, 2 new: queue (asset null, priority 70, maxAttempts 3, text lines) and refusals (unknown
  ref, missing --from, after today, from > to, 401 days, empty refs, bad day, asset, stray options).
- RED: 11 failing (`unknown option '--from'`, undefined exports, etc.); GREEN 23/23 in the two files.
- scripts/provision/test/test_orion_remote.py, 2 new (passthrough incl. HYPE '@' and PUMP upper case, 40 refs, 120 chars;
  refusals incl. `--refs=--yes`, `--refs --yes`, `a,-b`, trailing newline in --from/--to/--refs, Unicode digit, 41 refs,
  121 chars, other kinds with --from/--to/--refs). RED with the old script: test_backfill_prices_passthrough failed
  (the refusal test passes on the old script, which refuses the unknown kind). GREEN: 54 OK (was 52).

### Final runs
- `npx vitest run --maxWorkers=2`: 1904/1904 passed, 151 files (no load-sensitive timeouts this run).
- `npm run typecheck`: clean. `npm run lint:promises`: exit 0. `python3 -m unittest scripts/provision/test/test_orion_remote.py`: 54 OK.

## Self-review / concerns
1. R24 refusal is loader-level gated on prices.yaml, not schema-level (above). A config parsed without prices (tests,
   docs/templates test) still accepts a CoinGecko price; **8 onboarding templates (docs/templates T3-T8, T10) still
   template `field: price`**: an asset onboarded from them now fails to load in any real home. They need a
   `price.token` ref placeholder (not in my file list; flag for a follow-up/R8).
2. Lease-loss re-queue needed max_attempts > 1 for op prices (3). Budget deferrals don't consume attempts; only lost
   leases/restarts do, so a third interruption fails the job (lease_expired) and the operator re-queues it (it resumes).
3. Work time and calls exclude any run whose lease was lost (its progress isn't saved); rows are DB counts so they don't.
4. The done line names `..now` when --to is absent; with 17 refs it is ~600 chars (slackClean cap 2000).
5. The `prices` run lock is taken only by this job; the hourly levels writer doesn't take it (it doesn't need to: one
   daemon worker; the writer is idempotent per hour). Task 8's `data reprice` should take the same lock name if it must
   exclude the backfill.


## Fix round 1 (task-7-findings.md items 1-5; rulings R27, R28)

Env for every command: `export ORION_TEST_DATABASE_URL='postgresql://orion_dev@/orion_test?host=/var/run/postgresql'`.
RED command (all items, tests written first): `npx vitest run tests/daemon/backfill.test.ts tests/db/purge.test.ts tests/cli/job.cli.test.ts --maxWorkers=1`
-> `Test Files 3 failed (3); Tests 8 failed | 38 passed (46)`. GREEN, same command after the fix: `Test Files 3 passed (3); Tests 46 passed (46)`.

1. **R27, range frozen at enqueue, cap 550 for op prices** (src/daemon/jobs/backfill.ts, src/cli/commands/job.ts).
   - `parsePricesBackfillParams(raw, prices)` is now the handler's shape check only: no span cap and no "today". It still checks from <= to and refs.
   - The new `pricesBackfillRequest(raw, prices, now)` is the enqueue check, used by the CLI. It freezes `to` (no --to: today UTC) and stores it, refuses to/from after today, and refuses a span over `PRICES_BACKFILL_MAX_DAYS = 550`. `BACKFILL_MAX_DAYS` stays 400 for op fetch.
   - A job stored without `to` (queued before this fix) runs open-ended to the last completed hour.
   - Tests:
     - backfill.test "the constants; the enqueue check freezes to...": no-to stores `to: 2026-11-14`; 550 days accepted, 551 refused; 2025-10-13 fits on 2027-04-15; the run parse accepts a 1049-day stored span.
     - New "a stored job runs whatever its span is against today": 584-day stored span and a no-to job from 2025-04-01 both run.
     - job.cli: no --to stores `to: 2026-11-03` and the text line reads `2026-11-03..2026-11-03`; 550 days (2025-05-03) is queued; 551 (2025-05-02) is refused.
   - RED evidence:
     - the constants test: `expected 1200000 to be 600000`
     - the stored-span test: `expected 'failed' to be 'done'`
     - job.cli: `expected {...} to match object` (params had no `to`)
2. **Chain error kept when deferring.** When a budget stop has `w.errors`, the run logs and posts one line, then defers: `ORION ALERT <env> backfill prices: price_chain_stopped: <chain> stopped at <iso>: <err>; the job defers (budget used) and its next run reads the chain again`.
   - Test: "a run that uses its budget and has a chain error defers, and still posts and logs one ALERT line" (deferred to now, posts == [alert], logs contain it).
   - RED: `expected [] to deeply equal [ Array(1) ]`.
3. **Progress merged.** `result` starts as the row's saved prices progress (`progressOf(job.result)` when `job.result.op === 'prices'`), not null. A failure before the writer starts (params, lock, DB) keeps the earlier runs' counts.
   - Test: "a later run that fails before the writer keeps the progress saved by the earlier runs" (bad ref; the result equals the saved progress).
   - RED: `expected { Object (status, result, ...) } to match object` (result was null).
4. **R28, 10-min runs.** `PRICES_BACKFILL_BUDGET_MS = 10 * 60_000`.
   - The doc line is in deploy.md's verb reference and the constant's comment: "A drain (deploy, rollback: 30 min wait) waits for the current run's budget (<= 10 min + one chain-day)". The orion-remote help text and the CLI `--to` help are updated too.
   - Test: the constants test pins 10 min, and the range test checks the writer got `budgetMs === PRICES_BACKFILL_BUDGET_MS` (10 * 60_000).
   - RED: `expected 1200000 to be 600000`, and the range test's deep-equal failed.
5. **Namespaced lock.** `PRICES_LOCK = 'job:prices'` (backfill) and `PRICES_RUN_LOCK = 'job:prices'` (src/db/purge.ts, Task 8's purge-prices) are repointed together.
   - Tests:
     - backfill "the run lock is `job:prices`, so a run lock held for an asset named `prices` does not block it" (an asset lock `prices` is held; the job finishes done under the `daemon backfill prices` holder).
     - purge.test pins `PRICES_RUN_LOCK` equal to PRICES_LOCK and to `'job:prices'`.
   - RED: `expected 'deferred' to be 'done'` and `expected 'prices' to be 'job:prices'`.

Files: src/daemon/jobs/backfill.ts, src/cli/commands/job.ts, src/db/purge.ts, scripts/provision/files/orion-remote (help
text only), docs/ops/deploy.md, tests/daemon/backfill.test.ts (+4 tests, 2 edited), tests/cli/job.cli.test.ts, tests/db/purge.test.ts.

Final runs:
- `npx vitest run --maxWorkers=2`: 1928/1928 passed, 154 files (was 1924; +4). No load-sensitive timeouts, so nothing needed a rerun.
- Focused: backfill + purge + job.cli 46/46; reprice.cli + release/orionRemote 5/5.
- `python3 -m unittest scripts/provision/test/test_orion_remote.py`: Ran 59, OK (1 skipped).
- `npm run typecheck`: clean. `npm run lint:promises`: exit 0.

Notes:
- The CLI text line for a no-to job now prints the frozen day (`2026-11-03..2026-11-03`), not `..today`.
- The done line names `..now` only for a legacy job stored without `to`.
- A budget-deferred chain error posts once per such run. A chain that keeps failing therefore posts one ALERT every 10 min until a run ends without a budget stop and fails the job. I accepted that; it is not silent.
- Deferred to the ledger, as the findings say: permanently missing hours are re-read on every run; R8 http_json; the untested lease-gone save path. The rollback and templates T1-T10 items carry to Task 9.
