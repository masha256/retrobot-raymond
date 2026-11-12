# Final whole-branch review: Orion Phase 3 R0b + R1 (e61d663..ee295f6)

Reviewer role: superpowers `requesting-code-review/code-reviewer.md`. Read-only. 13 commits, 84 files. I read the code
diff without the goldens (`git diff e61d663 ee295f6 -- . ':!tests/report/golden' ':!tests/agent/golden'`, 6.5k lines)
in passes: src/db + src/daemon + src/cli, then src/ingest + src/report + src/config + src/provenance, then assets/,
orion-remote, deploy.md + followups, then tools/. I also read the ledger, the task-7 findings, review and report, and the
controller's proof outputs (`workspace/orion/phase3-proof/r1/{out,*.sh,*.log}`). I read the soak script
(`scripts/orion-stage-soak.py`, outside the repo) only to check R26.

**Tests run** (own detached worktree `.worktrees/rev-final` at ee295f6; node_modules symlinked; removed afterwards):
- `/usr/bin/python3 -W error -m unittest tools/phase3-proof/test_flatdiff.py tools/phase2-proof/test_prod_copy.py
  tools/phase2-proof/test_compare.py scripts/provision/test/test_orion_remote.py`: `Ran 182 tests ... OK`.
- `npx vitest run <15 files> --maxWorkers=1`: 15 files / 302 tests passed. The files: backfill, purge (db + cli), job
  cli, scheduleUnlocks, r1-third-party, daemonSchema, jobs, orionRemote, v2Golden, packGolden, incomeStatement (config +
  report), daemon, pg/migrate.
- `npx tsc --noEmit -p .`: clean.
- flatdiff probes against the real prod-copy outputs (`out/old|new/{lit,vvv}.json`) through the committed allowlist.
  Results are under Minor 1.

## Strengths

- **0007 is expand-only, and rollback was checked against the old code.** The migration only adds a nullable
  `params_json` and widens the kind CHECK under its default name (src/db/pg/migrations/0007_job_params.sql:6-10). Its
  first line is not `-- breaking`, and the migrator runs each file in a transaction (src/db/pg/migrate.ts:112).
  At tag orion-2026.11.11.1, the old migrator returns state `ahead` (migrate.ts:75), and src/db/connection.ts:79 and
  orion-remote:984 accept it. The old `enqueueJob` names its columns, so the old release runs on schema 7.
- **`data purge` errs toward refusing and is durable.**
  - Config refusals come before the lock (src/db/purge.ts:87), and all refusals are re-checked inside the transaction
    (:93-94).
  - The export is fsynced, then its directory, and each created parent, before the first delete. It is opened with
    `wx`, mode 600 (:250-276).
  - The delete count is checked against the plan (:114).
  - Side state goes only with a metric that is not configured and has no rows left (:183).
  - The rehearsal on the prod copy matched prod's counts exactly, and all 13 reports were byte-identical after the purge.
- **The backfill handler covers the failure modes the plan named.**
  - The CLI and the handler validate params the same way (`parseBackfillParams`).
  - A deferral doesn't use the attempt (`deferJob` attempts-1).
  - It runs once, and a lost lease fails it, with a RESTARTED alert at the next start (daemon.ts:244).
  - A failed requested primary source fails the job (`fetchFailure`).
  - Start, done (with duration and rows per metric) and failed lines all go to Slack.
- **The orion-remote changes add no new risk.**
  - Every value is a `fullmatch` regex, argv is a list and no shell is used (orion-remote:184-194).
  - `--yes` is passed only when given (:432).
  - The rung list is pinned against `SOURCE_TYPES` (tests/release/orionRemote.test.ts:37-40), and no new code path
    reads `.env`.
- **flatdiff's semantics are fail-closed.** Every matching entry must hold, a bounded entry fails on a type change, and
  inputs are validated strictly. ee295f6 closes the LIT `dilution.*` hole. My probe sets `burnedPerYear` to 0 on the
  real LIT output: exit 1.
