# Coinrevs comparison tables — 2026-10-12

Source: prod Orion DB (commit 4ed14b2), `report yield`, latest complete day 2026-10-11. Payout series backfilled to 200 days in prod (backup taken first).
Market cap = price × circulating supply (CoinGecko circulating; wrappers = on-chain total).
Annualized = last 90 days × 365/90 (Curve family and UNI: 91 days). Growth = latest 90d vs prior 90d, compounded to a year. PEG = P/E ÷ annualized growth (%).

## Revenue

| Protocol | Market cap | Annualized revenue | Annualized revenue growth | P/E | PEG |
|---|---|---|---|---|---|
| HYPE | $19,081M | $904.4M¹ | +282% (ex-new +135%)² | 21.1x | 0.07 (ex-new 0.16) |
| UNI | $4,681M | $132.0M³ | n/m⁴ | 35.4x | n/m⁴ |
| VVV | $1,155M | $100.0M⁵ | n/m⁴ | 11.5x | n/m⁴ |
| AERO | $909M | $69.7M | +30% | 13.0x | 0.43 |
| CRV | $574M | $5.7M | −55% | 100.5x | —⁶ |
| cvxCRV | $61.8M | $5.9M | −8% | 10.4x | —⁶ |
| sdCRV | $23.7M | $3.5M | −57% | 6.8x | —⁶ |
| yCRV | $14.1M | $2.2M | −63% | 6.3x | —⁶ |

## Holder flow

| Protocol | Market cap | Annualized buybacks | Annualized slippage-adj. direct payments | Annualized holder flow | Holder flow ratio |
|---|---|---|---|---|---|
| HYPE | $19,081M | $904.4M⁷ | $0 | $904.4M | 21.1x |
| UNI | $4,681M | $132.0M⁸ | $0 | $132.0M | 35.4x |
| VVV | $1,155M | $9.4M⁸ | $0 | $9.4M | 123.1x |
| AERO | $909M | $0 | $68.4M | $68.4M | 13.3x |
| CRV | $574M | $0 | $13.7M | $13.7M | 42.0x |
| cvxCRV | $61.8M | $0 | $5.2M | $5.2M | 11.9x |
| sdCRV | $23.7M | $0 | $2.4M | $2.4M | 9.9x |
| yCRV | $14.1M | $0 | $1.5M | $1.5M | 9.2x |

### Slippage adjustments (gross → net)
- **AERO:** fees $69.7M, 2% haircut (pool-token basket) → $68.4M
- **CRV:** crvUSD fees $5.14M, 0%; vote incentives $8.78M, 3% → $8.51M. Total $13.65M
- **cvxCRV:** crvUSD $2.69M, 0%; CRV $1.89M, 1% → $1.88M; CVX $0.64M, 0.5% → $0.64M. Total $5.20M
- **sdCRV:** crvUSD $0.66M, 0%; CRV $0.22M, 0.5% → $0.22M; bribes paid in sdCRV $1.59M, 5% → $1.51M. Total $2.39M
- **yCRV:** crvUSD vault shares $1.54M, 0%

## Footnotes
1. **HYPE revenue** = trading fees $727.0M + USDC reserve yield (AQAv2) $177.4M. 17 unpaid days of yield accrued at the last period's daily rate (provisional).
2. Reserve yield started 2026-08-26, so it's only in the latest window. "Ex-new" excludes it; the two converge by mid-Feb.
3. **UNI revenue** = protocol fees (v2 + selected v3) = UNI burned. v4 fee switch not on: upside, not revenue.
4. **Ramp, not meaningful.** UNI 90d/90d +173% (compounds to +5,500%/yr); VVV disclosures $70M (2026-07-01) → $100M (2026-08-17), +43% in 47 days (+1,500%/yr).
5. **VVV revenue** = founder-disclosed run rate, latest 2026-08-17 (8 weeks old). Measured on-chain burns are $9.4M.
6. Negative growth: PEG undefined.
7. **HYPE buybacks** = Assistance Fund $727.0M + reserve yield $177.4M (it funds the same buybacks). Held, not burned.
8. **UNI, VVV:** buybacks are burned. UNI verified on-chain: all 5.91M UNI bought in 91 days ended at 0xdead.

Wrapper revenue = the protocol's (Convex / StakeDAO / Yearn) revenue on the wrapper, not what holders receive. CRV and wrapper market caps aren't additive.
