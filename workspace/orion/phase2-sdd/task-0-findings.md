# Task 0 review findings (d614b08..ca1bc8e, proof harness incl. fix round 1)

### Spec Compliance

- ❌ Issues found:
  - "v2 figures must equal the parity map" is not enforced against the report: the parity check never reads the new-side JSON (compare.py:136-146, 188-193). See I1.
  - A run whose new side has `incomeStatement` passes without `--parity`/`--reclass` (compare.py:188, 194). See I2.
  - The yCRV `unreconciled` default contradicts binding ruling R6 (expected.py:107-114). See I3.
- ✅ Everything else in the brief is present: all 7 listed files exist. The Step 1 test list is fully covered (test_compare.py: identical, number diff, incomeStatement deletion, empty, <13, parity 3e-12 vs 5e-13, reclass 2e-12). Reducers are `.py` files. Every script writes its output to files. snapshot.sh follows postgres-backend.md steps 1-3 with the `p2proof_` prefix the global constraints require. Commit 1735e10 has the required message.
- ⚠️ Cannot verify from the diff:
  - The v2 dotted paths in expected.py (`incomeStatement.revenue.annualized`, `incomeStatement.belowLine.toHolders` without `.annualized`, `ratios.payoutRatio`, `unreconciled.annualized`) are guesses at a shape Tasks 3/4 have not built yet. The controller should pin them when Task 3 lands.
  - The Step 4 dry run is the controller's job (per the controller: 13/13 identical, anomalies and proposals PASS).

### Strengths
- Strict equality in compare.py: key order, int/float/bool type and exact numbers, plus a raw-byte check when there is no v2 key (compare.py:52-78, 186). It reports the first differing path.
- Bad runs fail: a missing, empty or unparseable file, a malformed `status.tsv`, a missing or non-zero exit per (side, file), an asset on one side only, and fewer than 13 assets on both sides. I found no way to get exit 0 from an empty, truncated or failed side.
- Live safety:
  - Both shell scripts unset caller `ORION_*`.
  - The source is opened only as `file:…?mode=ro`.
  - `<P>/schema` is written before Postgres is touched.
  - `.env` files are mode 600 under umask 077.
  - cleanup.py resolves paths (`..` and symlinks cannot escape), checks the schema name with a regex before building any SQL, uses `psql -X` with ON_ERROR_STOP, and confirms the drop.
- Fix round 1 is correct. The test `test_reports_sh_passes_orion_env_file_for_a_release_on_both_sides` uses a strict stub and reproduces the real `resolvePaths` refusal (src/cli/paths.ts).
- Ran `/usr/bin/python3 -m unittest tools/phase2-proof/test_compare.py`: 27 tests OK, clean output.

### Named-risk checks performed
1. **False pass.** I read compare.py end to end, including the paths through status.tsv, the asset count and the list files.
   - Empty, truncated or non-zero-exit sides fail, and so do fewer than 13 assets.
   - reports.sh refuses homes whose `ORION_DATABASE_URL`/`ORION_DB_SCHEMA` differ (reports.sh:31-38).
   - Gaps: I1, I2, M1, M2.
2. **Live safety.**
   - I checked src/cli/paths.ts `resolvePaths`: envFile is `ORION_ENV_FILE ?? <ORION_HOME>/.env`, and a checkout dist is never a release, so the new side and the migrate step read only `<home>/.env`.
   - tools/import-sqlite/cli.ts takes an explicit `--to`/`--schema`.
   - Nothing writes outside `<P>`/`<out>`, opens orion.db read-write, or drops a non-`p2proof_*` schema.
   - Gaps: M3, M4, M5.
3. **Formulas vs the table.** I checked them against `git show HEAD:src/report/holderYield.ts` (IncomeStatement revenue/holders/protocol `{annualized}`, `IncomeLine {id,to,annualized}`, `RevenueStreamLine.grossAnnualized`, `volume {annualized}`) and assets/sdcrv.yaml, ycrv.yaml and lit.yaml (line ids `vote_incentives`, `boost_delegators`, `vecrv_fees`, `crv_fee_share`, `styc_fee`; robinhood `share: 0.5`).
   - sdCRV and LIT match the table exactly. The sdCRV payoutRatio numerator checks out against the 2026-10-27 figures: 0.72×3.60 = 2.59 = 0.89 + 1.70, and 0.89/1.90 = 0.47.
   - yCRV revenue matches. yCRV unreconciled: see I3.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)

