# Final fix wave report (BASE f46f615)

Commit: 67e28f5 `docs/tools: R3 final review fixes (AERO 44+1, HYPE/PUMP null at D, soak grep, s3 withoutReplacement, LIT citation in register)`.
No src/ or assets/ change; no hash pin moved (tests/config, packGolden, v2Golden green).

## What

1. **R20 (AERO 44 + 1)**: plan N2, step 1 measured figures (aero 45 = 44 before 2026-11-10 + 1), step 6 (aero rebuilt 1
   = the 2026-11-10T00:45Z row; notRebuildable 44), step 7 (withoutReplacement 44); deploy.md table row (measured +
   cleared-by columns), steps 6 and 7; followups N2. Counts are still read from step 1. The happy fixture assumed 45
   notRebuildable: `generate.py` NR aero is now 44 (prod's split), so AERO's rebuild path (1 rebuilt) is exercised; the
   s2 `--resume` fixtures count aero's 1 row as done before cake (new `data_rebuild-supply-levels_aero.1` resume
   fixtures).
2. **R21 (HYPE/PUMP null at D)**: deploy.md prerequisite 1 and plan N4 class S: `marketCap`, `multiples.mcapTo*`,
   `perToken.*` become null at D after the purge; their class S entries are `"new": null` pins; table shows `-> null`;
   D-91 unchanged. Followups N4 line + an open item (two rows Mike hasn't seen: AERO's rebuilt row, HYPE/PUMP -> null).
3. **Minor 2 (soak)**: deploy.md and the plan name the real lines per `formatWatchPost` (`ORION WATCH <SYM>: <metric>
   <rule> <value>`, no env): `ORION WATCH CRV: circulating_gap_curve outside ...`, `ORION WATCH LINK:
   circulating_gap_chainlink outside ...` (nightly body), `ORION WATCH PUMP: reserved_balance change_pct ...` (hourly).
4. **Minor 3**: followups gain R19, the f46f615 Task 7 Step 1 line, R20, R21 and a line for this wave; spec Status says
   R1-R21 and records f46f615.
5. **Minor 5**: `supply` query gains `before_rebuild_from_all` (every status); step 1 records
   `mdWithoutReplacementAll` (HYPE/PUMP: market_data total; AERO: all-status rows before rebuild_from); `purge-dry` and
   `purge-dry-resume` compare against it (an expected.json without it, or supply rows without the column, is a STOP).
   `mdWithoutReplacement` (active) still drives s2's post-rebuild stale check. s0 prints `withoutReplacement N` per
   notRebuildable asset. New overlay `fixtures/r3/superseded-md` (one superseded md row on hype and one on aero before
   rebuild_from) + test `test_s3_counts_superseded_market_data_rows_of_the_not_rebuildable_set`.
6. **LIT citation in the register**: `ADAPTER_ENDPOINTS['chain.view_sum']` adds `locked_schedule.citation` (string) as an
   http endpoint; x.com row now reads `lit: adapter chain.view_sum, adapter schedule.unlocks_next_year`, note updated;
   docs/ops/sources-register.md regenerated (`--check` exit 0). New test in tests/tools/sourcesRegister.test.ts.
   Followups deferred item struck through.

## Tests (RED / GREEN)

- Python RED (after fixture/test change, before r3_check.py): 86 run, 2 errors (`KeyError: 'mdWithoutReplacementAll'`).
  Behavioural RED with the old r3_check.py on the superseded overlay: s3 `STOP: aero purge dry run
  observations/withoutReplacement (46, 45), expected from step 1 (46, 44)`.
- Python GREEN: `python3 -m unittest discover -s tools/phase3-proof`: 86 OK (85 + 1). `bash -n r3-s3.sh` OK.
- vitest RED: sourcesRegister 1 failed / 6 passed (view_sum returned only the RPC). GREEN: 7/7.
- Focused (sourcesRegister, scheduleUnlocks, tests/config, v2Golden): 12 files, 296/296.
- Full `npx vitest run --maxWorkers=2`: 2031/2032 (156 files); the 1 = tests/db/daemonSchema.test.ts "every 0002 table
  exists in schema orion" -> the controller's leftover probe schema `r3probe_1795204385` (known env, as in earlier
  waves).
- `npm run typecheck`: clean.

## Concerns

- Superseded market_data rows on a REBUILDABLE asset (or AERO on/after rebuild_from) are still not covered: the rebuild
  targets active rows only, so such a row is replaced only if an active non-market_data row shares its observed_at;
  otherwise the purge refuses (`purge_unreplaced_supply_level`) and s3 STOPs (fail closed). Prod has 0 superseded rows
  (2026-11-19), so not hit; out of this wave's scope.
- The 2026-11-10T00:45Z AERO rebuilt value (~700M) is still unseen by Mike; listed as a followups open item for the
  Task 7 table.
