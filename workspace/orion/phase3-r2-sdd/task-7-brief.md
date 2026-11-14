### Task 7: `backfill op: prices` and its remote verb

**Files:**
- Modify: `src/daemon/jobs/backfill.ts`, `src/db/jobs.ts` (`BackfillParams` union), `src/cli/commands/job.ts`,
  `scripts/provision/files/orion-remote` (+ its tests), `docs/ops/deploy.md` (verb table)
- Test: `tests/daemon/backfill.test.ts`, `tests/cli/job*.test.ts`, `scripts/provision/test/test_orion_remote.py`

**Interfaces:**
- Produces: params `{ op: 'prices'; from: 'YYYY-MM-DD'; to?: 'YYYY-MM-DD'; refs?: string[] }`, job `assetId` null,
  run lock name `prices`; each run calls `writeChainPrices` with `budgetMs` 20 min, then returns `{ status: 'deferred', untilMs: now }`
  until no hour is missing, then `done` with the WriteResult summary (rows per ref, oldest hour, missing by reason, calls
  per chain, breaches). `backfillWaitUntil` applies unchanged. CLI `job run-now backfill-prices --from D [--to D] [--refs a,b]`;
  remote the same verb, `--refs` a comma list validated against `^[a-z0-9:/._-]{1,120}$`.

- [ ] **Step 1: Failing tests**: Review Focus 4: a job whose lease is lost mid-day re-queues and the second run skips
  every committed chain-day (no multicall for them); the job defers while the nightly window is closed; a deferred job
  keeps priority 70 (hourly levels run between budgets); `refs` with an unknown ref is refused at enqueue; the old
  `op: fetch` path is unchanged (existing tests green).
- [ ] **Step 2-4: FAIL, implement, PASS.**
- [ ] **Step 5: Commit** `feat(daemon): resumable prices backfill job and its remote verb`.

