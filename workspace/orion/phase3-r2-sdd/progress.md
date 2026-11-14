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
