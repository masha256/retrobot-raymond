# Data sourcing, protocol revenue and holder-yield reporting

Use when Mike asks to record a new series (growth, revenue, yield), to cut a third-party dependency, or what it takes to get data "directly".

## Sourcing policy (Mike's rules)
- **Prefer direct on-chain or first-party APIs.** Don't add new general DefiLlama dependencies for new assets. Protocol-specific feeds are fine where they are the natural source (Llama Airforce for CRV bribes stays).
- **Store daily totals only, never raw transfer/event logs.** Mike won't grow the DB with per-transaction rows; any new bucket or metric must be derivable from daily totals (or a re-scan of the chain).
- Keep historical pricing on CoinGecko; rebuilding price history on-chain is slow and RPC-heavy. Keyless CoinGecko stops at 365 days, which bounds every backfill.
- VVV revenue is disclosure-based; its only daily series is DefiLlama. Keep it as a labelled proxy next to the disclosures, not as the official figure.

## DefiLlama usage audit
When Mike asks where Orion relies on DefiLlama: `grep -nE 'llama' assets/*.yaml` and map each hit to its metric (`awk` back to the nearest `^  <metric>:` line). Split into primary inputs (feeds tables/valuation), labels/context only, and cross-checks (`coins.llama.fi` price checks, one request per asset per run). `llama.box` is Curve's community site, not DefiLlama. Flag duplicates (HYPE pulls the same number as both `af_buyback` and `revenue_proxy`) and note that scratch backfills re-pull full histories, so they are the main load, not nightly runs.

## Inventory before proposing a build
Grep the asset configs for every `type:` per asset and classify each third-party source as **primary input** (moves the valuation) vs **cross-check**. Lead the reply with the primary dependencies; cross-checks are cheap to replace later. Order the build: shared engine capability first (e.g. multi-sink `transfer_flow`), then on-chain series on chains with a keyed RPC, then own pool quotes (they give price checks AND the pool depth the slippage haircut needs), then non-EVM APIs (Hyperliquid) after a history-depth test, and protocol rebuilds pinned to their migration dates.

## Protocol revenue = the protocol's cut, not emissions received
For lockers/aggregators, the CRV they collect from gauges mostly passes through to LPs. Record the protocol's retained cut as revenue and the gross CRV received as a separate volume line. Read the fee rates from the contract and confirm them against measured transfer ratios before relying on them.

