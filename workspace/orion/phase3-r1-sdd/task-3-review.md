# Task 3 review: orion-remote verbs and the runbook (de7f7e4..e88130f)

### Spec Compliance

- ✅ Spec compliant. Every Files entry has its hunk. orion-remote has the docstring (lines 30-41), `v_data` (420-430), `v_job` (494-507) and `JOB_KINDS`; `VERBS` needed no change because `data` and `job` were already there. test_orion_remote.py has `Phase3VerbTests` with all eight named tests. deploy.md has a new "Phase 3 R1 release" section (401-453).
  - `job run-now backfill` sends Orion `--metric` once per item, then `--backfill-days N --by raymond --json` (orion-remote:500-504). `--metrics`/`--backfill-days` on any other kind are refused (505-506), and so is a backfill with `--slot`.
  - `data compare-usd` is a passthrough that adds `--json` (R3). `--days` is optional, 1..400, and not sent when absent, so the CLI default of 91 applies (420-422).
  - `data purge` sends `--yes` only when the exact token `--yes` was given, and always adds `--json` (R3) (423-428).
  - The step 2 helpers are in place: `METRIC_RE` and `COUNT_RE` are reused, `RUNG_RE` is built from `RUNGS` (109), and `parse()`'s repeated-flag rule is unchanged.
  - R8: the `backfill` exclusion is gone from tests/release/orionRemote.test.ts:37.
  - R4: the section is in deploy order: the `orion-host.sh` re-run from a fixed `git archive` snapshot comes first, then the per-env steps, and the `<!-- release block: Task 8 -->` marker is at 453. The section also says that on an older release the new verbs fail with Orion's own "unknown command" error (423-427).
  - R10: the rollback note is present (449-451), but see I-1. R11: the sizing note is present (446-448), but see M-2.
  - The constants match the CLI. `--metric` is repeatable (`collect`), and `--backfill-days`, `--source-type`, `--yes` and `--json` all exist (src/cli/commands/job.ts:54-56, data.ts:220-223, 238).
  - Nothing extra was added beyond `METRICS_MAX = 20`, a reasonable cap that is tested.
- ⚠️ Cannot verify from this diff: whether the deploy.md example `$PR data purge lit --metrics unlocks_next_year --source-type third_party` (deploy.md:443) is accepted. That depends on LIT's `unlocks_next_year` source type after Task 4, and `purge.ts:143-144` refuses the current source's type. The controller should confirm it after Task 4, or Task 8 should adjust it.

### Strengths

- Validation stays inside the existing `parse()` contract. A metric list item can never contain `-`, because `METRIC_RE` has no `-`. Every value that starts with `-` is refused by `parse()` (orion-remote:322). The rung is an exact-match alternation, not a character class.
- `each()` builds argv as separate elements, and nothing goes through a shell.
- The tests assert the exact argv Orion receives, including the 20-item boundary, `x`*64 accepted and 65 refused, and nine-of-nine rungs accepted. Every refusal case checks exit 64, that Orion was not called (the `calls()` count), and a `refused` log line.
- The deploy.md check command really does tell the old and new orion-remote apart (I traced both through `parse()`). It also queues nothing in either case.
- The tests are the brief's tests, plus refusal variants (`--json`, `--force`, `--yes yes`, an extra positional).

### Named risks (verdict each)

1. **Shell/argv injection: no injection. One regex-anchor weakness (M-1).**
   - No caller text reaches a shell. `orion()` gets an argv list, `split_command` uses shlex in POSIX mode, and each `--metrics` item becomes exactly one argv element after its own `--metric` (293-295).
   - A list item that starts with `-` cannot pass `METRIC_RE`. A `,` only splits the list, and empty items are refused.
   - `--source-type` is limited to the nine rungs. Probes of `THIRD_PARTY`, `third_party,log_scan`, `defillama` and `''` were all refused, and they are also in the tests.
   - What I checked: in my own worktree at e88130f, a probe through the `Phase3VerbTests` harness showed that a trailing newline inside quotes passes the new validators (see M-1). Orion then fails safe: the source type is checked against `SOURCE_TYPES` (src/db/purge.ts:82), backfill metrics are checked against the config (backfill.ts:66), and `--backfill-days` is trimmed (job.ts:38).
2. **Destructive by default: safe.**
   - `--yes` is sent only when `o.get('yes')` is set, and only the exact `--yes` token sets it (orion-remote:311-321, 427).
   - Probes, all exit 64 with no Orion call: `--metrics=--yes` (unknown option), `--metrics --yes` ("needs a value"), `-- --yes`, `--ye`, and `--yes yes` (too many arguments, in the tests).
   - A metric can never be `--yes`, because `-` is not in `METRIC_RE`.
   - An asset positional cannot start with `-`, because `parse()` checks the option branch first. `ASSET_RE` itself would allow `--yes`, so this is worth knowing, but it is not reachable.
   - Commander's options cannot be reached by abbreviation, since `--ye` is refused upstream anyway.
3. **Logging: meets the contract.**
   - Refusals go through `Refused` and `log_call(env, verb, argc, 'refused')` (orion-remote:1115-1118), and successes log `job 8 ok`. No argument text is logged on either path.
   - `metric_list` and `count` raise only `Refused`. `int(v)` runs only after `COUNT_RE` matches, so it cannot raise.
   - The tests assert that the argument words are absent from the log line (test_orion_remote.py:917-919). That check is weak for quoted words (see M-5), but the code itself is correct.
