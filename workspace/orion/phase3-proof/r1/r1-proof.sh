#!/bin/bash
# Phase 3 R1 proof, steps 3-5 (controller). Usage: r1-proof.sh <P> <D>
set -u
P=$1; D=$2
WT=/home/hermes/git/orion/.worktrees/phase3
OLD=/home/hermes/git/orion/.worktrees/rel-2026.11.11.1/orion-2026.11.11.1
OUT=$P/out; mkdir -p $OUT/old $OUT/new $OUT/old-default $OUT/new-default
ASSETS="aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv"
old() { (cd $P/old && ORION_HOME=$P/old ORION_ENV_FILE=$P/old/.env node $OLD/dist/cli/index.js "$@"); }
new() { (cd $P/new && ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node $WT/dist/cli/index.js "$@"); }
URL=$(grep '^ORION_DATABASE_URL=' $P/old/.env | cut -d= -f2-); SCH=$(cat $P/schema)
q() { psql "$URL" -At -c "set search_path=$SCH; $1"; }

echo "== carry check (Task 4): disclosed rows with an adapter locator (want 0)"
q "select count(*) from observations where method='disclosed' and locator ? 'adapter'"
echo "== purge counts before (prod copy)"
q "select asset_id||' '||metric_key||' '||source_type||' '||count(*) from observations where (asset_id,metric_key) in (('cake','flow_usd.fees'),('cake','flow_usd.llama_revenue'),('lit','flow_usd.fees'),('lit','flow_usd.llama_revenue'),('uni','flow_usd.swap_fees'),('vvv','flow_usd.revenue_proxy'),('lit','unlocks_next_year'),('pump','unlocks_next_year')) group by asset_id,metric_key,source_type order by 1"

echo "== old reports (before any write)"
for a in $ASSETS; do
  old report yield $a --day $D --json > $OUT/old/$a.json 2>$OUT/old/$a.err; echo "old $a $?"
  old report yield $a --json > $OUT/old-default/$a.json 2>/dev/null
done
echo "== new dist migrate (0007)"
new db migrate --json > $P/migrate-new.json 2>&1; echo "migrate $?"; cat $P/migrate-new.json | head -20
echo "== fetch lit/pump unlocks on the new home"
new data fetch lit --metric unlocks_next_year --json > $OUT/fetch-lit.json 2>$OUT/fetch-lit.err; echo "fetch lit $?"
new data fetch pump --metric unlocks_next_year --json > $OUT/fetch-pump.json 2>$OUT/fetch-pump.err; echo "fetch pump $?"
q "select asset_id||' '||source_type||' '||method||' '||value||' '||coalesce(citation_url,'-') from observations where metric_key='unlocks_next_year' and superseded_by is null order by observed_at desc limit 2"
echo "== new reports"
for a in $ASSETS; do
  new report yield $a --day $D --json > $OUT/new/$a.json 2>$OUT/new/$a.err; echo "new $a $?"
  new report yield $a --json > $OUT/new-default/$a.json 2>/dev/null
done
echo "== default days old/new"
for a in $ASSETS; do echo "$a $(python3 -c "import json,sys;print(json.load(open('$OUT/old-default/$a.json')).get('day'))") $(python3 -c "import json,sys;print(json.load(open('$OUT/new-default/$a.json')).get('day'))")"; done
echo done
