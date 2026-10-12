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
1. If Mike says prod is being changed, wait for his go before reading it. Check `git log -5` for what changed, then run the report straight off prod (`node dist/cli/index.js report yield --json`, read-only).
2. Growth needs 180/182 complete days of every flow. If prod's payout series are short, backfill **prod once** rather than re-doing scratch backfills for every table request (Mike wants prod to carry the history). Follow the live-change rules in SKILL.md: check nothing is mid-run, `.backup` first, then run sequentially, one asset at a time (parallel writers contend on the DB), scoped to the payout flows and the revenue streams: `node dist/cli/index.js data fetch <a> --metric <flows...> --backfill-days 200`, in the background with notify, clear of the 05:05–05:40 PT cron window. A scratch backfill (parallel is fine there) is only for previews before Mike clears a prod write.
3. Before and after a history re-fetch, list `source='manual'` rows in the window (`select id, metric_key, observed_at, value, source_detail from observations where asset_id=? and source='manual' and superseded_by is null`). These are Mike-approved corrections; if the fetch superseded one, restore it (`data set ... --source manual --detail <original detail>`) and say so.
4. `report yield --json` gives everything: `marketCap`, `fdv`, `revenue.{basis,annualized,growth,growthExNew,streams[],provisional}` (use this for the revenue column; `income.revenue` is the old holder-flow-based figure), `revenueDisclosed`, `flows[].{gross,net,haircut,bucket}`, `notes`. Build the tables from it, not from hand-rolled sums. Show HYPE growth both as-is and ex new streams, and footnote provisional (unpaid) days.
5. A big jump between a fresh pull and prod means a DefiLlama revision. Use what prod reports where Mike has decided on the stored value (AERO keeps its manual row; see SKILL.md) and footnote DefiLlama's figure; otherwise offer the prod re-fetch (a live write, so ask).

### Revenue definitions (Mike's rule)
Revenue = what users pay the protocol, net of what goes to LPs/suppliers (fees − supply-side). Where a business discloses revenue that settles off-chain, use the disclosure. For HYPE, UNI and VVV, Orion's stored "revenue" ≈ holder flow, so P/E = holder flow ratio; check each against this rule whenever revenue is shown:
- HYPE: DefiLlama `dailyRevenue` ≈ Assistance Fund buys. Trading revenue checks out against Artemis and Token Terminal. Builder, HIP-3 deployer and HLP fees are correctly excluded as pass-through, and gas and priority fees are rounding. The material gap is AQAv2 USDC reserve yield (~$177M a year, paid every 30 days to the Assistance Fund): DefiLlama's data omits it and Token Terminal counts it. Orion now records it as the `reserve_yield` periodic stream (paid ledger + provisional unpaid tail); it is a step-up that inflates 90d/90d until it is in both windows, so show growth ex new streams beside the headline.
- UNI: burns (USD value of UNI sent to 0xdead) ≈ protocol fees, so the figure is right. Documented split (Uniswap developer docs, "Protocol Fee Configuration"): v2 all pools 1/6 of 0.30%; v3 selected pools only, 1/4 on the 0.01%/0.05% tiers and 1/6 on 0.30%/1%; v4 not switched on; Unichain sequencer fees also burn. DefiLlama's protocol revenue shows v3 only and misses v2 (~1/6 of v2 swap fees), so burns run slightly above it. Label it "protocol fees (v2 + selected v3)". v4 and the unswitched v3 pools are upside: a valuation scenario/catalyst, never revenue. Gross swap fees are LP income, not revenue.
- VVV: revenue = the latest disclosed run-rate (`revenue.basis = disclosed`; stored as `revenue_run_rate_usd`, manual, cited; disclosures are found via press coverage of founder posts and funding rounds).
- When auditing any asset's revenue, look for big missing streams first (a whole income type such as reserve yield or off-chain business revenue), not pass-through or rounding items; check at least two independent trackers (Token Terminal, Artemis, DefiLlama's adapter source on GitHub) and the protocol's own docs for the fee split. DefiLlama's series is just the burns: keep it as a cross-check only. Holder flow stays = burns. Growth between disclosures less than 90 days apart annualizes absurdly; show it as n/m.

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
- **DefiLlama revises past days upward.** Orion now re-reads the last 30 written days each run (`revision_days`), but older days keep the values first fetched, and manual rows in the window are left alone. A fresh pull can still run well above stored for older history (HYPE 20–46%). Compare per day to locate the drift, and footnote both figures rather than silently using either.
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