Measured routes (Ethereum, 91 days; probe with `scripts/onchain_probe.py` `io(addr)`):
- **Curve:** every protocol fee passes FeeAllocator `0x22530d384cd9915e096ead2db7f82ee81f8eb468` (in from the Hooker `0x9a9df35cd8e88565694ca6ad5093c236c7f6f69d`), split 90% to FeeDistributor `0xd16d5ec345dd86fb63c6a9c43c517210f1027914` / 10% to Curve treasury `0x6508ef65b0bd57eabd0f1d52685a70433b2d290b`. One stream = Curve's revenue.
- **Convex:** CRV from VoterProxy `0x989aeb4d…` into the Booster `0xF403C135…`; Booster getters `lockIncentive` 1000 (cvxCRV stakers, to `lockRewards()`), `stakerIncentive` 450 (CVX stakers, `stakerRewards()`), `platformFee` 200 (`treasury()` `0x1389388d…`), `earmarkIncentive` 50 (callers), out of `FEE_DENOMINATOR` 10000. Measured outflows match to 4 decimals, so revenue = 17% of gross CRV. crvUSD fees pass 100% via `lockFees()` to cvxCRV stakers.
- **StakeDAO:** Accountant `0x93b4b9bd266ffa8af68e39edfa8cfe2a62011ce0` `getProtocolFeePercent()` = 16.5% (1e18 scale) on strategy CRV, sent to FeeReceiver `0x60136fefe23d269af41ab72de483d186dc4318d6`, which splits about evenly to VeSDTRecipient, TreasuryRecipient and the CurveAccumulator (sdCRV). Plus the 15% of crvUSD fees the accumulator keeps (10% LiquidityFeeRecipient, 5% TreasuryRecipient).
- **Yearn (yCRV):** YCRVSplitter `0x05fc8174050f0a41deb7e562187911d45cd5e401` → Receiver `0x642a16a7…` → 90% SingleTokenRewardDistributor / 10% fee. The splitter also sends 20% of its vault shares straight to Yearn's SimpleTreasuryVault `0x044f9c86a0da637a235e83564215dc271bc0defc`, so Yearn's cut is about 28% of what the splitter mints, not 10%. Revenue = yvcrvUSD into `0x044f…` from splitter+receiver (needs `share_price`); gross = crvUSD into the splitter from the voter and the FeeBurner.
- **HYPE:** Hyperliquid `info` `userFillsByTime` on the Assistance Fund gives its own buy fills on spot pair `@107` (HYPE/USDC; side `B`), but the API keeps only ~10–12 days of fills. A direct series can't be backfilled: it grows forward from go-live, so keep DefiLlama feeding the valuation until the direct series has ~180 days and matches. Test history depth before promising a backfill from any non-EVM API.
- **Lighter (LIT), first-party, keyless:**
  - `GET <host>/api/v1/exchangeMetrics?period=all&kind=<k>` returns a kind's whole daily history in one reply, as `{timestamp: UTC day start in s, data: USD}`. The last point is today's partial day, so drop it.
  - Hosts: Core `mainnet.zklighter.elliot.ai`; the Robinhood instance `api.rh.lighter.xyz`, a separate exchange with its own fee account 0 and no LIT market.
  - Revenue kinds: `maker_fee`, `taker_fee`, `transfer_fee`, `withdraw_fee`. `liquidation_fee` goes to the LLP. Also `buyback`/`buyback_usdc`.
  - Lighter keeps 50% of Robinhood fees. DefiLlama reads these same endpoints but counts RH at 100%.
  - Staked LIT = the LIT balance of the pool account named by `/systemConfig.staking_pool_index`, read from `/account?by=index&value=<pool>`. Match the asset by `symbol`, never by position. Daily rewards are in `explorer.elliot.ai/api/accounts/<pool>/logs`.
  - Account balances have no history endpoint, so those levels start at go-live.
  - Real reward transfers in the explorer logs carry `status: nothing_to_execute`, so never filter rewards on `status`.
  - When an adapter sums several kinds per day, refuse a kind whose reply has no completed day (`metrics: []`, or today's row only). Counting it 0 silently gives a partial sum that understates revenue. A day missing inside a kind's own range is also a refusal; only days before that kind's first day count 0.
  - Holder flow is the Core treasury's buys only (≈99% of Core fees). The RH fee account (RH `/account?by=index&value=0`, `total_asset_value`) holds both halves of RH fees and has never traded, and RH `buyback_usdc` is ~0. So Lighter's 50% RH share is retained, not bought back. Keep it out of holder flow and watch the account and the RH buyback series. A sustained RH buyback is a valuation change for Mike (a second holder-flow member), not a config tweak.
- **Before proposing a revenue-source swap, recompute the report lines over Orion's exact window.** Take the window end from `max(observed_at)` of the current stream (day-end stamps, so end = that day − 1) and `report yield <a> --json` for today's figures. Show before → after for revenue, paid to holders, protocol income, payout ratio and volume. A "protocol income" line that shrinks to a real retained share (LIT: the RH half) is the check that the new source is right.
- **A split that exists only in a web app's code** (Lighter's 0.5 on RH fees): fetch the page HTML, then the entry bundle it references, then the chunk the entry names. Anchor the regex on stable literals (the fee-kind strings inside a `new Set([...])`, then `return <set>.has(<arg>)?<n>:1`), never on minified identifiers, which change every build. Refuse zero or two-plus matches, so a new build fails the read loudly instead of returning a guess. Use it as a watched display level next to a cited config constant, not as the stream's live multiplier: the constant has no history for backfilled days, and a broken parse shouldn't stop the revenue line.
- **Unverified contracts:** resolve an unknown recipient with Blockscout `/api/v2/addresses/<a>` and `/api/v2/smart-contracts/<a>` (name, verified source) before stating a protocol's cut; an unexplained outflow is often a second fee leg.

