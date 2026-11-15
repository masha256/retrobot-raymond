# Final fix wave: scoped re-review (1cac987..046908f)

### Finding Verdicts

- **I1 / R32(a): price.* / usd-flow assets refused on an empty map, everywhere.** ADDRESSED. src/config/load.ts:47-51
  (`prices && prices.size === 0` → `chainPricedSources` covers primary and cross-check `price.token`/`price.token_check`
  and `transfer_flow unit: usd`). Probe: from a missing / 0-byte / comment-only prices.yaml in dev, every repo asset
  except AERO → `invalid_asset_config`, and AERO loads.
- **I1 / R32(b): release root or ORION_ENV stage/prod is strict.** ADDRESSED. load.ts:92-95 `strictPricesRoot`, :127-132
  refuses `invalid_price_config` before parsing; paths.ts:68-71 `isReleaseRoot` = `shippedRelease`. Probe (15 cases:
  3 variants × dev / release / stage / prod / release+ORION_ENV=dev): every strict case refuses all 13 assets, AERO
  included; a release root under ORION_ENV=dev is still strict. With entries the CoinGecko refusal and ref checks run
  (load.ts:52-64; test load.test "release root with the real prices.yaml … CoinGecko price refusal runs"). The dev/test
  `size > 0` gate is R34, accepted.
