# Task 6 review: R1 config sweep (6a1c55f..35333a6)

### Spec Compliance

- ✅ Spec compliant. All 12 listed YAMLs carry their hunks. The removal set matches the brief item by item. Nothing out of scope was touched.
- ⚠️ Cannot verify from the diff alone (controller/Mike):
  1. **Prod default report day.** CAKE, UNI and VVV no longer gate the default `report yield` day on the deleted DefiLlama series (tests/report/incomeStatement.test.ts:358-364, `R1_REMOVED`). On prod, a report run without `--day` may land on a different day, and then every figure differs even though no formula changed. Task 7 compares at an explicit `--day`, which hides this. The brief requires these deletions, so it is not a defect in this task. It is a visible behaviour change the release note should carry (report Concern 5).
  2. **PUMP unlock rung vs the register.** PUMP's unlock rows sit on the `disclosure` rung: src/report/sourceTypes.ts maps `schedule.unlocks_next_year` to disclosure, which is Task 4's design. The register lists blockworks.com as `third_party`. The YAML comment and the dilution note do say "compiled by Blockworks, not the issuer", which meets P4's "labelled so". Whether Mike accepts a non-issuer filing on the disclosure rung is still his call under P4.

### Named risks (one verdict each)

**1. Exact removal set: PASS.** I diffed each YAML (`git diff 6a1c55f 35333a6 -- assets/`).

- **coins.llama.fi price cross-checks removed:**
  - crv.yaml:34
  - cvxcrv.yaml:51
  - hype.yaml:32
  - sdcrv.yaml:55
  - sky.yaml:42
  - ycrv.yaml:52
- **CoinGecko `total_supply` cross-checks removed:** crv, cvxcrv, hype, link, lit, pump, sky, uni, vvv. VVV keeps its own Venice `http_json` check (vvv.yaml:52).
- **CAKE:** `flow_usd.fees` and `flow_usd.llama_revenue` deleted. `volume` is `not_measured` with the exact brief string (cake.yaml:141).
- **UNI:** `flow_usd.swap_fees` deleted. `volume` carries the exact brief string (uni.yaml:118).
- **LIT:** fees, llama_revenue and the buyback `defillama` check are gone.
- **VVV:** revenue_proxy, the business-line `cross_check` (vvv.yaml:187) and the burn `defillama` check are gone.
- **Untouched (absent from the diff):**
  - HYPE af_buyback and revenue_proxy (hype.yaml:84, 107)
  - PUMP llama_revenue (pump.yaml:125), solana.supply_burn_daily history and the Jupiter check (pump.yaml:32-33)
  - CRV llama.box (crv.yaml:111, 113)
  - every price_usd and circulating primary, and all `external_ids`
  - the CAKE/UNI/LINK Chainlink `checks` blocks
  - aero.yaml (`git diff --quiet` true)
- **What is left in the 13 YAMLs:** a scan finds only these hosts: api.hyperliquid.xyz, api.rh.lighter.xyz, blockworks.com, lite-api.jup.ag, llama.box, mainnet.base.org, mainnet.zklighter.elliot.ai, outerface.venice.ai, x.com. None is coins.llama.fi or defillama-datasets.

**2. Goldens (R18): PASS.** I wrote a script (cache/scratch/rev-t6/golden.py and golden2.py) that loads both commits, JSON-parses the embedded report strings, flattens each to path=value and diffs. Results for v2-report-13.json:

- The top-level keys are identical. Only the cake, lit, uni and vvv entries changed, in all 5 variants each (stored, loader, prior, growing, growing-loader). The other 9 assets and AERO are byte-identical.
- **cake:** `incomeStatement.volume.{annualized, growth.{annualized,change,current,prior}}` → null; `growth.note` → "not measured"; `metrics` `[flow_usd.fees]` → `[]`; `notMeasured` added (9 paths).
- **uni:** the same 9 volume paths; `metrics` `[flow_usd.swap_fees]` → `[]`.
- **lit:** `flags[0]` "third_party: holders.buyback.cross_checks" and `provenance.thirdParty[0]` were removed, leaving both lists `[]` (4 paths).
- **vvv:** these 8 paths were removed:
  - the `revenue.lines[0].crossCheck.{annualized,metric,sourceType}` paths
  - `provenance.sources[2]` ("third_party:defillama", or "onchain:flow_usd.revenue_proxy" in prior)
  - `provenance.thirdParty[0..1]`
  - the `flags[2]` / `flags[3]` entry "third_party: revenue.business.cross_check, holders.burn.cross_checks"
