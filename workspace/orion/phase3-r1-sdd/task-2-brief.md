### Task 2: `data purge` (dry run by default, export before delete)

**Files:**
- Create: `src/db/purge.ts`, `tests/db/purge.test.ts`
- Modify: `src/cli/commands/data.ts`, `tests/cli/cli.test.ts` (or a new `tests/cli/purge.cli.test.ts`)

**Interfaces:**
- Produces: `purgeMetrics(db: Db, loaded: LoadedAsset, opts: { metrics: string[]; sourceType?: SourceType; apply: boolean; exportDir: string; now: Date }): Promise<PurgeResult>`.
  `PurgeResult = { asset; perMetric: { metric; configured: boolean; observations: number; superseded: number; firstDay: string|null; lastDay: string|null; valueSum: number; latestLevels: number; watchState: number; fetchCursors: number }[]; exportFile: string|null; applied: boolean }`.

- [ ] **Step 1: Tests** in `tests/db/purge.test.ts`, seeding observations with provenance on the test DB:
  - `dry run counts and writes nothing`: the counts match the seed, and the row counts are unchanged afterwards.
  - `orphan metric: deletes observations, latest_levels, watch_state and the fetch_cursors whose scan_key names it`.
  - `configured metric needs --source-type`: without it, `purge_configured_metric`.
  - `refuses the current source's type`: unlocks_next_year configured on `schedule.unlocks_next_year` (disclosure)
    with `--source-type disclosure` gives `purge_live_source`.
  - `configured metric + third_party`: deletes only the `source_type = 'third_party'` rows, keeps the disclosure rows,
    and leaves latest_levels/watch_state alone.
  - `open anomaly on the metric`: `purge_open_anomaly`.
  - `a kept row references a deleted row`: `purge_dangling_reference`, rolled back.
  - `apply writes the export first`: one JSON file with every deleted row (all columns) whose sha256 is printed. If
    the export can't be written, nothing is deleted.
- [ ] **Step 2: Implement** `purgeMetrics`. One transaction holding the asset run lock. Within the set, clear
  `superseded_by` before the delete (the self-referencing FK). `exportDir` = `$ORION_HOME/purged`, mode 700, file 600.
- [ ] **Step 3: CLI** `data purge <asset> --metric <k> (repeatable) [--source-type <t>] [--yes] [--json]`. Without
  `--yes` it prints the dry run and the line `dry run: nothing deleted; --yes deletes and exports to <dir>`.
- [ ] **Step 4: Run** the tests, the full suite and typecheck.
- [ ] **Step 5: Commit** `feat(data): data purge (dry run by default; exports the rows before deleting)`.

