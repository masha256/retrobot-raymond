# Task 10 fix round 1 — scoped re-review (0bd7a40..cc59fa7)

Method: read `git diff 0bd7a40 cc59fa7`, the report's "Fix round 1", progress.md's prod matrix, and ran checks in my own
worktree (rev-t10r1 @ cc59fa7, `npm ci --offline`, orion_test): tsc clean, lint:promises clean, targeted 9 files /
184 tests green, full suite 1609/1609 (two later runs); one earlier run had 2 failures I could not reproduce, while
another vitest was running on the host (orion_test contention, most likely; not traced to this diff). I ran each
mutation below, then reverted it.

## Verdicts

- **I-1 (refined R10.7): ADDRESSED.**
  - The derived branch of `originMismatch` is gone (run.ts ~519). The level guard is at run.ts:360 and the schedule
    guard at run.ts:336, both still there. Test: removing the level guard fails originGuard.test "refuses a reading…".
  - `withInputOrigin` spreads `{...p.locator, input_origin:'api'}` and only when `stamp === 'api'` (apiInputs > 0).
    The mixed api/onchain refusal stays. Tests:
    - (a) derived.test over hype.fund_buys_daily: the full locator `toEqual`s
      `{metrics, params, input_origin}`; stored and written both 'api'.
    - (b) burn_momentum over a transfer scan: the locator `toEqual`s the configured one, with no input_origin.
    - Mutations: replacing the locator instead of merging fails (a); always adding the key fails 3 derived tests;
      dropping the input_origin read in originOf fails (a) and the origin.test row.
  - `originOf(derived)` order: manual_* first, then input_origin, then the third_party → api fallback (kept), else
    onchain. For prod's shapes nothing changes: progress.md says all 389 derived rows are onchain with no
    input_origin, and the 2 manual_* rows are checked first. No measured or disclosed branch changed.
  - Registry test (tests/provenance/adapterOrigins.test.ts): the SAMPLES key set equals `adapterNames()`, and the
    writer stamp (level/schedule `source`, SERIES_ORIGIN for daily/periodic) must equal what originOf reads back.
    Mutations in src that this test catches: chain.view_sum → api, solana.supply_burn_daily → onchain, and deleting
    crv.emission_rate_annual. writeApiFlow and writePeriodicPayments now use SERIES_ORIGIN, so the test checks the
    constant those writers actually stamp.
- **M-1: ADDRESSED.** The README uses `"$WT/node_modules/.bin/tsx"`.
- **M-2: ADDRESSED.**
  - ADAPTER_ORIGINS now holds only the contract-state adapters, plus the retired aero.* entries. The file says why
    they are kept: rows of theirs are still on prod. origin.test pins the key set.
  - The retired names cannot be run (they are not in the registry), so the consistency test cannot cover them. That
    is acceptable: their values are pinned by the prod-matrix rows.
- **M-3: ADDRESSED.** deploy.md gives a remedy per count: obs_null/disclosure_uncited, and for levels_null:
  active → `job run-now levels`, paused → resume, run, re-pause, missing → `job run-now retention`.
- **M-4: ADDRESSED** (with the stated deviation, which I accept).
  - `src/provenance/configHash.ts` is deleted, and `git grep confirmConfigHash|UNLOADED|provenance/configHash` in
    src, tests and tools is empty. confirm takes `{approvedBy}`, and a missing stored provenance now throws
    `observation_not_found`.
  - The per-day fallback is removed. `basis:'config'` remains only when `input.provenance` is undefined.
  - Basis cannot change for a loader-built report:
    - `provenanceByDay`'s filters (confirmed; periodDays===1, with null also counted, a superset; periodic ≥1) cover
      every day of `dayRows`/`periodicDaily`/`statementSeries`. Provisional days were excluded before as well.
    - With method NOT NULL since 0006, the old per-day predicate was always true whenever provenance was passed.
    - The only undefined-provenance loader path is the v2-read catch (`v2ReadError`), and it behaved the same before
      the change.
  - The new incomeStatement test pins that a day with no row in the provenance map no longer flips the basis.

## New breakage

None found. Two Minors, neither a regression:

1. **Minor (pre-existing, not introduced here): the schedule-branch origin guard (run.ts:336) has no test.**
   - Replacing it with `null` leaves all 383 tests in tests/ingest green. Only the level branch is pinned
     (originGuard.test).
   - Test shape: register a schedule adapter that returns `schedule_steps` with `source:'onchain'` on a
     first_party_api rung. Expect the source to fail with `origin_mismatch` and no rows written.
   - The registry test does check every registered schedule adapter's stamp statically, so this only matters for a
     future adapter.
2. **Minor/info: a derivation over DefiLlama now writes `input_origin:'api'` too** (as the report says). Its origin is
   'api' either way, and progress.md lists no prod row with that shape. When a revised value is rewritten, the new row's
   locator carries the extra key, which is expected under R10.7.
