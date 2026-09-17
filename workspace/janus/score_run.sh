#!/bin/bash
export JANUS_DB=/home/hermes/.hermes/profiles/raymond/workspace/janus/janus.db
T=2026-09-17
R() { janus score record "$@" --date $T; echo; }

R BTC --factor catalyst=0 --factor trend=-0.5 --factor secular=1 --factor crowding=52 --factor divergence=0 --factor capitulation=0 --factor confidence=0.85 \
 --rationale "No new BTC-specific item before the 10:00 ET cutoff; the FOMC hike and relief tape are macro beta already in the regime. Rung unchanged at below-20-day-only (-1.72%) with +6.2%/+9.0% over the 50/200-day and a 9-session golden cross intact on a +1.18% day. funding_ref 7.8e-5 sits at the neutral baseline with Lighter matched, so positioning is unstressed."

R ETH --factor catalyst=0 --factor trend=1.5 --factor secular=1.5 --factor crowding=48 --factor divergence=0 --factor capitulation=0 --factor confidence=0.85 \
 --rationale "No new ETH catalyst before the cutoff. Rung changed: reclaimed the 20-day (+0.07%) after losing it Sep 15, restoring the above-all-three-MAs rung with a 17-session golden cross and 69 straight sessions over the 50-day. funding_ref 3.8e-5 runs under the 1e-4 baseline while Lighter pays 8.0e-5, so the global crowd is not long despite the +3.11% session."

R SOL --factor catalyst=0 --factor trend=-0.5 --factor secular=1 --factor crowding=52 --factor divergence=0 --factor capitulation=0 --factor confidence=0.85 \
 --rationale "No new SOL catalyst before the cutoff. +4.47% closed most of the gap but the rung is still below-20-day-only (-0.39%), with +12.7%/+21.6% over the 50/200-day and a 15-session golden cross underneath. funding_ref 8.0e-5 at the neutral baseline matched by Lighter."

R HYPE --factor catalyst=0 --factor trend=1.5 --factor secular=1.5 --factor crowding=52 --factor divergence=0 --factor capitulation=0 --factor confidence=0.8 \
 --rationale "No new HYPE item before the cutoff; the buyback and OI-share stories are carried from prior sessions. Rung changed: +5.36% reclaimed the 20-day (+0.76%), restoring the above-all-three rung on the roster's oldest golden cross at 164 sessions, +17.0%/+48.2% over the 50/200-day. funding_ref at the 1e-4 baseline keeps crowding neutral."

R LINK --factor catalyst=0 --factor trend=-0.5 --factor secular=1 --factor crowding=47 --factor divergence=0 --factor capitulation=0 --factor confidence=0.8 \
 --rationale "No new LINK catalyst before the cutoff. +5.91% but still below the 20-day (-2.66%), so the rung is unchanged at below-20-day-only with +9.1%/+23.4% over the 50/200-day and the 50-day held 65 sessions. funding_ref 3.6e-5 under the 1e-4 baseline against Lighter's 9.6e-5 keeps crowding just below neutral."

R AAVE --factor catalyst=1 --factor trend=-0.5 --factor secular=1.5 --factor crowding=55 --factor divergence=0 --factor capitulation=0 --factor confidence=0.8 \
 --rationale "New and asset-specific: Aave Labs announced an Avalanche RWA credit hub on Aave V4 letting institutions borrow Tether's USAT against tokenized collateral (Sep 16, pre-cutoff, not in any prior rationale) - a real product expansion into a \$51B RWA market, so +1.0. Rung unchanged at below-20-day-only despite +8.94%, price now only 0.48% under the 20-day with +13.7%/+30.0% over the 50/200-day. funding_ref 7.1e-5 near baseline with a small mark premium."

R ZEC --factor catalyst=0 --factor trend=1.5 --factor secular=1.5 --factor crowding=22 --factor divergence=1 --factor capitulation=0 --factor confidence=0.75 \
 --rationale "Catalyst 0: today's +19% coverage attributes the move to the Fed decision and NU7 optimism, both already carried in prior rationales. Strongest structure on the roster, rung intact: +33.5%/+84.2%/+185.3% over the 20/50/200-day on a 124-session golden cross. funding_ref -2.12e-4 is deeply negative on a name up 14.7% today while Lighter pays +3.2e-5 - the global crowd is short into a vertical advance, the bearish-positioning-versus-rising-price divergence, though the extension is why confidence is capped."

R UNI --factor catalyst=0 --factor trend=1.5 --factor secular=1 --factor crowding=42 --factor divergence=0 --factor capitulation=0 --factor confidence=0.8 \
 --rationale "Catalyst 0: the fee-surge, buyback and Robinhood Chain narratives are all in prior rationales and monthly DEX-volume figures are cumulative prints, not events; the Sep 14 v4-hook security report was already absorbed. Largest move on the roster at +17.62%, above all three MAs (+16.9%/+50.0%/+95.8%) on a 40-session golden cross. funding_ref 6.4e-6 is far under the 1e-4 baseline through the whole move, so this is spot-led rather than leverage-led and crowding sits below neutral."

