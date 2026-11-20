# FINAL whole-branch review: Phase 3 R3 (84cc9d2..f46f615, 11 commits)

Read-only. Ran (all pass): focused vitest at `--maxWorkers=1` over 38 files (v2Golden, sourcesRegister, supplyLevels,
purge, supplyLevels.cli, derived, tests/config, tests/levels, tests/assets, packGolden, proposals, adapters evm/hype/solana,
tests/provenance): 631/631. `npm run typecheck`: clean. `test_orion_remote.py`: 67 OK. `test_r3_scripts.py` +
`test_flatdiff.py`: 85 OK (HOME is sandboxed, so nothing was written to `~/r3-*`). Prod evidence: the scoping
`prod/circ_rows_all.json` (2026-11-19).

## Verdict: READY WITH FIXES

There is no Critical finding. Two Important findings must be settled before the Task 7 proof is signed, because they
change the counts and the allowlist Mike signs. Neither one is a code defect in the rebuild, the purge or the loader.
The code paths, the scripts' JSON contracts and the hourly/nightly behaviour all check out.

## Checks (pass/fail)

1. **Global constraints: PASS.**
   - No CoinGecko or DefiLlama read is added. `coingeckoIssues` (src/config/sources.ts:179) refuses every field. It
     runs at load (src/config/load.ts:60), which is also the filing and approve path (tests/app/proposals.test.ts +14;
     tests/config/sources.test.ts:190-197).
   - `coingeckoIds` returns [] for all 13 shipped assets, over both the levels keys and all metrics
     (tests/config/sources.test.ts:217-218), so `prefetchMarkets` makes no call (src/levels/levels.ts:114, 202).
   - The only remaining `api.coingecko.com` code is the R8-retained source type, and no config can reach it.
   - No migration and no `src/db/migrations` change. The scripts check that the schema max is 8 (r3_check.py c_migrations).
   - Rollback to orion-2026.11.15.1 is plausible on this data, but no test exercises it:
     - Old `originOf` defaults unknown adapters to onchain (84cc9d2 origin.ts:81).
     - Old retention deletes latest_levels/watch_state rows for unconfigured metrics (`reserved_balance`).
     - Rebuilt rows are ordinary `contract_state` rows.
     - deploy.md documents that the old release writes CoinGecko rows again.
2. **Value discipline: PASS.**
   - No file under src/report changed.
   - circulating feeds only the header `marketCap` (holderYield.ts:234), `multiples.mcapTo*` (incomeStatement.ts:847-852)
     and `perToken.*`/`circulatingSupply` (incomeStatement.ts:855, 1015).
   - Yields, `perTokenFdv` and dilution are on the total-supply basis.
   - circulating is `critical` on no asset, so no grade path reads it.
   - The golden `tests/report/golden/v2-report-13.json` is unchanged on the branch, and v2Golden passes against the new YAMLs.
   - The only golden move is packs-13.json paramsDoc (R8).
3. **Integration: PASS**, with Important 1 below.
   - The rebuild runs the configured handler with `ctx.block` = firstBlockAtOrAfter (supplyLevels.ts:206-232).
   - view_sum reads `times` and every term in one multicall at that block. `locked_schedule` uses `block.timestamp`
     (evm.ts viewSum).
   - viem `allowFailure` multicall turns a codeless call (`0x`) into a failure, so the result is refused, never a
     partial sum (viemRpc.ts:78-95).
   - CRV `curve_circulating` (contract_read) and the gap metrics are never targets: only `circulating_supply` is.
   - `supplyNotRebuildable` is shared by the rebuild and the purge (purge.ts:376).
   - Scripts vs real shapes:
     - `SupplyRebuildResult` fields used are rows/rebuilt/refused/notRebuildable/kept/applied.
     - `PurgeResult.perMetric[0].{metric,observations,withoutReplacement}`, exportFile and exportSha256.
     - `Job` fields used are kind/releaseTag/startedAt/status/result.failed/lastError, and `LevelsJobResult.failed`.
     - The guarded `{error:{code,message}}` shape is handled.
     - orion-remote appends `--json` to jobs/report/purge/rebuild (orion-remote:442-484), and usage exit 64 exists.
   - The purge `observations` count includes superseded rows. That matches step 1's `total`. On prod all 428 rows are
     active, so active == total.
