# Rules for every Phase 3 R3 implementer (binding)

Worktree: /home/hermes/git/orion/.worktrees/phase3-r3 (branch feat/phase3-r3-supply). Work ONLY there.

Never:
- touch /home/hermes/git/orion (the live checkout), any other worktree, or anything under ~/.hermes;
- push, merge, rebase, tag, or switch branches;
- use the network, ssh, a live/prod database, or a `.env` file (none exists in this worktree; don't create one);
- stage `node_modules` (it is a real directory from `npm ci`; never `git add -A`/`git commit -a`; stage explicit paths);
- edit files outside your task's file list except one-line repoints the dispatch names;
- write to skills or memory; dispatch subagents (no helpers, no reviewers).

Tests:
- `export ORION_TEST_DATABASE_URL='postgresql://orion_dev@/orion_test?host=/var/run/postgresql'` first.
- Focused runs while iterating: `npx vitest run <files> --maxWorkers=1`.
- Before committing: `npx vitest run --maxWorkers=2` then `npm run typecheck`. Load-sensitive files time out under
  the full run (tests/cli/{cli,ingest.cli,tick.cli,agent.cli}.test.ts, tests/agent/disclosure.e2e.test.ts,
  tests/app/tick.test.ts, tests/assets/{lit,sky}.ingest.test.ts, tests/push/gitPublisher.test.ts): rerun any failing file alone at `--maxWorkers=1` before
  calling it real; report both runs with real counts, and name every failing test.
- Python (orion-remote): `python3 -m unittest scripts/provision/test/test_orion_remote.py`.
- TDD: write the failing test, run it (RED, record the output), implement, run (GREEN).

Spec/plan: the brief is your requirements, with exact values to use verbatim. The spec is
docs/superpowers/specs/2026-11-09-orion-phase3-third-party-removal-design.md; read only the sections the brief names.

Conventions (from the codebase): new options default to "absent changes nothing" — an asset that doesn't use a new
option keeps its config hash and report bytes; refuse unknown keys in validateParams/zod (strict); OrionError(code,
message) for refusals; migrations are schema-unqualified and carry a header comment; a hash pin may move only for the
assets your task changes.

Report: write the full report (what, tests with RED/GREEN evidence, files, self-review, concerns) to the report path
in your dispatch; return only status, commits (sha + subject), a one-line test summary, concerns, report path.

R3 specifics:
- No RPC or HTTP in tests: use `fakeRpc({ callsAt })` (see tests/ingest/adapters.evm.test.ts) and fake HTTP/Solana transports.
- Values in test fixtures come from the brief, `task-N-values.md` in the SDD dir, or the scoping files (read-only; never edit):
  /home/hermes/.hermes/profiles/raymond/workspace/orion/phase3-r3-scoping/{README,code-and-data,crv-wrappers,link-uni,sky-lit,cake-vvv-aero,hype-pump}.md
  (reading those files is the one allowed exception to "nothing under ~/.hermes").
- Never write a CoinGecko or DefiLlama read into live code. Never call any pump.fun host (PUMP reads only ORION_SOL_RPC_URL).
- Baseline at 84cc9d2: vitest 1977/1977 (154 files), typecheck clean.
