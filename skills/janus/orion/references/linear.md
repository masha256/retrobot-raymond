# Orion project management in Linear (Mike, 2026-11-16)

Linear is the project board for Orion. Workspace "Retrograde Capital", team `RET`, project `orion`.

## Rules (Mike)
- One parent issue per phase; one sub-issue per step/sub-task inside it (nesting allowed, e.g. R2 -> its rollout steps).
- Anything that needs Mike to act (a decision, a go, a sudo step, a sign-off) gets the `Blocked` label. Remove it once he has done his part.
- Status: `Todo` until I start it -> `In Progress` -> `Done`. Don't use Backlog/In Review for this.
- New phases/steps/decisions that come up go into Linear as they appear; keep descriptions short with doc/branch/tag refs.

## Access
- The Linear MCP is configured in the raymond profile (`config.yaml` mcp_servers.linear, OAuth token in `mcp-tokens/linear.json`). Native `mcp_linear_*` tools load only in a session started after the auth.
- The hosted connector tools (`connectors__linear__*`) are a different, unconnected path: they return CONNECTION_REQUIRED. Don't use them.
- Fallback in an older session: `workspace/orion/linear/lmcp.py` (minimal streamable-HTTP MCP client with the stored token): `import lmcp; lmcp.init(); lmcp.call('save_issue', ...)`.
- OAuth over Slack: the redirect is `127.0.0.1:<port>/callback` on this host, so Mike's browser fails on it; he pastes the URL and I `curl` it locally (unescape `&amp;`).

## Tool quirks (Linear MCP)
- `save_issue` creates (no `id`) or updates (`id` = `RET-n`). Fields: team='RET', project='orion', state=<name>, labels=[names] (replaces the set), addLabels/removeLabels, parentId='RET-n'.
- Responses put the identifier in `id` (`RET-35`) and the UUID in `uuid`; there is no `identifier` key.
- `list_issues(project='orion', limit=100)` and `list_issues(parentId='RET-n')`; `get_issue(id)` returns `parentId`.

## Map
`workspace/orion/linear/issues.json` maps seed keys (P1, P15, P2, PF*, P3, R0-R8, R2a-d, P5*, P4*) to RET ids; `seed.py` is idempotent by key.
