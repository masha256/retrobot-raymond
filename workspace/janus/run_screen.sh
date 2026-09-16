#!/usr/bin/env bash
set -euo pipefail
export JANUS_DB=/home/hermes/.hermes/profiles/raymond/workspace/janus/janus.db
D=2026-09-16
r() { janus screen record "$@" --date $D || { echo "FAILED: $1"; exit 1; }; }

# ---------- CRYPTO (cluster regime -1.3) ----------
r ZEC --metric score=8 --metric confidence=0.85 \
  --rationale "Strongest trend in the book: +11.75% today, +21.2% vs 20-day, +66.1% vs 50-day, +153.6% vs 200-day with golden cross 123 sessions old. Funding 0.000096 matches the 0.0001 reference, so the move is spot-led rather than a crowded perp bid; 10.5% ATR makes it extended, not broken."
r ARB --metric score=7 --metric confidence=0.8 \
  --binary-date 2026-09-16 --binary-reason "Scheduled vesting unlock of roughly 92.6M ARB releasing to investors, team and DAO treasury." \
  --rationale "+6.88% today with a golden cross only 2 sessions old and +16.95%/+52.86%/+57.10% vs the 20/50/200-day - the cleanest fresh trend inflection in crypto. Today's unlock is the offset and gates new entries."
r NEAR --metric score=7 --metric confidence=0.8 \
  --rationale "+3.79% into a risk-off crypto tape, above all three MAs (+12.19%/+28.90%/+41.31%) with golden cross 113 sessions old. Funding 0.0001 in line with reference; no known catalyst, so this is pure relative strength."
r APT --metric score=6 --metric confidence=0.85 \
  --rationale "Cleanest bear structure in the roster: death cross 200 sessions, -9.60%/-8.62%/-31.46% vs the 20/50/200-day, -7.40% today and lost the 50-day yesterday. Funding negative at -0.000176 vs -0.000155 reference confirms short-side positioning rather than contradicting it."
r VVV --metric score=6 --metric confidence=0.75 \
  --rationale "Holds +11.94%/+39.18%/+78.61% vs the 20/50/200-day despite -2.12% today. 13.0% ATR is the widest in the book, so the trend is real but the entry is poor."
r LIT --metric score=6 --metric confidence=0.75 \
  --rationale "+1.10% on a red crypto day and still +32.03%/+128.55% vs the 50/200-day, though only +0.84% vs the 20-day - momentum is intact but flattening. Funding 0.000096 runs above the -0.000036 reference, a mild crowding tell."
r ENA --metric score=5 --metric confidence=0.75 \
  --rationale "Essentially flat (-0.20%) while the complex sold off, holding +16.13%/+39.54% vs the 50/200-day but -6.68% below the 20-day. Structurally strong, tactically mid-range."
r HYPE --metric score=5 --metric confidence=0.75 \
  --rationale "+1.46% against a red tape with +11.55%/+40.87% vs the 50/200-day, but -4.58% below the 20-day keeps it a pullback rather than a breakout. Funding 0.0001 matches reference."
r UNI --metric score=5 --metric confidence=0.75 \
  --rationale "-4.57% today drops it to -0.50% vs the 20-day, but it still holds +26.09%/+62.84% vs the 50/200-day. Funding 0.000096 vs a -0.000052 reference is the one crowding flag."
r BNB --metric score=5 --metric confidence=0.8 \
  --rationale "Most resilient major: only -0.93% below its 20-day versus -3.01% for BTC and -2.93% for ETH, holding +7.40%/+13.36% vs the 50/200-day with the 50-day reclaimed 45 sessions ago. Funding slightly negative at -0.000016."
r OP --metric score=5 --metric confidence=0.8 \
  --rationale "-7.99% today and lost the 50-day at age 0, with death cross 200 sessions and -15.36% vs the 200-day. Funding stays positive at 0.0001, so longs have not capitulated - a live bear case."
r XLM --metric score=5 --metric confidence=0.8 \
  --rationale "-9.36% today, lost the 50-day at age 0, with a fresh death cross only 6 sessions old and all three MA distances negative. Funding 0.0001 versus a -0.000095 reference shows longs still paying into the breakdown."
r BTC --metric score=4 --metric confidence=0.85 \
  --rationale "-1.00% and -3.01% below the 20-day, but longer structure holds at +5.29%/+7.71% vs the 50/200-day with golden cross 8 sessions old. Funding 0.000096 vs 0.000069 reference is neutral - a trend break inside an intact uptrend, no discrete edge."
