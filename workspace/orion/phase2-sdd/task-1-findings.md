# Task 1 review: `income_statement` config schema (ca1bc8e..eca4c4d, src+tests; commits fc5587b + eca4c4d)

### Spec Compliance

- ✅ Spec compliant. Spec §6, correction 6, R2 (sum-only checks) and R8 (strict unique ids) are all enforced in
  `src/config/incomeStatement.ts`. The file list matches the brief: the new module, the `schema.ts` hook-up and the new test file.
- ⚠️ Cannot verify from diff:
  - Correction 6 says below_line-to-holders lines "carry `capture_rule`", but the schema leaves it optional
    (incomeStatement.ts:89, 252). The brief's interface marks it optional too, and the implementer flagged this as
    concern 3. The controller should rule whether a *measured* to-holders below_line needs it, because `asset describe`
    reads it (see M3).
  - The automatic `parameter` check (share_metric) and `two_path` check (paid_metric) belong to Task 5 and are not
    in this diff, as intended.

### Named-risk checks

1. **Hash stability: OK.**
   - `income_statement` is `.optional()` with no default (schema.ts:203). The test asserts the key is absent and the
     MINI pin `c8cc4642…f830` holds (test:289-290; the same pin is at tests/config/load.test.ts:28).
   - The shared shapes (`WindowDaysSchema`, `VolumeSchema`, `DilutionSchema`, `BurnedTokensSchema`) match the
     removed inline shapes exactly, with no defaults added.
   - Spreading `...sharedReportingShape` first in `ReportingSchema` changes zod's output key order inside `reporting`.
     The hash is `sha256(canonicalJson(config))`, and `canonicalJson` sorts keys (src/util/canonical.ts:16-17,
     load.ts:35). No `src` code JSON-stringifies `config.reporting` without canonicalizing it (grep), so the order
     change is hash-neutral.
   - Error messages from `sharedReportingIssues` keep the exact old text (schema.ts:335-353). Only their order in a
     multi-issue error changed: volume, burned_tokens and dilution now come before extra_cash. Existing tests
     (tests/report/holderYield.test.ts:96,109) match single messages by regex, so nothing depends on the order.
   - Proposal filing reads `raw` (load.ts:18-19), which is unaffected.
2. **Validation holes: every rule is enforced.**
   - One value source per line: revenue :180 (5 keys), use :213, below_line :243.
   - Ids unique across all six sections: :163-166 (R8, no exception).
   - Disclosed revenue alone: :205.
   - Remainder section empty: :262.
   - Burn haircut 0: holders :230, below_line :258.
   - below_line metric not a revenue metric: :246 (covers `derived.from` too).
   - A use-line metric that equals a revenue metric is refused with "use of": :217.
   - `paid_metric` only on holders (by strictness) and a flow: :233.
   - below_line `run_rate` is a level: :249.
   - Every node is a strictObject, including estimate, derived and dilution, and `.extend` keeps strictness.
   - Metric existence and type are checked through `typed()` :145.
   - Some rules have no test that would fail if the check were deleted: see M1 and M2.
3. **resolveUse: OK.**
   - `share` defaults to 1 only in the resolver (:301). The schema's `Share` has no default (:15), and test:57 asserts
     the block round-trips.
   - An `of` line inherits metric, derived, estimate, disclosed, settlement and started, and gets back the revenue
     line so Task 3 can apply the run-rate weight (:307-310). This is acceptable because the weight depends on the data.
   - An `of` that names a missing id, or any id that is not a revenue line, is refused at load (:222). An `of` that
     names a not_measured revenue line is also refused (:223). The resolver's throw (:306) is defensive only.

### Strengths
- One definition of the shared reporting shapes and one set of checks (`sharedReportingIssues`), with the old
  messages unchanged. There is no copy-paste between `reporting` and `income_statement`.
- The type-only import from schema.ts avoids an ESM cycle (incomeStatement.ts:2), and the reason is documented.
- The rules are explicit and the messages are prefixed and name the line (`holders.buyback …`). Revenue metrics are
  read first, so a use or below_line line that re-reads one gets the specific "use of" or "is a revenue metric"
  message instead of the generic double-read one.
