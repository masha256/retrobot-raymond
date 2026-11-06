# Task 7b review: 14f020e..54d3a47 (yCRV vote incentives below the line; apportion-by-mix; count_from split flows)

### Spec Compliance

- ✅ Spec compliant. All brief/rulings items are present:
  - `assets/ycrv.yaml:146-59`: two monitor_only by-sender flows. `fees_rev` = `yearn_gross_fees` is the only revenue line.
    `ybs_payout` and `treasury` are apportioned by fees/gross. Below the line, `incentives_to_holders` (cash, haircut 0,
    staked, recipients, programmatic, with the note) and `incentives_to_protocol` are apportioned by incentives/gross.
    `splitter` is kept and the new `gross_by_sender` check has tolerance 1e-6 %. The v1 blocks are untouched.
  - Mechanism is generic: `apportion`, method `derived`, formula `apportion_by_mix@1`, and the schema refuses an
    unpartitioned set (`src/config/incomeStatement.ts` 479-511). The followups note has the R14 placeholder.
  - Only ycrv's hash is re-pinned (`tests/assets/ycrv.ingest.test.ts:1048`).
  - The deviation (one shared scan + `count_from`, instead of separate `from_allowlist` scans) is accepted by ruling R20.
    Not re-reported.
- ⚠️ Cannot verify from the diff: the real-data proof (backfill on the proof copy, cross-release compare) and the R14
  error figure. Both are controller steps.

### Named-risk checks run

1. **Invariance.**
   - Ran a tsx dump on detached checkouts of BASE and HEAD, using `syntheticInput` on all 13 repo assets. For the 12
     non-yCRV assets, the config hash, v1 JSON, v2 JSON and `reportFlowMetrics` are all byte-identical.
   - For yCRV, I fed the same serialized input to both commits: `holderYieldReport` (legacy) is byte-identical.
     `incomeStatement.yields` is identical, and so are `holderFlow.gross` and `holderFlow.net` (404,066.647…). Only
     `fromRevenue`/`fromBelowLine` move (404,066 / 0 becomes 185,032 / 219,035).
   - Collapse logic (`src/report/incomeStatement.ts`, diff L824-851): a set whose lines all reach holders alike is summed
     once as its whole flow (w=1). `units` equals `counted` when there is no set, so other assets keep the same order and
     values.
   - Zero total gives a null mix plus a flag, with no division (diff L671-687). This is tested, including a no-NaN
     assertion (tests/report/apportion.test.ts:1481-1497).
   - Line complements sum to the whole within 1e-15 (test L1447-1467).
   - Focused run: `npx vitest run tests/report tests/config tests/checks tests/assets --maxWorkers=1` → 29 files,
     378/378 passed. That includes the parity map 10/10 and the reclass test. `python3 -m unittest test_compare.py`
     → 43 OK.
2. **Schema guard.** I probed `parseAssetObject` on the locker fixture.
   - Refused, as intended: read twice without apportion; different totals; a by named twice; by not a flow / by =
     total; no partition check; a set of one; apportion with no metric or with `paid_metric`; another line's
     `paid_metric` = the apportioned flow; mixed units; a by series outside the total.
   - Accepted (gaps): see I-1, M-1.
3. **count_from.**
   - `count_from` already existed. The diff has no planner, flow or source changes (`git grep count_from|countFrom`:
     src/config/sources.ts 71/105/146/177, src/ingest/plan.ts 134, src/ingest/flow.ts 382).
   - Unlisted detection is per group, on the group allowlist (flow.ts ~L366), and unchanged. Members filter only their
     tally (L382). `sources.ts:177` requires `count_from` ⊆ `from_allowlist`.
   - The plan test pins the one group of three members (ycrv.ingest.test.ts L1108-1113). Every other asset's plan is
     unchanged: the hash and v2 are identical, and their asset tests pass.
4. **yCRV vs spec rule 3.**
   - Revenue is the veCRV fees only. The incentives are below the line, split between holders and protocol.
   - `expected.py` `ycrv_mix` refuses a mix that is missing, non-numeric, bool, 0, 1 or outside (0,1), and refuses when
     the incentives twin is not 1−mix within 1e-9. Tests cover each case (test_compare.py L1968-1997).
   - The revenue expectation (old `volume` × mix) still ties the new side's `totalSum` to the old gross, so it is not
     circular.

### Strengths
- The design is generic, with no yCRV code. The "whole set counted once" rule gives v1 holder flow, buckets and growth
  exactly, not merely within tolerance.
- The partition proof is required at load time. Partial sets are refused in sum checks, because their factor would move
  with the mix.
