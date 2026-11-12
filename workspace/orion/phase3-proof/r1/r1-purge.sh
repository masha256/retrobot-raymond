#!/bin/bash
# Phase 3 R1 proof, step 6: purge rehearsal on the prod copy (controller). Usage: r1-purge.sh <P> <D>
set -u
P=$1; D=$2
WT=/home/hermes/git/orion/.worktrees/phase3
OUT=$P/out; mkdir -p $OUT/purge $OUT/new-after-purge
new() { (cd $P/new && ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node $WT/dist/cli/index.js "$@"); }
pairs=("cake flow_usd.fees flow_usd.llama_revenue" "lit flow_usd.fees flow_usd.llama_revenue" "uni flow_usd.swap_fees" "vvv flow_usd.revenue_proxy" "lit unlocks_next_year --source-type third_party" "pump unlocks_next_year --source-type third_party")
i=0
for p in "${pairs[@]}"; do
  set -- $p; a=$1; shift; args=(); st=()
  while [ $# -gt 0 ]; do if [ "$1" = --source-type ]; then st=(--source-type "$2"); shift 2; else args+=(--metric "$1"); shift; fi; done
  i=$((i+1))
  new data purge $a "${args[@]}" "${st[@]}" --json > $OUT/purge/$i-$a-dry.json 2>&1; echo "dry $i $a exit $?"
done
i=0
for p in "${pairs[@]}"; do
  set -- $p; a=$1; shift; args=(); st=()
  while [ $# -gt 0 ]; do if [ "$1" = --source-type ]; then st=(--source-type "$2"); shift 2; else args+=(--metric "$1"); shift; fi; done
  i=$((i+1))
  new data purge $a "${args[@]}" "${st[@]}" --yes --json > $OUT/purge/$i-$a-yes.json 2>&1; echo "yes $i $a exit $?"
done
for a in aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv; do
  new report yield $a --day $D --json > $OUT/new-after-purge/$a.json 2>/dev/null
  if cmp -s $OUT/new/$a.json $OUT/new-after-purge/$a.json; then echo "after-purge $a identical"; else echo "after-purge $a DIFFERS"; fi
done
ls -la $P/new/purged/ 2>&1
