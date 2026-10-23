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
- DefiLlama revises history (HYPE: Orion $149M vs $178.5M latest 90d. AERO correction 2026-10-12: its apparent $17.1M→$24.9M "revision" was the known 2026-09-10 DefiLlama artifact ($7.92M day), not a revision — manual row re-applied after the prod backfill). Re-pull the last N days (e.g. 30) each run and supersede changed rows.

## VVV — use disclosed business revenue (reviewed 2026-10-12)
- Orion already stores disclosures (`revenue_run_rate_usd`, manual, cited) and reports them as `revenueDisclosed` with growth between consecutive disclosures; staleness anomaly `revenue_disclosure_stale` already fires.
- Gap 1: only ONE disclosure stored ($100M, 2026-08-17, founder X post). Add prior: >$70M ARR, 2026-07-01 (Series A, TechCrunch/GeekWire) — gives growth.
- Gap 2: coinrevs revenue column uses the DefiLlama proxy ($9.3M = on-chain burns). Rule: revenue = disclosed when the asset has `revenue_disclosed`; DefiLlama proxy stays as a cross-check only. Holder flow stays = burns.
- Growth on disclosures: compute from the two latest disclosures (not 90d/90d); flag when gap < 90d or latest > 90d old.

## UNI — reviewed 2026-10-12: no fix needed
- Revenue = burns ($132M/yr) = v3 selected-pool fees ($121.6M, DefiLlama) + v2 1/6 fee (~$10M, missing in DefiLlama) + Unichain sequencer (small). Label "protocol fees (v2 + selected v3)".
- Upside not revenue: v4 ($965M/yr swap fees, fee switch not on, ~$160M at 1/6) + remaining v3 pools → valuation scenario/catalyst.

## LIT — Robinhood revenue share, revenue source, unlock cadence (reviewed 2026-10-23, from Lighter Q3 investor call)
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
