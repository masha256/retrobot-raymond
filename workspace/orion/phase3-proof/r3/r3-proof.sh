#!/bin/bash
# Phase 3 R3 proof (plan Task 7 Steps 2-4, controller): read-only prod copy -> old vs new reports at D (today-2 UTC) and
# D-91, rebuild-supply-levels + market_data purge on the COPY (real RPC, read-only chain), counts, flatdiff, table.
# Prod is only read (prod_copy.py via sql-ro). Refuses to run before 2026-11-21T02:45Z (prod nightly -4 h/+2 h) or
# inside 05:00-06:30 PT. Stops at the first failure. Writes into $OUT; the copy lives in $TMPDIR (cleanup.py <P>).
set -u
stop() { echo "STOP: $*"; exit 1; }
[ "$(date -u +%s)" -ge "$(date -u -d '2026-11-21T02:45:00Z' +%s)" ] || stop "before 2026-11-21T02:45Z"
hm=$(TZ=America/Los_Angeles date +%H%M); [ "$hm" -ge 0500 ] && [ "$hm" -lt 0630 ] && stop "inside 05:00-06:30 PT"
A="aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv"
OUT=/home/hermes/.hermes/profiles/raymond/workspace/orion/phase3-proof/r3
OLD=/home/hermes/git/orion/.worktrees/rel-2026.11.15.1/orion-2026.11.15.1
NEW=/home/hermes/git/orion/.worktrees/proof-67e28f5
[ -x "$(command -v node)" ] || stop "node missing"
[ -f $OLD/dist/cli/index.js ] && [ -f $NEW/dist/cli/index.js ] || stop "old or new dist missing"
mkdir -p $OUT/old $OUT/newpre $OUT/new $OUT/dry $OUT/yes $OUT/dry2 $OUT/diff
P=${TMPDIR:?}/r3copy-$(date -u +%Y%m%dT%H%M%SZ)
echo "$P" > $OUT/copy-dir.txt
echo "== prod copy $(date -u +%T)"
P2_PROD_SSH='-i /home/hermes/.ssh/orion-prod_ed25519 -o IdentitiesOnly=yes orion-prod@192.168.0.12' \
  python3 $NEW/tools/phase2-proof/prod_copy.py "$P" $OLD $NEW > $OUT/prod_copy.log 2>&1 || stop "prod_copy exit $? (see prod_copy.log)"
o() { ORION_HOME=$P/old ORION_ENV_FILE=$P/old/.env node $OLD/dist/cli/index.js "$@"; }
n() { ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node $NEW/dist/cli/index.js "$@"; }
n db migrate --json > $OUT/migrate-new.json 2>&1 || stop "new migrate exit $?"
# the rebuild reads the chain: the new home needs the RPC URLs (values never printed)
grep -E '^ORION_(ETH|BNB|BASE|SOL)_RPC_URL=' /home/hermes/git/orion/.env >> $P/new/.env || stop "rpc urls"
chmod 600 $P/new/.env
D=$(date -u -d '2 days ago' +%F); D91=$(date -u -d "$D -91 days" +%F)
printf '{"D": "%s", "D91": "%s"}\n' $D $D91 > $OUT/days.json
echo "== reports old + new (before rebuild) D=$D D91=$D91 $(date -u +%T)"
for a in $A; do
  o report yield $a --day $D --json > $OUT/old/$a.json || stop "old $a"
  o report yield $a --day $D91 --json > $OUT/old/$a-91.json || stop "old $a-91"
  n report yield $a --day $D --json > $OUT/newpre/$a.json || stop "newpre $a"
  n report yield $a --day $D91 --json > $OUT/newpre/$a-91.json || stop "newpre $a-91"
done
S=$(grep '^ORION_DB_SCHEMA=' $P/new/.env | cut -d= -f2)
Q() { psql 'postgresql://orion_dev@/orion_dev?host=/var/run/postgresql' -AtF $'\t' -c "set search_path=$S; $1"; }
CQ="select asset_id, source_type, status, (superseded_by is null) active, count(*), min(observed_at), max(observed_at) from observations where metric_key = 'circulating_supply' group by 1,2,3,4 order by 1,2,3,4"
Q "$CQ" > $OUT/counts-before.tsv || stop "counts before"
echo "== rebuild dry $(date -u +%T)"
for a in $A; do s=$(date +%s); n data rebuild-supply-levels $a --json > $OUT/dry/rebuild-$a.json; rc=$?; echo "$a dry exit $rc $(( $(date +%s)-s ))s"; [ $rc -eq 0 ] || stop "$a rebuild dry exit $rc"; done
echo "== rebuild --yes $(date -u +%T)"
for a in $A; do s=$(date +%s); n data rebuild-supply-levels $a --yes --json > $OUT/yes/rebuild-$a.json; rc=$?; echo "$a yes exit $rc $(( $(date +%s)-s ))s"; [ $rc -eq 0 ] || stop "$a rebuild --yes exit $rc"; done
for a in $A; do n data rebuild-supply-levels $a --json > $OUT/dry2/rebuild-$a.json || stop "$a second dry"; done
echo "== purge dry + --yes $(date -u +%T)"
for a in aero cake crv hype link lit pump sky uni vvv; do
  n data purge $a --metric circulating_supply --source-type market_data --json > $OUT/dry/purge-$a.json || stop "$a purge dry exit $?"
done
for a in aero cake crv hype link lit pump sky uni vvv; do
  n data purge $a --metric circulating_supply --source-type market_data --yes --json > $OUT/yes/purge-$a.json || stop "$a purge --yes exit $?"
done
Q "$CQ" > $OUT/counts-after.tsv || stop "counts after"
md=$(Q "select count(*) from observations where source_type = 'market_data'"); echo "market_data rows after: $md"
[ "$md" = "0" ] || stop "market_data rows remain: $md"
echo "== reports new (after) $(date -u +%T)"
for a in $A; do
  n report yield $a --day $D --json > $OUT/new/$a.json || stop "new $a"
  n report yield $a --day $D91 --json > $OUT/new/$a-91.json || stop "new $a-91"
done
echo '{"_comment": "empty: list every differing path"}' > $OUT/empty-allowlist.json
for a in $A; do for f in $a $a-91; do
  python3 $NEW/tools/phase3-proof/flatdiff.py $OUT/old/$f.json $OUT/new/$f.json --allow $OUT/empty-allowlist.json --asset $a --json > $OUT/diff/$f.json
  python3 $NEW/tools/phase3-proof/flatdiff.py $OUT/old/$f.json $OUT/newpre/$f.json --allow $OUT/empty-allowlist.json --asset $a --json > $OUT/diff/pre-$f.json
done; done
python3 $OUT/r3-summary.py > $OUT/summary.txt 2>&1 || stop "summary exit $?"
cat $OUT/summary.txt
echo "ALL DONE $(date -u +%T)"
