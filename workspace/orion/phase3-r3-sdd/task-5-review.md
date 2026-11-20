# Task 5 review: `data rebuild-supply-levels` + unreplaced circulating purge refusal (176c45a on 596245b)

### Spec Compliance

- ✅ Spec compliant. Every Task 5 interface item, R5/R6/R12/R13 and Review Focus 1/5 are in the diff (file:line below = diff line in review-596245b..176c45a.diff).
- ⚠️ Cannot verify from the diff: that prod's stored rows match the target rule. Prod CoinGecko rows are `market_data` (always targets). The wrappers' old rows need `call: 'totalSupply()'` and no `adapter` in their locator, which is the shape the test seeds (diff:1078). Task 7 step 6 dry runs (expected `refused` 0, notRebuildable = HYPE/PUMP/AERO 45) confirm this on a prod copy.

Named risks:

1. **PASS: R5 normal runner, block, value parity.** `getSourceHandler(def.source.type).fetch([request], ctx)` (diff:510-533) is the handler a fetch uses; there is no bespoke read. The block is `firstBlockAtOrAfter(rpc, ceil(ms/1000), anchor, latest)` (diff:519). Checked rpc.ts:111: `anchor` only seeds the estimate and the bracket starts at `lo=null, hi=latest`, so a previous-row anchor is safe. 00:00Z rows use day_blocks (diff:515-520), and day_blocks is "first block at or after 00:00Z" (dayBlocks.ts:5). view_sum's `locked_schedule` reads `block.timestamp` (evm.ts:254), so a rebuild at that block is a fetch at that block. The ctx matches the fetch ctx (run.ts:261) minus observations/chainHourPrices/priceDeps/backfillDays, which no circulating source uses. The URL rule and validateReading + onchain check match run.ts:231/421. Adapter errors become failed readings (sources/adapter.ts), so a revert is refused, not a crash.
2. **PASS: R12 classification.** I ran `supplyNotRebuildable` + `fetchedProvenance` over the 13 shipped assets (tsx, read-only):
   - All 11 EVM assets: `contract_state`, adapter `chain.view_sum`, no `call`, rebuildable.
   - HYPE (`hyperliquid:core`) and PUMP (`solana:mainnet`): notRebuildable at every date.
   - AERO: notRebuildable at 2026-10-01, rebuildable at 2026-11-15.

   So `market_data` rows and the old erc20 rows (call mismatch) are targets. Refused rows stay untouched with exit 3 (diff:171, 720-731). A second dry run and a second `--yes` rebuild 0 (diff:1066-1071).
3. **PASS: writes.** `withRunLock` on the asset (diff:567), one `db.tx` per UTC day with `lockAsset`, an in-tx `rebuild_conflict` re-check, and insertObservation supersede (diff:576-596). This mirrors priceLevels.ts:149-180 line for line. A rerun after an interrupted `--yes` treats committed rows as `unchanged` (same adapter) and redoes the rest. `day_blocks` puts are `ON CONFLICT DO NOTHING`. Provenance (diff:579-583):
   - method `measured`, rung `contract_state`, chain, config hash (fetchedProvenance)
   - `blockFrom/blockTo` = the read block
   - `codeVersion` = the release
   - `locator.rebuilt = {at, release?, from_id}`
   - originOf re-check before the write

   The test asserts every field (diff:1048-1054).
4. **PASS: purge.** `unreplacedSupplyLevels` refuses `purge_unreplaced_supply_level` for any unreplaced row that is not `supplyNotRebuildable` and returns the rest as `withoutReplacement` (diff:305-321). The predicate is the one the rebuild uses (diff:416-421, 490). The R38 refactor into `unreplacedRows` keeps the SQL, the filter, the error code and the message byte-identical (diff:262-297). Tests: CAKE refused on dry run and apply, then allowed after the rebuild (diff:1156-1181). HYPE is listed (diff:1183). AERO is split at rebuild_from (diff:1193). A superseded CoinGecko row counts (diff:780).
5. **PASS: orion-remote, schema, pin.**
   - The verb parses like rebuild-price-levels (diff:57-60), and the usage block says exit 3 (diff:45-49).
   - The refusal message lists the verb (diff:69). The deploy.md entry is there (diff:24-33).
   - Py tests cover passthrough, 11 refusals and the exit-3 passthrough (diff:90-110).
   - `rebuild_from` is optional with no default, round-trip checked (diff:192-195), and refused on non-level metrics (diff:203).
   - Only AERO's pin moved (diff:608-610, 741-743).

Checks I ran (Task 4 fixer's edit in tests/assets/pump.ingest.test.ts left alone):
- `vitest --maxWorkers=1` on tests/db/supplyLevels.test.ts, tests/db/purge.test.ts and tests/cli/supplyLevels.cli.test.ts: 34/34.
- `python3 -m unittest scripts/provision/test/test_orion_remote.py`: 67 OK.
- crv.yaml:65-71: every term calls `balanceOf` ON the token, so CRV has no refusal risk at old blocks (R13).

### Strengths
- R5 holds in practice: the rebuild calls the source registry, so view_sum, `times` and `locked_schedule` all come for free and parity with a fetch is structural.
- Write semantics are a faithful copy of rebuildPriceLevels, and the R38 refactor shares the unreplaced-row SQL without changing R38 behaviour.
- One predicate (`supplyNotRebuildable`) classifies rows for both rebuild and purge. When nothing is rebuildable, no RPC is opened (tested with a throwing factory, diff:968/1095).
- The tests assert exact values, blocks, provenance, day_blocks contents and row counts, not mocks.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)
- **M1, supplyLevels.ts (diff:520, 570): day_blocks finality.** Boundaries are cached with no finality guard. flow.ts:255 caches only when `found.timestamp <= latest - DAY_BLOCK_MIN_AGE_SEC` (3600 s). The cache is "first write wins, never rewritten" (dayBlocks.ts:5-7), so a reorged boundary under a 00:00Z row from the last hour would persist for every scan on that chain. Prod targets are hours to days old, so the risk is low. Fix: apply the same min-age check before `boundaries.set`.
- **M2, tests: untested branches.** No test covers `rebuild_conflict` (a row superseded between plan and tx), a partially committed `--yes` finished by a rerun, a `locked_schedule` source rebuilt at an old block (LIT), or PUMP/solana notRebuildable (only HYPE). The code paths are simple and mirror tested code, but risk 3's "finished by a rerun" rests on reasoning, not a test.
- **M3, supplyLevels.ts:437 (diff): call counting.** The `counting` Proxy whitelists 7 method names. A transport method added later would go uncounted. Counting every function prop except non-RPC helpers, or wrapping at the transport layer, avoids the drift.
- **M4, supplyLevels.ts (diff:465): unused parameter.** `planRebuild` takes `opts` but never uses it.
- **M5, data.ts (diff:137): CLI line.** The NOT REBUILDABLE line says the market_data purge "deletes it without replacement". That holds only for `market_data` rows. A notRebuildable row of another rung (e.g. a pre-rebuild_from contract_state row) would not be deleted by that purge. No shipped asset has one today.

### Assessment

**Task quality:** Approved

**Reasoning:** The rebuild reuses the fetch's handler and block, copies rebuildPriceLevels' lock/transaction/supersede pattern, and shares one predicate with the purge. All five named risks pass, the focused tests are green, and the remaining items are hardening and coverage polish.
