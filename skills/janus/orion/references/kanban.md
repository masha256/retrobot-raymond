# Orion on kanban (live since 2026-10-24, signed off by Mike in #orion-dev)

## Setup (verified)
- Board `orion` (`~/.hermes/kanban/boards/orion/kanban.db`). Never use `default` for Orion.
- Only one gateway on the host dispatches: whoever holds `~/.hermes/kanban/.dispatcher.lock` (usually the default/Val gateway, pid in claim_lock `uranus:<pid>`). The dispatcher only submits the claim to the assignee profile's own gateway (`kanban_worker_client`), so a raymond card always executes inside raymond's gateway (`owner_admitted.db` = raymond `state.db`).
- `kanban.dispatch_profiles` per home (Mike approved touching the other homes): default=`default,raymond`, gordon=`gordon,raymond`, bones=`bones,raymond`, raymond=`raymond`. raymond must be in every home's list, or raymond cards sit `skipped_nonspawnable` whenever that home holds the lock. Never add another profile to raymond's list.
- `kanban.auto_decompose: false` in all four homes (the decomposer routes triage cards to any profile). Never use `--triage` or `specify` on `orion`.
- raymond `kanban.max_in_progress_per_profile: 1` (one card at a time, plan order).
- Check: `HERMES_HOME=<home> hermes kanban diagnostics | grep dispatch_profiles` for each home.

## Card recipe
- Body = `~/.hermes/profiles/raymond/workspace/orion/kanban/task-preamble.md` + task section (cat into a body file, `--body-file`).
- `hermes --profile raymond kanban --board orion create "<title>" --body-file <f> --workspace worktree:/home/hermes/git/orion --branch feat/<topic> --skill orion --max-retries 1 --max-runtime <45m..2h> --created-by raymond --json`, created UNASSIGNED (unassigned+ready never dispatches, verified over a full tick).
- Subscribe the orion-dev thread: `notify-subscribe <id> --platform slack --chat-id C0CB8SJKM8C --thread-id <thread ts> --chat-type thread --parent-chat-id C0CB8SJKM8C --user-id U0CBKGZFU9E --notifier-profile raymond --delivery-mode notify`.
- Worktree lands at `/home/hermes/git/orion/.worktrees/<task-id>` (`.worktrees/` is in `.git/info/exclude`; vitest `tests/**` and tsc `src,tests` don't see it). It's removed on completion unless dirty/unpushed; the branch stays: delete an empty canary branch with `git branch -d`.

## One thread per card (Mike, 2026-10-24)
- Mike starts each card with a top-level orion-dev message (e.g. "go t_xxx"); my reply threads under it, and that thread (thread ts = his message ts, shown in the session context) is the card's home for questions, blocks and approvals.
- On "go": `notify-unsubscribe <id> --platform slack --chat-id C0CB8SJKM8C --thread-id <setup thread ts>`, `notify-subscribe` the new thread ts (recipe above), `notify-list` to confirm, then `assign <id> raymond`. Post the card's scope + stop point in the thread.
- `--delivery-mode notify` only posts the notifier's text ping in the thread (the sub's `last_ping_event_id` advances; sends are debug-logged only, so gateway.log shows nothing). It does NOT start a turn for me, so I never see a finish or block until Mike writes. `notify+wake` also wakes my session in that thread, so I can verify and report on my own. Mike asked why I missed t_3bfa0ba7's finish (2026-10-24); the mode for later cards waits on his answer.
- On completion, the worktree is kept when its branch isn't on the remote (a local-only docs branch counts). After merging and pushing: `git worktree remove .worktrees/<id>`, then `git branch -d <branch>`.
- On a block notice there, read `kanban show <id>` (the block reason + worker summary), verify its claims, and put the decision to Mike in that thread; unblock only on his reply there. `thread_require_mention: false`, so he can reply without tagging.
- The setup thread was `1792854767.962179`; cards created there are subscribed to it until moved.

## Gates
- Mike says "go <id>" / "approved" in orion-dev; I run `assign <id> raymond` or `unblock <id>` and keep that message as the record. Approval covers the next step only.
- Cards end in `kanban_block` at every decision (spec ready, options to pick). Kanban covers scoping, specs and green branches only: merge, live build, live backfill, push, paid analyst runs, config-proposal approvals and cron changes stay interactive under the live-install rules.
- Verify every worker summary yourself before reporting (rerun its tests in your own `git worktree add --detach $TMPDIR/... main`, diff live HEAD/status/`orion.db`+`.env` mtimes/`dist` against a pre-snapshot). The canary's summary checked out exactly (100 files / 1127 tests).
- Headless workers are refused `rm -rf`; the preamble tells them to use `shutil.rmtree`. Keep that guard; don't loosen approvals.
