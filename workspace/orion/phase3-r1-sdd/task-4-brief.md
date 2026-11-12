### Task 4: `schedule.unlocks_next_year`, a generic cited unlock schedule

**Files:**
- Create: `src/ingest/adapters/schedule.ts`, `tests/ingest/scheduleUnlocks.test.ts`
- Modify: `src/ingest/types.ts` (level `SourceValue` gains `citation?`), the ingest writer that builds level
  observations (`src/ingest/run.ts`, where an adapter level becomes a `NewObservation`), `src/ingest/adapters/registry.ts`
  (register), `src/report/sourceTypes.ts` (`'schedule.unlocks_next_year': 'disclosure'`),
  `tools/sources-register/generate.ts` (`ADAPTER_ENDPOINTS`: no endpoint, the citation urls instead)

**Interfaces:**
- Produces: adapter `schedule.unlocks_next_year`, `needsRpc: false`, no network. Params (strict, unknown keys refused
  in `validateParams`):
  `{ citation: { url: string; quote: string }; schedules: Array<{ label: string; tokens: number } & ({ tranches: { first: 'YYYY-MM-DD'; every_months: 1..12; count: 1..120 } } | { linear: { start: 'YYYY-MM-DD'; years: number } })> }`.
  Value = the sum, over schedules, of the tokens due in (now, now + 365 d]. Tranches: `tokens / count` per tranche date
  (the dates are `addMonthsClamped`, the same as `lit.ts`). Linear: `tokens / years` per 365 days times the overlap
  in days / 365, clamped to [start, start + years x 365 d]. Returns
  `{ kind: 'level', value, observedAt: now, source: 'api', detail: '<label> <x>M, ...; cited <url>', citation }`.
  `citation` gives the row's `citation_url`/`citation_quote`, with method `disclosed`, rung `disclosure` (0006's
  `observations_disclosure_citation` CHECK needs the url).

- [ ] **Step 1: Find the PUMP citation (P4).** Search pump.fun's own pages (`pump.fun/docs/*`, the ICO terms, the
  `@pumpfun` posts) for the team/investor lock and vest. Record what was found, with url and verbatim quote, in the
  ledger. If no pump.fun page states it, use the Blockworks filing
  (`https://blockworks.com/token-transparency/filing/pump`, quote: "were locked for 12 months from 12 July 2025 and
  then vest linearly over three years to July 2029"), and begin the YAML comment with "compiled by Blockworks, not the
  issuer".
- [ ] **Step 2: Tests** (`ctx.nowIso` fixed):
  - `LIT at 2026-11-12T00:46:15Z`: tranches {first 2027-01-29, every_months 1, count 36}, tokens 260e6 + 240e6, gives
    `500e6 / 36 * 10` = 138,888,888.89 (to 1e-6).
  - `PUMP at 2026-11-12T00:46:41Z`: linear {start 2026-07-12, years 3}, tokens 150e9 (team) + 97.5e9 (investors), gives
    exactly 82.5e9.
  - `tranche on now + 365d counts; one on now does not`.
  - `linear ending inside the window counts only to its end`: start 2026-07-12, years 3, now 2029-01-12: 182 days'
    worth.
  - `before start counts nothing`, and `a schedule wholly past is 0`.
  - `validateParams` refuses an unknown key, a missing citation, a quote longer than 500 chars, `tokens` <= 0, both
    or neither of tranches/linear, and a bad date.
  - Ingest: the written row has `source_type 'disclosure'`, `method 'disclosed'`, and `citation_url` set.
- [ ] **Step 3: Implement**, then register it and add the rung and register lines.
- [ ] **Step 4: Run** the tests, `tests/report/sourceTypes*.test.ts`, the sources-register test, and typecheck.
- [ ] **Step 5: Commit** `feat(ingest): schedule.unlocks_next_year, a cited unlock schedule (disclosure rung)`.