To trace a new protocol: start at the address that receives the gross, `io()` it, read every fee getter on the router, then reconcile getter rates with measured outflow ratios.

## Auditing an asset's revenue figure ("are we missing something big?")
Goal: find material streams missing from the revenue figure. Small fees (gas, priority fees) are rounding errors, so don't chase them.
1. **Pull every DefiLlama view, not just the one Orion stores.** Fetch the parent slug's `dailyFees`, `dailyRevenue`, `dailyHoldersRevenue`, `dailySupplySideRevenue` and `dailyProtocolRevenue`, plus `totalDataChartBreakdown` (by child product), and annualize each one over Orion's window. Fees minus supply-side minus revenue should come to about 0. Each `childProtocols[]` entry carries `methodology` and `breakdownMethodology`, which list the streams the adapter claims to count.
2. **Read the adapter source** (`raw.githubusercontent.com/DefiLlama/dimension-adapters/master/<dexs|fees>/<slug>/index.ts`). That's how you see which streams are commented out or fed by inputs that may be empty.
3. **Test each claimed stream in the data.** Plot the daily revenue/fees ratio across the stream's start date and its first payment. If it stays flat, the stream is in the methodology but not in the numbers (HYPE: the USDC reserve-yield input reads zero).
4. **Cross-check against Token Terminal's revenue methodology** (it lists the products it counts) **and Artemis's last-12-month revenue**. Search news for new revenue programmes from the last ~6 months.
5. **Size the gap from the protocol's own docs and the first actual payment:** the accrual rule, the payment interval, and the amount over the days covered. Report the revenue and P/E effect, the growth-window effect, and the rate sensitivity.
6. Log the finding in the dev queue (`workspace/orion/dev-queue-revenue.md`). Don't build anything until Mike has reviewed every asset in the batch.

### Periodic and lump-sum revenue (design rule, Mike)
- **No one-off series per revenue type.** Revenue is a config list of streams, and a new type is config only. Each stream has a source and a settlement mode: `daily`, or `periodic` (lump payments with a known coverage period).
- **Spread a periodic payment evenly across the days it covers,** so the 90d windows line up with when it was earned, not when it was paid.
- **Days earned but not yet paid:** if the protocol documents a daily accrual (balance × an on-chain rate, as with Hyperliquid AQAv2), compute them from that rule. Fall back to the last period's daily rate, marked provisional, only when the inputs can't be read. Replace either with the actual payment when it lands.
- **Read rate-driven yield from the protocol itself, daily** (e.g. the on-chain AQA rate), never a fixed % or a T-bill proxy, so a change of manager/issuer, fee or methodology shows up automatically. Store daily rate, balance and earned amount plus the manager addresses; alert on rate jumps, manager change, a payment that differs from the summed accruals by >2%, and a late payment. The payment is the truth; accruals fill the gap until it lands.
- **A new stream inflates 90d/90d growth** until it has been in both windows (about 180 days). It's real income, not an error, but annualizing a one-time step reads as compounding. Show growth both with and without streams younger than 180 days.

## Holder-yield buckets (report-only)
Log each asset's holder flow in three separate daily buckets so later metrics can sum any subset:
1. **Burns:** bought back and destroyed. No haircut (the purest form).
2. **Holds:** bought back and kept. An overhang haircut, set the same way as slippage.
3. **Cash payouts:** stablecoins and liquid tokens, minus a slippage haircut per token sized from pool depth (fixed per-token percentages, reviewed periodically, not live quotes).

Yields on price, tradfi-style: cash yield, buyback yield (burns + haircut holds), shareholder yield (both), and net shareholder yield (minus emission dilution). Wrappers use per-staked-token yields. Growth per bucket and for protocol revenue: last 90d vs prior 90d, annualized.

