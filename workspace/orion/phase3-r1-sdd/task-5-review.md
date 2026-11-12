# Task 5 review: `volume: { not_measured: <reason> }` (6f97c21..6a1c55f)

### Spec Compliance

- ✅ Spec compliant. Every item in the brief is there:
  - Schema union: `src/config/schema.ts:45`. Helper: `:48`. Shared checks: `:150,154`.
  - Report output: `src/report/incomeStatement.ts:254,870-878`. The new form gives exactly `{ metrics: [], annualized: null, growth: noSeries('not measured'), notMeasured }`. `noSeries` is at `:333`. It is the same Growth a not_measured statement line gets (`:460`, `:677-678`).
  - Metrics read: `src/report/load.ts:27`.
  - `src/config/incomeStatement.ts` and `src/report/parity.ts` are listed "if needed". Neither reads `volume.metrics`, so leaving them unchanged is correct.
  - Extra: the cast at `tests/assets/lockers.ingest.test.ts:201` is outside the brief's file list. Ruling R17 accepted it.
- ⚠️ Cannot verify from the diff: the CAKE/UNI `VOLUME` parity pairs.
  - What happens: `src/report/parity.ts:79-81,94,124` and `tools/phase2-proof/parity.json:327,771` will read `null` once Task 6 moves those assets to the object form.
  - Already carried: R17 makes this binding on Task 6.
  - Controller: confirm Task 6 drops the pairs and regenerates parity.json.

### Named risks

**1. Byte equality for the list form: PASS.**
- Config hash:
  - `parseAssetObject` hashes `canonicalJson(config)` of the parsed config (`src/config/load.ts:25,35`).
  - The array branch comes first in the union and is the same schema as before (`z.array(z.string()).min(1)`).
  - I ran zod 4 from the phase3 node_modules (a scratch script outside the worktree): `['b','a']` parses to `["b","a"]` in order and unchanged. Duplicates pass the union and are still refused by `sharedReportingIssues` (`schema.ts:155`). So the parsed value and its hash are unchanged.
- New keys:
  - `incomeStatement.ts:870-878` is the only place that emits `volume` (I grepped `volume` in src/ and tools/).
  - The list branch builds `{ metrics, annualized, growth }` as before, with no `notMeasured`.
  - Test: `tests/report/incomeStatement.test.ts:617` asserts the exact key list for cake/cvxcrv/uni.
  - The implementer's ad hoc `cmp` of all 13 reports is reported but not committed. The key-order test is enough as a guard.

**2. Null discipline: PASS.** I grepped every reader:
- `src/report/load.ts:27`: `volumeMetrics` gives `[]`, so the object form reads no series.
- `src/report/parity.ts:146-150`: `num` passes `null` through and throws on non-numbers. It never turns null into 0.
- Snapshot/site export, `src/push/body.ts:72`: the report is `JSON.parse(JSON.stringify(...))` whole, so the nulls and `notMeasured` are kept as they are.
- Nightly Slack:
  - `src/notify/format.ts:110-121` reads only headline fields (revenue, multiples, holder-flow growth), never `volume`.
  - `src/daemon/jobs/nightlyReport.ts` passes the report through.
- `src/agent/*`: no reference to `volume` or the report's `annualized`. `context.ts:99` reads only revenue lines.
- `tools/phase2-proof`:
  - `expected.py:153` reads v1's `volume` via `total`→`num`, which raises on a non-number. It never treats null as 0.
  - `compare.py:58` reads v1 keys only.
- `src/push/envelope.ts:11` mentions `volume` only in a comment.

**3. Strictness: PASS.**
- Results of the zod check above:
  - `{not_measured:''}`: refused (too small).
  - 201 chars: refused (the test is at `tests/config/incomeStatement.test.ts:250`).
  - `{not_measured:'x',extra:1}`: refused (unrecognized key).
  - `[]`: refused (too small).
  - Mixed forms `['a',{not_measured:'x'}]` and `{not_measured:'x',metrics:[...]}`: refused.
  - `{}`, `null` and a bare string: refused.
- Proposal filing and approve parse through `parseAssetYaml` (`src/app/proposals.ts:6`), which uses the same `AssetConfigSchema`, so they refuse the same inputs.

### Strengths
- Small and well placed. A single `volumeMetrics` helper (`schema.ts:48`) is shared by the schema checks and `reportFlowMetrics`, so the object form can never feed a metric into the report-day calculation.
- The new output reuses the existing not-measured idiom (`noSeries('not measured')`, `notMeasured: <reason>`), so readers see one convention.
- The tests check the exact shape and key order of both forms (`tests/report/incomeStatement.test.ts:617,622`). They also check that `reportFlowMetrics` for the object form equals the no-volume block's.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)
1. `tests/config/incomeStatement.test.ts:250,253,256,259,262`: the refusal cases use a bare `.toThrow()`.
   - Problem: a case could pass for an unrelated reason, for example if a `base()` fixture change made it invalid.
   - Fix: assert the message, e.g. `/income_statement\.volume.*Unrecognized key/` and `/not_measured: Too small/`, as the neighbouring `refused(..., /re/)` cases do.
2. `tests/config/incomeStatement.test.ts:232-263`: no test for the mixed form, although it is a named risk. Examples: `['flow_usd.core', { not_measured: 'x' }]` and `{ not_measured: 'x', metrics: [...] }`. Both are refused today; I checked by script, not by a committed test.
3. `src/config/schema.ts:45`: the union makes list typos give a vaguer error.
   - Example: `volume: [flow_usd.a, 3]` now reports `income_statement.volume: Invalid input`. Before, it said `expected string` at `volume.1`.
   - Impact: operator-facing error quality only. A short `.refine`/custom message, or a `z.custom` pre-dispatch on `Array.isArray`, would restore it.
4. `src/config/schema.ts:45`: a whitespace-only reason (`'   '`) is accepted. This matches the statement lines' `not_measured: z.string().min(1)` (`src/config/incomeStatement.ts:49,66,95`), so it is consistent. Adding `.trim()` or `.regex(/\S/)` would close it if wanted.
5. `docs/templates/T2-exchange-buyback.md:166` documents only the list form. No doc describes `{ not_measured }` for `volume`.

### Assessment

**Task quality:** Approved

**Reasoning:** The change is minimal. The list form is unchanged byte for byte: same schema branch first, same output object, key order pinned by a test. The object form reads no metric and reports null with its reason, and I found no reader that turns it into 0. The remaining items are test precision and error-message polish.
