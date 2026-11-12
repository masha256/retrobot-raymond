# Task 7 tooling review (35333a6..811d33f: 61e0425 flatdiff + allowlist, 811d33f prod_copy --breaking + R21 bounds)

Line refs: `D:<n>` = line in review-35333a6..811d33f.diff; file:line = the file at 811d33f.

### Spec Compliance

- ✅ Spec compliant for Steps 1-2 and the tools commit of Step 8, with rulings R20/R21/R22 applied.
  - Step 1: `flatdiff.py <old> <new> --allow --asset` flattens, prints every differing path, exit 0 only if every path
    matches an applicable glob and every matching entry's bound holds (flatdiff.py:154-202, `entry_holds`/`diff`). The tests cover a
    match (test_flatdiff.py:100), out-of-bound (:112) and an unlisted path (:137).
  - Step 2: cake/uni `volume` + `volume.*` (r1-allowlist.json:10-17, 354-361); lit `dilution.*` + unlocks tokensPerYear
    rel 0.0007 (:128-136); pump the same paths at rel 1e-12 (:219-...); vvv business crossCheck (:384-391); 12 assets
    have todo placeholders; no aero key; `"*": []`.
  - R20: `db migrate --breaking --json` only on the OLD release's migrate of `<P>/old` (prod_copy.py:244). R21: all 11
    rel-0.0007 paths plus netPerYear abs 100000 and the checks* placeholder are there; PUMP mirrors them.
  - Step 8 (tools part): commit subject `test(proof): Phase 3 R1 flatdiff + allowlist` (61e0425).
- ⚠️ Cannot verify from the diff: the "all 12 provenance/cross-check listing paths ... enumerated from the first diff
  run" part of Step 2. By design (R6) these are inert `todo` placeholders, so the controller must replace them with exact
  paths. Until it does, every one of the 12 assets fails on provenance/flags, which errs on the safe side.

### Named risks (verdict each)

1. **False pass.** Mostly safe, with one real hole (Important 1) and some synthetic edge cases (Minor 1-3). I probed
   with synthetic JSON under cache/scratch/rev-t7:
   - Exit 2: missing, empty, whitespace-only, non-JSON, BOM, top-level list, no `asset`, wrong `asset`, and a
     malformed allowlist including a bool bound (`rel: true`) (flatdiff.py:46-106).
   - Exit 1 with no entry: number→null, number→string, `{}`→`[]`, null→absent, a list getting shorter, an index-list
     reorder, NaN→NaN (NaN != NaN, so it shows as changed), and 1→NaN / 1→Infinity under a bound (gap NaN/inf fails
     both `<=` comparisons, flatdiff.py:160-165).
   - `todo: true` is inert (flatdiff.py:174, used at :185). A todo-only path exits 1, while `todo: false` is active.
   - Glob: `*` crosses dots but the match is anchored with a literal prefix (flatdiff.py:144, `\Z`), so `dilution.*`
     cannot reach revenue. The committed allowlist has no glob matching `revenue.annualized`, `costOfRevenue`,
     `holderFlow.net` or `yields.cash` (test_flatdiff.py:266-271).
   - **Hole:** LIT's unbounded `incomeStatement.dilution.*` covers fields that should not move (Important 1).
2. **Bounds.** Correct.
   - rel = |new−old|/|old| (flatdiff.py:163). With old == 0, rel is inf unless there is no change; my probe 0→1e-300
     under rel 1 exits 1.
   - When an entry gives both bounds, either one may pass (`abs` first, :161-165). Probes: 0→0.5 with abs 1 exits 0;
     10→12 with rel 0.1 / abs 1 exits 1.
   - Every matching entry must hold (`all(...)`, flatdiff.py:191). An unbounded `*` plus a rel-0.01 entry on a 5% move exits 1.
   - A bounded entry on added/removed/non-numeric fails (:158). Bools are excluded from numbers (:70-71).
3. **prod_copy --breaking.** Safe.
   - The flag is only in the OLD release's migrate. That run uses ORION_* stripped from the inherited env,
     `ORION_HOME=<P>/old` and `ORION_ENV_FILE=<P>/old/.env`. That `.env` is `DEV_URL` (local orion_dev socket,
     prod_copy.py:39) plus the fresh `p2proof_<stamp>` schema (prod_copy.py:240-246).
   - Prod is never a migrate target: it is reached only through `sql_ro`.
   - The prod-vs-local `max(schema_migrations.id)` check still follows (:251-255), and so do the table and column set
     checks (:257-269).
   - `--breaking` is a real option at `orion-2026.11.11.1`: `git grep` shows src/cli/commands/db.ts:30, and
     src/db/pg/migrate.ts:106 refuses without it. 0006 starts with `-- breaking`.
   - Test test_prod_copy.py:244-266 pins argv, cwd and ORION_HOME, and asserts that neither prod nor psql is read
     before migrate.

### Tests run

- Own detached worktree at 811d33f: `/usr/bin/python3 -m unittest tools/phase3-proof/test_flatdiff.py
  tools/phase2-proof/test_prod_copy.py` gives `Ran 54 tests ... OK` with clean output. The report's 120 also includes
  test_compare.py.
- I ran synthetic probes as listed above. I also ran mutations of golden `lit/stored` / `pump/stored` through the
  committed allowlist.

### Strengths

- The "every matching entry must hold" semantics (flatdiff.py:184-191) is the right design: a broad unbounded glob can
  never relax a bounded path. The bounded-path-turns-null case fails.
