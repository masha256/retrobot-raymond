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
7. Alchemy: separate app for staging. CoinGecko: Basic key (prod, needs COINGECKO_PLAN=pro per 1.5c), free Demo key (staging).
8. Mike fills ~orion-prod/shared/.env and ~orion-stage/shared/.env (template has every key commented).

## Spec/plan doc fixes owed (no code impact)
- Spec §8.5 / §10.1 and plan 1.5a still say /srv/orion-refresh and /var/backups/orion; scripts now use
  /home/orion-refresh and /home/orion-backups (main 33efeea). §8.5's orion-refresh group not implemented (750 postgres).
