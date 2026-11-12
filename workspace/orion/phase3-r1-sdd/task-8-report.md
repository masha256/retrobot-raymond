# Task 8 report (Steps 2-4, docs): implementer

Status: DONE_WITH_CONCERNS. Commit f0074f9 `docs: Phase 3 R1 release block, followups note` (base 811d33f). Not pushed
(the dispatch said not to push, which overrides the brief's "Push the branch"). Step 1 (soak parity file, soak cron prompt) not
touched (Ruling R7).

## What

- docs/ops/deploy.md "Phase 3 R1 release": replaced `<!-- release block: Task 8 -->` with the per-env release block.
  The intro covers the order (stage -> one scheduled nightly soak -> prod on Mike's go), the Sunday 10:30Z
  `staging_refresh` check (schema 7 vs 6 refusal + alert; if a Sunday falls between the switches, deploy stage after it)
  and the 12 changed assets (all but AERO). The steps, in R14's order:
  0. save the pre-deploy `report yield <a>` (the 12 + AERO) before the switch;
  1. `deploy.sh <env> <tag>` (applied [7], no --breaking);
  2. `status`, `logs 30` (heartbeat on the new tag; deploys.log `migrations=7`);
  3. `job run-now refresh lit` / `pump`, then `jobs --since` until both are `done`;
  4. six `data purge` dry runs with the counts pasted (4 orphans with no --source-type; lit/pump `unlocks_next_year
     --source-type third_party`);
  5. on Mike's go, the same six with `--yes`, plus where the export files land (`~/home/purged/`);
  6. `report yield <a> --day <pre-deploy day>` for the 12 through `flatdiff.py --allow tools/phase3-proof/r1-allowlist.json`,
     with R22's manual perTokenFdv check and AERO checked with `cmp`.
- docs/superpowers/notes/2026-11-12-orion-phase3-followups.md (new): R1 decisions P1-P5; rulings R1-R22, one line
  each with its cost; all 16 `minor (deferred)` ledger lines, grouped by task 1-6; carried to later releases (P5's LIT
  two_path + VVV usage_index -> R3, R2's `op: prices`, the dead API cursor (M-6), the purge export files per env); Proof
  placeholder `Proof results: see controller commit`.
- Spec Status: added the bullet with the exact text from the dispatch.

## Checks

- Grep: every `- R<n>:` for n=1..22 is in the note. The 16 deferred lines in progress.md are all in the note (counted
  by hand: T1 5, T2 4, T3 3, T4 2, T5 1, T6 1).
- Verb syntax checked against scripts/provision/files/orion-remote (`v_job`, `v_report`, data purge) and the verb
  reference above the marker. The report's top-level `day` field was checked in src/report/incomeStatement.ts. The
  export file name was checked in src/db/purge.ts `exportFileName`.
- No code changes, no npm/vitest run (per dispatch).

## Concerns

1. Export file name: src/db/purge.ts writes ONE file per purge call, `<asset>-<first metric>[+N]-<UTCstamp>.json`,
   not one per metric. P2 and Task 3's verb-reference comment (deploy.md, the `data purge` code block) say
   `<asset>-<metric>-<UTCstamp>.json`. My block and the note use the real name (six files per env). I left Task 3's
   comment line alone. It is a one-line fix if wanted.
2. The brief's "`db status` current 7": the deploy keys have no `db status` verb. The block uses the deploy report's
   migrations applied `[7]` / deploys.log `migrations=7` as the check, with `o db status` (as the env user) as the
   optional direct check.
3. Step 6 compares on each asset's pre-deploy `day` (`--day`), not the new default day: CAKE/UNI/VVV's default day may
   move (Task 7 carry), and flatdiff needs both sides on the same day. I added AERO to the step-0 save so its
   byte-identity can be checked with `cmp`.
4. The note suggests R8 as the place to decide the dead-cursor drop and the purged/ file retention. Both are marked
   "suggested"; neither was decided by Mike.
