# Task 1 report: central prices.yaml, schema/loader, config-hash wiring

**Status: NEEDS_CONTEXT. Nothing is committed.** The implementation, tests and re-pins are finished in the worktree. Five
exact values that the brief says to copy from `hype-lit-pump.md` are truncated in that file (written as `0x7fFE42C4…7227`
and similar). I did not look them up elsewhere and did not invent them. They are in `prices.yaml` as
`MISSING_FULL_VALUE(<truncated form>)`, so `loadPrices` refuses the file and names each field (output below).

## Blocker: values needed (full strings)

| prices.yaml field | truncated form in hype-lit-pump.md |
|---|---|
| LIT `check.state_view` (Uniswap v4 StateView, Ethereum) | `0x7fFE42C4…7227` |
| LIT `check.pool_id` (v4 LIT/USDC 0.3% pool id, 32 bytes) | `0x8366b1dd…cc00f1` |
| PUMP `primary.base_vault` (PumpSwap pool_base_token_account) | `8TqK4PL3…9bhC` |
| PUMP `primary.quote_vault` (PumpSwap pool_quote_token_account) | `68Vdm7mQ…dr8t` |
| PUMP `check.pair` (Meteora DLMM PUMP/USDC bin-20 lb_pair) | `9SMp4yLK…KoZj` |

The refusal on the current file:
```
prices.yaml: eip155:1/0x232c…4ee2.check.state_view: must be a 20-byte 0x address
prices.yaml: eip155:1/0x232c…4ee2.check.pool_id: must be a 32-byte 0x id
prices.yaml: solana:mainnet/pumpCm….primary.base_vault: must be a base58 Solana address
prices.yaml: solana:mainnet/pumpCm….primary.quote_vault: must be a base58 Solana address
prices.yaml: solana:mainnet/pumpCm….check.pair: must be a base58 Solana address
```
While the placeholders are in place, every `loadAsset` throws `invalid_price_config`, so the suite fails in the worktree.

**To finish the task once the values are known:**
1. Replace the five placeholders in `prices.yaml`.
2. Recompute the LIT and PUMP hashes, which are the only pins that depend on those values. For example:
   `npx tsx -e "import {loadAsset} from './src/config/load.js'; for (const id of ['lit','pump']) console.log(id, loadAsset('.', id).hash)"`.
3. Put the new hashes in place of the provisional pins: LIT `4fcb90ae…` in tests/assets/lit.ingest.test.ts,
   tests/agent/disclosure.e2e.test.ts (LIT_HASH) and tests/config/load.test.ts; PUMP `9fffd887…` in
   tests/assets/pump.ingest.test.ts.
4. Run the two focused files, the full suite and typecheck.
5. Stage the explicit paths listed under Files and commit `feat(prices): central prices.yaml with one method and one
   check per token ref`.

## What was built

- **`prices.yaml`** (repo root) has 17 refs, keyed by token ref. It uses the table values verbatim, the AERO pools and
  feed from aero.yaml, and the HYPE, LIT and PUMP values from hype-lit-pump.md. The `valid_from` values follow Ruling R2
  (EVM refs 2025-10-13; AERO 2026-09-23; HYPE and LIT 2026-10-01; PUMP 2026-10-12). The header comment says that
  valid_from is "the first hour Orion writes for this ref". It also documents the fields, the hour semantics (P2) and
  Ruling R5 (the off-chain primaries name the Ethereum USDC/USD feed 0x8fFf…18f6 as `usd_feed`). Feeds appear only as
  `feed`/`usd_feed`, never as refs.
- **`src/prices/config.ts`**:
  - Zod strict nodes, with a `kind`-discriminated `PriceMethod` and a check node that is a method plus `tolerance_pct`,
    `consecutive` (default 1) and `label`.
  - `parsePrices(obj, where)`, plus `loadPrices(rootDir)`, which returns an empty map when the file is missing.
  - `entriesFor(asset, prices)`, `methodSource(m)` and `quoteRefOf(m)`.
  - Every refusal is an `OrionError('invalid_price_config')` naming `<ref>.<field>`. Refused: unknown keys, a tolerance
    <= 0, a missing tolerance, a tolerance on a `bound`, an address that is not 20 bytes, a pool_id that is not 32
    bytes, a malformed Solana address, a ref key that is not a lowercase token ref, a ref prefix that contradicts
    `chain`, a primary kind not read on `chain`, a `bound` used as primary, min >= max, a quoted method with both or
    neither of quote_ref/usd_feed, an unresolved quote_ref, a self-reference, and a cycle (over primary and check quote
    refs).