r ETH --metric score=4 --metric confidence=0.85 \
  --rationale "-1.36%, -2.93% below the 20-day but +7.79%/+15.74% vs the 50/200-day and above the 50-day for 68 sessions. Funding near zero at 0.000024; consolidation, not a setup."
r SOL --metric score=4 --metric confidence=0.8 \
  --rationale "-2.32% and -4.76% below the 20-day, still +8.54%/+16.43% vs the 50/200-day with golden cross 14 sessions old. Funding 0.000024 basically flat - same inert-major profile as BTC/ETH."
r AAVE --metric score=4 --metric confidence=0.8 \
  --rationale "-6.85% today pushes it to -7.97% vs the 20-day while holding +5.50%/+19.95% vs the 50/200-day. Funding 0.000096 against a -0.000053 reference means Lighter longs are paying into a flush."
r CRV --metric score=4 --metric confidence=0.8 \
  --rationale "-10.57% today, -11.31% vs the 20-day, but still +4.91%/+26.87% above the 50/200-day with golden cross 23 sessions old. Funding negative on both venues; a sharp flush without a structural break."
r LINK --metric score=4 --metric confidence=0.8 \
  --rationale "-5.24% today, -8.06% vs the 20-day, holding +3.55%/+16.60% vs the 50/200-day after 64 sessions above the 50-day. Funding flat at 0.000024 - no edge either way."
r MORPHO --metric score=4 --metric confidence=0.75 \
  --rationale "-12.43% vs the 20-day and -6.33% vs the 50-day, below the 50-day 3 sessions, with only +5.28% vs the 200-day left as cushion. Deteriorating but not yet a confirmed downtrend."
r LDO --metric score=4 --metric confidence=0.75 \
  --rationale "-6.76% today, lost the 50-day at age 1, sitting -11.34%/-4.00% vs the 20/50-day with the 200-day distance now flat at -0.10%. Golden cross 26 sessions old is at risk of reversing."
r AERO --metric score=4 --metric confidence=0.75 \
  --rationale "-3.53% to -2.09% below the 20-day but still +9.19%/+21.07% vs the 50/200-day with golden cross 87 sessions old. 9.2% ATR and no catalyst; middling."
r POL --metric score=4 --metric confidence=0.75 \
  --rationale "Golden cross just triggered at age 1, but -5.52% today and -4.42% below the 20-day undercuts it; only +3.63%/+4.46% vs the 50/200-day. Fresh signal with weak confirmation."
r AVAX --metric score=3 --metric confidence=0.8 \
  --rationale "Death cross 200 sessions and -9.20% vs the 200-day, though it holds +3.25% vs the 50-day after -2.37% today. Funding slightly negative at -0.000048; conflicted structure, no clean side."
r ONDO --metric score=3 --metric confidence=0.8 \
  --rationale "Below both the 20- and 50-day (-6.35%/-7.31%) with only +1.16% vs the 200-day left, and lost the 50-day 7 sessions ago. Weak drift rather than a tradeable break."
r JUP --metric score=3 --metric confidence=0.75 \
  --rationale "-7.12% today to -7.69% vs the 20-day, leaving only +3.10% vs the 50-day of cushion. Funding 0.000096 against a -0.000107 reference is the only notable divergence."
r MNT --metric score=3 --metric confidence=0.7 \
  --rationale "Flat at +0.17% but caught between +10.72% vs the 50-day and -4.39% vs the 200-day with death cross 199 sessions. No direction; thin 19.7k volume limits read quality."
r LINEA --metric score=3 --metric confidence=0.7 \
  --rationale "-3.66% today, -5.27% vs the 20-day, marginally +1.60% vs the 50-day and -15.07% vs the 200-day under a 181-session death cross. Weak-side drift, no catalyst known."
r TRX --metric score=2 --metric confidence=0.85 \
  --rationale "Inert: -0.32% today with all three MA distances inside +/-2.3% and a 1.4% ATR, the tightest in the roster. Funding -0.00016 is the only movement; nothing to trade."

# ---------- AI / SEMIS (cluster regime -1.0) ----------
r AMD --metric score=7 --metric confidence=0.85 \
  --rationale "Cluster leader: +3.59% today, above all three MAs at +7.32%/+7.99%/+26.62% with golden cross 20 sessions old and the 50-day reclaimed 8 sessions ago. Semis outperformance is the one constructive cluster signal today."
r INTC --metric score=6 --metric confidence=0.8 \
  --rationale "+3.59% and above all three MAs (+5.53%/+5.95%/+10.53%) with a 20-session-old golden cross. Funding 0.00037 vs a 0.00004 reference is elevated, a mild crowding caution."
