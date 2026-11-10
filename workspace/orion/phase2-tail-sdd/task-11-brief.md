### Task 11 (gate G4, one release after Task 4 on staging): retire v1

**Files:** `src/config/schema.ts` (delete `holder_flows` and `reporting`, which are then refused by name at load,
proposal filing and approve, per the orion skill's "Retiring a config key"), the 13 YAMLs, `src/app/eligibility.ts`
and `src/agent/context.ts` (read `income_statement`; the pack's flow set = the holders + below_line-to-holders
metrics, equal to today's `holder_flows` metrics), `--legacy` removed, `holderYield.ts` legacy paths deleted. The
disclosure e2e test keeps its fixture config. Proof: v2 JSON identical before and after, and the pack identical for
LIT (`tests/agent/context.test.ts`).

## Execution

- Interactive, in the orion skill's subagent mode (`references/subagent-execution.md`):
  - On Mike's go, archive kanban card t_1697d7dc, record P1-P3 in this plan's header and commit, and move the worktree
    to `.worktrees/data-strategy` (`references/kanban.md`, "Moving a card's work out of kanban").
  - Dispatch one task at a time, then verify each result yourself (git log, the core diff, rerunning the task's tests)
    and run a named-risk review.
  - Task 0, Task 4 Step 5, Task 5 Step 4, Task 6 Step 4 and Task 7 Step 5 are controller steps (they touch the live
    `.backup`, the scratch `.env` copy or the proof schemas).
  - D4's "internal only": the Phase 5 export must drop or flag every `provenance.thirdParty` line. Phase 2 only labels
    them, and the followups note carries this as a Phase 5 requirement.
- Stop points: G1 after Task 4, G2 after Task 7, then G3 and G4. A merge to `main` happens only with the Phase 1.5
  cutover and Mike's go. Any live/prod action stays outside this plan.
- At the end: a followups note with the ledger's minors and rulings, the v2 table, the check and backfill results, and
  the open items for Phase 3 (the gross/cost series per spec §8 "Missing", D4 on-chain vote incentives, and the
  generic source types if P3 stands).
