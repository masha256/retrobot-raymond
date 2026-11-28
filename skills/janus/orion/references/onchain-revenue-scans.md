# On-chain revenue scans (pool_scan class: multi-chain DEX fees, incentives, on-chain pricing)

Depth for a release that replaces a third-party revenue series with Orion's own multi-chain read (AERO's
`pool_scan` was the first; HYPE/PUMP/CRV follow the same shape). Read before scoping or planning such a release.

## Scoping
- Measure chains before pinning any value: a throwaway `.probe/*.mts` inside the release worktree (viem and tsx
  resolve only from that worktree's `node_modules`, not from `$TMPDIR`), reading the key from `orion/.env`, piping
  output through `sed -E 's#/v2/[A-Za-z0-9_-]+#/v2/***#g'`, and `rm -rf .probe` after. Per chain record
  `eth_chainId`, mean block time over ~200k blocks, and the widest `eth_getLogs` span the provider accepts
  (probe 10k/50k/100k/500k/1M blocks). The Alchemy key works across chains by swapping the subdomain
  (`opt-`, `arb-`, `ink-`, `robinhood-`, `arc-`, `elysium-mainnet`); Ink caps getLogs at 10,000 blocks.
- Never trust a protocol's GitHub deployment files for the chain list: read the protocol's own registry on chain
  (Aero: Base root Voter `chains()`), which found a chain the repo files lacked. Cross-check each sub-agent's
  headline finding with one read of your own before it goes into a spec.
- Reconcile scoping sums against the stored prod rows (pulled read-only) before trusting a sub-agent's DEV-REF
  comparison; a DefiLlama row stamped D covers UTC day D-1.

## Method rules (protocol-agnostic)
- Day boundaries: `s` = first block >= D 00:00Z, `e` = first block >= D+1 00:00Z, found by timestamp search;
  read state at `s-1` and `e-1` (a call at block N returns the state after N).
- Read each factory's own tape/accumulator getter; never assume one address per protocol (Arc Lite used
  different tapes). Pools absent at `s-1` start at 0. Pools not registered with the tape record nothing: count and
  list them, and treat a gauge on one as drift.
- A cumulative fee counter gives gross; the allocator/voter share usually needs a log scan (pending delta +
  collected events): a state-only estimate from reward-per-vote indices blew up near zero voting supply.
- Incentive streams: allocator-earned = rate x (overlap with the day - zero-allocation seconds), from contract
  state; class them by creator address from a reviewed list. Mirror the contract's lazy weekly checkpoint backfill
  (read `supplyAt(w-1)` for each week boundary skipped since the last checkpoint): lock ends are week-aligned, so a
  pool's last allocation expiring at a boundary otherwise reads as > 24 h of zero allocation until someone
  checkpoints, and a legitimate state fails the run.
- Read the allocator's pending fees on the pool side (CL `gaugeFees()`, V2 `pendingFees(gauge)`), not the gauge's
  own getter, which returns 0 while the gauge is unactivated or capped.
- Pricing with no CoinGecko/DefiLlama: reviewed anchor token ADDRESSES -> Chainlink USD feeds (description()
  checked on chain), then a deepest-pool graph with a priced-side depth floor and a hop cap, then the token's own
  pool, then unpriced. Never match anchors by symbol (Base has several "USDC"s and a spoof LINK). Never use
  tokenized-stock feeds as anchors (stale over weekends/holidays). Take the stable/volatile curve from the creating
  factory (`stable()` reverts on stable pools). A chain with no feeds can anchor on another chain's feed read at
  the matching timestamp, with Mike's sign-off.
- A live coverage percentage cannot divide by a DEV-REF value: value the still-unpriced fees with a floorless graph
  (coverage only, never stored).
- Enforce "no tokenized-stock anchors" in the adapter's `validateParams` (anchor feed `description()` must be on a
  fixed crypto/stable allowlist): the pricing code trusts whatever anchors config lists.
