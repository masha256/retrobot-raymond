# Task 5 review: flow_usd_chain_v and the report basis (b50e94b..7ff7562)

### Spec Compliance

- ✅ Spec compliant (one accepted deviation, below). Every brief item is present:
  - `CREATE VIEW flow_usd_chain_v` (0008_chain_prices.sql:37-87) has flow_usd_v's 13 columns in order (pinned by tests/db/prices.test.ts:165-177 via information_schema). The price lateral is restricted to `chain:`/`first_party:` (:73); ordering is `ts DESC, fetched_at DESC, source` (:74, R6); the 6-hour rule is at :72. `daily_mean` (:46, :53, :78-86) requires a null `hourly_amounts`, a non-null `amount`, `period_days = 1` and 24 priced chain hours, and computes `usd = amount x avg`.
  - `PriceBasis` gains `daily_mean`. `priceBasisOf(usdBasis)` now takes one argument (src/db/prices.ts:184). `HOURLY_SERIES_DAYS` and `pricedHourlyAtIngest` are deleted; `git grep` at 7ff7562 finds them only in an old-behaviour comment (tests/report/priceBasis.test.ts:103).
  - The step-1 tests all exist (tests/db/prices.test.ts:179-247): CoinGecko-only reads `legacy_unpriced` in the new view and `hourly` in the old one; a chain row reads `hourly` at the chain price; a newer CoinGecko row is ignored; 24 hours give `daily_mean` and 23 give `legacy_no_hourly`.
  - Extra files (src/cli/commands/data.ts:78-89, :237 and tests/cli/ingest.cli.test.ts:154-168) fall outside the brief's file list. They are required, because `compareUsd`'s shape changed. Not scope creep.
- ⚠️ The brief says "`source` shows the method (`chain:chainlink` etc.)". `incomeStatement.priceBasis.source` still reads `market_data:coingecko` in all 60 golden occurrences. That label comes from the asset YAML's `price_usd` adapter, which Task 6b repoints (R18), so it cannot move in Task 5 without touching YAML. The controller already recorded the deferral in progress.md:98. **Controller:** make sure Task 6b's golden re-pin moves `priceBasis.source` and nothing else.
- ⚠️ Proof tools need an update in Task 10; they are not broken by this task:
  - tools/phase2-proof/compare.py:10-12 compares the old and new v2 objects whole, so it would flag the new `priceBasis.flows` text and any line-label change.
  - tools/phase3-proof/r1-allowlist.json has no `priceBasis.flows` or line-`priceBasis` entries.
  - The R2 proof's allowlist must carry these paths. No proof script calls `compare-usd` (orion-remote only passes it through: scripts/provision/files/orion-remote:423-425).

### Named risks checked

1. **Golden integrity (R17).** I flattened `git show b50e94b:` against `7ff7562:` of tests/report/golden/v2-report-13.json, decoding the nested report JSON strings, with lists keyed by `id`: 17,401 leaf paths on each side.
   - Exactly one path changed: `report.incomeStatement.priceBasis.flows`, in 39 entries (13 assets x loader, prior and growing-loader).
   - Every `input` hash is unchanged. No revenue, cost, holder-flow, yield, dilution, grade, price or line-`priceBasis` path moved.
   - The re-seeded fixtures keep their values: priceBasis.test.ts:41 (10.5) and :178 (99) swap only the source, `coingecko` to `chain:chainlink`. The prices.test.ts re-seeds keep their values too (2, 10).
   - The only `coingecko` price writes left in tests/report are deliberate negative cases (priceBasis.test.ts:115).
2. **View correctness.**
   - CoinGecko is ignored even when newer (0008:73; test prices.test.ts:205-218).
   - The price used is at or before the hour start and at most 6 h old (:72, same predicate as 0005:96).
   - R6 tie: newer `fetched_at` wins and flips on a re-write (test :220-229). The daily lateral uses the same order (:84).
   - `daily_mean` requires exactly 24 distinct chain hours in [observed_at-24h, observed_at). 23 hours gives `legacy_no_hourly`, even with a CoinGecko row filling the gap. The next day's 00:00 is excluded, and the result does not depend on DST (tests :231-268).
   - `usd_native`, `hourly`, `legacy_unpriced`, `legacy_no_hourly` and `legacy_no_tokens` keep their flow_usd_v predicates and order (0008:47-58 vs 0005:59-70); `daily_mean` is inserted before `legacy_no_hourly`.
   - flow_usd_v itself is untouched: no DDL names it (0008 diff; test :175).
