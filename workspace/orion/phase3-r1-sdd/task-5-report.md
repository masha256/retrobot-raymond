# Task 5 report: `volume: { not_measured: <reason> }`

Status: DONE. Commit 6a1c55f `feat(report): volume may be not_measured with a reason` (on 6f97c21).

## What
- `src/config/schema.ts`: `VolumeSchema` = `z.union([z.array(z.string()).min(1), z.strictObject({ not_measured: z.string().min(1).max(200) })])`.
  The array branch is unchanged, so the list form parses to the same array (no config hash moves). New exported
  helper `volumeMetrics(volume)` (list → itself, object/undefined → `[]`); `sharedReportingIssues` uses it (its
  duplicate/flow-type checks now see no metrics for the object form).
- `src/report/load.ts`: `reportFlowMetrics` spreads `volumeMetrics(is.volume)`, so the object form loads no metric.
- `src/report/incomeStatement.ts`: `IsV2.volume` gains optional `notMeasured?: string`. Object form →
  `{ metrics: [], annualized: null, growth: noSeries('not measured'), notMeasured: <reason> }`. `noSeries('not measured')`
  is the exact Growth a not_measured statement line already gets (`valueGrowth` for kind `nm`):
  `{ current: null, prior: null, change: null, annualized: null, note: 'not measured' }`. List form: same code path as
  before, no `notMeasured` key.
- `src/config/incomeStatement.ts`: no change needed (only comments mention volume; the keys are checked in schema.ts).
- Other consumers checked by grep (`volume` in src/, tools/, scripts/): `src/report/parity.ts` reads only the paths
  `incomeStatement.volume.annualized` / `.growth.annualized` (no `.metrics`), so not changed; `src/push/envelope.ts`
  only mentions the retired v1 key in a comment; nothing in src/notify, src/agent or the snapshot code reads
  `volume`. The report is serialized whole, so the new key appears only where the object form is used.
- `tests/assets/lockers.ingest.test.ts:201`: one-line type cast `(is.volume ?? []) as string[]` (outside the brief's file
  list; required by typecheck now that the type is a union; no behaviour change).

## Tests (TDD)
- RED (`npx vitest run tests/config/incomeStatement.test.ts tests/report/incomeStatement.test.ts --maxWorkers=1`):
  2 failed | 103 passed (105); both with `OrionError: income_statement.volume: Invalid input: expected array, received object`.
- GREEN same command: 105 passed (105).
- New tests: config: object form parsed exactly as written; 200 chars accepted; 201, `''`, `{ not_measured: 'x', extra: 1 }`,
  `{}`, `[]` refused; list form parses to `['flow_usd.core']`. Report: object form gives the exact shape (toStrictEqual +
  key order) and `reportFlowMetrics` equals the no-volume block's; cake/cvxcrv/uni list form keys are exactly
  `['metrics','annualized','growth']` (existing test still deep-equals the windowSum/growthOf figures).
- Byte check: full `incomeStatementV2(syntheticInput(repoAsset(id)))` JSON for all 13 assets dumped before and after
  the change with a temporary (deleted, never staged) test file: `cmp` identical.
- Full suite `npx vitest run --maxWorkers=2`: 143 files, 1741/1741 passed (baseline 1735 + 6 new). No load flakes this run.
- `npm run typecheck`: clean (0 errors).
- No hash pin moved (suite green, no pin edited); VVV golden / v2Golden pass.

## Self-review
- Union order: array first, so the list form never hits the object branch; strictObject refuses unknown keys.
- No 0 anywhere for the object form: annualized null, growth all-null with the not_measured note.

## Concerns
- For Task 6: once CAKE/UNI switch to the object form, `PARITY_PATHS` cake/uni `VOLUME` pairs (src/report/parity.ts,
  tools/phase2-proof/parity.json) will read `null` for `incomeStatement.volume.annualized`. parity.test.ts asserts only the
  constant map, so it stays green, but any proof/soak that uses those pairs would see a null-vs-number diff: Task 6 or
  the controller should drop VOLUME from cake/uni there (and regenerate parity.json) if that map is still used.
- cvxcrv also lists `volume`; not in this task's scope, unchanged.
