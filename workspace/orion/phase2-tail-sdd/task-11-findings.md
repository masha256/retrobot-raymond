# Task 11 review (G4): 2f5bc8d (11a) + b48c3cf (11b) on cc59fa7

Spec verdict: **PASS with one Important deviation** (I1: R11.7's "13 packs byte-identical" isn't true, and the test
pins less than the report claims). Quality verdict: **Good**. 0 Critical, 1 Important, 7 Minor.

## How I checked
- I made my own detached worktrees, rev-11 (b48c3cf) and rev-11-base (cc59fa7), with node_modules symlinked (the lockfile
  is identical) and removed them at the end. I touched no Postgres outside orion_test, ran nothing over the network or
  ssh, and edited no repo file.
- Full suite at b48c3cf: `npx vitest run --maxWorkers=2` gave 138 files / 1672 tests passed, 0 failed, 0 skipped, on
  the first run. `npm run typecheck` and `npm run lint:promises` are clean. The harness
  (`/usr/bin/python3 -m unittest test_compare.py test_prod_copy.py`) ran 96 tests, OK.
- **Golden honesty (risk 3).** I copied 11a's `tests/agent/golden/packs-13.json`, `tests/report/golden/v2-report-13.json`,
  `v1-report-13.json`, `v2Golden.test.ts` and `packGolden.test.ts` (its first describe; `holderFlowMetrics` doesn't exist
  at the base) into the cc59fa7 tree and ran them there:
  - Both goldens pass at the base: 67 tests.
  - The base's `holderYieldReport(syntheticInput(repoAsset(id)))` equals `v1-report-13.json` for all 13 assets.
  - So the goldens really are cc59fa7 output, not self-generated at HEAD. The input sha256 also pins the frozen
    `SYNTHETIC_FLOWS` order.
- **Default day (risk 2).** I computed cc59fa7's `defaultDayFlowMetrics` minus v1's periodic streams for all 13 at the
  base. All 13 equal `V1_DAY_FLOWS` hard-coded in `tests/report/incomeStatement.test.ts:343-357`. The pin is real, and
  12 assets are asserted unchanged at HEAD.
  - yCRV changes per R11.6: `yearn_styc_fee` is dropped and the two by-sender flows join
    (`tests/report/incomeStatement.test.ts:366`, plus the DB test at `tests/report/load.test.ts:58`).
- **Config retirement and hash pins (risk 3).**
  - The retired keys are refused by name at three points:
    - at load: `tests/config/load.test.ts`, "refuses the retired %s key";
    - at filing: `tests/agent/tools.test.ts:323-325`, through `propose_change`;
    - at approve: `tests/app/proposals.test.ts:244-246`, where the YAML is read back unchanged afterwards.
  - All 14 base hashes are gone from `tests`/`src`: the 13 assets plus MINI's `c8cc4642…`. The only leftover is in the
    historical plan doc. `tests/fixtures` changes only by the 3 edits R11.7 accepts.
- **Snapshot (risk 4).** `SNAPSHOT_SCHEMA=orion.snapshot/2`, and `KNOWN_SNAPSHOT_SCHEMAS` still accepts a queued `/1`.
  Tests cover it: `tests/push/envelope.test.ts:106` (/1 publishes, /9 refused) and `tests/daemon/snapshotPush.test.ts:185`.
  It is documented in deploy.md §"Phase 2 tail: Task 11 release". I diffed every JSON path v1 published against v2;
  see M5.
- **Harness (risk 5).**
  - reports.sh: identical flags on both sides; no `--legacy`, no `--help` probe.
  - TMPDIR confinement uses `realpath -m` with a `"$TMP_ROOT"/?*` match, so TMPDIR itself, an unset TMPDIR and symlink
    escapes are all refused.
  - compare.py: v2-vs-v2 at rel 1e-12 when the new side has no v1 key and the old side has `incomeStatement`.
  - Maps are required only for v1-old vs v2-new; the 13 named assets are required; `--json` works.
  - Refusal tests are present (ReportsTest, V2VsV2Test).
