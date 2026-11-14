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
