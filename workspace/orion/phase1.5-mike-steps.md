# Phase 1.5 — Mike's deferred steps (status 2026-11-04)

Done: dev Postgres (dev-postgres.sh, 6/6); venus provisioned (orion-host.sh, 33/33; cluster in /home/postgres/18/main);
deploy keys from uranus installed and verified (`ssh -i ~/.ssh/orion-<env>_ed25519 orion-<env>@192.168.0.12 status`);
snapshot repos masha256/orion-data + orion-data-staging created (private, empty, main), venus publish keys added with
write; retrobitbot invited (write) and invitations accepted 2026-11-04. Keys: workspace/orion/venus-keys.md.

## Deferred by Mike: backups (do before prod cutover; remind him at staging deploy at the latest)
1. DO Spaces bucket `orion-backups` + an access key scoped to it.
2. Fill REPLACE_ME in /etc/pgbackrest/pgbackrest.conf on venus: endpoint, region, bucket, key id/secret, long random
   repo1-cipher-pass.
3. `age-keygen -o orion-dumps.key` on Mike's own machine; private key stays off venus and uranus.
4. On venus: `sudo ./orion-host.sh --hostname venus --pg-datadir /home/postgres/18/main --ssh-from 192.168.0.201
   --ssh-from 100.109.70.114 --ssh-from 192.168.0.112 --deploy-key-stage /tmp/deploy-stage.pub
   --deploy-key-prod /tmp/deploy-prod.pub --enable-backups --dump-recipient <age pubkey>`; paste SELF-CHECK.
   (--pg-datadir must be on every run. Local repo2/--backup-disk not used: venus has one physical disk.)
Until then: no WAL archive, no PITR, no dumps on venus. Fine while venus holds no live data.

