# Orion on Postgres: code and test rules

Use when changing the Postgres-backed Orion (Phase 1.5b onward: `pg` pool, `Db` interface `all/one/run/tx`, migrations in `src/db/pg/migrations/`).

## Dev database
- Local Postgres 18 on uranus, Unix socket only, peer auth mapped from `hermes` to role `orion_dev`. Always name the role:
  `ORION_TEST_DATABASE_URL=postgresql://orion_dev@/orion_test?host=/var/run/postgresql`. The suite refuses to start without it.
- Tests get a fresh schema per file in `orion_test`. After any run, check that none are left: `psql -U orion_dev -d orion_test -Atc "select nspname from pg_namespace where nspname like 't\_%'"`.
- Subagents may touch only `orion_test`; give them that rule explicitly.

## Code rules (each one bit during the conversion)
- Inside `db.tx(async (t) => ...)`, call only `t`, and await each call before the next. Never `Promise.all` on a tx handle: nested savepoint names collide, and an outer-`db` call inside a tx deadlocks a pool of 1.
- A nested tx may lock only the asset that its outer tx locked (`tx_asset_mismatch`). Locking two assets in one transaction deadlocks (40P01).
- Advisory locks cover the whole database, so the key includes the schema (`sha256('orion:<schema>:<space>:<id>')`). Keep separate key spaces for the run (session) lock and the per-asset transaction lock, otherwise a refresh deadlocks against its own writes.
- `SUM`/`AVG` over integer columns returns `numeric`, which `pg` hands back as a string. Cast every aggregate the code reads as a number (`::float8` / `::bigint`); `tests/meta/aggregates.test.ts` enforces this.
- Missing `await`s pass typecheck. `npm run lint:promises` (oxlint `--type-aware`, `no-floating-promises`) runs in the suite. The repo's TypeScript 7 rules out typescript-eslint and the TS compiler API, so don't reach for them.
- `tsc` doesn't emit `.sql`, so the build copies `src/db/pg/migrations` into `dist`. Migrations run only via `orion db migrate`, never on open; `openDb` refuses a schema with pending migrations.
- Text that holds a date or a zoned instant exactly as given (e.g. `documents.published_at`) stays `text`. `timestamptz` rewrites it.
- A self-referencing FK to later rows (`observations.superseded_by`) must be `DEFERRABLE`, and the importer defers constraints, because plain FK-order copying can't satisfy it.

## Tests
- Setting `synchronous_commit = off` on the test database removes fsync-bound timeouts in the ingest tests (a 36 s suite instead of timeouts). Apply it only to a database whose name ends in `_test`.
- The SQLite RAISE triggers that tests used for fault injection become plpgsql `RAISE EXCEPTION` trigger functions, dropped in `finally`, because a file's schema outlives each test (tables are truncated, not dropped).
- A `beforeAll` seed doesn't survive the per-test truncate. Assert on values captured in `beforeAll`, or seed in `beforeEach`.

## Importing live SQLite and the row-for-row proof (tools/import-sqlite)
Run it yourself (controller), never in a subagent. It reads a `.backup` of live, and the fetch leg needs a `.env` copy.
1. Put the scratch area outside the worktree: `sqlite3 orion.db ".backup '<P>/snap.db'"`, then `PRAGMA integrity_check`. Copy `snap.db` into `<P>/old/orion.db`, and copy `assets/` (plus `personas/` and `skills/`) into both `<P>/old` and `<P>/new`.
2. `<P>/new/.env` = only `ORION_DATABASE_URL=postgresql://orion_dev@/orion_dev?host=/var/run/postgresql` and `ORION_DB_SCHEMA=proof_<stamp>` (lowercase), mode 600. Migrate with `ORION_HOME=<P>/new node dist/cli/index.js db migrate --json`.
3. Run from the worktree with `npx tsx tools/import-sqlite/cli.ts`:
   - `import --from <snap> --to <url> --schema <s> --assets <wt>/assets --manifest-dir <dir>`, which writes `import-<stamp>.json`.
   - `proof ... --manifest <json>`: per table, the row counts and sha256 must match, `first_mismatch` must be null, and each table's next id must equal its `sqlite_sequence` + 1.
   - `reports --old-cli <sqlite release>/dist/cli/index.js --old-home <P>/old --new-cli <wt>/dist/cli/index.js --new-home <P>/new --day <D> --manifest <json> --out <dir>`. Expect 15 identical files for 13 assets: `report yield` per asset, plus the anomalies list and the proposals list.
