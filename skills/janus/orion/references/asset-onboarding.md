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
3. Reconcile against DefiLlama with its own subtraction (bribes = `dailyFees − dailyUserFees`) and its `methodology` text. If the gap is explained, prefer the on-chain `transfer_flow` with a sender allowlist (an unlisted sender then raises an anomaly when governance re-routes fees) and drop a cross-check that would fire every month.

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
- Before Mike's checkpoints, write any spec deviations found during the build into the Amendments section, and present any value-changing ones to him as a decision.
- **Checkpoints on live, in order:**
  1. `persona assign <asset> <persona>` + `data fetch <asset> --dry-run`.
  2. `./run-daily.sh <asset>` (first real fetch → blocked → bootstrap journal). Record observation counts before and after. Then check:
     - The `signal_id` stamp and `generated_at` are today. A future date means a future-dated row set the as-of. Every metric then reads stale and the grade falls to D.
     - Blocked only on `no_assumption_set`, at the grade you expected.
     - The bootstrap journal's `open_questions_json` (`sqlite3 orion.db "select open_questions_json from journal where asset_id='<x>'"`). The analyst flags real defects there; answer each one in the report.
  3. Calibration packages.
  4. First signal.
  5. The cron line.

## 6. Report shape Mike accepts
Per asset: holder-flow mechanism → what's config-only → what needs code → live numbers (30/90/365 annualized, market cap multiple) → open decisions. End with a recommended sequence and a short numbered list of decisions. Keep RPC keys out of chat output and commit messages; `.env` is git-ignored. If Mike pastes a key in chat, save it and mention it is now in the chat history (rotation is his call).
