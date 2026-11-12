### Task 5: `volume: { not_measured: <reason> }`

**Files:**
- Modify: `src/config/schema.ts` (`VolumeSchema`), `src/config/incomeStatement.ts`, `src/report/incomeStatement.ts`
  (the `volume` output, line ~867), `src/report/load.ts` (the metrics read), `src/report/parity.ts` if it reads
  `volume.metrics`
- Test: `tests/config/incomeStatement.test.ts`, `tests/report/incomeStatement.test.ts`

**Interfaces:**
- Produces: `income_statement.volume` = `string[]` (as today) | `{ not_measured: string }` (1-200 chars). Output, for
  the new form only: `volume: { metrics: [], annualized: null, growth: <the null Growth the report uses for a
  metric-less series>, notMeasured: '<reason>' }`. The list form's output has no `notMeasured` key (byte-identical).

- [ ] **Step 1: Tests.** The list form is unchanged for a fixture asset (deep-equal against the current output). The
  new form produces the shape above. `{ not_measured: '' }` and `{ not_measured: 'x', extra: 1 }` are refused. The
  VVV golden/report hash tests still pass.
- [ ] **Step 2: Implement.**
- [ ] **Step 3: Run** the report and config tests, the full suite and typecheck. No hash pin moves.
- [ ] **Step 4: Commit** `feat(report): volume may be not_measured with a reason`.