r SNDK --metric score=5 --metric confidence=0.8 \
  --rationale "Holds +2.36%/+13.53% vs the 50/200-day under a 20-session golden cross but sits -4.91% below the 20-day after a flat +0.25% session. Constructive base, no trigger."
r MU --metric score=5 --metric confidence=0.6 \
  --binary-date 2026-09-30 --binary-reason "Micron reports fiscal fourth quarter results after the close on September 30, 2026." \
  --rationale "Reclaimed and then lost the 50-day (below, age 1) at -0.28%, -3.82% vs the 20-day, and 200-day context is unavailable at 136 bars - declared gap, treated as neutral. Earnings in 14 days gate any new entry."
r NVDA --metric score=4 --metric confidence=0.85 \
  --rationale "+1.49% but still below both the 20- and 50-day (-2.71%/-1.26%), below the 50-day 3 sessions, with +5.69% vs the 200-day the only cushion. The heaviest cluster name is the laggard, which caps the semis case."

# ---------- AI / SOFTWARE (cluster regime -1.2) ----------
r META --metric score=7 --metric confidence=0.85 \
  --rationale "+1.72% and extended above all three MAs at +9.60%/+14.91%/+11.95%, the strongest name in a cluster that underperformed today. The 93-session death cross is stale and contradicted by price."
r AAPL --metric score=6 --metric confidence=0.85 \
  --rationale "+1.33% with price above all three MAs (+2.85%/+5.59%/+13.71%), golden cross 93 sessions old and the 50-day held 15 sessions. Quiet, durable uptrend against a soft software cluster."
r AMZN --metric score=5 --metric confidence=0.85 \
  --rationale "-0.88% and below both the 20- and 50-day (-3.80%/-5.69%) for 10 sessions, with only +0.47% vs the 200-day left as support. Clearest downside structure in the cluster."
r ORCL --metric score=5 --metric confidence=0.7 \
  --rationale "-5.65%/-2.44% vs the 20/50-day and below the 50-day 2 sessions after post-earnings damage; 200-day context unavailable at 135 bars, declared as a gap and treated as neutral. Earnings already passed on September 10, so no binary."
r MSFT --metric score=4 --metric confidence=0.85 \
  --rationale "-1.51% today, -1.38% below the 20-day but still marginally above the 50-day (+0.49%, held 51 sessions) and +17.06% vs the 200-day. Balanced - no discrete case."
r PLTR --metric score=4 --metric confidence=0.8 \
  --rationale "-1.41% and -1.99% below the 20-day, having just reclaimed the 50-day 2 sessions ago (+1.90%) with +17.74% vs the 200-day. Marginal signal, easily invalidated."
r TSLA --metric score=4 --metric confidence=0.8 \
  --rationale "+0.72% with price above the 20- and 50-day (+1.12%/+5.48%) but -4.19% below the 200-day under an 80-session death cross. Short-term strength fighting long-term damage."
r GOOGL --metric score=3 --metric confidence=0.8 \
  --rationale "+0.58% but whipsawing: golden cross 5 sessions old while price lost the 50-day at age 1, sitting +1.63%/-0.09%/+0.19% vs the 20/50/200-day. Pure chop."

# ---------- CRYPTO-ADJACENT EQUITY (no cluster; macro regime -1.1) ----------
r CRCL --metric score=6 --metric confidence=0.85 \
  --rationale "-10.35% today, lost the 50-day at age 0, -13.44% vs the 20-day and -10.98% vs the 200-day under a 53-session death cross. Funding 0.00258 against a 0.00031 reference is a roughly 8x dislocation, the most extreme in the roster."
r COIN --metric score=5 --metric confidence=0.85 \
  --rationale "-7.13% today to -6.02% vs the 20-day, clinging to +0.51% vs the 50-day with -4.30% vs the 200-day under a 96-session death cross. Crypto-equity complex underperformance is a live crypto-cluster signal."
r MSTR --metric score=4 --metric confidence=0.8 \
  --rationale "-3.83% today, -4.32% vs the 20-day, still +10.14% vs the 50-day but -1.69% vs the 200-day under a 53-session death cross. Funding 0.000248 vs 0.000167 reference; conflicted."
r HOOD --metric score=4 --metric confidence=0.8 \
  --rationale "-5.87% today to -6.33% below the 20-day, holding +2.59%/+17.34% vs the 50/200-day under a 77-session golden cross. Pullback inside an uptrend, no trigger."
r STRC --metric score=2 --metric confidence=0.7 \
  --rationale "-0.33% with a 0.8% ATR and price within 0.1% of its 20-day; 200-day context unavailable at 182 bars, declared as a gap. Functionally a yield instrument, not a trade."

echo "ALL RECORDED"