R NEAR --factor catalyst=0 --factor trend=1.5 --factor secular=1 --factor crowding=60 --factor divergence=0 --factor capitulation=0 --factor confidence=0.75 \
 --rationale "Catalyst 0: the milestone-incentive claim window was already rejected as a scheduled program mechanic in a prior session's rationale, and no new NEAR item published before the cutoff. Rung intact above all three MAs (+26.2%/+46.8%/+62.4%) on a 114-session golden cross after +15.24%. funding_ref at the 1e-4 baseline with Lighter paying 1.12e-4 above it; the 26% stretch past the 20-day is the binding entry risk."

R VVV --factor catalyst=0 --factor trend=1.5 --factor secular=1 --factor crowding=52 --factor divergence=0 --factor capitulation=0 --factor confidence=0.7 \
 --rationale "Catalyst 0 - the October emissions step-down and DIEM cap raise are scheduled forward items already in prior rationales. +10.39% holds the above-all-three rung (+21.5%/+52.3%/+97.2%) on a 194-session golden cross. funding_ref at the 1e-4 baseline keeps crowding neutral; ATR at 12.2% of price is the widest on the roster and caps confidence."

R LIT --factor catalyst=0 --factor trend=1.5 --factor secular=0 --factor crowding=45 --factor divergence=0 --factor capitulation=0 --factor confidence=0.7 \
 --rationale "No LIT-specific item found before the cutoff, so catalyst 0. Rung changed upward: +14.55% restores the above-all-three-MA rung at +13.8%/+49.3%/+160.7% on a 59-session golden cross after sitting barely over the 20-day yesterday. funding_ref 4.7e-5 under baseline against Lighter's 9.6e-5 keeps crowding below neutral; only 259 bars of history, so secular is declared neutral."

R ARB --factor catalyst=0 --factor trend=1.5 --factor secular=-0.5 --factor crowding=35 --factor divergence=1 --factor capitulation=0 --factor confidence=0.75 \
 --rationale "Catalyst 0: the ~92.6M Sep 16 unlock was the screen binary and sits in prior rationales, and it is now past. Above all three MAs (+16.1%/+53.7%/+60.2%) with the golden cross only 3 sessions old - the freshest structural turn in the cluster. funding_ref -7.4e-5 is negative while Lighter pays +6.4e-5 and price is +4.15%: global shorts offside into a rising chart, a bullish divergence; vesting through Mar 2027 is the structural drag in secular."

R POL --factor catalyst=0 --factor trend=1.5 --factor secular=0 --factor crowding=52 --factor divergence=0 --factor capitulation=0 --factor confidence=0.8 \
 --rationale "No POL-specific item before the cutoff. +7.22% above all three MAs (+2.41%/+9.95%/+11.62%) with a golden cross just 2 sessions old - a genuine structural turn with only two sessions of confirmation. funding_ref at the 1e-4 baseline matched by Lighter, crowding neutral."

R ONDO --factor catalyst=1 --factor trend=1.5 --factor secular=1.5 --factor crowding=55 --factor divergence=0 --factor capitulation=0 --factor confidence=0.8 \
 --rationale "New and asset-specific: Ondo's broker-dealer subsidiary Oasis Pro Markets became the first tokenization firm admitted to DTCC's Fund/SERV, the rail carrying 85%+ of US mutual fund transaction activity (Sep 16 12:33 ET, pre-cutoff, absent from prior rationales) - real distribution infrastructure, so +1.0. Rung changed: +14.42% reclaimed the 50-day at age 0, restoring the above-all-three rung (+5.5%/+5.0%/+14.3%) inside a 104-session golden cross. funding_ref at the 1e-4 baseline."

R AERO --factor catalyst=0 --factor trend=1.5 --factor secular=1 --factor crowding=52 --factor divergence=0 --factor capitulation=0 --factor confidence=0.75 \
 --rationale "Catalyst 0 - the Velodrome merger, buyback and TENOR collateral items are all prior-session stories with no new AERO-specific print before the cutoff. +13.25% holds the above-all-three rung (+10.7%/+23.9%/+38.1%) on an 88-session golden cross. funding_ref at the 1e-4 baseline with a fractional mark premium, so trend without crowding."

R NVDA --factor catalyst=0.5 --factor trend=-0.5 --factor secular=2 --factor crowding=48 --factor divergence=0 --factor capitulation=0 --factor confidence=0.85 \
 --rationale "New but minor: NVIDIA published Vera Rubin NVL72 MLPerf Inference v6.1 debut results and an AI-data-center energy alliance with Emerald AI and Google (nvidianews, Sep 16, pre-cutoff) - vendor-published benchmark and partnership news, largely expected, so +0.5. Rung changed: +1.42% reclaimed the 50-day (+0.21%) after four sessions beneath it, but price is still 1.04% under the 20-day so the rung is below-20-day-only. funding_ref 5.0e-5 under baseline with a negligible mark premium keeps crowding just under neutral."

