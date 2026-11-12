# Final fix wave report (BASE ee295f6 -> c0e4750)

Status: DONE. One commit, c0e4750 `fix: final-review wave: release block order + gated unlock purge; date-safe LIT
bounds; value-pinned allowlist strings; followups note complete`. Docs + proof tooling only; no src/TS change.

## What, per finding

- **I-1 (deploy.md Phase 3 R1 release block, reordered):** 0 before/ reports; 1 deploy; 2 switch check; 3 the 12-asset
  flatdiff + AERO `cmp` right after the switch, before any refresh (notes that LIT/PUMP unlock entries warn unmatched
  there; pinned flags/provenance entries match; positional index re-derivation); 4 stage-only smoke backfill (R25);
  5 refresh LIT/PUMP, `data show lit|pump unlocks_next_year` checks (138,888,888.89 at 10 tranches, plus the 11/12-tranche
  values; disclosure/disclosed; x.com / Blockworks citations; pump 82,500,000,000), save `mid/`; 6/7 orphan dry runs and
  `--yes` on Mike's go; 8 gated LIT/PUMP unlock purge; 9 `cmp` every report against `mid/` (after 7, again after 8(a)).
  Warning added above the block: no scheduled nightly slot (stage 02:45Z, prod 00:45Z) between step 0 and step 3;
  step 7 says to re-save `mid/` if a nightly passed since step 5.
- **I-2:** LIT `supply.netPerYear` abs 120000, `supply.netPct` abs 0.00013. Each reason names the 10-12 tranche range,
  gives the per-tranche figures and says "valid ... through 2027-01-28". The `_comment` and README were updated.
- **I-3 / R27:** the block purges only the 4 orphan pairs by default. Step 8 is gated "only on Mike's pick: (a) purge now
  (D6, past-day dilution null for ~4 weeks) or (b) keep the third_party rows until R8". It states the cost: rows
  2026-10-16..deploy day (31/29), and nulls for days whose asOf ends before the refresh. The followups note now has an
  "Open decisions (Mike)" section carrying the same text. The export-file count is 4 per env (+2 on (a)), and the
  dead-cursor carry applies only on (a).
- **I-4:** the uni/vvv/ycrv 2026-11-11/2026-11-11 default-day evidence is recorded in the followups Proof section.
- **Minor 1 (flatdiff value pins):** an entry may carry new optional keys `old`, `new` (any JSON value; compared like
  `same()`: numbers by value, everything else by type and value, so `[]` != `{}` and `null` is a real pin) and
  `absent: "old"|"new"`. A pin is checked before any bound, and both must hold. An `absent` that names a side which also
  carries a value exits 2. All 9 LIT/VVV flags/provenance entries are pinned to the real-run values. The README documents
  the positional dependence: re-derive the index from the env's `before/<a>.json`, keep the pin; flatdiff fails closed.
- **Minor 2 (followups note):** R21/R22 now read "superseded by R24 / ee295f6" (R21 also notes the I-2 widening).
  Added: R23-R27. Proof section filled from the Task 7 RESULTS block + I-4 + the final flatdiff + deviations (D-91 not
  run, "before" from the old release on the copy, Blockworks quote not checked verbatim). Also fixed:
  - P1 now names R9 and the unfinished-nightly guard;
  - P2 export name is `<asset>-<first metric>[+N]-<UTCstamp>.json`, one file per call;
  - R6 no longer overclaims the backfill rehearsal;
  - R11 gains the worker caveat.
  Two new carried items: purge-export retention (copy off venus) and the anomaly sweep (review Minors 5/6). The plan's
  P2 line uses the same export-name wording.
- **Minor 3 (R25):** the stage smoke backfill is step 4. It sits after the report check, so its re-read rows can't move
  HYPE's comparison. It covers `jobs` until done, the Slack start/done lines, and the deferral window.
