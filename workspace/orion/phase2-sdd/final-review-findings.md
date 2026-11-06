# Final whole-branch review: Orion Phase 2 (feat/data-strategy f1d2a23..c9c51a1)

Reviewer: final seat (whole branch, cross-task risks 1-6, deferred-minor triage). Read-only. Reviewed in passes:
migrations + DB layer, writer paths (flow/apiFlow/periodic/run/levels/proposals/ledger/data set), report/tick/nightly/
snapshot, checks, provenance + scrub, tokens/prices + backfill + compare-usd, R20, importer/staging refresh, docs/ops.
The 993-line `incomeStatement.ts` and the YAML blocks were read where the named risks touch them (holder-flow set
collapse, apportion, isolation); their figures rely on the per-task proofs (13/13 legacy, 361 parity, 3 reclass).

Verification run here (detached checkout `.worktrees/rev-final` @ c9c51a1, node_modules symlinked):
- `npx vitest run --maxWorkers=2`: **131 files / 1527 tests passed** (84.7 s).
- `npm run typecheck`: clean.
- Script over the 13 YAMLs: the metrics `income_statement` adds to `reportFlowMetrics` (so to the default report day)
  beyond v1's: **none for 12 assets; yCRV only `flow_usd.yearn_gross_fees`, `flow_usd.yearn_gross_incentives`.**

## Verdict

**Ready for the G2 rehearsal.** 0 Critical, 2 Important, 7 Minor. Neither Important blocks the rehearsal; both should be
fixed before merge / release 2 (I2 before any deploy).

## Strengths

- Expand-only discipline holds across 0003+0004+0005: every new column nullable, `value` still written, the anomaly-kind
  CHECK is a superset (named constraint re-added), the `usd` token seeded, view-only consumer (`flow_usd_v`) read by
  nothing but `compare-usd`. N-1 job-row compatibility is real both ways: the nightly reads `j.result` without a schema
  (`src/daemon/jobs/nightlyReport.ts:107-115`), the v2 tick fields and `checks`/`checks_error` are optional
  (`src/app/tickReport.ts:26-47,127-135`), `InboxSchema` kinds are `z.string()`.
- Provenance is made mandatory by the type (`NewObservation.provenance`), checked and re-scrubbed at the single insert
  (`src/db/observations.ts:136-145,213`); `confirmObservation` carries the provisional row's provenance forward; the
  latest_levels upsert scrubs too. Scrubbing is by context (query keys, keyed RPC hosts, key-shaped segments) and
  locators are built from config, never from env, so RPC URLs never reach a row. No real key in the diff (grep).
- The day scanner refactor (`openDayScanner`, `src/ingest/flow.ts:286-430`) keeps the per-transfer pricing order and
  arithmetic of the old loop, and the token backfill shares it, so both count the same transfers. The backfill only
  `UPDATE ... WHERE amount IS NULL AND active`, one day per tx under the lock, twin refusal exits 1.
- C4 isolation is clean for the computation (`statementOf`, `src/report/load.ts:141-147`) and both new failure modes
  print an ALERT line and make the block an alert (`src/notify/format.ts:128-129,161-171`).
- R20 is minimal and correct: listed members only, conflicts/adoption only for them, cursor frozen while any member is
  withheld, outcome note says so (`src/ingest/flow.ts:432-436,513-559`).
- R12 confirmed: SKY's v2 block has no protocol line and no remainder and passes both revenue lines whole (`of`) to
  holders, so v2 protocol is exactly 0 by construction; excluding that pair is sound (`assets/sky.yaml`,
  `src/report/parity.ts:117-119`).

## Issues

### Critical

None.

### Important

**I1. A check breach never makes the nightly block an ALERT (plan correction 12 says it does).**
- `src/app/tick.ts:105-107`: `await recordChecks(...)` discards the anomalies it raises; they are not added to
  `report.ingest.anomalies_raised`. `src/notify/format.ts:123-137` (`isAlert`) has clauses for `statement_error` and
  `checks_error` but none for `checks[].status === 'breach'`, and `holderYieldLines` never prints `checks`. The v2
  statement does not flag a breach either (`src/report/incomeStatement.ts:293` carries the status only).
- Effect: a breach shows only as an advisory `anom #N check_breach ...` line under DECISIONS (the inbox), in a block that
  is not an alert. Plan correction 12 (plan l.96-98): "It still makes the nightly block an ALERT (`isAlert` counts
  `anomalies_raised`)". Named risk 4 asks that a breach be visible as an alert line / flagged field. The test that pins
  the tick behaviour (`tests/app/tick.test.ts:84-92`) checks the inbox only.
