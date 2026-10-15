# Orion definitions agreed with Mike (2026-10-12)

## Supply / valuation
- total_supply = on-chain supply minus what CoinGecko also excludes (burn addresses; HYPE also the Assistance Fund). Formerly `effective_supply` (renamed, commit ab3af25).
- circulating_supply = CoinGecko circulating; if CoinGecko has none (cvxCRV, sdCRV, yCRV) use on-chain total. Do NOT use CoinGecko total for sdCRV/yCRV: frozen 2022 snapshots (CMC/CoinPaprika copy them; GeckoTerminal/DexScreener are current).
- market_cap = price x circulating; fdv = price x total_supply. P/E and holder-flow ratio use market cap.
- Valuation targets still divide by total_supply; Mike will rework targets later.

## Revenue (commit 4ed14b2)
- Revenue = config list of streams per asset (daily | periodic | disclosed). No one-off series per new revenue type.
- HYPE = DefiLlama trading revenue + AQAv2 USDC reserve yield (read rate/balance from Hyperliquid daily; paid every 30d to Assistance Fund, 8d after interval). Growth also shown ex-new streams (<180d).
- UNI = protocol fees (v2 + selected v3) = UNI burned to 0xdead (verified: all buybacks end at 0xdead). v4 fee switch off = upside, not revenue.
- VVV = founder-disclosed run rate ($70M 2026-07-01, $100M 2026-08-17); on-chain burns are holder flow only (~$9.4M/yr: ~monthly buyback_safe burns + per-subscription pool burns).
- Growth = latest 90d vs prior 90d (91 for Curve family/UNI), compounded; PEG n/m on ramps.

## coinrevs tables (column spec)
- Revenue: protocol, market cap, annualized revenue, annualized revenue growth, P/E (mcap/revenue), PEG.
- Holder flow: protocol, market cap, annualized buybacks, annualized slippage-adjusted direct payments, annualized holder flow (sum), holder flow ratio.
- Source: `node dist/cli/index.js report yield --json` on prod. Output: ~/.hermes/profiles/raymond/workspace/orion/coinrevs-tables-*.md. Dev queue: workspace/orion/dev-queue-revenue.md.

## Pitfalls
- AERO 2026-09-10 DefiLlama artifact ($7.92M day) has a manual correction row; `data fetch --backfill-days` skips AERO while it overlaps, and `--adopt` rejects it — re-apply with `data set aero flow_usd.fees 261631 --at 2026-09-10T00:00:00.000Z --period-days 1`. Don't mistake that spike for a DefiLlama revision.
- Backfilling older history exposes months to monthly cross-checks for the first time (VVV April mismatch -> anomaly #2, acked). Back up orion.db before prod backfills; run assets sequentially.