- **No other path moved:** no revenue, cost, holder flow, yield, dilution, grade or price path, and no flags were re-indexed.

Results for packs-13.json:

- **lit / pump:** `adapter_params[*].adapter` lit.unlocks_next_year → schedule.unlocks_next_year, and its `params_doc`.
- **Seeded row ids:** `observations_in_force[*].id` renumbered on cake (4 ids, 503→303…), lit (11, 903→703…), uni (7, 303→203…) and vvv (7, 407→307…). The entries themselves are unchanged and none was added or removed.

Every moved path is in the R18 set.

**3. Citations and values: PASS.**

- **LIT** (lit.yaml:127-141): url `https://x.com/Lighter_xyz/status/2005862687331303804`; team 260000000 and investors 240000000, each `tranches: { first: 2027-01-29, every_months: 1, count: 36 }`.
- **PUMP** (pump.yaml:102-116): url `https://blockworks.com/token-transparency/filing/pump`; team 150000000000 and investors 97500000000, each `linear: { start: 2026-07-12, years: 3 }`.
- **Quotes:** both match citations.md exactly (string-equality check by script; 121 and 451 chars).
- **PUMP comment** (pump.yaml:99-101): says "compiled by Blockworks, not the issuer" and that pump.fun publishes no schedule.
- **Dilution notes:**
  - LIT (lit.yaml:241): "sizes from Lighter's post, 26% team, 24% investors"
  - PUMP (pump.yaml:150): "Blockworks filing, compiled by Blockworks, not the issuer"
- **Values pinned by tests:**
  - LIT: 500e6/36×9 at 2026-10-16 (tests/assets/lit.ingest.test.ts)
  - PUMP: 82.5e9 unchanged (tests/assets/pump.ingest.test.ts:152)

**4. Pins and fixtures: PASS.**

- **Old pins:** none of the 12 old pins survives anywhere in tests or src (`git grep`).
- **Changed hashes in tests/:** the diff touches exactly the 12 old/new pairs. LIT ×5 is the 3 in load.test.ts, 1 in lit.ingest and 1 in the disclosure e2e; HYPE and VVV ×2 each are load.test.ts plus their own ingest test.
- **AERO:** 3c413feb is unchanged (tests/config/load.test.ts:255, aero.ingest).
- **Fixtures:** `git diff --quiet -- tests/fixtures` is true.
- **R19 replay:** `UNLOCKS_LINE_THEN` (tests/agent/disclosure.e2e.test.ts:197-201) matches `git show 48a5dc5:assets/lit.yaml`:
  - the unlock line (:137, `params: { allocations: [ Team, Investors ] }`) is char-identical
  - the fees and llama_revenue sources (`dailyFees` / `dailyRevenue`, backfill_days 150; :210-223) are identical in value, in flow style
  - NOTE_THEN matches :290
  - the YAML position differs but is a map key; `configHash` is normalized

  See Minor 5 for the one gap.

**5. Register / parity / TERMS: PASS.**

- **TERMS rows removed:** coins.llama.fi and defillama-datasets.llama.fi. No asset reads either now; AERO has 0 coins.llama.fi hits.
- **api.llama.fi kept:** it is still read by aero, hype and pump, and the register now lists exactly those three.
- **x.com:** `first_party_api`, operator Lighter, "cited by hand, not read by code". This is true: `schedule.unlocks_next_year` maps to `citationUrl` in generate.ts:95-96, and the Kind enum has no better rung.
- **blockworks.com:** `third_party`, "compiled by Blockworks, not the issuer". True.
- **Parity map:** only CAKE ...VOLUME, UNI ...VOLUME and VVV `revenue cross-check` were dropped (src/report/parity.ts:98, 128, 132). The VVV pair goes because its v2 path is gone (golden, risk 2). VOLUME is still used for cvxcrv (parity.ts:112).
- **parity.json:** regenerated; it drops exactly those 5 entries.

