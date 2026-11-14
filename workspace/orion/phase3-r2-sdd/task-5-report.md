# Task 5 report: the chain-only view and the report basis

Status: DONE. Commit 7ff7562 `feat(prices): chain-only flow USD view (0008) and the report basis without the ingest gate` (BASE b50e94b).

## What

- **0008** (appended; header comment updated; no `-- breaking`; `flow_usd_v` not referenced by any DDL): `CREATE VIEW flow_usd_chain_v`
  with `flow_usd_v`'s 13 columns in order (pinned by an information_schema test).
  - Hourly lateral: price rows restricted to `(starts_with(pr.source, 'chain:') OR starts_with(pr.source, 'first_party:'))`
    (methodSource() emits `chain:<kind>`, `first_party:hyperliquid`, `first_party:lighter`), `ts <= hour_start AND ts >= hour_start - 6h`,
    `ORDER BY pr.ts DESC, pr.fetched_at DESC, pr.source` (R6; `source` only as a final deterministic tie-break).
  - `daily_mean`: `hourly_amounts IS NULL`, `amount` not null, `token_ref <> 'usd'`, `period_days = 1`; the 24 hours
    `[observed_at - 24h, observed_at)` each need a chain row AT that ts (no 6-hour carry: otherwise 23 hours would still read
    daily_mean, contradicting the brief's 23 -> legacy_no_hourly). One price per ts (DISTINCT ON ts, newest fetched_at).
    `usd = amount x avg`. `hours_priced` = priced hours of the 24, `hours_needed` = 24 for such rows (0 otherwise, as before).
  - Basis order: usd_native, hourly, legacy_unpriced, daily_mean, legacy_no_hourly, legacy_no_tokens.
- **src/db/prices.ts**: `type PriceBasis = 'hourly' | 'daily_mean' | 'usd_native' | 'legacy'`; `priceBasisOf(usdBasis)` (one arg);
  `HOURLY_SERIES_DAYS` and `pricedHourlyAtIngest` deleted; `listFlowUsd` reads `flow_usd_chain_v` (no observations join).
  `compareUsd` reads `flow_usd_chain_v`, one priced group: `UsdComparison` loses `beyondHourly`/`beyond`, gains `dailyMean`;
  `hourlyCovered` = days in the sums (hourly + daily_mean + usd_native); `unpriced/noTokens/noHourly` kept.
- **src/cli/commands/data.ts** (compare-usd text/description follow the new fields) and **tests/cli/ingest.cli.test.ts**
  (its compare-usd assertions): outside the brief's file list, but required for "compareUsd must keep working".
- **incomeStatement.ts**: `priceBasis.flows` text (loader path) now: "each flow day's USD from its tokens x the chain/first-party
  hourly prices where every hour with an amount is priced (hourly), or its day amount x the mean of the day's 24 chain hours
  (daily_mean), else the stored value (per line: priceBasis)"; LinePriceBasis doc names daily_mean. load.ts / holderYield.ts: doc comments.
- **parity.ts**: fields unchanged; doc note that pairs read numbers only, never a line's basis label. New test: every parity
  asset's report with all USD days on `daily_mean` reads the same pairs (10 cases).

## Tests (RED -> GREEN)

- tests/db/prices.test.ts, before implementation: 10 failed | 7 passed (17) (view missing; priceBasisOf('hourly') -> 'legacy';
  listFlowUsd gave `{usd: 30, basis: 'legacy'}` for the >90-day row; compareUsd shape). After: 17/17.
  New: columns equal flow_usd_v + 0008 never touches flow_usd_v; CoinGecko-only -> new `legacy_unpriced` / old `hourly`;
  chain rows -> hourly at chain price (old view still CoinGecko-first) and first_party prices; newer CoinGecko row ignored and
  6-hour rule on chain rows; R6 tie (newer fetched_at wins, and flips on re-write); daily_mean 24 hours -> amount x mean,
  23 (+ a CoinGecko row in the gap) -> legacy_no_hourly with hours_priced 23; next day's 00:00 not counted; two sources at one hour
  counted once; daily_mean DST/TimeZone independence; priceBasisOf table; listFlowUsd no gate; compareUsd no split.
- tests/report/priceBasis.test.ts (R17: seeds `chain:chainlink`, same values), with src/db/prices.ts + 0008 stashed: 4 failed | 8
  passed (12) (flows text; no-gate; CoinGecko never read; daily_mean report). After: 12/12.
- Golden (tests/report/v2Golden.test.ts): 39 failed | 28 passed before re-pin; regenerated with UPDATE_GOLDEN=1, 67/67.
- Full: `npx vitest run --maxWorkers=2` -> 150 files, 1856/1856 passed (no load timeouts this run). `npm run typecheck` exit 0,
  `npm run lint:promises` exit 0, `python3 -m unittest scripts/provision/test/test_orion_remote.py` OK.

## Golden diff (flattened old vs new, every changed path)

Script: flatten each entry's report JSON (lists keyed by `id`), compare per entry; inputs compared too.
- Inputs: 0 changed (65/65 identical hashes).
- Changed paths: exactly ONE path, `incomeStatement.priceBasis.flows`, in 39 entries = 13 assets x {loader, prior, growing-loader}
  (aero, cake, crv, cvxcrv, hype, link, lit, pump, sdcrv, sky, uni, vvv, ycrv). The `stored`/`growing` entries are byte-identical.
- No revenue, cost, holder-flow, yield, dilution, grade, price or line-priceBasis value path moved. v1 golden untouched.

## Self-review / concerns

1. `priceBasis.source` in the goldens still reads `market_data:coingecko`: it is the `price_usd` metric's adapter label, which
   changes only when Task 6 swaps the asset price adapters. The brief's "source shows the method (chain:chainlink etc.)" could
   not move in Task 5 without touching asset YAMLs; flag for Task 6's golden re-pin.
2. daily_mean requires `period_days = 1` and a chain row at exactly each of the 24 hours (no 6-hour carry). This is my reading of
   "24 chain hours priced in the day"; if Task 8's reprice wants carry-filled hours, the view changes.
3. Golden loader fixture (`loaderLike`) still feeds only `hourly`/`legacy` bases (input hashes pinned); daily_mean on the report
   path is covered by priceBasis.test.ts and the parity test instead.
4. `flow_usd_chain_v` keeps `hours_priced`/`hours_needed` meaningful for daily rows (n of 24 / 24) where flow_usd_v reports 0/0:
   same column names and types, different values on non-hourly rows (intended, useful to Task 8/9's dry run).
5. docs/ops/deploy.md line 308 still describes compare-usd against flow_usd_v (Phase 2 release-block history); left for Task 9's docs.
