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
- Writes inside a Linear session: Raymond writes to the session ticket, its sub-tickets and tickets created from it without asking; writes anywhere else first ask Mike in the thread (Allow once / Deny). The sync tools, `linear_task_state` and `linear_session_link` work only in a session.
- Writes from Slack (or cron/CLI): `linear_comment`, `linear_issue_update`, `linear_issue_create`, `linear_relation`, `linear_attach`, `linear_document` and `linear_project` writes follow the plugin setting `outside_session_writes` (unset on raymond = `approve`): each write shows Mike an approval card in that chat first, and acts as the Raymond app. So from #orion-dev, keep the board true with these tools and let Mike approve each write.
- The hosted connector tools (`connectors__linear__*`) are a different, unconnected path. They return CONNECTION_REQUIRED, so don't use them.
- Settings live under `plugins.entries.linear.settings` in raymond's `config.yaml`; secrets are in raymond's `.env`. Health check: `hermes -p raymond linear status`.
- Raymond's Linear app (viewer "Raymond", id `a5319d88-b7e2-4866-b39b-db482511f228`, installed actor=app on 2026-11-17) has its client id/secret in 1Password: vault `hermes`, item `linear-raymond-app`. Print only lengths or format checks, never the values.

## Only path
The plugin is the only Linear path (Mike, 2026-11-26). The earlier prototype (a core webhook route, a script-based app client, a user-OAuth Linear MCP) was removed for good, archive included. Don't build another webhook route, app-token script or Linear MCP; if the plugin lacks something, ask Mike for a plugin ticket.

Per-issue history notes from earlier Orion work are in `workspace/orion/notes/` (`RET-10.md` + `RET-10-removed-jobs.json` archive the removed cron jobs). New notes go in the Linear thread or the ticket, not there.
