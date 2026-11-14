# Task 9 report: release block, plan amendments, followups, spec Status, templates

Status: DONE. Commit 4311313 `docs: Phase 3 R2 release block, plan amendments, followups; templates price via price.token`
(base 3aca04e). No src change.

## What

- **docs/ops/deploy.md "Phase 3 R2 release"** (new section before "The ssh verbs"):
  - Prerequisites: Task 10 signed and `r2-allowlist.json` in the tag; Mike re-runs `orion-host.sh` (R2's orion-remote
    adds backfill-prices/reprice/rebuild-price-levels/purge-prices; check: `$ST job run-now backfill-prices` exits 64
    `needs --from`, the R1 one says `bad job kind`); all four RPC URLs in each `.env` (ETH also for the USDC/USD feed of
    HYPE/LIT/PUMP, R5); a normal non-`--breaking` deploy, staging first; Sunday staging_refresh schema-mismatch note.
  - Timing: deploy outside the -4 h/+2 h nightly window (stage 04:45-22:45, prod 02:45-20:45 UTC); queue the backfill
    right after the switch; it defers itself; a nightly before it finishes prices only its scan day inline. A nightly
    between step 0 and the gate adds its writes to the diff: run the gate anyway and bring unallowed paths to Mike.
  - Block steps 0-10: before/ (default day and day-91, 13 assets) -> deploy (migrations [8]) -> switch check ->
    `job run-now backfill-prices --from 2025-10-13` (frozen to, cap 550, 10-min runs, job:prices, 3 attempts; record rows
    per ref, calls per chain, missing vs Task 10) -> mid/ -> `compare-usd --days 400` (`unpriced` 0 per metric) ->
    `reprice` dry runs (exit 3 = STOP; only coingecko:crvusd / coingecko:yearn-crv remapped; PUMP ~21 / ~369
    defillama_history) then `--yes` -> `rebuild-price-levels` dry/`--yes` (refused = stop, R31) -> `purge-prices
    --source coingecko` dry/`--yes` -> `data purge <a> --metrics price_usd[,diem_price_usd] --source-type market_data`
    dry/`--yes` -> after/ -> flatdiff before/ vs after/ with r2-allowlist (both days). Prod `--yes` only on Mike's go.
  - Soak note (stage differs from prod by the repricing; verdict vs the Task 10 table; controller updates the soak cron
    prompt outside the repo) and the corrected rollback note (0008 expand-only; old release reads flow_usd_v -> falls
    back to already-repriced `value` until its nightly/levels re-add CoinGecko rows; a queued/deferred prices backfill
    fails silently on it: wait for `done`; fix forward within days).
  - Stale fixes: :308 flow_usd_v -> flow_usd_chain_v note (dailyMean, no beyond/beyondHourly); :303 market_chart and
    :292 CoinGecko daily points marked as that release's path; `.env` prerequisite names the four RPC URLs and limits
    COINGECKO_API_KEY to circulating supply until R3; compare-usd verb line explains the R2 output.
- **docs/ops/daemon.md**: levels row (writes missing chain-price hours in the last 48 h, posts breaches); `backfill`
  kind row (was missing; priority 70, op prices 3 attempts, 10-min runs); Slack lines `ORION WATCH <env> price ...`,
  `ORION ALERT <env> levels prices`, `ORION BACKFILL <env> prices done` / `ORION ALERT <env> backfill prices`.
- **docs/ops/postgres.md**: a 0008 paragraph.
- **Plan**: inline fixes at Task 7 Interfaces (lock `job:prices`, 10 min, refs regex, frozen to / 550, max_attempts 3)
  and Task 9 (rollback addendum, commit subject); new "Amendments made during execution" section (R2, R3/R4/R15/R16,
  R5, R6, R7/R18, R8, R9/R10, R11, R12, R14, R17, R19, R21, R22, Task 6 findings A-D, R24, R25, R26/R29, R27/R28,
  R30 + exit 3, R31, Task 9).
