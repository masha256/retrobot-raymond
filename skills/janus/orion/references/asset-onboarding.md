# Scoping and onboarding a new orion asset

Use when Mike asks what it takes to add a token, or to start onboarding one.

## 1. Start from what the repo already knows
- `docs/research/2026-09-22-top50-revenue-models.md` (fit grade, data path, design findings) and `docs/research/tokens/<symbol>.md` (contracts, holder-flow kind/rule/base, supply, data table). Read these first; don't re-research from the web.
- The latest onboarding specs + followups notes (`docs/superpowers/specs|notes/*-onboarding*`) for conventions.
- `src/config/schema.ts` + `src/config/sources.ts` for what is config-only vs needs code: required standard metrics (price, revenue run rate, effective supply, staked supply, staker_emission_share, emission_rate_annual), source types, which types can be primaries/cross-checks for level vs flow.

## 2. Re-verify every figure live before recommending
Research notes go stale (UNI's 30d run rate fell ~30% in two weeks). Pull fresh numbers in one batched script:
- DefiLlama: `https://api.llama.fi/summary/fees/<slug>?dataType=<dailyHoldersRevenue|dailyRevenue|dailyFees|dailyUserFees>`; sum `totalDataChart` over 30/90/365 days and annualize. `totalDataChartBreakdown` gives per-chain/per-product splits; `methodology` says what is included.
- CoinGecko `simple/price`; DefiLlama coins `coins.llama.fi/prices/current/<chain>:<token>` for the price cross-check.
- `eth_call` reads via curl (compute selectors with `node -e "const {keccak256,toHex}=require('viem');console.log(keccak256(toHex('rate()')).slice(0,10))"` from the orion dir). Private Vyper constants revert as calls; take them from the published source.
- Blockscout `https://eth.blockscout.com/api/v2/addresses/<addr>` names unknown contracts (`name`, `is_contract`) — use it to label the senders/recipients of a fee route.

## 3. Measure the holder flow on chain; treat DefiLlama holders revenue as suspect
DefiLlama's holders revenue is often a formula or includes non-revenue money (bribes, product yield). Before choosing a flow source:
1. `eth_getLogs` Transfer logs into the payout contract over ~90 days (needs a keyed RPC on mainnet); group by sender and by day.
2. Then trace one hop up: logs out of and into the sender, to see the split (e.g. allocator → 90% distributor / 10% treasury).
3. Reconcile against DefiLlama using its `methodology` and `breakdownMethodology` text, and read the adapter source (`github.com/DefiLlama/dimension-adapters`, `dexs/<slug>/index.ts`) to see exactly what is summed. The public API does not return the per-label split (`dailyBribesRevenue` comes back empty, and `breakdownByLabel` is ignored), so measure the bribe part on chain rather than subtracting.
4. DefiLlama revises past days. Diff the stored daily rows against a fresh API pull: a day the API has since inflated (for example, a bribe-pricing spike) would come back on any re-backfill. Name the date and size when proposing a source change.

**AERO (Velodrome-style ve(3,3) on Base):** voter payouts can be measured from logs.
- Get every gauge's `bribeVotingReward` and `feeVotingReward` from Voter `0x16613524e02ad97eDfeF371bC883F2F5d6C480A5` `GaugeCreated` logs (about 2,000 gauges across 6 gauge factories).
- Then sum `NotifyReward(from, reward, epoch, amount)` into those contracts over 91 days and price each token with `coins.llama.fi/prices/current/base:<t>,...` in batches of about 80.
- Measured result: fees about $70M a year and bribes about $12M a year. DefiLlama's holders revenue counts the classic-pool bribes but none of the Slipstream ones, so the totals roughly offset.
- The bribes are mostly long-tail tokens priced at spot, so treat bribe dollars as low quality.
- AERO has no liquid wrapper worth its own asset (relays are non-tradeable; iAERO is a few $M). Revisit only if a wrapper passes about $50M.
**Before rebuilding a protocol's sources, search the news for an imminent migration** (merger, new token, new contracts, voting replaced by automation). If one is weeks away, recommend holding the current config, leaving a review flag on the signal, and setting a dated follow-up reminder after the migration (a cron one-shot to the orion-dev topic that checks signals around the dates, the new token/contracts/ids, and whether bribes still exist; then proposes the rebuild without changing anything). Contracts and bribe markets are what migrations change first.
If the gap is explained, prefer the on-chain `transfer_flow` with a sender allowlist (an unlisted sender then raises an anomaly when governance re-routes fees) and drop a cross-check that would fire every month.

## 4. Shape decisions that recur
- **Lumpy flows**: weekly payouts → make the run-rate window AND the holder flow's `window_days` the same whole number of weeks (91), so every window holds the same number of payouts and measured capture stays 1. The scanner already writes empty days as 0 rows.
- **Backfill > window** (e.g. 100 vs 90/91) so a lagging last day still yields a run rate.
- **Zero-valued structural metrics** (no staking, emissions not to lockers): Mike wants them fetched, not manual, so the grade stays A — a manual row in force caps the grade at B.
- **Contract-coded schedules** (halvings, annual cuts): Mike wants an adapter that reads the contract and computes the next step, not a hand-entered dated row. The engine's `buildSchedule` already consumes future-dated schedule steps.
- **Burn to 0xdead**: `totalSupply()` doesn't fall; use `erc20_supply` with `subtract_balances: [dead]`, and an allowlist to keep one-off treasury burns out of the flow.
- **buy_and_hold** (LINK, SKY, JUP…): the held-token policy (net from supply? retention haircut?) is unsettled — flag it as a decision before config.
- Emissions larger than the holder flow (ve-models) make the holder-cashflow module bearish by construction; say so up front so a low base case isn't read as a bug.

## 5. Build sequence that worked (CRV)
- Write the spec, then a short plan with one task per building block (transport/chain → new source types → adapters → engine module → asset yaml + asset test + persona paragraph + docs). Make one commit per task on `feat/<asset>`, with the full suite and the type check green after each.
- **The asset test** (`tests/assets/<asset>.ingest.test.ts`) follows the AERO pattern:
  - Check the config hash pin, `requiredAssumptionKeys`, that no metric lacks a source, and the plan's batch map.
  - Run a canned fetch with `fakeHttp`/`fakeRpc` (set `maxLogRange`/`blockTimeSec` for non-Base chains), then a valuation that must come out `ok` at grade A.
  - Build fixtures from the real feed, trimmed.
  - Pin the hash by printing `loadAsset('.', '<asset>').hash` via `npx tsx -e`, and re-pin on every deliberate yaml edit.
  - Also drive the asset through `updateAsset` (the tick path), not only `fetchAsset` + `runValuation`. The valuation's as-of is computed in `src/app/update.ts` from what the fetch wrote, so a test that calls `runValuation(db, asset, NOW)` directly can't catch an as-of bug. Anything that writes future-dated rows (schedule steps) needs this path tested.
  - Prove a new regression test bites: stash the fix (`git stash push <file>`), see the test fail, then pop it back.
- Then do a live dry run from a throwaway home (see SKILL.md, live-install rules), with `--json --metric ...` to pull the exact values, and record them in the spec's Amendments section.
  - Do it before writing the asset test's fixtures, so they reflect real data. In the same home, a real `data fetch`, a flat placeholder `model assumptions import` and `model whatif <x> --json` check the engine end to end. Report the result as a placeholder, not a calibration.
- Before Mike's checkpoints, write any spec deviations found during the build into the Amendments section, and present any value-changing ones to him as a decision.
- **Checkpoints on live, in order:**
  1. `persona assign <asset> <persona>` + `data fetch <asset> --dry-run`.
  2. `./run-daily.sh <asset>` (first real fetch → blocked → bootstrap journal). Record observation counts before and after. Then check:
     - The `signal_id` stamp and `generated_at` are today. A future date means a future-dated row set the as-of. Every metric then reads stale and the grade falls to D.
     - Blocked only on `no_assumption_set`, at the grade you expected.
     - The bootstrap journal (`select summary, thesis, open_questions_json from journal where asset_id='<x>' order by id desc limit 1`). The analyst flags real defects there; answer each one in the report. It reads raw drivers, not the valuation breakdown, so it can flag something the engine already handles (e.g. "valued per total supply?" when `valued_per: recipients` is set); check the breakdown before conceding a defect.
     - A first tick runs about 2 minutes for a single-stream asset and 5–6 minutes for a three-stream wrapper (one log scan per stream per day); launch it as one backgrounded command that does the backup, the run and the output tail together, and answer from its completion notice.
  3. Calibration packages: see section 6.
  4. First signal: `node dist/cli/index.js model run <asset>` right after the import. Report the expected value at each horizon, bear/base/bull, the per-module values and dispersion. Then run `inbox <asset>`.
  5. The cron line: copy the newest `orion-<asset>` job. Ask before creating it, and say whether any one-shot watch job should also cover the new asset.
     - Every asset has its own profile wrapper `scripts/orion-tick-<asset>.sh` (`exec /bin/bash .../orion-tick.sh <asset>`, mode 700). Copy one and `bash -n` it.
     - Read the source job's full prompt from `~/.hermes/profiles/raymond/cron/jobs.json` (`cronjob_manage list` shows only a preview). Swap `AERO`→`<ASSET>` and `aero`→`<asset>`, then diff old against new to confirm only the symbol changed.
     - Pass the real ~12k-char prompt text. Never pass a placeholder meaning to fill it in later: the job stores it literally. If a long prompt is awkward to inline, write it to a scratch file and run `hermes --profile raymond cron edit <id> --prompt "$(cat <file>)"`.
     - Verify by reading `jobs.json`: the prompt equals the intended text, and schedule/script/workdir/deliver/attach_to_session match the source job.
     - Schedule it 5 minutes after the last orion job, delivering to orion-ops with `attach_to_session`, `workdir` = repo.
     - Add the new job's line to the pending DST reminder job's prompt (`cron edit --prompt`), or it fires an hour off after the clock change. Add the asset to `docs/ops/hermes-daily-job.md` and mark checkpoint 5 done in the followups note.

## 6. Calibration (checkpoint 3)
Never price candidates against live. Work in scratch homes and import only the package Mike picks.
1. **Scratch home:** `sqlite3 orion.db ".backup '$TMPDIR/<x>-cal/orion.db'"`, copy `assets personas skills .env` (chmod 600 on `.env`), then `ORION_HOME=<scratch> node dist/cli/index.js ...`.
2. **Longer history, if a 1-year window is a candidate:** `data fetch <x> --metric flow_usd.<k> --metric revenue_run_rate_usd --backfill-days 362` in the scratch home.
   - Keyless CoinGecko refuses history older than 365 days (HTTP 401) when it prices a flow's days, so stay under 365.
   - `data fetch` exits 0 even when a source failed. Grep its output for non-`ok` sources before trusting the result.
   - Pick window lengths that are whole payout periods (28 / 91 / 357 for weekly payouts).
   - Count active flow rows with `superseded_by is null` (a backfill supersedes the earlier rows; there is no `status='active'`). Print the payout by month before choosing a window: a trend (e.g. bribe income falling with the underlying's price) makes the long window an assumption that the old regime returns, which is worth saying.
3. **Window and component variants:** one scratch home per variant. Copy the scratch home, edit its `assets/<x>.yaml` (`window_days` on both the run rate and the holder flow, plus `params.days` of the `flow_annualized` source; assert each replace hit), then `data fetch <x> --metric revenue_run_rate_usd --backfill-days 3` so the run rate is re-derived at the new window, and check its `source_detail` names the window. Then import and run `model whatif <x> --json` in each.
   - `whatif --json` shape: `output.horizons['12m']` has `expectedTarget`, `dispersion`, `scenarios.<s>.target`, `modules.<id>.value`; spot is `output.spot`. Script the import + whatif in one helper per home.
   - **What the market implies:** bisect one key (first-year growth, the discount rate, the multiple) with `--set` until `expectedTarget` equals spot; report each as "spot needs X".
   - **Wrapper ceiling check:** for a wrapper mintable 1:1 from an underlying, compare every scenario target against the underlying's spot. Flag any package whose bull lands above it, and recommend building the ceiling rule before Mike picks that package.
4. **One-at-a-time sweep** from a starter set (copy the shapes of the closest calibrated asset): run `model whatif --set key=v --scenario s` per key. Report which keys move the 12m expected value and which don't.
5. **Three packages** (conservative / central / constructive) × each window, plus the central window without each optional component. Report 12m expected (bear/base/bull) and what the market price implies: which package and settings reach spot. Recommend one package and one window, with the reason.
6. **After Mike picks:**
   - Write `calibration/<x>-assumptions.yaml`. Its comment header records the choice, the anchors (spot, supply, flows, emissions), the resulting 12m values, and that Mike heard the gap to spot before choosing.
   - Write agent bands into `assets/<x>.yaml` by the mirror rule. Inner edge is halfway to the neighbouring scenario, outer edge as far again, clipped to min/max.
   - **Sort each band's (min, max).** Keys that fall from bear to bull (discount rates) otherwise come out inverted.
   - Halve the band of the largest single driver, and tie a capped key (capture at 1.0) to the ceiling.
   - Price each band edge (and all keys at the edge together), and write the swing into the yaml comment.
   - Re-pin the hash. Add an asset test that the calibrated set is complete and inside its own bands.
   - Then branch `calib/<x>`, run the suite, ff-merge, build, back up, `model assumptions import <x> calibration/<x>-assumptions.yaml --rationale "..."`, `model run <x>`.
7. **Record:** write a followups note `docs/superpowers/notes/<date>-<x>-onboarding-followups.md` (checkpoints, the calibration table, open questions). Delete the scratch homes, which hold `.env`, and the merged branches.

## Multi-stream wrappers (cvxCRV, sdCRV pattern)

- One `transfer_flow` holder flow per reward token, measured at the staking contract (wrapper/gauge/merkle stash) with the funding contract as `from_allowlist`; `revenue_run_rate_usd` uses `flow_annualized` with `params.metrics: [a, b, c]` (sums days every flow has).
- **Capture is a share:** `capture_rate_terminal.<flow>` = that flow's share of the summed run rate. Setting 1 per flow counts the run rate N times (cvxCRV showed +62% instead of -45%). Band each capture key near its share; test that calibrated shares sum to <= 1.
- Before calibrating, chart each stream by month: a stream that stopped (cvxCRV's CVX, Sept 2026) still sits in the 91-day average — set its capture to 0 rather than dropping the stream.
- Scratch calibration: backfill all streams with `--metric` per flow plus `revenue_run_rate_usd`, `--backfill-days 362`; window variants by rewriting `days:`/`window_days:` in the scratch asset yaml and re-fetching only `revenue_run_rate_usd`. `model whatif --json` returns `{output: {horizons: {12m: {expectedTarget, upsidePct, stakedTotalReturnPct, scenarios}}}}`.
- Thin wrapper prices on CoinGecko drift vs DefiLlama; http_json cannot be a required primary, so widen the cross-check tolerance instead.

## 7. Holder yield vs what orion reports
The 12m target values flows from the horizon on (the token's price then), so cash paid DURING the horizon appears in no target. Engine 1.3.0 (`src/engine/stakedCash.ts`) adds it to the staked total return only: `((target + cash per receiving token) / spot) × (1 + emission yield)^H − 1`, signal fields `staked_cash_per_token` + `staked_cash_streams`. Rules it follows, keep them when extending:
- Count `fee_share` holder flows only; burns/buybacks act through price and supply, so counting them double-counts (VVV and HYPE stay unchanged).
- Vote incentives count only where the `vote_incentives` component sets `params.staked_return: all|staked|locked` (who collects them); CRV sets `locked`.
- Each stream follows the valuation's own growth path, divided by its recipients at each step: effective supply, staked supply (today's share under `valued_per: recipients`, else today's ratio moving to `staked_ratio_horizon`), or locked supply now.
- Targets never move; only staked total return does. AERO's figure inherits DefiLlama's mixed series (classic-pool bribes in, Slipstream bribes out) until its flow is rebuilt.
When Mike asks why a yield line reads 0 or equals the upside, check the engine version of the signal first: before 1.3.0 the line counted token emissions only.

When Mike asks whether a wrapper yield (yCRV/st-yCRV, cvxCRV, sdCRV…) is in the model, decompose it on chain before answering:
- the wrapper's veCRV share of the total;
- fees plus bribes pro rata;
- the staked fraction of the wrapper token (unstaked holders forfeit to stakers);
- the wrapper's discount to the underlying (DefiLlama coins price for both);
- the vault's fee (Yearn APR from `ydaemon.yearn.fi/1/vaults/<addr>`).

The direct-locker yield (holder cash ÷ locked tokens × spot) is the like-for-like number. The wrapper premium comes from the discount and the forfeit, not from extra protocol value.

### Vetting a wrapper as its own asset (read-only spike)
When Mike asks for "only the spike", make zero repo, DB or cron changes. Keep notes in `$TMPDIR`, and put the key numbers in the reply, because scratch is pruned.
1. **Find the live staking contract from the token's holders, not from Yearn's API.** Use Blockscout `GET /api/v2/tokens/<wrapper>/holders`. ydaemon still lists legacy vaults (st-yCRV holds almost nothing; YearnBoostedStaker holds 88% of yCRV), so its APR and vault can be the wrong product.
2. **Trace the cash route with `alchemy_getAssetTransfers`** (`fromAddress`/`toAddress`, `contractAddresses`, `category:["erc20"]`, `withMetadata`, follow `pageKey`). It's faster than chunked `eth_getLogs`. Start from FeeDistributor → the locker's voter, then follow each hop out, naming each address via Blockscout. Bribes usually arrive through a swap or "burner" contract that converts many tokens to one; treat that contract as the allowed sender rather than tracing every input token.
3. **Measure the staker share** from the splitter's outputs (vault shares × `pricePerShare`): stakers vs treasury.
4. **Reconcile supply:** compare the wrapper's supply with the locker's veCRV. Legacy wrapper tokens migrated into the new contract explain part of any gap.
5. **Price check:** the wrapper/underlying ratio weekly over a year (`coins.llama.fi/chart/<a>,<b>?span=53&period=7d`) shows whether the discount is a stable band or a de-peg.
6. **Rough fair value:** price per-token cash to stakers as a perpetuity, with fees growing slowly and bribes either shrinking with emissions or flat. Also solve for the discount rate the market price implies. Whether bribes shrink with emissions is usually the whole call; report it as such.
7. **For a build:** list the flows (fees, bribes via the converter), the staker share, and the engine rule that a wrapper mintable 1:1 from the underlying is capped at the underlying's price.

### Building a liquid-locker wrapper asset (yCRV pattern; reuse for cvxCRV, sdCRV)
- **Scope (Mike's choice):** value the wrapper as its staked position paying the stable reward (crvUSD). Leave auto-compounding vaults out; the other lockers share the staking shape.
- **Before building, list every reward token into the staking contract, not only crvUSD.** Sum `alchemy_getAssetTransfers` with `toAddress` = the staker or its wrapper, grouped by asset and sender. Then classify each stream:
  - protocol fee income (crvUSD);
  - emission-linked income (CRV platform fees, which shrink with CRV emissions and price);
  - a treasury program (a capped governance token handed out by the protocol, which can end);
  - bribes (check how they are paid: in the wrapper token through a Merkle distributor, and who is eligible).
  If the crvUSD-only rule would drop a large share of the cash, bring Mike priced scope options (streams in or out, yield at spot for each) before building. Don't silently extend the yCRV rule. Mike's picks: cvxCRV counts all three streams (crvUSD, CRV, CVX); sdCRV counts its sdCRV bribes alongside crvUSD and CRV.
  - Skip a listed reward token that paid nothing over the window (check its gauge weight; sdCRV's SDT is 0) and say so in the yaml comment.
  - **Merkle-paid bribes: verify who claims before valuing them per staked token.** Sum the stash's outflows by recipient and check the top claimants' gauge balance vs wallet balance; if they hold in the gauge, the bribes share the staked base with the fees.
- **Multi-stream build:** one `transfer_flow` metric + one holder flow per stream (each `recipient_base: staked`, `valued_per: recipients`, `window_days: 91`; a treasury program gets `capture_rule: discretionary` so its own premium carries the wind-down). `revenue_run_rate_usd` uses `derived` `flow_annualized` with `params.metrics: [flow_usd.a, flow_usd.b, ...]` (sums by day over days every flow has; can't mix API and on-chain flows).
  - **Set each `capture_rate_terminal.<flow>` to that flow's share of the run rate, never 1 per flow.** Measured capture per flow is flow ÷ run rate, so 1 on each counts the whole run rate once per stream (a scratch run read +62% instead of −45%). Compute the shares from the last 91 days of `flow_usd.*` rows and write them into placeholders and calibrations alike.
  - Sanity-check a placeholder run: if `fm_holder_flow` ÷ per-token cash is far above the multiple you set, a capture rate is wrong.
  - **Check each stream's recent daily rate against its 91-day average before calibrating.** A treasury program can stop mid-window (cvxCRV's CVX fell ~99% in Aug–Sep: CvxDistribution's funding hook stopped topping it up). Read the distributor's `rewardRate()`/`periodFinish()` and the funding transfers into it; if the program has ended, keep the stream (a restart shows up) but set its capture share from the current rate, not the window average, and tell Mike the corrected cash total.
  - The bootstrap analyst tends to ask that bribes paid to stakers in the wrapper token be moved into a `vote_incentives` component. Answer with the yCRV rule: bribes the stakers actually receive are cash flow in the holder flow; their decline lives in growth assumptions.
  - Start the 362-day calibration backfill only after the first live tick finishes, so the scratch copy holds the live 91-day flows; backfill each wrapper in its own scratch home, backgrounded (one wrapper ≈ 10+ minutes).
  - Asset test: the stock `fakeRpc` serves one log list, so wrap it to route `getTransferLogs` by `token>sink`; also fake `decimals()` on the wrapper token (`erc20_supply` reads it). A `for (const c of CASES) describe(...)` loop covers two wrappers in one file.
  - A scratch dry fetch scans ~100 days per stream (one `eth_getLogs` per day each), so two three-stream assets take 10+ minutes: run it backgrounded with `notify`, and do the asset test and full suite meanwhile.
- Fee routes into the staker contracts (read on chain, 91 days, starting from FeeDistributor `0xD16d5eC345Dd86Fb63C6a9C43c517210F1027914` crvUSD out):
  - **cvxCRV** (token `0x62B9c7356A2Dc64a1969e19C23e4f579F9810Aa7`):
    - crvUSD: VoterProxy `0x989AEb4d175e16225E39E87d0D97A3360524AD80` → Booster `0xF403C135812408BFbE8713b5A23a04b3D48AAE31` → crvUSD reward pool `0x191f455cc8acdd579f4e6956fc7007c9668c2289` (100%) → CvxCrvStakingWrapper `0xaa0c3f5f7dfd688c6e646f66cd2a6b66acdbe434`.
    - CRV: from the Booster into BaseRewardPool `0x3Fe65692bfCD0e6CF84cB1E7d24108E434A7587e`.
    - CVX: from CvxDistribution `0x449f2fd99174e1785cf2a1c79e665fec3dd1ddc6`.
    - No bribes: Votium pays vlCVX, not cvxCRV.
  - **sdCRV** (token `0xD1b5651E55D4CeeD36251c61c50C889B36F6abB5`):
    - crvUSD: locker `0x52f541764E6e90eeBc5c21Ff570De0e2D63766B6` → CurveAccumulator `0x11f78501e6b0cbc5de4c7e6bbabaacdb973eb4cd`, which splits 85% to the sdCRV gauge `0x7f50786a0b15723d741727882ee99a0bf34e3466`, 10% to LPs and 5% to treasury.
    - CRV: from FeeReceiver `0x60136fefe23d269af41ab72de483d186dc4318d6` through the accumulator.
    - Bribes: Botmarket `0xadfbfd06633eb92fc9b58b3152fe92b0a24eb1ff` swaps them to sdCRV and sends them to MultiMerkleStash `0x03e34b085c52985f6a5d27243f20c84bddc01db4`.
  - Bribes are about two-thirds of sdCRV's cash and about three-quarters of yCRV's; cvxCRV has none.
- **Holder flow = the last hop:** the reward token into the stakers' reward distributor, allowlisting only the contract that funds it (for yCRV, the Receiver). The splitter ratios and performance fee upstream are then netted out by measurement. Read them for the spec anyway (`getSplits()`, `performanceFee()`; probe the struct's field count, since a wrong ABI returns garbage).
- **Rewards paid in vault shares:** use `transfer_flow` `share_price: { contract, function: pricePerShare, decimals }`. It converts each day's shares at that day's last block, then prices the underlying.
- **Paid only to stakers:** `recipient_base: staked` + `valued_per: recipients` divides the flow by today's staked share in both estimate modules, because unstaked wrapper tokens forfeit to the treasury.
- **Bribes arriving as stable in the same flow:** no `vote_incentives` component. Put their link to the underlying's emission cuts in the growth assumptions (allow negative terminal growth), and add a `review_triggers.calendar` entry on the cut date.
- **Metrics:** supply = wrapper `totalSupply()`; staked = the staker's `totalSupply()`; emissions and staker share = `constant` 0. Price cross-checks on thin wrappers run near the 2% tolerance; say so.
  - When the first dry fetch trips the price cross-check, pull 90 days of CoinGecko `market_chart` vs DefiLlama `coins.llama.fi/chart` daily and size the tolerance from the median and recent spread (sdCRV: median −0.3%, recent +2–6%, so 5%). CoinGecko must stay primary: `http_json` is refused as the primary of a required metric.
- The ceiling at the underlying's price is not built yet (no cross-asset rule). List it as an open follow-up.
- **Dilution:** none to model. The wrapper has no emissions, and each new mint locks 1 underlying and brings its own ve-power, so cash per token holds whether or not the peg allows minting. Real dilution happens upstream and belongs in growth: the locker's ve share falling as others lock, and bribes per vote falling with emission cuts. The peg matters only for the price ceiling.
- **Staked share:** the splitter sets the stakers' cut from the staked share, so cash per staked token barely moves as staking changes. That is why `valued_per: recipients` holds today's share instead of the horizon assumption.
- **Calibrating a wrapper whose cash is mostly bribes:** the bribe path is the growth assumption (base decays with the underlying's emissions, negative terminal growth allowed). Pull ~362 days of payouts and compare 91/182/357-day windows against the underlying's price history; a long window reflects a past price era, not the present. Solve for what the market price implies (y1 growth, or discount/multiple with flat bribes). Flag any package whose bull exceeds the underlying's price (ceiling not built). The staked-ratio-horizon key does nothing under `valued_per: recipients`, so leave it unbanded. yCRV: central, 91d, 12m 0.122 vs spot 0.183.
- **Locker ve shares** (Convex, StakeDAO, Yearn) are read daily as `monitor_only` lines on the underlying (CRV): `ve.balanceOf(locker)` for voting power, `ve.locked(locker)` pick 0 for CRV locked, plus `ve.totalSupply()`; "everyone else" is the remainder. Show the locked-CRV share for display: lockers relock at the maximum, so their voting-power share drifts up as direct locks decay.
- **Throwaway home with live history in one line:** `H=$(mktemp -d)`, copy `assets personas calibration` (and `skills` if present), `sqlite3 orion.db ".backup '$H/orion.db'"`, copy `.env`, `chmod 600` both, then `ORION_HOME=$H` for `data fetch` and `model run`. Check the new rows' `source_detail` block and that the signal's 12m move is 0.0% (cause "config" only) when the change should not touch valuation. `rm -rf $H` afterwards.

## 8. Report shape Mike accepts
Per asset: holder-flow mechanism → what's config-only → what needs code → live numbers (30/90/365 annualized, market cap multiple) → open decisions. End with a recommended sequence and a short numbered list of decisions. Keep RPC keys out of chat output and commit messages; `.env` is git-ignored. If Mike pastes a key in chat, save it and mention it is now in the chat history (rotation is his call).
