# Orion rules for Phase 2 tail subagents (binding)
- Worktree only: /home/hermes/git/orion/.worktrees/phase2-tail (branch feat/phase2-tail, base main 0f4b2fe). Never touch /home/hermes/git/orion (its tree, orion.db, .env, dist/, backups/) or any other worktree (.worktrees/phase3, aero-supply, cake-pending-burn are other sessions' work).
- The old SQLite DB is retired: nothing reads it. No prod/stage access (no ssh), no RPC, no network, no Postgres outside the orion_test database.
- Tests: export ORION_TEST_DATABASE_URL='postgresql://orion_dev@/orion_test?host=/var/run/postgresql'. Full suite `npx vitest run --maxWorkers=2`, then `npm run typecheck`, `npm run lint:promises`; harness tests `/usr/bin/python3 -m unittest` in tools/phase2-proof (pytest is not installed). Load-sensitive files (tests/cli/*, tests/agent/disclosure.e2e.test.ts, tests/app/tick.test.ts, tests/push/gitPublisher.test.ts) may time out under load: rerun them alone with --maxWorkers=1 before calling a failure real; name every failure.
- Hash pins: only assets whose PARSED config changes may re-pin (`grep -rl <old hash> tests`); any other pin moving = stop and report.
- No push, no merge, no tag, no deploy. Stage files by explicit path (never `git commit -a`); never stage node_modules.
- Never edit files outside the repo (~/.hermes/profiles/raymond/scripts/*, cron prompts): those are controller rollout items; list them in your report instead.
- Migrations are append-only: never edit 0001-0005 (their sha256 is recorded on prod/stage).
