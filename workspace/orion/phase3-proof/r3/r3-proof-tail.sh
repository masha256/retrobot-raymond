#!/bin/bash
# Resume r3-proof.sh after its false STOP (psql printed SET before the count): steps from "counts after" on, local copy only.
set -u
stop() { echo "STOP: $*"; exit 1; }
A="aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv"
OUT=/home/hermes/.hermes/profiles/raymond/workspace/orion/phase3-proof/r3
NEW=/home/hermes/git/orion/.worktrees/proof-67e28f5
P=$(cat $OUT/copy-dir.txt)
n() { ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node $NEW/dist/cli/index.js "$@"; }
S=$(grep '^ORION_DB_SCHEMA=' $P/new/.env | cut -d= -f2)
Q() { psql 'postgresql://orion_dev@/orion_dev?host=/var/run/postgresql' -qAtF $'\t' -c "set search_path=$S; $1"; }
D=$(python3 -c 'import json;print(json.load(open("'$OUT'/days.json"))["D"])'); D91=$(python3 -c 'import json;print(json.load(open("'$OUT'/days.json"))["D91"])')
Q "select asset_id, source_type, status, (superseded_by is null) active, count(*), min(observed_at), max(observed_at) from observations where metric_key = 'circulating_supply' group by 1,2,3,4 order by 1,2,3,4" > $OUT/counts-after.tsv || stop "counts after"
md=$(Q "select count(*) from observations where source_type = 'market_data'"); echo "market_data rows after: $md"; [ "$md" = "0" ] || stop "market_data rows remain: $md"
for a in $A; do n report yield $a --day $D --json > $OUT/new/$a.json || stop "new $a"; n report yield $a --day $D91 --json > $OUT/new/$a-91.json || stop "new $a-91"; done
echo '{"_comment": "empty: list every differing path"}' > $OUT/empty-allowlist.json
for a in $A; do for f in $a $a-91; do
  python3 $NEW/tools/phase3-proof/flatdiff.py $OUT/old/$f.json $OUT/new/$f.json --allow $OUT/empty-allowlist.json --asset $a --json > $OUT/diff/$f.json
  python3 $NEW/tools/phase3-proof/flatdiff.py $OUT/old/$f.json $OUT/newpre/$f.json --allow $OUT/empty-allowlist.json --asset $a --json > $OUT/diff/pre-$f.json
done; done
python3 $OUT/r3-summary.py > $OUT/summary.txt 2>&1; echo "summary exit $?"
