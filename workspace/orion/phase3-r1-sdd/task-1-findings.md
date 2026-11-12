# Task 1 findings (fix round 1) — controller rulings binding

Source: task-1-review.md (reviewer), against a6c78d2.

- I-1 (Important, fix): src/daemon/jobs/backfill.ts guard is clock-only and reopens at slot + 2 h while the nightly report waits for refreshes until slot + 3 h (NIGHTLY_WAIT_MS) and refresh retries land 10/30 min later. Fix: ALSO defer while any `refresh` or `nightly_report` job of the newest nightly slot is not finished (status queued or running, including a queued retry). Defer until a re-check time (e.g. 15 min later), not a fixed slot + 2 h. Keep the 4 h pre-nightly clearance. Test first: a backfill claimed at slot + 2h30 while a nightly refresh retry is queued -> deferred; the same with all nightly jobs done -> runs.
- I-2 (Important, fix): a `partial` fetch whose failed source serves a REQUESTED metric (its primary) must end the job `failed` with the ALERT Slack line (attempt 1 of 1, no retry). `done` + partial stays only when the only failed sources are cross-checks. Test first for both cases.
- M-3 (Minor -> fix, cheap, Ruling R11): bound the run: refuse at claim time is impossible to size, so instead post a Slack line when the backfill STARTS (`ORION BACKFILL <asset> started: <metrics>, <n> days`), the done/failed line includes the run duration, and deploy.md (Task 3) states "a backfill must be sized to finish inside the 4 h clearance; split by --backfill-days otherwise". No code bound. 
- M-1, M-2, M-4: deferred (ledgered), not in this round.
