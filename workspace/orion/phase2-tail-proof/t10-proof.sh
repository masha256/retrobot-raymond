#!/usr/bin/env bash
# Task 10 controller proof on a read-only prod copy (G3). Never writes prod.
set -uo pipefail
WT=/home/hermes/git/orion/.worktrees/proof-0bd7a40
R=/home/hermes/git/orion/.worktrees/rel-2026.11.09.1/orion-2026.11.09.1
BASE=/home/hermes/.hermes/profiles/raymond/workspace/orion/phase2-tail-proof
mkdir -p $BASE; P=$BASE/p-$(date -u +%m%dT%H%M); echo $P > $BASE/last-P
cd $WT
export P2_PROD_SSH='-i /home/hermes/.ssh/orion-prod_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes orion-prod@192.168.0.12'
/usr/bin/python3 tools/phase2-proof/prod_copy.py "$P" "$R" "$WT" > $P.copy.log 2>&1; echo "copy rc $?"; tail -1 $P.copy.log
S=$(cat $P/schema); echo "schema $S"
URL='postgresql://orion_dev@/orion_dev?host=/var/run/postgresql'
# 1. origin check before the drop
ORION_DATABASE_URL=$URL ORION_DB_SCHEMA=$S npx tsx tools/phase2-proof/origin-check.ts > $P/origin-check.txt 2>&1; echo "origin-check rc $?"; tail -3 $P/origin-check.txt
# 2. old-release reports at 0005 (D = 2 days back)
D=$(date -u -d '2 days ago' +%F); echo "D=$D"
mkdir -p $P/out/old $P/out/new
for a in $(ls $P/new/assets | sed 's/\.yaml$//'); do
  (cd $P/old && ORION_HOME=$P/old ORION_ENV_FILE=$P/old/.env node $R/dist/cli/index.js report yield $a --day $D --json > $P/out/old/$a.json 2> $P/out/old/$a.err) || echo "old $a rc $?"
  (cd $P/old && ORION_HOME=$P/old ORION_ENV_FILE=$P/old/.env node $R/dist/cli/index.js report yield $a --day $D --legacy --json > $P/out/old/$a.legacy.json 2>/dev/null) || echo "old legacy $a rc $?"
done
# 3. new dist: migrate --breaking, then reports
(cd $P/new && ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node $WT/dist/cli/index.js db migrate --json > $P/migrate-plain.json 2>&1); echo "migrate without --breaking rc $? (expect refusal)"; tail -c 300 $P/migrate-plain.json; echo
(cd $P/new && ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node $WT/dist/cli/index.js db migrate --breaking --json > $P/migrate-new.json 2>&1); echo "migrate --breaking rc $?"
psql -U orion_dev -d orion_dev -Atc "select max(id) from \"$S\".schema_migrations; select count(*) from information_schema.columns where table_schema='$S' and table_name='observations' and column_name='source'"
for a in $(ls $P/new/assets | sed 's/\.yaml$//'); do
  (cd $P/new && ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node $WT/dist/cli/index.js report yield $a --day $D --json > $P/out/new/$a.json 2> $P/out/new/$a.err) || echo "new $a rc $?"
  (cd $P/new && ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node $WT/dist/cli/index.js report yield $a --day $D --legacy --json > $P/out/new/$a.legacy.json 2>/dev/null) || echo "new legacy $a rc $?"
done
echo DONE $P
