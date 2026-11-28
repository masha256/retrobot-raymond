R4 AERO revenue on chain (pool_scan pilot) — controller ledger
Linear: RET-20

- 2026-11-27 setup: Build with Hermes (superpowers). Branch ret-20-aero-pool-scan, worktree .worktrees/ret-20-aero-pool-scan, base GitHub main 2635cae (orion-2026.11.21.1). d422944 = .hermes-linear.yaml. Fresh npm ci (no identical lock elsewhere).
- 2026-11-27 baseline at d422944: vitest --maxWorkers=2 156 files / 2032 tests passed, 0 skipped; typecheck clean (EXIT 0).
- Stage: brainstorm (architectural). Scoping subagents running: code-and-data.md, onchain-revenue.md, incentives-and-events.md in workspace/orion/phase3-r4-scoping/.
- 2026-11-27 scoping back (code-and-data.md, onchain-revenue.md, incentives-and-events.md). Controller checks: (a) own viem read: Base root Voter 0x49d7…31e6 chains() = [8453,10,1,42161,57073,4663,5042,99901]; elysium-mainnet chainId 99901 -> 8th chain is real. (b) per-day sums of subagent dl_rev vs stored prod rows (D+1): 10-23 246059/246065, 11-01 136049/136051, 11-15 282272/282284, 11-25 304143/304151, 11-26 267509/270768 (-1.2%, DL revision after our pull; immaterial). Allocator/gross 0.885-0.952.
- Brainstorm Q1 asked: revenue definition.
- Q1 answered (Mike): A — revenue = gross pool fees (tape); LP share cost line; holders = allocator fees; incentives below the line.
- Q2 answered (Mike): cover all 8 chains now incl. Elysium (Base Chainlink anchors) and Arc Lite pools (per-factory tapes).
- Q3 answered (Mike): two below-line lines — vote_incentives (third parties + 0x80f7 issuer-token programs; holders, cash, haircut) and protocol_subsidy (0x7269 TGE + 0x42255 governance multisig; shown, not holder flow). Keyed on creator address, reviewed list in config.
- Q4 answered (Mike): Chainlink anchors (reviewed addresses, no tokenized-stock feeds) + deepest-pool graph, 30-min TWAP on CL edges, spot on V2, $10K floor, 3 hops; own-pool fallback; rest unpriced.
- Q5 answered (Mike): run rate over measured days labelled 'N of 91 days'; growth not meaningful until a full 91-day prior window exists (~2027-04-22).
- Design section 1 (architecture) approved: approach 1, shared memoized scan, new metric keys, core changes listed.
- Design section 2 (income statement) approved. Controller note for spec: lp = gross - allocator by construction, so the sum check is replaced by an allocator<=gross per chain-day bound (fail past 0.5%/$1) — flag in section 3 message.
- Design section 3 (history/cutover/errors + allocator<=gross bound) approved.
- Design section 4 approved. Spec written + self-reviewed: docs/superpowers/specs/2026-11-27-orion-phase3-r4-aero-pool-scan-design.md, commit 9b44bc9 pushed to GitHub ret-20-aero-pool-scan; synced to Linear doc feffc623. Waiting: Mike's spec review (Blocked label).
- Spec APPROVED by Mike (RET-20 thread). Writing plan.
- Controller measurement 2026-11-27 ~12:45 PT (eth_chainId, avg block time over last 200k blocks, eth_getLogs span probe on Alchemy): op 10 2.0s ok>=1M; arb 42161 0.3048s ok>=1M; ink 57073 1.0s cap 10000; robinhood 4663 0.1123s ok>=1M; arc 5042 0.5081s ok>=1M; elysium 99901 0.151s ok>=1M.
- Plan 0149fb7 + IDs commit; synced: Plan doc 0ee9be4a, T1..T10 = RET-196..RET-205. Spec re-synced (scope complete, in_holder_flow). Waiting: Mike plan approval + execution method.
