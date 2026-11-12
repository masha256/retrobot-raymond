# Task 7 (tools part, Steps 1-2) report

Status: DONE. Commit `61e0425 test(proof): Phase 3 R1 flatdiff + allowlist` on feat/phase3-third-party (parent 35333a6).
I ran nothing against prod, ssh, the network, a prod copy or any `.env`. I did not run vitest (the controller's full
suite was running).

## What

- `tools/phase3-proof/flatdiff.py <old> <new> --allow <allowlist> --asset <a> [--json]`, stdlib only.
  - Flattens each report to `path -> scalar`. Dict keys join with `.`. A list whose elements all have a unique scalar
    `id` becomes `key[id=x]`; any other list is indexed `key[i]`. An empty `{}`/`[]` is a leaf, so a list emptied by
    R1 shows up.
  - Lists every added, removed and changed path with old -> new. Equal numbers are equal (int vs float); a bool is
    not a number.
  - Globs: only `*` is special, and it matches across `.` and `[...]`. Brackets are literal (fnmatch would read
    `[id=unlocks]` as a character class). The glob must match the whole path.
  - Allow rule: at least one applicable entry (the asset's or `*`'s) matches, and **every** matching entry holds.
    - An entry with no bound holds for any change.
    - A bounded entry holds only for a numeric change within `abs` or `rel` (either one, when both are given). With
      old = 0, `rel` holds only for no change.
    - So LIT's unbounded `dilution.*` cannot loosen the rel-0.0007 entry on the unlocks line, and a bounded path that
      turns null fails.
  - `"todo": true` entries are inert placeholders, listed as `WARN todo`. Entries that matched nothing are listed as
    `WARN unmatched`; neither changes the exit code.
  - Exit codes: 0 iff every diff is allowed; 1 otherwise, listing the unallowed paths.
  - Exit 2 for:
    - a missing, empty, whitespace-only or unparseable file;
    - a file that is not an object, or has no `asset` or the wrong `asset`;
    - a malformed allowlist: a missing or empty `reason` or `glob`, a negative or non-numeric bound, an unknown key,
      or a non-bool `todo`. `_` keys are comments.
  - `--json` prints `{ok, asset, diffs[{path, kind, old, new, allowed, why, entries}], unallowed, unmatched, todo}`.
- `tools/phase3-proof/r1-allowlist.json`. The path names come from `IsV2` (src/report/incomeStatement.ts) and from
  the golden v2-report-13.json before R1 (6a1c55f) and at HEAD.
  - cake, uni: `incomeStatement.volume` and `incomeStatement.volume.*`.
  - lit: `incomeStatement.dilution.*` (no bound) and `incomeStatement.dilution.releases[id=unlocks].tokensPerYear`
    at rel 0.0007.
  - pump: the same two paths, both at rel 1e-12.
  - vvv: `incomeStatement.revenue.lines[id=business].crossCheck` and `.crossCheck.*`.
  - Each of the 12 assets: three TODO placeholders (`todo: true`, reason "fill from the first diff run") with
    candidate globs `incomeStatement.provenance.thirdParty*`, `incomeStatement.provenance.sources*` and
    `incomeStatement.flags*`.
  - `"*": []`; no aero key.
- `tools/phase3-proof/README.md`: how to run it, the path syntax, the allowlist format and semantics, and what the R1
  list contains.

## Tests

- RED: `python3 -m unittest tools/phase3-proof/test_flatdiff.py` gave `ModuleNotFoundError: No module named
  'flatdiff'`, `Ran 1 test ... FAILED (errors=1)`.
- GREEN: `Ran 22 tests in 0.035s OK`. The tests cover:
  - identical -> 0;
  - an in-bound change -> 0, where the total's own path also needs an entry;
  - out of bound under an overlapping unbounded glob -> 1;
  - the abs bound, and either bound passing when both are given;
  - a bounded entry refusing a change to null;
  - int vs float, and bool;
  - an unlisted path -> 1;
  - another asset's entries not applying;
  - the `*` entry;
  - volume -> not_measured;
  - an id-keyed element removed and added;
  - VVV crossCheck removed;
  - an unmatched-entry warning (JSON and text);
  - a TODO entry being inert;
  - text output;
  - empty file -> 2 (three variants);
  - missing, unparseable, wrong-asset and non-report files -> 2;
  - 9 malformed allowlists -> 2;
  - the committed allowlist loading, with no entry matching revenue, cost, holderFlow or yields paths.
