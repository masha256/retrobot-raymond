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

## 1b. Growth & PEG

Holder flow over the latest 90-day window (91 days for the Curve family) against the 90 days before it. Windows run 2026-04-12..07-12 → 2026-07-12..10-10.

| Asset | Holder flow, prior 90d | Holder flow, latest 90d | 90d/90d | **Annualized growth** | **PEG** (MC/HF ÷ ann. growth) | Orion base-case Y1 growth | PEG on Orion Y1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **HYPE** | $146.8M⁵ | $178.5M⁵ | +21.6% | **+121%** | **0.26** | +60% | 0.52 |
| **VVV** | $0.82M | $2.29M | +181% | **n/m⁴** | n/m⁴ | +110% | 1.05 (on burn) · 0.10 (on rev.) |
| **AERO** | $16.1M | $17.2M | +6.6% | **+30%** | **0.39** | +30% | 0.39 |
| **CRV** | $1.56M | $1.28M | −17.9% | **−55%** | n/m (shrinking) | +10% | 11.1 |
| **cvxCRV** | $1.49M | $1.30M | −13.0% | **−43%** | n/m (shrinking) | −11% | n/m |
| **sdCRV** | $0.79M | $0.61M | −21.8% | **−63%** | n/m (shrinking) | −11% | n/m |
| **yCRV** | $0.48M | $0.38M | −21.3% | **−62%** | n/m (shrinking) | −11% | n/m |

**Stream detail:**
- **cvxCRV:** crvUSD fees −17%, CRV +16%, CVX −43% (program stopped).
- **sdCRV:** crvUSD −18%, CRV −1%, bribes −26%.
- **VVV:** programmatic pool burns $0.24M → $1.19M (+402%); discretionary Safe buybacks $0.58M → $1.10M (+91%), one per month, rising from $119K in April to $411K in October.

**How to read it**
- **The 90d/90d figures:** I re-measured both windows today for all 11 streams, from the same sources Orion reads (DefiLlama for HYPE and AERO, on-chain Transfer logs for the rest, priced daily). For the latest window, the 9 on-chain streams match Orion's stored data to within about 1%.
- **Annualized growth** compounds the 90d/90d change over a year: (1 + g)^(365/90) − 1. That turns a single quarter into four, so a −18% quarter becomes −55% and +22% becomes +121%. It's a run rate, not a forecast.
- **PEG** = MC / Holder flow ÷ annualized growth in % points. Below 1 means you pay less than 1x of multiple per point of growth. It means nothing when growth is negative.
- **PEG on Orion Y1** uses Orion's own base-case first-year growth assumption (`rev_growth_y1`) instead of trailing growth. It's steadier, and it's what the 12m targets are built on.

**Read-through:**
- **HYPE** is the cheapest on growth: 0.26 on trailing growth, 0.52 on Orion's more conservative +60%.
- **AERO** is also cheap on growth at 0.39, and Orion's +30% assumption matches the trailing rate exactly.
- **The Curve family's holder flow is shrinking 13–22% a quarter.**
  - Orion's −11% Y1 assumption for the wrappers is far gentler than the trailing −43% to −63%.
  - CRV's +10% assumption runs against a −18% quarter.
  - The 9–12x multiples on the wrappers look cheap only if the decline stops.

**⁴ VVV:** the prior window contains the very start of the measured series. Programmatic pool burns were still ramping up, so +181% (+6,500% annualized) reflects that ramp, not a growth rate. On a steadier measure, monthly Safe buybacks grew about 3.5x in 6 months. Treat VVV's growth as "very high, not yet measurable" rather than a PEG input.

**⁵ HYPE data gap:** DefiLlama has since revised HYPE's daily history upward. Today's re-measure puts the latest 90d at $178.5M, a $724M annual run rate. Orion's stored figure for the same window is $149.2M ($605M a year), 16% lower, with nearly every day since August below the revised value. Orion didn't pick up the revisions, and its day labels also run one day later than DefiLlama's. On the revised series, HYPE trades at 25.8x and its PEG is 0.21. Both 90d windows above use the revised series, so the growth rate is like-for-like. AERO's DefiLlama history was also revised; I applied Orion's own fix for the 2026-09-09 artifact day, and the result matches Orion to 0.7%. This is worth a ticket: the DefiLlama ingest should re-fetch the trailing window so later revisions get picked up.

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