- `apportion` keys appear only on apportioned lines, so the other 12 assets' JSON has no new key (and a test proves it).
- The null-mix path lists its reasons, and no zero is ever filled in.
- `expected.py` reuses compare.py's path reader, so a path means the same thing in both tools.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
- **I-1. The below-line-vs-revenue rule can be bypassed through `apportion.by`.** `src/config/incomeStatement.ts:275-278`
  - The rule refuses a below_line `metric` that a revenue line reads. It does not check a below_line line's
    `apportion.by`.
  - Probe: swap the by series on the yCRV-shaped fixture. `ybs_payout`/`treasury` are then apportioned by incentives,
    and `incentives_to_holders`/`incentives_to_protocol` by `gross_fees`, which is the revenue line's metric. The config
    is **ACCEPTED**.
  - This publishes the user-paid share below the line and labels the third-party share "from revenue". No check fails:
    `splitter` resolves whole sets, and `gross_by_sender` is symmetric. Only a nonsense `unreconciled` hints at it.
  - Analyst config proposals pass through the same validation.
  - Fix:
    - Refuse a below_line apportioned line whose `by` is a revenue line's metric (the same message family as L275).
    - Optionally refuse a use-section apportioned line whose `by` is a series no revenue line reads.
    - Add both to tests/config/apportion.test.ts.

#### Minor (Nice to Have)
- **M-1. The partition proof accepts any tolerance and window.** `src/config/incomeStatement.ts:352`
  - `proven` matches only the total and parts. A partition check with `tolerance_pct: 100` or `window_days: 366` is
    ACCEPTED (probed).
  - Fix: require `window_days` 1 (absent) and a small tolerance (e.g. ≤ 0.01 %) on the check that proves the partition.
- **M-2. `gross_by_sender` can never fail on yCRV, and nothing says so.**
  - The three members come from one scan with `count_from` ⊆ the shared allowlist, so the check is true by construction
    up to float rounding. It catches only config drift (an allowlist sender with no by series). It cannot catch the
    brief's "unlisted sender" case, because an unlisted sender is excluded from all three series alike.
  - The circular-check rule (`joined`, schema.ts ~L300) does not treat same-scan members as dependent.
  - Fix: say in the yaml comment or followups note what the check can and cannot catch. Optionally have `joined` flag
    same-scan-key members (that would need an accepted exception for a partition proof).
- **M-3. The exact-equality claims are fixture-dependent.** `tests/assets/ycrv.ingest.test.ts:178` uses
  `toBe(o.value)`, and `assets/ycrv.yaml:154` says "by construction".
  - `flow.ts` accumulates each member's sum separately in log order. On a day with interleaved voter and fee_burner
    transfers, fees + incentives can differ from gross by an ULP.
  - The fixture passes because each day has one sender or exactly representable values. Production is safe: the check
    tolerance is 1e-8 relative and expected.py's is 1e-9.
  - Fix: use a relative tolerance in the test, or comment why exact equality holds for the fixture. Say "within rounding"
    in the yaml.
- **M-4. The default report day before the first fetch is understated.** `src/report/load.ts:107`
  - `lastCompleteReportDay` returns null while a report series has no rows. Between the deploy and the first yCRV fetch,
    `report yield ycrv` with no `--day` has no default day, and that includes `--legacy`, which the staging soak script
    reads.
  - The followups note says only "waits on the new series". The proof uses `--day D`, so it can't see this.
  - Fix: state the ordering in the rollout step: fetch/backfill before the first default-day report or snapshot.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The invariance holds: other assets are byte-identical on synthetic input, and yCRV's legacy, holder flow
and yields are identical on the same input. The schema guard covers the double-read and paid_metric paths. But the new
`by` field opens a path around the below-line-vs-revenue rule that validation accepts silently (I-1). It needs a
one-rule fix plus a test.

## Controller rulings on Task 7b findings (binding)
- I-1 FIX: an apportioned line's `by` decides which side it is on: a holders/protocol/opex apportioned line's `by` must be the metric of a revenue line; a below_line apportioned line's `by` must NOT be any revenue line's metric (and must not be read by any revenue line via derived/of). Swapping the `by` series is refused at load with a clear message; test the swap.
- M-1 FIX: the partition sum check for an apportion set must be daily (window 1) with tolerance_pct <= 1e-6 (or tolerance_abs <= $1); looser is refused.
- M-2 FIX (doc): comment in ycrv.yaml + the followups note that `gross_by_sender` is an invariant guard (one shared scan makes it hold by construction) and only fails if the scan planning changes.
- M-3 FIX: the ingest test compares the per-sender sum to the total with a relative tolerance (1e-12), not exact float equality.
- M-4 FIX (doc): rollout note: until the two new flows are backfilled, yCRV has no default report day for v2 AND legacy output; the rollout backfills them before the first nightly on the new release.
