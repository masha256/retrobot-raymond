# Review: Phase 3 R3 Tasks 1-3 (84cc9d2..5a68aff: 82dd4e4, 61e4c7d, 5a68aff)

### Spec Compliance

- ✅ Spec compliant (Tasks 1, 2, 3; Review Focus 2, 3, 4; rulings R1, R2, R7).
  - Task 1: `times` per term (evm.ts:12-23, 36-44, 116-123), `locked_schedule` (evm.ts:46-56, 89-106, 131-137), detail
    gains times value and locked amount (evm.ts:136, 140), paramsDoc extended (evm.ts:153-154). Plan's Step 1 cases all
    pinned (adapters.evm.test.ts:480-568). Test file is the existing `tests/ingest/adapters.evm.test.ts` (plan allowed
    "extend the existing view_sum tests").
  - Task 2: hype.ts:233-299; registered sourceTypes.ts:399, generate.ts:932; all Step 1 cases pinned
    (adapters.hype.test.ts:658-731).
  - Task 3: solana.ts:318-361, 370-376; sourceTypes.ts:407, generate.ts:940; all Step 1 cases pinned
    (adapters.solana.test.ts:814-858).
  - R1 (one implementer, three commits, shared one-liners): matches the commit list. R2 (single-amount LIT form): the
    schedule is single-amount only. R7 (month clamp): evm.ts:89-96, pinned at test:517-529.
- Extra (accepted, Minor): `locked_schedule` is refused together with `scale` / `plus_share` (evm.ts:78-79). Not in the
  plan; harmless (LIT uses neither) and the reasoning (mixed units) holds.
- Extra (required): `src/provenance/origin.ts:387` outside the Task 3 file list. Checked: tests/provenance/origin.test.ts:78-83
  asserts ADAPTER_ORIGINS keys == every `contract_state` adapter (+ retired), so a new contract_state adapter without
  this line fails that test. Required.
- ⚠️ Cannot verify from diff: R5 relies on the rebuild (Task 5) setting `ctx.block` per row; `locked_schedule` reads
  `chain(ctx).block.timestamp` (evm.ts:112, 133) so it will follow, but that is Task 5's to pin. Also Review Focus 1
  (a term whose contract has no code at an old block: does multicall return `ok:false` or decode garbage?) is Task 5's.

### Named risks

1. **view_sum** — PASS.
   - Reverting term or `times` view fails the level: all calls go through `readAt` (evm.ts:51-58 throws on any `!r.ok`,
     naming the call); pinned for a reverting term, a reverting times view and a plain term (test:487-493).
   - `times` in the same multicall/block: pushed onto the same `calls` array, one `readAt(ctx, block.number, calls)`
     (evm.ts:116-118); `rpc.stats.multicall === 1` pinned (test:483).
   - Integer math: term x times / 10^decimals in bigint (evm.ts:121), signed sum bigint, the only float conversion is the
     existing `unitsToNumber` (evm.ts:129). The schedule is subtracted after, in float tokens (by design: `amount` is a
     number of tokens).
   - AERO byte-identical: without `times`, `term(i) = values[i]` and the parts string is the old one plus `''`
     (evm.ts:140-141); `schedule = ''` when absent; pinned exactly (test:535-540); tests/assets/aero.ingest.test.ts green.
     Config hash: paramsDoc is read only by src/agent/context.ts:152-155 (the agent pack), never hashed; no hash pin file
     in the diff.
2. **locked_schedule** — PASS.
   - Boundaries pinned: 2027-01-28T23:59Z 500M, 2027-01-29T00:00Z 35/36 (= 486,111,111.111), 2029-12-28T23:59:59Z 1/36,
     2029-12-29T00:00Z 0, 2031-06-01 0 (test:503-515). Comparison is `<=` at 00:00Z (evm.ts:104).
   - Feb clamp: 2027-02-28 -> 34/36, 2027-03-29 -> 33/36, and a leap-year quarterly case where the clamp does not carry
     (test:517-529); `addMonthsUtc` always offsets from `first_tranche` (evm.ts:104).
   - Evaluated at the block timestamp, not `nowIso` (evm.ts:133, `block.timestamp * 1000`); tests drive it only via the
     fake block's time (test:459-466).
   - Negative refused (evm.ts:135; test:531-533). Locked never negative: k <= tranches.