Rules:
- **Report-only** unless Mike says otherwise: haircuts in the valuation would move every target and force recalibration of all assets.
- **Keep reporting tags in sync with the valuation config.** When a reporting-only reclassification would diverge from an asset's valuation tag (HYPE's fund buys and holds but is tagged burn), keep the valuation's tag in reporting too and note the economic view; don't let the two layers disagree silently.
- A first growth value needs 180 days of daily flows, so plan a ~362-day backfill (live write: backup + exact commands) to start with ~6 months of growth history.
- Show growth that lacks history as **pending** (needs 2 windows), and keep **n/m** for a zero or negative window. Mike reads n/m as "meaningless", not "not yet".
- Wrappers (yCRV, cvxCRV, sdCRV) show zero dilution of their own but inherit CRV's emissions; say so beside any table that ranks net shareholder yield across assets, or the wrappers look artificially clean.
- When an annualized 90d/90d comes off a tiny or fast-ramping base (VVV's revenue grew 13x in a quarter, which annualizes to thousands of percent), report it with the per-window change and say it isn't a trend. Don't present the annualized figure alone.

## Vetting a backfilled report series before trusting it
Monitor-only flows raise no `unlisted_sender` anomaly by design, so nothing flags a contaminated revenue total for you. After every report backfill:
1. Read the fetch output's `unlisted sender` lines for each report scan and triage every sender (procedure below). Unlisted senders are never counted, so the risk runs both ways: a real fee leg left off the allowlist understates revenue, and adding a non-flow sender to the allowlist inflates it.
2. Count rows per metric (`select asset_id, metric_key, count(*), min(observed_at) … group by 1,2`). A stream with far fewer days than its siblings (one cut at 148 days while the others have 362) is a coverage gap: find out why before summing the cuts.
3. Print monthly sums per series and eyeball them for jumps before computing growth.

### Triage unlisted senders
Use `scripts/onchain_probe.py` (`rpc`, `name`, `io`) on the senders listed in a `--dry-run --json` fetch (`sources[].unlistedTransfers`; the CLI lists only the first 50, so read the `N unlisted transfers in total` note too):
- **Zero-amount transfers** (reward stashes, distributors poking a sink) are noise; the scanner skips them.
- **Factory clones:** `eth_getCode` each sender. An EIP-1167 clone is `363d3d373d3d3d363d73` + 20-byte implementation + `5af43d82803e903d91602b57fd5bf3`, sometimes followed by immutable-arg bytes, so match on prefix + suffix rather than exact length. Group senders by implementation; dozens of senders usually collapse into one or two implementations, which go in `from_ignore_clones_of`.
- **Named contracts** (fee forwarders, other products' routers): find their owner/name on Blockscout. If they're the same protocol but a different product, put them in `from_ignore` with a why-comment in the YAML.
- **Mints from `0x0`:** the Transfer log's `from` is 0x0, so decode the tx receipt. The vault's ERC-4626 `Deposit(sender, owner, …)` event names the real depositor; the tx sender is often just a keeper, which is a weaker match.
- Before excluding a sender, measure what it would add (USD per year) and tell Mike when that's material (e.g. comparable to the series itself). An exclusion that removes half of a revenue line is a valuation-style decision for him, not cleanup.

Ignore rules on `transfer_flow`:
- `from_ignore: [names]` and `from_ignore_clones_of: [impl names]`: never counted, never reported. Both lists stay out of the scan key and source id, so cursors and history carry over. A name on both the allowlist and an ignore list is refused.
- They exist only to quiet the report: a correct ignore rule never changes a stored value. Verify this by fetching the same day before and after on one scratch `.backup` home with `data fetch <a> --backfill-days 1 --dry-run --json`. Copy only the changed asset YAMLs into the home between the two runs. Diff `written[]` flow values (expect identical) and per-source unlisted counts (expect →0), and report that diff.

A 362-day re-scan of several transfer streams on one asset takes tens of minutes (one `eth_getLogs` per day per scan). Scope every report backfill with `--metric <key>` (repeatable) to the new series only: a bare `data fetch <asset> --backfill-days N` re-scans every existing valuation stream too (VVV's burn scan alone ran ~30 min), which buys nothing and risks rewriting valuation rows.

Rehearse, then replay the same script live:
1. Write the backfill as one script that takes its commands from a single `ORION_HOME` line (mask keys with the `/v2/` sed, `echo EXIT=${PIPESTATUS[0]}` per fetch). Run it against a scratch `.backup` copy for timing, anomalies and unlisted senders.
2. Prove valuations didn't move: in the scratch home run `model run <asset> --json` for a few assets and compare `horizons['12m'].expected_target` and `data_quality.grade` from `signals.payload_json` (newest row) against the newest live signal for the same asset; expect identical values and `change.cause` none. Check `anomalies` for rows with `first_seen_at` after the run start (that table has no `created_at`).
3. For live, generate the script with `sed` replacing only the `ORION_HOME` line, so the live commands are byte-for-byte the rehearsed ones; list them verbatim to Mike. Start it clear of the nightly cron window, and afterwards confirm row counts per metric and that each asset logs one new day per series after the next tick.

## How the report layer is built (engine pattern)
- Report series are flow metrics with `monitor_only: true` (schema allows it on flows; still refused on anything the valuation reads). Ingest must exempt them from `unlisted_sender` anomalies and from failure streaks on sources that feed only monitor-only metrics, so report data never wakes the agent. The grade never reads fetch outcomes, so a failing report source can't move a signal.
- Per-asset `reporting:` block (optional, no default, so assets without it keep their hash): `window_days`, `haircuts` per holder flow (a burn's must be 0), `revenue`/`volume` metric lists, `revenue_disclosed` (VVV level), `extra_cash` (cash the valuation keeps outside holder_flows, e.g. CRV vote incentives).
- Yields, buckets, growth and PEG are computed on demand (`orion report yield [asset] [--json]`) from stored daily totals; nothing derived is stored, so any day can be recomputed and the DB grows one row per series per day.
- Adapters can be flow primaries returning a daily series (written like the DefiLlama API flow: cursor, revision days, a missing day is never written as zero).
- Adding the block to every asset moves every asset hash: re-pin each `*.ingest.test.ts`/cadence hash (compute with `parseAssetYaml(...).hash` via `node --input-type=module` on `dist/`), and update plan/source-list `toEqual`s and canned fakes (e.g. `decimals` for a new token, a `userFillsByTime` fake keyed on `startTime`). The VVV golden test passing proves valuations didn't move.
- Test pitfalls: the fake RPC ignores `to`, so to fail one specific scan wrap `getTransferLogs` and throw on `q.to`; the fake chain head is fixed, so a failure-streak test must run several attempts at `NOW + small offset`, not on later days. Add a control test showing the same failure on a valuation source still raises the streak.
- A new transport capability goes on the transport interface as an OPTIONAL method (e.g. `getCode` on `RpcTransport` for clone detection; `getText` on `HttpTransport` for HTML/JS reads, since it otherwise has only `getJson`/`postJson`). The adapter that needs it throws a clear error when it's absent, so other fakes and transports still compile. Also pass it through the run-level wrapper (`withRunCache` in `http.ts`, which `fetchAsset` puts around every transport): an adapter test on a raw fake passes, but in real runs the wrapper hides the method and the adapter always fails. Implement it in `viemRpc.ts` and in `tests/helpers/fakeRpc.ts` behind an option threaded through `fetchHarness` (e.g. `code: {addr: bytecode}`), with a call counter. Then a test can assert a cache: one read per sender per scan.

## Haircut sizing from pool depth
Quote each payout token's main pool with `get_dy` at a day's and a week's payout size; set the fixed haircut near the day-size impact plus a margin. Reference points: stables and redeemable vault shares 0; CVX 0.5%; CRV via TriCRV ~1% (day 0.6%, week 4.4%); sdCRV bribes paid in sdCRV 5% (sdCRV/CRV pool ~$1.5M: day 1.3%, week 9%); long-tail bribe/fee baskets 2–3%. Burns 0.
