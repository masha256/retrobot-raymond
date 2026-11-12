# Task 2 review: `orion data purge` (a6c78d2..b31c224)

Line numbers are file lines at b31c224 (from the diff hunks). One pass over the 760-line package; four focused checks
outside the diff, one per named risk (listed under each risk). No test was run: no doubt came up that the existing
runs don't answer.

### Spec Compliance

- ✅ Spec compliant. Every brief item is in the diff:
  - `purgeMetrics` with the brief's options and result shape (`src/db/purge.ts:76-118`). Two deviations, both
    accepted: `OrionDb` instead of `Db` (ruling R13), and `exportSha256` added (needed to print the sha256).
  - One transaction holding the run lock (`:87-117`). `superseded_by` is cleared inside the set before the delete (`:106`).
  - Export at `$ORION_HOME/purged`, directory mode 700, file mode 600 (`:225-235`; CLI `data.ts:226`).
  - CLI verb with a repeatable `--metric`, plus `--source-type`, `--yes` and `--json` (`data.ts:214-233`). The dry-run
    line matches the brief word for word (`data.ts:65`).
  - All eight brief tests are present (`tests/db/purge.test.ts:116-266`, CLI `tests/cli/purge.cli.test.ts:61-111`).
  - The fixture follows ruling R2: `unlocks_next_year` on a `constant` source (`tests/db/purge.test.ts:23-38`).
- ✅ Nothing extra beyond small helpers (`SOURCE_TYPES`, `exportFileName`).
- ⚠️ Cannot verify from the diff: whether the brief's "leaves latest_levels/watch_state alone" for a configured metric
  is the right call. After a `third_party` purge, `latest_levels` (which has a `source_type` column) may still hold a
  third-party value until the next levels job. The brief mandates it. The controller should confirm that Task 7's
  report/levels refresh overwrites it.

### Strengths

- Every refusal runs through one `planPurge` in both modes (`purge.ts:84,89`), so the dry run shows the refusal that
  `--yes` would hit. The DB tests pin this for `purge_configured_metric` and `purge_dangling_reference`
  (`purge.test.ts:155,226`).
- Deletes go by the id list planned inside the locked transaction, and the row count is checked
  (`purge.ts:107-108`). No predicate is re-evaluated at delete time.
- The export uses `to_jsonb(o)`, so no column list can drift (`:204`). The test compares it column for column with a
  `to_jsonb` snapshot taken before the purge, `superseded_by` included (`purge.test.ts:231-247`).
- The cursor match uses `right(scan_key, len+1) = '>'||m` instead of LIKE (`:121`), with a test that the shared hash
  cursor survives (`purge.test.ts:147`). Every statement filters on `asset_id`, and the test includes an `other` row
  on the same key (`purge.test.ts:103,143`).
- Opening the export with `'wx'` means an earlier export can never be overwritten (`:228`).

### Named risks

