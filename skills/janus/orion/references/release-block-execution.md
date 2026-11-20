# Executing a per-env release block (deploy.md "<release> release" sections)

Depth for running the numbered one-time steps (save before/, deploy, backfill, mid/, dry runs, --yes, after/, gate) on stage or prod over the forced-command ssh keys, and for checking where a soak stands.

## Status check after a network/LAN outage
- A `levels` job whose `result.failed` lists every asset ("could not read the latest block: HTTP request failed") = RPC/network down for that run; `snapshot_push` failures (`git ls-remote failed (128)`) and Slack post timeouts recover on their own retry.
- Hourly chain prices missed during the outage are refilled by the next successful `levels` run: its `prices.written` = refs x missed hours with `missing` 0. Confirm with the block's `compare-usd` step; never backfill by hand.
- Prod `levels` is latest-only: failed outage hours need no backfill.
- A soak cron run that failed offline lost nothing if the nightly it would have judged ran on the old tag.
- A deployed prod whose backfills never ran shows empty yCRV revenue and `legacy` price bases everywhere.

## Writing a release block (in a plan, before it runs)
- Follow `docs/ops/deploy.md` section 7 "Writing a per-env release block". For every read-only check that runs before the step that clears a known artifact (pre-switch `latest_levels` rows still on the old source, rows on an old definition before a rebuild, rows only a purge removes), name: the asset/metric, the counts measured on prod via `sql-ro` (and stage's, for prod's block), the clearing step, and an unexempted re-check after it that must show 0. The check exempts exactly those rows (printing counts) and stops on anything else. R2's step 5 is the model.
- Counts that grow every nightly (one level row per asset) are never typed into a script: the block's own read-only step writes an expected-counts file, and every later check reads it. A nightly between that step and a purge adds only rows on the new source, so the old-source counts must match exactly.
- One script per pre-approved stage (deploy+switch checks, rebuild, purge, gate), `set -u`, each step `|| stop`, exit 1 at the first deviation: each terminal call raises its own approval prompt.
- Pick report days so nothing moves between before/ and after/ except the release: `D` = today-2 UTC (a report reads levels to the end of D+1, so D+1 must be a complete past day).
- Allowlist classes carry the R43 lesson (`tools/phase3-proof/README.md`): any growth abs floor gets a rel alternative (a tiny prior window makes `.change` huge); fields that scale with one input (market cap, mcap multiples, per-token over circulating) get a `ratio: [lo, hi]` pin around the signed proof's new/old ratio (a symmetric `rel` bound passes a move in the wrong direction), never abs-only; fields the release must not move get no entry (fail closed).
- Handing Mike an `orion-host.sh` re-run: give the full two-step command (scp of the fixed `/home/hermes/orion-provision-<sha>/scripts/provision` snapshot, then on venus an optional `--dry-run` and the `sudo ./orion-host.sh` line with the current flags below), say which flags may be left off and the log line that proves the dead-man URL was kept, and name the SELF-CHECK lines to expect. Verify the snapshot against `git archive <sha> scripts/provision` first. After his SELF-CHECK, prove the new capability from uranus yourself (e.g. stage `sql-ro "select current_user"`) before reporting it installed.

## Coordinating with parallel threads
When Mike runs several threads and asks when this one closes or when others may proceed: a release thread closes when its prod block passes the gate. List per stage what it holds: branch-only build (only the shared `orion_test` DB and 4-core host for full suites, which time out when two run at once, plus the files it edits, named: a change there after the proof means re-proving); the prod-copy proof (read-only prod, shared RPC key, outside 05:00-06:30 PT); merge + tag (nothing else merges to main between them); stage deploy through the prod switch (no other stage deploy, no Sunday `staging_refresh` inside it). Announce each holding step in the thread before it starts.
- A stage pre-check needing `ssh orion-stage sql-ro` lists Mike's `orion-host.sh` re-run (from a snapshot that has `orion_stage_ro`) as a prerequisite decision, with the waiver below as fallback; a re-run from the release snapshot can install it together with the release's new verbs (one re-run instead of two).
- Record the plan's base sha in a Status line. Before each commit, `git reflog show --date=iso <branch>` and `git ls-remote` GitHub main: other sessions merge to main and may fast-forward your branch or the uranus checkout (Mike-authorized; never reset them). Re-sync with `git fetch https://github.com/masha256/orion.git main` + `git merge --ff-only FETCH_HEAD` and update the recorded base.

