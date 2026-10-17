# Price drivers, price-vs-target gaps, and new valuation ideas

Use this when Mike asks what is driving an asset's price, why Orion's target is far from spot, or whether the model is missing some value (TVL, value secured, network effects, monetary premium).

## 1. "What is driving <asset> today?"
1. Pull the move and the market at the same time: CoinGecko `coins/<id>` (24h/7d/30d change, 24h range, volume) plus BTC/ETH 24h change from `simple/price`. Compare them to split the asset's own move from market beta. For a merger or conversion, add the counterpart token and check the implied ratio (e.g. VELO vs 0.044 × AERO). A near-zero spread means the market believes the deal terms.
2. News: `web_search "<name> <ticker> price news <month year>"`, then `web_extract` the primary write-ups. Many news sites render articles client-side and return only the headline; use exchange news-flash pages (KuCoin flash, ChainCatcher mirrors) for the full terms.
3. Orion context: read the asset's latest signal (below), and say whether a known upcoming event makes the model stale (e.g. emissions or a staking mechanism changing). Don't let the reader treat a stale target as "the market is 2x overvalued".
4. Reply format: the move in numbers → the drivers ranked → a risk check (sell-the-news dates, migration friction, unknowns) → one offered next step.

## 2. Reading signals quickly
- `signals` columns: `id, signal_id, run_id, asset_id, schema_version, status, payload_json, emitted_at` (there is no `created_at`). In the payload: `spot.price`, `horizons.6m.{expected_target, upside_pct, scenarios.{bear,base,bull}.target}`, `horizons.6m.modules.<id>.{value, breakdown}`.
- To rank every asset by gap: `select asset_id, json_extract(payload_json,'$.spot.price'), json_extract(payload_json,'$.horizons.6m.expected_target'), round(json_extract(payload_json,'$.horizons.6m.upside_pct'),1) from signals where rowid in (select max(rowid) from signals group by asset_id) order by 4;`
- Before explaining a gap, read the asset YAML comments and its `docs/superpowers/notes/<date>-<asset>-onboarding.md`. They record Mike's decisions (bucket, capture rule, supply basis, haircut) and the open items. Never argue against those decisions in the explanation.

## 3. Explaining a big gap (narrative vs model)
- Compute the multiple the price implies: FDV ÷ measured holder flow (and on circulating), next to the bull-case multiple. Then work backward: holder flow needed to justify spot at a generous multiple (15–30x), as a multiple of today's flow.
- Go through possibly-missed value one item at a time, and give each one a verdict: off-chain or undisclosed revenue (is it already in the flow? does the trend show it?), fee-capture products (e.g. SVR: does it already route through the measured converter?), utility/payment demand (does payment abstraction remove any need to hold the token?), staking (paid from fees or from the team allocation = dilution), value kept by the company instead of the token.
- Always set dilution against the buy flow: tokens released per year vs tokens bought per year, the release wallet's behaviour (forwarded to an exchange?), and when the unreleased stock runs out.
- Label third-party figures (analyst targets, quarterly revenue claims) as unverified; on-chain figures as Orion's own reads.

## 4. "Total value X" metrics (TVL, TVS, volume) and network effects
Mike's position: a large TVL or TVS measures usefulness and network effects (deeper liquidity → less price impact → more use → more revenue; TVS = reach for integrators), and could some day be captured. Treat it as a call option to model, not an idea to dismiss.
- Don't value TVL/TVS as a standalone addend: it is user money with no claim, and fees already scale with it, so it double-counts. Route it through the assumptions instead:
  1. **Growth**: if TVL leads fees, TVL growth informs `rev_growth_y1`. Test the lead on the asset's history before building.
  2. **Durability/moat**: category share informs `growth_fade_years`, terminal growth and part of the discount rate.
  3. **Capture option**: base × target take rate × holders' share × probability of switch-on by year t × multiple, discounted. The probability comes from network strength, not a free pick.
