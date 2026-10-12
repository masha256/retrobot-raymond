# Orion dev queue — revenue definitions (hold until HYPE, UNI, VVV reviews are done)

## HYPE — USDC reserve yield missing from revenue (reviewed 2026-10-12)
- Trading revenue OK: DefiLlama dailyRevenue 90d ann. $727M (perps $706M, spot $20M, outcomes $0.3M) = 99% of fees net of builder/HIP-3 deployer/maker rebates/HLP 1%. Artemis LTM $918M (−27% YoY), consistent. HyperEVM gas (~$7M/yr) and priority fees: rounding.
- MISSING: AQAv2 USDC reserve yield (~90% of yield on USDC backing HyperCore), started 2026-08-26, funds Assistance Fund buybacks.
  - First payment 2026-10-03: $14.58M covering 2026-08-26..09-24 (30d) → ~$0.486M/day, ~$177M/yr (BlockBeats est. $193M).
  - Token Terminal counts it ("USDC Reserve Income"). DefiLlama's adapter adds `dailyAqav2Yield` but data shows it as zero (rev/fee flat 0.80–0.87 through 08-26 and 10-03).
  - Effect: revenue ≈ $904M/yr, P/E ≈ 21x (from 26.2x); holder flow rises the same.
  - Mechanics (Hyperliquid docs, "Aligned quote assets", AQAv2): accrues DAILY = USDC balance at 0 UTC × AQA rate. AQA rate = cost-adjusted reference rate, stake-weighted median of validator reports, published on-chain daily. 30-day intervals from activation; paid to the Assistance Fund 8 days after each interval ends. Implied rate from first payment: ~3.14%.
  - So unpaid days are earned and computable, not estimated — if balance + rate are readable (check Hyperliquid info API / system interest address 0x50..00+token_index).
- Unverified, likely small: USDH sends 50% of reserve yield to the Assistance Fund.

## Generic design requirement (Mike, 2026-10-12)
No one-off series per new revenue type. Revenue = config list of streams; adding a type is config only.
- Each stream: source + settlement mode.
  - `daily`: a daily series (as today).
  - `periodic`: lump payments with a known coverage period → spread evenly over the days covered.
- Unpaid tail (days since the last covered period): accrue at the last period's daily rate, marked provisional; replaced when the payment lands.
- Report: show growth with and without streams younger than 180 days (a new stream inflates 90d/90d).