3. **0008 expand-only.** The diff appends only a `CREATE VIEW` and edits the header comment. There is no `-- breaking`, ALTER or DROP. The prices PK (0005:28, `token_ref, ts, source`) serves both laterals' range scans. Schema-7 code (orion-2026.11.12.1) never names the new view, so it is unaffected.
4. **Consumers.** I ran `git grep` at 7ff7562 for `priceBasisOf`, `listFlowUsd`, `compareUsd`, `HOURLY_SERIES_DAYS`, `pricedHourlyAtIngest`, `beyondHourly` and `flow_usd_v`:
   - The only src readers are load.ts:91 (`listFlowUsd`) and data.ts:243 (`compareUsd`). Both now read flow_usd_chain_v (prices.ts:196, :236).
   - incomeStatement.ts:512-515 folds any `PriceBasis` generically, so `daily_mean` needs no new branch.
   - The remaining `flow_usd_v` readers are all deliberate tests: migrate.test.ts:190-323, prices.test.ts (the old-view regression checks), tokenBackfill.test.ts:264, and importSqlite.test.ts:304 (`upTo: 5`, so it never sees 0008's view).
   - The only stale prose is docs/ops/deploy.md:308, already carried to Task 9 (progress.md:99).

Check run: in my own worktree at 7ff7562 (`npm ci`), `npx vitest run tests/db/prices.test.ts tests/report/priceBasis.test.ts tests/report/v2Golden.test.ts tests/report/parity.test.ts tests/cli/ingest.cli.test.ts tests/db/pg/migrate.test.ts tests/tools/importSqlite.test.ts --maxWorkers=1` passed 7 files, 176/176 tests, with no warnings. The worktree has been removed.

### Strengths

- The view is a near-verbatim copy of flow_usd_v with only the intended deltas, so a side-by-side diff is easy to audit. The header comment (0008:25-36) documents each basis exactly.
- The tests pin the hard edges: an old-vs-new contrast on the same rows, the R6 flip on re-write, two sources at one hour counted once in `daily_mean`, the exclusive upper bound of the 24-hour window, and DST independence.
- The implementer's golden claim (one path, 39 entries) matches my independent flatten exactly. The deviations are stated honestly in report §Self-review.
- The `compareUsd` simplification removes the within/beyond split cleanly, and the CLI and its test follow it.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)

1. **0008_chain_prices.sql:80-85: the daily_mean lateral never checks that `ts` falls on the hour.**
   - It counts distinct `ts` in the window. A stray sub-hour row (e.g. 00:30) would count as an "hour": with one real hour missing, the day could still reach 24 and read `daily_mean`. With all 24 present, it reaches 25 and fails closed to legacy.
   - P2 guarantees hour-aligned `ts` from the writer, so the risk is low.
   - Fix: add `AND date_trunc('hour', pr.ts) = pr.ts`, or `extract(epoch FROM pr.ts)::bigint % 3600 = 0`.
2. **src/db/prices.ts:144-145 and data.ts:83: `GapStats.sumHourly` keeps its name but now also sums `daily_mean` and `usd_native` days.**
   - The doc comment and the CLI word "chain" explain this, but the JSON field name is now misleading for Task 8/9 readers.
   - Acceptable now; rename it if the JSON contract is touched again.
3. **compare-usd `--json` contract change.**
   - `beyondHourly` and `beyond` are removed and `dailyMean` is added. orion-remote passes the JSON through to an operator, and no script parses it.
   - Fold this into Task 9's deploy.md:308 rewrite alongside the existing carry.
4. **The 0008 view semantics differ from flow_usd_v on non-hourly rows.**
   - `hours_priced`/`hours_needed` read n/24 for every daily non-hourly token row, including `legacy_no_hourly`, where flow_usd_v reads 0/0 (0008:41-42). The column names and types are the same; this is intended (report concern 4).
   - Any Task 8/9 query that filters on `hours_needed > 0` to mean "hourly row" must use `usd_basis` instead.

### Assessment

**Task quality:** Approved

**Reasoning:** The new view matches P3 and R6 exactly, leaves flow_usd_v and the expand-only contract intact, and every consumer is moved to it. My flattened golden diff confirms that only `priceBasis.flows` text moved, with no value path changed. What remains is a minor hardening (hour alignment) and naming/doc follow-ups already routed to later tasks.