### Strengths

- The removals are surgical: one hunk per brief item, and no stray edits to out-of-scope reads.
- Every changed fetch test now asserts that no call goes to the removed host. The new `r1-third-party.test.ts` encodes the brief's allowlist directly (`DEFILLAMA_ALLOWED`).
- The golden rewrites are documented path by path in the test doc comments (v2Golden.test.ts:19-22, packGolden.test.ts:22-24). Both claims hold under an independent flatten-and-diff.
- The report flags its own deviations honestly: the TERMS removals, the VVV parity pair and the default-day move.
- `preApprovalLitYaml()` fails loudly if the current block's shape drifts (disclosure.e2e.test.ts:206).

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)

1. **src/report/parity.ts:78-82:** the doc comment on `VOLUME` also explains the VVV revenue cross-check removal, which has nothing to do with volume. Move that sentence beside the `vvv:` entry (:129).
2. **tests/assets/lockers.ingest.test.ts:209:** the new `expect` is indented 6 spaces inside a 4-space block. Cosmetic.
3. **tools/sources-register/generate.ts:143-147:** the TERMS row is keyed by host `x.com` with operator "Lighter". If a second asset ever cites an X post by another issuer, the shared row will name the wrong operator. Consider noting that it is per-citation, or keying by the account path.
4. **Comment rewrites drop calibration facts that were not reads:**
   - sky.yaml:33-35 drops "DefiLlama's holders revenue is reference only: 44.2M vs 44.6M measured".
   - sdcrv.yaml:47-48 collapses "+2 to +6 % over DefiLlama on 10-03..09, +16 % on 10-08, median -0.3 % over 90 days" into "+2 to +16 percent over the sdCRV/CRV Curve pool". That loses the median, and the comparison was to DefiLlama's price, not the pool.
   - lit.yaml:125 drops "no cliff" from the Q3-call summary.

   None is wrong in a way that matters, but these are historical records.
5. **tests/agent/disclosure.e2e.test.ts:194-196:** the comment says the replay restores the file "as the file stood when the run was filed". It does not restore the 2026-10-23 file's other DefiLlama/CoinGecko lines: the total_supply CoinGecko check and the buyback dailyHoldersRevenue check (48a5dc5:51, 93). This is harmless, because fixtures are byte-unchanged and the test passes. Narrow the comment to "the lines the run reads".
6. **tests/assets/r1-third-party.test.ts:43-51:** it checks `type: defillama` and two URL hosts only. An `http_json` to `api.llama.fi`, or another `*.llama.fi` host, in the 12 YAMLs would pass. A host regex `/llama\.fi/` with the R6 PUMP exception would close this.

### Checks run

- Per-YAML `git diff` of all 12 files, plus a grep of the head YAMLs for llama, emissions, revenue_proxy, swap_fees and coingecko total_supply.
- Golden flatten-diff scripts: cache/scratch/rev-t6/golden.py and golden2.py; output in v2deep.txt and packs.txt.
- Hash census with `git grep` on the old and new pins.
- `git diff --quiet -- tests/fixtures assets/aero.yaml`.
- Quote string-equality against citations.md.
- `git show 48a5dc5:assets/lit.yaml`, for R19.
- I ran no tests: there was no specific doubt that the implementer's run (1744/1745, flake 7/7 alone) and the controller's 16-file rerun leave open. Test evidence: suite-35333a6.log holds only the vitest header, because the background run had not finished. Before merge, the controller should confirm the full-suite rerun.

### Assessment

**Task quality:** Approved

**Reasoning:** The sweep removes exactly the brief's set. Every golden path that moved is in the R18 allowlist, and no value path moved. Citations, pins, fixtures, register and parity check out. What remains is comment and coverage polish, plus two cross-task items for the controller (the prod default day and PUMP's disclosure rung).