- The R8 fix is clean: the exception is fully removed, and the tests cover full and partial pass-on, the `_rev`
  convention and below_line id collisions (test:81-101).
- The Task 2 mapping rows (cvxcrv `crv` + paid_metric, crv run_rate, sdcrv bribes, lit share_metric, vvv
  cross_check) all fit the schema.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)

- **M1. tests/config/incomeStatement.test.ts:279 (also :240-242, :263-267): the estimate strictness case proves nothing.**
  The mutation deletes `revenue[1].metric` but leaves `settlement: 'periodic'` and `started`. So incomeStatement.ts:199
  ("takes settlement and started only with a metric or derived") throws even if `EstimateSchema` were not strict.
  Every case in the loop, and the sum-only test (:266), uses a bare `toThrow()` with no message regex, so an unrelated
  refusal hides a lost check. Fix: delete `settlement` and `started` too, and match `/Unrecognized key/` (and
  `/sum/` or the zod literal message for the check type).
- **M2. Rules with no test that would fail if the check were deleted** (incomeStatement.ts):
  - `derived` is never exercised. Untested: `derived.from` must be a flow (:189), the double-read and
    revenue-metric registration for `derived.from` (:190-191), and `derived.share_metric` must be a level (:192).
  - settlement or started without a metric or derived (:199). The test named "settlement only on metric lines"
    (test:197-201) asserts only the periodic-needs-started rule.
  - `of` naming a not_measured revenue line (:223). Also `of` naming an existing non-revenue id, such as a holders
    id; the test uses only `'nope'`.
  - `paid_metric` on a not_measured holder line (:234).
  - holders/protocol/cost `metric` must be a flow (:215); only the revenue metric type is tested.
  - check id unique (:268), and check `total` must be a flow (:270).
  - below_line `valued_per: recipients` needs `staked` (:259).

  These are coverage gaps; the logic reads correctly.
- **M3. incomeStatement.ts:89, :252-254: a measured below_line-to-holders line is not required to carry `capture_rule`.**
  Holders lines require it (:69). Correction 6 says both "carry" it, and `asset describe` reads it for the
  holder-flow text. A measured to-holders line, such as crv `vote_incentives`, would show no capture rule. Either add
  `capture_rule` to the required list at :252 or record a ruling (see ⚠️).
- **M4. incomeStatement.ts:232-235: `paid_metric` is left out of the double-read guard with no constraint of its own.**
  It may equal another holder line's `metric` or `paid_metric`, or a below_line metric. Holder flow reads
  `paid_metric` in place of the statement source, so that series would count twice in holder flow and yields. Fix:
  refuse a `paid_metric` that any other line reads, other than the revenue series this line passes on.
- **M5. tests/config/incomeStatement.test.ts:57 and :111.** "parsed exactly as written" uses `toEqual`, which ignores
  keys whose value is `undefined`. That is exactly the leak a default or undefined key would cause. Use
  `toStrictEqual`. `alone.volume = undefined;` (:111) is dead code before the `delete`.

### Assessment

**Task quality:** Approved (minor follow-ups only).

**Reasoning:** Every spec §6 and correction-6 rule is enforced at load, and the hash is provably unaffected
(sorted-key canonical JSON, no defaults, absent key asserted). The remaining gaps are test strength (one vacuous
strictness case, several rules with no test) and two small schema tightenings (M3, M4) that the controller can fold
into the R9 follow-up commit.

## Controller rulings on Task 1 findings (binding)
- M1 FIX (delete settlement+started too; match error messages with regexes in every refusal case).
- M2 FIX (add the listed tests; each must fail if its check is deleted).
- M3 FIX: a below_line line with to: holders and `metric` or `run_rate` REQUIRES capture_rule (not_measured lines don't). crv `vote_incentives` gets `capture_rule: programmatic` (same as sdcrv bribes: third parties pay voters through vote markets) unless crv.yaml's v1 reporting.extra_cash/holder_flows already states one, in which case copy that.
- M4 FIX: refuse a paid_metric that any other line reads (metric, paid_metric, run_rate, derived.from, share_metric, below_line metric), except the revenue series this line passes on via `of`.
- M5 FIX: toStrictEqual; remove the dead assignment.
