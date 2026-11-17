# Outage impact check and resuming a release block

Use when Mike reports a network outage and asks whether stage/prod or a soak was affected, or when a per-env release block has to be resumed in a later session. The check itself is read-only.

## Outage check procedure

1. **Both envs' state:** `ssh orion-<env> status` for each env. Note `current:`, the daemon heartbeat, `soak:` and `last nightly ... (release <tag>)`. If stage's last nightly ran on the OLD release, the soak on the new tag hasn't started, so the outage cost no soak pass.
2. **Bound the outage window from job rows, not the logs alone:** run `jobs` (or `jobs --since <iso>`) to `$TMPDIR/<env>-jobs.json` and parse it in Python.
   - A `levels` row whose `result.failed` lists every asset with `could not read the latest block: HTTP request failed`, plus `prices.errors` per chain, means the RPCs were unreachable.
   - `snapshot_push` failing with `git ls-remote failed (128)` means GitHub was unreachable.
   - `slack post failed ... timeout` lines in `logs` mean ALERTs were never delivered: tell Mike, since he never saw them.
   - Prod runs `levels` hourly, so it gives the finest window. Stage runs it every 6 h (00/06/12/18:15Z).
3. **Did each gap heal by itself?**
   - Stage hourly chain prices: the first `levels` after recovery writes every missed hour. Check that `prices.written` = refs x missed hours and `missing` = 0.
   - Prod `levels`: reads keep only the latest value, so nothing needs a backfill.
   - `snapshot_push`: one `done` row with `pushed` > 0 after recovery means publishing caught up.
   - Long jobs (backfills): check `done`, `result.missing` == {} and the calls/rows/breaches against the release block's measured run. Name every count above the measured one for Mike: the runbook makes it a stop, even when the cause is plausible (more days, a later fix).
4. **The soak cron:** `hermes --profile raymond cron list` shows its last run. A run that failed while offline only matters if the nightly it would have judged was on the release under soak.
5. **The real blocker check:** if a release block is open, list `~/r2-<env>/{before,mid,dry,yes,after}` (or that release's own dirs) and the ledger's last line. Empty dirs mean the block stalled after the backfill was queued. Its remaining steps must finish before the env's next scheduled nightly, or the soak judges a half-migrated env and the gate (step 10) picks up that nightly's writes. Name any step that needs Mike (stage SQL pre-checks need `sudo -iu orion-stage`, because stage has no `sql-ro`).
6. **Report and log:** give the window in UTC and PT, a per-env impact list, what healed by itself, the soak position, and the next nightly time with what must happen before it. Offer to run the remaining steps. Append a one-line ledger entry.

## Resuming a per-env release block

- Shell definitions (`A`, `ST`, `day`, `d91`) don't survive between terminal calls. Write them once to `$TMPDIR/<rel>env.sh` and source it at the top of every call:
  ```
  A="aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv"
  ST() { ssh -i $HOME/.ssh/orion-stage_ed25519 -o IdentitiesOnly=yes orion-stage@192.168.0.12 "$@"; }
  day() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["day"])' ~/r2-stage/before/$1.json; }
  d91() { python3 -c 'import datetime,sys; print(datetime.date.fromisoformat(sys.argv[1]) - datetime.timedelta(days=91))' "$(day $1)"; }
  ```
  `day` reads the saved `before/` files, so the report days stay the ones saved before the switch.
- A `--yes` loop over 13 assets can run past the 600 s foreground cap. The terminal then moves it to the background: wait on it with `process_manage wait` in repeated calls (each is capped at 180 s) and never re-run it.
- Run each step's read-only dry runs while waiting on a Mike-only pre-check; only the `--yes` has to wait for him.
- Compare each dry run against the signed proof's numbers (`workspace/orion/phase3-proof/<rel>/`, ledger). A small surplus explained by the extra days since the proof copy is expected; name it in the report.

## R2 step 5: the false yCRV stop

Before step 6, `compare-usd ycrv` shows `unpriced` > 0 on `flow_usd.fees`, `yearn_revenue` and `yearn_styc_fee`. Those rows still carry `coingecko:crvusd` / `coingecko:yearn-crv` refs, which only step 6's remap points at chain prices (Task 10's proof had the same pattern), so it is not a backfill gap. Gate it with the step 6 dry run instead (0 refused; remaps of crvusd and yearn-crv only), then re-run `compare-usd ycrv` after the `--yes`: it must read 0 unpriced on every metric. Any other asset unpriced, or yCRV still unpriced after the reprice, is a real stop. Tell Mike when you take this path, because it departs from the runbook's literal stop rule.
