# Task 4 review fixes — report

Commit: `0b4132e fix(ingest): watched monitor-only sources raise failure streaks; R3 review fixes` (on 176c45a).
Task 5's files were not touched.

## What

1. **I1 (src/ingest/run.ts, failure-streak rule).** Before, a source was exempt from `source_failure_streak` when every
   metric it writes is `monitor_only`. Now a metric counts toward that exemption only when it is monitor-only, has no
   `watch`, and is not a side (`a`/`b`) of a `level_gap_pct` metric that has a `watch`. The streak rule itself is
   unchanged: 3 failed attempts in a row, severity `advisory`, dedupeKey = the source id.
   - LINK's `http_json:https://supply.chain.link/supply` now streaks.
   - PUMP's `solana.owners_balance` (watched `reserved_balance`) now streaks too. It already did in practice, through
     `supply_less_owners`.
   - CRV's `ve_power.*` sources and other unwatched monitor-only sources stay exempt.
   - The `derived:level_gap_pct` source writes a watched gap, so it is no longer exempt either (the b = 0 failure).
2. **M1 (PUMP owner reads).** No code change was needed. The run's HTTP transport is already `withRunCache`
   (src/ingest/transport/http.ts:150). It caches POSTs by URL and body, so the identical `getTokenAccountsByOwner`
   bodies from `supply_less_owners` and `owners_balance` are sent once per run. Both the nightly and the hourly
   `runLevels` → `fetchAsset` paths use it. The review's "13 calls" counted adapter-level reads, not wire requests.
   - I added a test pinning it, plus a doc comment on `ownersHeld` in solana.ts.
   - I did not add a second solana-level cache, since it would duplicate the existing one.
3. **M3 (comments).** crv.yaml and link.yaml N5 comments now say both sides are read, and the watch checked, at the
   nightly run only (the hourly read skips derived and unwatched monitor-only metrics). Neither the YAML comments nor
   sources-register.md said "every run"; that wording was only in task-4-report.md (an SDD doc, left alone). No hash
   moved: comments are not hashed, and the full suite with the hash pins is green.
4. **M4 (src/ingest/derived.ts `levelGapIssues`).** A `constant` side is now refused, as a derived side already was:
   `"<m>" must be read this run (a source, not derived or constant)`.

## Tests (TDD)

- **I1:** new `describe('the failure streak of a source that feeds a watched check')` in tests/ingest/derived.test.ts.
  A failing `http_json` side runs 3 times, with three tests:
  - a side of a watched gap;
  - the side's own monitor-only metric watched (`change_pct`);
  - control: no watch anywhere, so no streak.
  - RED: the first two failed (`expected [[],[],[]]`, missing `http_json:https://issuer.test/supply advisory` on run 3);
    the control passed. GREEN: 3/3. The existing exemption tests (report.flows.test.ts) are unchanged and green.
- **M4:** an assertion added to the existing refusal test (`pinned_supply`, a constant level as `b`). RED:
  `expected '' to match /…must be read this run \(a source, not derived or constant\)/`. GREEN after the fix.
- **M1:** an assertion added to pump.ingest.test.ts ("fetches on-chain days…"): the `getTokenAccountsByOwner` owners in
  one run are exactly the six reserved owners plus the two burn wallets, each once.
  - It was GREEN at once, because the behaviour already existed. There was no RED to record.
  - A mutation check stands in for RED: with `withRunCache`'s `postJson` temporarily bypassed, the test failed with the
    six owners received twice. Reverted, and `git diff` was clean for http.ts before committing.
- **Full suite** (`npx vitest run --maxWorkers=2`): 156 files, **2024 passed / 1 failed (2025)**. Before: 2021/2022 plus
  the 3 new tests. The one failure is the known environmental one,
  `tests/db/daemonSchema.test.ts > 0002_daemon > schema: every 0002 table exists in schema orion` (the scratch schema
  r3probe_1795204385).
- `npm run typecheck`: clean.

## Files

src/ingest/run.ts, src/ingest/derived.ts, src/ingest/adapters/solana.ts (comment only), assets/crv.yaml and
assets/link.yaml (comments only), tests/ingest/derived.test.ts, tests/assets/pump.ingest.test.ts.

## Self-review / concerns

- M1 departs from the fix the findings prescribed (a new solana per-run cache). The cache already exists one layer down.
  The pinned test protects the behaviour if `withRunCache` is ever removed.
- I1: the watched-gap `derived:level_gap_pct` source and PUMP's `solana.owners_balance` source can now raise a streak
  where before they could not. This is intended under "a source that feeds a watched metric is not exempt". For PUMP
  it may add a second advisory alongside the `supply_less_owners` streak when the shared RPC fails (separate dedupe
  keys).
- No asset hash, golden or pin moved.
