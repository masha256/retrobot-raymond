# Task 10 report (gate G3): 0006 provenance NOT NULL, observations.source dropped

Status: DONE_WITH_CONCERNS. Commit 0bd7a40 on feat/phase2-tail (base 0f4b2fe): "feat(db)!: 0006 provenance NOT NULL,
source column dropped (Task 10, G3; breaking release)". 71 files, +837 / -929. Not pushed, merged, tagged or deployed.

## What changed
- `src/db/pg/migrations/0006_provenance_not_null.sql` (first line `-- breaking`): SET NOT NULL on observations.method,
  source_type, locator, code_version, config_hash; `observations_disclosure_citation` CHECK (source_type <> 'disclosure'
  OR citation_url IS NOT NULL OR code_version = 'pre-v2'); DROP COLUMN observations.source; latest_levels.source_type
  and locator SET NOT NULL (every writer sets them; prod 0 null source_type). 0001-0005 untouched.
- `latest_levels.source` is KEPT (R10.1 said drop "if it is only the legacy origin"): the `levels` snapshot body
  publishes it, and latest_levels has no `method` column, so originOf cannot derive it without a new column.
- `src/provenance/origin.ts`: `originOf({method, sourceType, locator, formula})`, `originOfRow(row)`, `ADAPTER_ORIGINS`
  (every registered adapter's stamp, plus the retired aero.* names prod rows carry). Rules: disclosed -> constant 'api',
  else 'manual'; derived -> formula `manual_*` 'manual', rung third_party 'api', else 'onchain'; measured -> log/pool
  scan 'onchain', contract_state -> ADAPTER_ORIGINS[locator.adapter] ?? 'onchain', any API rung 'api'. Inputs only as
  R10.2a allows.
- Readers: `Observation.source` is computed by originOfRow in `src/db/observations.ts` (so CLI text/JSON `source`, the
  agent pack/describe/ledger, inbox, flow conflicts + `--adopt`, the DefiLlama revision-window manual rule, the token
  backfill skips, Solana's supply drop all read it unchanged). The one SQL reader (`src/checks/evaluate.ts` revision
  check) now selects method/source_type/locator/formula and derives. StoredProvenance/LatestLevel types tightened to
  non-null.
- Writers: `source` removed from NewObservation and every insertObservation call (fetch, apiFlow, flow, periodic,
  data set, proposals approve, ledger, confirm). `src/ingest/run.ts` `originMismatch`: a level, schedule or derived
  reading whose own stamp differs from originOf(its provenance) fails that reading (`origin_mismatch`) and writes
  nothing (the fetch JSON `written[].source` keeps the stamp, so it always equals the stored origin).
- R10.3: `data set --source` removed (smaller change; a hand-entered row is disclosed/disclosure -> 'manual');
  `--citation` still required.
- Retired: `db backfill-provenance` + `src/provenance/backfill.ts` + its test (it reads `source`; nothing can be null
  after 0006). `defillamaUrlOf` moved to `src/provenance/locator.ts` (token backfill uses it).
- R10.4: `deploy.sh --breaking` and `orion-remote switch` already refuse a pending breaking migration without the flag,
  pg_dump first with it, and refuse rollback after `breaking=1`: no gap, no test added. docs/ops/deploy.md new section
  "Phase 2 tail: release with 0006 (breaking)" (pre-deploy null check via `sql-ro` on prod / `o db query-ro` as
  orion-stage, stage -> soak -> prod with --breaking, no rollback past it); postgres.md notes; deploy.md Phase 2 step 3
  marked release-2 only.
- R10.6(4): `tools/phase2-proof/prod_copy.py` unchanged (copy is migrated by the old release so columns match prod);
  README run order now runs `origin-check.ts` before the new side's `db migrate --breaking`.
  `tools/import-sqlite` now requires a target at exactly 0005 (`IMPORT_SCHEMA_LEVEL`), proof opens with
  checkSchema:false; documented path = import -> release-2 `db backfill-provenance` -> `db migrate --breaking`.
- New `tools/phase2-proof/origin-check.ts` (controller's 27,533/27,533 proof): on a schema that still has `source`,
  `ORION_DATABASE_URL=... ORION_DB_SCHEMA=p2proof_x npx tsx tools/phase2-proof/origin-check.ts` prints
  {rows, equal, unmapped, mismatches by shape, first 50 ids}; exit 0 only when equal == rows.
- Tests: `tests/helpers/provenance.ts` `testProvenance(source, cited)` replaces `source:` on ~80 seeding sites
  (manual uncited = the R17 2a correction shape, manual cited = disclosure). Test schemas migrate with breaking;
  `createTestSchema({ upTo })` for the importer. Followups note: Task 10 section.

## RED / GREEN
- origin table test: RED `Cannot find module '../../src/provenance/origin.js'` (no tests); GREEN 44/44.
- migrate tests: with 0006 removed, 3 failed (the 0006 test, the full-apply and schema-absent tests); GREEN 11/11.
- origin guard (tests/ingest/originGuard.test.ts): with the guard disabled, "refuses a reading whose stamp..." failed;
  GREEN 2/2.
- R10.6(2) manual row inside revision_days: tests/ingest/run.apiFlows.test.ts now runs it for both manual shapes
  (correction and cited disclosure): green.
- R10.6(3): `git diff --quiet -- tests/fixtures` = unchanged; tests/agent/context.test.ts and
  disclosure.e2e.test.ts pass unchanged in expectations (only their seeding calls changed).
- R10.6(1): grep of SQL text: no observations reader selects/inserts `source` in src or tools (except origin-check.ts,
  which reads it on purpose on a pre-0006 copy, and tools/import-sqlite, which writes a 0005 schema).

## Suite
- Full: `npx vitest run --maxWorkers=2`: 135 files, 1601 tests passed, 0 failed, 0 skipped (85 s; no load timeouts).
- `npm run typecheck`: 0 errors. `npm run lint:promises`: clean. `npm run build`: copies 6 migrations.
- `/usr/bin/python3 -m unittest` in tools/phase2-proof: 77 OK.
- No asset YAML changed: no hash pin moved.

## Concerns / for the controller
1. Ambiguous shape (R10.2): run.ts stamps a derivation over a first-party or contract-state ADAPTER flow `api`, but
   its provenance (derived, rung derived) equals a derivation over transfer scans (`onchain`). No asset config has one
   (all 4 derived metrics read transfer_flow; prod has none), so originOf maps derived/derived -> onchain and the guard
   REFUSES such a reading (origin_mismatch) rather than storing it mislabelled. A future config doing this needs a
   ruling (e.g. a formula/locator marker, or define derived = onchain). Not NEEDS_CONTEXT because no existing or
   stored row hits it.
2. `latest_levels.source` kept (see above): R10.1 left it conditional; dropping it changes the levels snapshot body.
3. Retired `db backfill-provenance` (and its tests, 310 lines) and `data set --source`: any external script that
   passes `--source` now gets "unknown option". None in the repo; check Raymond's profile scripts.
4. The `unloaded` config-hash fallback in confirm (`by.configHash`) is now unreachable (every row has provenance); left
   in place, its tests rewritten to assert the row keeps its own hash.
5. `checks`/report `basis: 'config'` fallback for unbackfilled windows is now unreachable; code left, test rewritten
   (a pre-0006 insert is refused).

## Rollout items (outside the repo / controller)
- Prod-copy proof (R10.5): prod_copy.py, then origin-check.ts (expect 27,533/27,533), then new dist
  `db migrate --breaking`, then `report yield <a> --day D --json` old vs new for all 13 assets.
- Any profile script calling `orion data set --source` or `db backfill-provenance` must drop it (none found in-repo).
- Release as its own `-- breaking` tag after R0 CAKE reaches prod; deploy.sh stage/prod `--breaking` per deploy.md.

## Fix round 1 (commit cc59fa7 on 0bd7a40)

Status: DONE_WITH_CONCERNS. 23 files (1 new test file, src/provenance/configHash.ts deleted). Not pushed/merged/tagged.

- I-1 / R10.7 refined: `src/ingest/run.ts` drops only the derived branch of `originMismatch`; the level and schedule
  guard stays. The derived writer merges `input_origin: "api"` into the `fetchedProvenance` locator only when
  `apiInputs > 0` (`withInputOrigin`), so the 4 existing derived metrics' provenance is unchanged; the mixed
  api/onchain refusal stays. `originOf(derived)`: `manual_*` -> manual; `locator.input_origin === 'api'` -> api;
  third_party rung -> api (kept); else onchain. `SERIES_ORIGIN` ('api') exported from origin.ts and used by
  writeApiFlow (stamp, own-rows filter, own origin for conflicts) and writePeriodicPayments.
- Registry test `tests/provenance/adapterOrigins.test.ts`: one fake read per registered adapter (key set == adapterNames()),
  writer stamp (level/schedule `source`; daily_series/periodic_payments SERIES_ORIGIN; monthly_series none) must equal
  `originOf(measured, ADAPTER_SOURCE_TYPES[name], {adapter})`; a contract-state adapter must be in ADAPTER_ORIGINS; in-test
  flips (solana.supply_burn_daily -> onchain, chain.view_sum -> api) and a deletion are detected.
- M-1: README runs `"$WT/node_modules/.bin/tsx"`. M-2: ADAPTER_ORIGINS = contract-state adapters + retired aero.* only
  (key test updated). M-3: deploy.md remedies per count (levels_null: list rows; active -> `job run-now levels`; paused ->
  resume, levels, re-pause; missing asset / dropped metric -> `job run-now retention`). M-4: confirm's `by.configHash` /
  `unloaded` branch and `src/provenance/configHash.ts` deleted (callers pass `{ approvedBy }`); income statement's per-day
  unmapped/null-method fallback deleted (`basisObservations = rowProv !== undefined`; DayProvenance method/label non-null);
  the rewritten provenance.test "window row without provenance" test deleted. Followups note updated.

RED / GREEN
- RED: origin.test "derived over an adapter series" expected 'onchain' to be 'api'; ADAPTER_ORIGINS key test (25 vs 13
  keys); derived.test (a) source derived:flow_annualized not ok (origin_mismatch); adapterOrigins: SERIES_ORIGIN missing,
  5 series adapters "stamps undefined"; with origin.ts's solana.supply_burn_daily flipped to 'onchain' the registry test
  fails "solana.supply_burn_daily: stamps api, reads back onchain"; confirm `{ approvedBy }` calls: 5 TS2741 errors;
  incomeStatement "loader's provenance ... basis observations": received 'config'.
- GREEN: targeted 49 files / 725 tests; full `npx vitest run --maxWorkers=2`: 136 files / 1609 tests passed, 0 failed,
  0 skipped (85.6 s); typecheck, lint:promises clean; harness unittest 77 OK. `git diff --quiet -- tests/fixtures assets`.

Deviation / concerns
- M-4 report: `basis: 'config'` is NOT fully deleted. It is still the path for a pure input without `provenance`
  (`yieldReport`/`incomeStatementV2` called directly: all synthetic report unit tests, e.g. the sources-label tests).
  Only the unreachable part (a loader input with an unmapped / null-method day) is gone. The loader always passes
  provenance and every day `dayRows`/`periodicDaily` holds has an entry in `provenanceByDay` (same filters), so v2 JSON
  is unchanged; the controller's prod-copy cmp is the proof.
- (b) of the ruling is pinned on burn_momentum over a transfer flow: locator equals the configured one, no input_origin.
- Derived over DefiLlama now also gets `input_origin: "api"` (apiInputs > 0); still 'api' either way. No prod row is that shape.
