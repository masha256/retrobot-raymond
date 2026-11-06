# Holder yield / growth / protocol revenue reporting (report-only)

Live since 2026-10-10 (main `901070a`, spec `docs/superpowers/specs/2026-10-10-orion-holder-yield-report-design.md`).

## Use
- `node dist/cli/index.js report yield [asset] [--day YYYY-MM-DD] [--json]` — computed on demand from stored daily rows; nothing extra stored.
- Buckets: burn (no haircut), hold (overhang haircut), cash (slippage haircut). Haircuts live in each asset's `reporting.haircuts`, fixed by hand from pool depth.
- Growth = (cur window / prior window)^(365/window) - 1. Prints `pending` until 2 windows of daily history exist; `n/m` only when a window is zero/negative.

## Rules (Mike)
- Report only: reporting never enters a driver, grade or signal. Flow metrics with `monitor_only: true` raise no unlisted_sender and no failure-streak anomalies.
- HYPE stays `burn` in reporting to stay in sync with the valuation.
- Revenue structure is the income statement below (revenue → paid to holders / protocol income / costs); gross pass-through (e.g. LPs' CRV) is `volume`, not revenue.
- Daily totals only, never raw logs. No new general DefiLlama deps; Llama Airforce OK for CRV. VVV/HYPE revenue = DefiLlama dailyRevenue as labelled proxy (VVV plus disclosures).

## Pitfalls
- Hyperliquid `userFillsByTime` keeps only ~12 days: `hype.fund_buys_daily` can't be backfilled; it grows forward. Move HYPE valuation off DefiLlama only after ~180 days of overlap.
- A full `data fetch <asset> --backfill-days 362` re-scans every series (VVV alone >30 min). For new report series, backfill with `--metric <key>` per new metric only (~40 min total for all 7).
- Any new `reporting` block changes every asset hash: re-pin the hashes in the ingest tests and cadence test.
- The full vitest run can time out CLI subprocess tests under load; rerun those files with `--maxWorkers=1` before calling it a failure.
- Yearn revenue: treasury vault `0x044f…` takes ~28% (20% splitter + 10% receiver), not 10%.

## Quieting unlisted senders on transfer_flow (live 2026-10-11, `a50dfea`)
- Zero-amount transfers are never reported. `from_ignore: [names]` (why-comment each), `from_ignore_clones_of: [impl]` (EIP-1167, one getCode per sender per scan), `mint_sender: erc4626_deposit` (a 0x0 mint takes the depositor of the vault's matching Deposit in the same tx; no match stays 0x0 and is reported).
- None of these count anything an unlisted sender didn't already not count, so stored values can't change; prove it with a before/after `data fetch <a> --backfill-days N --dry-run --json` on a scratch copy and diff the written flow rows.
- Ignore lists aren't in the scan key/source id, so cursors carry over; a name on both allowlist and an ignore list is refused.
- Live ignores: cvxCRV treasury ← 3 Convex fee forwarders; sdCRV gross ← sidecar clones of 0xef7c…/0x66c3…; yCRV revenue ← yvyCRV fee converter 0x988f… (it re-converts st-yCRV fees already counted in `flow_usd.yearn_styc_fee`; ignoring it avoids double counting).
- Before ignoring a sender as non-revenue, trace where its money originates: a converter of fees already earned elsewhere is not new income, but the fee it converts may be uncounted (measure it where it is earned, then ignore the converter to avoid double counting).

## Income statement (live 2026-10-11, `d8942ad`) — replaces `reporting.revenue`
- Mike's model: revenue = all the protocol takes in from the market; split into paid to holders / protocol income (kept, funds the protocol) / costs. Payout ratio + protocol margin are of revenue.
- `reporting.income.lines[]`: `{id, to: holders|protocol|cost, metric | estimate:{of, ratio}}`. `remainder_of` (VVV, HYPE proxies): protocol = total − holders − costs, no protocol lines allowed. `checks` reconcile parts to a measured total (gap reported, never booked). `outside_revenue`: reserve-funded payouts (cvxCRV's CVX program) kept out of the payout ratio.
- Mike's calls: Convex's 4.5% to CVX stakers = protocol income; keepers (Convex 0.5% caller, estimate 5% of the lock line) and StakeDAO boost delegators = costs; vote incentives are holder revenue for sdCRV (sold into sdCRV) but NOT Curve revenue (CRV keeps them in extra_cash).
- Series added for it: crv `flow_usd.curve_treasury` (FeeAllocator→Treasury 0x6508…), sdcrv `flow_usd.sd_boost_delegation` (accumulator→VeBoostDelegationMultiRewards 0xe1f9…).
- First figures (91d to 2026-10-10, ann.): CRV rev 5.71M / holders 90% / kept 0.57M; cvxCRV 5.91M / 77.6% / 1.23M (+0.65M CVX reserve payout outside revenue); yCRV 2.24M / 68.6% / 0.70M; sdCRV 3.47M / 71.4% / 0.88M; HYPE 724M / 100% / 0 (after re-fetching DefiLlama's revised holder series); VVV proxy 9.2M vs burns 9.3M (payout ~101%: proxy lags); AERO 69.5M / 100% / 0.
- A remainder_of statement is only as good as both proxies agreeing: DefiLlama can revise a holders series weeks later (nightly re-reads only the last 3 days, `REVISION_DAYS`), which shows up as fake protocol income. Check with `data fetch <a> --metric <flow> --backfill-days 100 --dry-run` (lists "revised by the source" days); a real fetch supersedes them.
- `report yield` with no `--day` picks the newest day of the holder flows only; if a revenue series lags a day, revenue prints n/a. Pass `--day` = the last day every series has (fix pending).
- Backfilling 362d of a transfer_flow takes >7 min; run it with background=true (a foreground terminal timeout kills it mid-way; rerunning resumes).

## Income statement v2 (Phase 2; spec `2026-10-28-orion-data-strategy-income-v2-design.md`, Mike's D1-D9 + P1-P4)
The v1 block above stays live (and stays the `--legacy` output) until v1 is retired one release later. v2 conventions, which every later asset and phase must follow:
- Config: one `income_statement` block beside `reporting`/`holder_flows`: `revenue` (everything users pay, partner/builder shares included) → `cost_of_revenue` → gross profit → `holders` (bucket burn/hold/cash) / `protocol` / `operating_costs` (keepers, callers, boost delegators) → `below_line` (not paid by users: third-party bribes, treasury programs). Pass-through emissions stay `volume`.
- Line ids are unique across ALL sections; a use line passing a revenue line on uses `of: <id>`, never the same `metric` (double-read refused). When names collide, the revenue line gets `_rev`.
- `not_measured: "<why, which phase fills it>"` is shown as n/m and NEVER zero-filled: any not_measured line makes its section total null and propagates (gross profit, take rate, unreconciled). A section whose lines are all not_measured is null, not 0.
- Payout ratio = holders / gross profit; when gross profit is n/m it falls back to holders / revenue with `payoutRatioBasis: 'revenue'` and a flag (keeps every v1 ratio). Keep a separate flag for a data gap vs a not_measured line.
- `holderFlow.net` = after haircuts (spec §7); `holderFlow.netOfDilution` = net − dilution at price (spec §6 "net holder flow"). Name both; they are different numbers.
- `scope: protocol_share_only` beside every revenue figure until a gross series exists, so the site never compares a protocol share with gross fees unflagged. Every DefiLlama/llama.box-fed line lands in `provenance.thirdParty` (metric-level cross_checks and derived metrics with a third-party input included).
- A disclosed revenue line carries the disclosure's growth and its cross_check, as v1 does.
- A v2 computation error must never fail the legacy report, the tick or the snapshot: `incomeStatement: null` + an error field, and the nightly prints one alert line for that asset.
- Only three assets move on the same stored data: sdCRV (bribes below the line), yCRV (splitter gross; st-yCRV fee excluded, see data-sourcing reference), LIT (Robinhood fees gross, Robinhood's 50% as cost of revenue).
- Apply the below-the-line rule by who pays, the same way on every wrapper. yCRV's splitter gross is about 75% vote incentives that Yearn's FeeBurner auctions into crvUSD, and only about 25% veCRV fees from the voter, so Mike picked the sdCRV treatment for it (plan Task 7b): two new flows split the splitter inflow by sender, revenue becomes the voter share only, and the measured YBS payout and treasury flows are apportioned between revenue and below-line by the window's sender mix, labelled derived. Holder-flow totals stay unchanged. Before classifying any wrapper's revenue, split its gross inflow by sender on chain (`transfers(to=<splitter>)` in `scripts/onchain_probe.py`).
