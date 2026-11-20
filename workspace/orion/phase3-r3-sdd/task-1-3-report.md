# Tasks 1-3 report (Phase 3 R3: view_sum extensions, hype.circulating_supply, solana.supply_less_owners)

Branch feat/phase3-r3-supply, worktree .worktrees/phase3-r3, base 84cc9d2. Three commits, one per task, each green
(full suite + typecheck before each commit). No asset YAML touched, no push/merge, no network, no live DB, node_modules
never staged (explicit `git add <paths>` only).

| commit | subject |
|---|---|
| 82dd4e4 | feat(ingest): view_sum times terms and locked_schedule |
| 61e4c7d | feat(hype): circulating supply from Hyperliquid less the genesis wallets |
| 5a68aff | feat(solana): supply less named owners' balances |

## Task 1: `chain.view_sum` `times` + `locked_schedule` (src/ingest/adapters/evm.ts)

- Term `times?: { contract, function, decimals }`: the term's raw value x the view's raw value / 10^decimals (bigint, exact
  truncation). Each times call goes into the **same multicall** at the run block as the terms (pinned:
  `rpc.stats.multicall === 1`). Any failed call (term or times) throws via `readAt`, naming the call: the level fails,
  never a partial sum (Review Focus 2, pinned for a reverting term, a reverting times view, and a plain reverting term).
- `locked_schedule?: { amount, first_tranche: YYYY-MM-DD, tranches, every_months, citation }`: value = sum - amount x
  (tranches - k)/tranches, k = tranches with day `addMonthsUtc(first_tranche, i x every_months)` 00:00Z <= the run block's
  timestamp. Refused when the result is negative. Month rule (code comment on `addMonthsUtc`): calendar months on the
  UTC day, day-of-month kept, clamped to the month's last day only if the month lacks it; every tranche counted from
  the first tranche, so a clamp never carries (2027-01-29 +1 = 2027-02-28, +2 = 2027-03-29).
- Pinned values (36 tranches of 500e6 from 2027-01-29, monthly): 2026-11-19 -> 500,000,000 locked; 2027-01-28T23:59Z ->
  500,000,000; 2027-01-29T00:00Z -> 486,111,111.111 (35/36); 2029-12-28T23:59:59Z -> 500e6/36; 2029-12-29T00:00Z -> 0;
  2031-06-01 -> 0. Feb clamp: 2027-02-27T23:59:59 -> 35/36, 2027-02-28T00:00 -> 34/36, 2027-03-28T23:59:59 -> 34/36,
  2027-03-29 -> 33/36; also a quarterly schedule from 2027-11-30 (2028-02-29 leap clamp, then 2028-05-30 unclamped).
- Validation (strict): unknown keys in `times` / `locked_schedule` refused by name; times needs contract name, function
  name, decimals 0..36; schedule needs amount > 0, a real calendar day (2027-02-30 and ISO timestamps refused), tranches
  integer 1..1200, every_months integer 1..120, citation an http(s) URL. **Design choice:** `locked_schedule` is refused
  together with `scale` or `plus_share` (the schedule is in result tokens; mixing units would be ambiguous). LIT needs
  neither.
- Detail: a term with times appends ` x st_ycrv.pricePerShare() <raw>/1e18`; the schedule appends
  ` - locked_schedule 500000000 x 35/36 = 486111111.1111111 (1 of 36 tranches out, every 1 months from 2027-01-29; <citation>)`.
  A view_sum without the new params produces the exact same detail as before (pinned).