- **`src/config/load.ts`**: `parseAssetObject(obj, prices?)` and `parseAssetYaml(text, prices?)`. `loadAsset(home, id)`
  passes `loadPrices(home)`. The hash input is `{ config, prices: entriesFor(config, prices) }`, with the entries sorted
  by ref. When there are no entries (no map, or no ref matches), the hash is `sha256(canonicalJson(config))` exactly as
  before. That keeps MINI and every test-home asset on its old hash ("absent changes nothing").
- **`src/config/sources.ts`**: `transfer_flow.share_price.underlying` is an optional contract name with no default.
  It is checked against `contracts` through `contractNames`. `price_coingecko_id` is untouched. The brief's file list
  names schema.ts, but the share_price schema lives in sources.ts, which schema.ts imports.

## Decisions to review (deviations from the brief's interface)

1. **`chain` union adds `'lighter'`** (per the controller ruling). LIT's ref is `eip155:1/0x232c…4ee2`, but its chain is
   `lighter` because chain means where the PRIMARY is read. The ref/chain rule is:
   - `eip155:N` refs need chain `eip155:N`, or `lighter`, the one off-chain venue that prices an EVM ref;
   - `solana:mainnet/…` refs need chain `solana`;
   - `hyperliquid:spot/@N` refs need chain `hyperliquid`.

   The primary kind must also fit the chain: EVM kinds on eip155, the `solana_*`/`meteora_dlmm` kinds on solana,
   `hyperliquid_candle` on hyperliquid, `lighter_candle` on lighter. The check's chain is not a field. An on-chain check
   on LIT (v4) is read on its ref's chain (eip155:1).
2. **`curve_oracle` takes `quote_ref` OR `usd_feed`** (exactly one). The brief gives only `quote_ref`, but CVX (× ETH/USD)
   and the crvUSD check (× USDT/USD) are quoted in feeds, which the ruling says are never refs. The same exactly-one rule
   applies to `v2_twap`, `v3_twap`, `v3_spot` and `v4_spot`.
3. **New kind `v3_spot {pool, quote_ref?|usd_feed?}`** for the AERO check. The table says "price_check_pool spot", and
   today's AERO check is `chain.cl_pool_spot_price`. `v3_twap` would have changed the method, so Task 2 must implement
   `v3_spot` (Slipstream `slot0`).
4. **`curve_get_dy` takes an optional `dx`** (tokens of coin i): 100 for cvxCRV and 10 for yCRV, from wrappers.md
   (`get_dy(1,0,100e18)` / `get_dy(1,0,10e18)`), with i=1, j=0.
5. **`hyperliquid_candle` and `lighter_candle` take a required `usd_feed`** (Ruling R5). HYPE's check carries the same
   feed.
6. **`bound` has no `tolerance_pct`.** Its band is the tolerance. It loads as `tolerancePct: 0` (documented as unused) to
   keep `PriceEntry.check.tolerancePct: number`.
7. **How an asset's refs are found (`entriesFor`).** Every `contracts` address becomes a token ref: on the asset's
   `ingest.chain_id`, or `solana:mainnet/` when `chain: solana`. The entry whose `symbol` equals the asset's symbol is
   added too, because HYPE has no address ref. Quote refs are then added transitively. Results:
   - ycrv → CRV, crvUSD, yCRV;
   - aero → AERO;
   - vvv → VVV, DIEM;
   - cvxcrv → cvxCRV, CRV, crvUSD, CVX.

   A crvUSD edit moves exactly crv, cvxcrv, sdcrv and ycrv, and an AERO edit moves only aero (both tested).
8. **Decimals.** 18 for every ERC-20, which is standard for these tokens and not re-measured. PUMP is 6 (pump.yaml). HYPE
   is 8, its HyperCore wei decimals (src/ingest/adapters/hype.ts).
9. **`loadPrices` on a root with no prices.yaml returns an empty map**, which gives config-only hashes. Test homes rely on
   this.

## Tests

