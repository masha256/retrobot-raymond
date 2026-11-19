# R3 scoping: code and data (measured 2026-11-19 14:30-14:45Z, prod read-only via sql-ro / report yield)

Base: GitHub main 02f39e3 = `orion-2026.11.15.1` (R2) on stage and prod, migrations max 8.
Branch for the plan: `feat/phase3-r3-supply` off 02f39e3 (worktree `.worktrees/phase3-r3`).

## 1. What circulating_supply feeds (code read, confirmed on prod's 13 reports)

- `report.marketCap` = price x circulating (`src/report/holderYield.ts:234`), and the v2 statement's
  `multiples.mcapToRevenue`, `mcapToGrossProfit`, `mcapToHolderFlow.{burn,hold,cash,total}`
  (`incomeStatement.ts:847-853`), `perToken.{revenue,grossProfit,holderFlow.*,dilution,circulatingSupply}`
  (`incomeStatement.ts:1015`, per circulating token; `perTokenFdv` is per total and does not move).
- Tick report `market_cap` (`src/app/tickReport.ts:69`), the Slack nightly line (`src/notify/format.ts`), the snapshot
  `full` body (it embeds `report yield`) and `levels` body (`latest_levels` rows).
- **No yield reads it.** `yields.{cash,buyback,shareholder,dilution,netShareholder,multiple,pegTrailing}` divide by
  `recipients(base)` = total_supply (`all`), staked or locked supply (`holderYield.ts:158`), times price. Checked on prod:
  hf.net / fdv == yields.shareholder on every asset whose lines use base `all` (CAKE 10.49%, HYPE 1.669%, LINK 0.589%,
  ...). So "every yield on market cap" = the inverse multiples (holder flow / mcap = 1 / mcapToHolderFlow.total): they
  move 1:1 (inversely) with circulating. Growth, PEG, revenue, holder flow, dilution and every yield are untouched.

## 2. CoinGecko reads left in live code after R2

- 9 YAML `circulating_supply` sources `{ type: coingecko, field: circulating_supply }`: CAKE, CRV, HYPE, LINK, LIT,
  PUMP, SKY, UNI, VVV. No `total_supply` CoinGecko check is left (R1 removed them); VVV's circulating cross-check is
  Venice's first-party `vvv_stats` (stays).
- `src/levels/levels.ts:104-140`: the hourly `levels` job batches `/coins/markets` for every coingecko id
  (`coingeckoIds`, `prefetchMarkets`, `withPrefetchedMarkets`). With no coingecko source configured, `ids` is empty
  and no call is made (`prefetchMarkets` returns early per batch; `levels.ts:202`).
- `src/ingest/sources/coingecko.ts` (the source), `src/config/sources.ts:8` (zod type, fields price / market_cap /
  circulating_supply / total_supply), `coingeckoPriceIssues` (R24/R25: refuses `field: price` at load, filing,
  approve). The type itself is deleted in R8 (spec §3.5).

## 3. Stored CoinGecko-derived data on prod (2026-11-19)

`observations`, metric `circulating_supply`, source_type `market_data`, all active, none superseded/rejected:
- aero 45 (2026-09-24..11-10; 25 before 2026-10-22, i.e. before the new AERO token's pools; AERO has its own
  contract_state rows from 11-10), cake 40, crv 43, hype 55, link 37, lit 38, pump 37, sky 36, uni 40, vvv 57
  = **428 rows / 10 assets**. Each nightly adds 1 per CoinGecko asset (9/day) until the release.
- LINK (766,849,970) and LIT (250,000,000) are constant over every stored row: CoinGecko's figure is static there.
- Not CoinGecko: VVV 1 `disclosure` row (2026-09-18, 48.35M, cited) - keep; the wrappers' and AERO's
  `contract_state` rows - keep.
- `latest_levels`: 9 rows `circulating_supply` source `api` / `market_data` (written hourly; PK asset+metric, so the
  first hourly run on the new release overwrites each).
- No `market_data` row of any other metric remains (R2 purged prices).
- Published snapshot repo `masha256/orion-data`: past commits carry CoinGecko-derived `marketCap`/circulating. Not
  "stored" in Orion's DB; rewriting git history is a Phase 5 question (decision listed).

## 4. Which history can be rebuilt

The report reads the newest circulating row at or before its as-of (staleness 14 d). Purging without a rebuild sets
`marketCap`, the mcap multiples and perToken to null on every report day from the first stored row (2026-09-20) to the
release day. D-91 reports (2026-08-19 for D = 11-18) predate every circulating row: marketCap is already null there,
so the gate's D-91 pair cannot move.
- EVM `chain.view_sum` terms are plain views: readable at an archive block for each stored `observed_at` (one
  multicall per row; ~380 rows => ~400 calls + block search, cached in `day_blocks`/`hour_blocks`). CAKE (BNB), CRV,
  LINK, LIT, SKY, UNI (Ethereum), VVV (Base), AERO from 2026-10-22.
- HYPE (Hyperliquid API: latest only) and PUMP (Solana: no archive balance reads; signature replay is costly): no
  rebuild; their 55 + 37 rows can only be purged (history starts on the release day).
- AERO's 25 rows before 2026-10-22 (pre-migration token): purged without replacement (as R2's 25 price rows, R38).

## 5. Code R3 needs (sized from the scoping files)

- YAML: 9 `circulating_supply` sources replaced (view_sum / adapters), contract entries with citation comments, hash
  re-pins for those 9 (plus any golden that prints source labels).
- Loader: extend the R24 refusal from `field: price` to every coingecko field (circulating_supply, total_supply,
  market_cap) at load, filing and approve (three tests), so a config proposal can't bring it back before R8.
- New adapters only where view_sum can't express the method (from the per-asset files): HYPE first-party, PUMP
  Solana token-account sum; anything else stays view_sum.
- A rebuild verb for supply levels (`data rebuild-supply-levels <a>`, dry run default, `--yes`), mirroring
  `rebuild-price-levels` (insert at the same `observed_at`, supersede the CoinGecko row; refused/listed when the read
  fails; `beforeValidFrom` analogue = `not_rebuildable` for non-EVM and pre-cutoff rows), and `data purge <a> --metrics
  circulating_supply --source-type market_data` (exists, R1 verb; it has no replacement check for this metric; the
  plan adds the R38-style refusal for circulating so a rebuildable row is never purged unreplaced).
- orion-remote: `data rebuild-supply-levels` verb (needs Mike's `orion-host.sh` re-run, as R1/R2).
- No migration expected (no schema change): rollback to `orion-2026.11.15.1` is a plain redeploy, but the old release
  would re-add CoinGecko circulating rows nightly, so a rollback needs a forward fix within days.
