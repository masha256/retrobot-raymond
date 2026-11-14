# Task 9 re-review 1 (fix round 1: 4311313..1cac987)

### Finding Verdicts

1. **Rollback mechanism wrong** — ADDRESSED. deploy.md:898-908 (at 1cac987): old `flow_usd_v` prefers CoinGecko, falls back to any stored source within 6 h, matching 0005_tokens_prices.sql (`ORDER BY CASE WHEN pr.source = 'coingecko' THEN 0 ELSE 1 END, pr.ts DESC`, `ts >= hour_start - 6h`). Says that after step 8 the hourly rows (`pricedHourlyAtIngest`) are priced from chain rows through the view and the rest from the repriced `value`, and that this lasts until the old nightly re-adds CoinGecko rows. Covers a rollback mid-release (steps 3-8): CoinGecko figures come back on the hourly rows over a partly repriced `value`, and no data is lost. Plan :365-371 is fixed the same way, in the plan's own numbering (its steps 2-6 = deploy.md steps 3-8).
2. **Stop rules not enforced** — ADDRESSED.
   (a) src/cli/commands/data.ts:333-334 sets `REPRICE_REFUSED_EXIT` (3) when any `perMetric[].refused` is non-empty, on the dry run and on `--yes`. Help text (data.ts:315-316) and the verb line (deploy.md:423-424) say so. New test tests/cli/reprice.cli.test.ts:124-152 checks exit 3 on the text dry run, the `--json` dry run and `--yes`, and that the refused row keeps its CoinGecko row. The no-refusal test now asserts exit `[]`. orion-remote `passthrough()` returns the child's returncode (files/orion-remote:387-399). New test_orion_remote.py:1075-1079 checks that 3 comes back through it for both forms.
   (b) Every prod `--yes` in the R2 block (steps 6, 7, 8a, 8b; deploy.md:749, 775, 794, 814) is in its own code block. Each has "**Stop here. Prod: only on Mike's go.**" placed before it. The closing line (:840-841) names 6, 7, 8a, 8b and says "never paste a prod `--yes` block before the go". The step 7 dry run checks rc and prints STOP on a refused row. The field names it uses (`perMetric`, `rows`, `rebuilt`, `refused`) match `RebuildMetric` (src/db/priceLevels.ts:33-40).
   (c) purge-prices: the dry run goes to `dry/purge-prices.json` and STOPs on non-empty `keptTokens`. `--yes` goes to `yes/purge-prices.json`. They are compared on (tokenRef, rows) and `deletedTokens`. The fields match `PurgePricesResult` (src/db/purge.ts). The market_data purge gets the same comparison on `observations` (`PurgeMetricCount`).
3. **'kept tokens row' → `keptTokens`** — ADDRESSED (deploy.md step 8a: "must have `keptTokens` empty (`[]`)").
4. **compare-usd --days 400 window** — ADDRESSED (deploy.md:768-770). It is stated as orion-remote's cap, and that cap is confirmed (files/orion-remote:112 `DAYS_MAX = 400`, :457). The text says the 400 days reach 2025-10-14 only until about 2026-11-18, and later the reprice dry run's `refused` list (exit 3) is the gate. The followups Task 9 section records it.
5. **Followups: Task 8 minor + 'Notes kept' rendering** — ADDRESSED. Task 8 now has the bullet "unknown future first_party:<x> label gets the contract_state rung". A blank line now separates the list from `Notes kept:`, so it renders as a paragraph.
6. **Merge/tag/push/build step** — ADDRESSED. New prerequisite 4 (deploy.md:685-688): fast-forward to `main`, tag `orion-YYYY.MM.DD.N`, push, `build.sh <tag>`, and why (deploy.sh needs origin/main).
7. **daemon.md stale retry sentence + table order** — ADDRESSED. The retry sentence now says `refresh` 2, `backfill` of op `prices` 3, every other kind 1. The `backfill` (70) row moved after `retention` (60), so the table is in priority order.
8. **T2/T3 old HTTP cross-checks, generic price-method text** — ADDRESSED. T2: the `http_json` cross-check and the `price_api_*` values are gone. It now uses `price.token_check` at 3%, matching assets/lit.yaml:40. T3: the `price_dex_usd` level, its `price_dex` check and the `dex_price_*` values are gone. It now uses a `price.token_check` cross-check at 2%, matching assets/pump.yaml:34. Neither template has `http_json`, `price_api`, `dex_price` or Jupiter left. The method text is generic (first-party venue / Solana pool reserves via our own RPC).

Checks run (own worktree `rev-t9b` at 1cac987, `npm ci`, since removed):
- `npx vitest run tests/cli/reprice* tests/config/templates.test.ts --maxWorkers=1`: 2 files, 55/55 passed.
- `python3 -m unittest scripts/provision/test/test_orion_remote.py`: 60 OK.

### New Breakage in the Fix Diff

None Critical/Important.
- Minor: deploy.md step 8a's 8a/8b split means "after step 8" in the rollback note (:902) could read as "after 8b". A rollback between 8a and 8b behaves like "after step 8" for flows, because the CoinGecko `prices` rows are already gone. Worth a few words; not blocking.
- Minor: in the followups note, `Notes kept:` (about Task 6b) now sits under `### Task 9`, so it reads as part of that section.

### Out-of-Scope Observations

- src/daemon/daemon.ts:103 comment "(only `refresh` does)" is stale in the same way daemon.md was (the implementer flagged it).

### Verdict

**Fix round:** All findings addressed, no new Critical/Important breakage.
