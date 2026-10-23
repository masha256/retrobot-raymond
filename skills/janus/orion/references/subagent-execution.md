# Executing an approved Orion plan with subagents

Use after Mike approves a plan and picks subagent-driven execution (superpowers:subagent-driven-development). This file covers the Orion- and Hermes-specific parts of that procedure.

## Setup
1. Check the live checkout first. If it sits on the feature branch, idle-check and `git checkout main`: cron builds and runs from that tree. Do all work in a worktree (`git worktree add $TMPDIR/orion-wt-<topic> feat/<topic>`, `ln -s /home/hermes/git/orion/node_modules node_modules`). Run the baseline suite there (`npx vitest run --maxWorkers=2 && npm run typecheck`) and record the counts in the ledger.
2. Keep the ledger, briefs (`scripts/task-brief PLAN N`) and review packages (`scripts/review-package PLAN BASE HEAD`) in the worktree's git-ignored `.superpowers/sdd/<plan>/`.
3. Extract, once, into files in that directory: the plan's Global Constraints + Review Focus, the implementer template's rules section, and the reviewer and re-review templates' rule sections. Each dispatch then points at those paths. Pasting them into every dispatch bloats the controller's context.
4. Run the pre-flight scan (task pairs that share files or interfaces) and write rulings into the ledger before Task 1. The usual one: a later task needs an accessor the plan never names (e.g. `ToolContext.targetDoc`). Name it in a ruling and carry it into every task that uses it.

## Harness mechanics (Hermes `delegate_task`)
- There is no model argument: every child runs on the session model. A finished child cannot be resumed, so a fix round is a fresh implementer given the brief, the report file and the findings file. The report file is the memory.
- Results arrive only after you end the turn. Append `Task N: dispatched (BASE <sha>)` to the ledger, then stop with a one-line status.
- Give implementers an `output_schema` (status, commits, test_summary, concerns, report_path).

## Per-task dispatch contents
The worktree path. "Never touch /home/hermes/git/orion, no push, no merge, no network, no live DB, never stage node_modules." The brief path and the shared rule files. Interfaces from earlier tasks the brief cannot know. Your rulings for this task, marked binding. The current suite counts. "Name any failing test." The exact commit message and the report path.

## Verify, review, rule
- Verify each result yourself before the review: `git log BASE..HEAD`, `git diff --stat`, rerun the task's focused test files. When an implementer reports an uncaptured one-off failure, rerun the full suite and record the result.
- When the type system forces an implementer to pull work forward (adding to `RUN_TYPES` breaks `Record<RunType, ...>` in `DEFAULT_BUDGETS` and the strict `agent.budgets` schema), accept it with a ledger ruling and tell the later task to skip that part.
- Give every reviewer 2–4 named risks drawn from the spec's invariants ("any route by which a machine-transcript citation reaches an in-signal row"). A focused check per named risk finds the cross-module holes that a diff-only read misses.
- Write each reviewer "cannot verify" item that belongs to a later task as `Carry to Task N:` in the ledger, and paste it into that task's dispatch as binding.
- Write a findings file (`task-N-findings.md`) with each finding and your binding ruling. The fix implementer and the scoped re-reviewer both read it.
- Check every "controller clarification" you put in a dispatch against the spec's invariants list before sending it. A clarification that loosens an invariant (e.g. "catalysts need no target-doc citation" against "every catalyst cites the document") gets built and passes review as compliant, because the reviewer is told it is binding.
- Before the task that freezes a fixture (the end-to-end test whose JSON a later component consumes), batch the accumulated rulings and reviewer wording fixes into one fix commit. Include a spec section "Amendments made during execution" listing each ruling and the section it amends. Then the fixture captures the final behaviour, and the spec stays the authority for later tasks.
- End-to-end fixture tasks: seed flows as confirmed `api` rows stamped at day end with exact per-quarter sums. Seed the asset's required level metrics (price, supply, emission, staked share, run rate) so a proposal's effect is a number rather than `blocked`. Normalize run timestamps and the config hash in the fixture, keep the real `agent run --json` shape for the consumer, and assert the repo's asset YAML hash pin after any approve-on-a-copy step.

## Review checks for agent-layer changes (the holes reviewers found)
- **Guards must hold after `ledger.commit`, not only in the staged ledger.** A flag that lives only in memory (e.g. `StagedObservation.live`) is lost on commit, and `eligibleObservations` re-decides from the DB row. Route the guarded case through something persisted (e.g. an `observation` proposal) rather than changing eligibility, because eligibility is the valuation path. The covering test: commit, then assert eligibility.
- **A read tool that reports "Orion's own measurement"** (e.g. a flow total feeding a dev finding's `orion_reading`) must sum only active CONFIRMED committed rows. Otherwise the analyst's own staged or provisional figure gets added on top of the fetched rows. Refuse, naming the ids, when any day is covered twice; never return a total in that case.
- Use one shared day-coverage helper (`observationDays` in `src/ingest/time.ts`) for every "which UTC days does this row cover" question. A daily row is stamped at day end (D+1 00:00Z), and a copied loop drifts from that convention.
- **Text cleaners for Slack or for files an LLM later reads:** remove control and format characters (Cc/Cf/...) FIRST, then strip `<@`, `<!`, `<#`, URLs and `<!--` markers, then cap. In the other order, a zero-width space inside `<!channel>` survives the regex and is re-joined into a live ping. Test with the sequence split by `\u200b` and `\x07`.
- **A Python driver of the Orion CLI must treat an error as `exit != 0` or `data.get('error')` being a dict.** Run rows always carry `"error": null`, so a check for an `error` key fails on success. Fake-`node` tests never caught this; the one real end-to-end run did (the digest printed `est $?`). Run the paid acceptance through the real script, not by hand.

## Stop point
Stop where the plan says (usually before merge, live build, first live fetch and any paid analyst run Mike has not approved). Report the per-task commits, the real suite counts, the plan's checklist, and every `Ruling:` line from the ledger with what it costs if wrong.
