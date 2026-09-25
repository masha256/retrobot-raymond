#!/usr/bin/env bash
set -euo pipefail
export JANUS_DB=/home/hermes/.hermes/profiles/raymond/workspace/janus/janus.db
D=2026-09-25
r() { out=$(janus screen record "$@" --date $D) || { echo "FAILED: $1 $out"; exit 1; }; echo "$1 $(echo "$out" | jq -c '{ok, d:.data}' | head -c 400)"; }

# ---------- CRYPTO (cluster regime +0.1) ----------
r BTC --metric score=8 --metric confidence=0.85 \
  --rationale "Sixth straight US spot ETF inflow (+190.7M USD on Sep 24, 5-session sum +2,684.3M) under a 17-day golden cross, with price +4.5%/+10.9%/+17.8% over the 20/50/200-day despite -1.0% on the snapshot. Lighter funding 0.0096%/8h is at the venue floor against a 0.0009% reference, so no long crowding."
r ETH --metric score=7 --metric confidence=0.8 \
  --rationale "Same structure as BTC without its own flow print: flat on the snapshot at +4.8%/+13.7%/+27.9% over the 20/50/200-day on a 25-day golden cross, funding 0.0096%/8h vs a 0.0067% reference. ETH-specific ETF flow unavailable and treated as neutral."
r SOL --metric score=6 --metric confidence=0.75 \
  --rationale "Trend intact and unextended: +2.6% on the snapshot, +11.5%/+23.4%/+41.0% over the 20/50/200-day on a 23-day golden cross, funding 0.0096%/8h vs a 0.0100% reference. No SOL-specific flow confirmation."
r BNB --metric score=5 --metric confidence=0.7 \
  --rationale "Healthy but undifferentiated: +3.4%/+11.3%/+22.2% over the 20/50/200-day on a 22-day golden cross, -1.0% on the snapshot, 3.1% ATR. Nothing separates it from the cluster."
r AAVE --metric score=6 --metric confidence=0.75 \
  --rationale "Clean uptrend: +2.0% on the snapshot, +10.3%/+23.0%/+49.0% over the 20/50/200-day on a 30-day golden cross, 6.7% ATR. Funding 0.0096%/8h vs a 0.0100% reference shows no crowding; OI and catalyst data unavailable, treated as neutral."
r AERO --metric score=5 --metric confidence=0.65 \
  --rationale "Up 11.7% on the snapshot to +29.0%/+51.7% over the 20/50-day, well past the late-trend line. Lighter funding 0.0680%/8h is about 7x the 0.0100% reference, a crowded-long read that offsets the momentum."
r APT --metric score=4 --metric confidence=0.65 \
  --rationale "+23.7%/+36.1% over the 20/50-day but only +9.4% over the 200-day inside a 200-day-old death cross; flat (+0.8%) on the snapshot. Extended bounce into damaged long-run structure."
r ARB --metric score=6 --metric confidence=0.65 \
  --rationale "Golden cross 11 days old is a real regime change, but +21.7%/+70.9% over the 20/50-day with an 11.1% ATR is one of the most extended entries in the book. Next unlock (Oct 16) sits outside the 14-day window."
r AVAX --metric score=4 --metric confidence=0.7 \
  --rationale "Extended bounce (+17.9%/+33.9% over the 20/50-day) inside a 200-day-old death cross, -1.1% on the snapshot. Funding 0.0096%/8h vs 0.0064% reference, neutral."
r CRV --metric score=4 --metric confidence=0.7 \
  --rationale "Fell 2.7% on the snapshot and is back 1.4% below the 20-day, so the short-term break is not repaired despite a 32-day golden cross and +8.1% over the 50-day."
r ENA --metric score=6 --metric confidence=0.6 \
  --binary-date 2026-10-05 --binary-reason "Ethena releases all remaining locked investor tokens in a single accelerated unlock on October 5, 2026." \
  --rationale "Up 14.4% on the snapshot to +41.9%/+71.2% over the 20/50-day on a 26-day golden cross, far past the late-trend line with an 8.2% ATR. The Oct 5 accelerated unlock gates new entries."
r HYPE --metric score=6 --metric confidence=0.7 \
  --binary-date 2026-10-06 --binary-reason "A projected 9.92M HYPE core-contributor unlock, roughly 4% of circulating supply, is scheduled for October 6, 2026." \
  --rationale "Mature uptrend on a 172-day golden cross at +6.2%/+18.8% over the 20/50-day, -1.9% on the snapshot. Lighter funding at the 0.0096% floor vs a slightly negative -0.0006% reference, so longs are not crowded; the Oct 6 unlock gates entries."
r JUP --metric score=5 --metric confidence=0.65 \
  --rationale "Up 4.4% on the snapshot within a 117-day golden cross, but +23.1%/+44.1% over the 20/50-day is past the late-trend line. Funding normalized to 0.0096% vs a 0.0100% reference; no catalyst data."
