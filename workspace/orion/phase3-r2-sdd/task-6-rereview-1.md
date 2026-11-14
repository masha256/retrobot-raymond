# Task 6 fix wave re-review 1 (661bf9c..7202a46)

### Finding Verdicts

- **A. Breaches from a flow scan's own price write were dropped** — ADDRESSED. src/ingest/flow.ts:444 `result.breaches.push(...w.breaches)`; run.ts:502 `keepBreaches(scan.breaches)` dedupes by ref|hour|check and returns sorted `priceBreaches` (run.ts:676-677, left out when empty); refresh.ts:149-163 posts each once via `formatPriceBreach` (the levels format), only on a real run, and keeps undelivered lines. The writer reports no breaches on a dry run (writer.ts:176, 432). Test: refresh.test.ts "a breach the nightly scan's own price write reports is posted once" (exactly one WATCH line, no cross_check_mismatch). Passes.
- **B. No alert when the levels price write fails** — ADDRESSED. src/daemon/jobs/levels.ts:114-116: one `ORION ALERT <env> levels prices: <errors joined "; ">` (slackClean) when the summary has errors (prices.yaml unreadable, writer threw, chain errors). Reads, onLevels/snapshot_push and the ping rule are unchanged; the alert is an ordinary post, so an undelivered alert withholds the ping like any other post. Test: levelsJob.test.ts covers throw, chain errors, clean, undelivered. Passes.
- **C. PUMP burn did not ensure its own hours** — ADDRESSED. run.ts:265-279: `ctx.chainHourPrices` first calls `priceWriterOf(deps, loaded.prices)` for the asked hours with `{ dryRun }`. Writer chain errors go on the running batch as notes, breaches are kept for A, and dry-run rows rank under CHAIN_DRY_RUN_SOURCE (R19). Test: pump.ingest.test.ts "a burn day with no stored PUMP prices": the writer is called for [.., todayStart); on a dry run the `prices` table stays empty and 7 days come out at 5M USD; the real run stores them. Passes.
- **D. Levels wrote only hours after the newest stored row** — ADDRESSED. src/levels/levels.ts:51-69: `recentPriceHours` reads every stored hour in [TO-48h, TO) and starts at the earliest hour any ref lacks under its primary source, from that ref's valid_from on. The writer skips stored hours per ref (writer.ts:305-310), so a ref that can never be written costs only its own hours. Tests: levels.test.ts recentPriceHours (gap at TO-10h, cap, valid_from after the window) and "runLevels: a gap 10 h back inside the window is filled" (one call [TO-10h, TO), the hour is written). Both pass.
- **E. AERO hash did not cover its prices.yaml entry** — ADDRESSED. src/prices/config.ts:276 `contractRef('token')`. Only aero's pin moved for E (3c413feb… → 035327b9…). Tests: prices/config.test.ts and config/load.test.ts. Both pass.
- **F. Cross-checks beyond the R22 set; LIT zero liquidity** — ADDRESSED. At 7202a46, `price.token_check` cross-checks exist only in cake:48 (2), link:36 (2), lit:40 (3), pump:34 (2), uni:31 (2), vvv:38 (2, price_usd). They are gone from crv, cvxcrv, hype, sdcrv, sky, ycrv and vvv diem_price_usd. LIT zero liquidity: price.ts:137-138 throws `NoReading` only for `skipped === 'zero_liquidity'`; adapter.ts:15-18 maps it to `{ok:false, noReading:true}`; run.ts:446-450 notes a skip and `continue`s before `markFailed`, so there is no anomaly, no source failure and no streak. A primary with no reading still fails. Test: lit.ingest.test.ts (3 runs: all ok, no crossChecks, one zero_liquidity note, no anomaly rows) and adapters.price.test.ts. Both pass.
  - Hashes: the pins moved are exactly aero (E) plus crv, cvxcrv, hype, sdcrv, sky, vvv, ycrv (F), in tests/assets/*.ingest.test.ts and tests/config/load.test.ts. Golden tests/agent/golden/packs-13.json: only `price.token_check` `adapter_params` entries were removed (6 price_usd, 1 diem_price_usd), with no value path. The report goldens are unchanged.
- **G. Broken comment line in assets/pump.yaml** — ADDRESSED. assets/pump.yaml:73-76 is reflowed into whole lines. It is a comment only, and pump's hash did not move.

### New Breakage in the Fix Diff

None Critical or Important.
- Minor: src/daemon/jobs/refresh.ts:153 `result.undelivered ??= []` adds `undelivered: []` to the job result whenever there are breaches. This is consistent with the `cleared` branch and changes the result JSON only.
- Minor: src/ingest/flow.ts:89-92 says breaches are "Empty on a dry run" and run.ts:97-100 says "always on a dry run". Both depend on the writer's dry-run behaviour (writer.ts:176), not on a guard in flow.ts or run.ts. True today; a fake writer that returns breaches on a dry run would put them in `priceBreaches`. The refresh job only posts on `!fetched.dryRun`, so nothing is posted.

### Out-of-Scope Observations

- Same as implementer concern 2: the CLI paths `orion fetch` (src/cli/commands/data.ts:181) and `orion tick` (src/app/tick.ts:67 via src/cli/commands/tick.ts) receive `priceBreaches` but neither posts nor prints them. A breach found by a CLI-run scan is written to the stored rows, but no later run reports it.
- Implementer concerns 1 and 3 (the real writer runs inside a burn fetch over the backfill window; NoReading covers level cross-checks only) are noted. Neither breaks a finding.

### Checks run

Own worktree at 7202a46 (`npm ci`, `--maxWorkers=1`, removed afterwards):
- refresh, levelsJob, levels, pump/lit/aero/cake/vvv ingest, prices/config, adapters.price, config/load: 11 files, 134/134 pass.
- packGolden, report parity, v2Golden: 3 files, 126/126 pass.

### Verdict

**Fix round:** All findings addressed, no new Critical/Important breakage.