- **R11 caveat:** the deploy.md sizing bullet now says the single worker holds the hourly `levels` job (watch posts,
  levels snapshot) and the prod dead-man ping.

## Tests (TDD)

New tests:
- `test_old_new_absent_pin_the_value`
- `test_malformed_pins_exit_2`
- `test_the_committed_lit_vvv_string_entries_are_value_pinned`
- `test_the_committed_lit_bounds_hold_for_10_to_12_tranches`: real-run per-tranche old/new tokens, LIT burn and total
  supply. 10, 11 and 12 tranches pass; 14 fails on exactly netPerYear + netPct; the reasons must name "10-12 tranche"
  and "2027-01-28".

The existing netPct abs assert was updated to 0.00013.

RED (before implementation): `Ran 37 tests ... FAILED (failures=5)`:
- malformed_pins (2 != 1);
- old_new_absent_pin (2 != 0: unknown keys);
- outside_the_unlocks_line (0.0001 != 0.00013);
- 10_to_12_tranches (11 tranches: netPct + netPerYear unallowed);
- value_pinned ({} != {'absent': 'old', 'new': []}).

GREEN: `/usr/bin/python3 -W error::SyntaxWarning -m unittest tools/phase3-proof/test_flatdiff.py
tools/phase2-proof/test_prod_copy.py tools/phase2-proof/test_compare.py` -> `Ran 134 tests ... OK` (baseline 130 + 4).

## flatdiff on the real copy outputs (committed allowlist at c0e4750)

```
cake exit=0 OK cake: 9 differing path(s), 9 allowed, 0 not allowed
crv exit=0 OK crv: 0 differing path(s), 0 allowed, 0 not allowed
cvxcrv exit=0 OK cvxcrv: 0 differing path(s), 0 allowed, 0 not allowed
hype exit=0 OK hype: 0 differing path(s), 0 allowed, 0 not allowed
link exit=0 OK link: 0 differing path(s), 0 allowed, 0 not allowed
lit exit=0 OK lit: 20 differing path(s), 20 allowed, 0 not allowed
pump exit=0 OK pump: 16 differing path(s), 16 allowed, 0 not allowed
sdcrv exit=0 OK sdcrv: 0 differing path(s), 0 allowed, 0 not allowed
sky exit=0 OK sky: 0 differing path(s), 0 allowed, 0 not allowed
uni exit=0 OK uni: 6 differing path(s), 6 allowed, 0 not allowed
vvv exit=0 OK vvv: 8 differing path(s), 8 allowed, 0 not allowed
ycrv exit=0 OK ycrv: 0 differing path(s), 0 allowed, 0 not allowed
aero cmp identical (no allowlist entry)
```

On these runs, all 9 LIT/VVV flags/provenance diffs show `value pinned`. I also ran the reviewer's probes on the real
outputs, with temp files in $TMPDIR that I removed afterwards. Each now exits 1:
- LIT `flags[0]` replaced;
- LIT `thirdParty[0]` replaced;
- a new VVV flag at `[3]`.

## Self-review / concerns

- Step 4's placement departs slightly from the ruling. The ruling says "right after the stage switch"; I put it right
  after the post-switch report check (step 3). Run any earlier and the backfill's 3-day re-read of
  `flow_usd.af_buys_direct` could move HYPE's step-3 comparison. It still comes before any refresh or purge.
- Step 5 lists 11- and 12-tranche LIT values (152,777,777.78 / 166,666,666.67) that I computed as 500M/36 × n. They are
  not observed values.
- Step 8 narrows the affected days to "asOf ends before the step-5 refresh (in practice two or more days before deploy
  day)". This follows from load.ts asOf = end of d+1, which the review states. The review's wording was "every earlier
  day".
- Process: my first flatdiff re-run wrote 12 text files to the workspace's `phase3-proof/r1/` (next to out/, not inside
  it). I deleted them right away. Nothing in out/ was touched.
- Not run: vitest/typecheck, because no TS changed.
