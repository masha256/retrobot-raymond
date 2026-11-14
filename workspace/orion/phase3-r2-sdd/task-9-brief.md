### Task 9: Release block and followups

**Files:**
- Modify: `docs/ops/deploy.md` ("Phase 3 R2 release" per env), `docs/superpowers/notes/2026-11-13-orion-phase3-r2-followups.md` (create), the spec Status
- No code.

The block, per env (stage first; prod only after the soak and Mike's go; every `--yes` on prod on Mike's go):
0. Save `before/` reports (13 assets, each asset's default day and that day minus 91).
1. `deploy.sh <env> <tag>` (0008, expand-only). Check: `status` on the tag, migrations 8.
2. `job run-now backfill-prices --from 2025-10-13`; poll `jobs` until `done`; record rows per ref, calls per chain, missing.
   Must finish before the env's nightly or be left to defer (it does on its own).
3. Per asset `data compare-usd <a>`: 0 `legacy_unpriced` on any flow that has tokens; otherwise stop.
4. Per asset `data reprice <a>` dry run, then `--yes` (stage: under the release go; prod: Mike's go). Refused rows: stop
   and bring to Mike.
5. Per asset `data rebuild-price-levels <a>` dry run, `--yes`.
6. `data purge-prices --source coingecko` dry run, `--yes`; `data purge <a> --metrics price_usd[,diem_price_usd] --source-type market_data` dry run, `--yes`.
7. Save `after/` reports; compare with Task 10's signed table (`flatdiff` with the R2 allowlist); anything outside is a stop.
8. Soak (stage): one scheduled nightly with no failed sources and no `ORION WATCH ... price` breach without a stated cause.

- [ ] **Step 1: Write** the block, the verb table lines, the rollback note (0008 is expand-only; a rollback to
  `orion-2026.11.12.1` reads `flow_usd_v`, whose CoinGecko rows are gone after step 6, so its reports read `value`,
  which step 4 re-priced: numbers stay chain-priced; the old code then re-adds CoinGecko rows nightly, so a rollback
  needs a forward fix within days) and the followups note.
- [ ] **Step 2: Commit** `docs: Phase 3 R2 release block and followups`.

