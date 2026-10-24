# Orion dev queue — revenue definitions

Open items only. Built or closed items move to dev-queue-revenue-archive.md (same folder).

Status 2026-10-24: LIT unlock cadence (proposal #3) applied live (main 4287b32). Open items below.
Kanban (board `orion`, all assigned 2026-10-24): LIT revision check t_3bfa0ba7 DONE (main 0739cd6); loadEnv fix t_7a5fb5d1 DONE (main 08ab5f6, pushed); agent budget t_46c152b5 DONE (main 4a2f126, pushed);
minors batch t_b3b09288 running.

## [DONE] Orion `loadEnv`: an empty process variable overrides `.env` (found 2026-10-23)
- Built: t_7a5fb5d1, merged + built + pushed main 08ab5f6 (2026-10-24); blank process values no longer override `.env`; 13/13 whatif identical.
- `src/cli/env.ts` `loadEnv` returns `{ ...fromFile, ...processEnv }`, so `ANTHROPIC_API_KEY=""` in the process env (the
  Hermes agent terminal exports it empty) beats the real key in `<ORION_HOME>/.env`; a hand-run `orion agent run` then fails
  `no_credentials` ($0). Cron is unaffected (wrappers source `.env` with `set -a`).
- Fix: skip process values that are empty or whitespace when merging (`.env` wins over an empty variable); test both orders.

## [OPEN] LIT fee series runs one day behind (found 2026-10-24, kanban t_3bfa0ba7)
- fetch_run 272 (10-24 12:50Z) held back Lighter day 10-23 because no kind listed a row for today (adapter treats the
  newest day as possibly partial). Lighter listed no 10-24 row at 01:28Z, 12:50Z, 15:48Z or 16:15Z. Nothing lost
  (written next tick, inside the 3-day re-read; staleness_days 5). Check the 10-25 12:50Z run writes stamp 10-24 (day
  10-23); if not, the series is stuck, not lagging -> adapter fix.

## [DONE] Deferred minors from the 2026-10-23/24 builds
- 26 repo minors on main c797f29 (kanban t_b3b09288, 13/13 whatif identical on live, no hash moves; `get_flow_total`'s
  straddle rule kept as its documented contract). The 3 watcher items were fixed 2026-10-24 in
  `disclosure-watcher/` (tests/test_minors.py; suite 110/110); docs main 2611dee. Details in
  `docs/superpowers/notes/2026-10-23-{disclosure-watcher,lit-lighter-api}-followups.md`.
