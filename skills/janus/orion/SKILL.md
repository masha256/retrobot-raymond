---
name: orion
description: Use when operating, debugging, or developing orion.
---

# Orion operations and development

This skill covers Mike's orion valuation pipeline (VVV/HYPE/AERO/CRV/yCRV/cvxCRV/sdCRV live; the last three are CRV liquid-locker wrappers): diagnosing ingest failures, vetting or swapping data endpoints and API keys, running the test suite, onboarding and calibrating new assets. Mike manages orion development from the Raymond bot's orion-dev topic.

## Development: tests and branches
- Run `npx vitest run --maxWorkers=2` then `npm run typecheck`. Plain `npm test` on this 4-core host times out the CLI tests (`tests/cli/{cli,ingest.cli,tick.cli}.test.ts` spawn subprocesses; 5s/10s timeouts) under full parallelism; rerun those files alone before calling any failure real.
- Report the counts (files/tests passed) from the real run, not an assertion.
- Feature work follows the repo's own pattern: branch `feat/<asset>`, a spec in `docs/superpowers/specs/<date>-orion-<topic>-design.md`, then a plan in `docs/superpowers/plans/`, then implementation, then a followups note in `docs/superpowers/notes/`. Read the latest onboarding spec+followups (AERO, HYPE) before drafting a new one; they carry the conventions (mirror-rule bands, backfill > window, hash pins, the 5 user checkpoints).
- Leave unrelated working-tree changes uncommitted and mention them, unless Mike says to commit them. Stage with explicit `git add <paths>` and never `git commit -a`/`-am`, because `-a` silently sweeps the stray file in. If it happens, `git reset --soft HEAD~1`, `git restore --staged <file>` and recommit.
- Adding a new asset (scoping, build, live checkpoints, calibration, cron line, wrapper-yield questions): follow `references/asset-onboarding.md`.
- Present every value-changing choice (packages, windows, price bases) as priced options with a recommendation, and let Mike pick. Record the pick and its rationale in the committed file, then don't re-argue it.
- Before building a model change for an asset (a new flow source, a component, a re-wire), search for imminent protocol events: mergers, token migrations, new emission or voting mechanisms. If one lands within weeks and would change the contracts or mechanism being wired, stop before writing code. Bring Mike hold-vs-interim-vs-full options with the event dates, and leave no half-built branch behind. When he picks hold, create a one-shot reminder (cronjob_manage, delivered to orion-dev) dated just after the event. Give it a check-only prompt that carries the background, the numbers and any data traps (e.g. a revised API day that a re-backfill would re-import), and ends with a proposed plan for his OK. Scratch notes are pruned, so the prompt must stand alone. Also answer "won't this break anything now?" concretely: which sources the asset reads that the event could move, and that the failure shows up as a degraded or blocked grade rather than a wrong value.
- Re-measure an earlier estimate (yours or a research note's) before acting on it. When the new number contradicts what you told Mike, say so explicitly with old vs new, rather than letting the old figure stand.
- When Mike defers a decision ("will think about it"), finish the work that doesn't depend on it. List the decision as open in the followups note, and don't build it unasked.
- Building blocks that keep the grade at A without manual rows: `constant` source for structural values (e.g. a zero staker share); adapters may return `schedule_steps` (step in force + future coded cuts) on schedule metrics; `vote_incentives` component for bribes (third-party vote payments are NOT holder flow; `price_basis: spot` per Mike's choice for CRV).
- Other config building blocks: `contract_read` with `args: [<contract names>]` (passed as `address` args) and `returns: [int128, uint256]` + `pick: <i>` for one field of a struct return (negatives refused); `transfer_flow` `share_price` for rewards paid in vault shares; holder flow `valued_per: recipients` for stakers-only flows; `monitor_only: true` on a level metric for display data (see below).
- **Data Mike wants for display (coinrevs site) or watching, not valuation:** add it as a `monitor_only` level metric on the asset whose run already reads that contract, so every line comes from one block and shares add up. It is stored daily, never a driver, never in the grade, and the schema refuses it on anything the valuation uses. Recommend "monitor, not input" when the measured holder flow already reflects the quantity, because adding it as a driver double-counts. History starts on the day it goes live (no level backfill path), so say so. A failed monitor read still marks its source (`chain_levels`) failed in the fetch report and counts toward the failure streak; warn Mike before merging.
- When a spec explains *why* a rule holds, check it against the code comment and the on-chain mechanism before committing. A spec that states the opposite of the code misleads the next reader even when the math is right.
- When a component or estimate comes out far from your back-of-envelope, debug-print its breakdown in the asset test before adjusting assertions, and surface the cause to Mike as a decision (e.g. horizon-price feedback shrank CRV bribes 20x) rather than silently loosening the test.
- A value derived from an on-chain flow is stamped `onchain`, not `api`.
- New engine/ingest options must leave every existing asset's output byte for byte the same: default the new field so it changes nothing, add new breakdown keys only when the option is active (e.g. `...(share !== 1 ? {k: share} : {})`), and confirm with the VVV golden test plus the full suite. Then no ENGINE_VERSION bump is needed. Adding a field to a planned type (e.g. a flow-group member) breaks `toEqual` plan tests; update those fixtures with the new key's null default.
- When a change is MEANT to alter output (a new output field, a new term in a return): bump `ENGINE_VERSION` (replay refuses across versions, by design), re-pin the VVV golden hash, and add a golden test that deletes the new keys and resets the version and still matches the old hash, proving nothing else moved. Add signal fields as `.optional()` (schema_version stays 1, old signals lack them). Before asking to merge, price all five assets in a throwaway home (`model whatif <a> --json`) against their latest live signals and report before → after per asset, saying which assets don't move and why.
- Give a new optional module param no default and validate it in the module's `validateParams` (errors surface via `validateAssetModules`, not `parseAssetYaml`), so existing config hashes stay put; setting it on an asset moves that asset's hash, so re-pin its test and warn that its next signal lists "config".
- Before committing, `git grep` for the RPC key prefix and compare any hit against the real key in `.env` (masked). Test fixtures may legitimately hold fake keyed URLs; the real key must never be in a commit.
- When Mike says to build while he is away, stop at a green feature branch: spec, code, asset test, a scratch-home live fetch. Merge, persona assign and live checkpoints wait for him.
- Future-dated observations (schedule steps for a coded cut) must never set the valuation's as-of. `updateAsset` values at the newest `observedAt` the fetch wrote; for schedule metrics, count only the earliest step (the one in force). Otherwise the signal is dated at the cut, every metric goes stale (grade D), and the bad signal stays "latest" until that date.

## Repairing bad rows a live run wrote
- Fix the code on a `fix/<topic>` branch with a regression test first. Then list the exact rows the run left (`signals`, `valuation_runs`, `snapshots`, `config_versions.created_at`; find them by scanning `*_at`/`as_of` columns for dates past today).
- Propose the repair to Mike before running it, in this order: deploy the fix (ff-merge + build); fresh backup; one `BEGIN…COMMIT` whose `DELETE`/`UPDATE`s are each pinned by id AND asset (AND signal_id/hash where there is one); re-run the valuation without a fetch or the agent.
- Leave correct observations and journal rows in place. Don't edit the append-only `signals.jsonl`/`ticks.jsonl` logs.
- `PRAGMA foreign_keys` is off in `orion.db`, so delete children before parents (signals → valuation_runs → snapshots) by hand.

## Changing the live install (Mike's standing rules)
The repo working tree IS the live site: cron runs `run-daily.sh` → `dist/cli/index.js` with `ORION_HOME` = repo root, so `orion.db` and `.env` there are production.
1. Before any live write, check nothing is mid-run (`pgrep -af 'orion|run-daily'`) and note when the next cron tick fires.
2. Back up the DB first, with the sqlite online backup, then verify it: `sqlite3 orion.db ".backup 'backups/orion.db.pre-<topic>-<UTCstamp>'"`, `PRAGMA integrity_check` on the copy, and compare row counts (observations, assumption_sets, fetch_runs, anomalies). `chmod 600` the copy and keep `backups/` out of git via `.git/info/exclude`.
3. Merge with `git merge --ff-only feat/<x>`, then `npm run build` — cron runs `dist/`, so an unbuilt merge changes nothing live — then `asset validate` every asset with the built CLI, not only the new one.
4. Run live commands with `node dist/cli/index.js ...` (what cron uses, not `tsx src`), and in the reply list every command run against live verbatim, in order, each with its result, and say plainly which ones wrote to the DB. Record row counts before and after, and state that a dry run left them unchanged.
5. Before a step that calls the analyst agent (a tick or bootstrap, which costs Anthropic spend) or writes signals, say what it will write and ask for a go.
6. Do dry runs and calibration during development from a throwaway home instead (`ORION_HOME=$TMPDIR/<x>`). Seed it with assets and `.env`, plus a `.backup` copy of `orion.db` when you need live history. It never touches production. Delete it afterwards, because it holds a copy of `.env`.
- Don't push orion (`git push`) until Mike explicitly says to. Never report a push you didn't see succeed.
- `package-lock.json` is committed; a later npm-touched lock change is again an unrelated working-tree change: leave it and mention it.

Repo: `/home/hermes/git/orion`. Live DB: `orion.db` in the repo root (sqlite). Secrets: `orion/.env` (gitignored, mode 600). It is sourced by the profile's `scripts/orion-tick.sh` and also read by orion itself via `loadEnv`. Cron jobs and delivery are covered in memory; use the `cron-job-administration` skill for any schedule changes.

## External dependencies (what each asset hits)
- **VVV, AERO**: Base mainnet RPC (chain 8453). The env var is named by `ingest.rpc_url_env` in `assets/<asset>.yaml` (currently `ORION_BASE_RPC_URL`). When it is unset, orion falls back to `https://mainnet.base.org` (`DEFAULT_RPC_URLS` in `src/ingest/run.ts`). They also use CoinGecko, DefiLlama and `http_json` cross-checks.
- **Ethereum mainnet (chain 1)**: `ORION_ETH_RPC_URL` in `.env` holds Mike's Alchemy key (passes 100k-block `eth_getLogs` with `blockTimestamp`, and archive `eth_call`). Free mainnet RPCs (drpc, publicnode) refuse ranged logs beyond ~10k blocks and archive reads, so never default chain 1 to a keyless URL. Chains live in `src/ingest/transport/chains.ts` (per-chain log range, block time, keyless default or none); adding a chain = a row there plus the viem chain in `viemRpc.ts`. The transfer scanner reads one day per `eth_getLogs` call regardless of the range cap, so a backfill costs one call per day (~2 min for 100 days on mainnet).
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
