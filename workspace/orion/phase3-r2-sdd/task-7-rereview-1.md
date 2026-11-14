# Task 7 re-review, fix round 1 (13ece08..c5e6172)

### Finding Verdicts

- **1. IMPORTANT, R27: span re-checked every run; deploy.md `--from 2025-10-13` refused from 2026-11-17.** ADDRESSED.
  - (a) The new `pricesBackfillRequest` (src/daemon/jobs/backfill.ts:149-160) freezes `to = parsed.to ?? todayDay` and returns it in the params. The CLI enqueues with it (src/cli/commands/job.ts:72).
  - (b) The handler's `parsePricesBackfillParams(job.params, prices)` (backfill.ts:124, called at :329) no longer takes `now`. It has no span cap and no today check, only shape, from <= to and refs.
  - (c) `PRICES_BACKFILL_MAX_DAYS = 550` (backfill.ts:36) applies at enqueue only (:157). `BACKFILL_MAX_DAYS` stays 400 for op fetch.
  - The CLI is the only enqueue path for op prices: a git grep finds no other `enqueueJob` with op prices. orion-remote calls the CLI.
  - deploy.md: 2025-10-13..2026-11-17 is 401 days, under 550. I hand-checked that the range fits until 2027-04-15, and the test pins it (`to: '2027-04-15'`).
  - Tests:
    - a no-`to` request stores `to` (backfill.test and job.cli `to: '2026-11-03'`)
    - a stored 584-day job and a legacy no-`to` job both run `done`
    - 551 days is refused, 550 accepted
- **2. MINOR: chain error dropped when the run also defers.** ADDRESSED.
  - backfill.ts:361-369 logs the line, then posts one `ORION ALERT <env> backfill prices: price_chain_stopped: …; the job defers…` line.
  - It checks for an abort before posting, then returns `deferred`.
  - The test checks both the posts and the log.
- **3. MINOR: progress nulled by a later failure before the writer.** ADDRESSED.
  - backfill.ts:325 seeds `result` from `progressOf(job.result)` when the row's result is op prices. The failure path (:403) returns that result.
  - The test (bad ref, saved progress) gets `result: saved`.
- **4. MINOR, R28: 10-min budget.** ADDRESSED.
  - `PRICES_BACKFILL_BUDGET_MS = 10 * 60_000` (backfill.ts:41) is passed to the writer (:343).
  - The test pins both the constant and the writer's `budgetMs`.
  - The drain sentence is in deploy.md's verb reference ("waits for the current run's budget (<= 10 min + one chain-day)").
- **5. MINOR: lock name `prices` collides with an asset.** ADDRESSED.
  - `PRICES_LOCK = 'job:prices'` (backfill.ts:48), and `PRICES_RUN_LOCK = 'job:prices'` (src/db/purge.ts:130) is used by purgePrices (:166).
  - Tests pin the two equal and equal to the literal. A held asset lock `prices` does not block the job.
  - No clash with `DAEMON_LOCK_ID = 'orion:daemon'`.

### New Breakage in the Fix Diff

None.
- The ALERT now posts every 10 min while a chain keeps failing under budget stops (report Notes). This is the expected effect of item 2, bounded by run count, not silent. It is acceptable.

Check run: in a detached worktree at c5e6172 (since removed), `npx vitest run tests/daemon/backfill.test.ts tests/db/purge* --maxWorkers=1` gave 2 files, 41/41 passed.

### Out-of-Scope Observations

- The plan's Task 7 "Produces" text still says run lock `prices` and `budgetMs` 20 min (docs/superpowers/plans/2026-11-13-orion-phase3-r2-price-swap.md:303). R27 and R28 supersede it. Ledger it for a plan or doc touch-up in the final review.

### Verdict

**Fix round:** All findings addressed, no new Critical/Important breakage.