RED (before src/prices/config.ts existed; the draft was moved aside, and the tests were written and run first):
```
FAIL tests/config/load.test.ts  Error: Cannot find module '../../src/prices/config.js'
FAIL tests/prices/config.test.ts Error: Cannot find module '../../src/prices/config.js'
Test Files 2 failed (2)  Tests no tests
```
GREEN (with well-formed stand-in values in the five placeholder fields, restored afterwards):
- `npx vitest run tests/prices/config.test.ts tests/config/load.test.ts --maxWorkers=1`: 2 files, 42/42 passed.
- `npx vitest run --maxWorkers=2`: **145 files, 1765/1765 passed** (the baseline was 144 files and 1745 tests; this task
  adds 20 tests and 1 file). No load-sensitive file failed.
- `npm run typecheck`: clean.
- `python3 -m unittest scripts/provision/test/test_orion_remote.py`: 52 OK.

With the placeholders restored (the current worktree state), the suite fails wherever an asset is loaded from the repo
root. That is expected until the values come in.

New tests:
- **tests/prices/config.test.ts:**
  - the committed file has the 17 refs with their symbols;
  - every quote_ref resolves, and DIEM is quoted in VVV;
  - the valid_from values follow R2;
  - LIT, HYPE and PUMP chains and methods, with the R5 feed;
  - tolerances, sdCRV's bound, and the 2-consecutive get_dy checks;
  - the AERO pools match aero.yaml;
  - `entriesFor` for ycrv, aero, hype, pump and vvv;
  - `methodSource`;
  - refusals by name: self-ref, cycle, missing quote ref, unknown key (entry and method), tolerance 0 and -1, missing
    tolerance, tolerance on a bound, a 19-byte address, a chain/ref contradiction (CAKE, HYPE), a lighter_candle on
    eip155:1, an uppercase ref, a bound primary, both quotes;
  - a root without the file gives an empty map.
- **tests/config/load.test.ts:**
  - the hash is `sha256(canonicalJson({config, prices: entriesFor}))`, and the config-only hash is kept without
    prices.yaml;
  - every real asset's hash differs from its config-only hash;
  - a crvUSD edit moves exactly crv, cvxcrv, sdcrv and ycrv; an AERO edit moves only aero;
  - `parseAssetObject(obj, prices)` equals `loadAsset`;
  - `share_price.underlying` is accepted and checked against contracts.

## Pins moved (all old asset hashes are gone from tests: `grep -rl <old> tests src` finds nothing)

The pins used `parseAssetYaml(text).hash`, which is now the config-only hash. I repointed each one to `loadAsset(ROOT,
id).hash`, the production hash that observations and the registry store, and added a "Re-pinned (Phase 3 R2 Task 1)"
comment. The parseAssetYaml/readFileSync imports that became unused were removed. No golden embeds an asset configHash:
the suite passed unchanged before the re-pin. No golden content changed.

| asset | old | new | where |
|---|---|---|---|
| aero | 3c413feb… | 035327b9eec2de16fb96541b2b09dfc5a52015fd4ef6a246691e5cb8bcf6578d | tests/assets/aero.ingest.test.ts, tests/config/load.test.ts |
| cake | 5434fc56… | 86b98b90382d270cdee19e8ad1e0d65dd4935e7bb857bb819bcfb751f3e1668f | tests/assets/cake.ingest.test.ts |
| crv | 7b4e1b57… | 5e797f7ca2acaac63549bc7042ea77a96e963964a6f51e680f0b3aa05475f361 | tests/assets/crv.ingest.test.ts |
| cvxcrv | 372064fc… | e4eed3b4b90c651da366cfc0ad51e5cca06adc7cbfad537b3b4a9beb14a1932d | tests/assets/lockers.ingest.test.ts |
| hype | 492438a0… | 2ec7d2cefc9ba484c8529e4c47db7b5b5a5210c7c9697df209839edd45303c37 | tests/assets/hype.ingest.test.ts, tests/config/load.test.ts |
| link | 3d098a29… | de8fdaa00cc4edca64269d723b668e94512aa1fcc4862e2979dc68dc33032324 | tests/assets/link.ingest.test.ts |
| lit | 0de769be… | **provisional** 4fcb90ae8e47f49345a6a75fd253824903146841a2211741129fd5b9e79bcd49 | tests/assets/lit.ingest.test.ts, tests/agent/disclosure.e2e.test.ts (LIT_HASH), tests/config/load.test.ts (x3) |
| pump | 4a9e1eba… | **provisional** 9fffd887902b5b647b8bcfceaa38ebd12e7cccfc2f55cf0e2d469e2f27ef011e | tests/assets/pump.ingest.test.ts |
| sdcrv | 0ba07bec… | 20de7d924c8f1f49361b08042d5dc78027d44785f4f7468172405301228486fd | tests/assets/lockers.ingest.test.ts |
| sky | ccfb251b… | 9d97775d492bb27d81d84f7558f35b724faab7a390d892899c6fb19bfd0cfa3d | tests/assets/sky.ingest.test.ts |
| uni | 2c0f3c2c… | 255b8a06512f32845fe375d2e1195086561f0847994e0bfd695ca115481cd9fa | tests/assets/uni.ingest.test.ts |
| vvv | 45ad0a3a… | d8223609d9e3f8532e51cd8529340ea38d8264d6d4d33892eedb13e3f69cff1e | tests/assets/vvv.ingest.test.ts, tests/config/load.test.ts |
| ycrv | cca3f10e… | fad46ffce87b17c118c61ff677f180f10bf08b319e2694a8634e013310f7b665 | tests/assets/ycrv.ingest.test.ts |

