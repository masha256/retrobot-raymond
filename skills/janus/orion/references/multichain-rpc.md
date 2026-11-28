# Multi-chain RPC facts (measured 2026-11-27, R4 / RET-20)

- Mike's Alchemy key (ORION_BASE_RPC_URL in /home/hermes/git/orion/.env) works on other chains by swapping the subdomain: opt-mainnet, arb-mainnet, ink-mainnet, robinhood-mainnet, arc-mainnet, elysium-mainnet. Never print the key; mask `/v2/***`.
- Chain id / mean block time / eth_getLogs span: OP 10 / 2.0 s / >=1M; Arbitrum 42161 / 0.30 s / >=1M; Ink 57073 / 1.0 s / **10,000 cap**; Robinhood 4663 / 0.11 s / >=1M; Arc 5042 / 0.51 s / >=1M; Elysium 99901 / 0.15 s / >=1M. Elysium is not in vendored viem 2.56.8 (defineChain).
- Aero runs on 8 chains, not 7: Base root Voter 0x49d7d4f17Ec56Ef8fA04E464AF5D1A4942CC31e6 `chains()` lists 8453,10,1,42161,57073,4663,5042,99901. Elysium is missing from dromos-labs deployment JSONs; trust `chains()` and the docs security page. Arc also has 'Aero Lite' factories with their own tapes — read each factory's poolTape()/clPoolTape().
- Ad-hoc viem probes must run from inside the repo/worktree (a script in $TMPDIR can't resolve 'viem'); put it in a temp dir in the worktree and delete it after.
- The execute_code sandbox has no pycryptodome; keccak needs the repo's node/viem or a pure-python implementation.
