### Task 7: proof on a read-only prod copy

**Files:**
- Create: `tools/phase3-proof/r1-allowlist.json`, `tools/phase3-proof/flatdiff.py`, `tools/phase3-proof/test_flatdiff.py`
- Results to `~/.hermes/profiles/raymond/workspace/orion/phase3-proof/r1/`

- [ ] **Step 1: `flatdiff.py <old.json> <new.json> --allow <allowlist> --asset <a>`.** It flattens both reports to
  `path = value` and prints every differing path. It exits 0 only when each one matches an allowlist glob for that
  asset and the numeric bound the entry carries (`rel` or `abs`). Unit tests cover a match, an out-of-bound value, and
  an unlisted path.
- [ ] **Step 2: Allowlist.** CAKE, UNI: `incomeStatement.volume.*`. LIT: `incomeStatement.dilution.*`, with the
  unlocks line's tokens rel ≤ 0.0007 (the +0.066%). PUMP: the same paths with rel ≤ 1e-12. VVV: the business line's
  cross-check fields. All 12: the provenance/cross-check listing paths that name the removed reads, enumerated from
  the first diff run, each with its reason. Revenue, cost of revenue, holder flow, yields and grades get no entry.
- [ ] **Step 3: Copy.** `tools/phase2-proof/prod_copy.py` into `$TMPDIR/p3r1` (run in the background). The OLD home
  is release `orion-2026.11.11.1`'s dist and assets; the NEW home is the branch's.
- [ ] **Step 4: Fetch on the new home.** `data fetch lit --metric unlocks_next_year` and
  `data fetch pump --metric unlocks_next_year` (no network: the adapter is offline). D = yesterday (UTC).
- [ ] **Step 5: Compare.** For all 13: before = prod's own `ssh orion-prod report yield <a> --day D` for the 12
  changed assets, and the OLD home's report for AERO; after = the NEW home. Run `flatdiff.py` on each. AERO must be
  `cmp`-identical. Write a sign-off table per asset (paths changed, old → new, reason) over both windows (D and D-91).
- [ ] **Step 6: Purge rehearsal on the copy.** Dry-run `data purge` for each pair below and check its counts against
  prod's (the 2026-11-12 counts are cake fees 398 / llama_revenue 398, lit fees 191 / llama_revenue 191, uni swap_fees
  191, vvv revenue_proxy 345, lit and pump unlocks_next_year third_party 31 / 29; re-read them, since they grow daily).
  Then run `--yes` and re-run Step 5: the reports must be byte-identical to Step 5's NEW output.
- [ ] **Step 7: Backfill job rehearsal.** In the NEW home (ORION_ENV unset = dev), queue `orion job run-now backfill
  vvv --metric flow_usd.burn --backfill-days 3`, start `orion daemon` in the background, poll `orion job list --kind
  backfill --json` (sleeps <= 60 s) until the job is `done`, then stop the daemon (SIGTERM). The job's result lists
  the rows written; rows are superseded only where the source changed. There is no `--once` mode; don't add one.
- [ ] **Step 8:** Copy the results to `workspace/orion/phase3-proof/r1/` and run `tools/phase2-proof/cleanup.py`.
  Commit the tools: `test(proof): Phase 3 R1 flatdiff + allowlist`.

