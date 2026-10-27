# Coinrevs comparison tables — 2026-10-26

Source: prod Orion DB (commit 2611dee), `report yield --json` (read-only), latest complete day 2026-10-25 (LIT 2026-10-24). No backfill needed.
Market cap = price × circulating supply (CoinGecko circulating; wrappers = on-chain total). Never FDV.
Annualized = last 90 days × 365/90 (HYPE, AERO, VVV) or 91 days (all others). Growth = latest window vs prior window, compounded to a year. PEG = P/E ÷ annualized growth (%).

## Revenue

| Protocol | Market cap | Annualized revenue | Annualized revenue growth | P/E | PEG |
|---|---|---|---|---|---|
| HYPE | $17,155M | $966.5M¹ | +536% (ex-new +258%)² | 17.7x | 0.03 (ex-new 0.07) |
| LINK | $8,788M | $57.4M¹¹ | −17% | 153.1x | —⁶ |
| UNI | $4,396M | $132.8M³ | n/m⁴ | 33.1x | n/m⁴ |
| PUMP | $1,954M | $679.2M⁹ | +1,022% | 2.9x | 0.003 |
| SKY | $1,617M | $50.0M¹⁰ | n/m⁴ | 32.4x | n/m⁴ |
| VVV | $1,199M | $100.0M⁵ | n/m⁴ | 12.0x | n/m⁴ |
| LIT | $795M | $41.0M⁸ | +368% (ex-new +100%)² | 19.4x | 0.05 (ex-new 0.19) |
| CAKE | $667M | $79.8M⁷ | +458% | 8.4x | 0.02 |
| AERO | $563M | $76.6M | +94% | 7.4x | 0.08 |
| CRV | $554M | $5.7M | −52% | 96.5x | —⁶ |
| cvxCRV | $58.6M | $6.0M | −16% | 9.8x | —⁶ |
| sdCRV | $22.7M | $3.6M | −41% | 6.4x | —⁶ |
| yCRV | $13.1M | $2.3M | −59% | 5.7x | —⁶ |

## Holder flow

| Protocol | Market cap | Annualized buybacks | Annualized slippage-adj. direct payments | Annualized holder flow | Holder flow ratio |
|---|---|---|---|---|---|
| HYPE | $17,155M | $966.5M¹² | $0 | $966.5M | 17.7x |
| LINK | $8,788M | $57.4M¹³ | $0 | $57.4M | 153.1x |
| UNI | $4,396M | $132.8M¹⁴ | $0 | $132.8M | 33.1x |
| PUMP | $1,954M | $316.2M¹⁴ | $0 | $316.2M | 6.2x |
| SKY | $1,617M | $0 | $50.0M¹⁶ | $50.0M | 32.4x |
| VVV | $1,199M | $10.2M¹⁴ | $0 | $10.2M | 117.8x |
| LIT | $795M | $32.7M¹⁵ | $0 | $32.7M | 24.3x |
| CAKE | $667M | $58.4M¹⁴ | $0 | $58.4M | 11.4x |
| AERO | $563M | $0 | $75.1M | $75.1M | 7.5x |
| CRV | $554M | $0 | $12.8M | $12.8M | 43.1x |
| cvxCRV | $58.6M | $0 | $5.0M | $5.0M | 11.6x |
| sdCRV | $22.7M | $0 | $2.5M | $2.5M | 9.2x |
| yCRV | $13.1M | $0 | $1.6M | $1.6M | 8.3x |

### Slippage adjustments (gross → net)
- **AERO:** fees (pool-token basket) $76.6M, 2% → $75.1M. Total $75.1M
- **CRV:** crvUSD fees $5.2M, 0%; vote incentives $7.9M, 3% → $7.7M. Total $12.8M
- **cvxCRV:** crvUSD fees $2.6M, 0%; CRV $2.0M, 1% → $2.0M; CVX $0.5M, 0.5% → $0.5M. Total $5.0M
- **sdCRV:** crvUSD fees $0.7M, 0%; CRV $0.2M, 0.5% → $0.2M; bribes paid in sdCRV $1.7M, 5% → $1.6M. Total $2.5M
- **yCRV:** crvUSD vault shares $1.6M, 0%
- **SKY:** USDS $21.1M and SKY paid on $28.9M, both 0%

## Footnotes
1. **HYPE revenue** = trading fees $789.1M + USDC reserve yield (AQAv2) $177.4M. 31 unpaid days of yield accrued at the last period's daily rate (provisional).
2. **Ex-new** excludes streams younger than 180 days: HYPE reserve yield (started 2026-08-26), LIT's Robinhood-instance fees (started 2026-06-26).
3. **UNI revenue** = protocol fees (v2 + selected v3) = UNI burned. v4 fee switch not on: upside, not revenue.
4. **Ramp, not meaningful.** UNI +161% vs prior 91d (burns began 2026-03-27, so the prior window is the ramp); VVV disclosures $70M (2026-07-01) → $100M (2026-08-17), +43% in 47 days; SKY +266% vs prior 91d ($3.4M → $12.5M) after the Splitter began sending 45% of surplus to stakers as USDS (2026-08-17) and surplus rose.
5. **VVV revenue** = founder-disclosed run rate, latest 2026-08-17 (10 weeks old). Measured on-chain burns are $10.2M.
6. Negative growth: PEG undefined.
7. **CAKE revenue** = fee-converter CAKE: burned $58.4M + treasury $21.3M (~73/27 split). +54% vs prior 91d.
8. **LIT revenue** = Lighter core fees $33.2M + Lighter's 50% of Robinhood-instance fees $7.9M (Lighter API). Holder-flow growth is not yet computable: the buyback series has 174 of 182 days (Lighter's API keeps ~150 days; no DefiLlama stitch by your call). It completes around 2026-11-03.
9. **PUMP revenue** = pump.fun revenue (DefiLlama dailyRevenue); 47% of it goes to buyback-and-burn. +83% vs prior 91d.
10. **SKY revenue** = surplus paid to stakers (both halves), not Sky's gross net interest income. Not yet audited against the revenue rule.
11. **LINK revenue** = on-chain service fees converted to LINK (Payment Abstraction). Off-chain/enterprise revenue isn't counted. −4% vs prior 91d.
12. **HYPE buybacks** = Assistance Fund $789.1M + reserve yield $177.4M (it funds the same buybacks). Held, not burned.
13. **LINK buybacks** go to the Chainlink Reserve: held, not burned. Shown gross; Orion's yield report applies a 5% overhang haircut ($54.5M).
14. **Burned:** UNI (verified on-chain: everything bought ends at 0xdead), VVV, CAKE (only the converters' CAKE; minted-and-reburned CAKE excluded), PUMP (read as the daily fall in supply; mint authority revoked).
15. **LIT:** bought LIT funds staking rewards, and an equal count is burned each quarter from the ecosystem reserve (Q2 15.64M, Q3 2.45M LIT), so it counts as buyback + burn. Watch: 3.0M bought LIT went to Coinbase Prime in September.
16. **SKY:** both halves reach staked SKY: USDS $21.1M (cash) + SKY bought by the flapper and paid on to stakers $28.9M (sellable tokens; nothing is burned despite the "Smart Burn Engine" name). Counted as direct payments, per your 2026-10-16 call.

Wrapper revenue = the protocol's (Convex / StakeDAO / Yearn) revenue on the wrapper, not what holders receive. CRV and wrapper market caps aren't additive.
