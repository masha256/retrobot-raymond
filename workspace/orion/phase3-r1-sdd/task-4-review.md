# Task 4 review: `schedule.unlocks_next_year` (e88130f..69caa3f)

### Spec Compliance

- ✅ Spec compliant. Every file in the brief has its hunk: schedule.ts (new), scheduleUnlocks.test.ts (new), types.ts:377 (`citation?`), run.ts:360-374, registry.ts:150, sourceTypes.ts:511, generate.ts:951-954,977. The interface matches: `needsRpc: false`, strict params, the (now, now+365d] window, tranches `tokens/count` on `addMonthsClamped` dates, linear `tokens/years` x overlap/365d clamped to [start, start+years x 365d], the detail format `<label> <x>M, ...; cited <url>`, and `citation` on the level. The row is `disclosed`/`disclosure` with `citation_url`/`quoted_text` set (test :231-246).
- Extra files are justified and needed: `dates.ts` (a verbatim move from lit.ts), `locator.ts:101` (method `disclosed` for a disclosure-rung adapter) and `origin.ts:66` (read-back `api`). Without these the rows would be `measured`, or the origin guard would refuse them. Step 1 was skipped per R5. Its fixtures match citations.md verbatim.
- The linear test pins 180 days (test :107-115) under ruling R16. The derivation is asserted in the test. ✅
- ⚠️ Cannot verify from the diff: prod/staging rows. The code-path proof under risk 1 covers every writer in the tree. A one-line SQL check on the prod copy would close it: `SELECT count(*) FROM observations WHERE method='disclosed' AND locator ? 'adapter'` should return 0.

### Named risks

1. **Value equality of the other adapters and assets: REFUTED (no change).**
   - `methodOfSource` (locator.ts:99-103): the new branch fires only when `ADAPTER_SOURCE_TYPES[name] === 'disclosure'`, and only `schedule.unlocks_next_year` has that rung (sourceTypes.ts:494-519). The test at :66 pins `measured` for every other registered adapter. Its only production caller is `fetchedProvenance` (locator.ts:122). The old `backfill.ts` (gone at 1ce53dc) used it when adapters were all measured.
   - `originOf` (origin.ts:66): it changes read-back only for `method='disclosed'` rows whose locator has a string `adapter`. I checked every writer of a disclosed row:
     - `disclosedProvenance` (types.ts:104-112: keys `citation_url/approved_by/approved_at/proposed_by`) is used by `data set` (data.ts:120), the agent ledger (ledger.ts:243), and proposal approval (proposals.ts:112).
     - `confirmObservation` (observations.ts:290-293) keeps the stored method and locator, and only adds `approved_*`.
     - The pre-v2 backfill (1ce53dc^:src/provenance/backfill.ts:162-163, 207-208: `{citation_url,...}` / `{note, legacy_seed}`) and constants (locator.ts:59 `{config_path, note}`, which were `api` already) are unaffected.
     - None carries `adapter`, so no existing row's origin changes. Adapter rows written before this commit are all `measured` and never reach the `disclosed` branch.
     - The other `originOf` readers (checks/evaluate.ts, db/observations.ts) use the same function. No SQL re-implementation exists (grepped the src/tools CASE forms).
   - run.ts:362: `uncited` needs `disclosed && disclosure`. Only the new adapter's level can produce that, so other readings are unaffected. The spread at run.ts:373 adds keys only when `v.citation` is set, so other insert inputs are byte-identical.
   - No YAML was touched, so the 13 config hashes and report bytes are unchanged (the full suite of 1735 is green per the report).
2. **Window arithmetic: CORRECT.**
   - Tranches are counted with `t > nowMs && t <= endMs` (schedule.ts:109). I mutated it to `[now, end)` in my own worktree: the month-end test (:136-140, 800 vs 400) fails. The left edge is therefore pinned, and with it the right edge via :96-105 (see M1).
   - Linear: schedule.ts:115-121 clamps to [max(now,start), min(end, start+years x 365d)], floored at 0.
   - Leap years: the window and vest use fixed 365 d (as lit.ts:199 does). The 180-day case crosses 2028-02-29 and is pinned.
   - Month-end clamping: `addMonthsClamped`/`isoDate`/`intIn` in dates.ts:2-23 match the removed lit.ts lines token for token. Only `export` and the `: boolean` annotation are added, and lit.ts:196,202 now imports them.
   - PUMP: the overlap is exactly YEAR_MS, so 150e9/3 + 97.5e9/3 = 50e9 + 32.5e9, exact in binary (`toBe(82.5e9)`, :89).
   - LIT: tranches Jan 29 to Oct 29 2027 give 10 (Nov 29 falls after the window end), so (260e6/36)·10 + (240e6/36)·10 ≈ 500e6/36·10 to within 1e-6 (:83).
