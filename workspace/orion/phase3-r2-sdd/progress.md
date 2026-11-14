# SDD ledger — plan: docs/superpowers/plans/2026-11-13-orion-phase3-r2-price-swap.md

Go: Mike 2026-11-13 #orion-dev "Go" (subagent-driven, as R1). Base 4498513 (= 8f50ac6 code + plan docs).
Baseline: build.sh orion-2026.11.12.1 at 8f50ac6 = vitest 1745/1745 (144 files), typecheck clean; no src/test change since (4498513 is docs only).
Ruling R1: no separate baseline run — 8f50ac6's release build ran the full suite on identical code 2026-11-12 — cost if wrong: a pre-existing red shows up in Task 1's full run and is attributed by stash-rerun.

## Task 1 Step 2 (controller): valid_from measured 2025-10-13T01:00Z (blocks eth 23565380, bnb 64423630, base 36763927)
All 29 EVM primary/check/feed reads answer non-zero there (price_oracle, latestRoundData, getReserves, currentCumulativePrices, slot0). File: workspace/orion/phase3-r2-scoping/valid-from-2025-10-13.json.
Ruling R2: validFrom = the first hour Orion needs, not the method's birth: every EVM token ref 2025-10-13 (flows from 2025-10-14); AERO 2026-09-23 (its oldest CoinGecko price_usd row 09-24; AERO flows are DefiLlama, not token-priced); HYPE 2026-10-01 and LIT 2026-10-01 (level rebuild M7 needs prices from their oldest price_usd rows, 10-02..); PUMP 2026-10-12 (level rows from ~10-13, burn days 10-24..). — Why: PUMP history costs ~8 Solana calls/hour; nothing reads older hours. — Cost if wrong: an older report day lacks a price; fix by lowering validFrom and re-running backfill-prices.

## Pre-flight scan
| pair / task | shared | finding | ruling |
|---|---|---|---|
| T2 -> T3 | HourPrice, PriceDeps | plan defines HourPrice in T2, PriceDeps in T3, SolanaPriceTransport in T4 but T3 consumes it | R3 |
| T3 -> T4 | writer dispatch | T3's writer must call off-chain methods T4 builds | R4 |
| T3 <-> T5 | 0008_chain_prices.sql | T3 creates file, T5 appends view; unreleased so in-place edit is fine | ok (one migration) |
| T3 <-> T5 | src/db/prices.ts | T3 upsertPrices cols, T5 basis funcs; disjoint functions | ok |
| T4 needs USDC/USD | eip155:1 feed | off-chain methods multiply by an Ethereum feed at the same hour | R5 |
| T5 view | prices PK (ref, ts, source) | two chain sources at one ts (method change later) are ambiguous | R6 |
| T1 <-> T6 | schema.ts | T1 adds share_price.underlying, T6 removes price_coingecko_id | ok, ordered |
| T1 hash | every asset pin + goldens | hash input grows -> every asset hash moves | allowed in T1 only (plan Step 4) |
| T2 <-> T6 | evm.ts | T2 moves pure decoders out of evm.ts; T6 adds price.* adapters in new price.ts | ok |
| T6 size | flow/levels/solana/adapters + 13 YAML + goldens | too big for one child | R7 |
| T7 <-> T8 | orion-remote, deploy.md, data.ts/job.ts | both add verbs to same files | serial dispatch, ok |
| T9 | docs | consumes T7/T8 verbs | ok |
| T10 | controller | allowlist bounds after Mike's sign-off | ok |
| each task self-consistency | | T1 says "17 refs" = table rows 17: ok. T2 tests use scoping values: ok. T3 migration test needs old-release fixture: existing migrate tests | ok |