3. **hype.circulating_supply** — PASS.
   - HYPE located by name in `meta.tokens` (exactly one, hype.ts:280-283), pair derived from `meta.universe`
     (`pairContext`, hype.ts:198-206); re-indexed to token 151 / `@300` pinned (test:697-706).
   - spot + delegated + undelegated + totalPendingWithdrawal summed (hype.ts:289-292); each shape pinned (test:679-695).
   - Unknown wallet: `{balances: []}` -> 0 (existing balanceAt), `null` / `{}` / zeros -> 0 (hype.ts:235); partial or
     negative summary refused by name (hype.ts:238-243; test:724-727).
   - Parsing: `toFiniteNumber` (units.ts:8-13) rejects '' and non-numeric; double precision is ~1e-7 at 3e8, ample.
   - Requests: exactly 1 + 2N, pinned as the full call list (test:670-676).
4. **solana.supply_less_owners** — PASS.
   - Owners, not accounts: `ownerBalance` (transport/solana.ts) is `getTokenAccountsByOwner(owner, {mint})` summed over
     every returned account with bigint-exact `uiAmount`; two-account custodian pinned (test:780, 831-832); the
     `{ mint }` filter and `finalized` asserted inside the fake (test:794-795).
   - Only ORION_SOL_RPC_URL's host: 7 calls, one host (test:848-853); a pump.fun URL refused before any request
     (solana.ts:343-349; test:855-857). Note: with ORION_SOL_RPC_URL unset, `solanaRpcUrl` falls back to the public
     `api.mainnet-beta.solana.com` — same as the existing solana adapters, not a pump.fun host; acceptable.
   - Refuses <= 0 (`!(value > 0)`, solana.ts:359; test:836-837).
5. **Golden / pins** — PASS. `git diff --name-only` shows the only fixture/golden file is tests/agent/golden/packs-13.json,
   4 changed lines = the two AERO `chain.view_sum` `params_doc` strings (diff:419-426), matching the new paramsDoc
   verbatim. No hash pin moved. origin.ts line required (see above).

Focused run (ORION_TEST_DATABASE_URL set, --maxWorkers=1): adapters.evm, adapters.hype, adapters.solana,
provenance/origin, provenance/adapterOrigins, agent/packGolden, assets/aero.ingest — 7 files, 135/135 passed, no warnings.

### Strengths

- The `times` view rides the same multicall via `calls.push(...) - 1` index mapping, so atomicity at one block is
  structural, not by convention (evm.ts:116-118).
- `addMonthsUtc` is small, documented with the R7 examples, and always counts from the first tranche (no clamp drift);
  boundary tests hit the exact second either side.
- The HYPE refactor (`spotMeta` + `pairContext`) removes what would otherwise be a duplicated meta/pair block while
  leaving hype.total_supply's messages and tests unchanged.
- Strict validators with by-name errors; tests check the exact error text for unknown keys.
- Solana error path keeps the keyed URL out of messages (pinned `not.toContain('SECRETKEY')`).

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)
1. solana.ts:319 duplicates the transport's `FORBIDDEN_HOST` regex (transport/solana.ts, `const FORBIDDEN_HOST`, not
   exported) and throws a plain `Error` where the transport throws `OrionError('forbidden_price_host')`. Two copies of
   an R8 guard can drift; export the regex (or a `assertNotPumpFun(url)` helper) from the transport and reuse it.
2. `isName` is now defined three times with the same regex (evm.ts:20, hype.ts:138, solana.ts:320). Move it to
   adapters/chain.ts next to `text` and import it.
3. hype.ts:293 / test:667: the detail prints `spot 4.4e-7` (JS default number formatting). Harmless for provenance but
   inconsistent with the decimal strings elsewhere; consider printing the reply's own string.
4. solana.ts:350-357: the supply and each owner balance are separate finalized reads at different slots (pinned as
   380000100 vs 380000101). Inherent to the RPC; the detail records each slot, so this is only a note for Task 4's
   PUMP watch (a transfer between reads can skew one day's value).
5. The `locked_schedule.citation` URL is not surfaced by tools/sources-register (ADAPTER_ENDPOINTS for chain.view_sum
   lists none), unlike `schedule.unlocks_next_year` (generate.ts:937). Implementer flagged it; Task 4/6 should decide
   whether the register lists it.
6. evm.ts:135 refuses `value < 0` only; a result of exactly 0 passes. Matches the plan ("refused when negative"), but
   hype/solana refuse `<= 0`; a 0 circulating supply is never real, so `<= 0` would be the consistent guard.

### Assessment

**Spec compliance:** ✅ Spec compliant (one accepted extra: schedule vs scale/plus_share refusal; origin.ts line required).

**Task quality:** Approved

**Reasoning:** All five named risks pass on code reading and are pinned by real-behaviour tests through fakeRpc / fake
HTTP; AERO's output and hashes are untouched and the only golden move is the two paramsDoc strings. Remaining items are
small DRY/consistency polish.