1. **Irreversible loss: mostly closed, one durability gap.**
   - The export is written and the file fsynced before the first UPDATE or DELETE (`purge.ts:96-102` then `:105`).
     If the export can't be written, the function throws before any write (test `purge.test.ts:253-260`).
   - The row set has no status or superseded filter (`:157-160`), so rejected and superseded rows are deleted *and*
     exported.
   - The export loses nothing: `value` and `period_days` are `double precision`, ids are bigint below 2^53, and
     `hourly_amounts` is a jsonb array of strings (checked `0001_baseline.sql:5,9`, `0005_tokens_prices.sql:35,81`).
   - No other table references `observations` (only `superseded_by`, NO ACTION, `DEFERRABLE INITIALLY IMMEDIATE`;
     checked by grepping `REFERENCES` across `src/db/pg/migrations`). So no cascade deletes unexported rows.
   - A failure between export and commit rolls back the deletes and leaves only a spare export file. That is benign.
   - Gap: the export directory is never fsynced (Important #1).
2. **Over-deletion: closed.**
   - A configured metric's row set is filtered by `source_type = $3` (`:158`). Its side state is never touched,
     because `gone` requires `!configured && kept === 0` (`:172`).
   - The live rung is computed with `sourceTypeOf(def, config.metrics)` (`:138`), the same call `fetchedProvenance`
     uses to stamp rows (checked `src/provenance/locator.ts:114`). So a derived metric that inherits `third_party`
     refuses `third_party`, consistently.
   - The shared transfer-scan cursor (a hash key) is never matched. `asset_id` is on every side-table statement
     (`:111-113`, `:205-209`).
3. **Concurrency: closed.**
   - Apply takes the session run lock (`withRunLock`, which the daemon refresh also takes through `tick`; checked
     `src/app/tick.ts:64`, `daemon/jobs/refresh.ts:121`). Its transaction also takes the asset's transaction advisory
     lock at BEGIN (`lockAsset`, `src/db/pg/pool.ts:180`).
   - Every observation writer (`insertObservation`, confirm/reject, `apiFlow`, `flow`, `periodic`, `tokenBackfill`,
     `raiseAnomaly`) takes that same lock (checked `git grep lockAsset`). So no row can be inserted, superseded or
     flagged with an anomaly between the plan and the commit.
   - FK both ways: a kept row pointing into the set is refused (`:187-196`, any asset). A deleted row pointing at a
     kept row is fine, because its pointer is cleared or removed with it. Pointers inside the set are cleared first
     (`:106`).
4. **CLI defaults: closed, one nit.**
   - `apply: opts.yes === true` (`data.ts:229`). Absent or anything other than the flag means a dry run.
   - The dry run takes no lock, creates no directory and makes no write (test `purge.test.ts:116-133`, CLI test
     `purge.cli.test.ts:61-76`).
   - Refusal codes are identical, with one exception: under `--yes` the lock is taken before the config-only checks
     (Minor #1).

### Issues

#### Critical (Must Fix)

None.

#### Important (Should Fix)

1. **`src/db/purge.ts:225-235`: the export file is fsynced, its directory entry is not.**
   - `mkdirSync`, then `openSync(file,'wx')`, `fsyncSync(fd)` and `closeSync`. Neither `dir` nor (on the first purge)
     `$ORION_HOME` is fsynced.
   - POSIX only makes the file's *name* durable after an fsync of its directory. On XFS or btrfs, or ext4 without
     journal-commit luck, a crash after the DB COMMIT (which is durable at once) can leave the rows deleted and the
     export file missing. That is exactly the irreversible-loss window named risk 1 exists to close.
   - Fix: after `closeSync`, `const d = openSync(dir, 'r'); fsyncSync(d); closeSync(d);`. Do the same for
     `dirname(dir)` when the directory was just created. It stays inside the `try`, so a failure is still
     `purge_export_failed` before any delete.

#### Minor (Nice to Have)

1. **`src/db/purge.ts:87-89`: the config-only refusals are checked inside the lock under `--yes`.**
   - While a refresh holds the run lock, `--yes` on a configured metric without `--source-type` reports
     `run_in_progress`, where the dry run says `purge_configured_metric`. Same outcome (nothing deleted), different code.
   - Also, `withRunLock` runs `abandonRunningRuns` (`src/app/lock.ts:22`) before the refusal. A refused `--yes` can
     therefore still write to `agent_runs` when orphaned runs exist, and "refused, nothing written" isn't literally true.
   - Fix: run `planPurge(db, …)` once before taking the lock (or at least the config checks at `:129-147`), then
     re-plan inside the transaction.
2. **`tests/db/purge.test.ts:160-176`: the `live === null` branch of `purge_live_source` (`purge.ts:139-145`, a
   source with no known rung) is untested.** Both refusal assertions hit the `live === sourceType` branch. Both
   branches return the same code, so a regression in the null branch would go unseen.
3. **`tests/cli/purge.cli.test.ts:96-111`: dry-run/`--yes` refusal parity is not pinned at the CLI level.** Every
   refusal case passes `--yes`. Add the same calls without `--yes` and assert the same codes (named risk 4).
4. **No test for `run_in_progress`.** Nothing covers a purge while another holder has the asset run lock. That
   protection is what named risk 3 relies on: add one test that holds `tryAssetRunLock('purg', …)` and expects
   `run_in_progress` with the counts unchanged.
5. **`src/db/purge.ts:217-218`: the export file name joins every metric key, so a long `--metric` list can exceed
   255 bytes.** The result is `ENAMETOOLONG` → `purge_export_failed`. It fails closed, but with an unhelpful message.
   Consider capping the name (e.g. the first metric plus `+N`), since the full list is in the JSON anyway.
6. **A configured metric's own API-flow cursor (`defillama:…>metric`) is kept after a `third_party` purge, and stays
   as dead state** (`purge.ts:172`, by design, per the report). It is harmless, because a new source gets a different
   key, but nothing ever removes it. Worth a note for Task 7 or ops.
7. **Report: under `--maxWorkers=2` the full suite had one failure, `tests/db/pg/migrate.test.ts`
   (`could not open relation with OID`), which passed when rerun alone.** It is not caused by this task. Suite output
   should be clean: record it in the ledger as a known flake.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The logic is correct and well tested on every named risk: row selection, lock coverage, FK handling,
export completeness and dry-run defaults. The one blocking gap is durability: the delete can commit while the
export's directory entry is not yet on disk. That is a three-line fix (fsync the directory) inside the existing
`purge_export_failed` path.
