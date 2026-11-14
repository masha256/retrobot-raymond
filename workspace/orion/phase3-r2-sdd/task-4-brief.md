### Task 4: First-party and Solana price methods

**Files:**
- Create: `src/prices/offchainMethods.ts`, `src/ingest/transport/solanaRpc.ts` (only if `src/ingest/adapters/solana.ts`
  has no reusable JSON-RPC client; otherwise extend that one)
- Test: `tests/prices/offchainMethods.test.ts`

**Interfaces:**
- Produces: `interface SolanaPriceTransport { getMultipleAccounts(keys: string[]): Promise<...>; slotAt(tsSec: number): Promise<number>; signaturesBefore(address: string, beforeSig: string | null, limit: number): Promise<...>; getTransaction(sig: string): Promise<...> }`;
  `priceHourOffchain(deps: PriceDeps, entries: PriceEntry[], hourMs: number, usdcUsd: number | null): Promise<Map<string, HourPrice>>`;
  `livePriceOffchain(deps, entry): Promise<HourPrice>` (levels: `allMids`, order-book mid, vault reserves).
  Hyperliquid and Lighter return a whole candle range per request: `priceRangeOffchain(deps, entry, fromHourMs, toHourMs): Promise<Map<number, HourPrice>>` (HYPE: one `candleSnapshot` for up to 5,000 hours; LIT: `/api/v1/candles`, 9 calls for 183 days).

- [ ] **Step 1: Failing tests** with recorded fixtures (shape-faithful, numbers from `hype-lit-pump.md`): HYPE spot and
  perp candles -> price x USDC/USD and gap; LIT candles + v4 check; PUMP past hour: slot search with 0.215 s slots,
  `getSignaturesForAddress` `before` cursor, `getTransaction(..., { maxSupportedTransactionVersion: 1 })`, price from the
  first swap's `postTokenBalances` of the two vaults (USDC 6 decimals, PUMP 6); Meteora check from its first swap before
  the hour (fee included); an hour with no swap in the hour before it -> reserves of the newest earlier swap, detail
  `last_swap_age_s`, refused beyond 6 h (`missing`). No request goes to a pump.fun host (assert the fake saw none).
- [ ] **Step 2: Run, see FAIL. Step 3: Implement. Step 4: Run, typecheck.**
- [ ] **Step 5: Commit** `feat(prices): Hyperliquid, Lighter and PumpSwap price methods`.