## Shell setup that survives across tool calls
Shell functions do not persist between terminal calls. Write the block's definitions once to `$TMPDIR/<rel>env.sh` and source it at the top of every step:
```
A="aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv"
ST() { ssh -i $HOME/.ssh/orion-stage_ed25519 -o IdentitiesOnly=yes orion-stage@192.168.0.12 "$@"; }
day() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["day"])' ~/r2-stage/before/$1.json; }
d91() { python3 -c 'import datetime,sys; print(datetime.date.fromisoformat(sys.argv[1]) - datetime.timedelta(days=91))' "$(day $1)"; }
```
`day` reads the saved `before/` file, so every later save uses the same report days.
- Keep each terminal call under ~580 s (13-asset `--yes` loops take minutes): a foreground timeout over 600 s is promoted to a background process you then have to wait on.
- Run gate tools (`flatdiff.py`, the allowlist) from the release tag, not the stale uranus checkout: `git show <tag>:tools/phase3-proof/<f> > $TMPDIR/r2tools/tools/phase3-proof/<f>` and run from there.
- Put a step's `--yes`, its count check, and the next step's dry run + check in ONE call, each guarded with `|| exit`: the write goes through the command-approval prompt, so tell Mike to watch for it. A timed-out approval did not run (verify the output file is absent) and must not be retried until he replies.
- Read-only dry runs of a later step may run before a pending human pre-check; only its `--yes` waits.

## When a runbook STOP fires
Before stopping, compare the stopping output with the signed proof's own run of the same step (`workspace/orion/phase3-proof/<rel>/B*`, `C*`). If the proof shows the identical pattern (scaled by the extra days since), it is an artifact of step order, not a gap: run the next read-only step that explains it, re-check after the step that should clear it, tell Mike in the thread, and fix the runbook before prod. Example: `compare-usd` flags yCRV rows still on `coingecko:*` refs as unpriced until `data reprice` remaps them; after the reprice they read 0.

## Stage `sql-ro` (installed 2026-11-19)
Mike re-ran `orion-host.sh` from `/home/hermes/orion-provision-06955e0` (SELF-CHECK 61/0): `ssh orion-stage "sql-ro \"select ...\""` now works as `orion_stage_ro` (same quoting as prod's). Re-run flags since 2026-11-11: `--hostname venus --pg-datadir /home/postgres/18/main --ssh-from 192.168.0.0/24 --ssh-from 100.64.0.0/10 --with-watcher --enable-backups` (deploy keys and the dead-man URL file are optional on a re-run: existing ones are kept). The waiver below applies only to an env/release without it.

## Stage without `sql-ro` (an orion-remote older than 06955e0)
Check first: `ssh orion-stage "sql-ro \"select current_user\""` prints `orion_stage_ro` when installed; exit 64 `sql-ro is prod-only` means not, and then: orion-remote refuses `sql-ro` on stage (no read-only role) and Raymond has no sudo on venus, so a pre-check written as `sudo -iu orion-stage` + `o db query-ro` needs Mike; granting permission does not change that. Offer a waiver backed by read-only evidence: the same query on prod via `sql-ro`; stage's counts via `data show <a> <metric>` (ACTIVE rows only, so it cannot show rejected ones) matched to prod's totals; `data anomalies --all` for any stage-only decision since the last `staging_refresh`; and the later step whose refusal would catch it anyway (a stop, no data loss).

## Gate (flatdiff) failures that are not regressions
Bring every unallowed path to Mike with before -> after and the mechanism; never call the gate passed. Recurring false-failure classes:
- Float noise on provenance method shares (`provenance.methods.measured` 1 <-> 1.0000000000000002): those paths have no allowlist entry (fail closed).
- Ratios with no entry by design (`ratios.payoutRatio`): a tiny move following the asset's own flow reprice.
- Absolute floors on degenerate growth: a line whose prior quarter is near zero has `change` in the hundreds, so a 0.02% relative move breaks the 0.05 abs floor. Show current/prior and the relative move.
Recommend exact-path entries in a separate addendum file used at prod's gate; never re-tag the soaking release for a tools-only change (it voids the soak).