- The reverse test that makes the option honest: gap ÷ multiple = extra holder flow needed; compare it with gross fees (implied holders' share of fees) and with the base (implied take rate of TVS/TVL). A gap that needs <~25% of existing gross fees is a real capture option (fee switch); one that needs >100% is a growth bet; one that needs a take rate far above the category's is narrative.
- The latent capture that exists today is the gap between gross fees and holder revenue (UNI, PUMP, CAKE, SKY). TVL is one step further out.
- Build order to propose: report-only `monitor_only` metrics plus an "implied capture" report line first (no engine change), then an option module only for assets where the gap is real. Both are priced options for Mike to pick, through the spec → plan → build process.
- **Settled result: TVL is not a growth input.** In a walk-forward test (recipe in §6), TVL growth and fees/TVL made next-quarter fee forecasts worse for UNI/CAKE/CRV/AERO and helped only SKY. TVL moves with fees at the same time, mostly through token price, and doesn't lead them. Don't re-propose lever 1 without new evidence.
- **What survives is dominance → durability, as judgment, not a formula.** Category share and its trend decide *where inside the band* `growth_fade_years`, `terminal_growth` and `discount_rate_base` sit, citing the share observation. Falling share means the bear edge even when share is high. Never use it for `rev_growth_y1` or the multiple. No `f(share)` coefficient until a cross-protocol durability study (30+ protocols) supports one. The design lives in `docs/superpowers/specs/2026-10-17-orion-dominance-design.md` (monitor-only `dominance_share` / `dominance_share_1y`, new `defillama_share` source, persona rule).
- Size the lever before building: in a scratch home, set each scenario's terminal growth to its band max, discount rate to its band min, and fade +2y, and report the gap closed. The lever is large for a dominant asset with a big flow (UNI closed ~45% of its gap) and near zero where the problem is flow size or dilution (LINK ~1%). Say which case the asset is.

## 6. Testing whether metric X leads fees (out-of-sample)
- Data: `api.llama.fi/protocol/<slug>` → `tvl[].{date,totalLiquidityUSD}`; `summary/fees/<slug>?dataType=dailyFees` → `totalDataChart` `[ts, value]`. Smooth both with a 28-day mean and work in logs. The execute_code kernel has numpy but no pandas, so use day-index dicts and arrays.
- Target: next-91-day log fee change, sampled weekly. Baseline: fee mean-reversion (log fee minus its trailing 180-day mean). Candidates: past-quarter TVL growth; log(fees/TVL) minus its trailing mean.
- Score walk-forward only: at each point, fit only on rows whose target was already known (leave a 13-week gap), predict, and record the absolute error. Report the MAE per model versus the baseline and versus "no change".
- Full-sample regressions on 1–2 years of overlapping windows give big spurious t-stats (|t| 6–9) even with Newey-West errors. Never report them as evidence. Also control for token price: a TVL effect that vanishes with price in the model is just price.
- Assets with under ~2 years of overlapping history (HYPE, LINK, PUMP, LIT) can't be scored this way; say "too short", don't extrapolate.

## 7. Dominance share recipe (DefiLlama, free endpoints)
- `overview/fees?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true` (`total30d`, `total1y`, `category`) and `overview/dexs?...` (volume); per chain, `overview/dexs/<Chain>` (e.g. `Base`, `BSC`). Filter by `category`, group by `parentProtocol`, share = parent ÷ category total; 30d vs 1y gives the trend.
- Categories and measures: DEXes `Dexs` volume (not TVL share, because emissions buy TVL). AERO and CAKE get both home-chain and global shares. HYPE/LIT `Derivatives` fee share (`overview/derivatives` volume is paywalled). PUMP `Launchpad`, SKY `CDP` (`parent#maker`). LINK: the fee `Oracle` category is meaningless (geodnet dwarfs it), so take TVS share from a cited secondary source.

## 8. Scratch whatif per scenario
- `model whatif <a> --scenario <s> --set k=v` overrides one scenario only. A `bull.k=v` key prefix is refused as an unknown key. Loop per scenario and recombine with the scenario probabilities (0.25/0.5/0.25).
- First check the scratch home reproduces the live signal's expected target exactly, then delete the scratch home (it holds `.env`).

## 5. DefiLlama cross-section recipe (read-only analysis)
- `api.llama.fi/protocols` gives `tvl`, `parentProtocol`, `gecko_id`, `symbol`. `api.llama.fi/overview/fees?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true&dataType=dailyFees|dailyRevenue|dailyHoldersRevenue` gives `total30d` per child protocol. Per asset: `summary/fees/<slug>?dataType=...`, `summary/dexs/<slug>` for volume.
- Group by `parentProtocol` (else `id#<defillamaId>`) for both TVL and fees. Most children have no `gecko_id` (e.g. Uniswap V3), so match to CoinGecko by parent `gecko_id`, else by symbol keeping the largest market cap, and dedupe by symbol. Matching by child `gecko_id` alone leaves a handful of rows and a meaningless regression.
- CoinGecko `coins/markets?per_page=250&page=N` for 2–3 pages, with ~3s between pages when keyless.
- Regress log market cap on log revenue, then add log TVL. Report the coefficient ± SE and the R² change, plus n and the snapshot caveat. A non-significant TVL coefficient cuts both ways (it really adds little, or the market under-prices it); only a time-series lead test can tell which.
- DefiLlama's `/oracles` (TVS) endpoint needs a paid key. Its "TVL" for Chainlink is staking, not value secured; cite TVS from a named secondary source and say so.
