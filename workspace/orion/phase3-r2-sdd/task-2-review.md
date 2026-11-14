# Task 2 review: EVM price-method readers (7b75080..1d8e9bd)

Reviewer: task reviewer (spec + quality). Diff read in one pass from review-7b75080..1d8e9bd.diff. Line numbers are at
1d8e9bd. Tests ran only in a detached worktree `.worktrees/rev-t2` (since removed). Probes used a scratch test file there
that was never committed.

### Spec Compliance

- ✅ **Spec compliant.**
  - `src/prices/evmMethods.ts` and `tests/prices/evmMethods.test.ts` were created. `src/prices/types.ts` holds HourPrice,
    PriceDeps, SolanaPriceTransport and WriteResult (Ruling R3).
  - The pure decoders `sideOf`, `reserveTwap` and `sqrtPriceInQuote` moved out of evm.ts and are imported back
    (evm.ts:1, :100, :196, :210).
  - Every Step 1 case in the brief has a test: CAKE Chainlink, cvxCRV 0.41377 x 0.2335, v2 fold, Aerodrome, v3 side,
    v4 zero liquidity, bound gap, Review Focus 2 (DIEM/VVV) and Review Focus 3 (feed_age_s 23760).
  - The signature departures are the ones the controller recorded in progress.md "Carry to Task 3":
    - `callsFor` and `decode` take a ctx.
    - `decode` returns a miss object with a reason instead of null.
    - `priceHourEvm` returns `{prices, feedUsd, checks, missing}`.
- ⚠️ **Cannot verify from this diff:**
  - "One multicall per chain-hour" holds on a v2/Aerodrome chain (Ethereum, Base) only when the Task 3 writer passes one
    `BlockReadCache` across consecutive hours and prunes it. Without the cache it is 2 multicalls per hour
    (evmMethods.ts:463-464). Task 3 must pin this with a multicall-count test.
  - The v4 currency side has no on-chain cross-check (see Minor 3).

### Named risks (checked)

1. **Price math per kind.** I wrote an independent Python script (scratch `t2_arith.py`, stdlib only, no Orion code)
   that recomputes every expected value from the raw test inputs:

   | Case | Independent result |
   |---|---|
   | CAKE | 1.74948 |
   | CAKE v3 check (ticks cross zero, two's-complement words) | 1.7497484 (gap 0.01534%) |
   | cvxCRV | 0.0966153 |
   | cvxCRV get_dy check (dx 100, /(1-fee)) | 0.42 (gap 1.5057%) |
   | SKY v2 with the fold | 0.055 |
   | SKY v2 without the fold | 0.031667 |
   | USDS-in-SKY (token1 side) | 18.3333 = (1/0.06 + 1/0.05)/2 |
   | VVV Aerodrome | 19.4017 |
   | DIEM | 1577.4358 = 81.304 x 19.4017 |
   | VVV v3 token1 side, 18 vs 6 decimals | 19.39806 (≈ 19.4 x 0.9999) |
   | LIT v4 currency0 | 3.3573 |
   | AERO v2 | 0.573529 |
   | AERO slot0 | 0.5765 |
   | sdCRV bound | +5 / -16.667 / 0 |
   | Feed age | 23760 |

   - Every value matches the test's expectation.
   - None of the expectations came from the code under test. Each was derived by hand: the reserve ratios, the
     piecewise 0.06/0.05 fold and `meanTickPrice` are re-implemented in the test.
   - The formulas match the contracts:
     - Uniswap v2 `price0 += encode(r1)/r0 * elapsed`, with uint32 elapsed and mod 2^256 (evmMethods.ts:66-70).
       The side is picked from the price0/price1 cumulative (:73-77).
     - v3 `(tc[1] - tc[0]) / seconds` then 1.0001^tick, using token1/token0 raw x 10^(td-qd) (:308-312).
     - observe word picks 3 and 4 match the controller's on-chain check of the observe word layout.
     - curve_get_dy dx is scaled by coin i's decimals and dy by the quote ref's decimals (:168-171, :287-291).
2. **Missing vs wrong.**
   - A failed call gives `call_failed` (:489).
   - A missing quote ref gives `quote_missing`, both when the ref is unpriced this hour and when it is absent from
     `entries` (:231, :498).
   - A zero feed answer gives `not_positive`, and the feed is dropped from feedUsd (:215, :476-482).
   - A negative answer is refused by the transport's `pickValue` (viemRpc.ts:27), so it becomes `call_failed`.
   - A non-finite or ≤0 in_quote gives `not_positive` (:278-281).
   - An unknown usd_feed on a pool method throws `invalid_price_config` (:446-447).
   - A pool whose token0/token1 don't match gives `bad_read` (:243-249).
   - A stale feed is priced, with feed_age_s (:212-216).
   - Probes I ran, all passing:
     - pool token mismatch -> VVV `bad_read` and DIEM `quote_missing`, empty map
     - zero Aerodrome reserves -> `bad_read`
     - ETH/USD answer 0 -> VVV `quote_missing`
     - unknown usd_feed -> throws
   - **No path produces a number instead of a miss.** One gap in what gets recorded: Minor 1.
3. **AERO byte-identity.**
   - `git diff --stat 7b75080 1d8e9bd -- tests/` touches only the new test file, so the aero and evm adapter tests are
     unchanged.
   - Between old and new evm.ts, the moved expressions are token-for-token identical:
     - `rQuote / 10 ** qd / (rToken / 10 ** td)`
     - `(Number(sqrt) / 2 ** 96) ** 2`
     - `(which === 0 ? raw : 1 / raw) * 10 ** (td - qd)`
   - The floating-point order is unchanged, the error strings are identical, and only the order of the throws relative
     to the side-effect-free `td`/`qd` lines changed.
   - No import cycle: prices/config.ts -> db/prices.ts -> types.ts only.
   - Ran `tests/prices/evmMethods.test.ts`, `tests/assets/aero.ingest.test.ts` and `tests/ingest/adapters.evm.test.ts`:
     **37/37 green**.
4. **Cost and cache.**
   - All planned calls (primaries, checks and feeds) are deduplicated by key and go into a single `rpc.multicall` per
     block (:401-418, :460).
   - B(H) is read only when some call is `at: 'start'` (:464).
   - The cache is keyed by block number first, then by call, so different blocks never share results.
   - Probe, passing: the hour [B50, B100) after [B100, B200) prices VVV at 1500, which is B50/B100's data and not the
     cached B200 data. That is 3 multicalls for 2 hours, and a third hour spanning two cached blocks costs 0.
   - Cache issues in Minor 2 and Minor 4.

### Strengths

- Data failures are separated cleanly from config errors. Data failures become misses with a reason. Config errors
  throw `OrionError` and are re-thrown from the decode catch (:441-443).
- A wrong row in `QUOTE_TOKENS` cannot misprice: the pool's own token0/token1 are read every hour and must equal the
  priced token and the quote.
- Quote-order resolution is a small fixed-point loop with cycle detection (:497-507). A quote ref outside `entries`
  degrades to `quote_missing`, not a throw.
- The v2 fold test is well designed. A swap in the middle of the hour and a last touch before B(H) make the result
  without the fold (0.0317) clearly different from the result with it (0.055). The report says mutation runs confirmed
  this.
- The test that every usd_feed pool method in prices.yaml has a quote-token row guards the table against config drift.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)