- **R1 is complete for its scope.** Grepping the 12 YAMLs leaves only out-of-scope reads:
  - HYPE `af_buyback` and `revenue_proxy`, and PUMP `llama_revenue` (DefiLlama);
  - CRV `llama.box`;
  - every CoinGecko `price` / `circulating_supply` primary, VVV's DIEM price included;
  - `external_ids`.

  Cross-checks are never stored (src/ingest/run.ts:381), so they have no rows to purge. The six purge pairs in
  deploy.md:507-512 are exactly the removed stored series: CAKE fees + llama_revenue, LIT fees + llama_revenue, UNI
  swap_fees, VVV revenue_proxy, and the LIT / PUMP `unlocks_next_year` third_party rows. Nothing outside R1 was
  removed. AERO is untouched.

## Issues

### Critical

None.

### Important

**I-1. The deploy.md per-env release block is not executable as written: step 3's full refresh of LIT and PUMP makes
step 6 STOP for both.** (docs/ops/deploy.md:492-498 vs :528-541; src/report/load.ts:202-206)
- A report for day `d` reads levels as of the end of `d + 1` (load.ts:202). Step 0 saves `before` with `d` = yesterday,
  so its asOf is the end of today. Step 3's `job run-now refresh lit|pump` then writes new price_usd, total_supply,
  circulating and staking level observations "now", which is inside that asOf. LIT's Core fee adapter also re-reads
  and supersedes its last 3 days.
- Step 6's `report yield lit|pump --day d` therefore moves price, market cap, every yield on market cap, the multiples
  and perToken. None of these has an allowlist entry, so flatdiff exits 1 and the block says STOP: no prod deploy.
- The prod-copy proof did not exercise this, because it ran `data fetch <a> --metric unlocks_next_year` (one level
  only), not a refresh (r1-proof.sh).
- A second, smaller trap: if a scheduled nightly falls between step 0 and step 6, every asset STOPs, and the block does
  not warn about it.
- Fix (docs only):
  1. Move the 13-asset flatdiff and the AERO `cmp` to right after step 2 (switch), before any refresh. LIT still shows
     the old unlock row there; the allowlist's unlock entries only warn "unmatched", and its flags/provenance entries
     match.
  2. After step 3, check the two new rows directly (`data show lit unlocks_next_year`: 138,888,888.89, disclosure, the
     x.com citation; pump 82.5e9, the blockworks citation) and save `mid/` reports.
  3. After step 5, `cmp` the reports against `mid/` (the rehearsal showed purge is byte-neutral).
  4. Say "do not straddle a nightly slot between step 0 and the check".

**I-2. LIT's `netPerYear` / `netPct` abs bounds are tied to the release date: from 2026-11-29 the true unlock delta
exceeds them.** (tools/phase3-proof/r1-allowlist.json:90, :115)
- The bounds are abs 100000 tokens and abs 0.0001, sized from today's delta (92,100 tokens = 10 tranches × 9,210, the
  500M-vs-499.67M gap / 36).
- The window (now, now + 365 d] picks up an 11th tranche (2027-11-29) from 2026-11-29: 101,310 tokens and netPct
  1.03e-4. From 2026-12-29 it holds 12 tranches: 110,520 tokens and 1.13e-4.
- A stage or prod run of step 6 on or after 2026-11-29 STOPs on two paths that are correct. The rel 0.0007 entries
  don't have this problem (0.000664 for any tranche count), and the net-of-dilution rel 0.0008 entries only get
  looser as dilution grows.
- Fix: abs 120000 and abs 0.00013, with the reason naming the 10-12 tranche range. Alternatively, note in deploy.md
  that the bounds hold only through 2026-11-28.

**I-3. The purge of LIT's and PUMP's third_party unlock rows nulls their dilution in every report for a day before the
deploy. This history change is undocumented, and the proof doesn't cover it, although the plan's "both windows"
comparison would have.**
- The deleted rows run from 2026-10-16 to the deploy day: 31 for LIT and 29 for PUMP on the copy (purge/5,6-yes.json).
  The schedule adapter writes its first row on deploy day.
- `report yield lit --day <any earlier day>` then finds no `unlocks_next_year` row at or before asOf (load.ts:203-206).
  So dilution, `yields.dilution`, `netShareholder`, `holderFlow.netOfDilution` and perToken dilution become null for
  roughly the four weeks before the deploy.
