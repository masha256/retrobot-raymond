# Task 3 review: hour blocks, 0008 part 1, chain price writer (1d8e9bd..a4d49c7)

### Spec Compliance

- ✅ **Spec compliant, with one exception.** Every file the brief lists has its hunk: 0008, hourBlocks.ts, writer.ts, prices.ts, the chains.ts comment, and the three test files. The `writeChainPrices` / `WriteResult` / `PriceDeps` shapes match the brief as amended by R3, R4 and R15. Extras are justified: `WriteResult.errors` and `PriceDeps.prices` (R15), the `opts.clock` test seam, and the migration-count edits in five test files that migration 8 forced. hour_blocks is in the restored-from-prod list per R14.
- ❌ **Named risk 1 is partly unmet: an aborted signal does not stop the next write.** See Important #1.
- ⚠️ **Cannot verify from this diff:**
  - Task 7 must pass a signal tied to the lease and must stay out of the nightly window (Review Focus 4).
  - Task 4 must register hyperliquid, lighter and solana in the R15 result shape.
  - Task 5 must append the view to 0008 while keeping it free of a `-- breaking` line.

#### Named risks: what I checked
1. **Resumability (partly met).**
   - The skip rule is per ref under `methodSource(primary)` (writer.ts:284-291, 421-428). A CoinGecko row does not count as stored.
   - A fully stored range never reaches `ChainBlocks.at`, so a re-run makes no latestBlock, getBlock or multicall (writer.ts:331). The test at writer.test.ts:197-210 shows it.
   - One `db.tx` per chain-day holds the prices rows, the tokens rows and the fresh hour_blocks (writer.ts:389-402).
   - The budget is checked only after a committed chain-day (writer.ts:407-412), so a budget stop leaves no half-written day (writer.test.ts:212-226).
   - **Abort is checked only between chain-days (writer.ts:298).** My probe aborted the signal inside the first multicall of a 24-hour chain-day. The writer still read all 24 hours (24 multicalls) and committed all 24 rows. See Important #1.
   - A transport error commits the hours read before the failure (writer.ts:351-352 then 389). This is report decision 4. It is acceptable: those rows are valid, and a re-run resumes from `prices`.
2. **Hour semantics and block search (met).**
   - Row ts=H is read with `end = B(H+1h)` and `start = B(H)` (writer.ts:337-345).
   - `findHourBlock` returns only when `prev.ts < target <= b.ts` (writer.ts:97). The fallback `firstBlockAtOrAfter` (rpc.ts:111) uses the anchor only to estimate and brackets from `upper`, so passing it an anchor above the target is safe.
   - Exact blocks on both sides of 53,556,128 with ≤4 getBlock per hour: writer.test.ts:115-131 measured 2, 2, 4, 4, 2.
   - `no_block_yet` comes from the head check (writer.ts:145 and 338-341; test at 187-195). A block younger than 1 h below the head is not cached.
   - hour_blocks is first-write-wins through `ON CONFLICT DO NOTHING` (hourBlocks.ts:32; tests/db/hourBlocks.test.ts:11-23).
   - Extra probe: a 12 s chain with 5% missed slots, 48 hours walked back. Every block was exact, at mean 4.2 getBlock per hour (max 8), which is in line with the P6 estimate.