- The refusals are fail-closed (exit 2 on empty or unparseable input, never "identical"), and the allowlist validation is
  strict: unknown keys, required reasons, finite non-negative bounds, bool `todo`.
- The literal-bracket glob avoids fnmatch's character-class trap with `[id=...]`.
- The golden-based R21 test (test_flatdiff.py:273-318) checks both sides: ×1.00066 passes through bounded entries, and
  ×1.001 fails exactly the 13 rel paths.
- The prod_copy test fakes `run` and makes sql_ro/psql raise. That is a real guarantee that nothing touches prod before
  migrate.

### Issues

#### Critical (Must Fix)

None.

#### Important (Should Fix)

1. **r1-allowlist.json:128 — LIT `incomeStatement.dilution.*` has no bound, so dilution fields outside the unlock
   line pass with any change (plan-mandated: brief Step 2 lists it literally).** Each of these mutations of golden
   `lit/stored` through the committed allowlist exits **0**:
   - `dilution.supply.burnedPerYear` → 0 or → null. This is tokens burned by the buyback, i.e. LIT holder flow, which
     the global constraints say must stay unchanged.
   - `dilution.emissionsPerYear` ×2.
   - `supply.addedPerYear` ×2.
   - `supply.netPct` ×3.
   - a new `releases[id=x]` line of 9e9 tokens.

   R1 moves only the unlocks line by +0.066%, so none of these should move freely. PUMP is safe here, because its
   `dilution.*` is rel 1e-12. Fix: exact entries (`"abs": 0`) for `dilution.supply.burnedPerYear` and
   `dilution.emissionsPerYear`, and rel 0.0007 on `supply.addedPerYear` (it equals tokensPerYear). Give `supply.netPct`
   an abs bound sized like netPerYear's (≈100000/totalSupply). Then either drop the unbounded `dilution.*` or keep it
   only for the `releases[id=unlocks].*` shape. Since every matching entry must hold, adding these entries is enough
   even if the unbounded glob stays.

#### Minor (Nice to Have)

1. flatdiff.py:118-133 — path collisions hide changes. `{"a":{"b":1}}` vs `{"a.b":1}` flatten to the same path (probe:
   exit 0). A list with ids `1` and `"1"` passes `_id_keyed` (it dedups via json.dumps, :114) but both elements map to
   `[id=1]`, so the later one overwrites the earlier. I changed the first element's value and got exit 0. Real reports
   use identifier keys and string ids, so this is synthetic. Fix: in `walk`, raise `Bad` when a path is already in
   `out`, and dedup ids by `str(id)`.
2. flatdiff.py:126-129 — reordering an id-keyed list, or the dict keys, gives no diff (probe: exit 0). Phase 2's
   compare.py checked key order exactly. The R1 proof is about values, and AERO is checked by `cmp`, but the 9 assets
   with no expected diffs would pass a reorder. Consider a sha/`cmp` line for assets whose flatdiff is empty, or record
   the list id order as its own leaf.
3. flatdiff.py:95-96 — any glob is accepted, including `"*"` or `"incomeStatement*"`; a probe with an asset entry
   `"*"` allowed a revenue change. The controller still has to turn the todo placeholders into globs, so refusing a
   glob that starts with `*`, or one whose literal prefix is shorter than one path segment, would make that safer.
4. r1-allowlist.json (all 12 `incomeStatement.checks*`, `provenance.sources*`, `flags*` placeholders) — once the todo
   flag is dropped, an unbounded `checks*` covers numeric check values (expected/actual) too. The controller should
   replace each placeholder with exact paths rather than flip `todo` off. The README (D:227-228) says to do this; it
   just bears repeating at fill time.
5. r1-allowlist.json:162 (lit) / :254 (pump) — `perToken.perTokenFdv.*` at rel 0.0007 also covers
   `perTokenFdv.revenue`, `grossProfit`, `holderFlow.total` and `byBucket.*` (probe: LIT perTokenFdv.revenue +0.06%
   exits 0). This is accepted by R22 (manual stop), and listed here only so the sign-off checks it.
6. flatdiff.py:78-87 (`load_json` via json.loads) — duplicate top-level asset keys in the allowlist are silently last-wins (json.loads). Consider
   `object_pairs_hook` to refuse duplicates (exit 2).
7. test_flatdiff.py:266-271 — the "forbidden paths" check names only 4 paths. Adding
   `incomeStatement.dilution.supply.burnedPerYear` and `incomeStatement.holderFlow.byBucket.*` would have caught
   Important 1.
8. test_prod_copy.py:264-266 — the test pins ORION_HOME but not `ORION_ENV_FILE == <P>/old/.env`, nor that no
   inherited `ORION_DATABASE_URL` reaches the env. The scratch-only safety of `--breaking` rests on those two facts.
   Set `ORION_DATABASE_URL` in `os.environ` in the test and assert it is absent from `kw["env"]`.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** flatdiff's comparison and bound semantics are correct and fail-closed on every malformed-input and
type-change case I probed, and prod_copy's `--breaking` is confined to the fresh scratch schema with the level and table
checks intact. But the committed LIT allowlist lets holder-flow-derived `dilution.supply.burnedPerYear` (and other
dilution fields) change without bound, which is a false-pass path against the "holder flow unchanged" constraint.
Bound those fields before the controller signs LIT off.