- The rehearsal compared only D, which works because D's asOf (the end of 11-12) includes the fetch made on 11-12.
  Plan Task 7 Step 5 and spec §5 ask for both windows (D and D-91); only D was run.
- The nightly and the snapshot (yesterday's day) are unaffected after deploy day. Ad-hoc historical reports, re-runs
  of an old nightly slot and any later history consumer are affected.
- Fix: say so in deploy.md and the followups note, and get it into Mike's go. The other options are to keep these two
  purges for R8, or to accept the loss knowingly; a value backfill is not possible for levels.

**I-4. The ledger's "default report day old == new for all 13" has evidence for only 10 assets, and UNI and VVV are
two of the three it doesn't cover.**
- `r1-proof.log` (and the copy in out/) stops after `sky 2026-11-11 2026-11-11`. There are no uni/vvv/ycrv lines and no
  `done` line, and the `old-default`/`new-default` reports were not kept.
- UNI's `flow_usd.swap_fees` (volume) and VVV's `flow_usd.revenue_proxy` (the business cross-check) were both in
  `defaultDayFlowMetrics` (load.ts:22, 27). Removing them can only move the default day later (load.ts:148-157).
- If it moves, the nightly report day, the snapshot's `report_day`/`lag_days` and the LAG lines change for that
  asset. None of those is in the report JSON that step 6 compares, and step 6 pins step 0's day.
- The soak compares `day` too (orion-stage-soak.py:51, 187), so R26's "R1 moves none of the soak's fields" depends on
  this.
- Fix (read-only, cheap): on prod, `sql-ro` the newest stored day of each `reportFlowMetrics` flow for uni, vvv and ycrv.
  Alternatively, re-run the default-day loop on the next copy. Then correct the ledger and add the result to the soak's
  known queue if a day moves.

### Minor

1. **The exact LIT/VVV flags and provenance entries have no bound and are positional.** (r1-allowlist.json:119-133,
   :229-247)
   - My probes on the real outputs each exit 0:
     - LIT `flags[0]` replaced by a different flag;
     - LIT `thirdParty[0]` replaced by another path;
     - VVV keeping `third_party:api.llama.fi`;
     - a new VVV `flags[3]`.
   - The index is also env-specific: the golden fixture has VVV's flag at `[2]`, prod has it at `[3]` (task-7 report,
     concern 3). On stage this can STOP where nothing is wrong.
   - Fix: let an entry carry `"kinds": ["removed", "added"]` (or the expected `old` value), so that only the removal is
     allowed. **Fix before merge**: it is the release-day net.
2. **The followups note is stale.** (docs/superpowers/notes/2026-11-12-orion-phase3-followups.md)
   - R21/R22 (:73-80) describe the superseded `perTokenFdv.*` glob and the todo placeholders.
   - R23-R26 are missing.
   - :143 reads "Proof results: see controller commit", but there is no such commit or section.
   - :16 and plan :48 still give `<asset>-<metric>-<stamp>`.
   - R6 (:44) says "backfill rehearsal" was done, but R25 skipped it.
   - The P1 summary (:11-13) omits R9 and the unfinished-nightly guard.
   
   **Fix before merge** (docs).
3. **The R25 staging smoke backfill is in no runbook.** R25 makes `ssh orion-stage job run-now backfill hype --metrics
   flow_usd.af_buys_direct --backfill-days 3` the handler's first real run, but deploy.md says "R1 itself queues no
   backfill" (:457). Add it as a stage-only step after step 6, with what to check: start and done lines, and `jobs`.
   **Fix before merge** (docs).
4. **R11's stated cost understates the effect of an oversized backfill.** The daemon has one worker, so a backfill also
   holds back the hourly `levels` job, with its watch fire/clear posts and the `levels` snapshot. On prod that is also
   the `ORION_DEADMAN_URL` ping (docs/ops/daemon.md:18), so a backfill of more than an hour or two can trip the prod
   dead-man. Add a sentence to deploy.md:446. Fine to defer: no prod backfill ships in R1. Add it before R2's
   `op: prices`.
