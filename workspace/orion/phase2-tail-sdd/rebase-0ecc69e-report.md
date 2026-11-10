# Rebase of feat/phase2-tail onto 0ecc69e (fix/cake-pending-burn), 2026-11-10

Status: DONE. No push. Postgres used: orion_test only.

## Old -> new shas (feat/phase2-tail, base 0f4b2fe -> 0ecc69e)
| commit | old | new |
|---|---|---|
| Task 10 (0006 breaking) | 0bd7a40 | 1ce53dc |
| Task 10 review fixes (release candidate) | cc59fa7 | 8422b4d |
| Task 11a | 2f5bc8d | 562fc05 |
| Task 11b | b48c3cf | d937281 |
| Task 11 review fixes | b360bc2 | 1de531d |

Trial branch tmp/rebase-trial (worktree .worktrees/rebase-trial) produced 5ec6e8c, 9127067, 1fe15af, 191b8c9, 6ca432b;
each real commit's tree equals its trial counterpart (`git diff` empty per pair), and `git diff tmp/rebase-trial HEAD`
was empty. Trial worktree and tmp branch removed afterwards.

## Conflicts and resolutions (only tests/assets/cake.ingest.test.ts)
1. At 2f5bc8d (11a): the hash pin. HEAD (0ecc69e) pinned 2d05a80b (CAKE fix, with holder_flows/reporting still in the
   parsed config); 11a pinned 79ac888b (retirement on the pre-fix YAML). Resolution: one pin = parse of the rebased
   assets/cake.yaml (auto-merged cleanly: CAKE fix's total_supply netting + no CoinGecko cross-check, and Task 11's
   retired blocks): **2f7d698f7f077e3769758dde049776f921dfd6381519892240fca3af98dd7a99**. Computed with
   `parseAssetYaml(...).hash` (src/config/load.ts at the rebased tree); the same script on 2f5bc8d's cake.yaml
   reproduces 79ac888b, so the method matches the test's. Comment lines record both re-pins. The rest of the CAKE fix's
   test edits (masterchef_v2/burner balances in the fake world, total_supply 335_120_997, cross-checks = price only)
   auto-merged with 11a's holderFlowMetrics/retired-key assertions.
2. At b48c3cf (11b): the report assertion block. 0ecc69e changed the v1 expectation's denominator to 335_120_997;
   11b moved the block to the v2 statement (`rep.dilution.supply`, `rep.revenue`, `rep.ratios`). Resolution: 11b's v2
   shape with the CAKE fix's 335_120_997.
CAKE test after each resolution: 7/7 passed.

## Goldens
Generator: the tip's tests/report/v2Golden.test.ts and tests/agent/packGolden.test.ts (first describe only;
`holderFlowMetrics` doesn't exist pre-11a) plus a v1 writer (`holderYieldReport(syntheticInput(repoAsset(id)))` for
ALL_ASSETS, `JSON.stringify(out, null, 1)+"\n"`), run with UPDATE_GOLDEN=1 in detached worktrees with each base's own
helpers.
- Validation at old cc59fa7: regenerated v2-report-13.json, packs-13.json, v1-report-13.json are byte-identical (cmp)
  to the committed files, so the generator is the one that wrote them.
- At rebased Task 10 (9127067 == 8422b4d's tree): all three regenerated files are byte-identical to the committed
  goldens. JSON diff old vs new: **no entry changed for any asset, CAKE included**. Reason: the goldens use synthetic
  report inputs and seeded pack rows; the CAKE fix changes only total_supply's source (subtract_balances) and drops a
  cross-check, which neither the report on a given input nor the pack (asset_config_yaml excluded) carries. No file
  contains `subtract_balances`/`pancakeswap-token`/`masterchef`.
- tests/app/golden/refresh-rows-orion-2026.11.09.1.json holds lit + aero rows only: not CAKE-dependent, untouched.
- Hence nothing amended into 562fc05 (the commit that introduced the goldens); docstrings ("golden at cc59fa7") stay true,
  and the files equal the rebased Task 10 output as well.

## Verification on the trial tip (6ca432b, tree = 1de531d)
- `npx vitest run --maxWorkers=2`: 138 files / 1677 tests passed, 0 failed, 0 skipped, first run (same count as b360bc2).
- `npm run typecheck`: clean. `npm run lint:promises`: exit 0.
- Harness `/usr/bin/python3 -m unittest` in tools/phase2-proof: 96 tests OK.

## Notes
- During the real rebase my first pass took the trial TIP's cake test at the 11a stop, which put 11b's assertions
  into 11a (tip identical, 11a not). Caught by the per-commit tree check; reset to b360bc2 and redid it taking each
  stop's file from its own trial commit (1fe15af / 191b8c9). The discarded commits (936c88c..f0201eb) are unreferenced.
- rerere preimages/resolutions for cake.ingest.test.ts were recorded in the shared .git/rr-cache during the trial
  (harmless; rerere is not enabled in config).
- feat/phase2-tail on GitHub is still at b360bc2: the rebased branch needs a force-push (`--force-with-lease=feat/phase2-tail:b360bc2`) when the controller decides.
