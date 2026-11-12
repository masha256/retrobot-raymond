### Task 6: the R1 config sweep (12 assets)

**Files:**
- Modify: `assets/{cake,crv,cvxcrv,hype,link,lit,pump,sdcrv,sky,uni,vvv,ycrv}.yaml`, their hash pins
  (`grep -rl <old hash> tests`), the asset ingest tests that mock the removed reads (`tests/assets/*.test.ts`),
  `docs/ops/sources-register.md` (regenerated)

**Interfaces:**
- Consumes: Task 4's adapter and Task 5's volume form.

The removals, exactly (spec §5 R1):

- **`coins.llama.fi` price cross-checks** (`cross_checks` items of `price_usd`): CRV, cvxCRV, HYPE, sdCRV, SKY, yCRV.
- **CoinGecko `total_supply` cross-checks:** CRV, cvxCRV, HYPE, LINK, LIT, PUMP, SKY, UNI, VVV.
- **CAKE:** delete the metrics `flow_usd.fees` and `flow_usd.llama_revenue`. Set `volume` to
  `{ not_measured: "gross swap fees: DefiLlama removed (Phase 3 R1); on-chain v2/v3 gross not read yet (Phase 3b)" }`.
- **UNI:** delete `flow_usd.swap_fees`. Set `volume` to
  `{ not_measured: "gross swap fees: DefiLlama removed (Phase 3 R1); v2 x6 derived and v3/v4 scans not built (Phase 3b)" }`.
- **LIT:** delete `flow_usd.fees` and `flow_usd.llama_revenue`, and the `defillama` cross-check on `flow_usd.buyback`.
  `unlocks_next_year` moves to `schedule.unlocks_next_year` with team 260e6 and investors 240e6, the approved
  tranches, and the citation `https://x.com/Lighter_xyz/status/2005862687331303804` (quote: "The team and investors all
  have a 1-year unlock and 3-year linear vesting after. The breakdown is 26% team, 24% investor."). Update the dilution
  line's note to the new source.
- **PUMP:** `unlocks_next_year` moves to `schedule.unlocks_next_year` (linear, start 2026-07-12, years 3; 150e9 team
  and 97.5e9 investors still locked; the citation from Task 4 Step 1). Update the dilution note.
- **VVV:** delete `flow_usd.revenue_proxy` and the `cross_check: flow_usd.revenue_proxy` on the `business` revenue line,
  and the `defillama` cross-check on `flow_usd.burn`.
- Rewrite every YAML comment that names a removed read. Leave `identifiers.coingecko/defillama` (R8).

- [ ] **Step 1:** Make the edits. Run `npx tsx src/cli/index.ts asset validate <a>` for all 13.
- [ ] **Step 2:** Assert in a test (`tests/assets/r1-third-party.test.ts`) that none of the 12 YAMLs has a `defillama`
  source or `coins.llama.fi`/`defillama-datasets` url outside the out-of-scope list in the Global Constraints, and no
  `coingecko` source with `field: total_supply`. Assert also that `lit.unlocks_next_year` is no longer referenced by
  any asset (the adapter stays until R8).
- [ ] **Step 3:** Re-pin the 12 hashes. AERO's must not move, and any other pin moving is a stop. Update the asset
  ingest tests' mocks (the removed endpoints are no longer called, so drop their stubs and assert no call goes to
  them).
- [ ] **Step 4:** Regenerate `docs/ops/sources-register.md`. Run the full suite and typecheck.
- [ ] **Step 5: Commit** `feat(config)!: Phase 3 R1: drop the DefiLlama/CoinGecko cross-checks and display series (12 assets); cited unlock schedules; CAKE/UNI volume not_measured`.