Ruling R3: T2 creates src/prices/types.ts holding HourPrice, PriceDeps, SolanaPriceTransport (interface only), WriteResult; T3/T4 import from it. — cost if wrong: a rename later.
Ruling R4: T3's writer dispatches through a per-chain registry `PRICE_CHAIN_METHODS: Record<chain, (deps, entries, at, ctx) => Promise<Map<string, HourPrice>>>`; T3 registers eip155:*; T4 registers hyperliquid and solana. T3 tests an off-chain chain via a fake registry entry. — cost if wrong: small refactor.
Ruling R5: the writer prices eip155:1 first for each hour and passes its feed values (`feedUsd` map keyed by feed address lowercased) to every other chain's method for that hour; off-chain entries name the Ethereum USDC/USD feed in `usd_feed`. A chain-1 hour that failed leaves the dependent off-chain refs missing for that hour (reason `quote_missing`). — cost if wrong: HYPE/LIT/PUMP hours missing when Ethereum RPC fails; visible in WriteResult.missing.
Ruling R6: flow_usd_chain_v tie-breaks equal ts by fetched_at DESC (newest write wins); rebuild-price-levels uses the same order. — cost if wrong: a method change mid-history picks the newer method, which is the intent.
Ruling R7: Task 6 is two dispatches, one review over the range: 6a code (flow.ts, tokenBackfill, solana.ts, levels.ts, daemon.ts, price.* adapters, schema retire of price_coingecko_id with its three-place test, coingeckoHourly.ts deleted) — 6b the YAML sweep of 13 assets + every hash/golden re-pin. 6a may leave asset tests red only where a YAML still names price_coingecko_id; 6b makes the suite green. — cost if wrong: one red intermediate commit on the branch.
Ruling R8: PUMP's swap-tx history (M5) is read only from our own Solana RPC (ORION_SOL_RPC_URL); never a pump.fun host (M8). Pinned by a test in T4.
Task 1: dispatched (BASE 4498513)
Task 1: NEEDS_CONTEXT (5 values truncated in hype-lit-pump.md; work uncommitted in tree). Controller looked them up and verified on chain: task-1-values.md.
Ruling R9: pack.sh and its test must ship prices.yaml — allowed in Task 1's commit (a release without it hashes config-only) — cost if wrong: none.
Ruling R10: every stored/compared asset hash must be the combined hash (config + entriesFor); implementer greps every hash producer (loadAsset, parseAssetYaml/parseAssetObject callers, proposals approve, provenance, valuation) and makes stored paths use the combined one, with a test that a config-proposal approve and a fetch compute the same hash — cost if wrong: spurious "config" changes on every signal.
Ruling R11: entriesFor's symbol match (HYPE) is interim; Carry to Task 6: entriesFor reads refs from price.token/price.token_check params and transfer_flow tokens, symbol match deleted.
Ruling R12: departures accepted (chain 'lighter'; curve_oracle quote_ref|usd_feed; v3_spot kind; curve_get_dy dx; candle usd_feed; bound without tolerance). Brief's interface updated by these; later briefs get them.
Task 1: committed 7b75080 (continuation implementer). Controller verify: 1 commit on 4498513, 0 MISSING placeholders, tests/prices + tests/config 185/185. Reported full suite 1769/1769 (146 files), typecheck clean, py 52 OK.
Task 1: review dispatched (package review-4498513..7b75080.diff), in parallel with Task 2 implementer.
Ruling R13: Task 1 review runs in parallel with Task 2's implementer (reviewer in a detached worktree); any Task 1 fix lands as its own commit after Task 2 returns — cost if wrong: a fix that touches config.ts conflicts with Task 2's import of it (small).
Task 2: dispatched (BASE 7b75080)
Task 1: review clean (spec ✅, quality Approved; 4 named risks pass).
Task 1: minor (deferred): check method not validated against a chain (Meteora check on an Ethereum ref would load)
Task 1: minor (deferred): chain 'lighter' accepts any EVM ref, not only eip155:1
Task 1: minor (deferred): valid_from checked by pattern only (2025-13-45 loads)
Task 1: minor (deferred): Solana mint in a ref key not checked for 32 bytes
Task 1: minor (deferred): missing prices.yaml gives config-only hashes silently at a config-root override (pack.sh prevents it for releases)
Task 1: minor (deferred): check schema built with a type cast (no static typing on check fields)
Task 1: minor (deferred): no test pins that a release root, not ORION_HOME, supplies prices.yaml
Task 1: complete (commits 4498513..7b75080, review clean)
Task 2: committed 1d8e9bd; reported 1785/1785 (147 files), typecheck + lint:promises clean.
Controller check (Task 2 concerns 1-2): QUOTE_TOKENS verified on chain (decimals + symbol): ETH WETH c02a.. 18, USDC a0b8.. 6, USDT dac1.. 6; BNB USDT 55d3.. 18; Base WETH 4200..06 18, USDC 8335.. 6 — all match. Uniswap v3 observe([3600,0]) on LINK/WETH returns 8 words (offsets 64,160; len 2; tickCumulatives at words 3-4, two's complement): matches the decoder's picks 3,4; tick -52929 -> 0.005029 LINK/WETH (live).
Carry to Task 3: priceHourEvm returns {prices, feedUsd, checks, missing}; withCheck() combines an off-chain primary with its EVM check (LIT); callsFor/decode take a context. The writer passes one BlockReadCache across consecutive hours of a chain-day (B(H+1h) of hour h = B(H) of hour h+1) and prunes it to the previous hour, so a v2 chain costs 1 multicall per hour.
Task 2: review dispatched (review-7b75080..1d8e9bd.diff) with Task 3 implementer (Ruling R13 cadence).
Task 3: dispatched (BASE 1d8e9bd)
Task 2: review clean (spec ✅, quality Approved; 4 named risks pass, arithmetic recomputed independently).
Task 2: minor (deferred): usd_feed value recorded on pool rows but not its age (stale ETH/USD under VVV leaves no trace)
Task 2: minor (deferred): failed calls cached with good ones (a transient failure at one block carries into the next hour)
Task 2: minor (deferred): v4 currency order not checked against the pool (LIT check only)
Task 2: minor (deferred): BlockReadCache key omits the call signature
Task 2: minor (deferred): cache test checks multicall count only, not which block's values the older hour used
Task 2: minor (deferred): no committed tests for pool token mismatch, unknown feed, zero/negative feed, zero reserves
Task 2: minor (deferred): v3 mean tick is float, not floored (<=0.01%)
Task 2: complete (commits 7b75080..1d8e9bd, review clean)
Task 3: committed a4d49c7; reported 1809/1809 (deploy.test.ts load timeout passed alone 9/9), typecheck + lint clean, py 52. Controller: focused 6 files 83/83; 0008 has no breaking line.
Ruling R14: hour_blocks restored from prod by staging_refresh (as the implementer chose) — block-at-hour is a chain fact, identical across envs; stage only loses cache entries it can re-search — cost if wrong: a few extra getBlock calls on stage after a refresh.
Ruling R15: registry methods return {prices, missing, feedUsd?, checks?, calls?} (not a bare Map) and PriceDeps.prices / WriteResult.errors added — accepted; Task 4 follows this shape.
Task 3: minor (deferred): a backfill that later fills the hour joining two breach runs can report a second breach for one run
Task 3: minor (deferred): rpc.ts:108 comment still says ~53,556,072 (switch block is 53,556,128)
Task 3: review dispatched (review-1d8e9bd..a4d49c7.diff) with Task 4 implementer.
Task 4: dispatched (BASE a4d49c7)
Task 3: review — spec ❌ / Needs fixes: 1 Important (abort not checked inside a chain-day) + minors; findings + rulings in task-3-findings.md (fix items 1-4).
Task 3: minor (deferred): a failed chain leaves no missing entry for its refs' later hours
Task 3: minor (deferred): block-search fallback discards its bracket (extra getBlock calls)
Task 3: minor (deferred): writeChainPrices ~230 lines
Task 4: committed 27a6ff1; reported 1827/1827 (150 files), typecheck/lint/py clean.
Controller probes for Task 4 concerns 1 and 4: task-4-controller-facts.md (Lighter t = candle start, open candle must be excluded; Meteora reserves from LbPair offsets, PUMP reserve is Token-2022, live price = active bin).
Ruling R16: Task 4 departures accepted (blockSignature(slot), slotAt number|null, R15 return shape, usdAt(feed, hourMs), livePriceOffchain reads USDC/USD at the Ethereum head; PUMP signatures read on the quote vault, which every swap writes) — cost if wrong: small refactor.
Task 3: fix round 1 dispatched (findings 1-4) with Task 4 review.
Task 3: fix round 1 committed bd4feed (items 1-4); reported 1830/1830, typecheck clean. Re-review dispatched (review-27a6ff1..bd4feed.diff).
Task 3: minor (deferred): an aborted chain-day does not save the hour blocks it found (re-searched next run)
Task 4: review — spec ❌ / Needs fixes: 2 Important (Meteora reserves by owner; open candle in priceRangeOffchain) + minors; task-4-findings.md (items 1-4 fix; item 5 live facts for fixtures).
Task 4: minor (deferred): slot search 6-8 getBlockTime per hour, 15 requests per PUMP hour with its check (above ~8 estimate) — measure in Task 10
Task 4: fix round 1 dispatched (findings 1-4) with Task 3 re-review.
Task 3: fix round 1/5 (4 addressed, 0 open; commits a4d49c7..bd4feed)
Task 3: minor (deferred): a backfill writing an older breaching hour in front of an already-reported run reports it again
Task 3: minor (deferred): an abort leaves earlier chains of the same day committed and records no missing for skipped hours
Task 3: complete (commits 1d8e9bd..bd4feed, review clean after fix round 1)
Task 4: fix round 1 committed b50e94b; reported tests/prices 82/82, full 1836/1836, typecheck/lint clean. Re-review dispatched (review-bd4feed..b50e94b.diff) with Task 5 implementer.
Task 5: dispatched (BASE b50e94b)
Ruling R17: report/golden fixtures seeding prices with source 'coingecko' are re-seeded with a chain source and identical values, so goldens move only on priceBasis/source labels; any value path moving is a stop — cost if wrong: a golden hides a real value move (mitigated by the flattened path list the implementer must report).
Task 4: fix round 1/5 (5 addressed, 0 open; commits 27a6ff1..b50e94b)
Task 4: minor (deferred): a failed LbPair read is not cached (one extra request per PUMP hour while the pair account is bad)
Task 4: complete (commits a4d49c7..b50e94b, review clean after fix round 1)
Task 5: committed 7ff7562; reported 1856/1856 (150 files), typecheck/lint/py clean; golden moves: only incomeStatement.priceBasis.flows (39 entries) per implementer; priceBasis.source stays market_data:coingecko until Task 6.
Carry to Task 9: docs/ops/deploy.md:308 says compare-usd reads flow_usd_v (now flow_usd_chain_v); UsdComparison dropped beyondHourly/beyond, gained dailyMean.
Ruling R18 (amends R7): Task 6 split so each commit is green — 6a = code (flow.ts reads/ensures chain prices; tokenBackfill price part deleted; solana supply_burn_daily daily mean; levels writes recent hours + alerts; daemon sharedHttpCache removed; coingeckoHourly.ts deleted; price_coingecko_id retired from the schema with its 3-place test) PLUS the mechanical YAML edits that retirement forces (drop price_coingecko_id from 34 transfer_flow lines; share_price.underlying on yCRV's share-priced members) and their hash re-pins. 6b = price.token / price.token_check adapters, every price_usd/diem_price_usd source + cross-check + type:price check repointed, entriesFor from refs (R11), goldens. — cost if wrong: none (two reviews over one task range).
Ruling R19: a dry-run fetch computes chain prices in memory and writes no prices rows (writer gets a dryRun option returning the rows) — cost if wrong: dry runs would write prices.
Task 5: review dispatched (review-b50e94b..7ff7562.diff, 942 KB: per-file diffs) with Task 6a implementer.
Task 6a: dispatched (BASE 7ff7562)
Task 5: review clean (spec ✅, quality Approved; 17,401 golden values compared, only priceBasis.flows text moved).
Task 5: minor (deferred): 0008 daily_mean count does not check each price is hour-aligned (writer only stores aligned rows)
Task 5: minor (deferred): sumHourly field name now also covers daily_mean and usd_native days
Task 5: minor (deferred): compare-usd --json dropped beyondHourly/beyond, gained dailyMean (consumers: none found)
Task 5: minor (deferred): hours_priced/hours_needed read n/24 on days without hourly buckets (use usd_basis, not hours_needed > 0)
Carry to Task 10: tools/phase2-proof/compare.py and tools/phase3-proof/r1-allowlist.json will fail on the new priceBasis.flows text; R2 allowlist must include it.
Carry to Task 6b: priceBasis.source must move from market_data:coingecko to the chain method when price_usd sources change (goldens).
Task 5: complete (commits b50e94b..7ff7562, review clean)
Task 6a: committed 7063c22; reported 1861/1861 (150 files), typecheck/lint/py clean, sources-register current, no golden path moved, 9 asset hash re-pins. Controller: ingest+levels+prices 40 files 517/517; no CoinGecko in flow.ts/solana.ts price paths (levels.ts keeps /coins/markets for remaining coingecko sources until 6b).
Carry to Task 9: a scan with no stored prices writes every hour of its range inline (no budget) — the release block runs backfill-prices BEFORE the first nightly on the new tag; ORION_ETH_RPC_URL is required on every env (off-chain USD feeds); docs/ops mentions of the shared market_chart cache.
Task 6a: minor (deferred): prices.yaml ref check at load runs only when the prices map is non-empty (a root without prices.yaml fails later with unknown_price_ref)
Ruling R20: Task 6a is reviewed on its own now (in parallel with 6b's implementer); 6b gets its own review — cost if wrong: none.
Ruling R21: AERO keeps its own price_usd adapters (chain.v2_pool_twap_price + cl spot check) in 6b — unchanged report bytes; its prices.yaml entry serves history/level rebuild only — cost if wrong: two definitions of AERO's price (same pools).
Task 6a: review dispatched (review-7ff7562..7063c22.diff, 391 KB) with Task 6b implementer.
Task 6b: dispatched (BASE 7063c22)
Task 6a: review — spec ✅, quality Needs fixes: 1 Important (flow-scan breaches dropped) + minors; all named risks pass (value bit-equal to view in a probe).
Task 6b: committed 661bf9c; reported 1881/1881 (151 files), typecheck/lint/py clean, register current; goldens moved only priceBasis.source/sourceType (60 entries) + pack adapter_params.
Ruling R22: price_usd level cross-checks only where one existed before R2 (CAKE, LINK, LIT, PUMP, UNI, VVV); new ones on CRV/cvxCRV/HYPE/sdCRV/SKY/yCRV/DIEM removed, because cross_check_mismatch opens an anomaly (paid triage on prod) and P5 says price checks never open anomalies; LIT zero-liquidity = no reading — cost if wrong: those six assets have no fetch-time level check (their hourly writer check + WATCH still runs).
Ruling R23: fix wave for 6a+6b items in task-6-findings.md (A-G) as one commit, dispatched now with the 6b review in parallel; the 6b reviewer is told E/F are being fixed — cost if wrong: the reviewer's 6b findings may overlap the wave (merged into a second round).
Task 6a: minor (deferred): flow scan writer call has no budget or abort (a partial write shows as 'no price point')
Task 6a: minor (deferred): view accepts non-hour-aligned prices; scan lookup does not (none stored)
Task 6a: minor (deferred): no committed test of stored value == view usd
Task 6a: minor (deferred): levels tests written after the code
Task 6b: minor (deferred): consecutive:2 (cvxCRV/yCRV) does not apply at fetch time (moot after R22: no level cross-check there)
Task 6b: minor (deferred): a config parsed without prices.yaml labels LIT's price source contract_state (production always loads prices.yaml)
Task 6b: note: CAKE/LINK/UNI keep check id price_chainlink (continuity) though it now checks the pool
Carry to Task 9: docs/templates still show CoinGecko prices.
Task 6: fix wave dispatched (findings A-G) with Task 6b review (review-7063c22..661bf9c.diff).
Task 6b: review clean (spec ✅, quality Approved; live price.token == writer value on 6 EVM families; goldens moved only priceBasis.source/sourceType).
Task 6b: minor (deferred): VVV price_usd and diem_price_usd share one source id (a DIEM-only failure streak merges with VVV's)
Task 6b: minor (deferred): price.ts:104/111 comment says a failed read is retried by the next adapter (EVM block cache keeps failures)
Task 6b: minor (deferred): per-run block cache shared across chains, keyed by block number only
Task 6b: minor (deferred): off-chain observedAt is run start (ctx.nowIso)
Task 6b: minor (deferred): LIT's v4 check read at the Ethereum head, not the run block
Ruling R24: two 6b minors are fixed now, as their own first commit in Task 7's dispatch: (1) refuse a `coingecko` source with `field: price` in the schema at load/filing/approve (a proposal could otherwise bring a CoinGecko price back — the global constraint); (2) config-proposal filing (agent/tools/write.ts:306) parses with ctx.loaded.prices so a bad ref is refused at filing — cost if wrong: none.
Task 6: fix wave committed 7202a46 (A-G); reported 1887/1888 (gitPublisher load timeout, passes alone 7/7), typecheck/lint/py/register clean; hashes moved: aero (E), crv cvxcrv hype sdcrv sky vvv ycrv (F); report goldens unchanged.
Task 6: minor (deferred): FetchResult.priceBreaches not printed by the CLI fetch summary
Task 6: fix-wave re-review dispatched (review-661bf9c..7202a46.diff) with Task 7 implementer.
Task 7: dispatched (BASE 7202a46)
Task 6: fix round 1/5 (7 addressed, 0 open; commits 661bf9c..7202a46)
Task 6: minor (deferred): refresh result gains an empty undelivered: [] when there are breaches
Task 6: minor (deferred): 'no breaches on a dry run' holds only through the writer's behaviour, not enforced in flow/fetch
Task 6: minor (deferred): CLI `orion fetch`/`tick` return breaches but neither prints nor posts them (a CLI-run scan's breach is never reported)
Task 6: complete (commits 7ff7562..7202a46, review clean after fix wave)
Task 7: committed 6373b45 (R24 config fixes) + 6c0b54e (prices backfill job + remote verb); reported 1904/1904 (151 files), typecheck/lint clean, py 54 OK.
Ruling R25: Task 7 departures accepted: the CoinGecko price refusal lives in the loader (parseAssetObject, runs when prices.yaml is present), not zod (495 fixture failures otherwise); ref regex allows upper case ^[A-Za-z0-9:/._@-]{1,120}$ (base58 PUMP ref) and dates use [0-9]; op prices max_attempts 3 (lost lease re-queues; budget deferral uses none); a stopped chain fails the job with one ALERT; no per-run start line; progress kept in jobs.result_json — cost if wrong: small rework.
Carry to Task 9: docs/templates T3-T8, T10 still use `coingecko field: price` and now fail to load in a real home: replace with a price.token ref placeholder (+ templates test).
Task 7: review dispatched (review-7202a46..6c0b54e.diff) with Task 8 implementer.
Task 8: dispatched (BASE 6c0b54e)
Ruling R26: reprice scope — CoinGecko-priced-at-write rows only: (a) transfer_flow log-scan rows, (b) PUMP flow_usd.buyback rows from solana.supply_burn_daily (amount from the flow_tokens.buyback twin when missing, daily_mean); usd_native, DefiLlama (R4-R6), periodic/disclosed and manual rows are `skipped` with a reason, never `refused`; coingecko:* token refs remapped before pricing; derived rows recomputed in the same tx; export first — cost if wrong: a CoinGecko-derived row misclassified as skipped survives (the Task 10 proof counts skipped by reason).
Task 7: review — spec ✅ (with R25), quality Needs fixes: 1 Important (open-ended job vs 400-day cap) + minors; task-7-findings.md (items 1-5, rulings R27, R28).
Task 7: minor (deferred): permanently missing hours re-read every run
Task 7: minor (deferred): http_json source pointed at a CoinGecko price URL still loads (R8)
Task 7: minor (deferred): lease-gone progress-save path untested
Task 8: committed 13ece08; reported 1924/1924 (154 files), typecheck/lint clean, py 59 OK (1 skipped).
Ruling R29: PUMP DefiLlama-history rows are told apart by the adapter's own rule — a buyback row with no amount whose day starts before the first stored solana.token_supply reading is skipped as defillama_history (expected dry run ~21 repriced / ~369 skipped on prod data); coingecko:* remap covers every row of the asset; derived rows get marker basis 'derived'; per-day apply with reprice_conflict on a row changed after export — accepted — cost if wrong: the Task 10 dry run shows other counts and we stop.
Task 7: fix round 1 dispatched (findings 1-5) with Task 8 review (review-6c0b54e..13ece08.diff).
Task 7: fix round 1 committed c5e6172 (items 1-5); reported 1928/1928 (154 files), typecheck/lint clean, py 59 OK. Re-review dispatched (review-13ece08..c5e6172.diff).
Task 7: minor (deferred): a repeatedly failing chain inside budget-limited runs posts one ALERT every 10 min until the job fails
Task 8: review — spec ✅ (R26/R29), quality Needs fixes: 1 Important (stale derived rows after an interrupted --yes) + minors; task-8-findings.md (items 1-5; R30, R31).
Task 8: minor (deferred): reprice refuses a log_scan row with hourly_amounts but amount null as 'no token amounts' (none known)
Task 8: minor (deferred): CLI tests written after the code
Carry to Task 9/10: dry run must show zero coingecko:* refs other than the two remapped, and PUMP ~21 repriced / ~369 defillama_history.
Task 8: fix round 1 dispatched (findings 1-5) with Task 7 re-review.
Task 7: fix round 1/5 (5 addressed, 0 open; commits 13ece08..c5e6172)
Carry to Task 9: plan doc :303 still says lock `prices` and 20-min budget (R27/R28 replaced them: `job:prices`, 10 min, cap 550) — amend the plan text.
Task 7: complete (commits 7202a46..c5e6172, review clean after fix round 1)
Task 8: fix round 1 committed 3aca04e (items 1-5); reported 1930/1930 (154 files), py 59, typecheck/lint clean; `data reprice` exits 3 when rows are refused.
Task 8: fix-round re-review dispatched (review-c5e6172..3aca04e.diff) with Task 9 implementer.
Task 9: dispatched (BASE 3aca04e)
Task 10 (controller) started early on code-final 3aca04e: detached .worktrees/proof-3aca04e (built), old side .worktrees/rel-2026.11.12.1 (tgz sha OK); prod_copy.py running 18:58Z (copy dir in workspace/orion/phase3-proof/r2/copy-dir.txt). Price-writer driver: workspace/orion/phase3-proof/r2/r2-prices.ts (calls writeChainPrices directly; no daemon on the copy, so no watcher/analyst/Slack).
Task 10: prod copy OK (p2proof_20261114t185657z, 119,774 rows / 21 tables, sums equal). Stage A (new dist migrated 0008; old vs new BEFORE chain prices, D=2026-11-13 and 2026-08-14 + default day): zero numeric diffs on all 13 at D; only priceBasis labels/basis strings (mixed -> legacy) moved. => method gap (per-transfer vs hour-bucket on CoinGecko) = 0.
Task 10 FINDING (proof harness + product): the new home lacked prices.yaml (prod_copy copies assets/personas/skills only); Orion then silently used config-only hashes and labelled LIT's price contract_state instead of refusing. Fix wave item (Important): refuse to load an asset that names price.token/price.token_check or a usd transfer_flow when the config root has no prices.yaml; prod_copy.py copies prices.yaml into both homes when present.
Task 10: smoke day 2026-11-12 all 17 refs x 24 h written, 0 missing, 0 breaches, 96 s; calls/day eth 120, bnb 173, base 78, solana 277, hl 2, lighter 1. Chain vs CoinGecko (dev-only reference) mean gaps -0.24%..+0.49%, check gaps within tolerances.
Cost estimate re-measured (supersedes P6's ~50k): ~397 EVM days x 371 calls + ~33 PUMP days x 277 = ~156k RPC calls (BNB block search 7/h dominates), ~3.5M Alchemy CU est; ~6-7 h wall.
Task 10: full rebuild running from 19:11Z with STOP_AT 23:45Z (clear of prod nightly 00:45Z, shared Alchemy key); resume after the stage nightly (~03:30Z).
Task 8: fix round 1/5 (5 addressed, 0 open; commits 13ece08..3aca04e)
Task 8: minor (deferred): an unknown future first_party:<x> label gets the contract_state rung
Task 8: complete (commits c5e6172..3aca04e, review clean after fix round 1)
Task 9: committed 4311313 (docs); reported 1950/1950 (154 files), templates test 51/51 (RED 20 first), typecheck clean.
Task 9: note: compare-usd --days 400 reaches the first flow day only until ~2026-11-18; older days covered by the reprice dry run's refused list (release block).
Task 9: review dispatched (review-3aca04e..4311313.diff).