4. **Docs accuracy: mostly correct. One Important gap (I-1) and one Minor gap (M-2).**
   - Correct:
     - Flag names, comma lists and the examples work through ssh as written (no shell metacharacters).
     - `$ST`/`$PR` are defined at deploy.md:104 and :189.
     - The `orion-host.sh` flags match README §4.
     - The `git archive | tar` snapshot command is correct and makes no change when re-run.
     - The nightly times (stage 02:45, prod 00:45) match docs/ops/daemon.md:79.
     - `~/home/purged` = `$ORION_HOME/purged`.
     - The R11 sentence is present.
   - Problems: the R10 note is not actionable as written (I-1), and the sizing note leaves out one deferral window (M-2).

### Issues

#### Critical (Must Fix)

None.

#### Important (Should Fix)

- **I-1. The rollback note tells the operator to drain, which the deploy keys cannot do, and does not say that the rollback itself fails while a backfill runs** (docs/ops/deploy.md:449-451).
  - What the note says: "let running backfills finish or drain the daemon".
  - Why that doesn't work:
    - orion-remote has no `daemon drain` verb (VERBS, orion-remote:1057-1082).
    - The `rollback` verb already drains, with `--wait 30m` (orion-remote:85, 890).
    - With a backfill running longer than that, the drain ends in `drain_timeout` (src/cli/commands/daemon.ts:119-120). orion-remote then undrains and raises `Failed`, which exits 1 and aborts the rollback (orion-remote:897-899).
    - Draining also does nothing for a *queued* backfill. Under R10, a queued backfill still fails with "no handler" on the older daemon.
  - Why it matters: backfill is the first job kind that is multi-hour by design. During an incident, an operator who follows this note gets a failed rollback with no explanation.
  - Fix: one or two sentences. `rollback` drains with a 30 min wait and fails ("drain timed out; still running job … backfill") while a backfill runs past that, so check `$ST jobs` first and wait for it to finish. A queued backfill fails "no handler" on the older daemon (R10, one failed row); re-queue it after a roll forward.

#### Minor (Nice to Have)

- **M-1. A trailing newline passes the new validators** (orion-remote:109 `RUNG_RE`, 288 via `METRIC_RE`, 274 via `COUNT_RE`).
  - Cause: Python's `$` matches before a final `\n`, and `split_command` allows a newline inside quotes. So `--metrics 'flow.fees\n'`, `--backfill-days '10\n'` and `--source-type 'third_party\n' --yes` all reach Orion unchanged (probe output, exit 0).
  - Impact: Orion fails safe in every case (purge.ts:82, backfill.ts:66, job.ts:38). The weakness predates this task (`METRIC_RE`, `ASSET_RE`, `COUNT_RE`), but the docs promise each item is `[a-z0-9_.]{1,64}` (deploy.md:432-433), and this script is the security boundary.
  - Fix: use `regex.fullmatch` (or `\Z`) in `pattern`, `count` and `metric_list`, plus one test with a quoted `\n`. This can be a follow-up across all the regexes.
- **M-2. The sizing note leaves out the deferral after the slot** (deploy.md:446-448).
  - The note lists "under 4 h away" and "while that night's refresh / nightly_report jobs are unfinished". It omits the R9 window: a backfill also defers until slot + 2 h after each nightly (backfill.ts:91).
  - Impact: an operator who queues at 00:50Z on prod will see it wait until 02:45Z with no explanation.
- **M-3. `RUNGS` is duplicated with no cross-check against the TypeScript** (orion-remote:95-96).
  - The report says there is "no JS source to cross-check it from". That is wrong: `SOURCE_TYPES` is exported at src/db/purge.ts:28.
  - Fix: extend tests/release/orionRemote.test.ts the same way it already checks `JOB_KINDS`, to catch drift when a rung is added.
- **M-4. The new section's placement makes an older block look like part of it** (deploy.md:453 onward).
  - The section sits in front of the pre-existing heading-less ssh-verb code block, so that block now reads as part of "Phase 3 R1 release".
  - The block lists none of the new verbs.
  - Task 8 will add its block at the marker, also above that orphan block.
  - Fix: give the orphan block a heading (or move it) when Task 8 lands.
- **M-5. The log-redaction check in `assert_refused` is vacuous for quoted arguments** (test_orion_remote.py:917-919).
  - It compares the raw command words, quotes included (`"'a;id'"`, `"' 10'"`), so `assertNotIn` passes trivially for those cases. Words of 2 characters or fewer are skipped entirely.
  - The code is right; only the assertion is weak. Fix: compare against the shlex-split words.

### Checks run

- Focused tests: `python3 -m unittest scripts/provision/test/test_orion_remote.py` in my own detached worktree at e88130f gave `Ran 51 tests … OK`, matching the report.
- Probe through the harness (temporary file, worktree removed afterwards):
  - Exit 0: the three newline values in M-1.
  - Exit 64: `--metrics=--yes`, `--metrics --yes`, `-- --yes`, `--ye`.
- Read at e88130f: orion-remote `parse`, `split_command`, `drain`, `main` and `log_call`; src/cli/commands/{job,data,daemon}.ts option definitions; src/db/purge.ts validation; src/daemon/jobs/backfill.ts `backfillWaitUntil`; README §4; docs/ops/daemon.md:79.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The verbs are correct and tight on the security-critical points. There is no shell or argv injection, purge is dry-run by default and `--yes` cannot be injected, and refusals are logged without argument text, all with strong argv-level tests. The one blocking issue is the R10 rollback note (I-1), which points to a drain the deploy keys cannot perform and hides that a rollback fails while a backfill is running. That is a one-sentence documentation fix.