4. Expected exclusions, which you should report: observations of metrics no YAML declares any more, all `revenue_run_rate_usd`, whose count grows until the cutover; non-disclosure transcripts; `assumption_value` proposals; and the whole tables `config_versions`, `run_locks` and the valuation-era tables. Group the excluded ids by `metric_key` in the snapshot to prove what they are.
5. Fetch leg: `data fetch <a> --dry-run --json` on both sides, reduced to the written metric keys plus `sourceId:status`. For a change that should alter only which calls are made (a block cache, finalized-block bounds, a request cache), also compare the written VALUE per `(metric_key, observed_at)`, since matching keys don't prove matching values. When both sides run on Postgres, one schema migrated by the newer release serves both, because an older release opens a newer schema. Save the raw JSON per asset first, then reduce it with a separate `.py` file. This needs a live `.env` copy with the `ORION_HOME=` line removed. Delete both copies, and drop every `proof_*` schema in `orion_dev`, at the end.
6. Build the SQLite release for the old side in a detached `.worktrees/` checkout of the pre-conversion main (`npm ci`, `npm run build`), not under `$TMPDIR`.
- A comparison that reports "identical" must also require non-empty, parseable output on both sides. A broken reducer, a wrong CLI path or a crashed command prints nothing on either side, and empty `cmp`s equal: count the sources and metric keys per asset and refuse zero.
- Put any reducer or summariser in its own `.py` file (write_file, then `python3 <file> <dir>`), never as `python3 -c '...'` inside a bash script. Nested quote escaping (`\"` inside single quotes) is a Python SyntaxError that the `| reduce` pipe swallows, leaving both sides empty.
- Write the proof as a script that saves every result to files, and inspect it by reading those files. Never re-invoke the script (e.g. `bash proof.sh | head`) just to view output: that runs the import again and leaves a second schema behind.

## Proving a conversion step changed nothing
- **Using a packaged release as the old side** (`/home/hermes/orion-releases/<tag>.tgz`, check its `.sha256` from that dir): extract under `$TMPDIR`, then `ln -s <worktree>/node_modules <release>/node_modules` (releases ship without `node_modules`; confirm `package-lock.json` is identical first). A release refuses to run unless both `ORION_HOME` and `ORION_ENV_FILE=<home>/.env` are set, and it reads assets/personas/skills from the release dir itself, never from the home. Unset every inherited `ORION_*` var before each run so only the home's `.env` picks the DB. Phase 2 packages this as `tools/phase2-proof/` (snapshot.sh, reports.sh, compare.py, expected.py, cleanup.py; README there).
- **Worktree on a Postgres-stacked base** (e.g. `feat/daemon`): run `npm ci` in the worktree. The live tree's `node_modules` (main, SQLite) has no `pg`, and symlinking another session's worktree `node_modules` breaks when that worktree is removed at cutover. Export `ORION_TEST_DATABASE_URL` before the baseline run, or vitest prints a misleading "No test files found" next to the real error.
After each conversion task, build the branch and run old release vs new on two fresh `.backup` copies of live: `report yield <a> --day <fixed D> --json` x all assets, plus `data anomalies --all --json`, `proposals list --json`, `inbox --json` and `agent runs list --json`, each pair compared with `cmp`. `data sources` differs only in `ageDays`, which follows the clock, so exclude that field. Delete the scratch homes afterwards.