- **v1 consumers (risk 1).** I ran `git grep` for `income.`, `holderFlowGrowth`, `flows[`, `--legacy`, `legacy`,
  `reporting`, `holder_flows`, `extra_cash`, `revenueDisclosed` over src, tools, docs/ops, docs/templates, scripts,
  skills, personas and README.
  - Left in src/tools/ops: parity.ts/parity.json/expected.py (v1-old-side only, deliberate), import-sqlite (retired),
    and the price-basis `legacy` (unrelated).
  - `scripts/provision/files/orion-remote` passes no `--legacy`.
  - README is stale (M1).
  - Old job rows: see M6.

## Important

**I1. The agent pack changed for 6 of the 13 assets; the golden test pins only LIT's whole pack.**
- Where: `src/agent/context.ts:95-104` (revenueStreams) and `tests/agent/packGolden.test.ts:56-60`.
- What changed: for aero, cake, crv, cvxcrv, sdcrv and ycrv, `buildContextPack` now emits a `revenue_streams` key that
  cc59fa7 never emitted. At the base it was built only from `reporting.revenue` metric streams; now it comes from every
  `income_statement.revenue` line with a metric. Examples:
  - aero: `[{id:fees, metric:flow_usd.fees}]`
  - cvxcrv: 4 lines (`vecrv_fees_rev`, `platform_*`)
  - sdcrv: 6+ lines
  - ycrv: `[{id:fees_rev, metric:flow_usd.yearn_gross_fees}]`
- How I found it: I ran packGolden with `expect(now[id]).toEqual(golden[id])` for all 13 against the cc59fa7 golden. LIT
  and the other 6 are identical; these 6 differ only in `revenue_streams` (absent before → present now).
- Why the test misses it: it compares `observations_in_force` for 12 assets and the whole pack only for LIT.
- What this contradicts:
  - task-11-report.md ("13 packs byte-identical");
  - R11.7 ("the pack goldens (13 packs byte-identical to cc59fa7) are the proof that nothing else moved").
- Impact: the disclosure analyst's paid-run context changes on 6 assets with no ruling. The report numbers are
  unaffected. The brief's minimum, "LIT pack identical" and "flow set equal", still holds.
- Fix, either one:
  - (a) emit `revenue_streams` only where cc59fa7 did. That was every asset with metric streams under
    `reporting.revenue`: hype, link, lit, pump, sky, uni, vvv-proxy... Simplest reproducible rule: only when some line's
    kept share < 1 (LIT), or else the frozen base set.
  - (b) accept the new key by ruling and make the test compare the full pack for all 13: whole-pack equality against the
    golden, with the 6 assets' `revenue_streams` listed explicitly as the accepted delta.
- Test shape:
  `for (const id of ALL_ASSETS) expect(now[id], id).toEqual(golden[id])`, which currently fails on aero first.

## Minor

**M1. README.md is stale.**
- `README.md:46` still documents `report yield ... [--legacy]`, which the CLI now refuses.
- `:74` describes the report from `reporting.window_days` / `reporting.revenue` and "`--legacy` adds the v1 keys".
- `:25` still lists "holder flows, the `reporting` block" as YAML content.
- Fix: update to income_statement / v2 only.

**M2. Stale comments in `src/config/incomeStatement.ts`.**
- `:10`, `:111` and `:160` still say the shared keys reuse "`reporting`'s shapes" and are "shared with `reporting`".
- `src/report/parity.ts:78` is the same, but parity is v1-old-side only, so that one is acceptable.

**M3. `tests/report/v2Golden.test.ts:59` can pass against itself.**
- It writes the golden when the file is missing (`|| !existsSync(GOLDEN)`), so a deleted golden regenerates from HEAD
  and every case passes.
- Fix: write only under `UPDATE_GOLDEN=1`; otherwise fail when the file is missing, as packGolden does.

