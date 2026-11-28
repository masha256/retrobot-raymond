#!/bin/bash
# Phase 3 R4 proof (plan Task 10, controller): read-only prod copy -> old (orion-2026.11.21.1) vs new (fddaa14) reports
# at D (today-2 UTC) and D-91; on the COPY only: export the stored DefiLlama flow_usd.fees rows (dev-only reference),
# purge them, backfill AERO's five pool metrics from 2026-10-22 with real (read-only) RPC, re-run reports, flatdiff all
# 13 assets with an empty allowlist, and the dev-only acceptance check. Prod is only read (prod_copy.py via sql-ro).
# Refuses inside the prod nightly window (20:45Z-02:45Z) and 05:00-06:30 PT. Stops at the first failure.
set -u
stop() { echo "STOP: $*"; exit 1; }
nowmin=$(( 10#$(date -u +%H) * 60 + 10#$(date -u +%M) ))
{ [ $nowmin -ge $((20*60+45)) ] || [ $nowmin -lt $((2*60+45)) ]; } && stop "inside the prod nightly window 20:45Z-02:45Z"
hm=$(TZ=America/Los_Angeles date +%H%M); [ "$hm" -ge 0500 ] && [ "$hm" -lt 0630 ] && stop "inside 05:00-06:30 PT"
[ "$hm" -ge 1630 ] && [ "$hm" -lt 1715 ] && stop "inside 16:30-17:15 PT"
A="aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv"
POOL="flow_usd.voter_fees flow_usd.lp_fees flow_usd.pool_fees_gross flow_usd.vote_incentives flow_usd.protocol_subsidy"
OUT=/home/hermes/.hermes/profiles/raymond/workspace/orion/phase3-proof/r4
OLD=/home/hermes/git/orion/.worktrees/proof-old-2635cae
NEW=/home/hermes/git/orion/.worktrees/proof-new-06d4d0b
[ -f $OLD/dist/cli/index.js ] && [ -f $NEW/dist/cli/index.js ] || stop "old or new dist missing"
mkdir -p $OUT/old $OUT/newpre $OUT/new $OUT/diff $OUT/purge $OUT/fetch
P=${TMPDIR:?}/r4copy-$(date -u +%Y%m%dT%H%M%SZ)
echo "$P" > $OUT/copy-dir.txt
echo "== prod copy $(date -u +%T)"
P2_PROD_SSH='-i /home/hermes/.ssh/orion-prod_ed25519 -o IdentitiesOnly=yes orion-prod@192.168.0.12' \
  python3 $NEW/tools/phase2-proof/prod_copy.py "$P" $OLD $NEW > $OUT/prod_copy.log 2>&1 || stop "prod_copy exit $? (see prod_copy.log)"
o() { ORION_HOME=$P/old ORION_ENV_FILE=$P/old/.env node $OLD/dist/cli/index.js "$@"; }
n() { ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node $NEW/dist/cli/index.js "$@"; }
n db migrate --json > $OUT/migrate-new.json 2>&1 || stop "new migrate exit $?"
# the backfill reads 8 chains: the new home needs the RPC URLs (values never printed)
B=$(grep -E '^ORION_BASE_RPC_URL=' /home/hermes/git/orion/.env | cut -d= -f2- | tr -d "\"'")
grep -E '^ORION_(ETH|BNB|BASE|SOL)_RPC_URL=' /home/hermes/git/orion/.env >> $P/new/.env || stop "rpc urls"
{ echo "ORION_OP_RPC_URL=${B/base-mainnet/opt-mainnet}"; echo "ORION_ARB_RPC_URL=${B/base-mainnet/arb-mainnet}"
  echo "ORION_INK_RPC_URL=${B/base-mainnet/ink-mainnet}"; echo "ORION_ROBINHOOD_RPC_URL=${B/base-mainnet/robinhood-mainnet}"
  echo "ORION_ARC_RPC_URL=${B/base-mainnet/arc-mainnet}"; echo "ORION_ELYSIUM_RPC_URL=${B/base-mainnet/elysium-mainnet}"; } >> $P/new/.env
chmod 600 $P/new/.env
D=$(date -u -d '2 days ago' +%F); D91=$(date -u -d "$D -91 days" +%F); Y=$(date -u -d 'yesterday' +%F)
printf '{"D": "%s", "D91": "%s", "yesterday": "%s"}\n' $D $D91 $Y > $OUT/days.json
echo "== reports old + new (before purge/backfill) D=$D D91=$D91 $(date -u +%T)"
for a in $A; do
  o report yield $a --day $D --json > $OUT/old/$a.json || stop "old $a"
  o report yield $a --day $D91 --json > $OUT/old/$a-91.json || stop "old $a-91"
  n report yield $a --day $D --json > $OUT/newpre/$a.json || stop "newpre $a"
  n report yield $a --day $D91 --json > $OUT/newpre/$a-91.json || stop "newpre $a-91"
done
S=$(grep '^ORION_DB_SCHEMA=' $P/new/.env | cut -d= -f2)
Q() { psql 'postgresql://orion_dev@/orion_dev?host=/var/run/postgresql' -qAtF $'\t' -c "set search_path=$S; $1"; }
echo "== DefiLlama reference export (dev-only) $(date -u +%T)"
Q "select source_type, (superseded_by is null) active, count(*), min(observed_at), max(observed_at) from observations where asset_id='aero' and metric_key='flow_usd.fees' group by 1,2 order by 1,2" > $OUT/fees-counts-before.tsv || stop "fees counts"
Q "select coalesce(json_object_agg(to_char(observed_at at time zone 'UTC','YYYY-MM-DD'), value), '{}') from observations where asset_id='aero' and metric_key='flow_usd.fees' and superseded_by is null and status <> 'rejected' and period_days = 1 and observed_at >= '2026-10-22'" > $OUT/dl-ref-stored-rows.json || stop "dl export"
echo "== purge dry + --yes $(date -u +%T)"
n data purge aero --metric flow_usd.fees --json > $OUT/purge/dry.json || stop "purge dry exit $?"
n data purge aero --metric flow_usd.fees --yes --json > $OUT/purge/yes.json || stop "purge --yes exit $?"
left=$(Q "select count(*) from observations where asset_id='aero' and metric_key='flow_usd.fees'"); echo "flow_usd.fees rows after: $left"
[ "$left" = "0" ] || stop "flow_usd.fees rows remain: $left"
NDAYS=$(( ( $(date -u -d $Y +%s) - $(date -u -d 2026-10-22 +%s) ) / 86400 + 1 ))
EXP=$NDAYS
MARGS=""; for m in $POOL; do MARGS="$MARGS --metric $m"; done
echo "== backfill $NDAYS days (2026-10-22..$Y) $(date -u +%T)"
for i in 1 2 3 4 5 6 7 8 9; do
  s=$(date +%s)
  n data fetch aero $MARGS --backfill-days $((NDAYS + 1)) --json > $OUT/fetch/run-$i.json 2> $OUT/fetch/run-$i.stderr; rc=$?
  have=$(Q "select min(c) from (select m, (select count(distinct (observed_at - interval '1 day')::date) from observations o where o.asset_id='aero' and o.metric_key=m and o.superseded_by is null and o.observed_at > '2026-10-22' and o.observed_at <= '$Y'::date + interval '1 day') c from unnest(array['flow_usd.voter_fees','flow_usd.lp_fees','flow_usd.pool_fees_gross','flow_usd.vote_incentives','flow_usd.protocol_subsidy']) m) x")
  echo "run $i exit $rc $(( $(date +%s)-s ))s days stored (min over 5 metrics): $have / $EXP"
  [ $rc -eq 0 ] || stop "fetch run $i exit $rc (see fetch/run-$i.*)"
  oc=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('outcome'))" $OUT/fetch/run-$i.json)
  [ "$oc" = "ok" ] || stop "fetch run $i outcome $oc (see fetch/run-$i.json)"
  [ "$have" = "$EXP" ] && break
done
[ "$have" = "$EXP" ] || stop "backfill incomplete: $have / $EXP"
Q "select metric_key, source_type, count(*), min(observed_at), max(observed_at), round(sum(value)::numeric,2) from observations where asset_id='aero' and metric_key like 'flow_usd.%' and superseded_by is null group by 1,2 order by 1,2" > $OUT/pool-counts-after.tsv
Q "select kind, dedupe_key, severity, occurrences from anomalies where asset_id='aero' and status='open' order by 1,2" > $OUT/anomalies-aero-open.tsv
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
echo "== acceptance (dev-only) $(date -u +%T)"
SQL=$(python3 $NEW/tools/phase3-proof/r4_acceptance.py --print-sql | sed 's/\$\$/'"'"'/g')
Q "select json_build_object('rows', coalesce(json_agg(t), '[]')) from ($SQL) t" > $OUT/orion-rows.json || stop "orion rows"
python3 $NEW/tools/phase3-proof/r4_acceptance.py $OUT/orion-rows.json $OUT/dl-ref-stored-rows.json --dl-stamp end --to $D --json > $OUT/acceptance.json; echo "acceptance exit $?"
python3 $NEW/tools/phase3-proof/r4_acceptance.py $OUT/orion-rows.json $OUT/dl-ref-stored-rows.json --dl-stamp end --to $D > $OUT/acceptance.txt
echo "ALL DONE $(date -u +%T)"