## Needed before the first staging deploy (1.5c)
5. Slack incoming webhooks: #orion-staging channel exists (2026-11-04). Mike creates a Slack app "Orion"
   (api.slack.com/apps, from scratch) -> Incoming Webhooks on -> one webhook for #orion-ops, one for #orion-staging.
   No bot/user scopes beyond the auto-added `incoming-webhook`. URLs are secrets: Mike puts them straight into
   SLACK_WEBHOOK_URL in ~orion-prod/shared/.env (#orion-ops) and ~orion-stage/shared/.env (#orion-staging), never in chat.
   DONE (Mike, 2026-11-04): both webhooks in both .env files. Not verifiable from uranus by design; first proof = the
   staging daemon's first post (1.5c).
6. healthchecks.io (free): 4 checks — prod hourly, prod nightly, staging nightly, backups.
   DONE (Mike, 2026-11-04): checks created (cron, UTC: prod-levels `15 * * * *` grace 30m; prod-nightly `45 0 * * *`
   3h; stage-nightly `45 2 * * *` 3h; backups `0 9 * * *` 2h, paused until backups). URLs in .env: prod
   ORION_DEADMAN_URL + ORION_DEADMAN_NIGHTLY_URL; stage ORION_DEADMAN_NIGHTLY_URL only. Backups URL goes into the
   backup timer at the deferred backups step. 1.5c must read ORION_DEADMAN_NIGHTLY_URL (plan T4/T6).
7. Alchemy: separate app for staging. DONE (Mike, 2026-11-04): Alchemy keys in both .env.
   CoinGecko: DONE for now (Mike, 2026-11-04): the same free Demo key (CG-..., from the developer dashboard) in both
   prod and stage .env, no COINGECKO_PLAN (demo header, works with current code). Fits only with 1.5c's batched hourly
   read (~1.2k prod + ~1.6k stage of 10k/mo). BEFORE PROD/SITE LAUNCH: Basic key in prod + COINGECKO_PLAN=pro (the
   site's 60 s price layer alone is ~43k/mo).
8. Mike fills ~orion-prod/shared/.env and ~orion-stage/shared/.env (template has every key commented).

## Spec/plan doc fixes owed (no code impact)
- Spec §8.5 / §10.1 and plan 1.5a still say /srv/orion-refresh and /var/backups/orion; scripts now use
  /home/orion-refresh and /home/orion-backups (main 33efeea). §8.5's orion-refresh group not implemented (750 postgres).
- BUG to fix in scripts/provision/files/env.template (owe a fix/ commit): the ORION_DATABASE_URL example is role-less
  (postgresql:///@DB@?host=...). libpq then asks for role = OS user name (orion-prod, with a hyphen), which pg_ident's
  map does not allow -> connection refused. Correct form names the role: postgresql://orion_prod@/orion_prod?host=/var/run/postgresql
  (stage: orion_stage). Mike set the values by hand 2026-11-04. Same R-b9 bug as the test URL; 1.5c's orion-remote/status
  self-check should connect with the .env URL to catch it.

## Overnight authority (Mike, 2026-11-04, orion-dev thread 1793249245.302979)
- Start 1.5c automatically when 1.5b is verified (stop and report instead if the ingest dry-run comparison shows a real diff).
- MAY deploy to STAGING (orion-stage@venus) without him: release build, deploy, db migrate, import of a fresh .backup of
  live SQLite, start the staging daemon; staging posts to #orion-staging and publishes to orion-data-staging.
- NOT without him: anything on prod (orion-prod), merging feat/platform-pg/feat/daemon into main, live install/cron/live DB
  writes, #orion-ops posts, analyst runs or other paid calls.

## Before the first staging deploy (status 2026-11-04 ~02:00 PT)
- Mike: `scp -r /home/hermes/orion-provision-f5f36fa/provision <you>@192.168.0.12:/tmp/` (as root on uranus), recreate
  /tmp/deploy-{stage,prod}.pub if gone, run orion-host.sh with the same flags (--hostname venus --pg-datadir
  /home/postgres/18/main --ssh-from 192.168.0.201 --ssh-from 100.109.70.114 --ssh-from 192.168.0.112 --deploy-key-stage
  /tmp/deploy-stage.pub --deploy-key-prod /tmp/deploy-prod.pub), paste SELF-CHECK.
- Mike: ORION_PUBLISH=git:git@github.com:masha256/orion-data.git#main (prod) and ...orion-data-staging.git#main (stage);
  no ANTHROPIC_* in stage .env.
- Raymond then: push tag orion-2026.11.04.2, deploy.sh stage orion-2026.11.04.2 --branch feat/daemon, import live
  .backup into orion_dev scratch + proof, pg_dump -Fc -n orion, `refresh-staging --stdin <sha>`, report cmp, asset
  activate x13, watch 02:45 UTC nightly. Runbook: docs/ops/deploy.md on feat/daemon.

## Staging soak (started 2026-11-04, orion-dev thread 1793827233.945569)
- Cron `orion-stage-soak` (e2fb64f34263) 06:30 PT daily -> that thread; collector scripts/orion-stage-soak.py (read-only:
  stage status/jobs/logs + stage-vs-prod parity of price-independent report fields).
- Baseline 2026-11-04 21:20 UTC: daemon healthy on orion-2026.11.04.2, 13/13 refreshes ok, 0 failed sources, parity 13/13
  (CRV vote_incentives level differs 0.7% = fetch timing, expected).
- Proposed merge gate: 3 consecutive clean scheduled nightlies (11-05/06/07 02:45 UTC) + parity clean.
- DONE (Mike, 2026-11-04 ~21:30Z): daemon pid 33378 has group 994 orion-refresh (Groups: 994 1005). Sun 11-08 10:30Z staging_refresh is the first real read test.

## Cutover prep (Mike, 2026-11-05: cut over after one more soak pass; "Proceed")
- Built I-2 data route: `orion-remote load-prod --stdin <sha256>` + staging_refresh prod mode (empty prod only).
  feat/daemon f1d2a23 (+48dcf2d test-only watcher date fix), tag orion-2026.11.05.1 pushed, built (1208/1208), deployed
  to staging 21:53Z. Gate: 2026-11-06 02:45Z nightly on .05.1 clean -> cutover on Mike's go.
- Mike owes before cutover: orion-host.sh re-run from a f1d2a23 provision snapshot (installs orion-remote with
  load-prod); ANTHROPIC_API_KEY in ~orion-prod/shared/.env (he'll add 2026-11-05); backups decision (before vs week 1).
- DONE (Mike, 2026-11-06 ~00:50Z): backups enabled. Spaces bucket orion-backups (sfo3; endpoint must be
  sfo3.digitaloceanspaces.com, NOT the bucket URL), pgbackrest.conf filled, age recipient in /etc/orion/dump-recipient
  (private key on Mike's machine only), orion-host.sh --enable-backups: SELF-CHECK 52/0 (pgbackrest check ok).
  Open: first full backup (timer Sun 09:00Z, or by hand now), healthchecks backups check unpause, restore drill (spec 10.3).

## PROD CUTOVER (Mike's go 2026-11-06 ~23:50Z: "cut over as is now", option a: orion-2026.11.05.1 with the known Base/VVV issue)
- [x] 23:54Z paused 13 orion-<asset> + orion-disclosure-watch Hermes jobs (nothing was running).
- [x] 23:55Z final SQLite backup -> backups/orion-final-20261106T235540Z.db (400, integrity ok); import into orion_dev
      PROOF_OK, exclusions as expected; dump .worktrees/prod-import-20261106T235540Z/latest.dump sha a47c5c9e...
- [x] GitHub main 33efeea -> f1d2a23 (ff). Local /home/hermes/git/orion checkout left on 33efeea + its built dist (fallback).
- [x] Mike: untar workspace/orion/orion-prod-disclosure-state.tgz (sha 4f896e61...) into ~orion-prod/home/ BEFORE deploy
      (prod's first tick runs disclosure_watch for real).
- [x] 00:23Z deploy.sh prod orion-2026.11.05.1 --no-soak (migrations 1,2; first tick: nightly/levels/snapshot x2/disclosure 0 posts/retention done) (gate would refuse VVV burn_sink: prod has no nightly to match).
- [x] 00:24Z load-prod job 11 done (initial_load, 10 tables); 13/13 reports cmp identical; anomalies 16=16, proposals 2=2; 00:25Z activated x13. Was: load-prod --stdin a47c5c9e...; cmp 13 reports vs ref; anomalies/proposals; asset activate x13 --for mike.
- [ ] watch: levels :15, deadman, first orion-data commit, 00:45Z nightly; then Base block-time fix release; remove Hermes jobs.
- Follow-up: prod watcher 'ytdlp: no venv' -> Mike re-runs orion-host.sh --with-watcher before the Q4 call window (2027-01-01).