- paramsDoc extended as the plan says. **This moved tests/agent/golden/packs-13.json** (aero's pack: the two
  `chain.view_sum` adapter_params `params_doc` strings; nothing else). I replaced exactly those two strings (count
  verified = 2) and added a paragraph to the packGolden.test.ts header saying so, following the R2 precedent. No hash
  pin moved (AERO's tests and every config-hash/report pin unchanged; full suite green).
- `yaml` v2 parses an unquoted `first_tranche: 2027-01-29` as a string (checked), so Task 4 can write it unquoted.

RED: `npx vitest run tests/ingest/adapters.evm.test.ts` -> 6 failed | 17 passed (times not applied: 9000 vs 7320; revert
not failing; locked 0; validate refused `terms[1].times`). GREEN: 23/23.

## Task 2: `hype.circulating_supply` (src/ingest/adapters/hype.ts)

- Params `{ subtract: contract names (non-empty, unique), url? (https) }`, strict validateParams. URL resolution is the
  same `infoUrl` as hype.total_supply (params.url, else external_ids.hyperliquid_info, else DEFAULT_INFO_URL).
- One `spotMetaAndAssetCtxs`; HYPE found in `meta.tokens` by name 'HYPE' (refused if none or more than one), its pair
  against quote token 0 derived from `meta.universe` (pinned with HYPE re-indexed to 151 / pair `@300`), the matching
  context's `circulatingSupply` (decimal string; missing/non-numeric refused by name). Then per wallet
  `spotClearinghouseState` (HYPE `total`, existing `balanceAt`) + new `stakedAt` = `delegatorSummary` `delegated +
  undelegated + totalPendingWithdrawal`. Unknown wallet: `{balances: []}` and a zero / `{}` / `null` summary = 0. A
  summary missing a field, non-numeric or negative is refused by name. Value refused <= 0. Stamped `api` at fetch time.
- Refactor: the spot-meta fetch and pair lookup were split out of `totalSupply` into `spotMeta` + `pairContext`, shared by
  both adapters; hype.total_supply's behaviour and every error message are unchanged (its tests untouched and green).
- Fixture: circ 301,557,370.473276; foundation spot 0.00000044 + delegated 60,642,286.11; grants spot none + delegated
  2,979,878.37 -> **237,935,205.99327556** (pinned to 6 dp, and ~237,935,206). Spot-only, staked-only (incl. undelegated),
  pending-withdrawal-only, mixed and unknown wallets all pinned (Review Focus 4). Request sequence pinned (5 POSTs).
- Registered: ADAPTER_SOURCE_TYPES `first_party_api`; ADAPTER_ENDPOINTS in tools/sources-register/generate.ts; sample in
  tests/provenance/adapterOrigins.test.ts; WRITERS list in tests/provenance/origin.test.ts. docs/ops/sources-register.md
  regenerated: no change (no asset uses the adapter yet).
- Test helper change: the hype test's `info` route now keys `delegatorSummary` by user too, and looks up overrides with
  `in` instead of `??` so a route can answer `null`.

RED: 6 failed | 11 passed (unknown adapter). GREEN: 17/17.

## Task 3: `solana.supply_less_owners` (src/ingest/adapters/solana.ts)

- Params `{ mint: contract name (required), subtract: owner contract names (non-empty, unique), rpc_url_env? (env var
  name) }`, strict validateParams. `tokenSupply(mint)` - sum of `ownerBalance(owner, mint)` (existing transport, all of an
  owner's token accounts, finalized); RPC via the existing `rpcUrl` (ORION_SOL_RPC_URL default). Refused <= 0. Stamped
  `onchain` at fetch time. Detail names the supply + slot and each owner name, address, balance and slot.
- R8: a resolved RPC URL on a pump.fun host is refused before any request (local guard; the transport's FORBIDDEN_HOST is
  not exported and I did not change the transport). Test pins that all 7 calls go only to ORION_SOL_RPC_URL's host.
- Fixture: supply 821,771,911,575.12; custodian 229,261,858,182.10 split over two token accounts; vaults 80e9, 35e9,
  25e9, 25e9, 24e9 (task-4-values owners) -> **403,510,053,393.02**. Owner with no accounts = 0; result <= 0 refused;
  transport error on either call fails the level with only the RPC origin in the message.
- Registered: ADAPTER_SOURCE_TYPES `contract_state`; **ADAPTER_ORIGINS 'onchain' in src/provenance/origin.ts** (not in the
  plan's file list, but required: tests/provenance/origin.test.ts pins that every contract-state adapter is declared);
  ADAPTER_ENDPOINTS `solRpc`; samples/lists in adapterOrigins.test.ts and origin.test.ts. Register regenerated: no change.

RED: 6 failed | 15 passed (unknown adapter). GREEN: 21/21.

## Full runs (ORION_TEST_DATABASE_URL set, `npx vitest run --maxWorkers=2`, `npm run typecheck`)

- Before commit 1: first run 1 failed | 1983 passed (tests/agent/packGolden.test.ts "every asset: the whole pack": the
  paramsDoc move above); after the golden update 154/154 files, **1984/1984**, typecheck clean.
- Before commit 2: 154/154 files, **1991/1991**, typecheck clean.
- Before commit 3: 154/154 files, **1998/1998**, typecheck clean.
- No load-sensitive file failed in any run.

## Self-review / concerns

1. packs-13.json golden moved (aero pack, view_sum params_doc text only) because the plan asks for the paramsDoc change.
   Not a hash pin, but flagged. Task 4 will move more packs anyway (assets gaining view_sum / the new adapters).
2. `locked_schedule` refuses `scale` / `plus_share` alongside it (my choice; not in the plan).
3. src/provenance/origin.ts edited (one line) outside the plan's Task 3 file list: needed for the existing origin tests.
4. The sources register lists endpoints only; a `locked_schedule` citation URL on a `chain.view_sum` source is not
   listed in the register (unlike schedule.unlocks_next_year). Task 4/6 may want it there.
5. Scoping suggested also refusing HYPE circ above total_supply; the plan says only <= 0, so not added.
6. hype.circulating_supply picks the token by name 'HYPE' (as ruled), not by `external_ids.hyperliquid_token`; a second
   token named HYPE is refused rather than guessed.