The LIT and PUMP pins were computed with stand-in values in the five fields. They must be recomputed after the real
values go in. The other 11 assets' entries do not include LIT or PUMP, so their pins are final. MINI's pin
(5b2f690b…) does not move.

## Files (to stage explicitly)

- New: `prices.yaml`, `src/prices/config.ts`, `tests/prices/config.test.ts`.
- Modified: `src/config/load.ts`, `src/config/sources.ts`, `tests/config/load.test.ts`.
- Pins: `tests/assets/{aero,cake,crv,hype,link,lit,lockers,pump,sky,uni,vvv,ycrv}.ingest.test.ts`,
  `tests/agent/disclosure.e2e.test.ts`.

## Self-review and concerns

- **The release pack omits prices.yaml.** `scripts/release/pack.sh` ships only `schedule.yaml` among the root config
  files, and tests/release/pack.test.ts pins that list. A release would therefore have no prices.yaml: `loadPrices`
  returns empty, and production hashes fall back to config-only, unlike dev. Both files are outside this task's list.
  pack.sh plus its test must add `prices.yaml` in Task 1 or a follow-up before the writer ships.
- **One bad prices.yaml blocks every asset.** `loadAsset` now throws `invalid_price_config` for every asset, including
  in `asset validate`. `asset validate` does not list prices.yaml as its own row, the way it does schedule.yaml. That
  could be added later in src/cli/commands/asset.ts, also outside this task.
- **`loadAsset` re-reads prices.yaml on every call.** That is fine at 13 assets, and caching was left out on purpose.
- **Symbol matching in `entriesFor`** depends on an asset's `symbol` equalling the entry's symbol, which is true for all
  13 assets. Only HYPE needs it; every other asset matches through its addresses too.
- **The interface deviations in items 2-6** add work for Task 2: `v3_spot`, `dx`, and `usd_feed` on curve_oracle and
  the candles.

## Continuation (second implementer, 2026-11-14)

**Status: DONE.** The previous attempt's work was kept as-is and finished.

### What changed
- **Five values** (task-1-values.md, verified on chain by the controller) replace the `MISSING_FULL_VALUE(...)` placeholders
  in `prices.yaml` verbatim: LIT `check.state_view` 0x7fFE42C4a5DEeA5b0feC41C94C136Cf115597227, `check.pool_id`
  0x8366b1dde4de12c8806985fbb599d408d92d01a6faf2e478cc6bb76189cc00f1; PUMP `primary.base_vault`
  8TqK4PL3x7zWR2dNinr1LMi8Uf4vTRSFE2Ev1yYW9bhC, `primary.quote_vault` 68Vdm7mQJ7RBxWioLVEUXbeTTpTtyiR1CL9vLRxmdr8t,
  `check.pair` 9SMp4yLKGtW9TnLimfVPkDARsyNSfJw43WMke4r7KoZj. A test pins each.
