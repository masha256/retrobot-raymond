#!/bin/bash
# Phase 3 R2 proof, stage A (controller): migrate the copy with the new dist (0008), then old vs new reports at D and D-91
# BEFORE any chain price exists (new side = new code on CoinGecko-era data: measures the per-transfer -> view change).
set -u
P=$(cat ~/.hermes/profiles/raymond/workspace/orion/phase3-proof/r2/copy-dir.txt)
OLD=/home/hermes/git/orion/.worktrees/rel-2026.11.12.1/orion-2026.11.12.1
NEW=/home/hermes/git/orion/.worktrees/proof-3aca04e
OUT=~/.hermes/profiles/raymond/workspace/orion/phase3-proof/r2
T=$NEW/tools/phase2-proof
cd $NEW
ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node dist/cli/index.js db migrate --json > $OUT/migrate-new.json 2>&1; echo "migrate-new exit $?"
for D in 2026-11-13 2026-08-14; do
  O=$TMPDIR/r2-pre-$D-$(date +%s)
  bash $T/reports.sh $OLD/dist $NEW/dist $P/old $P/new $D $O > $OUT/reports-pre-$D.log 2>&1; echo "reports $D exit $?"
  mkdir -p $OUT/pre-$D && cp -r $O/old $O/new $O/status.tsv $OUT/pre-$D/ 2>/dev/null
done
# default-day reports, both sides
mkdir -p $OUT/pre-default/old $OUT/pre-default/new
for a in aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv; do
  ORION_HOME=$P/old ORION_ENV_FILE=$P/old/.env node $OLD/dist/cli/index.js report yield $a --json > $OUT/pre-default/old/$a.json 2>/dev/null
  ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node dist/cli/index.js report yield $a --json > $OUT/pre-default/new/$a.json 2>/dev/null
done
echo done-A
