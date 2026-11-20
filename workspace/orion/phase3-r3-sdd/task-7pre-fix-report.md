# Fix wave before Task 7: R15 + Task 5 M2 tests + R3 scripts/docs

Status: DONE. BASE 14f521a. One commit:
`ca3be1d fix(data): rebuild targets only CoinGecko and old-locator rows; disclosure rows kept (R15); Task 5 test gaps`.

## What

1. **R15 in `src/db/supplyLevels.ts`.** Classification of each active circulating row:
   - current source by R12's (source_type, locator.adapter, locator.call) comparison -> `unchanged` (as before);
   - else source_type in {`market_data`, `contract_state`} -> target (CoinGecko rows; the wrappers' old erc20_supply
     rows: contract_state, call `totalSupply()`, no adapter, vs current `chain.view_sum`, found by R12's comparison);
   - else (disclosure, hand-entered, any other rung) -> new `kept: { id, observedAt, reason }[]`, never read or written.
     Reason: `a <source_type> row: only market_data and old-locator contract_state rows are rebuilt (Ruling R15)`.
   - `rows` = rebuilt + refused + notRebuildable (kept excluded). The purge is unchanged (it only targets market_data).
   - CLI (`src/cli/commands/data.ts`): summary line gains `; N kept;`, one `    KEPT #id observedAt: reason` line per
     kept row; JSON carries `kept`; command description mentions it. Exit code unaffected by kept rows.
2. **Task 5 review M2 tests** (tests/db/supplyLevels.test.ts):
   - (a) conflict: a refresh supersedes day 2's row right after its plan read (via a multicall hook). `--yes` throws
     `rebuild_conflict` naming `#id at <observedAt> is no longer active`; day 1 stays committed, day 2 rolled back
     (refresh row active, no contract_state row that day); lock released; a rerun rebuilds 1 row with
     `rebuilt.from_id` = the refresh row.
   - (b) interrupted `--yes`: a Db proxy fails the 2nd asset-locked tx (3 days). Day 1 written (+1 row), days 2-3 still
     CoinGecko; dry run then shows rows 2 / unchanged 1; rerun `--yes` rebuilds 2; a third dry run rebuilds 0 (unchanged 3).
   - (c) LIT-like view_sum + `locked_schedule` (500M, 36 x 1 month from 2027-01-29), chain to 2027-03-01: 2026-12-01 ->
     500,000,000 (36/36 locked); 2027-01-28T23:59:58Z whose block is 2027-01-29T00:00:00Z -> 35/36 (the block's time,
     not observed_at); 2027-02-10 -> 35/36 (1 of 36 out). Values exact, details asserted.
   - (d) PUMP-like `solana.supply_less_owners`: dry and `--yes` -> every row notRebuildable, calls 0, no RPC opened,
     values untouched.
   - R15: VVV-like (Base view_sum) with an active cited disclosure row at 2026-09-18 + 2 market_data rows: dry and
     `--yes` list the disclosure row as kept; it stays active with 48,350,000; both market_data rows rebuilt with exact
     values; a rerun is rows 0 / unchanged 2 / the same kept.
   - CLI (tests/cli/supplyLevels.cli.test.ts): KEPT line text, JSON kept, the disclosure row untouched after `--yes`.
3. **Scripts/docs.**
   - `tools/phase3-proof/r3_check.py`: `classify` splits out `kept` (non-current rows whose source_type is neither
     market_data nor contract_state); step 1 (`expected`) records `kept` / `keptKinds` per asset and prints
     `kept (never a rebuild target, ruling R15; untouched): vvv disclosure=1` instead of stopping; `stale` (pre, rebuilt,
     purged) STOPs when an asset's kept count differs from step 1's; `rebuild_counts` includes `len(kept)` (STOP when a
     result has no `kept` list, i.e. a pre-R15 binary), so rebuild-dry / rebuild-again / same-rebuild compare it with
     step 1's. Nothing hard-coded: the count comes only from step 1's sql-ro rows.
   - r3-s0.sh / r3-s2.sh: step labels mention kept (R15).
   - fixtures/r3/generate.py: VVV disclosure row (kind '', active 1) in every supply state; `kept` in every rebuild result
     (vvv's 1 entry); new overlays `stop-kept-unrecorded` (s2 step 5 sees vvv disclosure 2) and `stop-kept-rebuild`
     (cake's dry run keeps a row step 1 did not record). Fixtures regenerated.
   - test_r3_scripts.py: happy s0 asserts kept {vvv: 1} and the printed line, vvv rebuilt 57; s2/s3 assert the kept
     suffix and per-asset `kept` in dry lines; two new STOP tests (no rebuild call / no `--yes` made).
   - docs/ops/deploy.md R3 block: artifacts table gains the kept row (vvv 1 on prod, measured); the "unlisted kind"
     paragraph now covers only market_data/contract_state rows of an unknown locator; steps 1, 5, 6 describe kept.
   - Followups note: the VVV open item is struck through and marked resolved by R15; R15 added to the rulings list.

## Tests (RED -> GREEN)
- supplyLevels.test.ts RED (before the src change): `5 failed | 11 passed (16)` — the 3 existing exact-shape tests and the
  VVV and PUMP tests (no `kept` key). The conflict, interrupt and LIT tests passed on the existing code (coverage of
  existing behaviour, as M2 asked). Mutation check: disabling the in-tx `rebuild_conflict` re-check fails the conflict
  test; making locked_schedule use `ctx.nowIso` instead of the block timestamp fails the LIT test (both reverted).
  GREEN 16/16.
- CLI RED with data.ts stashed: `2 failed | 1 passed (3)`; GREEN 3/3.
- Python RED (before generate.py): `Ran 19 tests ... FAILED (failures=4, errors=2)`; GREEN
  `python3 -m unittest tools/phase3-proof/test_r3_scripts.py tools/phase3-proof/test_flatdiff.py`: Ran 65, OK (was 63).
- orion-remote `python3 -m unittest scripts/provision/test/test_orion_remote.py`: OK (67, unchanged).
- Full `npx vitest run --maxWorkers=2` (twice, the second after a test-only type fix): 2030/2031 passed (156 files). The one
  failure is the known environmental `tests/db/daemonSchema.test.ts > 0002_daemon > schema: every 0002 table exists in
  schema orion` (leftover probe schema r3probe_1795204385 in orion_test). `npm run typecheck`: clean.
- No asset YAML touched; no hash pin moved.

## Self-review / concerns
- The contract_state rule keeps R12's comparison: any contract_state row not of the current (adapter, call) is a target,
  not only the exact `totalSupply()`/no-adapter shape. On the shipped data that is exactly the wrappers' old rows. The
  stage scripts stay stricter: a contract_state row of another kind on a non-wrapper is still an unlisted STOP.
- A `first_party_api` (or other non-target rung) row of an old source on HYPE would now be kept, not notRebuildable; none
  exists per Task 6's artifacts.
- The spec's Status line still says "Rulings R1-R14" (not in this task's file list; left).
- Task 5 M5 (NOT REBUILDABLE line wording) is still deferred.
- Files: src/db/supplyLevels.ts, src/cli/commands/data.ts, tests/db/supplyLevels.test.ts,
  tests/cli/supplyLevels.cli.test.ts, tools/phase3-proof/{r3_check.py, r3-s0.sh, r3-s2.sh, test_r3_scripts.py,
  fixtures/r3/**}, docs/ops/deploy.md, docs/superpowers/notes/2026-11-19-orion-phase3-r3-followups.md. No network, ssh,
  live DB or .env; node_modules not staged.
