# Orion — Executive Summary

**As of:** latest Orion signals, 2026-10-10 00:05–00:35 UTC (2026-10-09 evening PT) · engine 1.3.0 · all 7 signals `ok`, 0 open anomalies

## 1. Valuation snapshot

| Asset | Price | Mkt cap | Revenue (ann.) | Holder flow (ann.) | MC / Rev | MC / Holder flow | Holder yield | Orion 12m target | Grade |
|---|---:|---:|---:|---:|---:|---:|---:|---:|:-:|
| **HYPE** | $84.08 | $18.70B | $605.2M | $605.2M | 30.9x | **30.9x** | 3.2% | $102.54 (+22%) | B |
| **VVV** | $22.05 | $1.07B | $100.0M¹ | $9.2M | 10.7x¹ | **115.2x** | 0.9% | $36.11 (+64%) | B |
| **AERO** | $0.8030 | $806.7M | $69.1M | $69.1M | 11.7x | **11.7x** | 8.6% | $0.4352 (-46%) | B |
| **CRV** | $0.3621 | $569.5M | $5.1M | $5.1M | 110.9x | **110.9x** | 0.9% | $0.0321 (-91%) | A |
| **cvxCRV** | $0.1447 | $61.3M | $5.2M | $5.2M | 11.7x | **11.7x** | 8.5% | $0.0675 (-53%) | A |
| **sdCRV** | $0.1952 | $23.2M | $2.5M | $2.5M | 9.4x | **9.4x** | 10.7% | $0.1177 (-40%) | A |
| **yCRV** | $0.1907 | $13.7M | $1.5M | $1.5M | 9.0x | **9.0x** | 11.1% | $0.1220 (-36%) | A |

## 2. Holder flows by type (annualized, trailing 90–91d)

| Asset | Paid to | Buyback / burn | Fee share (crvUSD / fees) | CRV rewards | Bribes / vote incentives | CVX rewards | **Total** |
|---|---|---:|---:|---:|---:|---:|---:|
| **HYPE** | all | $605.2M | — | — | — | — | **$605.2M** |
| **VVV** | all | $9.2M | — | — | — | — | **$9.2M** |
| **AERO** | veAERO | — | $69.1M | — | — | — | **$69.1M** |
| **CRV** | veCRV | — | $5.1M | — | $8.6M² | — | **$5.1M** |
| **cvxCRV** | stk-cvxCRV | — | $2.7M | $1.9M | — | $660K³ | **$5.2M** |
| **sdCRV** | staked sdCRV | — | $659K | $219K | $1.6M | — | **$2.5M** |
| **yCRV** | st-yCRV | — | $1.5M | — | — | — | **$1.5M** |

## Read-through

- **Cheapest on cash to holders:** yCRV, cvxCRV and sdCRV trade at about 9–12x holder flow, with an 8–11% yield. CRV is the most expensive at about 111x. That's because veCRV's crvUSD fee share is only $5.1M a year, against a $570M market cap.
- **HYPE** pays the most in absolute terms, with $605M a year in buybacks at about 31x. Orion's 12m target is the only one well above spot besides VVV: +22%.
- **VVV** shows +64% upside, but that rests on a revenue figure from August that was disclosed rather than measured¹. On-chain burns alone put it at about 115x.
- **AERO** sits at about 12x holder flow, yet Orion's 12m target is −46% below spot. Orion's 10x forward multiple and its discount rate (base band 17.5–24%) value the fees well below the market's ~12x.

## Notes & method

- **Revenue column.** For every asset except VVV, Orion's `revenue_run_rate_usd` *is* the holder flow, so the two columns are equal and MC/Rev = MC/Holder flow. Orion doesn't track protocol-level gross revenue, such as total Curve fees before the split. Gross P/S multiples would need a separate data source.
- **¹ VVV revenue.** $100M a year comes from a founder disclosure dated 2026-08-17, not a measurement. Anomaly #1 (`revenue_disclosure_stale`) is open as an advisory. The holder flow is the on-chain burn: VVV transfers to 0x0 from the Aerodrome pool and the buyback Safe.
- **² CRV bribes.** These are third-party vote incentives paid to veCRV voters, $8.6M a year. Orion values them as a separate component rather than holder cash flow, so they're **excluded** from CRV's total and multiple. Including them, CRV's holder flow is $13.8M a year, 41x, 2.4% yield.
- **³ cvxCRV CVX.** $0.66M a year was still received over the last 91 days. Orion's model sets CVX capture to 0 going forward because the program has stopped. Excluding it, the total is $4.6M, 13.4x.
- **Market cap** is price × circulating supply. For wrappers (yCRV, cvxCRV, sdCRV) it's price × wrapper supply, because the wrappers have no separate circulating figure.
- **Holder yield** is holder flow / market cap. For wrappers whose flows go only to stakers, the yield per *staked* token is higher.
- **Annualization:** sum of daily on-chain or DefiLlama flows over each asset's model window (90d for VVV/HYPE/AERO, 91d for the Curve family) × 365 / window. This matches Orion's own `revenue_run_rate_usd` to the dollar for all six measured assets.
- **12m target** is Orion's probability-weighted expected value (bear/base/bull 25/50/25), with upside measured against spot at signal time.
- Source: `/home/hermes/git/orion/orion.db` (signals, observations) and `assets/*.yaml` (flow definitions).
