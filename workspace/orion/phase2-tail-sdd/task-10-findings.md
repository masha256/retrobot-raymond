# Task 10 review: 0bd7a40 on 0f4b2fe (0006 provenance NOT NULL, observations.source dropped, originOf)

**Spec verdict: PASS.** R10.1-R10.6, R10.2a and R10.8 are met. R10.7 is sound but incomplete as worded (I-1).
**Quality verdict: APPROVED WITH FIXES.** Fix I-1 in the R10.7 round. The minors can ride along.
Counts: Critical 0, Important 1, Minor 4.

Reproduced on a detached worktree `rev-t10` at 0bd7a40: `npx vitest run --maxWorkers=2` gave 135 files / 1601 tests
passed, 0 failed, 0 skipped. `npm run typecheck` and `npm run lint:promises` were clean. `tsx tools/phase2-proof/origin-check.ts`
run with an absolute path takes its main branch (it failed on the missing DB URL as expected, so the `import.meta.url`
guard works).

## Named risks: what I checked

1. **Readers of `observations.source`.**
   - I scanned every string and template literal in src/, tools/ and scripts/ that names `observations` or
     `latest_levels`, contains a SQL keyword and has a bare `source`. Only three hit:
     - `latestLevels.ts:42`: latest_levels keeps the column (R10.8).
     - `tools/import-sqlite/sqliteMigrations.ts`: the SQLite DDL.
     - `origin-check.ts:26`: reads the column on purpose, on a pre-0006 copy.
   - The `SELECT *` readers of observations (`observations.ts:179/186/200`) go through `fromRow`, which sets
     `source: originOfRow(r)`. The one hand-written SQL reader, `checks/evaluate.ts:170`, now selects the four origin
     columns and derives the value.
   - Every TS `.source` reader uses the computed `Observation.source`: `apiFlow.ts:76`, `flow.ts:104/108`,
     `tokenBackfill.ts:159/244`, `adapters/solana.ts:113`, `agent/describe.ts:12`, `agent/context.ts:65`, `evaluate.ts:185`.
   - No view depends on the column: the 0006 test reads `flow_usd_v` after the drop.
   - Baseline indexes don't include `source` (`0001:10-11`), so the drop removes no uniqueness.
   - **Clean.**
2. **originOf totality against the writer list.**
   - Writers checked:
     - run.ts levels: coingecko, contract_read, erc20_supply, http_json (first and third party), defillama_share,
       constant, every adapter.
     - run.ts schedules and derived rows.
     - `flow.ts:529` (log_scan), `apiFlow.ts:200` (defillama is third_party; the adapter series are first_party, plus
       `solana.supply_burn_daily` as contract_state mapped to api), `periodic.ts:73` (hype first_party).
     - `data set`, `proposals.ts:108`, `ledger.ts:240`, `confirmObservation` (copies the provisional row's provenance;
       a provisional row needs a citation, so it is always disclosure and maps to manual, the same as the old hard-coded
       'manual').
     - The pre-v2 backfill shapes: rule 2a (manual_*), 2b (legacy seed), 4 and 5.
   - Each adapter's stamp matches `ADAPTER_ORIGINS` (checked by grepping every `source:` stamp in src/ingest/adapters
     and src/ingest/sources).
   - The table test has the prod matrix plus a WRITERS table, and a totality test over methods × rungs.
   - The derived-over-api-adapter shape is the known gap. R10.7 handles it.
   - **OK.**
3. **Behaviour that depends on the origin is unchanged.**
   - These all read the computed field: manual-row protection (`apiFlow.ts:127-139`), conflicts and `--adopt`
     (`flow.ts:101-109`), the token-backfill skips, Solana's supply drop, the agent pack/describe/ledger, inbox, and the
     CLI JSON `source`.
   - The revision-window test runs both manual shapes (`run.apiFlows.test.ts:232`).
   - These are all empty: `git diff 0f4b2fe 0bd7a40 -- tests/fixtures`, `tests/agent/context.test.ts`, and migrations
     0001-0005.
   - The only expected-value change in tests is `cli.test.ts:158`. `data set ... --source onchain` used to store
     `onchain`; it now reports `manual`. This is the accepted R10.3 consequence: prod has no disclosure row with a
     non-manual stored source, per the controller's matrix.
