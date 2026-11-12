# Final fix wave re-review (ee295f6..c0e4750)

Read-only. Sources: final-findings.md (rulings incl. R27), final-review.md, final-fix-report.md, the diff file, and
`git show c0e4750:` of scripts/provision/files/orion-remote, src/report/load.ts, src/report/incomeStatement.ts,
src/levels/levels.ts, src/cli/commands/data.ts, src/db/observations.ts, src/provenance/origin.ts. I did not run any
tests: reading the code raised no doubt that the reported 134/134 run doesn't already answer. The real-run flatdiff
output in the fix report (all 12 exit 0, 9 entries `value pinned`) matches the committed pins.

## Finding verdicts

- **I-1: release block reorder.** ADDRESSED.
  - Step 3 (flatdiff of the 12 + AERO `cmp`) runs right after the switch and before any refresh
    (docs/ops/deploy.md:500-520).
  - Step 5 refreshes, runs `data show lit|pump unlocks_next_year` with the expected values and citations, and saves
    `mid/` (:532-555).
  - Step 9 `cmp`s every report, AERO included, against `mid/` (:596-606), after step 7 and again after 8(a).
  - The nightly-slot warning is at :469-473.
  - The step-3 claim that LIT/VVV flags and provenance match before the refresh holds. `thirdParty` and `sources`
    cover only revenue, use and below-line metrics, never the dilution metric (incomeStatement.ts:924-965), so the
    old third-party unlock row can't add a flag.
- **I-2: LIT abs bounds, date-safe.** ADDRESSED.
  - r1-allowlist.json:91 sets `netPerYear` abs 120000 and :116 sets `netPct` abs 0.00013. Both reasons name the
    "10-12 tranche" range and "2027-01-28".
  - `test_the_committed_lit_bounds_hold_for_10_to_12_tranches` (test_flatdiff.py:980-1019) checks that 10, 11 and
    12 tranches pass, that 14 fails on exactly these two paths, and that the reasons carry the strings.
  - Note: with I-1's reorder, step 3 sees no LIT unlock delta, so the release itself never uses these bounds. They
    matter only for the proof runs.
- **I-3 / R27: orphan-only default purge; gated LIT/PUMP unlock purge.** ADDRESSED.
  - Steps 6 and 7 cover only the four orphan pairs (deploy.md:557-576).
  - Step 8 is a separate step, "Gated, only on Mike's pick", with (a) purge now (D6, about 4 weeks of null past-day
    dilution) and (b) keep the rows until R8 (:577-595). It states the cost: 31/29 rows, the nulled fields, and that
    the loss is permanent.
  - The followups note's "Open decisions (Mike)" section (:99-106) and R27 (:95) say the same.
  - The export-file count (4, +2 on (a)) and the dead-cursor carry (only on (a)) are adjusted.
- **I-4: UNI/VVV/YCRV default-day evidence.** ADDRESSED. The followups note's Proof section (:186-191) records
  uni/vvv/ycrv as 2026-11-11 / 2026-11-11.
- **Minor 1: value pins.** ADDRESSED.
  - Validation: flatdiff.py:130-134 checks `absent` (it must be "old" or "new", and conflicts with a pin on that side
    exit 2).
  - `pin_fails` (:202-214) runs before any bound in `entry_holds` (:217-221). It compares with `same()`, so `[]` is
    not `{}` and null is a real pin.
  - Empty-list leaves are real `[]` values (flatten :170-180), so the `"new": []` pins compare correctly.
  - All 9 LIT/VVV entries carry the real-run values (r1-allowlist.json:119-143, :237-266), and
    `test_the_committed_lit_vvv_string_entries_are_value_pinned` pins them.
  - The README documents the positional dependence (README.md "Positional paths").
- **Minor 2: followups note and plan.**
  - ADDRESSED. R21/R22 are marked superseded (:79-82), R23-R27 are added (:83-97), and the Proof section is filled
    (:174+).
  - The export name `<asset>-<first metric>[+N]-<UTCstamp>.json` (one file per call) is fixed in the note (:17,
    :162) and in the plan (:48).
  - R6 and P1 are fixed. No `<metric>-<stamp>` text and no "see controller commit" text is left.
- **Minor 3: R25 stage smoke backfill.** ADDRESSED as step 4 (deploy.md:522-531).
  - It has the exact verb, `jobs` until done, the Slack start/done lines, the deferral window, the failure path, and
    "Not on prod". The closing paragraph says prod runs without step 4.
- **R11 caveat.** ADDRESSED. deploy.md:450-452 and followups R11 (:55-58) cover the single worker: the hourly `levels`
  job (watch posts, levels snapshot) and the prod `ORION_DEADMAN_URL` ping.

## Extra checks

