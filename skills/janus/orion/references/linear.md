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
- The issues are attributed to Mike while the board runs on his OAuth token. Move board writes to the app token once it is installed, so my comments don't look like his and can't wake the comment trigger.

## Comment-triggered turns (built 2026-11-17)
- Live wiring: Linear app webhook URL `https://uranus.tail4eb3a7.ts.net:8443/webhooks/linear-orion` -> Funnel path map (`tailscale funnel --bg --https=8443 --set-path /webhooks/linear-orion http://127.0.0.1:8644/p/raymond/webhooks/linear-orion`; only that path is public) -> Hermes webhook listener 127.0.0.1:8644 (DEFAULT profile `~/.hermes/config.yaml` platforms.webhook, route `linear-orion`, `profile: raymond`, secret `${env:LINEAR_RAYMOND_WEBHOOK_SECRET}` in `~/.hermes/.env`, toolsets hermes-slack, skills orion, deliver log). Backups of both default files: `*.bak-20261117-linear`. Config changes need a `systemctl --user restart hermes-gateway` (Mike runs it; drops all bots for seconds).
- Filter `~/.hermes/profiles/raymond/scripts/linear-orion-filter.py` (route scripts resolve under the routed profile's `scripts/`): Comment create only, `webhookTimestamp` <= 60 s, author must be Mike (`70e0e80c-...`), never the app, issue in project orion; enriches with issue + thread. Decisions log: `logs/linear-orion-webhook.log`.
- Replies go on the Linear issue only (Mike, 2026-11-17), via `scripts/linear_app.py comment <RET-n> --parent <root>` (app token, auto-refresh). `linear_app.py update` moves state/labels. Use linear_app.py (as Raymond) for ALL board writes now, not the MCP/lmcp path (that writes as Mike).
- Hermes does not dedupe Linear retries (it doesn't read `Linear-Delivery`); a non-2xx answer makes Linear retry.
- Smoke-test issue: RET-36. VERIFIED 2026-11-17 04:54Z: Mike's comment -> accept -> Raymond reply in-thread 16 s later -> own reply ignored by the filter; bad signature via Funnel = 401; unmapped Funnel path = 404.
- Per-issue notes (continuity across triggered turns; webhook sessions are per delivery and can't be reused natively): `workspace/orion/linear/notes/RET-n.md`, appended with `linear_app.py note RET-n < text`; the filter injects the last 5,000 chars as `{issue_notes}`. Also write a note when working an issue from Slack, so the next comment turn knows.
- The route no longer preloads the orion skill (Mike, 2026-11-17). Its prompt says to `skill_view('orion')` before any action beyond answering. Before that change, `skills: [orion]` inlined the whole ~100 KB orion SKILL.md into every triggered prompt (prompt_len ~102k).

## Comment-triggered turns (design notes)
- Design Mike chose: Linear webhook (Comment events) -> Tailscale Funnel `https://uranus.tail4eb3a7.ts.net:8443` -> Hermes webhook listener on localhost, route `linear-orion` with `profile: raymond` (URL `/p/raymond/webhooks/linear-orion`). Mechanics: hermes-agent `references/webhooks.md`.
- Identity: a custom Linear OAuth app installed with `actor=app` (authorize URL with `actor=app&scope=read,write,issues:create,comments:create`, callback `https://uranus.tail4eb3a7.ts.net:8443/linear/oauth/callback`). Its token goes to `secrets/linear-app-token.json` (0600; the profile backup ignores `secrets/`). The app has no client_credentials grant, so use the browser authorize flow.
- `workspace/orion/linear/oauth_app_callback.py` is a one-shot receiver on 127.0.0.1:8645: it checks `state`, exchanges the code, writes the token, and exits. Run it in the background with LINEAR_CID/LINEAR_CS/LINEAR_STATE/LINEAR_REDIRECT, point the Funnel at it, then repoint the Funnel to the webhook listener.
- Route filter: drop the app's own comments (no loop), non-`orion` issues, and `webhookTimestamp` older than 60 s.
- Secrets are in 1Password, vault `hermes`, item `linear-raymond-app`: `client-id`, `client-secret`, `webhook-signing-secret`. The service-account token is `OP_SERVICE_ACCOUNT_TOKEN` in `~/.hermes/.env`. Export it only inside the shell that runs `op read`, and print only lengths or format checks, never values.
- **App installed (Mike, 2026-11-17):** viewer "Raymond", id `a5319d88-b7e2-4866-b39b-db482511f228`, `app: true`. That id is what the route filter drops. Token file holds a 24 h access token plus `refresh_token` (refresh: POST https://api.linear.app/oauth/token, grant_type=refresh_token). Hermes is a Tailscale operator: `tailscale funnel --bg --https=8443 <target>` needs no sudo. Funnel was turned off after the install; leave the tailnet-only 443 -> 9119 serve alone.

## Tool quirks (Linear MCP)
- `save_issue` creates (no `id`) or updates (`id` = `RET-n`). Fields: team='RET', project='orion', state=<name>, labels=[names] (replaces the set), addLabels/removeLabels, parentId='RET-n'.
- Responses put the identifier in `id` (`RET-35`) and the UUID in `uuid`; there is no `identifier` key.
- `list_issues(project='orion', limit=100)` and `list_issues(parentId='RET-n')`; `get_issue(id)` returns `parentId`.

## Map
`workspace/orion/linear/issues.json` maps seed keys (P1, P15, P2, PF*, P3, R0-R8, R2a-d, P5*, P4*) to RET ids; `seed.py` is idempotent by key.
