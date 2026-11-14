#!/bin/bash
# Phase 3 R2 proof, stage C (controller): apply the release steps on the prod copy with the final build (046908f),
# then new-dist reports at D, D-91 and default day, diffed against the pre-release old-dist baseline (pre-noprices-*/old).
set -u
P=$(cat ~/.hermes/profiles/raymond/workspace/orion/phase3-proof/r2/copy-dir.txt); S=$(cat $P/schema)
NEW=/home/hermes/git/orion/.worktrees/proof-046908f
OLD=/home/hermes/git/orion/.worktrees/rel-2026.11.12.1/orion-2026.11.12.1
OUT=~/.hermes/profiles/raymond/workspace/orion/phase3-proof/r2/C; mkdir -p $OUT
U="postgresql://orion_dev@/orion_dev?host=/var/run/postgresql"
pg_dump "$U" -n $S -Fc -f $P/schema-before-C.dump; echo "dump $? $(du -h $P/schema-before-C.dump | cut -f1)"
cd $NEW
o() { ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node dist/cli/index.js "$@"; }
A="aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv"
for a in $A; do o data reprice $a --yes --json > $OUT/reprice-$a.json 2>$OUT/reprice-$a.err; echo "reprice $a $?"; done
for a in $A; do o data reprice $a --json > $OUT/reprice-again-$a.json 2>/dev/null; echo "reprice-again $a $?"; done
for a in $A; do o data rebuild-price-levels $a --yes --json > $OUT/levels-$a.json 2>$OUT/levels-$a.err; echo "levels $a $?"; done
o data purge-prices --source coingecko --json > $OUT/purge-prices-dry.json 2>&1; echo "purge-prices-dry $?"
o data purge-prices --source coingecko --yes --json > $OUT/purge-prices.json 2>&1; echo "purge-prices $?"
for a in $A; do
  for m in price_usd diem_price_usd; do
    o data purge $a --metric $m --source-type market_data --json > $OUT/purge-md-dry-$a-$m.json 2>&1; r=$?
    [ $r -eq 0 ] || { echo "purge-md-dry $a $m $r"; continue; }
    o data purge $a --metric $m --source-type market_data --yes --json > $OUT/purge-md-$a-$m.json 2>&1; echo "purge-md $a $m $?"
  done
done
for D in 2026-11-13 2026-08-14; do
  mkdir -p $OUT/rep-$D
  for a in $A; do o report yield $a --day $D --json > $OUT/rep-$D/$a.json 2>/dev/null; done
done
mkdir -p $OUT/rep-default; for a in $A; do o report yield $a --json > $OUT/rep-default/$a.json 2>/dev/null; done
mkdir -p $OUT/rep-old-default; for a in $A; do ORION_HOME=$P/old ORION_ENV_FILE=$P/old/.env node $OLD/dist/cli/index.js report yield $a --json > $OUT/rep-old-default/$a.json 2>/dev/null; done
echo done-C