R AMD --factor catalyst=0 --factor trend=1.5 --factor secular=1.5 --factor crowding=50 --factor divergence=0 --factor capitulation=0 --factor confidence=0.85 \
 --rationale "Catalyst 0: no new AMD-specific item published before the cutoff, and the sector AI-doomer rebuttal is carried from prior sessions. Cluster leader with the rung intact: +1.91% above all three MAs (+9.6%/+10.6%/+29.7%) on a 21-session golden cross. funding_ref 2.5e-5 under the equity baseline with a small mark premium, so crowding is neutral at reduced confidence on thin equity perp funding."

R INTC --factor catalyst=1.5 --factor trend=1.5 --factor secular=1.5 --factor crowding=58 --factor divergence=0 --factor capitulation=0 --factor confidence=0.8 \
 --rationale "New, cluster-moving and not in any prior rationale: Reuters reported Sep 16 that SK Hynix is in talks with Intel to manufacture memory chips in the US for the first time, lifting both names and validating Intel Foundry's external-customer thesis, so +1.5. Largest equity move on the roster at +7.07%, rung intact above all three MAs (+12.7%/+13.7%/+18.9%) on a 21-session golden cross. funding_ref 8.5e-5 near baseline but Lighter pays 1.76e-4, roughly double - local longs are the crowded side."

R MU --factor catalyst=0.5 --factor trend=1 --factor secular=2 --factor crowding=50 --factor divergence=0 --factor capitulation=0 --factor confidence=0.7 \
 --rationale "Minor and partly priced: Micron's announcement of the first 512GB DDR5 module surfaced in Sep 16 pre-cutoff coverage - a real first-mover product print but incremental against the existing shortage thesis, so +0.5. Trend is the above-20-and-50 rung (+1.05%/+4.50%) only: with 137 bars of history there is no 200-day and no 50/200 cross, and that input is declared neutral rather than estimated. Declared gap: funding_ref 5.5e-6 is effectively zero on a thin equity perp, so crowding falls back to neutral on a small mark premium alone; Sep 30 earnings is the binary."

R SNDK --factor catalyst=0 --factor trend=-0.5 --factor secular=2 --factor crowding=52 --factor divergence=0 --factor capitulation=0 --factor confidence=0.75 \
 --rationale "Catalyst 0: the memory-shortage reporting is cluster-level and already carried in the cluster regime, with no SNDK-specific print before the cutoff. +5.14% still leaves price 0.82% under the 20-day, so the rung stays below-20-day-only with +6.3%/+18.5% over the 50/200-day and a 21-session golden cross. Declared gap: funding_ref is 0 on the equity perp, so crowding leans on a small mark premium and OI alone and sits a shade above neutral."

R GOOGL --factor catalyst=0 --factor trend=1.5 --factor secular=1.5 --factor crowding=55 --factor divergence=0 --factor capitulation=0 --factor confidence=0.8 \
 --rationale "No new GOOGL-specific item before the cutoff, so catalyst 0. Rung changed: +0.45% reclaimed the 50-day at age 0, putting price above all three MAs with a 6-session golden cross - but at only +0.63% over the 200-day the three MAs are compressed inside 2% and the structure has no cushion. funding_ref 2.7e-5 with Lighter paying 1.68e-4, a 6x local-versus-global gap that tilts crowding above neutral."

R AAPL --factor catalyst=0 --factor trend=1.5 --factor secular=1 --factor crowding=48 --factor divergence=0 --factor capitulation=0 --factor confidence=0.75 \
 --rationale "Catalyst 0: the Siri AI ship is carried from a prior session and no new Apple item published before the cutoff. Rung unchanged above all three MAs (+2.27%/+5.24%/+13.14%) on a 94-session golden cross, flat at -0.05% on the day with the lowest ATR of any equity on the roster at 1.65%. Declared gap: funding_ref is 0 and mark sits fractionally under index, so crowding leans on premium alone and stays just below neutral at reduced confidence."

R PLTR --factor catalyst=0 --factor trend=1.5 --factor secular=1 --factor crowding=47 --factor divergence=0 --factor capitulation=0 --factor confidence=0.75 \
 --rationale "No new PLTR-specific item before the cutoff; the France/Palantir story is a prior-session item. Rung intact above all three MAs (+1.45%/+4.62%/+21.55%) on a 30-session golden cross after +3.41%, outperforming a cluster whose regime is the weakest of the three. Declared gap: funding_ref is 0 on the equity perp and mark sits under index, so crowding leans on premium alone and sits just below neutral."
