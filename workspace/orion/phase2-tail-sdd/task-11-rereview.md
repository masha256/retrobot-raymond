# Task 11 fix round 1: re-review (b48c3cf..b360bc2)

Checked against `git diff b48c3cf b360bc2`, task-11-report.md "Fix round 1", in three detached worktrees of my own
(cc59fa7, 0f4b2fe, b360bc2; `npm ci --offline`; DB orion_test only; all three removed afterwards).

## Per finding

- **I1 ADDRESSED.** `src/agent/context.ts:101`: `revenueStreams` skips a line with no `metric` or no `settlement`.
  - Golden is genuine: I regenerated all 13 packs at cc59fa7 with packGolden's `packOf` (same seeding and NOW). The output
    is byte-identical (`cmp`) to `tests/agent/golden/packs-13.json`. That file has not changed since 2f5bc8d, and not in b48c3cf..b360bc2.
  - Whole-pack test is real (`tests/agent/packGolden.test.ts:49-66`): it lists every differing asset by JSON bytes, then
    checks toEqual and the bytes for each asset, then checks revenue_streams in the golden = hype, link, lit, pump, sky, uni.
  - Mutations at b360bc2: (a) with the `settlement` condition reverted, the test fails with
    `expected ['aero','cake','crv',…(3)] to deeply equal []`. (b) One non-revenue field (`asset`) changed for vvv in
    the golden fails with `['vvv']`. (c) With the golden deleted the test fails on ENOENT and the file is not recreated.
    Without UPDATE_GOLDEN it never writes.
  - The settlement-keyed rule (report concern) gives cc59fa7's output on all 13 (checked). It is a design choice that needs
    a ruling, not breakage.
- **M1 ADDRESSED.** README: `--legacy` is gone from the command list. The YAML and report paragraphs describe income_statement / v2.
  The only remaining "legacy"/"reporting" mentions are the retirement notes.
- **M2 ADDRESSED.** src/config/incomeStatement.ts: 3 comments rewritten. The only `reporting` left is "which once shared them, was retired".
- **M3 ADDRESSED.** `tests/report/v2Golden.test.ts` `readGolden` writes only when UPDATE_GOLDEN=1. A missing file throws.
  With v2-report-13.json deleted at b360bc2 the suite fails ("golden … is missing", no tests run) and the file is not recreated.
  The new unit test checks that `readGolden(missing, now, false)` throws and writes nothing. The test can no longer pass
  against itself unless someone sets the documented flag.
- **M4 ADDRESSED.** `tests/config/load.test.ts`: the T10 Lido shape (revenue, `remainder: protocol`, no holders) loads with no
  statement error. Yields cash/buyback/shareholder are 0 (numbers), holderFlow is empty, byBucket is null, flags are [] and
  payoutRatio is 0. It is named as a characterisation pin. Passes.
- **M5 ADDRESSED.** The docs/ops/deploy.md note lists per-bucket growth, disclosure dates, stream metric names,
  protocolMargin and revenue.basis, each with its nearest v2 field. I spot-checked that the fields named exist in src
  (`disclosedGrowth.latestAgeDays`/`gapDays` in src/report/holderYield.ts:115-116; `byBucket` without growth in
  src/report/incomeStatement.ts:244; no `protocolMargin` in src).
- **M6 ADDRESSED.** The rows are real 0f4b2fe output. In a 0f4b2fe worktree,
  `summarizeHolderYield(yieldReport(syntheticInput(repoAsset(id)), {legacy:true}))` gives a holder_yield deep-equal to the
  fixture's for **both** lit and aero (23 keys each). 0f4b2fe's `src/app/tick.ts:85` writes holder_yield with
  `{legacy:true}`, so this matches what prod writes.
  - The envelope equals `tests/fixtures/daemon/refresh-result-v1.json`'s, except aero's `asset`/`tick_id`, which is expected.
  - At HEAD the test parses each row through TickReportSchema (round-trip equal, nothing stripped) and checks `formatAssetBlock` lines.
- **M7 ADDRESSED.** Both proposal edits in tests/app/inbox.test.ts use `['income_statement','window_days']`.

## Invariants
- No change in b48c3cf..b360bc2 to tests/report/golden/v2-report-13.json, tests/agent/golden/packs-13.json or assets/*.yaml.
- `git diff cc59fa7 b360bc2 -- tests/fixtures`: only aero.yaml (holder_flows removed), hype.yaml (holder_flows removed)
  and disclosure/lit-q3-run.json (2x path `reporting` -> `income_statement`). These are R11.7's three edits; the M6
  fixture is in tests/app/golden/.

## New breakage
None found. At b360bc2: `npm run typecheck` clean; `npx vitest run --maxWorkers=2`: 138 files / 1677 tests passed.