5. **The purge export files are the only long-term copy, on one host, and no verb can read them.**
   (deploy.md:521-525; followups "Purge export files")
   - Raymond only sees the path and sha256 that the JSON output prints.
   - Suggest that Mike copies the six files off venus after step 5, or a later `purged list` verb. The followups note
     already leaves retention open.

   Fine to defer: DefiLlama history can be fetched again.
6. **Open anomalies keyed to removed sources stay open.** Examples are `cross_check_mismatch` / `source_failure_streak`
   with a dedupe key of coins.llama.fi, CoinGecko total_supply or the DefiLlama emissions. The only way to close one is
   by hand (src/db/anomalies.ts:139-153). Suggest a `data anomalies` sweep in the release block, resolving each with the
   note "source removed in R1". Fine to defer.
7. **Proof deviations, recorded only.** Plan Step 5 takes "before" from `ssh orion-prod report yield`; the controller
   used the old release on the copy. That is equivalent and arguably stronger, because both sides read the same data.
   The D-91 window was not run (see I-3). The PUMP Blockworks quote (pump.yaml:111) could not be checked verbatim
   offline.

## Deferred-minor triage (every `minor (deferred)` ledger line)

| Ledger line | Item | Verdict |
|---|---|---|
| 46 | T1 M-1 `message`/`codeOf` copied from refresh.ts | fine to defer |
| 47 | T1 M-2 `ctx.signal` not passed into fetch | fine to defer: the same gap as refresh, and a switch drains rather than steals the lease |
| 50 | T1 M-4 job.ts trim() vs untrimmed Number() | fine to defer: the result is correct |
| 58 | T2 M-6 dead API cursor after a third_party purge of a configured metric | fine to defer: moot in R1 (the purged configured metric `unlocks_next_year` is a level and has no cursor) |
| 59 | T2 M-7 migrate.test OID flake at maxWorkers=2 | fine to defer: it passed for me at maxWorkers=1 |
| 62 | T1 RR-1 an orphaned newest-slot row defers every backfill silently | fine to defer: the operator watches `jobs`, and the next nightly clears it. Worth a line in the M3 stage smoke step |
| 63 | T1 RR-2 derived requested metric: an input failure doesn't fail the job | fine to defer: no current config hits it |
| 68 | T2 RR-1 export left in purged/ when the dir fsync fails | fine to defer: nothing is deleted, so it fails closed |
| 69 | T2 RR-2 DB refusals run under the lock; a refused --yes may abandon orphaned agent runs | fine to defer |
| 72 | T3 rung list not pinned against TS SourceType | fine to defer: it is now pinned against `SOURCE_TYPES` (orionRemote.test.ts:37-40), which is typed `SourceType[]`; only a missing rung would slip through |
| 78 | T4 M1 the window-ends test passes with swapped ends | fine to defer: the month-end test catches it |
| 79 | T4 M2-M7 (originOf, duplicate loop, validation tests, "50000.00M" detail, registry monkeypatch, schedule_steps citation guard) | fine to defer: all cosmetic or hypothetical. The "50000.00M" PUMP detail is visible in `data show`; cosmetic |
| 83 | T3 gitPublisher timeout flake | fine to defer |
| 85 | T3 `assert_refused` substring false-fail | fine to defer: it can only false-fail, never false-pass |
| 91 | T5 bare `.toThrow()`, no mixed-form test, vague typo error, whitespace-only reason, form undocumented | fine to defer |
| 101 | T6 parity.ts comment, indentation, x.com keyed by host, dropped calibration facts, replay comment, r1 test coverage gap | fine to defer. Note: x.com keyed by host would label a future non-Lighter x.com citation `first_party_api`; fix with R8's register rework |
| 112 | T7 tooling: id-list / key reorder shows no diff | fine to defer: AERO is checked with `cmp`, and a report's key order is deterministic and pinned by the v2 golden tests |

All 17 ledger lines are fine to defer. Three of my own minors (1, 2, 3) are marked fix-before-merge.

## Ruling verdicts (R1-R26)