- `tools/phase2-proof/test_compare.py` still passes (I touched nothing there).
- Smoke run, not a proof: the golden reports before R1 (6a1c55f) vs HEAD for all 13 assets, through the committed
  allowlist.
  - aero, crv, cvxcrv, hype, link, pump, sdcrv, sky and ycrv: 0 diffs.
  - cake, uni: 9 volume paths each, all allowed.
  - vvv: the 3 crossCheck paths are allowed; it fails only on `flags[2]`, `provenance.sources[2]` and
    `provenance.thirdParty[...]`.
  - lit: fails only on `flags[0]` and `provenance.thirdParty[0]` (+ the `[]` leaves).
  - Those failures are the paths the TODO placeholders leave to the controller. The fixtures don't move dilution, so
    the lit/pump dilution entries weren't exercised against real data here, only in the unit tests.

## Self-review / concerns

1. **The LIT dilution change will spread outside `incomeStatement.dilution.*`.** The brief puts holder flow and
   yields off-limits, but a +0.066% unlocks change also moves:
   - `incomeStatement.yields.dilution`
   - `yields.netShareholder`
   - `holderFlow.netOfDilution`
   - `perToken.dilution`
   - `perToken.holderFlow.netOfDilution`
   - `perToken.perTokenFdv.*` (and possibly `multiples`)

   flatdiff will fail on them. I left them unlisted as the brief says; the controller has to decide whether they get
   bounded rel-0.0007 entries.
2. In LIT, only the unlocks line's `tokensPerYear` is bounded, as the brief literally says. Its `yield` and the
   totals (`dilution.pct`, `tokensPerYear`, `supply.*`) sit under the unbounded `dilution.*`. Consider rel 0.0007 on
   `releases[id=unlocks].yield`, `dilution.pct` and `dilution.tokensPerYear` too. Not on `supply.netPerYear`: it is
   a difference of two terms, so its relative change can exceed 0.0007.
3. Lists of strings (`thirdParty`, `sources`, `flags`) are keyed by index, as specified. Removing one item shifts the
   later indexes, so the diff shows changed and removed indexes rather than a clean removal. The globs `...thirdParty*`
   etc. cover all of them, so this is cosmetic.
4. The bare `incomeStatement.volume` and `...crossCheck` entries will normally warn "unmatched". They only match when
   the whole object becomes null or `{}`; harmless.
5. `incomeStatement.checks[id=...]` entries may also change if a removed cross-check had a stored reconciliation
   check. There is no placeholder for that; the first diff run will show it.

## Files

- tools/phase3-proof/flatdiff.py (new, executable)
- tools/phase3-proof/test_flatdiff.py (new)
- tools/phase3-proof/r1-allowlist.json (new)
- tools/phase3-proof/README.md (new)

## Tools fix (R20, R21)

Status: DONE. One commit on feat/phase3-third-party (parent 61e0425). No prod_copy run, no ssh, no network, no vitest
(no TS changes).

### What

- R20, `tools/phase2-proof/prod_copy.py`: the OLD release's migrate of the fresh scratch schema is now
  `db migrate --breaking --json`. 0006 is `-- breaking`, so without the flag a fresh schema was refused
  (`migration_breaking`) before prod was read. The target is always a fresh `p2proof_*` schema, and prod already applied
  0006. The module docstring (`migrate-old.json`), the step-1 comment and `tools/phase2-proof/README.md` (table row and
  run-order comment) say so.
- R21, `tools/phase3-proof/r1-allowlist.json`. The paths were checked against `lit/stored` and `pump/stored` in
  tests/report/golden/v2-report-13.json. The report has no top-level dilution fields: they all sit under
  `incomeStatement.`. The two shapes the brief means are `dilution.releases[id=unlocks]` and
  `yields.dilutionLines[id=unlocks]`, and both are covered.
  - LIT, rel 0.0007 (the reason names the +0.066% change: Lighter's 500M vs DefiLlama's 499.67M):
    - `yields.dilution`, `yields.netShareholder`
    - `holderFlow.netOfDilution`
    - `perToken.dilution`, `perToken.holderFlow.netOfDilution`
    - `perToken.perTokenFdv.*`: one glob over every leaf under it, including revenue, grossProfit and holderFlow.total
    - `dilution.pct`, `dilution.tokensPerYear`
    - `dilution.releases[id=unlocks].yield`
    - `yields.dilutionLines[id=unlocks].tokensPerYear`, `yields.dilutionLines[id=unlocks].yield`
  - LIT, abs 100000: `dilution.supply.netPerYear`.
  - PUMP: the same 12 paths at rel 1e-12. That includes netPerYear, which `dilution.*` already bounds at rel 1e-12.
  - All 12 changed assets: a `incomeStatement.checks*` todo placeholder.
  - The `_comment` and tools/phase3-proof/README.md are updated.

