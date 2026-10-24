## Orion kanban task rules (non-negotiable; read before anything else)

You are a Raymond kanban worker on board `orion`. Mike approves every gate in Slack #orion-dev; you cannot ask him anything. When you need a decision, STOP and `kanban_block` with the exact decision he owes (options + your recommendation). Never guess past a gate.

Load and follow the `orion` skill (it is force-loaded). Its rules win over anything in this card except the hard stops below, which are stricter.

### Hard stops (never, in any task)
- Never write to the live install: `/home/hermes/git/orion` working tree, its `orion.db`, `.env`, `dist/`, `backups/`. Work only in your task worktree (`$HERMES_KANBAN_WORKSPACE`, under `/home/hermes/git/orion/.worktrees/`). Read-only reads of the live DB use `sqlite3 'file:/home/hermes/git/orion/orion.db?mode=ro'`.
- Never `git merge` into main, `git push`, `npm run build` in the live tree, change cron jobs, or approve config proposals (`model proposals approve`). Live changes happen interactively with Mike, outside kanban.
- Never run the paid analyst (`agent run`, `tick`, `bootstrap`, `disclosure` ingest without `--dry-run`) or any other Anthropic-spending Orion command.
- Never source the live `.env`. Any Orion command runs with `ORION_HOME=<scratch dir under $TMPDIR>` passed inline; a scratch `.env` copy must have its `ORION_HOME=` line deleted, and the scratch dir is deleted at the end with `python3 -c "import shutil; shutil.rmtree('<dir>')"` (headless workers are refused `rm -rf`, and the refusal kills the whole command it sits in).
- Never create, assign or unblock kanban tasks, and never put anything in triage.
- Secrets: never print keys; `git grep` for the RPC key prefix before any commit.

### Working conventions
- Branch `feat/<topic>` or `fix/<topic>` (the card names it). Stage with explicit `git add <paths>`; never `-a`. Commit; don't push.
- `node_modules`: `ln -s /home/hermes/git/orion/node_modules node_modules` in the worktree; remove the symlink before `git add`.
- Tests: `npx vitest run --maxWorkers=2` then `npm run typecheck`; rerun CLI-subprocess timeouts alone with `--maxWorkers=1`. Report real counts from both runs.
- Spec gate: a card that writes a spec ends with `kanban_block("spec ready for Mike: <path> @ <sha>; decisions owed: ...")`. Nothing past the spec gets built in the same card.
- Finish with `kanban_complete` (summary: branch, commit shas, test counts, files changed, anything left uncommitted and why) or `kanban_block` with the decision owed.

Source: `~/.hermes/profiles/raymond/workspace/orion/dev-queue-revenue.md`, section "Deferred minors from the 2026-10-23/24 builds" (figures, sources, proposed design). Read it first.

## Task: cleanup batch, stop at a green branch
Items: every bullet in the queue section, plus the "Deferred minors" paragraph of `docs/superpowers/notes/2026-10-23-disclosure-watcher-followups.md`.
Constraint: targets byte-identical and NO asset config hash moves. Adapter `validateParams` additions must not change any hash (they validate, they don't change params). If an item can only be fixed by moving a hash or changing output, skip it and list it.
1. Fix items one commit per logical group; tests first where the item is a missing check.
2. Full suite + typecheck. Prove no value change: in a scratch ORION_HOME seeded with a `.backup` copy of the live DB (via `sqlite3 'file:...?mode=ro' ".backup <scratch>/orion.db"`) and assets, run `model whatif <a> --as-of <one fixed ISO> --json` for all 13 assets with main's dist and with this branch's dist (build into the worktree, never live `dist/`), `cmp` each pair. Delete the scratch home.
3. Commit; don't merge or push. `kanban_complete` with per-item fixed/skipped(why), shas, test counts, and the 13-asset identical/differs list. If any asset differs, `kanban_block` instead.
