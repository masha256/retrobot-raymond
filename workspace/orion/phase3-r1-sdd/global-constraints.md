## Global Constraints

- No new live read of CoinGecko or DefiLlama. CoinGecko/DefiLlama in dev-time probes only, labelled "dev-only reference".
- AERO's report is byte-identical (R1 does not touch `assets/aero.yaml`).
- Revenue, cost of revenue, holder flow, yields and grades of all 13 assets are unchanged. The only value moves allowed
  are listed in Task 7's allowlist; anything else is a stop.
- Migration 0007 is expand-only (no `-- breaking` line): `orion-2026.11.11.1` must still run on schema 7 (rollback).
- New options default to "absent changes nothing": an asset that doesn't use them keeps its config hash and its
  report bytes.
- Out of scope here: HYPE `af_buyback`/`revenue_proxy` (R5), PUMP `llama_revenue` and `solana.supply_burn_daily`
  history (R6), CRV `llama.box` (R7), AERO `flow_usd.fees` (R4), every price and circulating primary (R2/R3), the
  `defillama`/`coingecko` source types and `identifiers` (R8).
- Tests: `export ORION_TEST_DATABASE_URL='postgresql://orion_dev@/orion_test?host=/var/run/postgresql'`;
  `npx vitest run --maxWorkers=2`, load-sensitive files rerun alone at `--maxWorkers=1`; `npm run typecheck`;
  `python3 -m unittest scripts/provision/test/test_orion_remote.py`.
- Commit with explicit `git add <paths>`; never `-a`.

## Plan decisions (Mike's go on the plan covers these)

- **P1 Backfills run as a daemon job, not a long SSH session.** `job run-now backfill <a> --metrics ... --backfill-days N`.
  The daemon's single worker runs it at priority 70 (after refresh, nightly, push, levels, watch), with no automatic
  retry. If the env's next nightly slot is less than 4 h away when it starts, it defers to 2 h after that slot. Why not
  a synchronous verb: a multi-hour SSH call dies with the connection, and it races deploys (a switch drains the daemon,
  not a stray CLI process).
- **P2 `data purge` is a remote verb that dry-runs by default.** `--yes` deletes, after writing the rows to
  `$ORION_HOME/purged/<asset>-<metric>-<UTCstamp>.json`. It refuses (a) the rows of a metric's current source type,
  (b) a metric with an open anomaly, and (c) a kept row that references a deleted row. Prod purges run only on Mike's go.
- **P3 R0b and R1 ship as one release** (0007 is expand-only; R1's value moves are the two below).
- **P4 Unlock citations.** LIT: Lighter's own post (team 26%, investors 24% = 500M; 1-year lock, 3-year vest; the
  monthly tranches from 2027-01-29 stay as approved in proposal #3). The next-365-day figure goes from 138,796,789
  (DefiLlama's 499.67M) to 138,888,889 (+0.066%). PUMP: pump.fun has published no vesting schedule (searched
  2026-11-12). The plan cites the allocation sizes (team 20%, investors 13% = 330B) and the lock/vest terms (12-month
  lock from 2025-07-12, then linear for 3 years). It prefers a pump.fun page if Task 4 finds one, and otherwise uses the
  Blockworks Token Transparency filing (compiled by Blockworks, labelled so). The value is unchanged: 82.5B a year. If
  Mike doesn't accept a non-issuer citation, PUMP's `unlocks` line goes `not_measured` (dilution becomes null), which
  is a value change he would have to approve.
- **P5 R1 drops checks without replacing them.** LIT's buyback check (fills vs the treasury's LIT balance, a
  `two_path`) and VVV's `usage_index` watch are built in R3, not here. Until R3, LIT's buyback and VVV's burn have no
  external check (LIT's and VVV's own reconciliation checks stay).
- **Dropped from §3.4:** `db backfill-provenance` (gone since 0006) and `data backfill-tokens` (one-time Phase 2 fill,
  done on both envs). R2 adds its price-history rebuild as a second `backfill` op (`op: prices`) on this job kind.

## Review Focus

- A `backfill` job queued while the nightly runs: it must wait (priority) and never delay the nightly's refreshes.
  The test is in Task 1.
- A deploy `switch` while a backfill runs: the drain waits for the job or the lease expires. It must never re-run
  automatically under the new release (max_attempts 1). The test is in Task 1.
- `data purge` on a metric that is still configured, without `--source-type`, or with the current source's type:
  refused, nothing written. The test is in Task 2.
- `orion-remote` given `--metrics a,,b`, a metric with uppercase or `/`, or `--backfill-days 0` / `401`: refused with
  exit 64 before Orion runs. The test is in Task 3.
- An unlock schedule whose tranche dates straddle `now + 365d` exactly, or a linear vest that ends inside the window:
  only the part inside (now, now+365d] counts. The test is in Task 4.

---
