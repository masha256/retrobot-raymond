# Holder yield / growth / protocol revenue reporting (report-only)

Live since 2026-10-10 (main `901070a`, spec `docs/superpowers/specs/2026-10-10-orion-holder-yield-report-design.md`).

## Use
- `node dist/cli/index.js report yield [asset] [--day YYYY-MM-DD] [--json]` — computed on demand from stored daily rows; nothing extra stored.
- Buckets: burn (no haircut), hold (overhang haircut), cash (slippage haircut). Haircuts live in each asset's `reporting.haircuts`, fixed by hand from pool depth.
- Growth = (cur window / prior window)^(365/window) - 1. Prints `pending` until 2 windows of daily history exist; `n/m` only when a window is zero/negative.

## Rules (Mike)
- Report only: reporting never enters a driver, grade or signal. Flow metrics with `monitor_only: true` raise no unlisted_sender and no failure-streak anomalies.
- HYPE stays `burn` in reporting to stay in sync with the valuation.
- Protocol revenue = protocol's kept cut; gross pass-through logged as `volume`.
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
- Wrapper "protocol revenue" is the operator's kept cut (Yearn/StakeDAO/Convex), not holder cash; for cvxCRV, Convex's 10% lockIncentive does go to cvxCRV stakers, so it overlaps holder cash.

## Income statement (live 2026-10-11, `d8942ad`) — replaces `reporting.revenue`
- Mike's model: revenue = all the protocol takes in from the market; split into paid to holders / protocol income (kept, funds the protocol) / costs. Payout ratio + protocol margin are of revenue.
- `reporting.income.lines[]`: `{id, to: holders|protocol|cost, metric | estimate:{of, ratio}}`. `remainder_of` (VVV, HYPE proxies): protocol = total − holders − costs, no protocol lines allowed. `checks` reconcile parts to a measured total (gap reported, never booked). `outside_revenue`: reserve-funded payouts (cvxCRV's CVX program) kept out of the payout ratio.
- Mike's calls: Convex's 4.5% to CVX stakers = protocol income; keepers (Convex 0.5% caller, estimate 5% of the lock line) and StakeDAO boost delegators = costs; vote incentives are holder revenue for sdCRV (sold into sdCRV) but NOT Curve revenue (CRV keeps them in extra_cash).
- Series added for it: crv `flow_usd.curve_treasury` (FeeAllocator→Treasury 0x6508…), sdcrv `flow_usd.sd_boost_delegation` (accumulator→VeBoostDelegationMultiRewards 0xe1f9…).
- First figures (91d to 2026-10-10, ann.): CRV rev 5.71M / holders 90% / kept 0.57M; cvxCRV 5.91M / 77.6% / 1.23M (+0.65M CVX reserve payout outside revenue); yCRV 2.24M / 68.6% / 0.70M; sdCRV 3.47M / 71.4% / 0.88M; HYPE 724M / 84% / 114M; VVV proxy 9.2M vs burns 9.3M (payout ~101%: proxy lags); AERO 69.5M / 100% / 0.
- Backfilling 362d of a transfer_flow takes >7 min; run it with background=true (a foreground terminal timeout kills it mid-way; rerunning resumes).
