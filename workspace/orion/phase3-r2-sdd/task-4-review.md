# Task 4 review: a4d49c7..27a6ff1 (Hyperliquid, Lighter, PumpSwap/Meteora price methods)

Reviewer read the full review package (1,503 lines, in two passes), brief, report, global constraints, progress rulings
(R4, R5, R8, R15, R16), task-4-controller-facts.md (ground truth) and hype-lit-pump.md. Line numbers are file lines at 27a6ff1.

### Spec Compliance

- ❌ Issues found (2, both against the controller's measured facts; everything else in the brief is present):
  1. Meteora historical check finds the pair's reserves with `owner == pair` instead of the LbPair's
     reserve_x@152 / reserve_y@184 (`src/prices/offchainMethods.ts:203`). See Important 1.
  2. The open (current-hour) candle is excluded only by the writer's gate (`writer.ts:372`); the exported
     `priceRangeOffchain` (`offchainMethods.ts:368-410`) and `closeAt` (`:150`) never compare with `deps.now`, so a range
     ending past the open hour prices the open candle. See Important 2.
- Brief checklist, verified: HYPE spot `@107` close × USDC/USD with perp check and gap (test 89.035/89.372, +0.3785%);
  one `candleSnapshot` per coin per 5,000 h; LIT `/api/v1/candles` ≤500/call, 9 calls for 183 d, v4 check from chain 1,
  zero_liquidity skipped; PUMP: slot search seeded at 0.215 s (`solana.ts:104`), `before` cursor from the seek block's
  first signature, `getTransaction` with `maxSupportedTransactionVersion: 1` (`solana.ts:241`), price from the two
  vaults' `postTokenBalances` resolved through static + loaded keys (`offchainMethods.ts:168-193`) with mint checks;
  Meteora check = first swap's execution price, fee included, non-swap txs skipped; older swap priced with
  `last_swap_age_s`, refused > 6 h as `stale_swap`; R8 pinned (`afterAll` over every fake HTTP + transport refusal test).
  `solanaRpc.ts` correctly not created (solana.ts already had the client). Departures 1-4 are covered by R16.
- ⚠️ Cannot verify from diff: Lighter `/orderBookOrders?market_id=2049&limit=1` reply shape (`bids[0].price` /
  `asks[0].price`, `offchainMethods.ts:485-490`) is not in the controller facts or the scoping file — needs one live probe
  (Task 10 at latest). Same for PumpSwap base vault's jsonParsed Token-2022 shape (code does not depend on the program
  owner, so it should parse; the fixture does not show it).

### Named risks (each checked)

1. **Ground truth vs code.**
   - Lighter `t` = candle start: ✅ keyed as hour start, ms or s accepted (`:117-125`). Open candle: ✅ in the writer path
     (`writer.ts:372` refuses `h + H > now` before calling the method; `closeAt` fetches only `[from, hourMs+1h)`, so no
     open candle enters the cache); ❌ in `priceRangeOffchain` — probe in my worktree: now 14:30Z, range 12:00–15:00Z
     priced the 14:00Z open candle (9.99 fake close → usd 9.9878).
   - Meteora reserves from LbPair offsets 152/184: ❌ not read at all; `owner == pair && mint == want`, first match.
     Probe: a swap tx that also lists a second pair-owned USDC account (the measured EjYhsATU… spam account) first gives
     check `in_usdc` 1.1e-7 and `checkGapPct` −99.997% — a breach alert from the wrong account.
   - PUMP reserve as Token-2022: ✅ functionally (neither tx-balance nor jsonParsed path depends on the token program),
     but no fixture uses the Token-2022 shape (test `:461` uses Tokenkeg / `spl-token` for the PUMP vault).
   - LIVE Meteora price = active bin: ✅ `(1+bin_step/1e4)^active_id × 10^(dec_x−dec_y)` from offsets 76/80, mints at
     88/120 verified, reversed pair inverted correctly (`:438-453`).
   - Historical Meteora = swap execution price: ✅ |ΔUSDC|/|ΔPUMP| (`:212-215`), but from the wrong-identified accounts (above).
2. **Missing vs wrong.** ✅ stale swap → `stale_swap` (no tx fetched, age from signature list); no swap / budget →
   `no_swap`; RPC/HTTP throw → writer `read_failed` + `errors`, chain stopped (`writer.ts:326-331`); zero vault → tx
   skipped (history) / throw (live); missing feed → `quote_missing` with no read (test asserts 0 fetches); HYPE window
   not reaching back → empty reply → `no_candle`. No path emits a number for these. Caveats in Minor 3/4/6.
3. **Units and timing.** ✅ HL candle `t = H` close prices [H, H+1h) (not H+1h); USDC/USD = chain-1 `feedUsd` of the same
   `h` (`writer.ts:376`, lowercased keys `writer.ts:178-181`); decimals from `uiTokenAmount.decimals` (6/6), live bin
   uses `entry.decimals` = 6. Slot search: probe in my worktree over 48 consecutive hours newest-first: 6–8 getBlockTime
   per hour (10 for the first), 0 wrong slots. A full PUMP hour with check = 15 requests (1 getSlot + 9 getBlockTime +
   getBlock + 2 sig pages + 2 tx). See Minor 1.