r LDO --metric score=6 --metric confidence=0.7 \
  --rationale "Second strong follow-through session (+6.7% after +7.2%) confirms the 50-day reclaim from 9 sessions ago, now +14.5%/+24.6% over the 20/50-day on a 35-day golden cross and still under the late-trend line. Lighter funding 0.0168%/8h vs 0.0100% reference is a mild warm-up, not crowding."
r LINEA --metric score=4 --metric confidence=0.7 \
  --rationale "Only +0.5% over the 200-day inside a 190-day death cross; +6.2%/+14.7% over the 20/50-day is a bounce within broken long-run structure."
r LINK --metric score=6 --metric confidence=0.7 \
  --rationale "Up 7.8% on the snapshot to +13.2%/+23.9%/+47.7% over the 20/50/200-day on a 30-day golden cross, 73 sessions above the 50-day and still inside the late-trend line. Funding 0.0096% vs a 0.0100% reference; move recorded as an observation, no catalyst attributed."
r LIT --metric score=5 --metric confidence=0.5 \
  --rationale "Fell 8.4% on the snapshot, cutting the 20-day cushion to +3.0% while still +137% over the 200-day with a 9.8% ATR. Funding is negative on both Lighter (-0.0320%) and the reference (-0.0203%), so shorts are paying; momentum is fading from an extreme."
r MNT --metric score=4 --metric confidence=0.7 \
  --rationale "+9.2%/+23.3% over the 20/50-day but the 50/200 death cross is 200 days old and it fell 2.3% on the snapshot. Short-term strength inside unrepaired long-run structure."
r MORPHO --metric score=6 --metric confidence=0.65 \
  --rationale "Gave back 2.1% after yesterday's surge but holds +14.2%/+18.5% over the 20/50-day on a 186-day golden cross, 8 sessions above the 50-day. Lighter funding 0.0096% vs a -0.0043% reference; no OI or catalyst data."
r NEAR --metric score=5 --metric confidence=0.65 \
  --rationale "Parabolic: +10.2% on the snapshot atop +58.1%/+114.3% over the 20/50-day with a 10.0% ATR. Funding neutral (0.0120% vs 0.0100%), but the entry is blow-off risk."
r ONDO --metric score=6 --metric confidence=0.6 \
  --rationale "Up another 5.0% to +35.5%/+45.3% over the 20/50-day on a 112-day golden cross, well past the late-trend line. Lighter funding normalized to 0.0096% vs 0.0100% reference (from ~3x yesterday); the move is unexplained and not researched."
r OP --metric score=4 --metric confidence=0.7 \
  --rationale "Up 3.8% to +24.3%/+36.9% over the 20/50-day but the death cross is 200 days old; extended bounce in broken structure. Routine Sep 30 linear unlock is anticipated and not treated as binary."
r POL --metric score=6 --metric confidence=0.65 \
  --rationale "Up 7.8% on the snapshot confirming a 10-day golden cross, +12.6%/+19.9%/+28.8% over the 20/50/200-day and still inside the late-trend line. Fresh structure; no flow or catalyst data."
r TRX --metric score=3 --metric confidence=0.8 \
  --rationale "No edge: 0.6% below the 20-day and 0.2% above the 50-day with a 1.6% ATR. Funding negative on Lighter (-0.0168%) and reference (-0.0230%) is carry, not direction."
r UNI --metric score=6 --metric confidence=0.6 \
  --rationale "Strong momentum at +26.1%/+69.2% over the 20/50-day on a 48-day golden cross, +4.0% on the snapshot, but far past the late-trend line with a 10.1% ATR. No catalyst data."
r VVV --metric score=5 --metric confidence=0.6 \
  --rationale "Flat on the snapshot at +19.2%/+59.3%/+126.0% over the 20/50/200-day with a 10.8% ATR; mature golden cross but heavily extended entry and no catalyst data."
r XLM --metric score=5 --metric confidence=0.7 \
  --rationale "Golden cross now 5 days old with +3.0% on the snapshot to +12.2%/+19.0% over the 20/50-day. Fresh turn, not yet a trend; 289 bars of history."
r ZEC --metric score=6 --metric confidence=0.6 \
  --rationale "Strongest long-run trend in the roster (+64.7% over the 50-day on a 132-day golden cross), +2.7% on the snapshot, but +180.8% over the 200-day with a 9.3% ATR is extreme extension. Funding 0.0192% vs 0.0100% reference, modestly warm."

# ---------- AI SEMIS (cluster regime -0.1) ----------
r AMD --metric score=6 --metric confidence=0.75 \
  --rationale "Secular trend intact at +16.0%/+25.1%/+46.6% over the 20/50/200-day on a 29-day golden cross, +3.1% on the snapshot. Extension is the main risk; ATR 3.6%."
r INTC --metric score=6 --metric confidence=0.75 \
  --rationale "Turnaround trend at +15.2%/+24.5%/+31.2% over the 20/50/200-day on a 29-day golden cross, +1.9% on the snapshot. Lighter funding 0.0088% vs 0.0124% reference clears yesterday's crowding flag."
