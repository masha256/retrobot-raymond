# Task 2 report: `orion data purge`

Status: DONE. Commit `b31c224 feat(data): data purge (dry run by default; exports the rows before deleting)` on
feat/phase3-third-party (on top of a6c78d2; Task 1 files untouched).

## What

- `src/db/purge.ts`: `purgeMetrics(db, loaded, { metrics, sourceType?, apply, exportDir, now }) -> PurgeResult`, plus
  `SOURCE_TYPES` and `exportFileName`.
  - Dry run (`apply: false`): runs every refusal and count, writes nothing (no lock, no export dir).
  - Apply: `withRunLock(db, asset, lockHolder('orion data purge'), now, ...)` around ONE `db.tx(..., { lockAsset })`:
    plan (all refusals and counts) -> read every deleted row with `to_jsonb` (all columns) -> write the export (mkdir 700
    + chmod 700, `open(..., 'wx', 0o600)`, write, fsync) -> `UPDATE observations SET superseded_by = NULL` inside the
    set -> `DELETE` by id (row count checked against the plan, else `purge_conflict`) -> side-state deletes.
    No export file when there is nothing to delete (`exportFile: null`, `applied: true`).
  - Refusals, all checked for every metric before anything is written (one refused metric refuses the whole request),
    on the dry run too: `purge_no_metric`, `invalid_source_type`, `purge_configured_metric` (configured, no
    `--source-type`), `purge_live_source` (the type equals `sourceTypeOf(def, metrics)`, or the current source has no
    known rung = null), `purge_open_anomaly` (an `open` anomaly on asset+metric_key), `purge_dangling_reference` (a row
    outside the set whose `superseded_by` points into it; any asset/metric), `purge_export_failed`.
  - Export file: `$ORION_HOME/purged/<asset>-<metric>[+<metric>...]-<YYYYMMDDTHHMMSSZ>.json`, JSON
    `{ asset, metrics, sourceType, createdAt, perMetric, observations[], latestLevels[], watchState[], fetchCursors[] }`.
    `observations` holds `superseded_by` as it was before the purge cleared it.
- `src/cli/commands/data.ts`: `data purge <asset> --metric <k> (repeatable) [--source-type <t>] [--yes] [--json]`,
  wrapped in `guarded` (JSON error + exit 1). Without `--yes` the last line is
  `dry run: nothing deleted; --yes deletes and exports to <ORION_HOME>/purged`; with it,
  `deleted; exported to <file> sha256 <hex>`.

## Side state and fetch_cursors ownership

Side state (latest_levels, watch_state, fetch_cursors) goes only with a metric that is gone entirely: not configured,
and no row of it left after the purge (so an orphan purged with `--source-type` that leaves other rows keeps it). A
configured metric's side state belongs to its live source and is never touched (the brief's "leaves
latest_levels/watch_state alone"; I applied the same rule to its cursors).

Cursor ownership was determined from the code that builds scan keys:
- `src/ingest/run.ts:287` (API flow series, `apiFlow.ts`): `scanKey = \`${batch.sourceId}>${metricKey}\`` — one cursor
  per metric, so it belongs to that metric alone. Matched with `right(scan_key, length(m)+1) = '>' || m` (no LIKE, so
  `_` in a metric key is literal).
- `src/ingest/plan.ts` `flowScanKey` (transfer scans): `sha256(token|sink|allowlist).slice(0,16)` — shared by every
  metric that scan feeds and never names a metric, so it is never deleted (pinned in the orphan test: the hash cursor
  stays).

## Tests (TDD)

RED:
- `tests/db/purge.test.ts` before `src/db/purge.ts` existed: `Failed to load url ../../src/db/purge.js` (1 file failed, no tests).
- `tests/cli/purge.cli.test.ts` before the CLI verb: 3/3 failed, `CommanderError: error: unknown command 'purge'`.

GREEN: `npx vitest run tests/db/purge.test.ts tests/cli/purge.cli.test.ts --maxWorkers=1` -> 13/13.

