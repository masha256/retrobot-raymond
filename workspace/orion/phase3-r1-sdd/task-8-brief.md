### Task 8: soak expectations and the release record

**Files:**
- Modify: `~/.hermes/profiles/raymond/scripts/orion-phase2-parity.json` (outside the repo; back it up first to
  `.pre-p3r1`), `docs/superpowers/notes/2026-11-12-orion-phase3-followups.md` (create), the spec's Status line

- [ ] **Step 1: Soak parity.** Stage (on R1) vs prod (on 2026.11.11.1) will differ on Task 7's allowlist paths. Add
  them to the parity file as expected for this soak only, and write the "known queue" line of the soak cron
  (e2fb64f34263) prompt. Dry-run `orion-stage-soak.py` against the current envs to show it still passes.
- [ ] **Step 2: Release block** for deploy.md (Task 3's section), per env, in this order: `deploy.sh <env> <tag>` →
  `status`, `logs 30`, `db status` current 7 → `job run-now refresh lit` and `pump` → `data purge` dry runs (paste the
  counts) → on Mike's go, `--yes` for each pair → `report yield` for the 12, through `flatdiff` against the
  pre-deploy report. Stage first, then soak one scheduled nightly, then prod on Mike's go. Before deploying, check that
  no Sunday 10:30Z `staging_refresh` falls between the stage and prod switches (it refuses on schema 6 vs 7 and
  alerts). If one does, deploy stage after it.
- [ ] **Step 3: Followups note.** Carry: P5's two replacements (R3), R2's `op: prices` on the backfill job, ledger
  minors, and the purge export files' location per env.
- [ ] **Step 4: Commit** `docs: Phase 3 R1 release block, followups note`. Push the branch.

**Stop point:** after Task 8, before any tag, merge to main or deploy. The release itself (tag, build, stage, purge,
soak, prod) follows the standing release-day steps, and each env's purge `--yes` needs Mike's go.
