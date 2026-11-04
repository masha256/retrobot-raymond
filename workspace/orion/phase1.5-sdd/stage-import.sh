#!/bin/bash
# First staging data load (docs/ops/deploy.md "First staging deploy" step 2), controller-run.
set -euo pipefail
WT=/home/hermes/git/orion/.worktrees/daemon
CLI="node $WT/dist/cli/index.js"
ST="ssh -i $HOME/.ssh/orion-stage_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes orion-stage@192.168.0.12"
U='postgresql://orion_dev@/orion_dev?host=/var/run/postgresql'
D=$(date -u -d yesterday +%F)
P=/home/hermes/git/orion/.worktrees/stage-import-$(date -u +%Y%m%dT%H%M%SZ); mkdir -m 700 "$P"
echo "P=$P D=$D"
if pgrep -af 'dist/cli/index.js|run-daily' | grep -v pgrep | grep -v tirith | grep -v "$WT"; then echo "live tick running: stop"; exit 1; fi
sqlite3 /home/hermes/git/orion/orion.db ".backup '$P/snap.db'"; sqlite3 "$P/snap.db" 'PRAGMA integrity_check'
n=$(psql -X -U orion_dev -d orion_dev -Atc "select count(*) from pg_namespace where nspname='orion'"); [ "$n" = 0 ] || { echo "orion schema exists in orion_dev: stop"; exit 1; }
mkdir -m 700 "$P/new" "$P/ref"; cp -r $WT/assets $WT/personas $WT/skills "$P/new/"
printf 'ORION_DATABASE_URL=%s\n' "$U" > "$P/new/.env"; chmod 600 "$P/new/.env"
ORION_HOME="$P/new" $CLI db migrate --json | head -c 300; echo
cd $WT
ORION_HOME="$P/new" npx tsx tools/import-sqlite/cli.ts import --from "$P/snap.db" --to "$U" --schema orion --assets $WT/assets --manifest-dir "$P" > "$P/import.out"
M=$(ls "$P"/import-*.json)
python3 - "$M" <<'EOF'
import json,sys; m=json.load(open(sys.argv[1]))
ex=[(t['table'],e['reason'],e['count']) for t in m['tables'] for e in t['excluded']]
print('excluded', ex); print('carried', {t['table']:t['carried'] for t in m['tables']})
ok={('observations','undeclared_metric'),('agent_transcripts','non_disclosure_transcript'),('proposals','retired_kind')}
bad=[x for x in ex if (x[0],x[1]) not in ok]
print('EXCLUSIONS_OK' if not bad else f'EXCLUSIONS_BAD {bad}')
EOF
npx tsx tools/import-sqlite/cli.ts proof --from "$P/snap.db" --to "$U" --schema orion --assets $WT/assets --manifest "$M" > "$P/proof.json" && echo PROOF_OK || { echo PROOF_FAILED; exit 1; }
for a in aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv; do ORION_HOME="$P/new" $CLI report yield $a --day "$D" --json > "$P/ref/$a.json"; done
ORION_HOME="$P/new" $CLI data anomalies --all --json > "$P/ref/anomalies.json"
ORION_HOME="$P/new" $CLI proposals list --all --json > "$P/ref/proposals.json" 2>/dev/null || ORION_HOME="$P/new" $CLI proposals list --json > "$P/ref/proposals.json"
/usr/lib/postgresql/18/bin/pg_dump -Fc -n orion -f "$P/latest.dump" "$U"
S=$(sha256sum "$P/latest.dump" | cut -d' ' -f1); ls -l "$P/latest.dump"; echo "sha $S"
$ST refresh-staging --stdin "$S" < "$P/latest.dump" > "$P/refresh.out" 2>&1; echo "refresh rc=$?"; tail -c 1500 "$P/refresh.out"; echo
same=0
for a in aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv; do
  if $ST report yield $a --day "$D" --json 2>/dev/null | cmp -s - "$P/ref/$a.json"; then same=$((same+1)); else echo "DIFF $a"; $ST report yield $a --day "$D" --json 2>&1 | head -c 300; echo; fi
done
echo "reports identical: $same/13"
echo "$P" > /home/hermes/.hermes/profiles/raymond/workspace/orion/phase1.5-sdd/stage-import-dir.txt