1. **Verb syntax at c0e4750 (orion-remote).** All OK.
   - `status`, `logs 30|50`, `jobs --since <iso>`: ISO_RE, :400-402.
   - `report yield <a> [--day $d]`: DAY_RE, with `--json` appended so the saved files are JSON, :405-409.
   - `data show <a> <metric>`: :420-422.
   - `data purge <a> --metrics k1,k2 [--source-type third_party] [--yes]`: comma list via `metric_list`, :283-293;
     `third_party` is in RUNGS; `--yes` is a switch, :426-432.
   - `job run-now refresh <a>` and `job run-now backfill hype --metrics flow_usd.af_buys_direct --backfill-days 3`:
     :495-510.
   - Quoting: no command needs quoting through ssh. Metric names match `[a-z0-9_.]`, `$d` expands locally to
     yyyy-mm-dd, and shlex splits the rest cleanly (:211-248).
   - The R27 gate holds: the unlock purges appear only in step 8(a). The `--yes` pair runs "on his go" after Mike's
     pick, and prod runs steps 7 and 8 only on Mike's go (:608-610).
2. **I-3 narrowing (only days whose asOf ends before the refresh): correct.**
   - load.ts:202 sets asOf to the end of `d+1`, and :205 `latestLevel(rows, asOf)` takes the newest row at or before
     asOf.
   - For d = deploy day - 1, asOf is the end of the deploy day. It holds step 5's schedule row, which is newer than
     that day's third-party row, so the purge is neutral (this is what the rehearsal showed).
   - For d ≤ deploy day - 2, there is no schedule row inside asOf, so dilution goes null.
   - The review's "every earlier day" overstated it by one day. The implementer's "two or more days before the deploy
     day" (deploy.md:579) and the note's "asOf ... before the deploy-day refresh" (:102-104) are the accurate form.
3. **Smoke backfill after the step-3 check: the right call.**
   - Putting it literally "right after the switch" would let its 3-day re-read of `flow_usd.af_buys_direct` move
     HYPE's step-3 flatdiff.
   - After step 3 it is still before any refresh or purge, and it holds the worker only ahead of the step-5 refreshes,
     which just wait.
   - I accept the deviation from the ruling's wording. One gap remains, Minor N2 below.

## New breakage in the fix diff

Critical: none. Important: none.

Minor:
- **N1.** The step-5 check (deploy.md:543-548) asks for "source type disclosure, method disclosed", but
  `data show ... --json` doesn't print either field.
  - It prints `Observation` rows: `source` (onchain|api|manual), `sourceDetail`, `citationUrl`, `quotedText`
    (src/db/observations.ts:9-24, :150-165).
  - The schedule row reads `source: "manual"` (origin.ts:65-66: disclosed, no adapter locator).
  - The step's stop condition (value or citation) can be checked, but those two fields can't. Fix: say "`source`
    manual, `citationUrl` x.com / Blockworks", or check source_type/method with `sql-ro` on prod.
- **N2.** Step 4 permits "let it wait" while the backfill is deferred (:529-530).
  - A backfill still queued when step 5 saves `mid/` can run before step 9.
  - Its re-read of HYPE's last 3 days can then make HYPE's step-9 `cmp` differ, a false STOP (it fails closed).
  - Fix: "do not start step 5 until the backfill is `done`, or run step 4 after step 9".
- **N3.** The nightly guard is imprecise.
  - The warning (:469-471) says a nightly writes levels "inside the step-0 reports' asOf". For the usual step-0 day
    (deploy day - 1, asOf = end of the deploy day), the next slot (deploy day + 1) falls outside asOf. Only re-read
    flow rows can move. The wording is conservative and harmless.
  - The "re-save `mid/` if a nightly passed" instruction sits only before step 7 (:575-576). Step 8(a) can come later
    on Mike's pick, and it gets no matching line.
- **N4.** Step 9's rationale holds only for some step-0 days.
  - It says "the step-0 day, whose asOf includes step 5's schedule row" (:596-597). That holds only when step 0's day
    is deploy day - 1. If step 0 ran before that day's nightly slot (day = deploy day - 2), LIT/PUMP's step-9 `cmp`
    after 8(a) differs by design (the I-3 nulls). That fails closed, with no explanation.
  - 8(b)'s reason, "step 5's refresh already moved `latest_levels`" (:594-595), is wrong: reports read observations
    (load.ts:203-205), not `latest_levels`. The actual reason is that the schedule row is the newest row at or before
    asOf. "From the deploy day on" also understates the safe range: deploy day - 1 is safe too.

## Out-of-scope observations

- deploy.md:459 "after step 1 above" points to the section's earlier list (the orion-host.sh re-run). The block now
  has its own step 1, so the reference reads ambiguously. This predates the fix wave.

## Verdict

**Fix round: All findings addressed, no new Critical/Important breakage.** 4 new Minors (N1-N4), all docs wording in
the release block, all fail-closed or cosmetic.
