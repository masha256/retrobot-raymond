# Orion dev queue — revenue definitions

Open items only. Built or closed items move to dev-queue-revenue-archive.md (same folder).

Status 2026-10-24: LIT unlock cadence (proposal #3) applied live (main 4287b32). Open items below.

## [OPEN] Orion `loadEnv`: an empty process variable overrides `.env` (found 2026-10-23)
- `src/cli/env.ts` `loadEnv` returns `{ ...fromFile, ...processEnv }`, so `ANTHROPIC_API_KEY=""` in the process env (the
  Hermes agent terminal exports it empty) beats the real key in `<ORION_HOME>/.env`; a hand-run `orion agent run` then fails
  `no_credentials` ($0). Cron is unaffected (wrappers source `.env` with `set -a`).
- Fix: skip process values that are empty or whitespace when merging (`.env` wins over an empty variable); test both orders.

## [OPEN] Agent budget counts cache reads at full weight (found 2026-10-24, AERO deep run #44)
- `src/config/agentPolicy.ts`: `inputTokens` = uncached + cache reads + cache writes, summed over requests, checked against
  one cap (deep default 2_000_000). Each request re-reads the whole context, so a long-context run hits the cap in a few
  requests even though cache reads cost ~10% of uncached input.
- Run #44 (aero, deep, 2026-10-24): 5 requests, 172,555 uncached + 2,098,816 cache read + 177,334 cache write = 2.45M vs the
  2M cap -> `budget_exhausted`, staged change discarded (base rev_growth_y1 0.30 -> 0.25, 12m $0.486 -> $0.475). Context was
  ~690k chars (11 web searches at ~22k chars each, an 84k GitHub PR fetch, a 63k DefiLlama API fetch). Estimated ~$3-4.
- Proposed design: a price-weighted budget (`input_cost_units` = uncached x1 + cache_write x1.25 + cache_read x0.1, or a
  USD cap from a per-model price table) replacing or alongside the raw token cap; keep `requests` and output caps.
  Recalibrate the per-run-type defaults so existing runs keep similar headroom on uncached input. Must leave every asset's
  config hash unchanged if the default is a pure re-weighting (or accept re-pins and say so).
- Related option: on budget exhaustion, allow one final commit-only request so staged changes aren't lost.

## [OPEN] LIT fee series: revision check (from the Lighter-API rollout, 2026-10-24)
- Diff the stored `flow_usd.fees_core` / `flow_usd.fees_rh` rows for 2026-10-17..10-23 against
  `workspace/orion/lit-scoping/revision-baseline-2026-10-24T0112Z.csv` after the next LIT tick (it re-reads 7 days).
  Record restated days in `docs/superpowers/notes/2026-10-23-lit-lighter-api-followups.md`; if Lighter restates beyond
  7 days, raise `days` for those metrics.

## [OPEN] Deferred minors from the 2026-10-23/24 builds (none blocks; triaged by the final reviews)
- Disclosure watcher: `docs/superpowers/notes/2026-10-23-disclosure-watcher-followups.md` (Deferred minors).
- Lighter API (the build ledger was removed with its worktree; the list is here):
  - `lit.app_fee_share` has no validateParams (a mistyped key is ignored).
  - `lit.staking_pool` reads only the explorer's first log page and does not dedupe by tx hash (fails safe: 2-day freshness).
  - `lit.exchange_fees_daily` with `days: 1` and an unclosed newest day refuses instead of holding back (LIT uses 7).
  - `src/db/fetchRuns.ts` imports the `WatchFiring` type from `src/ingest` (layering only).
  - Tests: non-numeric-data test asserts only `/maker_fee/`; HTTP spacing test checks config values only; duplicate
    `messageOf` helpers; `withShare` depends on `replace()` order; watch rule count relies on zod omitting absent keys;
    `trigger_firings` count around `fetchAsset` proves little (assert in the tick test); "absent when empty" watch test
    reuses one instant; core stream `share` absence not asserted with `in`; new LIT metrics' type/unit not asserted;
    the LIT report test uses `loadHolderYieldReport`, not the CLI JSON; context test applies LIT notes to the mini asset.
- Build them as one cleanup batch when convenient.