### Tests

- RED: `Ran 120 tests ... FAILED (failures=2)`. Both new tests failed:
  - the prod_copy argv lacked `--breaking`;
  - LIT +0.066% was unallowed on the 9 holder-flow/yields/perToken paths.
- GREEN: `/usr/bin/python3 -m unittest tools/phase2-proof/test_prod_copy.py tools/phase3-proof/test_flatdiff.py
  tools/phase2-proof/test_compare.py` gives `Ran 120 tests ... OK`.
  - `test_the_old_release_migrates_the_fresh_scratch_schema_with_breaking` pins the full argv, cwd and ORION_HOME. A
    fake `run` returns rc 1, and the fake sql_ro/psql assert they are never called.
  - `test_the_committed_allowlist_bounds_lit_dilution_derived_fields` uses the golden `lit/stored` report with every
    dilution-derived field scaled:
    - ×1.00066 gives exit 0, and every moved path passes through a bounded entry;
    - ×1.001 gives exit 1, with exactly the 13 rel-0.0007 paths unallowed (netPerYear +12k stays inside abs 100000);
    - every PUMP path has a rel 1e-12 entry.
- Smoke: golden `lit/stored` and `pump/stored` vs themselves through the allowlist give 0 diffs, exit 0.

### Concerns

1. `dilution.supply.addedPerYear` (it equals tokensPerYear), `supply.netPct` and `dilution.emissionsPerYear` are still
   only under LIT's unbounded `dilution.*`. R21 doesn't name them; bound them if wanted.
2. `perToken.perTokenFdv.*` at rel 0.0007 also allows a ≤0.07% move in perTokenFdv revenue, grossProfit and
   holderFlow.total, which the unlock change should not touch. That is the brief's "every numeric under it". Exact
   per-path entries would be tighter.
3. `yields.netShareholder` and `holderFlow.netOfDilution` are differences of two terms. For real LIT they move about
   0.066% × dilution/(dilution − flow) ≈ 0.067%, close to the 0.07% bound. If the copy's holder flow is a larger share
   of dilution than in the golden, they could exceed it, and flatdiff will then fail loudly.

## Fix round 1

Status: DONE. One commit on feat/phase3-third-party (parent f0074f9). I ran no prod_copy, cleanup, ssh, network,
database, npm or vitest (no TS changes), and did not touch dist/. The controller addendum (from the prod-copy run) is
in the same commit.

### What

- I-1, `r1-allowlist.json` (LIT): the unbounded `incomeStatement.dilution.*` is gone. Every dilution path is now an
  exact entry:
  - `dilution.releases[id=unlocks].id`, `dilution.emissionsPerYear` and `dilution.supply.burnedPerYear` at abs 0;
  - `dilution.supply.addedPerYear` at rel 0.0007;
  - `dilution.supply.netPct` at abs 0.0001.
  
  As a result, no LIT entry matches a new or removed `releases[...]` element. PUMP keeps `dilution.*` at rel 1e-12, a
  bounded entry, so an added or removed line fails there too.
- M, `flatdiff.py` path collisions:
  - In keys, a backslash, `.` and `[` are escaped with a backslash (`{"a.b":1}` gives `a\.b`).
  - Number ids are tagged `#` (`[id=#1]`). String ids escape a backslash, `]` and a leading `#`. `_id_keyed` dedups on
    that step string.
  - As a backstop, a leaf whose path is already taken raises `Bad` (exit 2).
  - No golden report path contains an escape (tested), so the committed globs are unchanged.
- M, strict allowlist:
  - `object_pairs_hook` refuses a duplicate key anywhere in any input (exit 2). That covers allowlist assets, keys
    inside an entry, and report keys.
  - A glob that is blank or starts with `*` exits 2. This covers `*`, `**` and `*.x`.
- M, `test_prod_copy.py`: the old-release migrate test now runs with inherited `ORION_DATABASE_URL`, `ORION_DB_SCHEMA`,
  `ORION_ENV_FILE` and `ORION_HOME` (mock.patch.dict). It asserts:
  - `ORION_ENV_FILE == <P>/old/.env`;
  - `ORION_DATABASE_URL` and `ORION_DB_SCHEMA` are absent;
  - the only ORION_* keys are ORION_ENV_FILE and ORION_HOME.
  
  prod_copy already strips ORION_*, so prod_copy.py is unchanged.
