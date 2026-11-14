# Task 3 re-review, fix round 1 (27a6ff1..bd4feed)

### Finding Verdicts

1. **IMPORTANT: abort inside a multicall still finished and committed the chain-day** — ADDRESSED. `src/prices/writer.ts:342` checks `aborted()` at the top of every hour (breaks the hour loop); `writer.ts:406` checks it again right before `takeFresh()`/`db.tx` and `break days`, so the in-flight chain-day's prices, tokens and hour_blocks are not committed and `written` is not incremented. `aborted()` (writer.ts:~285) is sticky and sets `WriteResult.stoppedBySignal` (`src/prices/types.ts:94`). Test `tests/prices/writer.test.ts:237` aborts on the 3rd multicall and asserts written 0, stoppedBySignal, reachedMs null, multicall/getBlock counts frozen after the abort, 0 prices rows, 0 hour_blocks rows. The pre-aborted test (writer.test.ts:233) now also asserts `stoppedBySignal: true`.
2. **MINOR: duplicate breach when a breach run crosses midnight** — ADDRESSED. Written hours are collected per ref over the whole run (`writer.ts:291, 423-424`) and `breachesOf` is called once per ref after the day loop (`writer.ts:435`; also reached after a budget/signal `break days`), reading stored rows `ORDER BY ts`. Test writer.test.ts:334 (23:00/00:00/01:00 at 3.5%, consecutive 2) asserts exactly one breach at 00:00.
3. **MINOR: an hour with no row must reset the consecutive count** — ADDRESSED. `breachesOf` now reads null-gap rows too; `writer.ts:472` resets the run when consecutive rows are more than 1 h apart, `writer.ts:474` skips null-gap rows after updating `prev` (skipped neither breaches nor resets). Test writer.test.ts:342 (3.4% stored 00:00, no row 01:00, 3.5% written 02:00 -> no breach); the existing null-gap test still passes.
4. **MINOR: stagingRefresh doc comment must name hour_blocks as restored from prod (R14)** — ADDRESSED. `src/daemon/jobs/stagingRefresh.ts:21-22`; `ENV_LOCAL_TABLES` unchanged (hour_blocks not listed, i.e. restored).

### New Breakage in the Fix Diff

None.
- Checked: `stoppedBySignal` is a new required field; the only `WriteResult` constructor is in writer.ts (git grep at bd4feed), so no other producer breaks.
- Checked: dropping the aborted chain-day's fresh hour blocks is harmless (run ends; next run re-searches), as the report notes.
- Ran (own worktree at bd4feed, `npm ci`): `npx vitest run tests/prices --maxWorkers=1` -> Test Files 4 passed (4), Tests 76 passed (76). Worktree removed.

### Out-of-Scope Observations

- (Minor, logic unchanged by the fix) `breachesOf` can re-report a run already reported by an earlier writer run when a backfill writes an older breaching hour in front of it: stored 3.5% at 01:00, 02:00 (reported at 02:00), a later run writes 3.5% at 00:00 -> run reaches `consecutive` at 01:00 and includes a fresh row, so a second breach for the same run is reported at 01:00. The "once per run" rule holds within one writer run, not across runs that extend a run backwards.
- An abort leaves earlier chains of the same UTC day committed (commit unit is the chain-day, as the ruling's test describes); no `missing` entries are recorded for the uncommitted hours. Fine for a lease loss, noted only.

### Verdict

**Fix round:** All findings addressed, no new Critical/Important breakage.