4. **Migration 0006.**
   - The first line is exactly `-- breaking`, and the migrator detects it (`migrate.ts:43`).
   - NOT NULL is on method, source_type, locator, code_version and config_hash. Every writer sets these through the
     required `Provenance` (`observations.ts:228-245`). Chain, blocks, formula, inputs and citation stay nullable, and
     the test checks that.
   - latest_levels source_type and locator are set by the only writer, `toLatestLevels`, which now throws rather than
     writing null (`levels.ts:87-93`).
   - The CHECK has the pre-v2 exemption. Every new disclosed writer requires a citation (`disclosedProvenance`, the
     ledger, approve), and confirm keeps the citation.
   - Without `--breaking`:
     - the migrator refuses (`migrate.ts:106`, tested);
     - `orion-remote switch` refuses before drain (`orion-remote:915-918`);
     - `deploy.sh` passes `--breaking` through (`deploy.sh:170`);
     - `rollback` refuses when the last switch has `breaking=1` (`orion-remote:971-975`).
   - A later non-breaking release can only roll back to the 0006 release, never past it.
   - The deploy.md "Phase 2 tail" section matches this, and its pre-check also covers `disclosure_uncited` and
     `levels_null`.
5. **Retired commands.**
   - `db backfill-provenance` and `src/provenance/backfill.ts` are gone. Every remaining mention is history in
     docs/plans/notes, the deploy.md release-2 step (marked "release 2 only"), the 0004 SQL comment, or the
     importer/postgres.md note telling you to use a release-2 build.
   - `data set --source` is gone. No caller remains in src/, tools/, scripts/ or docs/ops.
   - Read-only grep of `~/.hermes/profiles/raymond/scripts`: no `backfill-provenance` or `--source`. The disclosure
     watcher passes `doc add --source-id`, a different command.
   - **Clean.**

## Important

**I-1. R10.7 removes the whole `origin_mismatch` guard, but only its derived branch is the problem**
(`src/ingest/run.ts:336-340` and `:360` levels/schedules, `:521-526` derived).
- The level/schedule branch is the only runtime check that a reading's stamp matches what `originOf` will read back,
  that is, that the `ADAPTER_ORIGINS` value and the rung are right.
- `tests/provenance/origin.test.ts` ("every registered adapter declares...") checks only the key set, not the values.
- The series writers (`apiFlow.ts:200`, `periodic.ts:73`) have no check at all.
- Failure if a new contract_state adapter that returns a series is left at, or declared, `'onchain'`:
  - its rows read back as onchain;
  - `storedApiDays` (`apiFlow.ts:76`, `o.source === 'api'`) no longer sees them;
  - `findFlowConflicts(..., own='api')` (`flow.ts:104`) lists the writer's own rows as foreign conflicts;
  - so the next run writes nothing ("nothing was written: ... not manual rows") and the asset's revenue stalls;
  - `tokenBackfill.ts:159` skips them too.
- Before 0006 the stored column was the stamp, so this could not happen.
- Fix (amend R10.7):
  - Drop only the derived branch, which is replaced by `input_origin`. Keep the level/schedule guard.
  - Add a registry test: every adapter whose rung is `contract_state` and which returns a series (`writeApiFlow`
    stamps `api`) must be `'api'` in ADAPTER_ORIGINS, and every level adapter's declared value must equal its stamp
    (run each adapter against `fakeRpc` / `fakeHttp` and compare `result.source` with `originOf(fetchedProvenance(...))`).
- Test shape: register a contract_state series adapter declared `'onchain'`, fetch twice, and assert the second run
  writes and reports no conflicts. Today that would pass only by luck.

R10.7 judgement:
- **Sound.** The writer's existing `apiInputs > 0` test (config-based: defillama | adapter inputs) is exactly the old
  stamp. Every prod derived row has no `input_origin` and maps to onchain, so origin-check stays 27,533/27,533.
