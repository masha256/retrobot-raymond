# Orion dev queue — revenue definitions (hold until HYPE, UNI, VVV reviews are done)

## HYPE — USDC reserve yield missing from revenue (reviewed 2026-10-12)
- Trading revenue OK: DefiLlama dailyRevenue 90d ann. $727M (perps $706M, spot $20M, outcomes $0.3M) = 99% of fees net of builder/HIP-3 deployer/maker rebates/HLP 1%. Artemis LTM $918M (−27% YoY), consistent. HyperEVM gas (~$7M/yr) and priority fees: rounding.
- MISSING: AQAv2 USDC reserve yield (~90% of yield on USDC backing HyperCore), started 2026-08-26, funds Assistance Fund buybacks.
  - First payment 2026-10-03: $14.58M covering 2026-08-26..09-24 (30d) → ~$0.486M/day, ~$177M/yr (BlockBeats est. $193M).
  - Token Terminal counts it ("USDC Reserve Income"). DefiLlama's adapter adds `dailyAqav2Yield` but data shows it as zero (rev/fee flat 0.80–0.87 through 08-26 and 10-03).
  - Effect: revenue ≈ $904M/yr, P/E ≈ 21x (from 26.2x); holder flow rises the same.
  - Mechanics (Hyperliquid docs, "Aligned quote assets", AQAv2): accrues DAILY = USDC balance at 0 UTC × AQA rate. AQA rate = cost-adjusted reference rate, stake-weighted median of validator reports, published on-chain daily. 30-day intervals from activation; paid to the Assistance Fund 8 days after each interval ends. Implied rate from first payment: ~3.14%.
  - So unpaid days are earned and computable, not estimated — if balance + rate are readable (check Hyperliquid info API / system interest address 0x50..00+token_index).
  - REQUIREMENT (Mike, 2026-10-12): read the rate from Hyperliquid itself, daily, not a fixed % or a T-bill proxy — so a change of treasury/technical deployer, a deployer fee change, or a validator methodology change shows up automatically.
    - Store daily: AQA rate (as published on-chain), USDC balance at 0 UTC, earned = balance × rate. Store the deployer addresses too.
    - Alert on: rate change > X bp day-over-day, deployer change, a payment that differs from the sum of earned days by > 2%, a payment > 10 days late.
    - Reconcile each 30-day payment against the summed daily accruals; the payment is the truth, accruals fill the gap until it lands.
    - First step: confirm the info API exposes the AQA rate and the per-token balance history (if not: read the system interest address 0x50..00+token_index and derive).
- Unverified, likely small: USDH sends 50% of reserve yield to the Assistance Fund.

## Generic design requirement (Mike, 2026-10-12)
No one-off series per new revenue type. Revenue = config list of streams; adding a type is config only.
- Each stream: source + settlement mode.
  - `daily`: a daily series (as today).
  - `periodic`: lump payments with a known coverage period → spread evenly over the days covered.
- Unpaid tail (days since the last covered period): use the stream's own daily accrual inputs when available (HYPE: balance × on-chain rate), else the last period's daily rate; mark provisional; replaced when the payment lands.
- Report: show growth with and without streams younger than 180 days (a new stream inflates 90d/90d).

## All API daily series — re-fetch recent history each run
- DefiLlama revises history (HYPE: Orion $149M vs $178.5M latest 90d; AERO: $17.1M vs $24.9M). Re-pull the last N days (e.g. 30) each run and supersede changed rows.

## VVV — use disclosed business revenue (reviewed 2026-10-12)
- Orion already stores disclosures (`revenue_run_rate_usd`, manual, cited) and reports them as `revenueDisclosed` with growth between consecutive disclosures; staleness anomaly `revenue_disclosure_stale` already fires.
- Gap 1: only ONE disclosure stored ($100M, 2026-08-17, founder X post). Add prior: >$70M ARR, 2026-07-01 (Series A, TechCrunch/GeekWire) — gives growth.
- Gap 2: coinrevs revenue column uses the DefiLlama proxy ($9.3M = on-chain burns). Rule: revenue = disclosed when the asset has `revenue_disclosed`; DefiLlama proxy stays as a cross-check only. Holder flow stays = burns.
- Growth on disclosures: compute from the two latest disclosures (not 90d/90d); flag when gap < 90d or latest > 90d old.

## UNI — reviewed 2026-10-12: no fix needed
- Revenue = burns ($132M/yr) = v3 selected-pool fees ($121.6M, DefiLlama) + v2 1/6 fee (~$10M, missing in DefiLlama) + Unichain sequencer (small). Label "protocol fees (v2 + selected v3)".
- Upside not revenue: v4 ($965M/yr swap fees, fee switch not on, ~$160M at 1/6) + remaining v3 pools → valuation scenario/catalyst.