- Task 8 concern 1, `docs/ops/deploy.md` (the verb-reference comment): the comment now reads "every metric's rows to
  ONE file per call, `<asset>-<first metric>[+N]-<UTCstamp>.json`". This matches `exportFileName` in src/db/purge.ts.
  The step-5 text (:524-526) was already right.
- Controller addendum:
  1. LIT's four net-of-dilution fields each have their own rel 0.0008 entry, with reason "net = holder flow -
     dilution ... ~0.073%". The fields are `holderFlow.netOfDilution`, `perToken.holderFlow.netOfDilution`,
     `perToken.perTokenFdv.holderFlow.netOfDilution` and `yields.netShareholder`.
     - LIT's `perToken.perTokenFdv.*` (rel 0.0007) is replaced by exact `perTokenFdv.dilution` (rel 0.0007) and
       `perTokenFdv.holderFlow.netOfDilution` (rel 0.0008). Every matching entry must hold, so if the glob had stayed,
       its rel 0.0007 would still have failed the 0.000729 move.
     - This also closes review Minor 5 for LIT: perTokenFdv revenue, grossProfit and holderFlow.total no longer have
       an entry.
  2. All todo placeholders are deleted.
     - LIT gets exact `incomeStatement.flags`, `flags[0]`, `provenance.thirdParty` and `provenance.thirdParty[0]`.
     - VVV gets exact `flags[3]`, `provenance.sources[2]`, `provenance.thirdParty`, `provenance.thirdParty[0]` and
       `provenance.thirdParty[1]`.
     - The other 10 assets have no provenance, flags or checks entry.
  3. The `flatdiff.py` module docstring is now `r"""..."""`. My escape note had introduced `\``, an invalid escape;
     HEAD compiled clean.
- README and allowlist `_comment` updated to match.

### Tests

- RED, fix-round findings:
  - The run gave `Ran 127 tests ... FAILED (failures=6)`. The six failures were bare-star glob (0 != 2),
    dotted-key collision, duplicate asset key (1 != 2), id 1 vs "1" collision, LIT dilution probes (burnedPerYear -> 0
    exited 0 via `lit[0] no bound`) and the holder-flow match.
  - The prod_copy env pin passed on unchanged code, so I checked that it bites by mutation on a scratch copy (never
    the real file). With the strip changed to `env = dict(os.environ)`, the test FAILS
    (`'ORION_DATABASE_URL' unexpectedly found`).
- RED, addendum:
  - `-W error` compile of flatdiff.py raised `SyntaxError: invalid escape sequence '\`'`. I fixed this before writing
    `test_flatdiff_compiles_without_warnings`, so that test was never seen failing.
  - The run gave `Ran 130 ... FAILED (failures=2)`: net-of-dilution rel 0.0007 != 0.0008, and a todo still present.
- Expected updates to existing tests:
  - The R21 ×1.001 test now also lists `supply.addedPerYear` as unallowed, because it is newly bounded.
  - `test_the_committed_allowlist_loads` now asserts that no todo is left.
- GREEN: `/usr/bin/python3 -m unittest tools/phase2-proof/test_prod_copy.py tools/phase3-proof/test_flatdiff.py
  tools/phase2-proof/test_compare.py` gives `Ran 130 tests ... OK`. It is also clean under `-W error::SyntaxWarning`.
- The reviewer's probes are all exit 1 on golden `lit/stored`:
  - burnedPerYear -> 0, -> null, ×(1+1e-12);
  - emissionsPerYear ×2 and +1;
  - addedPerYear ×1.001;
  - netPct +0.0002;
  - a new `releases[id=x]` 9e9 line;
  - the unlocks line removed;
  - a new dilution field.
  
  addedPerYear +0.066% with netPct +5e-5 exits 0.
- Smoke (not a proof): golden reports before R1 (6a1c55f) vs HEAD through the committed allowlist.
  - 12 assets exit 0.
  - VVV exits 1 on `incomeStatement.flags[2]` only. The golden fixture's flag index differs from prod's `flags[3]`
    (the addendum's exact path); prod is what the proof runs against.

### Concerns

1. The duplicate-key refusal also applies to the two reports, not only the allowlist. A JS `JSON.stringify` report
   cannot carry one, so this only fails closed.
2. `docs/superpowers/notes/2026-11-12-orion-phase3-followups.md:16` (and the historical plan, :48) still say
   `<asset>-<metric>-<UTCstamp>.json`. I left both alone: they are outside the dispatch's file list.
3. The exact index entries (`flags[0]`, VVV `flags[3]`, `sources[2]`, `thirdParty[0..1]`) are positional. If prod's
   lists shift before the proof is rerun, flatdiff fails loudly; it does not false-pass.