- **Followups note** `docs/superpowers/notes/2026-11-13-orion-phase3-r2-followups.md`: open items for Mike (Task 10
  sign-off, HYPE same-venue, sdCRV no independent check, prod --yes, licence notes); all 31 rulings with cost if wrong
  (R8, R11, R12, R15, R27, R28, R30, R31 state none: marked "not stated", with an "assessed here" line where I added
  one); binding review fixes; all 50 `minor (deferred)` lines grouped by task (verbatim, generated from progress.md)
  plus the 6b note; carries (R3, R4-R7, R6 PUMP history + token twins, R8 coingecko type + http_json guard, rollback
  window, exports to keep, soak prompt).
- **Spec Status**: one bullet (2026-11-14 R2 built, commits 4498513..3aca04e + this docs commit, plan amendments,
  release block, followups note).
- **Templates T1-T10**: `price_usd` source = `{ type: adapter, name: price.token, params: { ref: "{{price_ref}}" } }`
  with a comment pointing at prices.yaml; `price_ref` example values = the live asset's prices.yaml ref (T7/T10 dummy
  refs). T1/T7/T8 (the ones with a Chainlink `contract_read` cross-check and `type: price` check) now use
  `price.token_check` like the live UNI/LINK, and drop the `chainlink_price` contract / `chainlink_feed_address`
  placeholder. Input/check prose updated (CoinGecko id = circulating only until R3; T4 CRV and T6 SKY checks per M1).
  README gains a "Prices from prices.yaml" rule.

## Tests

- RED (templates.test.ts with two new tests per doc, old templates): first new test 10 failed / 31 passed
  (`expected [ Array(1) ] to deeply equal []`: the CoinGecko price issue); with both new tests on the stashed old
  templates 20 failed / 31 passed (51).
- GREEN: `tests/config/templates.test.ts` 51/51. New tests: (1) no CoinGecko price (`coingeckoPriceIssues`) and
  `price_usd` is `price.token` with a well-formed ref; (2) the filled skeleton loads with the committed prices.yaml
  (T1-T6, T8, T9), and T7/T10 (dummy) are refused only for their unpriced ref.
- Full: `npx vitest run --maxWorkers=2` 154 files, 1950/1950 passed (3aca04e reported 1930; +20 new). `npm run
  typecheck` clean. `python3 -m unittest scripts/provision/test/test_orion_remote.py` OK. The two shell/python
  one-liners in the block were run on a sample (d-91 arithmetic, the unpriced filter).

## Self-review / concerns

1. The `mid/` set is a bisect aid only; I did not assert that `data reprice` is report-neutral (the report already
   reads flow_usd_chain_v after the backfill), because nothing measured it. Task 10 can tighten step 4/6 into a `cmp`.
2. `compare-usd --days 400` covers from about 2025-10-14 only until ~2026-11-18; older days are covered by the reprice
   dry run's `refused` list. If the release slips, the 400-day cap no longer reaches the first flow day.
3. Cost-if-wrong for R27, R28, R30, R31 (and R8, R11, R12, R15) is not stated in the ledger; the note says so and adds
   my assessment labelled "assessed here". The controller may want to replace them.
4. The rollback claim "a queued/deferred prices backfill fails silently on the old release" is taken from the dispatch
   (Task 7 findings carry); I did not test the old release's handler.
5. I added a `backfill` row to daemon.md's job table (it was missing since R1) and the 0008 paragraph to postgres.md:
   outside the brief's file list but within "every other stale statement".
6. Historical plans/notes/specs (Phase 2, R1, research token docs) still name market_chart / flow_usd_v /
   price_coingecko_id as history; left unchanged on purpose.

## Fix round 1 (task-9-findings.md items 1-8)

1. **Rollback mechanism** (deploy.md rollback note; plan Task 9 Step 1): rewritten. Old `flow_usd_v` prefers a
   CoinGecko price but falls back to any stored source (0005:84-87); the old report takes view USD for `hourly` rows
   inside `pricedHourlyAtIngest` (day within 90 days of fetched_at; checked at `git show orion-2026.11.12.1:src/db/prices.ts`)
   and `value` elsewhere. After step 8: chain rows through the view + repriced `value`; chain-priced until the old
   nightly re-adds CoinGecko rows. New: rollback between steps 3 and 8 (CoinGecko rows present: the old view prefers
   them, CoinGecko figures again, no data lost); on roll-forward re-save `before/`. Plan line fixed the same way.
