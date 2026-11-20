# Task 7 Step 1 report: flatdiff `ratio: [lo, hi]` bound (R3 class S)

Status: DONE. Commit `f46f615 tools(flatdiff): ratio bound [lo, hi] (R3 class S)` on BASE 7c8a82f.

## What
- `flatdiff.py`: new optional entry key `ratio: [lo, hi]` (`ENTRY_KEYS`, `BOUND_KEYS = (rel, abs, ratio)`).
  - Validation (`is_ratio`): a list of exactly two finite numbers (bools refused), `0 < lo <= hi`; anything else ->
    `Bad` -> exit 2, message names `ratio`.
  - `entry_holds`: a ratio entry is a bounded entry (only a numeric `changed` holds; added/removed/non-numeric fail).
    Holds when `old != 0` and `lo <= new/old <= hi` (signed quotient: old -10, new -9 = 0.9; a sign change is
    negative and never holds). With `old == 0` it holds only if `new == old`. Combined with rel/abs: the entry holds
    when ANY bound holds (same either-rule as rel/abs); the failure detail lists every failed bound.
  - Docstring updated (format line, either/any rule, signed ratio, old == 0).
- `README.md`: entry keys and the "any bound" rule; new section "R3 (circulating supply): the `ratio` bound" —
  class S uses `ratio` (signed proof ratio +- 0.01, no abs-only entry), class L exact pins, the R43 lesson still binds
  class G growth entries (abs floor AND rel alternative).
- `test_flatdiff.py`: 7 new tests (helper `ratio_code`): within / both edges (99/100, 101/100 exact) / outside / sign
  flip / large ratio pin; negative values; old == 0 (incl. 0.0 vs -0.0 via `entry_holds`); non-numeric, added,
  removed; combined with rel and abs (each direction, all-fail detail, old == 0 + abs); an unbounded overlapping glob
  never relaxes it and value pins still apply; 16 malformed variants exit 2 plus valid `[2, 2]`.

## Tests
- Baseline: `python3 -m unittest discover -s tools/phase3-proof -p 'test_*.py'` -> Ran 78, OK.
- RED (`-k ratio`, before implementation): Ran 8, FAILED (failures=7) — every new test fails with exit 2 (`ratio` was
  an unknown key); `test_malformed_ratio_exits_2` failed on its valid `[2, 2]` case (`2 != 0`).
- GREEN: `-k ratio` Ran 8 OK; full discover Ran 85, OK (78 + 7).

## Files
tools/phase3-proof/flatdiff.py, tools/phase3-proof/test_flatdiff.py, tools/phase3-proof/README.md.

## Self-review
- Absent `ratio` changes nothing: existing r1/r2/r43 allowlists and their tests unchanged and green.
- Edge comparisons are on the float quotient `new / old`; the proof's ±0.01 margin dwarfs rounding, but a pin built as
  exactly the measured ratio (lo == hi) depends on identical float division — use the ±0.01 window as the plan says.

## Concerns
None blocking. Pyright flags `res["diffs"]` subscripts in the new tests (run_cli returns dict|str); same pattern as the
existing tests, runtime-correct.