`tests/db/purge.test.ts` (10), fixture asset `purg` written in the test (ruling R2: `unlocks_next_year` on a
`constant` source; `flow_usd.fees` hand-entered = disclosure; `flow_usd.llama_fees` is the orphan):
dry run counts and writes nothing; orphan deletes observations/latest_levels/watch_state and the cursor naming it (the
shared hash cursor, another asset's row and a kept metric stay); configured needs `--source-type`; live source refused
(constant, and disclosure for a hand-entered metric; a mixed request with an orphan deletes nothing); configured +
third_party deletes only those rows (one superseded by a kept disclosure row), keeps disclosure/constant rows and the
side state; open anomaly refused, allowed once resolved; dangling reference refused and rolled back (superseded_by
unchanged, no export, dry run refuses too); export file name, sha256, mode 700/600, every column of every deleted row
equals `to_jsonb` before; export can't be written (dir under a regular file) -> `purge_export_failed`, nothing deleted;
empty metric list / unknown source type.
`tests/cli/purge.cli.test.ts` (3): dry-run text lines exactly incl. the dry-run line; `--yes` export path + printed
sha256 and the deletion; refusal codes under `--json` with exit 1 and nothing written.

Full suite, `npx vitest run --maxWorkers=2`:
- run 1 (before fixing two meta-guard hits): 2 failed / 1703 passed — `tests/meta/aggregates.test.ts` (my
  `COALESCE(sum(value), 0)::float8` -> fixed to `COALESCE(sum(value)::float8, 0)`) and `tests/meta/awaits.test.ts`
  (an un-awaited `purgeMetrics` returned from the withDb arrow -> awaited). Both mine, fixed.
- run 2 (final tree): 142 files, 1704 passed / 1 failed / 1705. The failure: `tests/db/pg/migrate.test.ts > migrate >
  0003 applies after 0002 and the constraint name anomalies_kind_check exists before it` with `could not open relation
  with OID ...` (a catalog race against another file's schema drop under parallel load). Rerun alone at
  `--maxWorkers=1` twice: 11/11 both times. Not touched by this task (no migration change).
- Baseline 1692 (140 files) + 13 new tests (2 files) = 1705 (142).
- `npm run typecheck` clean; `npm run lint:promises` clean. No `t_*` test schemas left. No hash pin moved (no asset or
  schema change).

## Files

- Created: `src/db/purge.ts`, `tests/db/purge.test.ts`, `tests/cli/purge.cli.test.ts`
- Modified: `src/cli/commands/data.ts`

## Self-review / deviations

- Signature: `purgeMetrics(db: OrionDb, ...)` instead of the brief's `Db`, because the run lock (`withRunLock`) needs
  `tryAssetRunLock`; `OrionDb` is `Db` plus that. `src/db/purge.ts` thus imports `src/app/lock.ts` (the only db -> app
  import; no cycle, no layering guard exists). Alternative if preferred: take the lock in the CLI and keep `Db`.
- `PurgeResult` gains `exportSha256: string | null` (the brief requires the sha256 printed).
- `firstDay`/`lastDay` are the UTC date of `observed_at` (a daily flow row is stamped at day end, so it is the day after
  the covered day); `valueSum` sums every deleted row, superseded ones included.
- Repeated `--metric` values are deduplicated, not refused.
- Refusals apply on the dry run too, so the dry run shows what `--yes` would hit.
- If the commit itself failed after the export was written, the export file would remain for rows not deleted (the
  delete/commit has no other failure path short of a DB error); the file is named with the stamp and never overwritten.

## Concerns

- Orion-remote does not expose `data purge` yet (Task 3's scope).
- The `migrate.test.ts` catalog-race flake under `--maxWorkers=2` is pre-existing behaviour, worth a ledger note.


---

## Fix round 1 (task-2-findings.md: I-1, Minors 1-5)

### Changes (src/db/purge.ts; data.ts needed no change)
- **I-1:** `writeExport` now fsyncs the export directory after the file (open 'r' + fsync + close), and, when
  `mkdirSync` reports it created directories, every created level's parent up to the first existing one
  (`$ORION_HOME` on the first purge). All inside the existing `try`, so a failure is `purge_export_failed` before any
  UPDATE/DELETE. Test seam: `PurgeOptions.syncDir?: (dir) => void` (defaults to the real `fsyncDir`).
- **M1:** config-only refusals moved into `checkConfigured(loaded, metrics, sourceType)`, called in `purgeMetrics`
  before the dry-run/apply branch, so before `withRunLock` (no `abandonRunningRuns` on a refused `--yes`, and the same
  code while a refresh holds the lock). `planPurge` still calls it, so the in-transaction re-plan is unchanged.
- **M5:** `exportFileName` = `<asset>-<first metric>[+N]-<UTCstamp>.json`; the JSON still lists every metric. The CLI
  test's two-metric name became `purg-flow_usd.llama_fees+1-20261112T120000Z.json`.
- Unknown metrics: an unconfigured metric has no config refusal (it is an orphan by definition), so nothing moved there.

### Covering tests
- tests/db/purge.test.ts (new):
  - `apply fsyncs the export directory, and its parent when the purge created it; a failed directory fsync is purge_export_failed, nothing deleted` (I-1): synced = [exportDir, home] on first purge, [exportDir] later; failing seam -> purge_export_failed, counts unchanged.
  - `refuses a configured metric whose current source has no known source type (live === null)` (M2): metric with `fetcher: scripted`, no source; dry run and apply both purge_live_source.
  - `config refusals come before the run lock ...` (M1): a `running` agent run stays `running` after refused `--yes`; with `tryAssetRunLock('purg', 'tick pid 999')` held, dry run and `--yes` both give purge_configured_metric / purge_live_source.
  - `run_in_progress: another holder has the asset run lock ...` (M4): `--yes` -> run_in_progress, counts unchanged, no export dir; dry run still counts.
  - `export file name: the first metric plus +N ...` (M5): unit cases + a 40-metric applied purge writes `purg-flow_usd.retired_series_number_0+39-...json`.
- tests/cli/purge.cli.test.ts (M3): every refusal looped over `--yes` and no `--yes`, same code, exit 1.

### RED (before the fix)
`npx vitest run tests/db/purge.test.ts tests/cli/purge.cli.test.ts --maxWorkers=1` -> `Tests 4 failed | 14 passed (18)`:
- fsync test: `AssertionError: expected [] to deeply equal [ …(2) ]` (seam never called: no directory fsync).
- before-the-lock test: `expected 'error' to be 'running'` (refused `--yes` took the lock and abandoned the run).
- file name test: `Received: "purg-flow_usd.llama_fees+unlocks_next_year-20261112T120000Z.json"`.
- CLI `--yes exports ...`: old file name.
The live===null (M2), run_in_progress (M4) and CLI no-`--yes` parity (M3) tests passed before the fix: they pin
existing behaviour that was untested, as the findings describe.

### GREEN
- Focused: same command -> `Test Files 2 passed (2)`, `Tests 18 passed (18)`.
- Full: `npx vitest run --maxWorkers=2` -> `Test Files 142 passed (142)`, `Tests 1712 passed (1712)` (1707 + 5 new); no flake this run.
- `npm run typecheck` -> clean.

### Concerns
- The directory fsync is exercised for real by the existing apply test (default `syncDir`); only the failure path uses the seam.