- **I1 / R32(c): levels and the prices backfill ALERT on an empty map, never a silent done.** ADDRESSED.
  levels.ts:73-78 sets `pricesError`, no writer call → `ORION ALERT <env> levels prices: prices.yaml has no entries`
  (:121). In a strict root every asset also fails, the ALERT is still posted (:121-127) and the job fails "every asset
  failed". backfill.ts:316-318 throws `invalid_price_config` before params/writer → the catch → `ORION ALERT … backfill
  prices failed: invalid_price_config: prices.yaml has no entries` and `failed` (:380-391). Tests levelsJob ×3 and
  backfill ×3 check the exact post and `writer.calls == []`.
- **I1 / R32(d): tests for missing/empty/comment-only + the deferred release-root test.** ADDRESSED.
  tests/config/load.test.ts "prices.yaml must be usable (Ruling R32)" (a)/(b) ×3 variants + real-prices release test;
  tests/cli/paths.test.ts:1400-1415 (resolvePaths → release root; loadAsset there gives the repo hash; ORION_HOME
  copy without prices.yaml refused).
- **I1 / R32(e): prod_copy.py copies prices.yaml per config source.** ADDRESSED. tools/phase2-proof/prod_copy.py:2257-2260;
  test_prod_copy.py `test_prices_yaml_is_copied_…` (worktree-only → new only; both → each its own). Ran OK.
- **I2 / R33: inactiveCoingeckoRows counted and printed, not rewritten.** ADDRESSED. src/db/reprice.ts:314-322 reads
  `NOT (ACTIVE)` flow_usd rows in range, classifies them with the same pure `classify` (no writes), counts non-skip;
  never added to `flows`. data.ts:92 prints `; inactive: N superseded/rejected CoinGecko-priced row(s), kept as written`
  on the dry run and `--yes`; `--json` carries it. Test reprice.test "R33" (2 counted, rejected DefiLlama row not,
  values 50/60 and no marker after `--yes`). Followups "Carried to later releases" and the spec Status line carry the
  ruled sentence verbatim.
- **M1: op-fetch backfill posts its own price breaches.** ADDRESSED. backfill.ts:440-446 (`breachLines(…,
  fetched.priceBreaches, loaded.prices)` after the fetch, before done/failed); test backfill.test M1 (22 → start, 20 +
  summary, done).
- **M2: WATCH caps shared by levels / refresh / backfill.** ADDRESSED. src/levels/levels.ts `PRICE_WATCH_MAX = 20`,
  `breachLines`; used by levels.ts:113, refresh.ts:153, backfill.ts op prices :345 and op fetch :442;
  `PRICES_BACKFILL_WATCH_MAX = PRICE_WATCH_MAX` (the op prices summary line is byte-identical, its old test unchanged
  and passing). Tests levelsJob 23 → 20 + summary, refresh 21 → 20 + summary.
- **M4: deploy.md staging_refresh gaps.** ADDRESSED in substance (deploy.md R2 block item 5, gaps (i) and (ii) both
  stated with an action). The known item stands: no pause mechanism for `staging_refresh` exists (orion-remote has no
  pause/disable verb for jobs; `asset pause` is per asset; JOB_KINDS only feeds `run-now`), so "pause `staging_refresh`
  for that Sunday" (deploy.md:695) **and** "pause the refresh (or expect it)" (deploy.md:697) are unactionable. Both
  lines need the controller's wording (finish prod's steps 6-8 before Sunday 10:30Z, or accept it and re-run 3-8 on
  stage; after a rollback, expect the refresh).
- **M5: followups note.** ADDRESSED. Task 9 minors added (marked fixed); "None blocks the release" qualified (four
  must-fix minors marked fixed (R32)); "Notes kept:" moved under Task 6b; M1-M4 listed; R32/R33 in rulings, R25 marked
  superseded in part.
- **Extras.** ADDRESSED. daemon.ts:103 comment; orion-remote usage text says exit 3 for reprice and
  rebuild-price-levels (+ test, 61 OK); rollback note "After step 8a" (8a = purge-prices, after which no CoinGecko
  `prices` rows remain, which is what the view reads).

### Re-fixtured tests (sampled for weakened assertions)

- ingest.cli: price_usd moved from `coingecko` to `price.token` on the mini entry (both Chainlink feeds answer 10);
  the stats cross-check (10 vs 10.1 within 2%) and the anomaly test (stats 12 vs 10) still exercise the same paths; the
  source list now asserts both `coingecko` (circulating_supply) and `adapter:price.token`. Intent kept.
- levelsJob / refresh: counts 10 → 8, 5 → 4, 6 → 5 are exactly price_usd dropping out (hand-entered); levelsJob
  test 1 now also pins a real price write (`written: 48`), stricter than before.
- tick.cli inserts price_usd = 10 so `holder_yield.price: 10` is still asserted; job.cli, watch.test, cli.test,
  lit.ingest, disclosure.e2e, reprice.cli, agent.cli only add a prices.yaml. load.test: the bare-root hash assertion
  now takes the config-only hash from `parseAssetYaml` and adds a refusal assertion; `parseAssetObject(obj, new Map())`
  flips not.toThrow → toThrow, as R32(a) requires.
- One small loosening: ingest.cli "data sources" `valueInForce` toEqual → toMatchObject drops `ageDays: 0` (the text
  form "0.0 days old" is still asserted on the next line). Minor, see below.

### Checks run (detached worktree .worktrees/rev-ff at 046908f, removed afterwards)

- Probe (temporary test, deleted with the worktree): 13 repo assets × {missing, empty, comment-only} ×
  {dev, release root, ORION_ENV stage, ORION_ENV prod, release root + ORION_ENV dev}: 15/15 passed with the expected
  codes (dev: AERO loads, others `invalid_asset_config`; strict: all `invalid_price_config`).
- `vitest run` (maxWorkers=1) load, paths, levelsJob, backfill, refresh, reprice, reprice.cli, ingest.cli, tick.cli,
  job.cli, watch, agent.cli: 12 files / 171 passed; nightlyReport, watchTransitions, disclosure.e2e, lit.ingest,
  cli.test: 5 files / 59 passed.
- `python3 -m unittest tools/phase2-proof/test_prod_copy.py`: OK; `scripts/provision/test/test_orion_remote.py`: OK.

### New Breakage in the Fix Diff

- Minor: deploy.md:695 and :697 tell the operator to pause `staging_refresh`; no such mechanism exists (the known item;
  :697 is a second instance of it).
- Minor: tests/cli/ingest.cli.test.ts:1307 (diff) `valueInForce` toEqual → toMatchObject no longer pins `ageDays`.
- Note (no action): src/config/load.ts now imports src/cli/paths.ts (config → cli layering); paths.ts imports only
  types.js, so no cycle. `strictPricesRoot` reads `process.env.ORION_ENV` (stated in the fix report).

### Out-of-Scope Observations

- src/app/proposals.ts:185 (approve) parses with `parseAssetYaml(edited, loadPrices(configRoot))`, not `loadAsset`,
  so the R32(b) strict-root refusal does not apply at approve. No live gap: a strict root with an empty map already
  refuses every asset load, so nothing reaches approve. Non-blocking.

### Verdict

**Fix round:** All findings addressed, no new Critical/Important breakage. One open item, already on the controller's
list: deploy.md:695 **and :697** both say to "pause" `staging_refresh`, and no pause mechanism exists. Reword both.
