# R3 plan constraints (Mike, merge-coordinator note, 2026-11-19)

- Base: `.worktrees/phase3-r3` (`feat/phase3-r3-supply`) fast-forwarded to GitHub main **06955e0** (RET-41 merged)
  on 2026-11-19. Record "base main 06955e0" in the R3 plan's Status line when the plan is written. Never rebase onto
  the uranus checkout's main; never reset that checkout (the RET-10 thread moved it, and Mike authorized that).
- Release block: follow docs/ops/deploy.md section 7 "Writing a per-env release block" (expected pre-remap artifacts
  with counts from the prod copy (and stage for prod's block), the step that clears them, a re-check that must show 0)
  and R2 step 5's pattern (the check exempts exactly those metrics and prints them; the re-check has no exemption).
- Stage `sql-ro` (`orion_stage_ro`) is on main but NOT installed on venus until Mike re-runs orion-host.sh from
  /home/hermes/orion-provision-06955e0. If a stage pre-check needs `ssh orion-stage sql-ro`, list that re-run as a
  prerequisite in the decision list; otherwise use only verbs that exist today.
- Allowlist classes: apply the R43 lesson (tools/phase3-proof/README.md): every growth `.change` / `.annualized`
  class entry gets its abs floor AND a rel alternative; check the proof reports for lines with a tiny prior window.
- No build, merge, stage or prod work until Mike approves the plan.
