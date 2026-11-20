# Task 5 report: `data rebuild-supply-levels` and the unreplaced circulating purge refusal

Status: DONE. Commit `176c45a feat(data): rebuild-supply-levels and the unreplaced circulating purge refusal`, on BASE 596245b.

## What
- `src/db/supplyLevels.ts` (new): `rebuildSupplyLevels(db, loaded, { rpc, http, env? }, { yes, now, release? })` ->
  `{ asset, applied, metric: 'circulating_supply', rows, rebuilt, unchanged, refused[{id,observedAt,reason}], notRebuildable[{id,observedAt,day}], calls }`.
  - R5: no per-adapter read path. Each target row runs the asset's configured source through `getSourceHandler(type).fetch([request], ctx)`, the same handler a fetch uses. `ctx.block` is `firstBlockAtOrAfter(ceil(observed_at))` (anchored on the previous row's block). A 00:00Z row uses the `day_blocks` cache (dbDayBlocks) and fills it; the cache is written only on `--yes`. The reading is checked with `validateReading` and must be `onchain`.
  - Which rows are targets: a row counts as the current source's only when its `source_type` equals the current source's rung AND its locator `adapter` and `call` keys equal the current locator's (an absent key equals an absent key). So CoinGecko `market_data` rows and the wrappers' old `erc20_supply` rows (contract_state, no adapter, call `totalSupply()`) are targets. Rows of the current adapter, including rebuilt ones, are `unchanged`, so a second run rebuilds 0. A params change inside the same adapter does not make a row a target (on purpose).
  - `rows` = rebuilt + refused + notRebuildable.
  - `supplyNotRebuildable(loaded, observedAt)` is exported and shared with purge. A row is notRebuildable when the source does not read EVM state (`isChainSource`, or an RPC adapter whose `chainOfSource` is `eip155:*`; HYPE's hype.* and PUMP's solana.* are not), or when the row is before 00:00Z of `rebuild_from`. When nothing is rebuildable, no RPC is opened.
  - Refused: the block search fails, the latest block can't be read, the handler throws or returns a failed reading (a reverting term fails the whole view_sum, Review Focus 1), the result is not a level, or the value is invalid. A refused row is listed and left untouched.
  - Provenance: `fetchedProvenance` of the current source (method measured, rung contract_state, chain, config hash) plus `blockFrom/blockTo` = the read block, `codeVersion` = the release, and `locator.rebuilt = { at, release?, from_id }`. Before writing, it checks that `originOf` reads back `onchain`. `sourceDetail` = `rebuilt from #id: <adapter detail>`.
  - Dry run by default (reads run, nothing is written). `--yes` takes the asset's run lock, uses one transaction per UTC day, and re-checks inside the transaction that the old row is still active (`rebuild_conflict`). insertObservation supersedes the old row.
  - `calls` counts RPC requests through a Proxy on the transport.
- `src/db/purge.ts`: a `market_data` purge of `circulating_supply` refuses with `purge_unreplaced_supply_level` when any targeted row (superseded ones too) has no active non-market_data row at its observed_at and is rebuildable. notRebuildable rows are deleted and listed as `withoutReplacement` (same shape as R38). The R38 "no replacement" SQL is now `unreplacedRows`, shared by both refusals; R38's behaviour is unchanged.
- `src/config/schema.ts` (R6): `rebuild_from` is optional, must be a real UTC day `YYYY-MM-DD` (round-trip checked), has no default, and is refused on non-level metrics.
- `assets/aero.yaml`: `rebuild_from: 2026-11-10` on circulating_supply, with a comment. Only AERO's hash was re-pinned (80c32373… -> 4f3d7c2f…, in tests/assets/aero.ingest.test.ts and tests/config/load.test.ts, each with a re-pin comment).
- CLI `orion data rebuild-supply-levels <asset> [--yes] [--json]` (src/cli/commands/data.ts): deps come from `ingestDepsFor(ctx)` (rpcFactory/http/env). It exits 3 when any row is refused, on both the dry run and `--yes`.
- orion-remote: verb `data rebuild-supply-levels <a> [--yes]` (usage text says exit 3; passthrough adds `--json`; listed in the `data:` refusal message). docs/ops/deploy.md has a new entry in the verb block.

