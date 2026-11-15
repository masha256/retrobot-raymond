# Final review fix wave: report (base 1cac987)

One commit 046908f: `fix: final review wave: prices.yaml must be present (release/live strict), levels/backfill refuse an empty map; inactive CoinGecko rows counted; breach posts capped; docs`.
Env for every TS run: `ORION_TEST_DATABASE_URL='postgresql://orion_dev@/orion_test?host=/var/run/postgresql'`.

## I1 / Ruling R32: prices.yaml integrity

**(a) chain-priced assets refused on an empty map, everywhere.** `src/config/load.ts` `parseAssetObject`: when a prices map
is given and is empty (the root's prices.yaml missing, 0 bytes or comment-only all parse to an empty map), every
`price.token` / `price.token_check` source (primary or cross-check) and every `unit: usd` transfer_flow is refused:
`invalid_asset_config`, `metrics.<k>.source (<what>): reads a chain price, but prices.yaml has no entries (missing,
empty or comment-only)`. A hand-built asset (`parseAssetObject` without a map) is unchanged. AERO (no price.* source,
no usd flow) still loads in dev.

**(b) strict release / live roots.** `src/cli/paths.ts` exports `isReleaseRoot(root)` (= `shippedRelease`: a `RELEASE`
file, not a git checkout, exactly as resolvePaths tells one). `loadAsset` refuses every asset (`invalid_price_config`,
`<root>/prices.yaml is missing|has no entries: a release (or ORION_ENV stage/prod) needs prices.yaml with at least one
entry; <id> is not loaded`) when the map is empty and the root is a release root or `process.env.ORION_ENV` is stage or
prod. There the map always has entries, so the CoinGecko price refusal and the ref checks (gated on `size > 0`) always
run. Dev/test roots keep the `size > 0` gate (I tried making it unconditional: 6 dev fixtures with a CoinGecko price and
no prices.yaml failed, contrary to R32(b)'s "dev/test fixtures keep their current behaviour"; reverted, and
`adapters/price.ts:47` left as is for the same reason: an empty map refuses price.token by (a) first anyway).

**(c) levels and the prices backfill.** `src/daemon/jobs/levels.ts`: an empty map sets `pricesError = 'prices.yaml has
no entries'` and runs no price write → one post `ORION ALERT <env> levels prices: prices.yaml has no entries`.
`src/daemon/jobs/backfill.ts` op prices: an empty map throws `invalid_price_config: prices.yaml has no entries` before
params/writer → failed + `ORION ALERT <env> backfill prices failed: invalid_price_config: prices.yaml has no entries`.

**(d) tests (RED then GREEN).**
- `tests/config/load.test.ts` "prices.yaml must be usable (Ruling R32)": for missing / empty / comment-only: (a) every
  repo asset except AERO refused `invalid_asset_config`, LIT's message, the usd-flow-only refusal message, AERO loads in
  dev; (b) a release root refuses every asset incl. AERO `invalid_price_config`; ORION_ENV stage/prod (no RELEASE)
  refuses AERO; ORION_ENV dev loads it. Plus a release root with the real prices.yaml under ORION_ENV=prod: every asset
  hash = repo hash, and a CoinGecko `field: price` asset is refused.
- `tests/cli/paths.test.ts` "a release root, not ORION_HOME, supplies prices.yaml" (the deferred Task 1 minor):
  resolvePaths gives the release root; loadAsset there has prices and the repo hash; the same asset in ORION_HOME
  (no prices.yaml) is refused.
- `tests/daemon/levelsJob.test.ts` ×3 (missing/empty/comment-only → the ALERT, no writer call);
  `tests/daemon/backfill.test.ts` ×3 (failed + ALERT, no writer call).
- RED (before the code): load+paths `7 failed | 37 passed (44)` (the six (a)/(b) cases and the paths test; the
  release-with-real-prices test passed from the start, as a guard); levels/backfill RED in the batch below.
- Existing assertions updated as the ruling implies: load.test "a root without prices.yaml hashes the config alone"
  now takes the config-only hash from `parseAssetYaml` without a map and expects the bare root to refuse;
  `parseAssetObject(obj, new Map())` now throws.

**Fixture fallout of (a)** (42 existing tests failed with the code alone; fixed in fixtures, no production change):
- `tests/helpers/ingestAsset.ts`: `MINI_PRICES_YAML` (the mini token entry already used inline by 3 tests),
  `forPricedRoot(yaml)` (INGEST_ASSET_YAML's CoinGecko price_usd block → the hand-entered one of
  PRICED_INGEST_ASSET_YAML; other YAML unchanged), `writeMiniHome(home, id, yaml)`.
- `tests/helpers/levelsWorld.ts`: writes `forPricedRoot` YAMLs and the mini prices.yaml (tests needing another
  overwrite it). Knock-ons: levels test 1 `rows 10 → 8` and `prices: null → { written: 48, … }` (the root now has a
  ref, the harness's fake writer writes it); onLevels `[5] → [4]`; refresh latest_levels lose `price_usd`, `levels 6 → 5`.
- CLI homes via `writeMiniHome`: job.cli, tick.cli (the report-price test inserts a price_usd=10 observation, as
  CoinGecko gave it), watch.test. ingest.cli: price_usd reads `price.token` on the mini entry (harness RPC answers both
  Chainlink feeds 10 via `feedCalls`), keeping the stats cross-check and anomaly tests; expectations moved from
  `coingecko`/`api` to `adapter:price.token`/`onchain`, observedAt = the run block (NOW − 1 s).
- Real-asset homes copy the repo prices.yaml: lit.ingest, cli.test (hype/crv), disclosure.e2e (both homes);
  reprice.cli writes an RPX entry; agent.cli's stage test writes MINI_PRICES_YAML + MINI_HOLDER_YAML (stage is strict).

**(e) prod_copy.py.** `make_homes` copies `<src>/prices.yaml` (when a file) into each home from its own config source
(old: release dir, new: worktree); docstrings updated. Test
`HomesTest.test_prices_yaml_is_copied_into_each_home_from_its_config_source_when_present` (worktree only → new only;
both → each its own). `/usr/bin/python3 -m unittest tools/phase2-proof/test_prod_copy.py tools/phase3-proof/test_flatdiff.py`:
RED `Ran 69 … FAILED (errors=1)` (FileNotFoundError new/prices.yaml) → GREEN `Ran 69 … OK`.

## I2 / Ruling R33: inactive CoinGecko rows counted

`src/db/reprice.ts`: `RepriceMetric.inactiveCoingeckoRows`. planReprice reads the superseded/rejected `flow_usd.*` rows
(period_days not null, in range), classifies each with the same `classify` as active rows and counts those not skipped
by design (priced or refused = a CoinGecko-priced class). Never written, never exported. `src/cli/commands/data.ts`:
the metric line (dry run and --yes) ends `; inactive: N superseded/rejected CoinGecko-priced row(s), kept as written`;
`--json` carries the field. Tests: `tests/db/reprice.test.ts` "R33: …" (a superseded and a rejected burn scan counted
2, a rejected DefiLlama fees row not counted, both burn rows keep value 50/60 and no marker after `--yes`);
`tests/cli/reprice.cli.test.ts` dry-run line updated. Followups "Carried to later releases" + spec Status line:
"superseded/rejected rows keep their write-time value; Mike decides keep vs purge (R8 at the latest)", with PUMP's
DefiLlama-era `flow_tokens.buyback` twins named.

## M1 / M2: breach posts

`src/levels/levels.ts`: `PRICE_WATCH_MAX = 20` and `breachLines(env, job, breaches, prices)` (moved from backfill.ts;
summary `ORION WATCH <env> price <job>: N more breaches not posted (T this run); the prices rows carry check_gap_pct`).
Used by levels (`levels`), refresh (`refresh`), backfill op prices and op fetch (`backfill`; the prices backfill's
line is byte-identical to before). `PRICES_BACKFILL_WATCH_MAX = PRICE_WATCH_MAX` (still exported, test unchanged).
M1: op fetch posts `fetched.priceBreaches` after the fetch, before the done/failed line.
Tests: levelsJob 23 breaches → 20 + summary (and `result.prices.breaches` = the posts); refresh 21 → 20 + summary;
backfill op fetch 22 → start, 20 + summary, done.

RED batch (levels, backfill, refresh, reprice, reprice.cli; before the code): `11 failed | 53 passed (64)` — the 3+3
R32(c) cases, M1, M2 ×2, R33, the reprice.cli line. GREEN with load+paths: `108 passed (108)`.

## M4 / M5 / extras (docs)

- deploy.md R2 block item 5: the two staging_refresh gaps (Sunday refresh before prod's steps 6-8 → finish first, or
  pause/accept and re-run 3-8 on stage; a prod rollback keeps schema 8 → pause or expect the refresh until roll-forward).
  Rollback note "After step 8 (no CoinGecko rows" → "After step 8a".
- followups: "None blocks the release" qualified (four must-fix minors fixed by R32, marked "fixed"); Task 9 minors
  added (both fixed here); M1-M4 listed under "Final whole-branch review"; "Notes kept:" moved under Task 6b; R32/R33
  added to rulings; R25 marked superseded by R32 for its "only when present" part.
- spec Status: the R32/R33 line.
- `src/daemon/daemon.ts:103` comment: retries per job attempts (refresh's second; op prices up to
  PRICES_BACKFILL_MAX_ATTEMPTS).
- orion-remote usage text: reprice and rebuild-price-levels "exit 3 when any row is refused". Test
  `test_usage_text_names_exit_3_for_reprice_and_rebuild_price_levels`: RED `Ran 61 … FAILED (failures=1)` → GREEN.

## Verification (final tree)

- `npx vitest run --maxWorkers=2`: `Test Files 1 failed | 153 passed (154)`, `Tests 1 failed | 1968 passed (1969)`;
  the failure: tests/assets/sky.ingest.test.ts "reports both halves as cash to stakers, …" — `Test timed out in 5000ms`
  (load). Alone at `--maxWorkers=1`: `7 passed (7)`. So 1969/1969 (1951 + 18 new).
- `npm run typecheck`: clean. `npm run lint:promises`: exit 0, no findings.
- `python3 -m unittest scripts/provision/test/test_orion_remote.py`: `Ran 61 … OK` (60 + 1).
- `/usr/bin/python3 -m unittest tools/phase2-proof/test_prod_copy.py tools/phase3-proof/test_flatdiff.py`: `Ran 69 … OK`.
- `npx tsx tools/sources-register/generate.ts --check`: exit 0.
- Hash pins: none moved (no pinned fixture's prices map changed).

## Concerns

- R32(b)'s ORION_ENV check reads `process.env` inside `loadAsset` (loadAsset has no env parameter); a real stage/prod
  run always loads from a RELEASE root (resolvePaths refuses stage/prod without one), so the release-root test is the
  operative one there.
- Not addressed (not ruled): M3 (concurrent levels/backfill double-post) is listed in the followups only.
- The fixture changes are broad (helpers convert INGEST_ASSET_YAML for priced roots); they change what some
  CLI/daemon tests read for price_usd (hand-entered, or price.token in ingest.cli), not what they test.