3. **R5 dependency order (met).**
   - Chain order is eip155:1, then the other EVM chains, then off-chain (writer.ts:169, 215).
   - `feedsAt` and `checksAt` are rebuilt for each day (writer.ts:292-293), so a quote cannot carry over from an earlier day.
   - A chain-1 hour that failed or has no block yet sets `null`. The off-chain ref then gets `quote_missing` and its method is not called (writer.ts:340, 350, 368-375; tests at 349-391).
   - DIEM without VVV is covered: `closureOn` pulls the quote refs into the same `priceHourEvm` call (writer.ts:263-272), which marks DIEM missing (Task 2's code).
4. **Breach rule (met, with one Minor below).**
   - Null gaps are excluded in SQL (writer.ts:440), so a null neither breaches nor resets.
   - A `bound` check breaches on any `gap != 0` (writer.ts:444).
   - 3.4%/3.5% gives one breach, 3.4%/0.1% gives none, and 3.4%/null/3.5% gives one breach (writer.test.ts:282-310).
5. **Migration 0008 (met).**
   - 0008 has no `-- breaking` line, and the test asserts it (migrate.test.ts:286).
   - It adds only a table and nullable columns. orion-2026.11.12.1's verbatim INSERT, stored-hours and list statements still run on schema 8 (migrate.test.ts:282-324).
   - At 8f50ac6, `openDb` (connection.ts:85) and the daemon start (daemon.ts:223) refuse only `pending`; a schema ahead of the code is allowed. So the old release runs on schema 8.
   - Old stagingRefresh: it restores everything not in `ENV_LOCAL_TABLES`, so an unknown hour_blocks table is restored, not refused.
   - N+1 multicalls: 6 for 5 hours (writer.test.ts:170) and 25 for 24 (writer.test.ts:222). The cache is keyed per block and per call (evmMethods.ts:401-418), so a partially warm block is safe.

### Strengths
- `findHourBlock`'s two-guess re-estimate is small, correct by construction (it returns only on an exact bracket), and backed by mutation evidence. It hands chain halts to the existing bracketed search, and the halt is tested (writer.test.ts:133-157).
- The chain-day transaction cleanly couples rows with the hour blocks they used. The skip rule is source-aware, so a later method change re-prices instead of silently skipping.
- Reorg-safe caching: only blocks at least 1 h below the head go into hour_blocks.
- The R5 plumbing goes through `feedsAt` and `checksAt` per day. No cross-day state means no stale quote is possible.
- The migration test is strong: column types, nullability, the `"check"` collation C, the PK, the old row kept, and the old release's statements run verbatim.
- `upsertPrices` sends one jsonb payload, rejects a non-finite gap, and leaves CoinGecko callers unchanged.
- Tests use the real DB and `fakeRpc` throughout, with exact block and value assertions.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
1. **writer.ts:298 and 325-402: an aborted signal still finishes and commits the in-flight chain-day.**
   - The signal is checked only before each chain-day starts. My probe aborted on the first multicall; the writer then made 23 more multicalls and committed 24 rows.
   - This misses named risk 1 ("a lost lease / aborted signal stops before the next write"). After a lease loss, the old runner keeps doing RPC work and writes while the new lease holder may be writing the same chain-day. The rows are identical upserts, so the damage is double work, duplicate breach reports and a slower shutdown on deploy, not corrupt data.
   - The only abort test (writer.test.ts:228-235) uses a signal aborted before the run starts, so the hole is untested.
   - Fix: check `opts.signal?.aborted` at the top of the hour loop (break), and again just before the `db.tx` (skip the commit, then `break days`). Add a test that aborts from inside a fake multicall and asserts no row was written and no further multicall was made.

#### Minor (Nice to Have)
1. **writer.ts:435-458 (breaches): the deferred double-report is more common than recorded.** Because the writer walks newest day first, one run of breaching hours that crosses midnight is reported twice in a single writer run, not only by a later backfill.
   - Probe: cvxCRV at 3.5% for 23:00, 00:00 and 01:00 (consecutive 2), in one run from 22:00 to 03:00. It reported breaches at 01:00 (from the newer day) and at 00:00 (from the older day).
   - With P5's per-breach `ORION WATCH` notify, this means duplicate alerts.
   - Fix: report only when the run's breaching hours before the completing hour don't already include `consecutive` stored hours, i.e. skip a run already long enough without the new rows. Alternatively, compute breaches once at the end of the run over the full written set.
2. **writer.ts:438-457: an absent hour (no row) neither resets nor breaks a run.** Only null gaps were meant to be "skipped". A breach at H and another at H+6 count as consecutive when H+1..H+5 have no row, for example after `read_failed`. Consider resetting the run when the gap between rows is more than 1 h, unless the hour between exists as a null-gap row.
3. **writer.ts:300-302 and 318-323: a chain that has failed records `missing` only for the failing hour.** Its own refs in later hours and later days get no `missing` entry, while off-chain dependents get `quote_missing` for every hour. `errors` plus a non-advancing `reachedMs` do signal it, but `missing` under-reports. Either list those hours or document that `missing` excludes them.
4. **writer.ts:112: the fallback discards the bracket.** When both guesses miss, `firstBlockAtOrAfter` restarts with only `upper` as `hi`, and the probed blocks below the target are lost. This is why missed-slot hours cost 6-8 getBlock (probe above). Optional: pass the known `lo`.
5. **writer.ts:191-418: `writeChainPrices` is one ~230-line function with nested closures** (`collect`, `fail`, and the EVM and off-chain branches inline). Extracting the per-chain-day loop, say `priceChainDay(...) -> { rows, fresh }`, would make the abort and budget points easier to test. writer.ts is a new 500-line file.
6. **src/daemon/jobs/stagingRefresh.ts:20 (unchanged): stale doc comment.** It describes `day_blocks` as env-local because "a staging release may compute them anew". R14's reasoning for hour_blocks is the opposite. The doc comment should name hour_blocks and why it differs.
7. **Test evidence:** the full run had one load-timeout failure (deploy.test.ts), which passed when rerun alone. That matches the global rule for load-sensitive files. Noted, not a code issue.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The hour semantics, block search, skip rule, chain-day transaction, R5 ordering, breach cases and expand-only migration are correct and well tested. The abort signal, however, does not stop the in-flight chain-day's reads or its commit. That misses an explicit resumability requirement and has no test. The fix is small: check abort in the hour loop and before the commit, plus a mid-run abort test.

Probes ran in a detached worktree at a4d49c7 with a throwaway test file, which was removed. Nothing was run in the main worktree.