1. **evmMethods.ts:239.** A `usd_feed` quote records only `{feed, usd}` in the row's detail. It does not record the
   feed's `updated_at` or `feed_age_s`.
   - Probe: with ETH/USD (Base) 10 h stale, VVV is priced 19.4017 with `detail.quote = {feed, usd: 3000}` and no age.
   - Review Focus 3 is met for feeds that are a primary or check: CAKE, LINK, and CRV's check carries age in
     `detail.check`.
   - A stale quote feed under VVV, AERO, DIEM, LINK's check, or the R5 off-chain refs (USDC/USD, 24 h heartbeat) leaves
     no trace of its age.
   - Fix: keep each feed's `decodeFeed` detail in a map next to `feedUsd`, and spread `updated_at`/`feed_age_s` into
     `quote`.
2. **evmMethods.ts:415.** Per-call failures are cached together with successes, including `'no result'` and transport
   `pickValue` errors.
   - With the writer's shared cache, a failed B(H+1h) read of hour h is reused as B(H) of hour h+1.
   - This is correct for reverts, which are deterministic per block. A transient multicall sub-call failure would spread
     to the next hour.
   - Consider not caching `ok:false` results, or document it.
3. **evmMethods.ts:324.** For v4, the side comes from address order against the `QUOTE_TOKENS` USDC, and nothing checks
   that `pool_id` really is LIT/USDC. The report discloses this.
   - It is acceptable because the only use is LIT's check, never a primary.
   - A comment at the v4 case saying "unverifiable: StateView exposes no pool key, check-only" would stop a later
     primary use.
4. **evmMethods.ts:398.** `keyOf` leaves out `signature`, so two calls with the same address, function, args and pick
   but different return signatures would share one cached result. There are no collisions today.
   - Adding the signature costs nothing.
5. **tests/prices/evmMethods.test.ts:277-289.** The cache test asserts only the multicall count and
   `prices.has(VVV)`. It does not check that the older hour used B(H-1h)/B(H) values.
   - A cache that wrongly served the wrong block's data would still pass.
   - Assert the value: with the fixture's 10/20 cumulatives it is 0.5 WETH x 3000 = 1500. My probe confirms the code is
     right.
6. **Coverage gaps.** There are no committed tests for:
   - a pool token mismatch -> `bad_read`
   - an unknown usd_feed -> throw
   - a zero/negative feed answer -> miss
   - zero reserves

   All four were confirmed by my probes. Add them so they stay fixed.
7. **evmMethods.ts:310.** The mean tick is a float, while OracleLibrary floors toward -∞. The difference is ≤0.01%
   (disclosed). It only matters if a check tolerance ever approaches 0.01%; stables use 0.5%.

### Assessment

**Task quality:** Approved

**Reasoning:** Every method's arithmetic matches an independent recomputation from raw inputs and every failure mode I
probed produces a miss, not a number. AERO's decoders moved byte-identically and its tests are unchanged and green.
The remaining items are traceability (quote feed age) and cache and test hardening, not wrong prices.
