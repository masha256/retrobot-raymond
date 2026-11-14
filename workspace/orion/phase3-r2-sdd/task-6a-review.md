# Task 6a review (7ff7562..7063c22)

### Spec Compliance

- ✅ Spec compliant for the R18/R19 6a scope. Every listed item has its hunk: flow.ts chain prices (src/ingest/flow.ts:419-445,
  :340-357), tokenBackfill price part deleted (src/ingest/tokenBackfill.ts, `backfillPrices`/`BackfillPrices`/`result.prices`
  gone; CLI line src/cli/commands/data.ts:56 removed), PUMP burn daily mean (src/ingest/adapters/solana.ts:83-97, :126, :179),
  levels write + alert (src/levels/levels.ts:47-61, :218-228; src/daemon/jobs/levels.ts:66-111), sharedHttpCache removed
  (src/daemon/daemon.ts, src/ingest/run.ts, src/ingest/transport/http.ts, refresh.ts:120), src/prices/coingeckoHourly.ts
  deleted, price_coingecko_id removed from the strict schema (src/config/sources.ts:71-77) with 34 YAML lines dropped
  (`git diff … -- assets | grep -c '^-.*price_coingecko_id'` = 34), yCRV `share_price.underlying` (assets/ycrv.yaml:100,122,138).
- ⚠️ Cannot verify from diff: (a) PUMP burn prices only from rows already stored (solana.ts:126 reads `chainHourPrices`;
  the nightly does not ensure PUMP hours). Whether a burn day ever gets its 24 hours depends on the hourly levels job
  having written them with no gap; levels never refills a gap behind its newest row (levels.ts:56-58). Controller: confirm
  that Task 7's backfill-prices is the planned gap filler. (b) Breach "once per run" end-to-end is pinned only by Task 3's
  writer tests; levels tests use a fake breach list (report concern 4, accurate).

### Named risks — what I checked

