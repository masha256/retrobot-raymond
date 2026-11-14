# Task 4 re-review, fix round 1 (bd4feed..b50e94b)

### Finding Verdicts

1. **Meteora check picks reserves by owner == pair** — ADDRESSED. `dlmmReservesOf` (offchainMethods.ts, diff L87-99) decodes token_x/y_mint @88/@120 and reserve_x/y @152/@184, accepts either PUMP/USDC order, and throws otherwise. `dlmmReserves` (L102-112) reads it with one `getMultipleAccounts([pair])` per deps and caches it. `dlmmExecution` (L119-143) matches `keys[b.accountIndex] === account` using `accountKeys(tx)`, which covers the static keys plus loaded writable/readonly, and asserts the mint. The fixture `dlmmTx` (test L509-523) uses the real 6uVEyA1R… (PUMP, programId TokenzQd…) and 5RLzTiyG… (USDC, Tokenkeg) keys. Spam USDC EjYhsATU… is pair-owned, listed first, and moves by 1 raw. The test "reads the LbPair's reserve_x/reserve_y (once per run)…" (L609-620) shows it ignored (gap +0.1455%) and exactly one `[[PAIR]]` read over two hours.
2. **An open candle can be priced** — ADDRESSED. `openHourMs`/`isClosed` (L31-32) treat hour h as closed iff h+1h ≤ floor(now/1h)·1h.
   - `priceRangeOffchain` (L303-310) caps fetches at `closedTo` and marks later hours `no_block_yet`, with no fetch when nothing is closed.
   - `priceHourOffchain` (L253-254) short-circuits an unclosed candle hour before any fetch.
   - `closeAt` (L55) returns null for an unclosed hour, so neither the primary nor the check candle can fetch or cache an open hour.
   - The live path never reads candles (allMids / orderBookOrders mid / vaults).
   - Test L446-463: at now 14:30Z, the 12–16Z range prices only 12Z and 13Z, every endTime is < 14Z, and a single 14Z hour makes 0 calls.
3. **Check read error drops the primary / stops the chain** — ADDRESSED.
   - In `solanaHour` (L221-230), the try wraps the LbPair read, `lastTx` and `dlmmExecution`. A non-Orion error becomes `check_error` with `{method, error}`, and the primary is still returned through `withCheck`. Config `OrionError`s are rethrown, which is correct.
   - The live path does the same (L334-340).
   - The writer's abort is polled (`opts.signal?.aborted`), not thrown through the transport, so the catch cannot swallow a lease loss.
   - Tests: L622-644 (−32603 on the pair signatures, a missing LbPair, wrong mints) and live L708-711.
4. **missing.detail lost / no_swap conflates budget** — ADDRESSED.
   - writer.ts `collect` (L391-392) copies `m.detail`, and `types.ts` adds `detail?`.
   - In `lastTx`, the end of history gives `no_swap` (L177), while an exhausted tx budget (L165) or page budget (L181, with `signature_pages`) gives `read_budget_spent`.
   - Tests: writer L737-742 and offchain L646-655.
5. **Fixtures use the live shapes** — ADDRESSED.
   - Meta balances carry `programId` (Token-2022 for PUMP, Tokenkeg for USDC; L491).
   - The live PUMP vault is `spl-token-2022` with the immutableOwner and transferHookAccount extensions and `tokenAmount{amount, decimals 6, uiAmount}` (L680-685).
   - The Lighter book fixture is unchanged, and the code reads `bids[0].price`/`asks[0].price` strings and takes the mid (as probed).

Check run: an own detached worktree at b50e94b, `npm ci`, `npx vitest run tests/prices --maxWorkers=1` → 4 files, 82/82 passed. The worktree was removed.

### New Breakage in the Fix Diff

- Minor: when `dlmmReservesOf` throws (a bad or missing LbPair), nothing is cached. Every later PUMP hour in the run therefore re-reads the pair (+1 request per hour) and gets `check_error` again. The extra cost is bounded and the result is correct, so this does not block.

### Out-of-Scope Observations

- None new; the implementer's own concern (a `stale_swap` reached via a failed signature carries `scanned_back_s`, not `last_swap_age_s`) is acceptable and documented.

### Verdict

**Fix round:** All findings addressed, no new Critical/Important breakage.
