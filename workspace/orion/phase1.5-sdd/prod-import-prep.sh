#!/bin/bash
# Prod cutover data prep (docs/ops/deploy.md "Prod's one-time initial load"), controller-run. Writes nothing on venus.
# Final SQLite snapshot -> orion_dev scratch import + proof -> reference reports -> pg_dump. The upload is separate.
set -euo pipefail
WT=/home/hermes/git/orion/.worktrees/daemon
CLI="node $WT/dist/cli/index.js"
U='postgresql://orion_dev@/orion_dev?host=/var/run/postgresql'
D=$(date -u -d yesterday +%F)
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
P=/home/hermes/git/orion/.worktrees/prod-import-$STAMP; mkdir -m 700 "$P"
echo "P=$P D=$D"
if pgrep -af 'dist/cli/index.js|run-daily' | grep -v pgrep | grep -v tirith | grep -v "$WT"; then echo "live tick running: stop"; exit 1; fi
# Final SQLite: one online backup, kept twice (import source + the archived final copy).
sqlite3 /home/hermes/git/orion/orion.db ".backup '$P/snap.db'"; sqlite3 "$P/snap.db" 'PRAGMA integrity_check'
mkdir -p /home/hermes/git/orion/backups
cp "$P/snap.db" "/home/hermes/git/orion/backups/orion-final-$STAMP.db"; chmod 400 "/home/hermes/git/orion/backups/orion-final-$STAMP.db"
for t in observations fetch_runs anomalies agent_runs proposals journal documents; do printf '%s=%s ' "$t" "$(sqlite3 "$P/snap.db" "select count(*) from $t")"; done; echo
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
echo "$P" > /home/hermes/.hermes/profiles/raymond/workspace/orion/phase1.5-sdd/prod-import-dir.txt
