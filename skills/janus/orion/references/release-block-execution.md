# Executing a per-env release block (deploy.md "<release> release" sections)

Depth for running the numbered one-time steps (save before/, deploy, backfill, mid/, dry runs, --yes, after/, gate) on stage or prod over the forced-command ssh keys, and for checking where a soak stands.

## Status check after a network/LAN outage
- A `levels` job whose `result.failed` lists every asset ("could not read the latest block: HTTP request failed") = RPC/network down for that run; `snapshot_push` failures (`git ls-remote failed (128)`) and Slack post timeouts recover on their own retry.
- Hourly chain prices missed during the outage are refilled by the next successful `levels` run: its `prices.written` = refs x missed hours with `missing` 0. Confirm with the block's `compare-usd` step; never backfill by hand.
- Prod `levels` is latest-only: failed outage hours need no backfill.
- A soak cron run that failed offline lost nothing if the nightly it would have judged ran on the old tag.
- A deployed prod whose backfills never ran shows empty yCRV revenue and `legacy` price bases everywhere.

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

## Stage has no `sql-ro`
orion-remote refuses `sql-ro` on stage (no read-only role) and Raymond has no sudo on venus, so a pre-check written as `sudo -iu orion-stage` + `o db query-ro` needs Mike; granting permission does not change that. Offer a waiver backed by read-only evidence: the same query on prod via `sql-ro`; stage's counts via `data show <a> <metric>` (ACTIVE rows only, so it cannot show rejected ones) matched to prod's totals; `data anomalies --all` for any stage-only decision since the last `staging_refresh`; and the later step whose refusal would catch it anyway (a stop, no data loss).

## Gate (flatdiff) failures that are not regressions
Bring every unallowed path to Mike with before -> after and the mechanism; never call the gate passed. Recurring false-failure classes:
- Float noise on provenance method shares (`provenance.methods.measured` 1 <-> 1.0000000000000002): those paths have no allowlist entry (fail closed).
- Ratios with no entry by design (`ratios.payoutRatio`): a tiny move following the asset's own flow reprice.
- Absolute floors on degenerate growth: a line whose prior quarter is near zero has `change` in the hundreds, so a 0.02% relative move breaks the 0.05 abs floor. Show current/prior and the relative move.
Recommend exact-path entries in a separate addendum file used at prod's gate; never re-tag the soaking release for a tools-only change (it voids the soak).