2. **Stop rules.**
   (a) Code: `data rebuild-price-levels` sets exit 3 (`REPRICE_REFUSED_EXIT`) when any `perMetric[].refused` is
   non-empty, dry run and `--yes` (src/cli/commands/data.ts); help text says so; deploy.md verb line says so.
   - RED: new test `rebuild-price-levels: a refused row exits 3 (dry run and --yes) and keeps its CoinGecko row` in
     tests/cli/reprice.cli.test.ts (plus exit `[]` asserts on the no-refusal test).
     `npx vitest run tests/cli/reprice.cli.test.ts --maxWorkers=1` -> `AssertionError: expected [] to deeply equal [ 3 ]`,
     Tests 1 failed | 3 passed (4).
   - GREEN: same command -> Tests 4 passed (4).
   - orion-remote: `passthrough()` returns the child's code (generic `test_exit_code_is_the_childs`); added
     `test_rebuild_price_levels_exit_3_passes_through` (dry run and --yes return 3). Python suite 60 OK.
   (b) Steps 6, 7, 8a (purge-prices), 8b (market_data purge): each dry run and its `--yes` are separate blocks, with
   "**Stop here. Prod: only on Mike's go.**" before every `--yes` block; the closing prod line names steps 6, 7, 8a, 8b.
   Step 7 dry run checks the exit code and a one-liner prints per-metric counts and STOP on any refused row; `--yes`
   then a dry-vs-yes `rebuilt` comparison.
   (c) purge-prices dry run -> `dry/purge-prices.json` (one-liner: rows, refs, deletedTokens, STOP on non-empty
   `keptTokens`), `--yes` -> `yes/purge-prices.json` and a dry-vs-yes comparison (rows per ref, deletedTokens); the
   market_data purge gets the same `observations` comparison. All five one-liners run on sample JSON in $TMPDIR
   (ok / STOP paths both seen).
3. Step 8 names the JSON field `keptTokens` (empty array), not the text line.
4. Step 5: `--days 400` is orion-remote's cap (DAYS_MAX = 400; the CLI itself has no cap); reaches 2025-10-14 only
   until ~2026-11-18; later the older days are gated by step 6's reprice dry run (`refused`, exit 3).
5. Followups note: Task 8 minor (unknown first_party:<x> label -> contract_state rung) and a Task 9 section (the
   compare-usd window note from progress.md:184); blank line before `Notes kept:`; the "re-review still running" caveat
   replaced.
6. Prerequisite 4 (new): merge `feat/phase3-third-party` to `main` (fast-forward), tag `orion-YYYY.MM.DD.N` on main,
   push, `build.sh` (deploy.sh refuses a commit not on origin/main); old 4 is now 5.
7. daemon.md: retry sentence now `refresh` 2, op `prices` backfill 3, others 1; `backfill` (70) row moved after
   `retention` (60).
8. T2/T3: dropped the `http_json` cross-check (T2 Lighter API; T3 Jupiter `price_dex_usd` level and its `price_dex`
   check) and their example values; both now cross-check with `price.token_check` like live lit.yaml (3%) / pump.yaml
   (2%); price-method prose generic: first-party venue (LIT example) / Solana pool reserves via our own RPC (PUMP example).

Tests: reprice.cli 4/4, templates 51/51; `npx vitest run --maxWorkers=2` 154 files, 1951/1951 passed (no
load-sensitive failures); `npm run typecheck` clean; `python3 -m unittest scripts/provision/test/test_orion_remote.py`
60 OK.

Concerns: src/daemon/daemon.ts:103 comment "(only `refresh` does)" is equally stale; not touched (code comment, outside
the findings). `rebuild-price-levels --yes` still writes the rebuildable rows before exiting 3 (same as reprice);
the block never reaches `--yes` after a refused dry run.
