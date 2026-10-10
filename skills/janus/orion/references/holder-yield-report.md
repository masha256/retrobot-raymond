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
