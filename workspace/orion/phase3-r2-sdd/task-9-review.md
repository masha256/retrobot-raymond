# Task 9 review: 3aca04e..4311313 (docs: R2 release block, plan amendments, followups, templates)

### Spec Compliance

- ✅ Spec compliant, with one Missing item. Every step the brief asks for is present: the block (steps 0-10 map brief 0-8, with `mid/` and the compare-usd gate added); the verb lines; the rollback note; the followups note; spec Status; the plan amendments; the templates.
- ❌ Misunderstood (plan-mandated): the rollback mechanism is wrong. See Important 1. The brief's own Step 1 text has the same error, and the plan still has it at plan:365.
- ⚠️ Cannot verify from the diff: whether the hourly `levels` price_usd writes after the switch, which fall inside the default day's asOf, are covered by the R2 allowlist (step 10). That is Task 10's job. Also whether `data purge --source-type market_data` accepts the rows superseded by `rebuild-price-levels`. Task 10's block run on the copy covers it.

### Checks run (named risks)

1. **Executability.** I walked every block command against `scripts/provision/files/orion-remote` and the CLI at 4311313:
   - Exist over ssh: `report yield [<a>] --day` (orion-remote:438-442), `data compare-usd --days 1..400` (:456-458), `data reprice [--yes]` (:466-469), `data rebuild-price-levels [--yes]` (:470-473), `data purge-prices --source coingecko [--yes]` (:474-479), `data purge --metrics k1,k2 --source-type` (comma list split to `--metric` each, :301-311/:459-464), `job run-now backfill-prices --from/--to/--refs` (:548-553), `jobs --since` (:433-435), `status`, `logs`.
   - Env-user only: `o db status` is correctly marked "as the env user".
   - The prereq check holds: the R2 remote answers `needs --from` with exit 64 (:550-551); the R1 remote answers `bad job kind: ...` (orion-2026.11.12.1 orion-remote:265-271/500).
   - Exit 3 on refused reprice rows: data.ts:306-307. Every remote verb forces `--json` and passes the child's exit code through.
   - The step 5 one-liner matches `UsdComparison` (array; `metric`, `unpriced`, `gapPct`, `p50DayGapPct`, `p90DayGapPct`: src/db/prices.ts:181-213). The step 6 field names match `RepriceResult` (reprice.ts:58-86).
   - `purge-prices` refusal and `job:prices` lock: purge.ts:163-195.
   - The `deploys.log` line format matches orion-remote:1051-1052. flatdiff `--allow/--asset` exits 0/1/2 (flatdiff.py:4,291-296). The `day()`/`d91()` pattern is the R1 block's.
   - deploy.sh `<env> <tag>` signature is fine; see Minor 4.
2. **Order and gates.**
   - Present: the four RPC URLs per env; the deploy window (stage 04:45-22:45, prod 02:45-20:45 UTC, arithmetic correct); backfill queued at the switch; compare-usd -> reprice dry runs -> `--yes` -> rebuild -> purge-prices -> market_data purge; before/mid/after sets on `d` and `d-91`; the expected dry-run facts (deploy.md:778-782); any refused row = stop.
   - The step 7 and step 8 gates are weak. See Important 2.
3. **Rollback.** I read old `flow_usd_v` (0005_tokens_prices.sql:52-90) and the old `listFlowUsd` / `pricedHourlyAtIngest` (orion-2026.11.12.1 src/db/prices.ts:169-203). See Important 1.
   - Verified: the old backfill handler returns `failed` with no Slack line on `assetId === null` (orion-2026.11.12.1 backfill.ts:146). So "fails silently" holds.
4. **Record completeness.** A script grepped `Ruling R<n>` in progress.md and the findings files, and every `minor (deferred):` line, then diffed them against the note and the amendments section:
   - Rulings R1-R31: all 31 are in the followups note, and all 31 are in the amendments section (process-only ones by name).
   - Minors: 51 in the ledger, 50 in the note. The missing one is in Minor 3.
   - All six `Carry to Task 9` items are handled.
   - Stale grep over docs/ops and docs/templates finds no stale `flow_usd_v`/compare-usd claim, no 20-min/`prices` lock, no live market_chart path, no `price_coingecko_id`, no `field: price`. The leftovers are labelled history (deploy.md:305, :311).
5. **Templates.** In my own worktree at 4311313 (`npm ci`), `npx vitest run tests/config/templates.test.ts --maxWorkers=1` passed 51/51 with clean output.
   - Every T1-T10 has exactly one `name: price.token,` with a `{{price_ref}}` placeholder, plus a prices.yaml pointer. None has `field: price`.
   - T7/T10 are refused only for their dummy ref (templates.test.ts:1901-1919 as in the diff).

### Strengths