- A null read (revert or decode failure) of anything a number depends on must fail the chain-day, never default:
  a null `s-1` accumulator read as "absent" puts a pool's lifetime fees into one day, a null registration read
  silently drops the pool, a null pending reads as 0. The only legitimate null is a pool created during the day
  (no code at `s-1`), and that needs a successful `s-1` pool-count read to prove it. Treat negative per-pool deltas
  (gross or allocator) as failures too: counters are monotonic and a negative allocator means missed logs.
- Read pools from each factory's LIVE tape getter at `e-1` and only compare it with config (drift warn): reading the
  config tape after a migration gives stale or zero gross with only a warning.

## Orion code pitfalls (where a new adapter family plugs in)
- The series writer used to stamp every adapter row `api` and treat other origins as foreign: a `pool_scan`
  (origin `onchain`) series must take its origin from provenance, or it conflicts with its own rows and stalls.
- Build any per-chain RPC on `priceRpcFactory ?? rpcFactory`: levels/refresh wrap `rpcFactory` to record the fetch
  block, so another chain's `latestBlock()` would become the asset's stored `block_number`.
- A new anomaly kind needs a migration (the `anomalies_kind_check` constraint): route adapter warnings through the
  existing advisory `cross_check_mismatch` with a namespaced dedupe key.
- Existing check types (`sum`, `coverage`, `two_path`) compare window sums with a symmetric tolerance: a one-sided
  bound (allocator <= gross) or a per-chain coverage floor goes in the adapter (fail the run / warn).
- Income statement schema: `scope` is `complete | protocol_share_only | partial`; below-line `to` is `holders |
  protocol`; `started` zero-fill and short-window annualizing apply to revenue lines only (cost/holder lines inherit
  through `of`). A series with no 91-day history needs revenue lines with `started`, CRV's two-revenue-line shape
  (each passed on whole with `of`) so unreconciled is exactly 0, and the statement-level `history_start` key (window
  label "N of 91 days" + growth null until the prior window starts on or after it). Never key a statement-wide guard
  on line-level `started`: HYPE and LIT each carry one young `started` line inside a full history, so such a guard
  nulls their published growth and PEG. A recycled-subsidy line that is shown but not holder flow is a below-line
  line with `in_holder_flow: false` (needs a `note`). Check every enum against `src/config/incomeStatement.ts`
  before writing it into a spec.
- Adapters run once per metric with no RPC cache: memoize a multi-metric scan per run context (a WeakMap on the
  SourceContext). The series writer throws on an empty series, so return at least one day every run.
- Run warnings are deduped per metric request, not per run: emit scan-level warnings (drift, coverage, dropped
  anchors) from ONE metric of the set (the monitor-only gross metric), or each posts once per metric.
- Give a history-limited adapter a `since` date param and set it on every metric: routine runs scan the oldest
  missing days first, and days before the contracts existed fail every nightly.
- Retiring the old metric key (new keys for the new series) lets one `data purge <asset> --metric <old> --yes`
  remove every source type of it (third_party and derived corrections) plus its cursor; keeping the key needs a
  two-step purge before any backfill.
- `CHAINS.maxLogRange` (Base 2,000) is tuned for transfer scans; a once-a-day scan should carry its own per-chain
  `log_range` from the measured provider span (1M on Alchemy except Ink 10k), or Base costs ~216 getLogs/day.
  Don't change the CHAINS row itself: transfer_flow assets would move.
- Test fixtures: trim them from the scoping `raw/` day files, mark any invented datum `"synthetic": true`, and have
  the reviewer diff fixture pools against the raw files by script, so expected values aren't circular.
- Backfill jobs: `job run-now backfill <a> --metric <k>` (repeatable) `--backfill-days N` (<= 400, one attempt, kept
  clear of the nightly). For a long multi-chain history, cap days scanned per run in the adapter (oldest missing
  first, from the stored days) and loop the job, so a lost lease costs one chunk.
