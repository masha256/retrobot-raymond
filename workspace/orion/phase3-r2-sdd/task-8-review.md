# Task 8 review: commit 13ece08 (base 6c0b54e)

### Spec Compliance

- ✅ Spec compliant (with R26/R29) for everything in the brief: `repriceAsset`, `rebuildPriceLevels`, `purgePrices`, the CLI verbs, the orion-remote verbs and their tests, and the deploy.md table. One unflagged departure needs the controller's OK. It is listed under Minor 1: rebuild-price-levels refuses a row whose newest price is more than 6 h old, and the brief only says "refused where none exists".
- ⚠️ Cannot verify from the diff. The remap list only works if prod has no other `coingecko:*` observation refs. I checked the code side: at 7063c22^ the only `coingecko:<id>` refs come from `share_price` members (`memberToken`), and those are yCRV's `crvusd` and `yearn-crv`, so `COINGECKO_REF_REMAP` (src/db/reprice.ts:37-40) covers every ref the code could write. Any other `coingecko:*` ref on prod would make purge-prices refuse permanently. Task 9's dry run should confirm it shows zero.
- ⚠️ The R29 split (~21 repriced, ~369 `defillama_history`) depends on prod's first `solana.token_supply` reading. Task 9 should confirm it.

### Strengths

- **Export before write.**
  - reprice exports `to_jsonb(o)` for every touched row before any write: remap-only superseded and rejected rows, flows and derived rows. It also exports the derived old and new values, all through the shared `writeDurableExport`, which fsyncs the file, the directory and new parents and opens with `wx` (src/db/reprice.ts:155-160, src/db/purge.ts).
  - purge-prices exports the full `prices` and `tokens` rows inside its transaction, before the DELETEs (src/db/purge.ts:175).
  - Tests check the export against `to_jsonb` byte-for-byte.
- **Every write is scoped.**
  - Each reprice UPDATE is guarded on `id`, `asset_id`, the old `value` and the old `token_ref` (`reprice_conflict`).
  - purge-prices filters `source = $1`, and its tokens delete is limited to `coingecko:*` refs nothing references, checking every observation status and every other price source.
  - The remap writes `value = old` and leaves `amount` and `locator` alone (null marker), so only `token_ref` changes.
- **Value equality with the view.** I ran a probe on a seeded DB with prices from two chain sources: gap hours inside the 6 h lookback, equal-ts ties broken by `fetched_at`, and a newer CoinGecko row on every hour. After `--yes`, `value` equals `flow_usd_chain_v.usd` exactly (relative diff 0) on all 5 rows. `chainHourPrices` uses the view's tie order (src/db/prices.ts:154), and daily_mean needs all 24 exact hours.
- **Derived recomputation matches run.ts.** It uses the same stored `value` series (run.ts `storedDailyFlow`), the same `metric`/`metrics`/`minus` summing, the default of 30 days, and `derivedFunction`. The window check `touches` (src/db/reprice.ts:410) matches `windowSums`.
- **PUMP history (R29).** The rule mirrors the adapter's own split (`dayMs < firstReadingMs`, solana.ts:142). Twin amounts are used only on chain days.
- **Dry runs.** reprice and rebuild dry runs use the same planner as `--yes`, take no lock and create no file. purge-prices refuses on the dry run the same way as on `--yes`, and succeeds once the remap has run (tested).
- **Price-level rebuild.**
  - The test runs rebuild, then `purgeMetrics --source-type market_data`, then `latestLevel` for each day.
  - AERO's ref comes from its `token` contract.
  - `first_party_api` is used for candle sources.
  - I checked all 14 real price-level metrics: `priceLevelRef` resolves each to a ref present in prices.yaml.
- **orion-remote.**
  - Every value goes through `pattern()` (fullmatch), and `parse` refuses option-looking values.
  - My extra probes all exited 64 before Orion ran: `'crv --yes'`, `--from '2025-10-13 --yes'`, `-crv`, `--from -2025-10-13`, `--from=… --yes`, `--source=coingecko --yes`, `'--source coingecko'`, `--source 'coingecko --yes'`, `'--yes\n'`, `-`, and `\;id`.
  - The help text and the three deploy.md verb lines are present.

### Issues

#### Critical (Must Fix)

None.

#### Important (Should Fix)

