#!/usr/bin/env bash
# AERO supply proof: every asset's `report yield` (v2 default and --legacy) with the release dist and the branch dist,
# against the same read-only prod copy. Usage: aero-supply-reports.sh <P> <out-subdir>
set -uo pipefail
P="$1"; OUT="$P/$2"; D="${3:-2026-11-09}"
R=/home/hermes/git/orion/.worktrees/rel-2026.11.08.1/orion-2026.11.08.1
WT=/home/hermes/git/orion/.worktrees/aero-supply
mkdir -p "$OUT/old" "$OUT/new"
for y in "$P"/new/assets/*.yaml; do
  a=$(basename "$y" .yaml)
  for mode in v2 legacy; do
    flag=""; [ "$mode" = legacy ] && flag="--legacy"
    (cd "$P/old" && ORION_HOME="$P/old" ORION_ENV_FILE="$P/old/.env" node "$R/dist/cli/index.js" report yield "$a" --day "$D" --json $flag) >"$OUT/old/$a.$mode.json" 2>"$OUT/old/$a.$mode.stderr"; e1=$?
    (cd "$P/new" && ORION_HOME="$P/new" ORION_ENV_FILE="$P/new/.env" node "$WT/dist/cli/index.js" report yield "$a" --day "$D" --json $flag) >"$OUT/new/$a.$mode.json" 2>"$OUT/new/$a.$mode.stderr"; e2=$?
    if cmp -s "$OUT/old/$a.$mode.json" "$OUT/new/$a.$mode.json"; then s=SAME; else s=DIFF; fi
    echo "$a $mode exit $e1/$e2 $s $(wc -c <"$OUT/new/$a.$mode.json")"
  done
done
