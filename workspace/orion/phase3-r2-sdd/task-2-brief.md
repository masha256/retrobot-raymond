### Task 2: Price-method readers (EVM)

**Files:**
- Create: `src/prices/evmMethods.ts`
- Test: `tests/prices/evmMethods.test.ts`

**Interfaces:**
- Consumes: `PriceEntry`, `PriceMethod` (Task 1); `RpcTransport.multicall` (src/ingest/transport/rpc.ts).
- Produces: `callsFor(m: PriceMethod, at: { end: BlockRef; start: BlockRef }): ContractCall[]` and
  `decode(m: PriceMethod, raw: bigint[], at, quoteUsd: (ref: string) => number | null, feedUsd: Map<string, number>): { usd: number; detail: Record<string, unknown> } | null`;
  `priceHourEvm(rpc: RpcTransport, entries: PriceEntry[], at: { start: BlockRef; end: BlockRef }): Promise<Map<string, HourPrice>>`
  with `interface HourPrice { usd: number; source: string; checkGapPct: number | null; check: string; detail: Record<string, unknown> }`.
  One multicall for every primary, check and feed of the chain's entries; refs resolved in dependency order from that one result.

- [ ] **Step 1: Failing tests** with `fakeRpc({ callsAt })` per method, values taken from the scoping files' measured
  rows: Chainlink 8 decimals (CAKE 1.74948 at NOW row); Curve `price_oracle()` x CRV (cvxCRV 0.41377 x 0.2335 = 0.09662);
  Uniswap v2 cumulative TWAP over dt = 3600 s with `getReserves` timestamp catch-up (the pair's last-update fold);
  Aerodrome `currentCumulativePrices`; v3 `observe([3600,0])` tick mean with token0/token1 side; v4 `getSlot0` with zero
  liquidity -> check skipped (`checkGapPct: null`, detail `skipped: zero_liquidity`); `bound` outside [0.3, 1.0] -> gap
  reported as the distance to the bound. Review Focus 2: DIEM with VVV's primary call failing -> no DIEM entry in the map.
  Review Focus 3: a feed with `updatedAt` 6.6 h before `end.timestamp` -> priced, `detail.feed_age_s` = 23760.
- [ ] **Step 2: Run, see FAIL.**
- [ ] **Step 3: Implement.** Reuse the decoding already in `src/ingest/adapters/evm.ts` (`v2TwapPrice`, `clSpotPrice`,
  `side`) by moving the pure parts into `evmMethods.ts` and importing them back into `evm.ts` (AERO's adapters keep
  their output byte for byte: its asset test must stay green unchanged).
- [ ] **Step 4: Run** the new file, `tests/assets/aero*.test.ts`, typecheck.
- [ ] **Step 5: Commit** `feat(prices): EVM price methods read in one multicall per chain-hour`.

