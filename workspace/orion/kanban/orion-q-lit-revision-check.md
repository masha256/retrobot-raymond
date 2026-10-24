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

Source: `~/.hermes/profiles/raymond/workspace/orion/dev-queue-revenue.md`, section "LIT fee series: revision check" (figures, sources, proposed design). Read it first.

## Task: LIT fee revision check (read-only on live; docs commit only)
Gate type: read-only measurement + a notes commit. No config, code or DB changes.
1. Read stored `flow_usd.fees_core` and `flow_usd.fees_rh` rows for 2026-10-17..2026-10-23 from the live DB READ-ONLY (`sqlite3 'file:/home/hermes/git/orion/orion.db?mode=ro'`; daily flow rows are stamped at day end). The tick after the baseline is fetch_run 272 (2026-10-24T12:50Z).
2. Diff day by day against `~/.hermes/profiles/raymond/workspace/orion/lit-scoping/revision-baseline-2026-10-24T0112Z.csv`. Also pull those days fresh from Lighter `exchangeMetrics` (read-only HTTP) and diff that too.
3. Record the result (per day: baseline, stored, fresh, delta) in `docs/superpowers/notes/2026-10-23-lit-lighter-api-followups.md` under the existing revision-check line. Commit on this branch.
4. If any day older than 7 days back is restated, or deltas are material, do NOT change `days`: `kanban_block` with the options (raise `days` to N vs leave) and a recommendation. Otherwise `kanban_complete` with the table and "no restatement" or the restated days.
