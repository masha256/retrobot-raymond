# Coinrevs comparison tables — 2026-10-12

Data: prod Orion DB as of 2026-10-12 (commit ab3af25), latest complete day 2026-10-11. Payout series backfilled to 200 days in a scratch copy for growth; prod untouched.
Market cap = Orion's report market cap (price × CoinGecko circulating supply; wrappers = price × on-chain total supply).
Growth = latest 90 days vs prior 90 days (91 for the Curve family), compounded to a year.

## Revenue

| Protocol | Market cap | Annualized revenue | Annualized revenue growth | P/E | PEG |
|---|---|---|---|---|---|
| HYPE | $19,081M | $727.0M | +135% | 26.2x | 0.20 |
| UNI | $4,681M | $132.0M | n/m¹ | 35.4x | n/m¹ |
| VVV | $1,155M | $9.3M² | n/m¹ | 124.2x | n/m¹ |
| AERO | $909M | $100.8M³ | n/m¹ | 9.0x | n/m¹ |
| CRV | $574M | $5.7M | −54.7% | 100.5x | n/m⁴ |
| cvxCRV | $61.8M | $5.9M | −7.6% | 10.4x | n/m⁴ |
| sdCRV | $23.7M | $3.5M | −56.6% | 6.8x | n/m⁴ |
| yCRV | $14.1M | $2.2M | −62.6% | 6.3x | n/m⁴ |

## Holder flow

| Protocol | Market cap | Annualized buybacks | Annualized direct payments (slippage-adj.) | Annualized holder flow | Holder flow ratio |
|---|---|---|---|---|---|
| HYPE | $19,081M | $727.0M⁵ | $0 | $727.0M | 26.2x |
| UNI | $4,681M | $132.0M⁶ | $0 | $132.0M | 35.4x |
| VVV | $1,155M | $9.4M⁶ | $0 | $9.4M | 123.1x |
| AERO | $909M | $0 | $98.8M³ | $98.8M | 9.2x |
| CRV | $574M | $0 | $13.7M | $13.7M | 42.0x |
| cvxCRV | $61.8M | $0 | $5.2M | $5.2M | 11.9x |
| sdCRV | $23.7M | $0 | $2.4M | $2.4M | 9.9x |
| yCRV | $14.1M | $0 | $1.5M | $1.5M | 9.1x |

### Slippage adjustments (gross → net)
- **AERO:** fees $100.8M, 2% haircut (pool-token basket) → $98.8M
- **CRV:** crvUSD fees $5.14M, 0%; vote incentives $8.78M, 3% → $8.51M. Total $13.65M
- **cvxCRV:** crvUSD $2.69M, 0%; CRV $1.90M, 1% → $1.88M; CVX $0.64M, 0.5% → $0.64M (program ran dry 2026-08). Total $5.20M
- **sdCRV:** crvUSD $0.66M, 0%; CRV $0.22M, 0.5% → $0.22M; bribes paid in sdCRV $1.59M, 5% → $1.51M. Total $2.39M
- **yCRV:** crvUSD vault shares $1.54M, 0%

## Footnotes
1. **Ramp quarters, PEG not meaningful.** 90d/90d change: UNI +173%, VVV +185%, AERO +54%; compounded that is +481% to +7,000% a year.
   - UNI monthly burns: $4–5M Apr–Jul → $7.9M Aug → $18.1M Sep.
   - VVV monthly burns: $0.1–0.2M Apr–Jun → $2.2M Sep.
   - AERO monthly fees: $4.5–6.8M Apr–Aug → $15.0M Sep.
2. **VVV:** measured revenue (DefiLlama, ≈ burns). Founder-disclosed revenue $100M/yr → P/E 11.5x on that basis.
3. **AERO:** uses DefiLlama's revised history (re-fetched in the scratch copy). Prod still holds the pre-revision series: $69.5M a year, P/E 13.1x. The backfill also replaced one manual row (2026-09-10). Prod needs the same re-fetch.
4. Negative growth: PEG undefined.
5. **HYPE:** the Assistance Fund buys and holds (non-circulating); not burned.
6. **UNI, VVV:** buybacks are burned. UNI verified on-chain: all 5.91M UNI bought in 91 days ended at 0xdead.

Wrapper revenue = the protocol's (Convex / StakeDAO / Yearn) revenue on the wrapper, not what holders receive.
