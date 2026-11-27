R4 AERO revenue on chain (pool_scan pilot) — controller ledger
Linear: RET-20

- 2026-11-27 setup: Build with Hermes (superpowers). Branch ret-20-aero-pool-scan, worktree .worktrees/ret-20-aero-pool-scan, base GitHub main 2635cae (orion-2026.11.21.1). d422944 = .hermes-linear.yaml. Fresh npm ci (no identical lock elsewhere).
- 2026-11-27 baseline at d422944: vitest --maxWorkers=2 156 files / 2032 tests passed, 0 skipped; typecheck clean (EXIT 0).
- Stage: brainstorm (architectural). Scoping subagents running: code-and-data.md, onchain-revenue.md, incentives-and-events.md in workspace/orion/phase3-r4-scoping/.
- 2026-11-27 scoping back (code-and-data.md, onchain-revenue.md, incentives-and-events.md). Controller checks: (a) own viem read: Base root Voter 0x49d7…31e6 chains() = [8453,10,1,42161,57073,4663,5042,99901]; elysium-mainnet chainId 99901 -> 8th chain is real. (b) per-day sums of subagent dl_rev vs stored prod rows (D+1): 10-23 246059/246065, 11-01 136049/136051, 11-15 282272/282284, 11-25 304143/304151, 11-26 267509/270768 (-1.2%, DL revision after our pull; immaterial). Allocator/gross 0.885-0.952.
- Brainstorm Q1 asked: revenue definition.
