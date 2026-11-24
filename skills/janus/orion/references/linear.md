# Orion project management in Linear (Mike, 2026-11-16)

Linear is the project board for Orion. Workspace "Retrograde Capital", team `RET`, project `orion`.

## Rules (Mike)
- One parent issue per phase; one sub-issue per step/sub-task inside it (nesting allowed, e.g. R2 -> its rollout steps).
- Anything that needs Mike to act (a decision, a go, a sudo step, a sign-off) gets the `Blocked` label. Remove it once he has done his part.
- Status: `Todo` until I start it -> `In Progress` -> `Done`. Don't use Backlog/In Review for this.
- New phases/steps/decisions that come up go into Linear as they appear; keep descriptions short with doc/branch/tag refs.

## Access: the hermes-linear plugin (Mike, 2026-11-24)
- Linear runs through the `linear` plugin (hermes-linear) as the Raymond app. When Mike delegates a ticket to Raymond or @mentions it in a comment thread, a Linear session starts. Replies, progress and questions go in that thread. The plugin's skills explain how a session works.
- Reads: `linear_issue_get`, `linear_search` and `linear_query` work from any session, Slack included.
- Writes: `linear_comment`, `linear_issue_update`, `linear_issue_create`, `linear_attach` and the sync tools. **These only work inside a Linear session.** From Slack they refuse with `NOT_LINEAR_SESSION`. Inside a session, Raymond can write to the session ticket, its sub-tickets and tickets created from it without asking. Writes anywhere else first ask Mike in the thread (Allow once / Deny).
- Work done from Slack: read the board with the read tools, then tell Mike which state/label changes are due. He makes them himself, or delegates the ticket to Raymond so the change is made in a session.
- The hosted connector tools (`connectors__linear__*`) are a different, unconnected path. They return CONNECTION_REQUIRED, so don't use them.
- Settings live under `plugins.entries.linear.settings` in raymond's `config.yaml`; secrets are in raymond's `.env`. Health check: `hermes -p raymond linear status`.
- Raymond's Linear app (viewer "Raymond", id `a5319d88-b7e2-4866-b39b-db482511f228`, installed actor=app on 2026-11-17) has its client id/secret in 1Password: vault `hermes`, item `linear-raymond-app`. Print only lengths or format checks, never the values.

## Retired (2026-11-24)
The early prototype is gone:
- the `linear-orion` comment-trigger route (the core webhook platform on :8644 in the default profile);
- `scripts/linear_app.py`, its filter and the post-restart check;
- the user-OAuth Linear MCP (`mcp_servers.linear`, `mcp-tokens/linear*`);
- `workspace/orion/linear/lmcp.py`, `seed.py`, `issues.json` and `oauth_app_callback.py`.

Don't recreate any of them. The archive `archive/20261124-linear-orion.tar.gz` holds the old version of this file and `issues.json` (the map from seed keys P1, P2, R0-R8, … to RET ids). The per-issue notes in `workspace/orion/linear/notes/` stay as history; `RET-10.md` is the archive of the removed cron jobs.