- The block is concrete and scriptable. It keeps every output in `~/r2-<env>/{dry,yes,...}`, checks exit codes, adds `mid/` as a bisect point, and pins the `d-91` day from the saved `before/` file, so a moved default day can't skew the diff.
- The expected dry-run facts, the refusal semantics (exit 3, `refused` lists, `keptTokens`) and the export paths all match the code.
- The followups note is complete for the rulings, and honest where a ruling stated no cost (marked "assessed here").
- The amendments section maps each ruling to the plan text it overrides. Task 7's Interfaces were fixed inline.
- The template tests read both blocks from each doc and load against the committed prices.yaml, so docs and code can't drift.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)

1. **docs/ops/deploy.md:854-858, plan:365-367: the rollback mechanism is false (plan-mandated wording).**
   - The note says the old release "reads `flow_usd_v`, which after step 8 has no CoinGecko `prices` rows, so its reports fall back to `value` for every hourly row".
   - But the old `flow_usd_v` reads prices of **any** source (0005_tokens_prices.sql:84-87: `ORDER BY CASE WHEN pr.source='coingecko' THEN 0 ELSE 1 END, pr.ts DESC`, within 6 h at or before the hour).
   - So after the backfill, every hourly row with all its hours priced gets `usd_basis = 'hourly'` from the **chain** rows. The old report then uses that view USD for rows whose `fetched_at` is within 90 days of the day (`pricedHourlyAtIngest`), and `value` only for the rest.
   - The conclusion ("figures stay chain-priced until its nightly re-adds CoinGecko rows") still holds. The stated mechanism does not, and risk 3 asks for no claim the code can't support.
   - Also unstated: a rollback between steps 3 and 8 (CoinGecko rows still present) gets the view preferring CoinGecko over chain. That release then reads CoinGecko-priced view USD on top of partly repriced `value`.
   - Fix: reword both places to "reads `flow_usd_v`, which prefers CoinGecko rows but falls back to any stored price. After step 8 it prices hourly rows from the chain rows (and reads the repriced `value` elsewhere)". Add a line for a rollback before step 8. On a roll-forward, re-save `before/`.
2. **docs/ops/deploy.md:795-819: the step 7/8 stop rules are not enforced, and the prod `--yes` sits ahead of its gate.**
   - Step 7's refused row is the stop before the purge. But `data rebuild-price-levels` exits 0 when rows are refused: data.ts:312-327 sets no exit code, unlike reprice. So the `|| { echo STOP; break; }` on line 798 can never fire, and no check of `perMetric[].refused` is given (step 5 has one for compare-usd).
   - The dry-run loop and the `--yes` loop are one paste block (797-798).
   - In step 8, `purge-prices --source coingecko --yes` (807) comes **before** the `# after pasting the dry-run counts (prod: on Mike's go)` comment (812). Copying the block on prod runs the irreversible purge before the go. purge-prices output is also not saved to `dry/`/`yes/`, though "each deleted count must equal its dry run's".
   - Fix:
     - Add a one-liner over `dry/rebuild-*.json` that prints STOP when any `perMetric[].refused` is non-empty.
     - Split each dry run and `--yes` into separate blocks, with "stop here; prod: Mike's go" between them, as in step 6.
     - Redirect both purge-prices calls to `dry/purge-prices.json` and `yes/purge-prices.json`.

#### Minor (Nice to Have)

1. deploy.md:819: "must list no `kept tokens row`" is the text output. Over ssh the output is JSON, so name `keptTokens` (empty array).
2. deploy.md:759: `--days 400` reaches the first flow day (2025-10-14) only until ~2026-11-18. Prod will run later. Say that older days are covered by the reprice dry run's `refused` list (ledger note, report concern 2), or use `reprice` alone as the gate for the older days.
3. Followups note:
   - It lacks the Task 8 minor "an unknown future first_party:<x> label gets the contract_state rung", which was logged after the note, as its :176 caveat warns, and the ledger's Task 9 compare-usd note.
   - The `Notes kept:` line at note:196 directly follows a list item, so it renders as a lazy continuation of "CLI tests written after the code". Add a blank line.
4. deploy.md R2 prerequisites: no step says to merge `feat/phase3-third-party` and tag on `main`. deploy.sh refuses a commit not on `origin/main` (prod refuses `--branch`; deploy.sh:13-16). Section 1 covers this in general, but this branch is explicitly unmerged.
5. daemon.md:74:
   - "only `refresh` has a second attempt" is now stale (op `prices` has 3).
   - The `backfill` row (priority 70) is inserted before `retention` (60), breaking the table's priority order (:70-71).
6. Templates:
   - T2 (:73) and T3 (:72) keep their `http_json` price cross-check (Lighter API) and the Jupiter `price_dex_usd` level, while live `lit.yaml` and `pump.yaml` moved to `price.token_check`.
   - The generic "a primary (a Chainlink feed, else the deepest pool's TWAP)" text in T2:26 and T3:21 doesn't describe LIT (Lighter candle) or PUMP (PumpSwap reserves).
   - This drift from the live assets predates R2 in part; not blocking.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The block is executable as written and matches the verbs, flags, exit codes and JSON shapes at 4311313, and the record is complete for all 31 rulings. But the rollback note states a mechanism the old view contradicts, and the step 7/8 refusal and prod-go gates rely on prose where the code gives no exit signal, ahead of an irreversible purge.
