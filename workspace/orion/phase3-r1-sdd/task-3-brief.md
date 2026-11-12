### Task 3: `orion-remote` verbs and the runbook

**Files:**
- Modify: `scripts/provision/files/orion-remote` (docstring verb table, `v_job`, `v_data`, `VERBS`),
  `scripts/provision/test/test_orion_remote.py`, `docs/ops/deploy.md` (new section "Phase 3 R1 release")

**Interfaces:**
- Consumes: Task 1's `job run-now backfill`, Task 2's `data purge`, the existing `data compare-usd`.
- Produces (verbs):
  - `job run-now backfill <asset> --metrics <k1,k2,...> --backfill-days <1..400>`: passes `--metric` once per item.
  - `data compare-usd <asset> [--days <1..400>]`: passthrough, read-only.
  - `data purge <asset> --metrics <list> [--source-type <rung>] [--yes]`.

- [ ] **Step 1: Tests** with the existing fake-node harness (assert the argv Orion receives):
  `backfill_passes_each_metric`, `backfill_refuses_empty_item` (`a,,b`), `backfill_refuses_bad_metric` (`A`, `a/b`,
  65 chars), `backfill_days_range` (0, 401, `1e3`), `purge_dry_run_by_default` (no `--yes` in argv),
  `purge_source_type_is_a_known_rung` (the nine rungs from 0004's CHECK, anything else exit 64),
  `compare_usd_passthrough`, and `backfill_on_kinds_other_than_backfill_refused`. Every refusal exits 64 and logs
  `refused` to remote.log without the argument text.
- [ ] **Step 2: Implement.** Use the existing `METRIC_RE` and `COUNT_RE` and a `RUNG_RE` built from that list. Keep
  `parse()`'s rule against repeated flags, which is why the list is comma-separated.
- [ ] **Step 3: deploy.md.** Add "Phase 3 R1 release" in deploy order: Mike re-runs `orion-host.sh` from a fixed
  `git archive` snapshot of the release sha (installs the new `orion-remote`); then the per-env steps of Task 8's
  release block. Note that the verbs fail with Orion's own "unknown command" on a release older than this one.
- [ ] **Step 4: Run** `python3 -m unittest scripts/provision/test/test_orion_remote.py` (all pass).
- [ ] **Step 5: Commit** `feat(provision): orion-remote verbs for backfill jobs, compare-usd and purge`.