- **Incomplete in three details**, which the fix round should state:
  - (a) I-1 above.
  - (b) Keep the `third_party` fallback: `input_origin ?? (sourceType === 'third_party' ? 'api' : 'onchain')`.
    Otherwise the WRITERS shape "derived over defillama" without the key changes meaning, and a pre-fix row of that
    shape would flip. Prod has none, but the table test pins it.
  - (c) Write `input_origin` only when it is `'api'`, merged into `locatorOfSource`'s locator. `fetchedProvenance`'s
    `extra.locator` replaces the whole locator, so the writer must spread it. Then the 4 existing derived metrics'
    provenance is byte-identical (R10.5), and the mixed api/onchain refusal (`run.ts:518`) stays.
  - Also: the wording "inputs include an api-origin row" should say "an input metric sourced from defillama or an
    adapter" (the config test), since that is what reproduces the old column.

## Minor

- **M-1** `tools/phase2-proof/README.md:49` runs `npx tsx "$WT/tools/phase2-proof/origin-check.ts"` from `$P/new`.
  `$P/new` has no node_modules, so npx resolves tsx from the cwd and may try to install it from the registry (no
  network on proof hosts), and the proof step fails or hangs. Use `"$WT/node_modules/.bin/tsx"`, or run from `$WT`
  with the env vars inline.
- **M-2** `src/provenance/origin.ts:27-59` vs `:78-81`. `ADAPTER_ORIGINS` is consulted only for `contract_state`.
  Its `api` entries for the first_party_api and third_party adapters (hype.*, lit.*, vvv.*_api) are inert:
  changing one to `'onchain'` has no effect, though the doc says "a new adapter has to say". Either consult it for
  every measured adapter row (and assert the value against the rung in the test), or mark those entries as
  documentation only.
- **M-3** `docs/ops/deploy.md:337-341`, pre-check. On `levels_null > 0` it says "find the writer first". A null
  latest_levels row has no writer: it is a row not rewritten since 0004 (e.g. an asset that was paused, which the
  hourly read doesn't refresh). Give the remedy: resume the asset and let one hourly levels read run (or
  `job run-now levels`), or let retention prune a metric the YAML dropped. Then re-check.
- **M-4** Fallbacks left unreachable by 0006 (reported by the implementer):
  - `confirmObservation`'s `disclosedProvenance(by.configHash, ...)` branch and the `by.configHash` parameter
    (`src/db/observations.ts:290-299`);
  - the report/checks `basis: 'config'` path for unbackfilled windows.
  - Fine to keep for this release. List both in the followups note for removal with Task 11, so they don't read as
    live behaviour.


## Controller rulings (binding for Task 10 fix round 1)
- I-1 FIX, R10.7 refined: remove ONLY the derived-row branch of the origin_mismatch guard (run.ts ~521-526). Keep the level/schedule branch (run.ts ~336-340, ~360). The derived writer adds `input_origin: "api"` to the derived row's EXISTING locator object (merged, never replacing keys) only when run.ts's apiInputs > 0; originOf(derived) = 'manual' for formula manual_*, else locator.input_origin === 'api' ? 'api' : 'onchain'; keep the third_party -> api fallback wherever it exists today. Add the missing runtime/registry coverage: a test that for EVERY adapter in the registry ADAPTER_ORIGINS[name] equals the origin that adapter's writer stamps (series, level, schedule, periodic and apiFlow paths), so a mismatch fails CI instead of silently turning own rows into foreign conflicts. Tests first: (a) derived over an api-origin input writes and reads back 'api' (no refusal); (b) derived over onchain inputs reads 'onchain' and has no input_origin key; (c) the registry consistency test fails when one entry is flipped.
- M-1 FIX (README run line uses the worktree's node_modules / an absolute tsx path).
- M-2 FIX: ADAPTER_ORIGINS holds only entries originOf reads (contract_state adapters), or document in the file why others are kept; the consistency test covers what is kept.
- M-3 FIX (deploy.md levels_null remedy).
- M-4 FIX: delete the two unreachable fallbacks (confirm's by.configHash 'unloaded', report basis 'config') and their rewritten tests, if nothing else reads them.
Commit: "fix(provenance): derived rows carry input_origin; adapter origin registry checked; Task 10 review fixes". Report: append 'Fix round 1' to W/task-10-report.md.