**I1. compare.py:136-146 and 188-193: the parity check never looks at the report.**
- What: `check_parity` compares the two numbers inside each `[label, a, b]` triple of the map file. Nothing ties `a` or `b` to `new/<asset>.json` `incomeStatement`.
- Why it matters: a parity map that is stale, from another day or schema, or produced by code that never read this run's output, passes for all 10 parity assets whatever the new release printed. That is a false pass against "Its v2 figures must equal the parity map … at rel 1e-12".
- Basis claimed: the report cites "ruling 4" for the format, but progress.md's R4 is about `--legacy` consumers, so no recorded ruling backs this shape.
- Fix: make the parity input `{asset: {dotted path: expected}}`, like `--reclass`, and resolve each path on the new side with `get_path`. Alternatively, require `a` to be a dotted path into the new JSON. Add a test where the map is self-consistent but the new JSON differs, and check that it FAILs.

**I2. compare.py:188 and 194: a v2 run passes without its v2 checks.**
- What: both checks are gated on `parity is not None` / `reclass is not None`. Once the new side carries `incomeStatement`, running `compare.py <out>` without the flags still prints `PASS` for all 13 assets and `OK`, and exits 0. Only the absent `(+ parity, reclass)` suffix hints at what was skipped.
- Why it matters: "exits 0 only on a full pass" is violated, and it takes one omitted flag. The README calls the maps "required", but the code does not enforce it.
- Fix: if any new-side file has `incomeStatement` and the matching map was not given, emit `FAIL setup: --parity/--reclass required (new side has incomeStatement)`. Add a test for it.

**I3. expected.py:107-114: the default yCRV `unreconciled` contradicts ruling R6.**
- What: `unreconciled = volume − income.holders − income.protocol`, where v1 `income.protocol` includes the `styc_fee` line (assets/ycrv.yaml:166). With R6's default (revenue = yearn_gross only, 2.20), this gives ≈ −0.10.
- Why it matters: ycrv-styc-probe.md's binding ruling R6 leaves the st-yCRV fee out of the v2 statement ("no revenue, holders or protocol line"). The v2 protocol is then the treasury line only, so a correct implementation reports unreconciled ≈ 0, because the yearn_gross = ybs_payout + treasury check holds. The harness would fail a correct Task 2/4, or push the implementer toward −0.10. The table's own pairing ("2.20 … ≈ 0 or −0.10") allows either value, so R6 decides it.
- Fix: in the default (non-`--ycrv-styc-separate`) mode, use `income.protocol − styc_fee line`. Keep the current formula for the spec-alternative flag. Name the R6 dependency in the docstring and in a test.

#### Minor (Nice to Have)

**M1. compare.py:220-255: no check of what each report is about.**
- What: compare never checks that a report is the asset it is filed under, or the day `D`. It does not read `run.txt` or the asset list either. Two sides that both print the same vacuous object (wrong `--day`, an `{error}` document with exit 0) pass as identical.
- Fix: require `obj["asset"] == stem` and `obj["day"] == D` (from run.txt), and require the asset set to equal the run.txt list.

**M2. reports.sh:31-38: only two `.env` lines are compared.**
- What: just `ORION_DATABASE_URL` and `ORION_DB_SCHEMA` are checked. Any other DB-affecting line in one home's `.env` is not.
- Fix: compare the two `.env` files byte for byte. snapshot.sh writes them identical anyway.

**M3. cleanup.py:33-39 and 73, snapshot.sh:30: `$TMPDIR` is trusted as given.**
- What: cleanup.py removes any directory strictly under `$TMPDIR`, even with no `schema`/`snap.db` marker. With a mis-set `TMPDIR` (e.g. `/home/hermes`), `cleanup.py /home/hermes/git/orion` would `rmtree` the live tree. snapshot.sh has the same gap: it would build `<P>` in the live tree.
- Fix: refuse when `<P>` or `$TMPDIR` overlaps `/home/hermes/git/orion`, and require `<P>/snap.db` or `<P>/schema` before deleting.

