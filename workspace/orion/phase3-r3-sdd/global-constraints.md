## Global Constraints

- No live read of CoinGecko or DefiLlama is added. After this release no code path calls `api.coingecko.com`
  (`/coins/markets` included); a config naming a `coingecko` source of any field is refused at load, filing and approve.
  The `coingecko` type and its code stay until R8 (spec §3.5).
- No migration. The release must run on schema 8; `orion-2026.11.15.1` must still run after it (rollback, Task 6).
- Value moves allowed: `circulating_supply` itself and what it feeds — `marketCap`, `incomeStatement.multiples.mcapTo*`,
  `incomeStatement.perToken.{revenue,grossProfit,holderFlow.*,dilution,circulatingSupply}` — plus provenance/source
  labels of that metric. Every other field (prices, flows, revenue, growth, PEG, every `yields.*`, `perTokenFdv`,
  dilution, grades) is byte-identical. Anything else in the proof is a stop.
- Staking rule (decision N1a): tokens in irrevocable long locks (veCRV, veAERO) are not circulating; staking with an
  exit (cooldown, fee-free withdraw) is circulating (LINK v0.2, lsSKY, VVV, LIT, HYPE).
- Every excluded address is a named `contracts:` entry with a comment carrying its citation or on-chain evidence.
- Tests: `export ORION_TEST_DATABASE_URL='postgresql://orion_dev@/orion_test?host=/var/run/postgresql'`;
  `npx vitest run --maxWorkers=2`, load-sensitive files rerun alone at `--maxWorkers=1`; `npm run typecheck`;
  `python3 -m unittest scripts/provision/test/test_orion_remote.py`. RPC only through `fakeRpc({ callsAt })` and fake
  HTTP/Solana transports; no network in any test.
- Commit with explicit `git add <paths>`; never `-a`. Implementers never use the network, ssh, a `.env`, or a live DB.


## Review Focus

1. **A rebuild at a block where a term's contract did not exist yet** (CRV grant escrows, AERO's new token, a vault
   created later): the row is refused and listed, keeps its CoinGecko value, never a partial sum. Pinned in Task 5.
2. **A `view_sum` term that reverts at the run block** (an unverified Safe, a `take()` on an upgraded converter): the
   level fails (source failure, grade drop), never a sum missing one term. Pinned in Task 1.
3. **The LIT schedule across tranche boundaries** (exactly 2027-01-29T00:00Z, the last tranche, a run after full
   vesting): locked never negative, 0 after the last tranche. Pinned in Task 1.
4. **A Hyperliquid wallet with spot only, staked only, or a pending withdrawal**: all three counted; an unknown address
   (empty reply) is 0, not an error. Pinned in Task 2.
5. **A purge run before the rebuild**: refused for every EVM asset row that a rebuild could replace
   (`purge_unreplaced_supply_level`); allowed and listed (`withoutReplacement`) only for the not-rebuildable set.
   Pinned in Task 5.

---