4. **R8.** ✅ `git grep pump.fun 27a6ff1 -- src`: only comments and the `FORBIDDEN_HOST` guard (`solana.ts:110,131`);
   Hyperliquid/Lighter URLs are constants; `makePriceDeps` has no public Solana fallback (`writer.ts:488-496`); pinned by
   the transport refusal test and the file-wide `afterAll` (`tests/prices/offchainMethods.test.ts:58-63`).

### Strengths

- The PumpSwap primary is done carefully: vaults matched by account key (static + `loadedAddresses`), mints asserted,
  failed signatures never fetched, stale detection from the signature list without a `getTransaction`.
- `slotAt` is a sound bracket search: correct handling of skipped slots (-32007/-32009), `null` past the finalized
  head, anchors reused across hours; exact against a brute-force oracle with a deliberately wrong slot time.
- Run-scoped candle cache makes the writer's hour-by-hour walk cost 1 request per coin per run; `calls` is reported (R15).
- Test fakes are behaviour-faithful where it matters (−32015 for v0, `before` semantics, skipped slots), and the report's
  mutation table is backed by assertions that would catch each mutation.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
1. **`src/prices/offchainMethods.ts:199-216` (`dlmmExecution`) — Meteora reserves identified by `owner == pair`, first
   match.** Ground truth: the pair owns 12 token accounts including a second USDC account; reserves are the LbPair's
   `reserve_x`@152 / `reserve_y`@184. Any tx that lists another pair-owned account of the same mint yields a check from
   the wrong quantity (probe: −99.997% gap → false `ORION WATCH` alert). Fix: read the lb_pair once per run
   (`getMultipleAccounts([pair])`, cache), decode reserve_x/reserve_y/token_x_mint/token_y_mint, then match balances by
   `accountKeys(tx)[accountIndex]` exactly as `vaultReserves` does. Make the `dlmmTx` fixture (test `:275`) use the real
   reserve keys (6uVEyA1R… Token-2022 PUMP, 5RLzTiyG… USDC) plus a pair-owned spam USDC balance, and assert it is ignored.
2. **`src/prices/offchainMethods.ts:368-410` (`priceRangeOffchain`) — no open-candle exclusion.** The function is the
   brief's history API (Task 6/7 consumers); with `toHourMs` past `floor(now/1h)` it writes the still-moving close of
   the current hour (probe above). Fix: clamp `toHourMs` to `floor(deps.now/H)*H` (hours beyond → `missing`
   `no_block_yet`), and add the same guard in `closeAt` (`:150`) as defence in depth; test with a range ending after now.

#### Minor (Nice to Have)
1. `src/ingest/transport/solana.ts:214-217` — the interpolation aims 2 slots low and clamps to `lo+1`, so near the
   target it creeps one slot per probe: 6–8 getBlockTime per consecutive hour vs the scoping's 5–6, and ~15 requests per
   PUMP hour vs R2's "~8 Solana calls/hour" (≈10k calls for ~700 h). Bisect once `top−lo` is small, and pin per-hour
   cost over consecutive hours (the test's ≤14 bound per search at `tests/…:356` is loose).
2. `offchainMethods.ts:283` — a Meteora check read that throws (RPC error) loses the PUMP primary for the hour and stops
   the Solana chain for the run; a check failure should leave the check unread (`skipped: read_failed`).
3. `offchainMethods.ts:233` — when the first > 6 h signature is a failed one, `stale_swap` carries `scanned_back_s` but no
   `last_swap_age_s`; and `no_swap` is reported both for "history ended" and "1,000-signature/8-tx budget spent" — give
   the budget case its own reason.
4. `writer.ts:321` (Task 3 code, noted in report) — `collect` drops the missing entry's `detail`, so `stale_swap` age and
   `no_swap` budget never reach `WriteResult`.
5. `offchainMethods.ts:334-338` and `:401` — the candle-check read (quote_missing / close / no_candle) is written twice
   with the same three branches; extract one helper.
6. `tests/prices/offchainMethods.test.ts:461` — the live PUMP vault fixture is a Tokenkeg/`spl-token` account; the real
   PUMP vault is Token-2022 (`spl-token-2022`, with `extensions`). Use the faithful shape so the parser is pinned on it.
7. `writer.ts:387-388` — `no_rpc_url` from `solanaFrom` is an `OrionError`, which the writer re-throws: a run that wants
   PUMP without `ORION_SOL_RPC_URL` aborts entirely (after committing earlier chains of the day) instead of listing PUMP
   missing. Probably intended (fail loud); confirm.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The HYPE/LIT candle paths and the PumpSwap primary are correct against the measured facts and well
tested, but the Meteora historical check identifies its reserves by ownership rather than the LbPair's reserve fields
(a check computed from the wrong quantity when another pair-owned account appears), and the exported range API does not
exclude the open candle; both are small, targeted fixes.

Checks run (own detached worktree `.worktrees/rev-t4` at 27a6ff1, `npm ci`, removed afterwards): a scratch copy of the
test file plus 4 probes (`npx vitest run tests/prices/zrev.test.ts --maxWorkers=1`: 22/22 passed, probes printed the
figures cited above). No network, no edits to the main worktree.