1. **Value equality.** Read `chainPricesAt`/`chainHourPrices` (src/db/prices.ts:141-178) against flow_usd_chain_v
   (0008_chain_prices.sql:58-77): same source filter, same `ts <= H AND ts >= H - 6h` window (loop t = h .. h-6h inclusive,
   prices.ts:169), same tie order ts DESC, fetched_at DESC, source ASC; zero-amount hours skipped on both sides
   (flow.ts:350, view `b.amt <> 0`); same token_ref (row stores `tokenOf.tokenRef`, flow.ts:488, = `refOf`) and same hour
   starts (observedAt = dayEnd, view `observed_at - 24h + (i-1)h`). **Probe run** in the detached worktree (temp test, deleted):
   scanned the mini world with irrational per-hour prices, and with prices only every 4th hour (lookback exercised); for every
   written flow_usd row `observations.value === flow_usd_chain_v.usd` bit-for-bit and `usd_basis = 'hourly'` (3/3 pass). Same
   probe: dry-run `written` values equal the real run's. Only divergence: the view also accepts non-hour-aligned chain rows,
   `chainPricesAt` keys by exact hour (Minor 4). No golden file changed in the diff (`git diff --stat` shows no
   tests/report/golden or tests/agent/golden path); asset tests re-seed the same flat prices (e.g. tests/assets/*.ingest.test.ts).
2. **No CoinGecko price read.** `git grep -i -E "market_chart|priceAt\b|coingeckoHourly|price_coingecko_id|priceCoingeckoId|sharedHttpCache" 7063c22 -- src tools assets docs/templates`
   → only a schema comment (sources.ts:74). `loadPrices(` hits are prices.yaml loaders (proposals.ts:185, load.ts:87,
   jobs/levels.ts:69). Remaining coingecko in src: the `coingecko` level source type, `/coins/markets` in levels.ts:86-107,
   whose ids come only from `source.type === 'coingecko'` requests (levels.ts:89). Pass.
3. **Missing vs wrong.** A non-zero hour with no price throws before any write (flow.ts:353; test flow.test.ts "withholds
   the day…" asserts no observation and cursor null). PUMP: `dailyMeanChainPrice` stops at the first unpriced hour and sets
   no mean unless n = 24 (solana.ts:88-95); the day gets no USD point, all-unpriced fails the read (solana.ts:179).
   Dry run: writer `dryRun` skips both `prices` and `hour_blocks` (writer.ts:415-417) and breach bookkeeping (:432); flow test
   asserts `SELECT * FROM prices` empty. Pass.
4. **Retired key.** Refused by zod strictness at load (tests/config/sources.test.ts "refuses the retired price_coingecko_id
   by name"), at filing (tests/agent/tools.test.ts:337) and at approve with YAML untouched and proposal pending
   (tests/app/proposals.test.ts:259). `share_price.underlying` required on a usd share (sources.ts:181). Load-time ref check
   (load.ts:46-53) + test loading every repo asset against the repo prices.yaml (tests/config/load.test.ts:276-290). Pass.
5. **jobs/levels.ts rebuild.** File is unchanged b50e94b..7ff7562 (`git log 4498513..7063c22 -- src/daemon/jobs/levels.ts`
   = only 7063c22). The 7ff7562..7063c22 diff is purely additive (+26/-4; the 4 are import, doc, `runLevels` call, result
   literal). Dead-man ping (:126-128), snapshot_push enqueue (:123), watch fire/clear (:82-100), abort checks, allFailed
   path, per-asset `failed` sort all byte-identical to 7ff7562. Pass.

Focused run (detached worktree at 7063c22, `--maxWorkers=1`): 15 files (flow, flow.sharePrice, levels, levelsJob, sources,
tools, proposals, load, db/prices, adapters.solana, writer, coingeckoPlan, ycrv, pump, refresh) 257/257 passed, no warnings.

### Strengths

- Hour-bucket valuation mirrors the view exactly, including the 6 h lookback and R6 tie order; verified bit-equal.
- R19 dry run done properly: in-memory rows ranked with stored ones under a chain source so the dry run predicts the real
  value (flow.ts:439-441), and the writer's dry path touches neither table.
- Missing-price error keeps the old message shape, naming ref and hour; cursor stays.
- Retirement: three-place tests plus a load-time "every usd ref is priced" guard, with a negative case naming metric and ref.
- Clean removal of the shared market_chart cache across daemon/refresh/run/http with no stragglers.
- Report is candid (levels tests written after code, the `cp` clobber, first-backfill cost).

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)

1. **src/ingest/flow.ts:437-438 (and src/daemon/jobs/refresh.ts:120) — breaches from a flow scan's price write are
   dropped.** The scan uses only `w.errors`; `w.breaches` is discarded and the refresh job posts nothing. The writer reports
   a breach only when the run contains a newly written hour (Task 3), so when the nightly scan is the job that writes those
   hours (levels down or behind, first scan of a range, any hour levels missed), the next levels run finds them stored and
   never reports the breach. The alert is lost with no trace. Plan P5 says the breach "is posted by the job that wrote it".
   Fix: add the breaches to the scan outcome (or `FlowScanResult`) and have the refresh handler post them with
   `formatPriceBreach`, counted in undelivered like the other posts. At minimum, write them to `outcome.notes`. Test: a scan
   whose fake writer returns a breach ends with it posted or recorded.

#### Minor (Nice to Have)

1. src/daemon/jobs/levels.ts:66-72, :102-111, :126 — a price write failure (prices.yaml unparsable, `no_rpc_url`, writer
   throw) is only in the job result. It posts nothing and does not withhold the dead-man ping, so the levels job can stop
   writing prices and stay silent. Flows would later fail at the nightly, but PUMP burn days just go unpriced (detail line).
   Consider one alert after N consecutive failing hours.
2. src/ingest/flow.ts:437 — the writer gets no budget or signal, and `stoppedBySignal`/`stoppedByBudget` are ignored. A
   partial write then shows up as the misleading "no <ref> price point" error. Already carried to Task 9 for cost; a note
   would make the cause visible.
3. src/levels/levels.ts:52-58 — `fromHourMs` is the minimum over refs. One ref that can never be written (an off-chain
   venue down, a ref whose valid_from is ahead) keeps every hourly run at the 48 h floor. Stored hours are skipped without
   reads, so the cost is that ref's 48 hours re-attempted each hour. Fine, but it is worth a line in the doc comment.
4. src/db/prices.ts:164-178 — `chainPricesAt` only sees hour-aligned rows, while the view takes any `ts` in [H-6h, H]. The
   writer and the fake both store aligned rows only, so nothing diverges today. Assert alignment, or note it beside Task 5's
   deferred minor of the same kind.
5. Tests: no committed test pins `observations.value = flow_usd_chain_v.usd` for a scanned row (my probe did). Add one, since
   the report and the stored derived rates depend on it.
6. assets/pump.yaml:73-74 — the reworded comment leaves a broken short line ("Before / the first on-chain reading: DefiLlama's
   daily holders"). Reflow it.
7. Process: the levels/levelsJob tests were written after the code, with RED shown by swapping in HEAD's files. That is
   acceptable evidence, but it is not test-first.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The core swap is correct: stored flow values equal the chain view bit-for-bit, no CoinGecko price read
remains, missing prices withhold, and the dry run writes nothing. The one Important is that price-check breaches found by a
flow scan's inline price write are silently discarded, contrary to P5. The fix is small.
