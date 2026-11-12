# Task 6 report: the R1 config sweep (12 assets)

Status: DONE. Commit `35333a6` feat(config)!: Phase 3 R1: drop the DefiLlama/CoinGecko cross-checks and display series (12 assets); cited unlock schedules; CAKE/UNI volume not_measured. 37 files, +360/-371.

## Removed sources per asset

| Asset | Removed |
|---|---|
| cake | metrics `flow_usd.fees` (defillama dailyFees), `flow_usd.llama_revenue` (defillama dailyRevenue); `volume` -> `{ not_measured: "gross swap fees: DefiLlama removed (Phase 3 R1); on-chain v2/v3 gross not read yet (Phase 3b)" }` |
| crv | price_usd cross-check coins.llama.fi; total_supply cross-check coingecko total_supply (llama.box kept, R7) |
| cvxcrv | price_usd cross-check coins.llama.fi; total_supply cross-check coingecko total_supply |
| hype | price_usd cross-check coins.llama.fi; total_supply cross-check coingecko total_supply (af_buyback / revenue_proxy kept, R5) |
| link | total_supply cross-check coingecko total_supply |
| lit | metrics `flow_usd.fees`, `flow_usd.llama_revenue`; `flow_usd.buyback` defillama cross-check; total_supply coingecko cross-check; `unlocks_next_year` lit.unlocks_next_year (defillama-datasets) -> `schedule.unlocks_next_year` (team 260e6 + investors 240e6, tranches first 2027-01-29 / every_months 1 / count 36; citation https://x.com/Lighter_xyz/status/2005862687331303804 with the verbatim quote); dilution note now "(Lighter terms; sizes from Lighter's post, 26% team, 24% investors)" |
| pump | total_supply coingecko cross-check; `unlocks_next_year` lit.unlocks_next_year (defillama-datasets/emissions/pump) -> `schedule.unlocks_next_year` (linear start 2026-07-12 years 3; team 150e9, investors 97.5e9; citation https://blockworks.com/token-transparency/filing/pump, verbatim quote; YAML comment says "compiled by Blockworks, not the issuer" and that pump.fun publishes no vesting schedule); dilution note names the Blockworks filing. llama_revenue and supply_burn_daily history kept (R6) |
| sdcrv | price_usd cross-check coins.llama.fi |
| sky | price_usd cross-check coins.llama.fi; total_supply coingecko cross-check |
| uni | metric `flow_usd.swap_fees` (defillama dailyFees); total_supply coingecko cross-check; `volume` -> `{ not_measured: "gross swap fees: DefiLlama removed (Phase 3 R1); v2 x6 derived and v3/v4 scans not built (Phase 3b)" }` |
| vvv | metric `flow_usd.revenue_proxy`; `cross_check: flow_usd.revenue_proxy` on the business line; `flow_usd.burn` defillama cross-check; total_supply coingecko cross-check |
| ycrv | price_usd cross-check coins.llama.fi |

Every YAML comment naming a removed read was rewritten (cake/uni/lit/pump/sky headers, sdcrv price note, lit/pump total_supply notes, lit buyback, vvv burn + revenue notes, lit/pump unlock notes). `external_ids` untouched. AERO untouched.

## Hashes (old -> new); AERO 3c413feb... unchanged

| Asset | Old | New |
|---|---|---|
| cake | 2f7d698f7f077e3769758dde049776f921dfd6381519892240fca3af98dd7a99 | 5434fc561d3f70d20eb8e31be5cf41b03e691bf14a4fa1d14b845d072c4d5837 |
| crv | 02417b36678c4d60d189ee7a86b748a5fed020c66528bcb19d199d83dbd0a80b | 7b4e1b57f1a56cb68842d1f9ed209727418a8fdff57f7d756d9eb453ada5a78c |
| cvxcrv | e9ecdb0d739a2be07973e015419c328ee67d6325a597e33e71a65ea411ded7a8 | 372064fcfca833e0adbb9aa562cdb955aa37092ee0de29cae510a7ed8d4a4db9 |
| hype | f7dcfeecf846ff6161e18797728bc37ae2d30d52157446bd92e21b1b8b245b3f | 492438a0835419c95fa6c9a6fbe9a77c7f1c3df6cc870cea70d1325db457d98a |
| link | 6bc2033876e803860ab6aa949e6ab20a1db8f24d695e12a454ec7f7a77d0f8b1 | 3d098a292b83acc30e57105b4f868145dc8c801db4be63c49dd7ce0ddc42b8ba |
| lit | a3e049f1d277b4d5ba23af6995fbf4527776ce8c5493433d4c671faf83ce1004 | 0de769beeae95c555b2db4e89ca3d7b68f705719ead7de62dd53b768cccb0cc9 |
| pump | 3a2f142bfc7a25afd959263a479a22b8f188d8827a47ce52dd8ed2a3bd98bd06 | 4a9e1eba3c80615f6abd04c572c36c76602c803caa5e937333ecf9a23a728126 |
| sdcrv | 0583401d6b4d5a409522a3c29958b3b7bf4baf99a22b72fe57255697c0199b32 | 0ba07bec8636ce7983e3b616d0074bd7697e44b0265317bb632880f1215f43d8 |
| sky | cef8a54bcbc5186f9a742ec6b8a99be2f19308f51f01630bdf33647df7b9cd74 | ccfb251b4e859a8ca6dacd9faae6ae6d6fdbfec63b85235bfdcc34000c754c72 |
| uni | e63169375421ff156ebf8735ea21897828794118ac68ecff22f3f9f3b131c792 | 2c0f3c2c69fce619ce90e86898e4a50cc0477a55a0dad96f5a363a5acc45aed9 |
| vvv | fa05d39217ee2160f6e746350494a818b51c316368e6d3b364dc1c105b328838 | 45ad0a3a44763cf55abccdcf6d1e2facaf49c430f222953bb00556120e9adaa2 |
| ycrv | d594acfc729f0b3b8c4022ec44ecd0f11133e5df07582049a6c09685d4e87f37 | cca3f10e921d66c7b703a202ffc401c802bb2882b34d34deb196a27984d1517d |

Re-pinned only in the files named by the controller (each asset's own pin): the 11 `*.ingest.test.ts` (lockers carries cvxcrv + sdcrv), `tests/config/load.test.ts` (hype, lit x3, vvv), `tests/agent/disclosure.e2e.test.ts` LIT_HASH. No other pin moved.

## `asset validate` (no ORION_HOME; reads the worktree's assets/)

```
aero: ok    listing bar (D6): fails: revenue.fees (third_party), holders.voter_fees (third_party)
cake: ok    listing bar (D6): ok
crv: ok     listing bar (D6): ok
cvxcrv: ok  listing bar (D6): ok
hype: ok    listing bar (D6): fails: revenue.trading (third_party), holders.af_buyback (third_party)
link: ok    listing bar (D6): ok
lit: ok     listing bar (D6): ok
pump: ok    listing bar (D6): fails: revenue.protocol (third_party)
sdcrv: ok   listing bar (D6): ok
sky: ok     listing bar (D6): ok
uni: ok     listing bar (D6): ok
vvv: ok     listing bar (D6): ok
ycrv: ok    listing bar (D6): ok
```
(The three listing-bar fails are the out-of-scope R4/R5/R6 lines.)

## Tests

- RED (`tests/assets/r1-third-party.test.ts` against the pre-edit assets, `git stash -- assets`): 5 failed | 1 passed (6): defillama sources (cake fees…), coins.llama.fi urls (crv, cvxcrv, hype, …), 9 coingecko total_supply, lit.unlocks_next_year on lit+pump, LIT not on schedule. GREEN after: 6 passed (6).
- New test asserts: no `defillama` source outside {hype af_buyback, hype revenue_proxy, pump llama_revenue} primaries; no coins.llama.fi / defillama-datasets url in the 12 YAMLs; no coingecko `field: total_supply`; no asset (13) uses `lit.unlocks_next_year`; LIT and PUMP use `schedule.unlocks_next_year`.
- Asset ingest tests: removed stubs (cake/uni/lit/vvv api.llama.fi, lit/pump defillama-datasets, crv/cvxcrv/sdcrv/hype/sky/ycrv coins.llama.fi), and each fetch test asserts no call to the removed host. LIT's unlocks value now 500e6/36 x 9 = 125,000,000 at NOW 2026-10-16 (offline); PUMP 82.5e9 unchanged.
- Full suite `npx vitest run --maxWorkers=2`: 1744 passed | 1 failed (1745). The failure is the known flake `tests/push/gitPublisher.test.ts > a moved remote is refused, alerted once, outbox kept` (5000 ms timeout); alone at `--maxWorkers=1`: 7 passed (7).
- `npm run typecheck`: clean. `python3 -m unittest scripts/provision/test/test_orion_remote.py`: Ran 52, OK.
- `npx tsx tools/sources-register/generate.ts --check`: current. `git diff --quiet -- tests/fixtures assets/aero.yaml`: true.

## Other files

- `src/report/parity.ts`: dropped CAKE and UNI `...VOLUME`, and VVV's `revenue cross-check` pair (its v2 path no longer exists); `tools/phase2-proof/parity.json` regenerated (`npx tsx tools/phase2-proof/write-parity.ts`, -25 lines). `tests/report/parity.test.ts`: volume pairs required only for list-form volume; VVV cross-check pair asserted absent; cake/uni asserted to have no volume pair.
- `tools/sources-register/generate.ts` TERMS: added `x.com` (first_party_api, Lighter, cited by hand, not read by code) and `blockworks.com` (third_party, Blockworks, compiled by Blockworks not the issuer, cited by hand, not read by code). REMOVED `coins.llama.fi` and `defillama-datasets.llama.fi` rows: the generator throws on a TERMS entry no asset reads (AERO has no coins.llama.fi read). `docs/ops/sources-register.md` regenerated.
- `tests/report/golden/v2-report-13.json` regenerated (UPDATE_GOLDEN=1) after a path-level diff of the 4 changed assets: only CAKE/UNI `incomeStatement.volume.*`, VVV business `crossCheck.*`, and provenance.thirdParty/sources/flags entries naming LIT's buyback and VVV's burn/revenue cross-checks moved; inputs and the other 9 assets byte-identical. Note added to the test's doc comment.
- `tests/agent/golden/packs-13.json` regenerated: only LIT/PUMP adapter_params (lit.unlocks_next_year -> schedule.unlocks_next_year) and seeded level-row ids on cake/lit/uni/vvv (fewer flow metrics seeded first). Note added.
- `tests/report/incomeStatement.test.ts`: thirdParty expectations (lit, vvv now []), day-gate table filtered by an `R1_REMOVED` map (cake fees, uni swap_fees, vvv revenue_proxy), VVV line has no crossCheck, list-form volume tests on cvxcrv only plus a cake/uni not_measured test.
- `tests/agent/context.test.ts`: LIT adapter_params entry is schedule.unlocks_next_year with its paramsDoc.
- `tests/config/load.test.ts` params-validation test now varies `schedules[0].tranches`.
- `tests/agent/disclosure.e2e.test.ts`: LIT_HASH re-pinned; `preApprovalLitYaml()` now swaps the new schedule block back to the pre-approval `lit.unlocks_next_year` line and re-adds the two removed display series (the scripted run reads `flow_usd.llama_revenue`), i.e. the file as it stood when the run was filed. Fixtures byte-unchanged; 11/11 pass.

## Concerns

1. disclosure e2e: more than the HASH constant changed — its replay derives the 2026-10-23 lit.yaml from the current file, so the derivation had to change (block swap + re-adding the two DefiLlama series in the replay copy only). Fixtures unchanged.
2. Two goldens (v2 report, packs) were rewritten off the base commit, against their "only at the base commit" note; diffs were checked path-by-path (above) before the rewrite.
3. Sources-register TERMS rows for coins.llama.fi and defillama-datasets.llama.fi removed (generator requires it); the controller only asked for additions.
4. VVV's parity pair `revenue cross-check` dropped too (not only CAKE/UNI volume): the path is gone with the cross-check.
5. Default report day: CAKE, UNI and VVV no longer gate on the removed DefiLlama series, so on prod the default `report yield` day may move (likely later, the DefiLlama series lagged). Task 7 compares at an explicit `--day D`, which sidesteps it, but it's a visible behaviour change.
6. LIT unlocks on the asset test's NOW (2026-10-16) is 125.0M (9 tranches); the plan's 138,888,889 is 10 tranches at the prod date — consistent, just a different day.
