# Task 2 findings (fix round 1) — controller rulings binding

Source: task-2-review.md against b31c224.

- I-1 (Important, fix): src/db/purge.ts export durability: fsync the export file's DIRECTORY (and $ORION_HOME when `purged/` is first created) inside the existing try, so any failure raises `purge_export_failed` before any delete. Test: inject a dir-fsync failure (seam) -> purge_export_failed, row counts unchanged.
- Minor 1 (fix): run the config-only refusals (purge_configured_metric, purge_live_source, unknown metric) BEFORE taking the run lock, so dry run and --yes return the same code and a refused --yes writes nothing (no abandonRunningRuns side effect). Re-plan inside the transaction as today.
- Minor 2 (fix): test the `live === null` branch of purge_live_source.
- Minor 3 (fix): CLI tests: each refusal also without --yes, same code.
- Minor 4 (fix): test run_in_progress (another holder has the asset run lock) -> refused, counts unchanged.
- Minor 5 (fix): cap the export file name: `<asset>-<first metric>[+N]-<UTCstamp>.json`.
- Minor 6: deferred to followups note (dead API cursor of a third_party-purged configured metric).
- Minor 7: known flake, ledgered.
- ⚠️ latest_levels after a third_party purge of a configured metric: Ruling R14 — the release block runs `job run-now refresh <a>` (new source writes latest_levels) BEFORE the purge, so no third-party value is left there. Task 8 encodes the order. No code change.
