---
name: orion
description: Use when operating, debugging, or developing orion.
---

# Orion operations and development

This skill covers Mike's orion valuation pipeline (VVV/HYPE/AERO; CRV in progress): diagnosing ingest failures, vetting or swapping data endpoints and API keys, running the test suite, and scoping/onboarding new assets. Mike manages orion development from the Raymond bot's orion-dev topic.

## Development: tests and branches
- Run `npx vitest run --maxWorkers=2` then `npm run typecheck`. Plain `npm test` on this 4-core host times out the CLI tests (`tests/cli/{cli,ingest.cli,tick.cli}.test.ts` spawn subprocesses; 5s/10s timeouts) under full parallelism; rerun those files alone before calling any failure real.
- Report the counts (files/tests passed) from the real run, not an assertion.
- Feature work follows the repo's own pattern: branch `feat/<asset>`, a spec in `docs/superpowers/specs/<date>-orion-<topic>-design.md`, then a plan in `docs/superpowers/plans/`, then implementation, then a followups note in `docs/superpowers/notes/`. Read the latest onboarding spec+followups (AERO, HYPE) before drafting a new one; they carry the conventions (mirror-rule bands, backfill > window, hash pins, the 5 user checkpoints).
- Leave unrelated working-tree changes (e.g. an npm-touched `package-lock.json`) uncommitted and mention them; don't sweep them into feature commits.
- Adding a new asset: follow `references/asset-onboarding.md`.

Repo: `/home/hermes/git/orion`. Live DB: `orion.db` in the repo root (sqlite). Secrets: `orion/.env` (gitignored, mode 600). It is sourced by the profile's `scripts/orion-tick.sh` and also read by orion itself via `loadEnv`. Cron jobs and delivery are covered in memory; use the `cron-job-administration` skill for any schedule changes.

## External dependencies (what each asset hits)
- **VVV, AERO**: Base mainnet RPC (chain 8453). The env var is named by `ingest.rpc_url_env` in `assets/<asset>.yaml` (currently `ORION_BASE_RPC_URL`). When it is unset, orion falls back to `https://mainnet.base.org` (`DEFAULT_RPC_URLS` in `src/ingest/run.ts`). They also use CoinGecko, DefiLlama and `http_json` cross-checks.
- **Ethereum mainnet (chain 1)**: `ORION_ETH_RPC_URL` in `.env` holds Mike's Alchemy key (passes 100k-block `eth_getLogs` with `blockTimestamp`, and archive `eth_call`). Free mainnet RPCs (drpc, publicnode) refuse ranged logs beyond ~10k blocks and archive reads, so never default chain 1 to a keyless URL. The transport (`viemRpc.ts`) only accepts Base until the CRV branch adds chain 1.
- **HYPE**: no RPC. It uses `api.hyperliquid.xyz/info` (REST), CoinGecko and DefiLlama.
- **CoinGecko**: the optional `COINGECKO_API_KEY` is sent as the demo-key header. Without it, the code spaces requests 2.5s apart to stay under the keyless limit.
- To re-derive this list: `grep -n '^ingest:' assets/*.yaml` and `grep -rn 'env\.\|https://' src/ingest`.

## Diagnosing ingest failures
The cron output .md files rarely contain the real error. Query `fetch_runs` instead. Its columns are `id, asset_id, started_at, ended_at, outcome, detail_json`; outcome is `ok` or `partial`. Per-source errors live in `detail_json.sources[]`:
```
sqlite3 orion.db "select f.asset_id,f.started_at,json_extract(s.value,'$.sourceId'),substr(json_extract(s.value,'$.error'),1,250) from fetch_runs f, json_each(f.detail_json,'$.sources') s where json_extract(s.value,'$.status')!='ok' order by f.id desc limit 20;"
```
- "RPC Request failed." on `chain_levels`, on `adapter:*` `totalSupply()`, or on `transfer_flow` `eth_getLogs` means the Base RPC was throttled or rejected the request. Errors are deliberately scrubbed: viem's `shortMessage` is used and URLs are cut to their origin. To see the provider's actual message, curl the endpoint directly.

## Vetting a new RPC endpoint (before relying on it)
Orion's Base RPC must support all of the following. Test every item. A provider that passes the reads can still fail the logs check.
1. `eth_blockNumber` and `eth_getBlockByNumber` (historical): used for the block-by-time search.
2. `eth_call` at a specific block through Multicall3. All reads go out as one batched call.
3. **`eth_getLogs` over a 2,000-block range** (`MAX_LOG_RANGE` in `src/ingest/transport/rpc.ts`). Free tiers often cap this hard; Alchemy Free allows only **10 blocks** and returns `-32600 "Under the Free tier plan..."`. Viem surfaces that as the misleading "JSON is not a valid request object." Probe the range with raw curl at spans 10, 11, 500 and 2000 to find the cap.
4. **`blockTimestamp` on every log**. This field is non-standard, and orion throws when it is missing. Check with a small-range `eth_getLogs` on the VVV token's Transfer topic. Burns to the zero address are sparse, so use plain transfers rather than burns as the sample.

Procedure:
- Append the URL to `.env` (it is gitignored). Then run a throwaway `.mjs` probe that imports the built transport, `dist/ingest/transport/viemRpc.js` (`createViemRpc`) and `rpc.js` (`getLogsChunked`). That exercises the exact code path the cron jobs use. Include the historical range that last failed in `fetch_runs`, plus one full day of back-to-back chunks (~22 for Base).
- Pipe every output through `sed -E 's#/v2/[A-Za-z0-9_-]+#/v2/***#g'` (or an equivalent for the provider's path), because keyed URLs must not land in logs or chat. Delete the probe file afterwards.
- If any check fails, **comment the line out** in `.env` with a one-line reason and the fix (for example, "uncomment after PAYG upgrade"). Then confirm with `grep -c '^ORION_BASE_RPC_URL=' .env` that it is 0. A rejected endpoint is worse than the public fallback, and the next nightly run would hit it.
- **Plan-tier changes take effect gradually.** Right after a Free→PAYG upgrade, the same key answers some requests under the new limits and others under the old 10-block cap, whatever the span. So one passing 2,000-block request proves nothing. Run several rounds of mixed spans (10/11/50/500/2000, with and without the Transfer-to-0x0 topic filter) and enable the key only on a 100% pass. A new key from the same account inherits the account's tier, so swapping keys does not get around a cap.
- For a deferred retest, use the profile script `scripts/orion-rpc-retest.sh` (it wraps `orion-rpc-retest.mjs`). It runs 36 raw range probes plus orion's transport (latest block, multicall, and 7 days of chunked burn logs, about 150 chunks). It uncomments `ORION_BASE_RPC_URL` only if every check passes, and prints a key-masked report. Schedule it as a one-shot `no_agent` cron job delivering to orion-ops; dry-run it by hand first. Before enabling a different provider, change the line it matches (`/v2/` masking, `# DISABLED` comment).
- Report the result as a pass/fail per check. Quote the provider's own error text and give the concrete options (upgrade the plan, switch provider, or shrink the chunk size, which costs ~200x more calls).

Volume, for sizing plans: ~22 `eth_getLogs` calls a day, a few multicalls, and ~2k calls for a one-time 90-day backfill. That is free-tier volume. A paid plan only buys range limits and throttling headroom.
