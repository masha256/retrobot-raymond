# Provisioning scripts Mike runs (dev host, Orion server)

Raymond writes host setup as scripts in `scripts/provision/` (`dev-postgres.sh`, `orion-host.sh`, `sql/*.sql`, `files/*`, `test/run.sh`, README). Mike runs them as root. Raymond never runs them for real: he has no sudo, and the server isn't reachable before the deploy keys exist.

## Writing them
- Plain bash with `set -euo pipefail`. Every change goes through a `run`/`write_file` helper that prints instead of acting under `--dry-run`, and skips with an `ok:` line when the state already holds. A second run prints only `ok:` lines.
- `--dry-run` must work as non-root and list every change a real run makes.
- Every refusal (wrong OS codename, SSH caller not in `--ssh-from`, non-empty target dir) happens before any change.
- Finish with a `SELF-CHECK: N passed, M failed` block, and print public keys as `pubkey:` lines. Mike pastes both back.
- Never print secrets. Never overwrite a filled `.env`, a generated key, or a config file whose placeholders have been filled.
- Pin version-sensitive software to upstream, not the Ubuntu archive: PGDG for Postgres and pgBackRest, so both hosts run the same minor; the official Node tarball with its sha256; yt-dlp from pip. Then a newer server OS than dev's is no blocker. Check each package's version in both codenames' apt indexes (`dists/<codename>-pgdg/main/binary-amd64/Packages.gz`).
- Put data on the big partition with the tool's own option, never a symlink. For Postgres, `--pg-datadir`: `pg_dropcluster --stop` plus `pg_createcluster -d <dir>`, only when the package-default cluster is fresh. Symlinks under `/var/lib/postgresql` break on upgrades and with AppArmor. Ask for `lsblk` and `df -h` before choosing paths: a small `/` means everything that grows (data dir, dumps, refresh drops) goes under the large mount.
- A local backup repo on the same physical disk as the data gives no disk-failure protection. Say so, and keep off-box (Spaces) as the real copy.

## Testing without root
- `test/run.sh`: dry runs of each script, refusal cases, and helper unit tests. Run it with `SHELLCHECK=<path>`. shellcheck can be installed without root via `pip install --target <dir> shellcheck-py`.
- SQL leg: set `PG_BINDIR` (the installed `/usr/lib/postgresql/18/bin`, or binaries unpacked from the PGDG .debs). It runs the role SQL twice against a throwaway `initdb` cluster owned by `hermes`.
- The harness must fake the system probes (`dpkg-query`, `pg_lsclusters`, `psql`, `/etc/postgresql` via a test hook). Without fakes, dry runs read the dev host's real packages once Postgres is installed there, and the tests fail.

## Handing them to Mike
1. Merge the script-only branch into main and push it before asking him to run anything. He runs from `/home/hermes/git/orion` on main and should not have to switch branches. Check the merge is a fast-forward and touches only `scripts/provision/` and `docs/`, so no rebuild is needed.
2. He logs in as root, not `sudo` from hermes (he has no hermes password). So `$SUDO_USER` is empty, and a dev script that maps a Unix user needs `--os-user hermes`. Put that flag in the command you give him.
3. For the server, copy the whole `scripts/provision/` directory, not one script, because it sources `lib.sh`, `files/` and `sql/`. As root on uranus: `scp -r /home/hermes/git/orion/scripts/provision <user>@<server>:/tmp/`. Then a `--dry-run` first, then the real run. The server gets no repo checkout; releases arrive through deploy.
4. Give him the exact command with every flag filled in (hostname, data dir, `--ssh-from` for each address), and say which flags must be repeated on later runs.
5. Verify his reported SELF-CHECK yourself where you can. Peer-auth Postgres needs the role named in the URL or `-U`, because the default role is the OS user (`psql -U orion_dev -d orion_test`).
6. Keep a running list of the steps he still owes (cloud accounts, keys, webhooks, `.env` filling) in `~/.hermes/profiles/raymond/workspace/orion/phase1.5-mike-steps.md`, done vs deferred. When he asks "what was I supposed to do?", answer from it in two groups: needed now, and needed before the next milestone. Public keys he pastes go in `workspace/orion/venus-keys.md`.

## Deploy keys and snapshot repos (after the server run)
- Create the per-env deploy keys on uranus only on Mike's go: `ssh-keygen -t ed25519 -N '' -f ~/.ssh/orion-<env>_ed25519`, never overwriting an existing file. Post the public halves as `echo '<key>' > /tmp/deploy-<env>.pub` lines plus the full re-run command with `--deploy-key-stage/--deploy-key-prod`.
- Verify each key yourself, including the refusal of shell input: `ssh -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -i ~/.ssh/orion-<env>_ed25519 orion-<env>@<server> status`, then the same with `'id; cat .env'`. The second must be refused by `orion-remote`.
- Forced-command keys block `scp`, so deploys stream the tarball over the SSH session's stdin.
- Snapshot repos (one per env): private, created EMPTY (no README, licence or .gitignore, because the publisher makes the first commit and alerts on any commit it didn't write), default branch `main`, no branch protection. Each gets its env's server publish key as a deploy key with write access.
- A personal-account GitHub repo has no read-only collaborator role: inviting `retrobitbot` always grants write. Accept invitations with `PATCH /user/repository_invitations/<id>` using GH_PAT. If Mike wants read-only, offer a read-only deploy key from uranus instead of the collaborator.
