### Task 3: Hour blocks and the chain price writer

**Files:**
- Create: `src/db/pg/migrations/0008_chain_prices.sql` (this task adds the `hour_blocks` table and the `prices`
  columns; Task 5 appends the view to the same file before release), `src/db/hourBlocks.ts`, `src/prices/writer.ts`
- Modify: `src/db/prices.ts` (`upsertPrices` writes `check_gap_pct`, `check`, `detail`), `src/ingest/transport/chains.ts` (comment: the switch block is 53,556,128)
- Test: `tests/prices/writer.test.ts`, `tests/db/hourBlocks.test.ts`, `tests/db/pg/migrate.test.ts`

**Interfaces:**
- Consumes: Task 1, Task 2; `firstBlockAtOrAfter` (rpc.ts:111).
- Produces: 0008 part 1: `CREATE TABLE hour_blocks (chain_id bigint, hour timestamptz, block bigint NOT NULL, block_ts bigint NOT NULL, PRIMARY KEY (chain_id, hour))`;
  `ALTER TABLE prices ADD COLUMN check_gap_pct double precision, ADD COLUMN "check" text COLLATE "C", ADD COLUMN detail jsonb`.
  `dbHourBlocks(db, chainId): { get(hourMs): Promise<BlockRef|null>; put(hourMs, b): Promise<void> }` (first write wins, as day_blocks).
  `writeChainPrices(db: Db, deps: PriceDeps, refs: string[], fromHourMs: number, toHourMs: number, opts?: { signal?: AbortSignal; budgetMs?: number }): Promise<WriteResult>`
  with `interface WriteResult { written: Record<string, number>; skippedExisting: number; missing: { ref: string; hourMs: number; reason: string }[]; breaches: { ref: string; hourMs: number; gapPct: number; check: string }[]; calls: { [chain: string]: number }; reachedMs: number | null; stoppedByBudget: boolean }`.
  It skips hours already stored for that ref under its primary's source, walks newest hour first, commits one chain-day per transaction, and stops at `budgetMs`.
  `interface PriceDeps { rpcFor(chain: string): RpcTransport; solana: SolanaPriceTransport; http: HttpTransport; now: Date }` (Task 4 supplies `SolanaPriceTransport`).

- [ ] **Step 1: Failing tests.** Review Focus 1: a fake Base chain with 2 s blocks then 0.2 s from block 53,556,128;
  hours 2026-11-05T16:00Z..20:00Z resolve to the first block at or after each hour; the search from the previous hour's
  block costs <= 4 `getBlock` calls per hour (measured scoping: 1-2); an hour whose H+1h is after the head writes
  nothing (`missing` reason `no_block_yet`). Idempotence: running twice writes 0 rows the second time and makes no
  multicall. Budget: with `budgetMs` 0 after the first day, `stoppedByBudget` true and exactly one chain-day committed.
  Breach: cvxCRV gaps 3.4% then 3.5% -> one breach (consecutive 2); 3.4% then 0.1% -> none. Migration test: 0008 applies
  on a 0007 schema without `--breaking`, and `orion-2026.11.12.1`'s queries still run (existing migrate fixtures).
- [ ] **Step 2: Run, see FAIL.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** the three files, typecheck.
- [ ] **Step 5: Commit** `feat(prices): hour-block cache and a resumable chain price writer`.

