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

## Proving a conversion step changed nothing
After each conversion task, build the branch and run old release vs new on two fresh `.backup` copies of live: `report yield <a> --day <fixed D> --json` x all assets, plus `data anomalies --all --json`, `proposals list --json`, `inbox --json` and `agent runs list --json`, each pair compared with `cmp`. `data sources` differs only in `ageDays`, which follows the clock, so exclude that field. Delete the scratch homes afterwards.