- Fix: add `rep.checks?.some((c) => c.status === 'breach')` to `isAlert` and print one `CHECK BREACH <SYM> <id>
  (<type>) gap <pct>%` line per breached check (or push the raised anomalies into `anomalies_raised`); add a format test.
  Controller ruling needed with R15: yCRV's/sdCRV's dust breaches would then alert on their days until M4 (relative-only
  gaps) is decided at G2. If the advisory-only behaviour is intended, amend correction 12 instead.
- Triage: must-fix before merge (not a G2-rehearsal blocker).

**I2. docs/ops has no Phase 2 release runbook; the rollout order lives only in scattered followups-note paragraphs.**
- `docs/ops/deploy.md:136,151-155`, `docs/ops/postgres.md:158-161`, `docs/ops/daemon.md:136` cover `--legacy` only. Not
  in docs/ops: migrations 0003-0005 must reach prod and stage in the same release step (`staging_refresh` refuses a dump
  whose migrations differ; followups l.271-272); `db backfill-provenance` (dry run first; R17's 18 unmapped rows); the
  yCRV by-sender backfill `data fetch ycrv --metric flow_usd.yearn_gross_fees --metric flow_usd.yearn_gross_incentives
  --backfill-days N` right after the deploy (followups l.375-385); `data backfill-tokens` per chain asset, one at a time,
  outside 05:00-06:30 PT (exit 1 = stop); `data compare-usd` for G2; the rollback note (N-1's latest_levels upsert leaves
  stale `source_type`/`locator`, T6 M6; N-1 rows written after a rollback need a second `backfill-provenance` /
  `backfill-tokens` pass).
- Effect: an operator following deploy.md for release 2 skips the backfills; nothing breaks silently (yCRV v2 lines are
  flagged `apportion mix n/a`, history keeps `legacy_no_tokens`), but G2/G3 rely on them having run. Named risk 6.
- Fix: one "Phase 2 release (0003-0005)" section in deploy.md with the ordered commands, and a pointer from postgres.md.
- Triage: must-fix before merge (before any staging deploy, which P4 already holds back).

### Minor

**M1. The yCRV "partition by construction" claim does not hold for R20-backfilled history.**
`docs/superpowers/notes/2026-11-04-orion-phase2-followups.md:352-353,369-380`. With R20 the rollout rescan writes only
`yearn_gross_fees`/`_incentives`, priced at backfill time (and at CoinGecko **daily** points for days > 90 back,
correction 13), while the stored `yearn_gross` rows keep their write-time prices. So on backfilled days Σfees + Σinc ≠
Σgross by the price revisions (crvUSD, so small), the two apportion mixes do not sum to exactly 1, and the set's lines
do not sum to the flow "within 1e-15" for the first 91 days. `gross_by_sender` is evaluated only for the report day, so
it never sees those days. Holder flow is unaffected (the set collapses to the whole flow). Fix: correct the note; in the
G2 rehearsal, measure Σfees + Σinc vs Σgross over the current and prior windows after the backfill. Can wait (G2
rehearsal records it).

**M2. `--backfill-days 100` does not cover yCRV's v2 growth window.** `fees_rev` reads `flow_usd.yearn_gross_fees`
directly, and revenue growth compares 91 days with the prior 91, so v2 yCRV revenue growth stays n/m for ~3 months
after rollout (followups l.376-377). Use `--backfill-days` >= 183 if `yearn_gross` history reaches that far (days
beyond 90 are then priced daily: see M1). Can wait (rehearsal parameter).

**M3. The v2-only DB reads sit outside C4's isolation.** `src/report/load.ts:223-226`: `listCheckResults` and
`provenanceByDay` run before `yieldReport`, so a throw there (a bad jsonb locator, a check_results read failure) fails
the legacy report, the tick's `holder_yield` and the snapshot, not just `incomeStatement`. Fix: catch them into
`incomeStatementError` (or skip checks/provenance on error). Can wait (before release 2).

**M4. yCRV's legacy default report day is gated by v2-only series.** `src/report/load.ts:28,36-49`
(`statementFlowMetrics` feeds `lastCompleteReportDay`; verified: yCRV only). The note (l.381-385) overstates the window:
the first nightly fetch scans yesterday for every member of the shared scan, so a default day exists after it; only a
`report yield ycrv` / snapshot between deploy and the first fetch fails (loudly: `no stored day for every report flow
yet`). Either exclude v2-only metrics from the legacy default-day computation for the legacy release, or fix the note's
wording. Can wait.

**M5. T5 template still contradicts 7b M-2.** `docs/templates/T5-liquid-locker-wrapper.md:37` says of `gross_by_sender`
"one scan: any gap is a data finding"; 7b fix round 1 made it an invariant guard that cannot catch an unlisted sender
(followups l.364-368, `assets/ycrv.yaml` comment). The ledger routed it to the final fix wave; not done. Must-fix before
merge (one line).

**M6. The `levels` snapshot body changed shape.** `src/db/latestLevels.ts:16-18,33-35` + `src/push/body.ts:84-86`: each
level now carries `sourceType` and `locator`. Additive and scrubbed, documented in followups l.258, but P2 approved the
`full` body only. Confirm with Mike (or drop the two keys from `levelsBody` until Phase 5). After a rollback they go
stale (T6 M6). Can wait (G2 agenda item).

**M7. N-1-on-0005 is proven at SQL level only; the real staging restore of 0005 objects is untested.**
`tests/db/pg/migrate.test.ts:184-225` inserts a named-column row as N-1 would; no test runs f5f36fa/f1d2a23 writers
(fetch, levels upsert, supersede, confirm) on 0005, and `tests/daemon/stagingRefresh.test.ts` uses a fake runner, so
`pg_restore --clean` of the filtered TOC with the `flow_usd_v` view and the FKs to `tokens` has never run. The code
reading says both work (named-column inserts; the view and FKs are not env-local, so they are kept). Recommendation for
the rehearsal (no live access needed): on the p2proof copy run the old release's `data fetch <a>` for one cheap asset and
`orion db status`, and a `pg_dump -Fc -n <schema>` + `planRestore` + `pg_restore -L` into a scratch schema. Can wait
(G2 rehearsal).

## Deferred-minor triage (ledger R1-R20)

| Origin | Item | Decision |
|---|---|---|
| T0 M2 | only 2 `.env` lines compared | drop (controller-run harness, scratch env reduced to 2 lines by design) |
| T0 M3 | `$TMPDIR` trusted | drop |
| T0 M4 | out/homes not confined to `$TMPDIR` | can wait (Task 11 proof, harness hardening) |
| T0 M6 | proof `ok` read by grep | can wait (Task 11 proof) |
| T0 M7 | refusal paths untested | can wait (Task 11 proof) |
| T0 M8 | `P2_OLD_CONFIG` unrequested | drop |
| T0 | coverage check doesn't require the 13 named assets | can wait (Task 11); the count >= 13 rule already fails short runs |
| T0 | `get_path` can't address ids containing `.` | drop (no line id contains `.`; schema could refuse it if ever needed) |
| T1 | paid_metric guard untested for share_metric/run_rate readers | can wait (Phase 3, unreachable by a flow today) |
| T2 | statementShape tests pin ids/of only | drop (parity proof covers values) |
| T2 | disclosure.e2e `preApprovalLitYaml` replaces only the first NOTE_NOW | drop (latent; the fixture must not be regenerated) |
| T4 M2 | Slack yields/multiples lines mix v1 and v2 sources | can wait (Task 11, removing v1 resolves it) |
| T4 M3 | fragile CLI text assertion `tests/cli/cli.test.ts:1089` | can wait (Task 11 rewrites the text output) |
| T3/4 M-a | `ratioOf` drops disclosed growth on estimate/of lines | can wait (Phase 3; unreachable) |
| T3/4 M-b | `sourceLabelOf` not given asset metrics | can wait (Phase 3; latent label) |
| T3/4 M-c | listing bar uses third_party inheritance | can wait (consistent with M4; listing bar is report-only) |
| T3/4 M-d | 'missing day' flag fires on a null cost level | can wait (Task 11) |
| T5 M2 | price cross-check record matched by sourceId+label, not contract | can wait (Phase 3, when llama price checks are replaced) |
| T5 M3 | UNI/LINK/CAKE price checks duplicate the existing cross-check | can wait (Phase 3) |
| T5 | circular rule doesn't follow mixed derived-of-adapter chains | can wait (Phase 3, before the first such check is wired) |
| T6 M6 | after a rollback N-1's latest_levels upsert leaves stale provenance | can wait; document in the I2 rollback note (must-fix with I2) |
| T7 | backfillPrices may refetch an id for a ref with no day to fill | can wait (quota only) |
| T7 | one contiguous range refetches stored hours between gaps | can wait (quota only) |
| T7 | R18 uses the current config's `usdNative` for history | can wait (same class as accepted M3; compare-usd p90 is the net) |
| T9 | no drift test on copied adapter URLs | can wait (Phase 3) |
| T9 | unknown adapter/derived names pass the template test | can wait (Phase 3) |
| T9 | no-URL test checks TERMS, not generated output | can wait (Phase 5 export) |
| T9 | fallback hosts (Base/Solana public RPC, pro-api.coingecko.com) not rows | can wait (Phase 5, before the export reads the register) |
| T9 | CoinGecko note wording | drop |
| T9 | 'date checked' on quoted rows | can wait (Phase 5) |
| T9 | T5 template line 37 contradicts 7b M-2 | **must-fix before merge** (= M5) |
| T7b | no test of an incremental `--metric` run on a group with a cursor | must-fix before merge (cheap; R20 is the rollout path) |
| T7b | ycrv R20 test step 3 doesn't check listed members' active row count | must-fix before merge (cheap; pins the exact rollout command) |
| R15 | dust breach ($0.05) on a relative-only sum check | G2 decision (with I1: decide alert vs advisory) |
| R17 | 18 unmapped provenance rows | G2 decision (backfill re-runnable) |

## Recommendations

- Fold I1, M5 and the two 7b tests into one small fix commit; I2 as a docs commit; then the rehearsal.
- In the G2 rehearsal add: Σfees + Σinc vs Σgross after the yCRV backfill (M1, both windows), the backfill depth (M2),
  one N-1 write + a real filtered restore on the proof copy (M7).

## Declined to judge

- `data set` now refuses without `--citation` for every metric (`src/cli/commands/data.ts:105-107`): spec §3 makes a
  hand-entered figure a disclosure; documented in README. Behaviour change for operators, ruled by the spec.
- All 13 config hashes move (income_statement blocks): the accepted P1-A cost; first nightly lists 13 config changes and
  pending config proposals filed against the old hashes go stale.
- R14's sender-mix approximation and its size: Mike's G1 call; the rehearsal measures it.
- Tasks 8, 10, 11 not built: gated (G2, G3, G4).
- Per-asset v2 figures inside `incomeStatement.ts`: covered by the per-task proofs, not re-derived here.
- Whether the CLI `report yield` exit code should be non-zero when the statement errors: spec silent; the JSON field
  and text line make it visible, and the nightly alerts.

## Controller rulings on the final review (binding for the final fix wave)
- I1 FIX as plan correction 12 says: a check breach makes the asset's nightly block an ALERT (isAlert counts breached checks or the check_breach anomalies the tick raised; the anomalies from recordChecks are added to report.ingest.anomalies_raised), and the block prints one line per breached check (id, type, day, gap). Tests. (Whether the sdCRV dust breach should alert is Mike's G2 decision on tolerance_abs; don't change any tolerance.)
- I2 FIX: a "Phase 2 release (migrations 0003-0005)" section in docs/ops/deploy.md with the ordered commands (prod and stage migrate in the same release step; db backfill-provenance dry run then real, R17's unmapped rows listed; yCRV by-sender backfill `data fetch ycrv --metric flow_usd.yearn_gross_fees --metric flow_usd.yearn_gross_incentives --backfill-days 183` right after the deploy and before the first nightly; data backfill-tokens per chain asset one at a time outside 05:00-06:30 PT, exit 1 = stop; data compare-usd for G2; the rollback note incl. T6 M6 and the second backfill pass for N-1 rows), and a pointer from docs/ops/postgres.md. Also the staging soak script note (`~/.hermes/profiles/raymond/scripts/orion-stage-soak.py` must pass --legacy; controller-owned, outside the repo — document only).
- M1 FIX (note wording): the yCRV partition holds by construction only for rows written by one scan; R20-backfilled history is priced at backfill time, so the controller measures Σfees+Σinc vs Σgross in the rehearsal.
- M2: rehearsal/rollout parameter = --backfill-days 183 (in I2's runbook). No code.
- M3 FIX: listCheckResults / provenanceByDay failures are caught into incomeStatementError (legacy report, tick holder_yield and snapshot never fail because of them); tests.
- M4 FIX: v2-only metrics (statementFlowMetrics not read by v1) are excluded from the LEGACY default report day computation, so legacy behaviour equals v1 exactly; v2 shows its own missing-day flag instead. Tests (yCRV before the new flows exist: legacy default day equals v1's).
- M5 FIX (T5 template line 37 wording).
- The two T7b tests: FIX (incremental --metric run on a group with a cursor; ycrv R20 step 3 checks the listed members' active row count).
- Task 6 scrub coverage (ledger line 'Task 6: minor (deferred -> final fix wave, security-cheap)', missed by the extract): FIX: query names x_cg_demo_api_key, x_cg_pro_api_key, x-api-key, auth_token, access_key, password, auth, authorization; object keys access_token, privatekey, apitoken (case-insensitive); string-valued auth/headers keys emptied too. Tests. HYPE params.token "USDC" still survives.
- Everything else in the triage table: as the reviewer triaged (can wait / drop); copied into the followups note's open items.