**M4. The "Lido case" test in `tests/config/load.test.ts:55` doesn't test the Lido shape.**
- It parses MINI with no `income_statement` at all.
- The T10 shape is an income_statement with revenue, cost_of_revenue and `remainder: protocol`, and no `holders`.
- I checked in scratch that this shape loads and reports: yields `cash/buyback/shareholder = 0`, `holderFlow.gross = 0`,
  no flags, which matches T10's "the yields read zero". Nothing pins it.
- Test shape: parse `${MINI_ASSET_YAML}income_statement: {category, scope, window_days: 91, revenue: [{id: fees_rev,
  metric: flow_usd.fees}], remainder: protocol}`, then `yieldReport(syntheticInput(a)).incomeStatement.yields.shareholder === 0`.

**M5. `/2` drops some v1 fields that have no direct v2 equivalent, and the docs don't list them.**
- Where: `src/push/envelope.ts:8-13` and deploy.md:379. Both say only that the v1 keys are gone.
- v1 → v2 has no direct counterpart for:
  - `buckets.{burn,hold,cash}.growth`: per-bucket holder-flow growth. `holderFlow.byBucket` has none; it can only be
    re-summed from the lines' `growth.current/prior`.
  - `revenueDisclosed.latestAt` / `previousAt`: disclosure dates. v2 has only `disclosedGrowth.latestAgeDays` / `gapDays`.
  - `revenue.streams[].metric`: v2 `revenue.lines[]` carries no metric name.
  - `income.protocolMargin`: derivable as protocol/revenue.
  - `revenue.basis`: partly covered by each line's `method`.
- Everything else maps:
  - `flows` → `holderFlow.lines`
  - `holderFlowGrowth` → `holderFlow.growth`
  - `supply` → `dilution.supply`
  - `volume` → `incomeStatement.volume`
  - `yields` (incl. `pegTrailing` and `dilutionLines`) → `incomeStatement.yields`
  - `crossCheck` / `disclosedGrowth` → revenue line
  - `outsideRevenue` → `belowLine`
  - `income.checks` → `checks`
- Fix: add this list to the release note, so the site doesn't discover the gaps.

**M6. No test parses a job row from the release now on prod.**
- `tests/app/tickReport.test.ts:113` parses only `refresh-result-v1.json`, which is pre-Task-4 (v1 fields only).
- The release now on prod (Tasks 4-10) writes v1 fields and statement fields in the same `holder_yield`.
- The strict schema accepts that shape: `revenue_annualized` etc. are now optional, and the statement fields are
  optional too. But nothing pins it.
- Test shape: at cc59fa7, run `summarizeHolderYield(yieldReport(input, {legacy:true}))`, freeze it as a fixture, and
  `TickReportSchema.parse` it plus `formatAssetBlock` it at HEAD.

**M7. Stale proposal fixtures in `tests/app/inbox.test.ts:36` and `:115`.**
- They still file proposals with path `['reporting','window_days']`.
- They're display-only, so they work, but they model edits that can no longer be approved.
- Fix: use `['income_statement','window_days']`.

## Not findings (checked)
- **Eligibility.** The window is `income_statement.window_days` (91 on all 13, asserted) instead of the max
  `holder_flows.window_days` (all 91 at the base). `holderFlowMetrics` equals the retired `holder_flows` metrics for all
  13, hard-coded from cc59fa7. I confirmed that list against the base YAML via the base pack golden.
- **Header and notes.** `reportHeader` re-derives v1's 4 notes from income_statement in the same order. The 65-input
  v2 golden at base equals HEAD.
- **Tick holder_yield.** It now reads only the statement (T4 M2). A C4 row prints the header plus an ALERT. Nightly
  `yields:` numbers are now the statement's: Task 8 basis, intentional and documented.
- **Manifest vs envelope.** A queued `/1` envelope in a `/2` manifest is documented in sign.ts:11-12.
- **Outside the repo.** The soak script and Phase 3 spec §7 are listed in the report as controller items. Correct.