4. **Hourly/nightly behaviour: PASS.**
   - Hourly (levels job: unwatched monitor-only and derived metrics are excluded):
     - 10 view_sum assets: one multicall each at the levels block (LINK is one eth_call with 34 terms). The wrappers'
       call count is unchanged. The 9 CoinGecko calls (1 batched `/coins/markets`) are gone.
     - HYPE: +4 POSTs (2 wallets x spotClearinghouseState + delegatorSummary). spotMeta is shared through withRunCache.
     - PUMP: getTokenSupply + 6 getTokenAccountsByOwner. `reserved_balance` (watched, hourly) hits the run cache, so it
       adds 0.
   - Nightly only: CRV `curve_circulating` (contract_read) and LINK `supply.chain.link` (1 GET), plus the two
     `level_gap_pct` rows.
   - A failing circulating source never degrades a grade (non-critical). The report keeps the last stored row (14 d
     staleness), and 3 failed attempts give an advisory `source_failure_streak`.
   - Gap breaches surface only as `ORION WATCH <SYM>: circulating_gap_* outside ...` in the nightly report body
     (format.ts:154 via tick.ts:74). The derived gap is not in latest_levels/watch_state. PUMP `reserved_balance`
     posts from the hourly job. None of these is an anomaly.
   - R14 (run.ts:699-708): only the sides of a watched gap leave the exemption. LINK's `supply.chain.link` failing 3
     nights gives an advisory streak anomaly. That is by design, and the anomaly can start a triage run.
   - LIT and PUMP watched reads stay silent, as recorded in the followups open item.
5. **Deferred minors:** triage below.
6. **Docs: PASS with minors.**
   - The deploy.md R3 block and verb table are complete.
   - The sources register is current: `registerIsCurrent` passes, the CoinGecko row is gone, and supply.chain.link
     is added.
   - The followups note and spec Status lag one ruling (Minor 3). The soak grep wording is off (Minor 2).

## Critical

None.

## Important

1. **AERO is "45 notRebuildable" in the docs, but the code makes it 44 + 1 rebuilt.**
   - Prod's last AERO CoinGecko row is observed at `2026-11-10T00:45:09Z` (scoping prod/circ_rows_all.json). Its
     first `contract_state` row is at 03:31Z.
   - `supplyNotRebuildable` uses `observed_at < 2026-11-10T00:00Z` (src/db/supplyLevels.ts:93-97, assets/aero.yaml
     `rebuild_from: 2026-11-10`), and so does r3_check's `before_rebuild_from` (r3_check.py:66).
   - So the scripts will expect, and the code will give, AERO rebuilt 1, notRebuildable 44, withoutReplacement 44.
   - Plan N2/Task 6 (plan:75, 282, 290), deploy.md:1094, 1131, 1138 and followups:42 all say 45. Mike's N2 text was
     "AERO pre-11-10 purged".
   - The rebuilt value at the 00:45Z block (~700M+, mid upgrade-wave; scoping cake-vvv-aero.md §6: 11-09 = 690.2M)
     will replace CoinGecko's ~305M. That is consistent with the 03:31Z on-chain row, but it is a value Mike has not
     seen.
   - Fix before signing, either way:
     - (a) accept 44 + 1: update deploy.md (table and steps 6-7), the followups N2 line, and put the row in the Task 7
       table; or
     - (b) set `rebuild_from: 2026-11-11`: AERO hash re-pin; every 11-10 contract_state row is untouched (not a
       target), and REBUILD_FROM in r3_check.py must follow.
   - This doesn't block the scripts, which are self-consistent, but the signed counts must match what runs.
