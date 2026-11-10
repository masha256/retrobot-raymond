#!/usr/bin/env bash
# Task 11 controller proof on a read-only prod copy (G4): v2 old (release orion-2026.11.09.1 at 0005) vs new (b48c3cf at 0006),
# fixed day D and the default day (no --day). Never writes prod.
set -uo pipefail
SHA=${1:?sha}
WT=/home/hermes/git/orion/.worktrees/proof-$SHA
R=/home/hermes/git/orion/.worktrees/rel-2026.11.09.1/orion-2026.11.09.1
BASE=/home/hermes/.hermes/profiles/raymond/workspace/orion/phase2-tail-proof
P=$TMPDIR/t11p-$(date -u +%m%dT%H%M); echo $P > $BASE/last-P
cd $WT
export P2_PROD_SSH='-i /home/hermes/.ssh/orion-prod_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes orion-prod@192.168.0.12'
/usr/bin/python3 tools/phase2-proof/prod_copy.py "$P" "$R" "$WT" > $P.copy.log 2>&1; rc=$?; echo "copy rc $rc"; tail -1 $P.copy.log; [ $rc -eq 0 ] || exit 1
S=$(cat $P/schema); echo "schema $S"
D=$(date -u -d '2 days ago' +%F); echo "D=$D"
mkdir -p $P/out/old $P/out/new
A=$(ls $R/assets | sed 's/\.yaml$//')
for a in $A; do
  (cd $P/old && ORION_HOME=$P/old ORION_ENV_FILE=$P/old/.env node $R/dist/cli/index.js report yield $a --day $D --json > $P/out/old/$a.json 2> $P/out/old/$a.err) || echo "old $a rc $?"
  (cd $P/old && ORION_HOME=$P/old ORION_ENV_FILE=$P/old/.env node $R/dist/cli/index.js report yield $a --json > $P/out/old/$a.default.json 2>/dev/null) || echo "old default $a rc $?"
done
(cd $P/new && ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node $WT/dist/cli/index.js db migrate --breaking --json > $P/migrate-new.json 2>&1); echo "migrate --breaking rc $?"
for a in $A; do
  (cd $P/new && ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node $WT/dist/cli/index.js report yield $a --day $D --json > $P/out/new/$a.json 2> $P/out/new/$a.err) || echo "new $a rc $?"
  (cd $P/new && ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node $WT/dist/cli/index.js report yield $a --json > $P/out/new/$a.default.json 2>/dev/null) || echo "new default $a rc $?"
done
(cd $P/new && ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node $WT/dist/cli/index.js report yield crv --legacy --json > /dev/null 2>$P/legacy-flag.err); echo "new --legacy rc $? (expect non-zero)"; head -c 200 $P/legacy-flag.err; echo
echo DONE $P