| Ruling | Verdict |
|---|---|
| R1 code on the spec/plan branch | sound |
| R2 synthetic fixture for `purge_live_source` | sound |
| R3 remote purge/compare-usd append `--json` | sound (orion-remote:425, :432) |
| R4 deploy.md section split T3/T8 | sound |
| R5 PUMP citation researched by the controller | sound in process. I could not check the quote verbatim offline |
| R6 Task 7 split | sound |
| R7 Task 8 Step 1 is the controller's | sound |
| R8 four pin-test edits | sound |
| R9 extra 2 h post-slot guard | sound. Cost as stated |
| R10 queued backfill fails "no handler" on rollback | sound. deploy.md:453-458 says so and why |
| R11 no code bound on backfill time | sound decision, but the stated cost is incomplete (Minor 4: hourly levels, watch and the prod dead-man stall too) |
| R12 one implementer at a time | sound |
| R13 purge takes OrionDb | sound |
| R14 refresh before purge for latest_levels | sound as a ruling. Doing it as written breaks step 6 (I-1); the fix keeps R14's order |
| R15 env prefix on the start line | sound |
| R16 180 days, not 182 | sound. Checked: start 2026-07-12 + 3 × 365 d = 2029-07-11; now 2029-01-12, so 180 d |
| R17 `as string[]` cast | sound |
| R18 goldens rewrite | sound. The moved set matches the proof's moved set (CAKE/UNI volume, LIT flags/provenance, VVV crossCheck/flags/provenance), and the prod-copy run backs it |
| R19 disclosure e2e rebuilds the historical lit.yaml | sound |
| R20 `--breaking` for the old release's scratch migrate | sound. The ORION_* strip is now pinned by test (ee295f6) |
| R21 LIT/PUMP dilution-derived bounds | superseded by R24 / ee295f6. The abs bounds are date-fragile (I-2) |
| R22 perTokenFdv.* manual stop | superseded for LIT (exact entries, ee295f6). PUMP's `perTokenFdv.*` at rel 1e-12 is fine. The deploy.md:537-538 manual-read instruction is now redundant but harmless |
| R23 no `db status` verb; switch report as the schema check | sound |
| R24 net-of-dilution rel 0.0008, exact paths, todos deleted | sound in bounds (real 0.000729). The exact string entries are unbounded and positional (Minor 1) |
| R25 skip the local daemon rehearsal | sound reasoning (the network and a possible paid analyst run). The stage smoke it relies on is not in deploy.md (Minor 3), and the followups R6 line overclaims (Minor 2) |
| R26 soak parity file unchanged | sound for the value fields: the soak picks holderFlow gross/net, hfg and revenue.annualized. But the soak also compares `day`, and the UNI/VVV default-day carry is unproven (I-4) |

## ee295f6 scoped re-review (task-7-findings.md + the steer)

| Finding | Verdict |
|---|---|
| I-1 LIT `dilution.*` unbounded | **ADDRESSED.** The glob is gone. burnedPerYear and emissionsPerYear are abs 0, addedPerYear rel 0.0007, netPct abs 0.0001, and `releases[id=unlocks].id` abs 0, so no entry allows an added or removed release line. My probe sets burnedPerYear → 0 on the real LIT output: exit 1. The real LIT run gives 20/20. Caveat: the abs sizing is date-fragile (I-2) |
| M path collisions (dotted key; id 1 vs "1") | **ADDRESSED.** `key_step` escapes `\ . [`; `id_step` tags `#` on numbers and escapes strings; a collision is caught as a backstop and exits 2 (flatdiff.py:127-171). Tested |
| M duplicate asset key; bare `*` / empty glob | **ADDRESSED.** `object_pairs_hook` applies to all inputs (:51-72); a glob that is blank or starts with `*` exits 2 (:112-115). Note: `"i*"` is still accepted; acceptable |
| M test_prod_copy pins ORION_ENV_FILE and strips inherited ORION_DATABASE_URL | **ADDRESSED.** test_prod_copy.py:245-275 runs under mock.patch.dict, with the full ORION_* key-set assertion |
| Task 8 concern 1: export name wording in deploy.md | **ADDRESSED** in deploy.md:437-439 and :521-523. **NOT ADDRESSED** in followups :16 and plan :48 (outside the dispatch; Minor 2) |
| Steer: LIT net-of-dilution rel 0.0008 | **ADDRESSED** (r1-allowlist.json:33-62). The real move is 0.000729 |
| Steer: exact provenance/flags paths for LIT and VVV | **ADDRESSED** as specified. The entries are unbounded and positional (Minor 1) |
| Steer: all other todo placeholders deleted | **ADDRESSED.** No `todo` key is left, and `test_the_committed_allowlist_loads` asserts it |
| Steer: raw docstring | **ADDRESSED** (`r"""`). The tests pass under `-W error` |
| Deferred: reorder shows no diff | stays deferred (table above) |
| New breakage | none found. 182 python tests OK |

