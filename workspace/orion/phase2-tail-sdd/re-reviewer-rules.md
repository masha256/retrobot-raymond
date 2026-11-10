# Reviewer / re-reviewer rules (binding)
- Read-only: read via `git show <sha>:<path>` / `git diff <base> <sha>`; to run anything use your own `git worktree add --detach /home/hermes/git/orion/.worktrees/rev-<n> <sha>` + `npm ci`, removed with `git worktree remove --force` at the end. Edit nothing except your findings/re-review file.
- No network, no ssh, no Postgres outside orion_test (ORION_TEST_DATABASE_URL='postgresql://orion_dev@/orion_test?host=/var/run/postgresql').
- Findings: Critical / Important / Minor, each with file:line, the concrete failure, and a minimal reproducing test shape. Check every named risk in the dispatch explicitly and say what you checked.
- Re-review: per finding ADDRESSED / NOT ADDRESSED with evidence, then new breakage.
