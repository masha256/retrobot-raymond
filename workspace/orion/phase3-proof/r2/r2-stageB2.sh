#!/bin/bash
# Phase 3 R2 proof, stage B (controller), dry runs only: compare-usd, reprice dry run, rebuild-price-levels dry run, per asset.
set -u
P=$(cat ~/.hermes/profiles/raymond/workspace/orion/phase3-proof/r2/copy-dir.txt)
NEW=/home/hermes/git/orion/.worktrees/proof-63c0fe4
OUT=~/.hermes/profiles/raymond/workspace/orion/phase3-proof/r2/B2
mkdir -p $OUT
cd $NEW
o() { ORION_HOME=$P/new ORION_ENV_FILE=$P/new/.env node dist/cli/index.js "$@"; }
for a in aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv; do
  o data compare-usd $a --days 400 --json > $OUT/compare-$a.json 2>$OUT/compare-$a.err; echo "compare $a $?"
  o data reprice $a --json > $OUT/reprice-dry-$a.json 2>$OUT/reprice-dry-$a.err; echo "reprice-dry $a $?"
  o data rebuild-price-levels $a --json > $OUT/levels-dry-$a.json 2>$OUT/levels-dry-$a.err; echo "levels-dry $a $?"
done
o data purge-prices --source coingecko --json > $OUT/purge-prices-dry.json 2>$OUT/purge-prices-dry.err; echo "purge-prices-dry $?"
echo done-B