1. **src/db/reprice.ts:358-360 with :410-417 — a re-run after a partial apply leaves derived rows stale, permanently and silently.**
   - **Cause.** `touches()` only counts days whose flow value changes *in this run*. A flow day committed by an earlier, interrupted run is "unchanged" on the re-run. So is a day whose new value equals its old one: a zero-burn day, value 0 → 0, gets only the marker. Neither day enters `changedDays`.
   - **Effect.** A derived row of a later day whose window covers those days is never recomputed. A third run reports nothing to do.
   - **Reproduced** in my worktree. Five burn days with 10-04 at zero burn and `usage_index` = burn_momentum over 3 days. A trigger failed the 10-04 day transaction once (standing in for a crash or `reprice_conflict` mid-apply, which R29 accepts as "rerun to continue"). After the re-run, `usage_index` for 10-04 = 7.67, the old CoinGecko-based value; derived.ts on the final flows gives 77.98. The third run shows `recomputed: 0` and exports nothing.
   - **Why it matters.** This breaks risk 1 (a re-runnable state after a crash) and risk 3 (derived rows equal derived.ts on the new inputs). It also breaks P4's "derived rows recomputed". The stale value reaches the report, and the Task 10 proof would see a usage_index that matches neither the old nor the new flows.
   - **Fix.** Count a flow day as moved when its row already carries `locator.repriced`, as well as when its value changes in this run. Or recompute every in-range derived row whose window holds any repriceable day, writing only when `v !== d.value`. Either keeps the second `--yes` a no-op, because equal values count as unchanged. Pin it with a test: fail one day's transaction, re-run, then assert the derived rows equal derived.ts on the final flows. My probe is at `~/.hermes/profiles/raymond/cache/scratch/t8-review-probe.test.ts`.

#### Minor (Nice to Have)

1. **src/db/priceLevels.ts:105-108 — undeclared departure.** The 6 h bound (`ts >= upTo - 6h`) is not in the brief. It is reasonable and matches the view, and docs/ops/deploy.md and the CLI help state it, but the report's "decisions to check" does not list it. The controller should accept it explicitly.
2. **src/db/priceLevels.ts:79-84, :143-146 — rung logic duplicated.** `kindOfSource` inverts `methodSource`, and `firstParty ? 'first_party_api' : 'contract_state'` re-derives the rung that `venueOfMethod(...)` already returns (`venue.rung`). Use `venue.rung` so a new first-party venue cannot disagree.
3. **src/db/reprice.ts:227 — supply reading includes rejected rows.** The first reading counts readings of any status. The adapter only sees the active ones from `ctx.observations`. An earlier rejected reading would move the history/chain split and could reprice a DefiLlama-era day from a CoinGecko-derived twin. That is unlikely, but filtering on `status <> 'rejected'` would match the adapter exactly.
4. **src/db/reprice.ts:259 — `no token amounts` covers too much.** A log_scan row that has `hourly_amounts` but `amount = null` is refused under `no token amounts`, but the view would price it hourly. No such rows are known; this is about edge-case consistency.
5. **tests/db/reprice.test.ts:202 — tautological assertion.** `expect(burn.repriced).toBe(yes ? 1 : 1)` asserts the same thing in both branches. On `--yes`, assert the post-write state instead, e.g. `unchanged` on a third call.
6. **tests/cli/reprice.cli.test.ts — written after the code.** The report says so; this is a process note.
7. **No CLI exit code for refused rows.** The refused rows are listed, which is fine for Task 9. The orion-remote JSON consumer must read `refused` itself.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The export, scoping, view equality (bit-equal in a probe), idempotence and the remote-verb hardening are all solid. But a re-run after a mid-apply failure leaves derived rates computed over the old CoinGecko flows, and nothing reports it. That breaks the re-runnable-after-crash and derived-equality requirements this task was dispatched to guarantee.

Checks run (in the detached worktree rev-t8, since removed):
- the 4 Task 8 vitest files: 35/35;
- `test_orion_remote.py`: 59 OK;
- a value-vs-view probe: passed, bit-equal;
- a crash-and-rerun derived probe: FAILED, which is Important 1;
- 14 orion-remote injection probes: all exit 64;
- `priceLevelRef` over the 14 real price-level metrics: all resolve.
