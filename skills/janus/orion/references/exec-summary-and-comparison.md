# Cross-asset executive summary and like-kind comparison

Use this when Mike asks for a summary table across Orion assets (price, revenue, holder flows, multiples, growth, PEG) or for an apples-to-apples comparison of protocols.

## Coinrevs comparison tables (Mike's current spec)
Two tables, one row per asset, sorted by market cap, columns in exactly this order:
- **Revenue:** protocol, market cap, annualized revenue, annualized revenue growth, P/E (market cap ÷ annualized revenue), PEG (P/E ÷ annualized growth in percentage points).
- **Holder flow:** protocol, market cap, annualized buybacks, annualized slippage-adjusted direct payments to holders (cash + sellable tokens merged), annualized holder flow (= buybacks + direct payments), holder flow ratio (market cap ÷ holder flow).
- Market cap = price × circulating supply (CoinGecko's; on-chain total for the wrappers). Never FDV.
- Burns are not a separate column: a burn is a buyback that was destroyed; add buybacks once. Footnote which buybacks are burned (UNI, VVV) and which are held (HYPE's Assistance Fund).
- Under the tables: a slippage-adjustment list (gross → haircut → net per stream) and numbered footnotes. File: `~/.hermes/profiles/raymond/workspace/orion/coinrevs-tables-<date>.md`, sent with `MEDIA:`.

### Procedure
1. If Mike says prod is being changed, wait for his go before reading it; then re-copy prod (`sqlite3 orion.db ".backup <scratch>/orion.db"`) so the tables reflect his latest commits.
2. Growth needs 180/182 complete days of every flow; live payout series hold ~100. Backfill in a scratch home only, scoped and parallel: `ORION_HOME=$S node dist/cli/index.js data fetch <a> --metric <payout flows> --backfill-days 200`, one background job per asset. If a fetch reports `partial` with a manual-row conflict, re-run with `--adopt` (scratch only) and footnote that prod still holds the old row.
3. `ORION_HOME=$S node dist/cli/index.js report yield --json` gives everything: `marketCap`, `fdv`, `income.revenue.{annualized,growth}`, `flows[].{gross,net,haircut,bucket}`. Build the tables from it, not from hand-rolled sums.
4. Compare each backfilled window with prod. A big jump means a DefiLlama revision (AERO went $69.5M → $100.8M); use the revised figure, footnote prod's, and offer the prod re-fetch (a live write, so ask).

### Revenue-definition caveat
For HYPE, UNI and VVV, Orion's "revenue" ≈ holder flow, so P/E = holder flow ratio. Flag this whenever revenue is shown:
- HYPE: DefiLlama `dailyRevenue` ≈ Assistance Fund buys; excludes HLP, builder and deployer fees.
- UNI: the USD value of UNI burned, which understates the fees burners receive. Gross swap fees are LP income, not revenue.
- VVV: DefiLlama's series tracks the burns; real revenue is off-chain (only founder disclosures).

## Output shape (Mike's preferences)
- Deliver a markdown file he can save, under `~/.hermes/profiles/raymond/workspace/orion/orion-exec-summary-<date>.md`, sent with `MEDIA:`. On later requests, extend the same file rather than starting a new one.
- Use simple executive-summary tables, one row per asset, with the key multiple in bold. Put caveats in numbered footnotes under the table, not in the cells.
- Standard sections:
  1. Valuation snapshot: spot, market cap, revenue, holder flow, MC/Rev, MC/holder flow, yield, Orion 12m target (upside), grade.
  1b. Growth & PEG: previous-90d flow, latest-90d flow, 90d/90d change, annualized growth, PEG, Orion `rev_growth_y1`, PEG on that assumption.
  2. Holder flows by type: one row per stream, with its payout token and bucket.
- Chat reply: lead with 3–5 takeaways, then the gaps. Keep it short; the file holds the detail.

## Data procedure
1. Price, targets and grade: take the latest signal per asset from `signals` (`payload_json`), not `signals.jsonl`, which is missing some recent lines.
2. Holder flow per stream: annualize Orion's own window from `observations` (`flow_usd.*`, `superseded_by is null`). Window is 90d for HYPE/AERO/VVV and 91d for the Curve family. Check that your annualized total reproduces the signal's revenue run rate before trusting it.
3. Revenue: Orion has no gross protocol revenue for most assets; there revenue = holder flow. Say so in the table, and don't present MC/holder flow as price-to-sales. VVV's revenue input is a disclosure, not a measurement.
4. Growth: `orion report yield` now computes 90d/90d growth once 180/182 days of history exist (see the coinrevs procedure for the backfill). `rev_growth_y1` in the assumption sets is a calibrated assumption, not a measurement. Fallback when the report can't be used, measure 90d/90d yourself:
   - Re-pull ~185 days per stream from the same sources Orion uses: DefiLlama daily holders revenue for HYPE/AERO, and on-chain Transfer logs priced daily for the rest, via `ORION_BASE_RPC_URL` / `ORION_ETH_RPC_URL` from `.env`.
   - Run the probe as a throwaway `.mjs` in the repo, with key-masked output, and delete it afterwards.
   - Validate the latest window against Orion's stored observations. On-chain streams should match within ~1%.
   - Annualize as (1+g90)^(365/90)-1.
   - PEG = MC/holder flow ÷ annualized growth in percentage points. It is undefined (n/m) when growth ≤ 0. Also show the PEG on Orion's Y1 assumption, because annualizing one quarter exaggerates both ways.

## Pitfalls
- **DefiLlama revises past days upward**, and Orion keeps the values it first fetched. A fresh pull can run 20–46% above stored (HYPE). Compare per day to locate the drift, and footnote both figures rather than silently using either.
- **A stream that started or ramped inside the earlier window gives a meaningless 90d/90d** (VVV's burn program ramped from about $0.24M to $1.19M). Mark it n/m and give a steadier measure, such as the monthly trend of the discretionary Safe buybacks.
- **Before agreeing that Orion used to have a metric, check:** `git log --all -G`, calibration YAML comments, `docs/superpowers/notes`, signal payload keys and `session_search`. Calibration notes record observed trends as prose, not stored numbers. Report what exists, and offer to build it.

## Like-kind holder-flow buckets (Mike's framework)
Classify every holder-flow stream into one of four buckets, and compare multiples within a bucket:
1. **Cash**: stablecoins, or vault shares redeemable 1:1 (e.g. Yearn crvUSD vault shares).
2. **Sellable tokens**: any liquid token paid out, e.g. CRV, CVX, WETH, pool tokens.
3. **Buyback + burn**.
4. **Buyback + hold**.

Mike treats liquid non-stable payouts as effectively cash: they can be sold immediately, minus slippage. Distributions in either form deserve a higher multiple than any buyback.
- For recorded (not ad hoc) bucket series and haircuts — burns unhaircut, holds with an overhang haircut, cash minus per-token slippage — see `data-sourcing-and-protocol-revenue.md`.
- Don't penalize sellable-token payouts for the token's price risk or for Orion's bearish fair value; the holder can sell on receipt. He rejects that framing as too conservative.
- Only apply a slippage or circularity markdown when it is material:
  - Payouts in the valued token itself, in a thin market (sdCRV bribes are paid in sdCRV).
  - Long-tail tokens in a fee basket (AERO).
- Useful refinements to raise alongside the buckets:
  - Funding source: fee-funded vs emission-funded (bribes shrink as emissions decline).
  - Discretionary vs programmatic buybacks (`capture_rule`).
  - Yield measured on the receiving supply, and lock cost (ve-locks vs a sellable wrapper).
- Bucket edge cases:
  - HYPE's Assistance Fund buys and holds (economically a hold). Orion's configs tag it `burn`; in comparison tables show it as a buyback, not burned, and footnote it. Don't change the config tag unasked.
  - Verify "buyback = burn" on chain before asserting it: for every burn tx in the window, net each address's token transfers across the receipt. In-tx transfers to non-burn addresses are usually DEX routing (pools buying the token), not leakage; only net gainers other than the burn address matter (UNI: all 5.9M bought ended at 0xdead).
  - CRV's vote incentives go in sellable tokens, at about 41x versus 111x on fees only.
- Orion's model multiples (8x for wrapper distributions vs 80x for HYPE's buyback) are the inverse of Mike's ranking. Point this out, but don't change asset configs unasked; propose one multiple per bucket instead.