- **Validator:** Solana addresses must decode from base58 to exactly 32 bytes (`base58ByteLength`, exported from
  src/prices/config.ts; the message is now "must be a base58 32-byte Solana address"). The v4 `pool_id` stays a 32-byte
  0x hex (now tested).
- **Pins:** LIT 4fcb90ae… -> 300863b835e7243c5238d7a0ef377d1a71ba0f977282b88460bb8919aa0d77f5 (lit.ingest, disclosure.e2e
  LIT_HASH, config/load x3); PUMP 9fffd887… -> a616f10dacc988b44e484c79d408cc6cb45214d819853be5fd7b4cbe9a0644bf
  (pump.ingest). The other 11 recomputed with `loadAsset` and match the previous table exactly (aero 035327b9…, cake
  86b98b90…, crv 5e797f7c…, cvxcrv e4eed3b4…, hype 2ec7d2ce…, link de8fdaa0…, sdcrv 20de7d92…, sky 9d97775d…, uni
  255b8a06…, vvv d8223609…, ycrv fad46ffc…). No provisional hash is left in tests or src.
- **R9:** `scripts/release/pack.sh` ships `prices.yaml` and refuses a tree without it (like schedule.yaml);
  tests/release/pack.test.ts adds it to the fixture and the expected listing, and checks the refusal.
- **R10 (hash producers/consumers found by grep):**
  - `loadAsset` (src/config/load.ts) is the one combined-hash producer: it passes `loadPrices(home)`.
  - Stored/compared via `loadAsset(...).hash`, so combined: ingest `fetchAsset` (src/ingest/run.ts -> fetchedProvenance,
    scanFlowGroup/writeApiFlow/writePeriodicPayments configHash), provenance/locator.ts (`asset.hash`), data.ts
    (fetch/backfill/validate), daemon jobs refresh.ts, backfill.ts, levels.ts, nightlyReport.ts (registry hashes),
    registry/reconcile.ts + actions.ts (asset_registry.config_hash), app/proposals.ts observation approve
    (disclosedProvenance(hash)), agent/run.ts (agent_runs config_hash input = loaded.hash + persona + skills; the
    mid-run change check compares two loadAsset hashes; Ledger's disclosed rows), cli tick.ts/agent.ts/asset.ts show.
    Valuation and tick read `config` only, no hash.
  - `parseAssetYaml/parseAssetObject` without prices (config-only hash) remain only where the hash is discarded:
    app/proposals.ts `approveConfig` (validation before write; now passes `loadPrices(configRoot)` anyway, so it uses the
    same loader inputs), agent/tools/write.ts propose-config validation (ToolContext has no config root; hash unused),
    and test helpers (agentWorld, fetchHarness fixtures, which have no prices.yaml).
  - New test tests/config/combinedHash.test.ts: a home with a prices.yaml entry for the mini token (address match); a
    fetch's stored provenance configHash and an approved observation proposal's provenance configHash both equal
    `loadAsset(home).hash`, which differs from the config-only hash; a config-proposal approve reloads to a combined hash.
    It passed on first run (no RED): every stored path already went through `loadAsset`; the test is the proof R10 asks for.
- **R11:** comment on the symbol match in `entriesFor`: interim, HYPE only, replaced in Task 6.
- **R12:** departures accepted; nothing changed.

### Tests
- RED: prices validator test (`expected '' to contain '…base_vault: must be a base58 32-byte Solana address'`, 1 failed
  / 17 passed); pack test (2 failed / 3 passed before pack.sh change). GREEN after each.
- Focused: 14 files / 227 tests passed. Full `npx vitest run --maxWorkers=2`: **146 files, 1769/1769 passed** (no
  load-sensitive failures, no reruns needed). `npm run typecheck` clean. `python3 -m unittest
  scripts/provision/test/test_orion_remote.py`: 52 OK.

### Files added by this continuation
- tests/config/combinedHash.test.ts; modified scripts/release/pack.sh, tests/release/pack.test.ts, src/app/proposals.ts
  (plus prices.yaml, src/prices/config.ts, tests/prices/config.test.ts and the LIT/PUMP pin files).

### Concerns
- agent/tools/write.ts still validates a proposed config without prices (hash discarded, so harmless); worth giving
  ToolContext the config root if a later task stores that hash.
- `asset validate` still has no prices.yaml row of its own (carried from the first report).