## Tests (RED -> GREEN)
- tests/db/supplyLevels.test.ts (11):
  - RED: `Cannot find module '../../src/db/supplyLevels.js'`. With purge.ts stashed: the 3 purge cases failed (3 failed | 8 passed). GREEN 11/11.
  - Cases:
    - A CoinGecko row at 2026-10-20 is rebuilt at `blockAtOrAfter(ts)` with an exact value and provenance; a midnight row's block is cached in day_blocks.
    - An escrow `lockedSupply()` reverting before 2026-10-01 means the 09-15 row is refused (reason names the call and block), stays active and keeps its value.
    - A second dry run and a second `--yes` after `--yes` rebuild 0.
    - A wrapper's old erc20_supply row is rebuilt; the current-adapter row is unchanged.
    - HYPE: notRebuildable, `calls: 0`, the RPC factory is never called.
    - AERO: rows before rebuild_from are notRebuildable, a row on it is rebuilt.
    - `run_in_progress` under a held lock.
    - An asset with no circulating_supply returns all zeros.
    - `rebuild_from` invalid values (2026-02-30, a timestamp, 20261110, 2026-1-10, a word, "") are refused, and so is the key on a flow metric.
    - Purge before rebuild is refused for CAKE (dry run and apply, nothing deleted), then allowed after the rebuild, with every day still having a level.
    - HYPE purge is allowed and lists every row.
    - AERO: rows before rebuild_from are listed; a row on it with no replacement refuses.
    - A third_party purge is not a supply-level purge.
- tests/db/purge.test.ts (+2): a superseded CoinGecko row with no replacement refuses (EVM source), and a contract_state row at the same observed_at replaces it. An API source, or a row before rebuild_from, is listed; a row on rebuild_from refuses.
- tests/cli/supplyLevels.cli.test.ts (2): RED `unknown command 'rebuild-supply-levels'`; GREEN 2/2. Covers the dry-run lines, `--yes --json`, the refused row's exit 3 on the dry run and `--yes`, and that the refused row keeps its value.
- Python: RED with orion-remote stashed (67 run, failures=2, errors=1); GREEN `Ran 67 tests ... OK` (was 65). Covers passthrough, refusals, usage text and exit-3 passthrough.
- Full suite `npx vitest run --maxWorkers=2`: 2021/2022 passed (156 files). Typecheck clean.
  - The one failure is `tests/db/daemonSchema.test.ts > 0002_daemon > schema: every 0002 table exists in schema orion`. It fails on the environment, not the code: the test DB `orion_test` contains schema `r3probe_1795204385`, the controller's live-probe schema (its cleanup is waiting for Mike, per progress.md), and the test asserts no other schema holds 0002 tables. I did not drop it.
  - The first full run also failed tests/meta/awaits.test.ts on a non-awaited `purgeMetrics` in my new purge.test.ts helper. That is fixed (`async`/`await`), and the file plus purge.test.ts are 22/22.

## Self-review
- `nowIso` in the rebuild context is the row's observed_at. `priceDeps` is not passed: a price adapter would read its other-chain feed at the head, not at the block. No circulating source uses one.
- `--yes` re-reads under the lock (the dry run's reads aren't reused), so a row can't be written from a stale read.
- Per-day transactions: a `rebuild_conflict` rolls back that day only. Earlier days stay committed, as in rebuild-price-levels.

## Concerns
- daemonSchema test fails until the controller's `r3probe_1795204385` schema is dropped from orion_test.
- A term whose contract had no code yet but is read as an argument (`token.balanceOf(escrow)`) returns 0 rather than reverting. That is correct (the escrow held nothing then), so the row is rebuilt, not refused. Only a call ON a contract with no code reverts. If Mike wants "no-code term = refuse" for argument terms too, that needs code-at-block checks, which the RpcTransport can't do (getCode reads the head only).
- The target rule ignores a params change within the same adapter (an AERO row from an earlier params set stays `unchanged`). This is deliberate, so AERO's post-11-10 rows don't move.
