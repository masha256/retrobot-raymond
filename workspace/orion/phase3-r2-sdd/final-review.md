# Final whole-branch review — Orion Phase 3 R2 (4498513..1cac987, 17 commits)

Reviewer: final whole-branch seat. Read via `git show/diff` at 1cac987; ran only in a detached worktree
`.worktrees/rev-final` (removed afterwards). Passes: (1) the ledger, findings files, plan amendments, spec status,
followups note; (2) per-file diffs of src/ (flow, run, prices/*, db/prices, db/reprice, db/priceLevels, db/purge,
daemon/jobs backfill/levels/refresh/stagingRefresh, levels, config/load, adapters price/solana, report/provenance),
0008, prices.yaml, assets, pack.sh, orion-remote, deploy.md R2 block; (3) the six named risks; (4) a probe.

**Verification run (1cac987, rev-final):** `npm ci`; `tsc --noEmit` exit 0; full suite `vitest run --maxWorkers=2`
**154 files / 1951 tests passed**. Probe (temporary test, deleted): `loadAsset` of lit/cake from a root with prices.yaml
**absent, empty (0 bytes), or comment-only** all load without error, `prices.size = 0`, and give the config-only hash
(lit `5d0fd64d…` vs `7864c283…` with the real file; cake `cba784f1…` vs `e863393a…`).

## Verdict: **ready with fixes**

The price swap itself is sound: no price is read from CoinGecko anywhere, the four price-lookup implementations agree
with the view, the release block's gates stop on every refusal, 0008 is expand-only. One Important finding (the Task 10
finding, which is wider than queued) must be fixed before the tag; one Important is a Mike-visible disclosure gap.

## Strengths

- One lookup rule, implemented four times and consistent: `flow_usd_chain_v` (0008:62-70), `chainPricesAt`
  (src/db/prices.ts:166-180), `repriceAsset` (src/db/reprice.ts:328-338) and `planRebuild` (src/db/priceLevels.ts:104-111):
  newest chain/first_party row with ts ≤ H and ≥ H−6 h (inclusive both ends), tie `fetched_at DESC, source`; the
  daily mean needs 24 exact hours (0008:81-88 / solana.ts `dailyMeanChainPrice` / reprice.ts:344-357), summed in hour
  order then ÷24. The scanner sums `hourly[h] × price` skipping zero hours exactly as the view's `amt <> 0`
  (flow.ts:346-361). Reprice-vs-view equality is pinned (tests/db/reprice.test.ts:251-256, :343-345).
- CoinGecko is gone from every price path: flow.ts, tokenBackfill, solana burn, levels, coingeckoHourly deleted; the
  only CoinGecko reads left are `/coins/markets` for `circulating_supply` (9 assets, all `field: circulating_supply`)
  via sources/coingecko.ts and levels.ts:94-107; `field: price|market_cap` refused by name (sources.ts:165-182).
- Release mechanics: `rebuild-price-levels` and `reprice` exit 3 on any refused row (data.ts:307, :328; `setExitCode`
  is wired in cli/index.ts:21; orion-remote `passthrough` returns the child's code); every prod `--yes` behind its own
  "Stop here. Prod: only on Mike's go" line; dry-run vs `--yes` count comparisons for every destructive step; purge
  exports fsynced before delete; reprice per-day transactions guarded by the old value (reprice.ts:179-185).
- Backfill job: frozen `to`, 550-day cap at enqueue only, 10-min budget, merged progress, capped WATCH lines
  (backfill.ts:288-292), namespaced `job:prices` lock shared with purge-prices.
- 0008 test runs orion-2026.11.12.1's statements verbatim on schema 8 (tests/db/pg/migrate.test.ts).
- Secrets: `git grep -nE 'alch_[A-Za-z0-9]{8,}|/v2/[A-Za-z0-9_-]{20,}|api-key='` at 1cac987: no hit. The only keyed
  URLs in the diff are test fixtures (`/v2/sol_SECRETKEY`); Solana errors scrub the URL to its origin (transport/solana.ts:21-46).

## Issues

### Critical
None.

### Important

**I1. A config root without a usable prices.yaml is silently accepted, and the queued fix does not cover it all**
(Task 10 FINDING; also Task 1 / 6a / 6b deferred minors).
- `src/prices/config.ts:229` — missing file → `new Map()`; an empty or comment-only file also parses to an empty map
  (probe above). `src/config/load.ts:48` gates every price rule on `prices.size > 0`, and `:63` falls back to the
  config-only hash when `entriesFor` is empty. Effects: (a) every asset hash moves to config-only, so reconcile records a
  config change on all 13 assets (src/registry/reconcile.ts:78); (b) price-source labels/rungs are wrong (LIT
  `contract_state`); (c) the CoinGecko price refusal (R24/R25) and the price-ref check (`adapters/price.ts:47`) are off,
  so `field: price` would load; (d) **the hourly `levels` job goes silent**: `recentPriceHours` returns null for an
  empty map (src/levels/levels.ts:50) so no write, no `ORION ALERT … levels prices` (src/daemon/jobs/levels.ts:69-116
  only alerts on a throw); (e) a prices backfill with no `--refs` takes `refs = []` (src/daemon/jobs/backfill.ts:332)
  and posts a "done" line with nothing written. The nightly does fail loudly (`unknown_price_ref`), so (d)/(e) are the
  silent paths.
- The queued fix ("refuse an asset naming price.token/price.token_check or a usd transfer_flow when the root has no
  prices.yaml") misses: the empty/comment-only file; **AERO** (no price.* source, no usd transfer_flow, but its hash
  includes its own `token` entry since Task 6 finding E — it would still hash config-only); the levels job and the
  prices backfill, which call `loadPrices` directly, not `loadAsset`.
- Fix: make prices.yaml *required* where Orion runs from a config root: `loadPrices(root)` throws
  `invalid_price_config` when the file is missing or has zero entries (tests that want none opt out explicitly, e.g.
  `loadPrices(root, { optional: true })` or a hand-built `LoadedAsset`). Then load.ts:48's `prices.size > 0` gate and
  price.ts:47's become unconditional (R25's "only when prices.yaml is present" goes away), levels' existing catch
  (levels job :70-75) turns it into the ALERT, and the backfill fails with an ALERT. Add the Task 1 minor's test that
  the release root, not `ORION_HOME`, supplies prices.yaml (src/cli/paths.ts:83). `prod_copy.py` copies prices.yaml.

**I2. Superseded / rejected flow rows keep their CoinGecko-priced `value`, uncounted and not disclosed** (named risk 1).
- `src/db/reprice.ts:134,215-218`: reprice reads `ACTIVE` rows only. Every flow day rewritten before R2 (re-scans,
  R1 backfills, R20 single-member writes) left a superseded row with a CoinGecko-priced `value`; rejected rows likewise.
  Nothing reads them in a report, but D3 says "no CoinGecko-derived USD is kept", the remap (:206-210) already touches
  them for `coingecko:*` refs, and neither the dry run, Task 10 nor the followups note counts or names them.
- Fix (cheap, no data change): add a `history` count per metric to the reprice result (superseded/rejected `flow_usd.*`
  rows of the asset, `period_days = 1`, not carrying the marker), show it in Task 10's table, and add one line to the
  followups "Carried to later releases" / spec Status so Mike decides: keep as audit history (state it) or purge later.
  Same line should name PUMP's DefiLlama-era `flow_tokens.buyback` twins (already in followups, not in the spec Status).

### Minor

- **M1. Daemon op-`fetch` backfill drops the price breaches of its own writes.** `src/daemon/jobs/backfill.ts`
  `makeBackfillHandler` op-fetch path never reads `fetched.priceBreaches` (only refresh.ts:151 does). A `job run-now
  backfill … --backfill-days 400` that writes missing hours inline posts nothing (rows still carry `check_gap_pct`).
  Same class as the deferred CLI fetch/tick minor. Fix with breachLines (capped) when touched next.
- **M2. WATCH posts are capped only in the prices backfill.** levels (src/daemon/jobs/levels.ts:116) and refresh
  (refresh.ts:151-163) post every breach. Bounded today (48 h window, one post per breach run), so defer; reuse
  `breachLines` for consistency.
- **M3. Concurrent writers double-post.** The hourly levels writer does not take `job:prices`; during step 3 it and the
  backfill can write and report the same recent hour's breach. Harmless (upserts); note in deploy step 3.
- **M4. Staging refresh after prod reaches schema 8.** deploy.md:689-691 covers stage-ahead (refused, correct: ids +
  checksums, stagingRefresh.ts:239). Not covered: (a) a Sunday refresh after prod's deploy but before prod's steps 6-8
  mirrors prod's un-repriced flows and CoinGecko rows onto stage (no CoinGecko read follows, but stage's soak baseline
  is gone); (b) a prod rollback to orion-2026.11.12.1 keeps schema 8, so a refresh no longer refuses and copies the
  CoinGecko rows the old release writes. One sentence in the R2 block: finish prod's block before a Sunday, and after a
  prod rollback, skip/expect the refresh.
- **M5. Followups note omits the two Task 9 deferred minors** (ledger :191-192, daemon.ts:103 comment; orion-remote
  usage lacks exit 3) and says "None blocks the release", which is wrong for the three prices.yaml minors (I1).

## Named risks

1. **No CoinGecko price survives a correct block run.** Code: `git grep -i coingecko src` at 1cac987 — price reads:
   none. Remaining: sources/coingecko.ts + levels.ts:94-107 (`/coins/markets`, `circulating_supply` only, 9 assets),
   provenance/sourceTypes labels, tokens.coingecko_id (metadata, R8), purge/reprice/remap code. Stored classes R2 leaves:
   PUMP ~369 DefiLlama-era `flow_usd.buyback` (DefiLlama $, skipped `defillama_history`) and their CoinGecko-derived
   `flow_tokens.buyback` twins → deferred to R6, visible in followups + deploy step 6 ✅; `usd_native`/`third_party`/
   `disclosed`/`periodic` skips — not CoinGecko-priced ✅; superseded/rejected flow rows → **I2** ❌ (not visible);
   exports `~/home/repriced`, `~/home/purged` and pg_dumps — by design, listed ✅; published `snapshots_out`, anomalies,
   check_results history — see Declined. Base-tree check: the only CoinGecko price consumers at 4498513 were flow.ts,
   tokenBackfill.ts, solana.ts, coingeckoHourly.ts, levels.ts and the `coingecko` source with `field: price` — all
   replaced; cake/crv/vvv/hype/lit adapters never priced from CoinGecko.
2. **Value equality.** ✅ (see Strengths). Writer value = view (same hour-order sum); reprice = view (tested to 1e-9);
   report reads the view's `usd` when basis ≠ legacy (src/db/prices.ts:240-249), so a last-ulp difference cannot reach
   a report. Gap: no committed scanner-value == view test (6a minor; Task 10 covers on prod data — defer).
3. **Silence means broken.** reprice / rebuild exit 3; purge-prices / purge refuse non-zero; backfill-prices fails or
   defers-with-chain-error with an ALERT, done posts missing-by-reason; levels alerts on writer errors; refresh posts
   breaches. Breaks: empty/missing prices.yaml → levels and backfill silent (**I1**); op-fetch backfill breaches (M1);
   caps only in backfill (M2). Anomalies: only the pre-existing `price.token_check` cross-checks on CAKE, LINK, LIT,
   PUMP, UNI, VVV (+ `type: price` checks on CAKE/LINK/UNI, pre-existing ids) — matches R22 ✅. LIT zero liquidity is
   `NoReading` (no anomaly) ✅.
4. **Deploy / rollback.** 0008 expand-only, old statements tested on schema 8; `ahead` is not refused by the R1 code
   ✅. Block order backfill → mid → coverage → reprice → rebuild → purge-prices → market_data purge → after → gate ✅;
   prod `--yes` only after "Stop here. Prod: only on Mike's go" ✅. Drain: a run holds ≤ 10 min + one chain-day under a
   30-min drain ✅ (the nightly's inline writer has no abort — deferred 6a minor, commits per chain-day so safe).
   Staging refresh: refuses while migrations differ ✅; gaps M4.
5. **Config integrity.** One hash producer (load.ts:63), used by reconcile, data.ts, proposals approve (with
   `loadPrices(configRoot)`), agent filing (`ctx.loaded.prices`) ✅; pack.sh ships and requires prices.yaml, tested
   ✅; configRoot = release root when shipped (paths.ts:83) ✅ but untested; missing/bad prices.yaml refuses loudly ❌
   (**I1**: missing, empty or comment-only accepted; malformed YAML/schema errors do refuse).
6. **Secrets.** ✅ none.

## Deferred-minor triage (53 ledger lines)

| # | Task | Minor | Call | Why |
|---|---|---|---|---|
| 1 | T1 | check method not validated against a chain | defer | config is reviewed; a wrong pairing fails at the first write |
| 2 | T1 | chain `lighter` accepts any EVM ref | defer | one ref uses it; reviewed config |
| 3 | T1 | valid_from pattern only (2025-13-45) | defer | Date.parse NaN would surface at first write; cheap later |
| 4 | T1 | Solana mint in ref key not checked for 32 bytes | defer | address fields are checked (base58 32); key mismatch fails reads |
| 5 | T1 | missing prices.yaml → config-only hashes silently | **must fix** | = I1 |
| 6 | T1 | check schema built with a type cast | defer | typing only |
| 7 | T1 | no test that release root supplies prices.yaml | **must fix (with I1)** | guards I1's path; one test |
| 8 | T2 | usd_feed age not recorded | defer | provenance depth; values correct |
| 9 | T2 | failed calls cached with good ones | defer | costs one hour, re-read next run |
| 10 | T2 | v4 currency order not checked (LIT check) | defer | check only; verified by Task 10 gaps |
| 11 | T2 | BlockReadCache key omits signature | defer | key has address+fn+args+pick; collision needs an overload with equal args |
| 12 | T2 | cache test counts multicalls only | defer | test depth |
| 13 | T2 | no tests for pool token mismatch / unknown or zero feed / zero reserves | defer | add with next price change |
| 14 | T2 | v3 mean tick float, not floored | defer | ≤ 0.01 % |
| 15 | T3 | backfill filling a joining hour can report a second breach | defer | WATCH noise only |
| 16 | T3 | rpc.ts:108 comment block number | defer | comment |
| 17 | T3 | failed chain leaves no missing entry for later hours | defer | the chain error fails/alerts the job |
| 18 | T3 | block-search fallback discards its bracket | defer | cost only |
| 19 | T3 | writeChainPrices ~230 lines | defer | style |
| 20 | T3 | aborted chain-day does not save hour blocks | defer | re-searched; cost only |
| 21 | T3 | older breaching hour written in front of a reported run reports again | defer | WATCH noise |
| 22 | T3 | abort leaves earlier chains of the day committed, no missing for skipped hours | defer | resumable by design |
| 23 | T4 | slot search ~15 req per PUMP hour | defer (closed) | Task 10 measured solana 277/day (~11.5/h) |
| 24 | T4 | failed LbPair read not cached | defer | one extra request |
| 25 | T5 | daily_mean count does not check hour alignment | defer | upsertPrices refuses unaligned ts (db/prices.ts:82) |
| 26 | T5 | `sumHourly` name covers daily_mean/usd_native | defer | naming |
| 27 | T5 | compare-usd --json field change | defer | no consumers |
| 28 | T5 | hours_priced/needed n/24 without hourly buckets | defer | use usd_basis; documented |
| 29 | T6a | ref check at load only when prices non-empty | **must fix (with I1)** | same root cause |
| 30 | T6a | flow scan writer call has no budget/abort | defer | commits per chain-day; backfill-prices runs first |
| 31 | T6a | view accepts unaligned prices | defer | none can be stored |
| 32 | T6a | no committed test stored value == view usd | defer (recommend) | report reads the view; Task 10 compares on prod data |
| 33 | T6a | levels tests written after code | defer | process |
| 34 | T6b | consecutive:2 not at fetch time | defer | moot (R22) |
| 35 | T6b | no prices.yaml labels LIT contract_state | **must fix (with I1)** | same root cause |
| 36 | T6b | VVV price_usd/diem share a source id | defer | failure-streak merge only |
| 37 | T6b | price.ts:104/111 comment | defer | comment |
| 38 | T6b | block cache shared across chains keyed by block | defer | key includes address; cross-chain same address+block+call is negligible |
| 39 | T6b | off-chain observedAt = run start | defer | seconds |
| 40 | T6b | LIT v4 check at head, not run block | defer | check only |
| 41 | T6 | FetchResult.priceBreaches not printed by CLI | defer | CLI only; rows keep the gap |
| 42 | T6 | refresh result empty `undelivered: []` | defer | cosmetic |
| 43 | T6 | no breaches on dry run only via writer | defer | holds today |
| 44 | T6 | CLI fetch/tick breaches never posted | defer | CLI only; see M1 for the daemon twin |
| 45 | T7 | permanently missing hours re-read every run | defer | cost only |
| 46 | T7 | http_json at a CoinGecko price URL loads | defer (R8) | proposals are human-approved; disclosed in followups |
| 47 | T7 | lease-gone progress-save untested | defer | logged path |
| 48 | T7 | failing chain posts an ALERT every 10 min until fail | defer | loud not silent; prerequisite 3 checks the URLs |
| 49 | T8 | log_scan row with hourly but amount null refused | defer | none known; refusal is loud (exit 3) |
| 50 | T8 | CLI tests after code | defer | process |
| 51 | T8 | unknown future first_party:<x> → contract_state rung | defer | only two venues exist |
| 52 | T9 | daemon.ts:103 comment stale | defer | comment (add to followups, M5) |
| 53 | T9 | orion-remote usage lacks exit 3 | defer | deploy.md states it (add to followups, M5) |

Must fix before release: #5, #7, #29, #35 (one change, I1). Everything else defers.

## Rulings

Agree with R1-R31 except:
- **R25 (partial disagreement):** keying the CoinGecko-price refusal on "prices.yaml is present" reuses the signal I1
  shows is unreliable. With I1's fix (prices.yaml required in a config root) the refusal should be unconditional in
  `loadAsset`; fixtures without a prices file keep working through `parseAssetObject` without a map.
- **R26 (scope OK, wording):** "skipped by design, never refused" is right, but the ruling's "Cost if wrong" assumes all
  CoinGecko-derived rows are classified; superseded/rejected ones are not classified at all (I2).
- **R14 (agree, caveat):** restoring `hour_blocks` is fine; see M4 for the whole-dump timing caveat.

## Recommendations

- Land I1 + I2 (+ M5) as the final fix wave together with the queued Task 10 item; I1's test matrix: missing, empty,
  comment-only prices.yaml × loadAsset, levels job (expect ALERT), prices backfill (expect failed + ALERT), AERO hash.
- Task 10 table: add the I2 history count per asset.

## Declined to judge

- Published `snapshots_out`, anomalies, check_results and journal history containing CoinGecko-era figures: historical
  outputs, not re-published by R2; outside the plan (R2 re-prices stored inputs). Mike may want a line on it.
- Writer internals per method (decoders, block search, Meteora/PumpSwap math): reviewed per task with live
  checks; not re-derived here.
- Task 10 numbers (call counts, gaps, allowlist bounds): not yet signed; not reviewed.
- `tools/phase2-proof/compare.py` / R1 allowlist vs the new `priceBasis.flows` text: carried to Task 10.
- HYPE same-venue check and sdCRV's band: Mike's open decisions, recorded in followups.