3. **Strict params refused at load: CONFIRMED.**
   - `validateScheduleUnlocksParams` (schedule.ts:87-101 and 58-85) refuses: unknown keys at every level, a missing citation, a non-http url, an empty quote or one over 500 chars, tokens that are not finite or ≤ 0, both or neither of tranches/linear, bad dates (via `isoDate` round-trip), every_months outside 1..12, count outside 1..120, and years outside (0,50].
   - It is wired through `adapterParamIssues` (load.ts:38-48) for primaries and cross-checks. Agent config-proposal filing calls `parseAssetObject` (agent/tools/write.ts:306) and approval calls `parseAssetYaml` (app/proposals.ts:183), so both refuse.
   - `run` re-validates and throws (schedule.ts:128-129).
   - Tests: :147-195, plus the load-time test at :197-203.
4. **The disclosure CHECK and latest_levels: NO UNCITED PATH.**
   - The level path has three layers: the run.ts:362 guard (it fails the read and writes nothing, test :248-269), `checkedProvenance` (observations.ts:143), and 0006's `observations_disclosure_citation` CHECK (`source_type <> 'disclosure' OR citation_url IS NOT NULL OR code_version='pre-v2'`).
   - The adapter returns only `level`, so the steps, flow and payment writers are unreachable.
   - latest_levels has no citation column or CHECK. `runLevels` writes it via a dry-run `fetchAsset` (the guard still applies), and its locator carries `params.citation` (test :271-278).

### Strengths

- The params validation is tight and gives precise messages, with an exact-message test for each refusal, including the load path.
- The guard in front of the DB CHECK turns a would-be `citation_required` throw into a clean failed read. The test proves nothing is written.
- `adapterOrigins.test.ts:858` now uses the writer's real `methodOfSource`, so the origin invariant covers the new rung without a special case.
- The date helpers were moved verbatim rather than re-implemented, and lit.ts behaviour is unchanged.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)
- **M1** tests/ingest/scheduleUnlocks.test.ts:96-105: "tranche on now + 365d counts; one on now does not" passes under the swapped window `[now, now+365d)` too. I checked by mutating schedule.ts:109: this test stays green and only the month-end test at :136 fails. The Review Focus test does not isolate what its name claims. Fix: use a single-tranche schedule (count 1). With now = the tranche date, expect 0; with now = tranche − 365d, expect the full amount.
- **M2** src/provenance/origin.ts:66: the new `api` branch keys on any `disclosed` row with `locator.adapter`, not on `sourceType === 'disclosure'` as well. It is safe today (see risk 1). Tightening it to `p.sourceType === 'disclosure' && typeof p.locator?.adapter === 'string'` would match the comment and narrow future surprises.
- **M3** src/ingest/adapters/schedule.ts:107-110 and src/ingest/adapters/lit.ts:201-204 carry the same tranche-count loop. A `tranchesInWindow(first, every, count, now, end)` in dates.ts would share it. This is low priority if Task 6 retires `lit.unlocks_next_year`.
- **M4** Validation gaps:
  - Coverage: no test for `years > 50`, `tokens: NaN/Infinity`, `tranches: null`, or a non-object `schedules[i]`.
  - Code: duplicate `label`s are accepted, which makes the detail ambiguous (`team 1M, team 2M`).
- **M5** schedule.ts:139: detail formatting prints billions as `50000.00M` and `32500.00M`. This is cosmetic, but the detail is user-facing (sources line).
- **M6** tests/ingest/scheduleUnlocks.test.ts:251-266: the citation-less test monkeypatches the shared registry's `def.run`. It is restored in `finally`, but it mutates module-global state that other tests in the same worker read. An injected adapter or harness hook would be cleaner.
- **M7** src/ingest/run.ts:336-347: the `schedule_steps` path has no `uncited` guard. A future disclosure-rung adapter that returns steps would throw `citation_required` out of `insertObservation` instead of `markFailed`. This is hypothetical today, because the only disclosure adapter returns a level.

### Checks run

- I made a detached worktree at 69caa3f (now removed) and ran `npx vitest run tests/ingest/scheduleUnlocks.test.ts tests/provenance/adapterOrigins.test.ts --maxWorkers=1`: 26/26 passed with clean output.
- Mutation `t >= nowMs && t < endMs` at schedule.ts:109 gave 1 failure (the month-end test only), which is the basis for M1. I reverted it before removing the worktree.

### Assessment

**Task quality:** Approved

**Reasoning:** The adapter's arithmetic, its strict loading and the citation enforcement are correct and covered. The reader-side changes to `methodOfSource` and `originOf` cannot reach any row that existing writers produce. What remains is test-precision and polish nits.