**M4. reports.sh:19-22: `<out>` and the homes need not be under `$TMPDIR`.**
- What: unlike snapshot.sh, reports.sh never checks where `<out>` and the homes live. The CLI writes its data-home files into `<home>`.
- Why it matters: a home that names a p2proof schema is the only guard. Constraint: scratch homes go under `$TMPDIR`.
- Fix: apply the same `$TMPDIR` check as snapshot.sh.

**M5. snapshot.sh:67: `db migrate` has no `ORION_ENV_FILE`.**
- What: the migrate step does not pass `ORION_ENV_FILE="$P/new/.env"`, unlike every reports.sh run after fix round 1. It fails safe if `P2_NEW_DIST` is a release (`release_env_required`), but the asymmetry is the exact bug fix round 1 fixed elsewhere.

**M6. snapshot.sh:81: the proof result is read with a formatting-dependent grep.**
- What: `grep -q '^  "ok": true,$'` relies on the formatting and on `ok` not being the last key. If either changes, it gives a false refusal (fail-safe).
- Fix: read `ok` with a small `.py` reducer.

**M7. test_compare.py: refusal paths have no committed tests.**
- What: the reports.sh refusals (differing schema, non-p2proof schema, <13 YAMLs, existing `<out>`, a recorded failing run) and the snapshot.sh preconditions were only checked ad hoc, per the report. Only the ORION_ENV_FILE happy path is committed.
- Fix: these stub-dist tests are cheap and guard the live-safety claims. Add them.

**M8. snapshot.sh:23-25: unrequested env overrides.**
- What: `P2_OLD_CONFIG` was not asked for. Per the README and the fix round, it has no effect for a release old side. `P2_NEW_DIST` and `P2_SOURCE_DB` are useful for testing but are also unrequested.
- Fix: consider dropping `P2_OLD_CONFIG`.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The legacy byte-identity half is solid and safe, with no false pass on empty, failed or short runs. But the v2 half can pass without checking the report: the parity triples are self-referential (I1) and the maps are optional (I2). The yCRV expected value also conflicts with ruling R6 (I3). All three need fixing before Task 3/4 relies on the harness.

## Controller rulings on Task 0 findings (binding for the fix)
- I1: FIX. Ruling R7: the parity file becomes a path map, not value triples: `{"<asset>": [["<label>", "<v2 dotted path in new JSON, e.g. incomeStatement.revenue.annualized>", "<v1 dotted path in old JSON, e.g. income.revenue.annualized>"], ...]}`. compare.py reads both values itself (new side from new/<a>.json, old side from old/<a>.json), rel <= 1e-12; a missing path on either side fails; null == null passes only if both are null. Task 3 writes the real tools/phase2-proof/parity.json from its PARITY definition. Paths may index arrays by element id: `income.lines[id=vecrv_fees].annualized` (support this selector syntax; test it).
- I2: FIX. If any new-side asset JSON has `incomeStatement`, compare.py requires both --parity and --reclass, and requires every one of the 13 assets to be covered by exactly one of them (10 parity: aero cake crv cvxcrv hype link pump sky uni vvv; 3 reclass: sdcrv ycrv lit); otherwise FAIL.
- I3: FIX per R6: yCRV expected unreconciled = revenue - (ybs_payout line) - (treasury line), never subtracting styc_fee; with --ycrv-styc-separate, revenue includes styc_fee and unreconciled = revenue - ybs_payout - treasury - styc_fee.
- M1: FIX (cheap): each report's top-level `asset` must equal the file name and `day` must equal D (read from run.txt) on both sides.
- M5: FIX (cheap): snapshot.sh passes ORION_ENV_FILE to db migrate too.
- M2, M3, M4, M6, M7, M8: deferred -> followups note (Task 0: minor (deferred) lines in the ledger).