2. **HYPE/PUMP class S paths at D become null, and a `ratio` pin cannot hold them.**
   - D = today-2, and the report's as-of is the end of D+1. After s3 purges every HYPE/PUMP circulating row, both
     assets have no row at or before the as-of. The first new-source observation is the first nightly after the
     deploy.
   - So `marketCap`, `multiples.mcapTo*` and `perToken.{...,circulatingSupply}` go from number to null in the D report
     (N2: "market cap starts on the release day").
   - Plan N4 / deploy.md prerequisite 1 say class S = `ratio` on "the 12 changed assets". flatdiff fails a bounded
     entry whose value turns null (README "a bounded path that turns null fails"; flatdiff.py entry_holds).
   - Task 7 must write HYPE/PUMP class S as value pins (`"new": null`; no bound), and the signed table must show
     `-> null` for them. Otherwise s4 STOPs on stage. This is a Task 7 / allowlist design point, not a code change.
   - AERO "no entry" is still right: its D row is the 11-10+ contract_state row, and its D-91 has no circulating row
     on either side.

## Minor

1. Task 7 must check the archive RPC on each env: a BNB endpoint that prunes state would refuse every CAKE row, and the
   STOP that follows is correct. With non-midnight `observed_at` (most prod rows are 00:45Z / 12:xxZ), the day_blocks
   cache rarely applies. Expect one block search per row and dry + `--yes` = 2x the reads, and record both in the
   Task 7 table.
2. deploy.md soak (around line 1160) says "no `ORION WATCH stage ... circulating` line". The real lines are
   `ORION WATCH <SYM>: <metric> ...` (src/notify/format.ts:67): they carry no env, and PUMP's metric is
   `reserved_balance`, not "circulating". Name the three metrics exactly.
3. The followups note and spec Status (spec:10-16) stop at R18. R19 (closing-fix concerns) and f46f615 (flatdiff
   `ratio`, Task 7 Step 1) are not recorded.
4. The prod figures in the deploy.md section 7 table are the 2026-11-19 scoping counts. Task 7 should add the
   prod-copy counts and stage's s0 lines (the range-review note, still open).
5. The s3 purge-dry `withoutReplacement` check compares with step 1's active count (`mdWithoutReplacement`), but the
   purge lists superseded rows too. It is exact on prod today (0 superseded), but it would STOP if a superseded
   HYPE/PUMP/AERO market_data row appeared. Use `total` for the never-rebuildable assets.

## Deferred `minor (deferred)` triage (progress.md)

| # | item | before release? |
|---|---|---|
| T1-3 | solana.ts pump.fun regex duplicated, plain Error | wait (the R8 cleanup; behaviour correct) |
| T1-3 | `isName` x3 | wait |
| T1-3 | hype detail prints exponent form | wait (detail text only) |
| T1-3 | solana supply vs owner balances at different slots | wait (detail records both slots; in-flight transfers are small vs 403B) |
| T1-3 | `locked_schedule` citation URL not in sources register | **fix with the doc fixes before the tag** (cheap, register completeness: x.com row lists only `schedule.unlocks_next_year`); does not block the proof |
| T1-3 | view_sum + locked_schedule accepts exactly 0 | wait (LIT far from 0) |
| T4 | ownersBalance resolves before validating | wait (load-time check covers it) |
| T4 | schema.ts imports ingest layer | wait |
| T5 | rebuild day_blocks without 3600 s age check | wait (past days only) |
| T5 | (tests: conflict, partial --yes, LIT old block, PUMP) | done in ca3be1d |
| T5 | RPC counter counts 7 named methods | wait (they are every method on RpcTransport the rebuild uses; Task 7's count is accurate for EVM) |
| T5 | planRebuild unused `opts` | wait |
| T5 | CLI NOT REBUILDABLE line says purge deletes it | wait (true on shipped data: every notRebuildable row is market_data) |

None of the deferred minors has to be fixed before the release. The register citation is recommended alongside
Minors 2-3.

## Before the prod-copy proof

- Settle Important 1, (a) or (b), and align the docs.
- Write the allowlist per Important 2.
- Optional, same docs commit: Minors 2, 3 and 5, and the register citation.