r MU --metric score=6 --metric confidence=0.75 \
  --binary-date 2026-09-30 --binary-reason "Micron reports fiscal Q4 2026 results after the close on September 30, 2026." \
  --rationale "Rebounded 2.2% to +7.4%/+11.7% over the 20/50-day after two soft sessions, but the case resolves on the Sep 30 print. 200-day and 50/200 cross unavailable (145 bars), treated as neutral."
r NVDA --metric score=4 --metric confidence=0.8 \
  --rationale "No momentum: +0.7%/+0.9% over the 20/50-day and +0.4% on the snapshot despite a 104-day golden cross. Cleanest risk profile in the cluster (1.8% ATR) but no directional edge."
r SNDK --metric score=6 --metric confidence=0.7 \
  --binary-date 2026-09-30 --binary-reason "Micron's September 30 fiscal Q4 report and memory pricing guide is the sector readout that directly reprices NAND peers." \
  --rationale "Uptrend intact at +3.2%/+10.7%/+25.4% over the 20/50/200-day on a 29-day golden cross, flat on the snapshot. Lighter funding 0.0208% vs 0.0000% reference is a mild crowding flag; SanDisk's own earnings date is an unconfirmed gap."

# ---------- AI SOFTWARE (cluster regime -0.5) ----------
r PLTR --metric score=6 --metric confidence=0.75 \
  --rationale "Relative strength holding against a -0.5 software regime: +8.2%/+8.0%/+29.7% over the 20/50/200-day on a 38-day golden cross, -0.5% on the snapshot. The cluster tilt is the headwind."

# ---------- UNFILED (macro regime) ----------
r AAPL --metric score=5 --metric confidence=0.75 \
  --rationale "Steady trend with no edge: +1.8%/+5.3%/+13.5% over the 20/50/200-day on a 102-day golden cross, 1.4% ATR, flat on the snapshot. No catalyst inside 14 days."
r AMZN --metric score=5 --metric confidence=0.75 \
  --rationale "Bear lean intact but unresolved: -2.1%/-4.4% vs the 20/50-day after 19 sessions under the 50-day, yet price is back on the 200-day (+0.1%) and the 102-day golden cross has not rolled. The 200-day test is the open question."
r COIN --metric score=5 --metric confidence=0.7 \
  --rationale "Gave back 1.5% and the 20-day cushion shrank to +4.7% (+10.1% over the 50-day) despite a sixth straight BTC ETF inflow; the 105-day death cross remains the structural caveat."
r CRCL --metric score=4 --metric confidence=0.65 \
  --rationale "Fell 4.1% to lose the 20-day (-4.0%) and 200-day (-1.8%) inside a 62-day death cross, clinging to +2.3% over the 50-day with a 6.6% ATR. Bear lean forming, not confirmed; Lighter funding 0.0344% vs 0.0491% reference."
r GOOGL --metric score=5 --metric confidence=0.75 \
  --rationale "Bear case lost follow-through: +1.0% on the snapshot brings it back onto all three averages (-0.1%/-0.6%/-1.3%), though the 50/200 death cross is only 3 days old. Structure bearish, momentum absent."
r HOOD --metric score=5 --metric confidence=0.7 \
  --rationale "Second soft session (-2.0%) thins the 20-day cushion to +1.2%, still +8.7%/+28.2% over the 50/200-day on an 86-day golden cross. Real trend, fading short-term edge."
r META --metric score=6 --metric confidence=0.7 \
  --rationale "Golden cross 2 days old with +10.8%/+21.2% over the 20/50-day, but a second pullback (-2.4%) and Lighter funding 0.0224% against a 0.0013% reference flag crowded longs. Trend leader with rising positioning risk."
r MSFT --metric score=5 --metric confidence=0.75 \
  --rationale "Up 3.7% on the snapshot to reclaim the 50-day this session (+3.3%/+3.5% over the 20/50-day, +20.6% over the 200-day). The move is unexplained and recorded as an observation; one session does not make a trend."
r MSTR --metric score=4 --metric confidence=0.7 \
  --rationale "Levered BTC proxy that underperformed again (-2.4% vs BTC -1.0%) inside a 62-day death cross; +24.8% over the 50-day is an extended bounce in broken structure. Funding 0.0216% in line with 0.0220% reference."
r ORCL --metric score=6 --metric confidence=0.75 \
  --rationale "Breakdown held but did not extend: flat (-0.2%) on the snapshot at 7.5% below the 20-day and 7.3% below the 50-day, 7 sessions under the 50-day. 200-day unavailable (144 bars) and treated as neutral; reference funding 0.0250% vs Lighter 0.0032%."
r STRC --metric score=2 --metric confidence=0.8 \
  --rationale "No tradeable case: within 0.2% of the 20-day and 1.4% of the 50-day with a 0.7% ATR. The 200-day is unavailable and treated as neutral."
r TSLA --metric score=4 --metric confidence=0.7 \
  --rationale "Fell 2.3% and sits 2.7% below the 200-day inside an 89-day death cross, only +0.6%/+3.8% over the 20/50-day. The Q3 delivery report date is unconfirmed and treated as a declared gap, not a binary gate."
echo "ALL RECORDED"
