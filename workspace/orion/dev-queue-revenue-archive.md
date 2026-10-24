# Orion dev queue — archive of built or closed items

Moved from dev-queue-revenue.md on 2026-10-24 (Mike). Kept for the record: findings, figures and the design decisions behind what was built.

## [DONE] HYPE — USDC reserve yield missing from revenue (reviewed 2026-10-12)
Built: `flow_usd.reserve_yield` from `hype.reserve_yield_payments` (ledger of 0x5000…0000 → Assistance Fund), revenue stream `settlement: periodic`. The daily on-chain rate is not available (Hyperliquid's `alignedQuoteTokenInfo` returns 422), so accrual between payments runs at the last period's daily rate (provisional).
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

## [DONE] Generic design requirement (Mike, 2026-10-12)
Built: `reporting.revenue` stream list (daily | periodic | disclosed); growth shown as-is and ex streams < 180d.
No one-off series per new revenue type. Revenue = config list of streams; adding a type is config only.
- Each stream: source + settlement mode.
  - `daily`: a daily series (as today).
  - `periodic`: lump payments with a known coverage period → spread evenly over the days covered.
- Unpaid tail (days since the last covered period): use the stream's own daily accrual inputs when available (HYPE: balance × on-chain rate), else the last period's daily rate; mark provisional; replaced when the payment lands.
- Report: show growth with and without streams younger than 180 days (a new stream inflates 90d/90d).

## [DONE] All API daily series — re-fetch recent history each run
Built: DefiLlama primaries re-read 30 written days (`revision_days`); manual rows in the window are left alone.
- DefiLlama revises history (HYPE: Orion $149M vs $178.5M latest 90d. AERO correction 2026-10-12: its apparent $17.1M→$24.9M "revision" was the known 2026-09-10 DefiLlama artifact ($7.92M day), not a revision — manual row re-applied after the prod backfill). Re-pull the last N days (e.g. 30) each run and supersede changed rows.

## [DONE in Orion] VVV — use disclosed business revenue (reviewed 2026-10-12)
Built: revenue = disclosed stream (`revenue_run_rate_usd`, DefiLlama proxy as cross_check); 3 cited disclosures ($70M 2026-07-01, $100M 2026-08-17, $150M 2026-10-14). Not verified here: whether the coinrevs site's revenue column now uses it (Gap 2 is a site change).
- Orion already stores disclosures (`revenue_run_rate_usd`, manual, cited) and reports them as `revenueDisclosed` with growth between consecutive disclosures; staleness anomaly `revenue_disclosure_stale` already fires.
- Gap 1: only ONE disclosure stored ($100M, 2026-08-17, founder X post). Add prior: >$70M ARR, 2026-07-01 (Series A, TechCrunch/GeekWire) — gives growth.
- Gap 2: coinrevs revenue column uses the DefiLlama proxy ($9.3M = on-chain burns). Rule: revenue = disclosed when the asset has `revenue_disclosed`; DefiLlama proxy stays as a cross-check only. Holder flow stays = burns.
- Growth on disclosures: compute from the two latest disclosures (not 90d/90d); flag when gap < 90d or latest > 90d old.

## [NO ACTION] UNI — reviewed 2026-10-12: no fix needed
- Revenue = burns ($132M/yr) = v3 selected-pool fees ($121.6M, DefiLlama) + v2 1/6 fee (~$10M, missing in DefiLlama) + Unichain sequencer (small). Label "protocol fees (v2 + selected v3)".
- Upside not revenue: v4 ($965M/yr swap fees, fee switch not on, ~$160M at 1/6) + remaining v3 pools → valuation scenario/catalyst.

## [DONE items 1-2, 2026-10-24; item 3 = proposal #3] LIT — Robinhood revenue share, revenue source, unlock cadence (reviewed 2026-10-23, from Lighter Q3 investor call)
Status: item 3 (unlock cadence) = Orion proposal #3, pending Mike's decision. Items 1-2: Mike picked 1a (holder flow Core-only + watch) and 2a (Core + 0.5 x RH first-party streams), 2026-10-23; LIVE 2026-10-24 (main ede5f4c): revenue = Core + 0.5 x RH from Lighter API, RH fee-account and buyback watches, app split watch; holder flow unchanged (Core-only).
Scoping result (2026-10-23, measured; full notes: workspace/orion/lit-scoping/robinhood-revenue.md, re-checked by Raymond):
- Robinhood instance = separate exchange, API api.rh.lighter.xyz (Robinhood Chain 4663). Its fee account (RH L2 account 0) has never traded:
  no LIT market on RH, Q3 buyback_usdc $125. It holds $3.49M USDG collateral = ~all RH fees to date (both halves), less one
  320k USDG withdrawal 2026-08-25 to an unlabelled EOA 0xac71ec13…c357. -> The RH share is NOT bought back (as of 2026-10-22).
- First-party fees: exchangeMetrics?period=all&kind=maker_fee|taker_fee|transfer_fee|withdraw_fee, daily USD, both hosts, keyless
  (Core from 2025-01-17, RH from 2026-06-26). Q3: Core $7.540M + 0.5 x RH $2.227M = $8.654M, 87.1% Core (call: $8.5M, 87%).
  Lighter's stats page applies the 0.5 in its frontend (Core + 0.5 x RH lifetime $68.20M vs $68.21M shown). DefiLlama reads the same API, RH at 100%.
- Core buys Q3 $7.46M = 99.0% of Core fees: "100% to buybacks" holds for Core only.
Source: Lighter Q3 2026 investor update video, https://x.com/Lighter_xyz/status/2113065839352336774 (posted 2026-10-22).
Transcribed locally (faster-whisper small.en); figures quoted are Vlad's.
Call figures: Q3 volume $137.67B (Robinhood instance $17.8B); revenue $8.5M, 87% Lighter Core; Robinhood is a 50/50 rev share,
">$1M" to Lighter by end Q3; take rate ~0.5bp -> ~0.6bp; "100% of trading revenue is used for buybacks"; 2.45M LIT bought+burned
in Q3, 18M+ cumulative; 109.8M LIT staked; unlocks monthly over 36 months, no cliff, first 2027-01-29.

Where Orion's numbers come from (verified 2026-10-23):
- Holder flow `flow_usd.buyback`: OUR OWN, Lighter trades API (account 0 bids on spot market 2049). Not DefiLlama.
- Revenue (`reporting.revenue` stream `trading`): DefiLlama `dailyRevenue` (`flow_usd.llama_revenue`). Report shows revenue
  $48.4M/yr, holders $32.5M, payout 67%, "protocol income" $15.9M -- that remainder is an artifact (see 2).

1. Holder flow misses the Robinhood share (finding; possible upside).
   - Orion Q3 buys $7.44M / 2.479M LIT = Core only (87% x $8.5M = $7.4M; burn 2026-10-09 2.452M).
   - DefiLlama dailyRevenue by child, monthly ($k): Perps+Spot / Robinhood Perps
     Jul 2,199 / 6; Aug 2,680 / 499; Sep 2,795 / 1,666; Oct 1-23 2,168 / 1,566. Orion buys Jul 2,098; Aug 2,573; Sep 2,765; Oct 2,213.
     -> account-0 buys track Core only. Robinhood share (50% of DefiLlama's gross) ~ $1.1M in Q3, ~$12M/yr at Oct pace.
   - Core buys per day: Q2 $82k, Q3 $81k, Oct $96k -> growth is in Robinhood, not in the measured holder flow.
   - Effect if the RH share IS bought back somewhere: holder flow +35-40% (~$32.5M -> ~$44M/yr); target ~proportional (12m ~$0.37 -> ~$0.50; spot $3.38).
   - First step (read-only): find where Lighter's RH 50% share goes -- a treasury/fee account on the Robinhood instance buying LIT,
     a different market/account on Core, a bridge to L1, or held as USDC. Check Robinhood instance API + Robinhood Chain LIT.
     Also resolves the open onboarding question "is LIT on Robinhood Chain bridged supply or separate".
   - Design if found: second holder-flow member (same buyback kind), own source; cross-check total vs Lighter's quarterly disclosure.
     If NOT bought back: note it, keep holder flow as is, and flag the gap vs "100% to buybacks" (watch it each quarter).
2. Revenue overstated: DefiLlama counts 100% of Robinhood Perps fees; Lighter keeps 50%.
   - Q3: DefiLlama $9.75M vs Lighter-disclosed $8.5M. Oct pace: DefiLlama ~$62M/yr vs ~$37M Core + ~$12M RH share.
   - Options: (a) split the stream into core (Perps+Spot) + robinhood x 0.5 (needs per-child DefiLlama breakdown);
     (b) Lighter's quarterly disclosure as a `disclosed` stream ($8.5M Q3 2026, cite the video) with DefiLlama as cross_check (VVV pattern);
     (c) own source if Lighter's API exposes fees per account (check first, per the DefiLlama rule).
   - Recommendation: (c) if available, else (a) daily + (b) disclosures as the quarterly truth.
3. Unlock cadence: `unlocks_next_year` (DefiLlama emissions) models linear weekly from 2026-12-29 (1.661M + 1.533M LIT/wk).
   Lighter: monthly tranches, first 2027-01-29. Next-365d figure today 136.0M vs ~124.6M on monthly tranches (~8% high). Report only.
   - Fix: schedule from Lighter's terms (monthly, 36 tranches from 2027-01-29) or adjust the adapter; re-check whenever DefiLlama updates.
Also noted (no action): 1.5M bought LIT routed to Coinbase Prime again on 2026-10-01 (after 1.5M in Sep); not addressed on the call.
Strategic-investor placements are secondaries from the existing cap table (no new supply).
Catalysts (dates for the analyst): vanilla options + portfolio margin by YE 2026; Lighter EVM mainnet by YE; CFTC DCM+DCO filing
Nov 2026, review up to 180 days (US instance mid-2027 at the earliest).

## [DONE 2026-10-24] LIT — Issuer states 109.8M LIT staked; Orion's staked_supply is a constant 0 (disclosure watcher, 2026-10-23, run #43, doc #1)
Built (live 2026-10-24, main ede5f4c): `staked_tokens_reported` (111.08M LIT at first read) and `staking_apr` (0.0602, watched outside 5.7-6.3%) via `lit.staking_pool`, display only; `staked_supply` stays constant 0 and the analyst sees it labelled structural. The text below is the original finding.
<!-- dw:fp=8b2b72b7d6cb88a9fbd2703cba72322887cd7f336565494a9dc9ca9a2167f99d -->
Source: https://x.com/Lighter_xyz/status/2113065839352336774 (posted 2026-10-22), machine transcript (small.en): names and numbers may be misheard; every figure in it is the speaker's dated claim, not a fact. Machine-written from the document by the analyst; verify before building.
- Category: supply; metrics: staked_supply; a fix moves targets: none
- Claim: The founder (doc:1, 2026-10-22) says 109.8M LIT is currently staked, about 11% of total supply and 44% of the 250M circulating figure.
- Orion: staked_supply = 0 (obs 25269), a config constant: the staking rewards are bought LIT passed on, not a fee share. As a result, staked_ratio and real_staking_yield read 0 in the driver report. For scale, total supply is 981,909,280 (obs 25267), so the issuer's figure is an 11.2% staked ratio.  (evidence: observation ids 25269, 25267)
- Quotes: "as of the end of Q3, 2.45 million in Q3 and also 109.8 million lit is currently staked," [11:36]
- Proposed fix: Keep the valuation treatment (the burn reaches every holder). Add a monitor-only staked LIT level from Lighter's API or staking contract, so the report shows the real staked share and the reader can size the staking-reward redistribution. Then rename the constant so the driver report does not state "staked 0" as a fact.
- Reviewed (Mike, 2026-10-23): queue it. Monitor only, never a valuation input: keep `staked_supply` = 0 (lit.yaml:58; valuing it per staker would count the redistributed buys twice).
  - Purpose: display (report + coinrevs) and a float signal: ~110M staked vs ~13.5M/month of unlocks from 2027-01-29.
  - Design: a `monitor_only` level, e.g. `staked_tokens_reported`, read daily. Source to scope first: Lighter's API or the staking contract (Lighter runs its own chain, so EVM `contract_read` may not apply); no DefiLlama unless nothing first-party exists. History starts on the go-live day (levels don't backfill).
  - Also: the driver report shows "staked 0" / real_staking_yield 0 from the constant. Label it as structural (rewards are passed-on buys) so it isn't read as a measured fact.
  - Cross-check: the issuer's 109.8M at 2026-09-30 [11:36-11:41] (doc #1), within ~2% once the series exists.
  - Scoping result (2026-10-23, measured; notes: workspace/orion/lit-scoping/staked-supply.md): staking is on the L2. Staked = LIT balance of
    pool account 281474976624800 (= /systemConfig staking_pool_index): 110.92M LIT at 2026-10-23 23:34Z (11.3% of supply). Rewards are
    6%/365 of staked daily since 2026-07-07; the 2026-09-30 reward implies 109.76M (call: 109.8M). Source: /account?by=index&value=<pool>,
    asset symbol LIT. No history endpoint (levels start at go-live).
