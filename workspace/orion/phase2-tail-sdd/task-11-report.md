# Task 11 report (gate G4): v1 retired

Status: DONE_WITH_CONCERNS (concerns at the end).

## Commits (feat/phase2-tail, on cc59fa7)
- A `2f5bc8d` feat(config)!: holder_flows and reporting retired; eligibility and the agent pack read income_statement (Task 11a) — attempt 1, committed before this continuation.
- B `b48c3cf` feat(report)!: v1 report retired; --legacy removed (Task 11b) — attempt 1's uncommitted work kept as found, finished per R11.8, committed here.

## A (11a), summary
- `holder_flows` / `reporting` deleted from src/config/schema.ts (strict: refused by name at load, filing, approve; tests in tests/config/load.test.ts, tests/app/proposals.test.ts, tests/config/edit.test.ts). Removed from the 13 asset YAMLs; templates updated.
- src/app/eligibility.ts and src/agent/context.ts read income_statement; pack flow set = holders + below-line-to-holders, pinned against cc59fa7 (tests/agent/packGolden.test.ts + golden/packs-13.json: 13 packs byte-identical).
- v2 JSON golden for 13 assets x 5 inputs written at cc59fa7 (tests/report/v2Golden.test.ts), byte-identical after A and after B.
- All 13 hash pins re-pinned (parsed config changed for every asset), incl. LIT_HASH in disclosure e2e.
- R11.3: tests/ingest/originGuard.test.ts "refuses schedule steps stamped onchain on a first_party_api rung (origin_mismatch), and writes no step" (in A).
- R11.7 fixture edits: tests/fixtures/hype.yaml and aero.yaml lose `holder_flows`; tests/fixtures/disclosure/lit-q3-run.json edit path `reporting.dilution` -> `income_statement.dilution`.
- R11.6: yCRV's default report day gated on the statement's flows (`yearn_styc_fee` dropped: no statement line reads it); other 12 pinned equal to cc59fa7. Controller verifies yCRV on a prod copy.

## B (11b), what it does
- `report yield`: no `--legacy` (commander refuses `unknown option '--legacy'`), no v1 key in JSON or text; src/report/legacy.ts deleted; `yieldReport` / `loadHolderYieldReport` lose the options arg.
- Tick `holder_yield` (src/app/tickReport.ts) reads only the statement (T4 M2): flows/yields/multiple/holder_flow_growth from `incomeStatement`; `revenue_annualized`, `revenue_growth_annualized`, `payout_ratio` optional (old job rows still parse). Statement threw (C4): header + empty flows + null yields + statement_error.
- Nightly Slack block (src/notify/format.ts): v2 rows print the statement block; a C4 row prints header+price (ALERT line says why); a pre-Task-4 row still prints the v1 block.
- Snapshot body v2 only; `SNAPSHOT_SCHEMA = orion.snapshot/2`; `KNOWN_SNAPSHOT_SCHEMAS` keeps accepting a queued `/1` envelope (tests/push/envelope.test.ts).
- T3/4 M-d: a cost line with no reading says so, not "a missing day" (tests/report/incomeStatement.test.ts). T4 M3: tests/cli/cli.test.ts text assertion rewritten.
- Harness (R11.2/R11.8): reports.sh runs both sides with identical flags (no `--help` probe, no `--legacy`), refuses `<out>`/homes outside `$TMPDIR` or an unset TMPDIR (T0 M4); compare.py v2-vs-v2 (rel 1e-12), header+maps for a v1-only old side, legacy check for a new side still printing v1, 13 NAMED assets required (`FAIL coverage`), `--json` (T0 M6). Tests: V2VsV2Test, V1OldSideTest, JsonOutputTest, coverage tests, ReportsTest identical-flags + every refusal path (T0 M7: bad D, missing dists, existing out, no .env, no DB url, different schemas, non-p2proof schema, 12 assets, outside TMPDIR x5, unset TMPDIR).
- Docs: tools/phase2-proof/README.md; docs/ops/deploy.md new section "Phase 2 tail: Task 11 release (v1 retired, gate G4)" with the release note "report yield prints v2 only; snapshot schema orion.snapshot/2; outbox still accepts /1 envelopes", plus the reference-run paragraph updated; followups note section "Task 11 (gate G4)" incl. R11.6 and the Phase 3 proof note (Phase 3 spec §7 compares `--legacy`: after this release compare v2 only).

## RED / GREEN
- TS RED (src changes stashed, B's tests run on A's src): 6 files failed, 12 tests failed / 113 passed (envelope /2 and /1 acceptance, tickReport T4 M2 and C4, nightly block, snapshot body, cli `--legacy` gone, M-d cost-line flag). GREEN: those files pass with B's src.
- Harness RED (HEAD reports.sh/compare.py with the new tests): 16 failures + 2 errors (v2-vs-v2, V1OldSide, --json, coverage, identical flags, TMPDIR confinement). GREEN: `cd tools/phase2-proof && /usr/bin/python3 -m unittest test_compare.py test_prod_copy.py` -> Ran 96 tests, OK.

## Full suite (on b48c3cf's tree, before commit; no other vitest running)
- `npx vitest run --maxWorkers=2`: 138 files passed, 1672 tests passed, 0 failed, 0 skipped (first run, no reruns needed).
- `npm run typecheck`: clean. `npm run lint:promises`: clean.
- No hash pin moved in B.

## v1-consumer sweep (git grep income., holderFlowGrowth, flows[, --legacy, legacy in src/ tools/ docs/ops/ scripts)
- Left on purpose: src/report/parity.ts + tools/phase2-proof/parity.json + write-parity.ts (v1 paths, read only against a v1-only old release); tools/import-sqlite/reports.ts (retired SQLite cutover proof; its `--legacy` probe is optional and finds none); docs/ops/postgres.md §172 (historical cutover proof text); `legacy` as a price basis (src/db/prices.ts, load.ts, incomeStatement.ts) is unrelated; incomeStatement.ts's internal `holderFlowGrowth` variable is the v2 holder-flow growth.
- Updated: docs/ops/deploy.md reference-run paragraph; tests/cli/cli.test.ts comment.
- deploy.md lines ~257 (Phase 2 release step 1) still describe the release-2 soak-script change; historical, left.

## Rollout items for the controller (outside the repo)
- ~/.hermes/profiles/raymond/scripts/orion-stage-soak.py: must not pass `--legacy` anywhere (now refused) and must read v2 fields only; its parity map scripts/orion-phase2-parity.json compares v1 vs v2 and becomes v2-vs-v2 once both envs run this release.
- Snapshot consumers (coinrevs site / anything reading masha256/orion-data{,-staging}): `full` bodies switch to orion.snapshot/2 without v1 keys.
- The 13 `orion-<asset>` paused cron fallback prompts (week-1 fallback on the old tree) read the old dist; unaffected unless resumed on a new dist.
- Controller proofs: v2 JSON byte-identical on a prod copy (reports.sh + compare.py --json, v2-vs-v2), yCRV default day on a prod copy = cc59fa7's (R11.6).

## Deviations
- reports.sh run.txt no longer has a `legacy=` line (nothing read it besides humans); compare.py reads only `day=`.
- reports.sh refusal tests live in test_compare.py's ReportsTest (where the reports.sh test already was).

## Concerns
- 11a's own RED evidence was produced by attempt 1 and is not re-shown here.
- The Phase 3 spec §7 text itself (on feat/phase3-third-party, another session's branch) still says `--legacy`; only the followups note records the change. The controller should tell that session.
