# Task 3 report: orion-remote verbs and the runbook

Status: DONE. Commit e88130f `feat(provision): orion-remote verbs for backfill jobs, compare-usd and purge` (on de7f7e4).

## What
- `scripts/provision/files/orion-remote`
  - `JOB_KINDS` gains `'backfill'` (R8). New constants `RUNGS` (the nine source types of 0004's CHECK),
    `RUNG_RE` built from it, `METRICS_MAX = 20`, `DAYS_MAX = 400`.
  - `metric_list()` check for `--metrics`: split on `,`; >20 items, an empty item (`a,,b`, `a,`, `,a`, `''`) or an item
    failing `METRIC_RE` (so `A`, `a/b`, a space, 65 chars) -> Refused. `each(flag, values)` emits `--metric` once per item.
  - `v_job`: `job run-now backfill <asset> --metrics <list> --backfill-days <1..400>` -> Orion
    `job run-now backfill <asset> --metric k1 --metric k2 ... --backfill-days N --by raymond --json` (v_job's pattern, R3).
    Backfill without asset/--metrics/--backfill-days, or with --slot: refused. `--metrics`/`--backfill-days` on any other
    kind: refused. Days via `count(1, 400)` (COUNT_RE + range), so `0`, `401`, `1e3`, `-1`, `10.5`, `+5` refuse.
  - `v_data`: `data compare-usd <asset> [--days 1..400]` -> `data compare-usd <a> [--days n] --json`;
    `data purge <asset> --metrics <list> [--source-type <rung>] [--yes]` -> `data purge <a> --metric ... [--source-type r]
    [--yes] --json` (dry run unless `--yes`; `--json` appended as every v_data verb, R3). `--json` from the caller is
    refused (as for the other data verbs). Error text lists the new subverbs.
  - Docstring verb table updated (three new lines). parse()'s repeated-flag rule kept (that is why lists are commas).
  - Refusals go through `Refused` -> exit 64, remote.log `<iso> <user> <verb> <argc> refused`, no argument text.
- `tests/release/orionRemote.test.ts`: the temporary `backfill` exclusion removed; compares with `[...JOB_KINDS]` (R8).
- `docs/ops/deploy.md`: new section "Phase 3 R1 release" (before the trailing verb block): (a) the one-time
  `orion-host.sh` re-run by Mike from a non-destructive `git archive` snapshot of `scripts/provision/` at the release sha
  (`/home/hermes/orion-provision-<sha>`), README §4 flags, SELF-CHECK paste-back, a check command that distinguishes new
  vs old orion-remote, and the note that the new verbs fail with Orion's own unknown command/option error on an older
  release (brief Step 3); (b) verb reference for the three verbs with one example each (vvv backfill as in the plan's
  Step 7 rehearsal; lit unlocks_next_year third_party purge from the plan's Step 6 list); R11 sentence verbatim; R10
  rollback note; (c) `<!-- release block: Task 8 -->`.

## Tests
- RED (tests written first, implementation absent): `python3 -m unittest scripts/provision/test/test_orion_remote.py`
  -> Ran 51, FAILED (failures=6): backfill_days_range, backfill_passes_each_metric, backfill_refuses_bad_metric,
  compare_usd_passthrough, purge_dry_run_by_default, purge_source_type_is_a_known_rung (all "64 != 0 ... data: only ..."
  / bad job kind). backfill_refuses_empty_item and backfill_on_kinds_other_than_backfill_refused passed already (pure
  refusal guards: the old script refuses the whole verb).
- GREEN: same command -> Ran 51 tests, OK (baseline 43 + 8 new).
- `npx vitest run tests/release/orionRemote.test.ts --maxWorkers=1` -> 2/2 passed.
- Full: `npx vitest run --maxWorkers=2` -> 142 files, 1712/1712 passed (no flake this run). `npm run typecheck` clean.
- Also checked by hand: the HEAD~ orion-remote answers the deploy.md check command with `unknown or misplaced option`,
  the new one with `bad metric in --metrics` (the doc quotes both).

New test names: test_backfill_passes_each_metric, test_backfill_refuses_empty_item, test_backfill_refuses_bad_metric,
test_backfill_days_range, test_purge_dry_run_by_default, test_purge_source_type_is_a_known_rung,
test_compare_usd_passthrough, test_backfill_on_kinds_other_than_backfill_refused (class Phase3VerbTests). Every refusal
asserts exit 64, no Orion call, and remote.log's last line ends `refused` and contains none of the argument words.

## Files
scripts/provision/files/orion-remote, scripts/provision/test/test_orion_remote.py, tests/release/orionRemote.test.ts
(R8 repoint), docs/ops/deploy.md.

## Self-review
- Argv order matches the CLI's options (`--metric` repeatable, `--backfill-days`, `--source-type`, `--yes`, `--json`,
  `--by`) in src/cli/commands/{job,data}.ts. Orion still validates metrics against the asset config (remote only
  shapes them).
- `--days` on compare-usd absent -> nothing passed (CLI default 91).
- 20-metric cap: 20 accepted (asserted), 21 refused.

## Concerns
- docs/ops/deploy.md ends with an orphaned ssh-verb code block (no heading, pre-existing after the Task 11 section). I
  inserted the new section before it, so it now follows "Phase 3 R1 release"; I did not move it (outside my brief).
- The section's `ST`/`PR` refer to definitions earlier in the file (First staging deploy / Prod's initial load).
- `data purge` RUNG list is duplicated in orion-remote (no JS source to cross-check it from Python, unlike JOB_KINDS);
  the orionRemote.test.ts check could be extended to compare RUNGS with SourceType if the controller wants.

# Fix round 1 (Task 3 review I-1, M-1..M-5) — commit 6f97c21

## What
- **I-1** (docs/ops/deploy.md rollback note): rewritten. The deploy keys have no drain verb; `rollback` drains with a
  30 min wait and aborts (exit 1, nothing switched) when a backfill runs past it. Before `rollback` past this release:
  `ssh orion-<env> jobs`, wait until no `backfill` is `running`; a `backfill` still `queued` fails "no handler" on the
  older release with no retry — re-queue it with `job run-now backfill ...` after rolling forward again. "drain the
  daemon" removed.
- **M-1** (orion-remote): `pattern()`, `count()` and `metric_list()` use `re.fullmatch` (a quoted trailing `\n` no
  longer passes). `pattern()` is shared by every older verb (tag, sha256, id, asset, metric, who, day, ISO, job kind), so
  all of them are now stricter in the same way (refuse a trailing newline; nothing they accepted before is refused
  otherwise). `prune()`'s `TAG_RE` (directory names, not caller input) also moved to fullmatch for consistency.
- **M-2** (docs): the sizing note now names the R9 window too (a nightly begun under 2 h ago: waits until slot + 2 h),
  with the prod example (queued 00:50 UTC -> starts 02:45 UTC at the earliest).
- **M-3** (tests/release/orionRemote.test.ts): the compile test also pins `RUNGS` (multi-line tuple) to
  `SOURCE_TYPES` from src/db/purge.ts, same order; the orion-remote comment names the check. Test renamed
  "compiles; its job kinds are JOB_KINDS and its rungs SOURCE_TYPES".
- **M-4** (docs): the pre-existing heading-less ssh-verb block got its own heading, `## The ssh verbs (any release)`,
  after the `<!-- release block: Task 8 -->` marker (so Task 8's block stays inside the Phase 3 R1 section).
- **M-5** (test_orion_remote.py `assert_refused`): compares the shlex-split words (quotes removed) instead of raw text;
  asserts the log tail after `<ISO> <user> ` is exactly `<verb> <argc> refused`, and that no argument value (any
  length, empty excepted) is in it.

## Tests (RED -> GREEN)
- M-1 RED: new `Phase3VerbTests.test_trailing_newline_refused` (quoted `'flow_usd.burn\n'`, a list ending in one,
  `--backfill-days '3\n'`, `--days '3\n'`, `--source-type 'third_party\n' --yes`, asset `'aero\n'`, kind
  `'refresh\n'`) before the fix: `AssertionError: 0 != 64 : job run-now backfill aero --metrics 'flow_usd.burn\n'
  --backfill-days 10` (FAILED, failures=1). GREEN after fullmatch.
- M-5 RED (mutation, reverted): orion-remote temporarily logged the shlex values containing `;` or a space before
  `refused`. HEAD's old assertion: 4 refusal tests `OK` (vacuous). New assertion: `FAILED (failures=4)`, e.g.
  `'job 8 a;id refused' != 'job 8 refused'`, `'data 7 third_party  refused' != 'data 7 refused'`.
- M-3 RED (mutation, reverted): `market_data` dropped from RUNGS -> the compile test fails (`- "market_data"`);
  restored -> passes.
- Python: `python3 -m unittest scripts/provision/test/test_orion_remote.py` -> Ran 52 tests, OK (51 + 1).
- vitest full `--maxWorkers=2` run 1: 1734/1735, one failure `tests/push/gitPublisher.test.ts > git publisher: a moved
  remote is refused, alerted once, outbox kept` (9786 ms, a load timeout; file not touched); alone at
  `--maxWorkers=1`: 7/7 passed. Run 2: 1735/1735, 143/143 files. `tests/release/orionRemote.test.ts` alone: 2/2.
- `npm run typecheck`: clean.

## Files
scripts/provision/files/orion-remote, scripts/provision/test/test_orion_remote.py, tests/release/orionRemote.test.ts,
docs/ops/deploy.md.

## Concerns
- None blocking. The fullmatch tightening applies to every verb that goes through `pattern()` (stricter only).