## Named risks

1. **Deploy and rollback: mostly safe; the release block needs fixes.**
   - 0007 is expand-only, and orion-2026.11.11.1 runs on schema 7 (checked at the tag).
   - orion-remote cannot run caller text in a shell (argv list, fullmatch validation), cannot delete without an
     explicit `--yes`, and reads or prints no `.env`.
   - The block's order is right: the orion-host.sh re-run, stage, soak, then prod; refresh before purge; dry runs
     before `--yes` on Mike's go. It names the Sunday 10:30Z staging_refresh hazard (deploy.md:461-466).
   - But it is not executable as written (I-1). It is also date-fragile (I-2), and stage may false-STOP on VVV's flag
     index (Minor 1).
2. **Silence means broken: OK for this release.**
   - Backfill done, partial (named), failed (ALERT) and start lines all post; a lease loss is alerted at restart.
   - A deferral is silent, but `jobs` shows it, and RR-1 is a known edge.
   - Purge refusals exit non-zero with a code and write nothing.
   - The not_measured volume carries `annualized: null` plus `notMeasured: <reason>`, never 0. Volume is not in any
     Slack or text line, before or after this release, so no line changes silently.
3. **Value equality.** Every path the YAML diffs predict was seen, and no other path, on day D for all 13 (the proof
   outputs agree with the allowlist). The snapshot `full` body and the tick summary are the report JSON, so flatdiff
   covers them. The gaps:
   - default day, `report_day`/`lag_days` and the LAG lines for UNI/VVV/YCRV (I-4);
   - every pre-deploy day for LIT/PUMP after the purge (I-3);
   - the levels snapshot was not compared. Expected unchanged: it holds latest_levels of level metrics, and R1 removes
     only cross-checks there.
4. **Data loss: OK.** The export is written and made durable (fsync of the file, its directory and created parents)
   before any delete, inside the locked transaction, and the delete count is verified. The scope is (asset, metric,
   source_type) by planned ids. The six pairs match the removed series exactly. The residual risks are that the export
   is the single long-term copy on one host (Minor 5), and that LIT/PUMP lose their historical dilution (I-3, a
   history change rather than lost rows).
5. **Completeness: OK.** No live DefiLlama or CoinGecko read is left among the R1 items (CAKE, LIT, UNI and VVV series;
   the six coins.llama.fi checks; nine CoinGecko total_supply checks; the LIT and PUMP unlock datasets). The
   `lit.unlocks_next_year` adapter is unreferenced (r1-third-party.test.ts) and stays registered until R8. Nothing
   out of scope was removed.

## Declined to judge

- Whether Mike accepts a Blockworks (non-issuer) citation for PUMP: P4 makes it his call.
- Whether the LIT quote's "1-year unlock" fits tranches from 2027-01-29: approved in proposal #3 (P4).
- The golden JSON rewrites line by line: I relied on R18, Task 6's review and the proof's moved-path set, which agree.
- The full vitest suite: I ran the 15 most relevant files only; the controller ran 1745/1745 at 35333a6, and ee295f6
  touches no TS.
- The healthchecks grace period for the prod dead-man (Minor 4): not in the repo.

## Assessment

**Ready to merge: With fixes.** No Critical. Merge after the docs/tooling fix wave:
- I-1: reorder the release block's check;
- I-2: widen the two abs bounds or date-limit them;
- I-3: document the loss of LIT/PUMP historical dilution and put it in Mike's go;
- I-4: close the UNI/VVV/YCRV default-day evidence with one read-only query;
- Minors 1-3.

The code (0007, the backfill job, purge, orion-remote, the schedule adapter, volume not_measured, the config sweep) is
sound and well tested. None of the open items needs a TS change, and none risks data. They all sit in the release
procedure and the proof.
