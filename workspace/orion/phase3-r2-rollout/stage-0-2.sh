#!/bin/bash
# R2 release block steps 0-2 on stage (deploy.md "Phase 3 R2 release")
set -u
E=stage; K=~/.ssh/orion-stage_ed25519
S() { ssh -i $K -o IdentitiesOnly=yes orion-stage@192.168.0.12 "$@"; }
A="aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv"
R=~/r2-$E; mkdir -p $R/before $R/mid $R/after $R/dry $R/yes
day() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["day"])' $R/before/$1.json; }
d91() { python3 -c 'import datetime,sys; print(datetime.date.fromisoformat(sys.argv[1]) - datetime.timedelta(days=91))' "$(day $1)"; }
echo "== step 0 $(date -u +%FT%TZ)"
for a in $A; do
  S report yield $a > $R/before/$a.json || { echo "STOP: $a exit $?"; exit 1; }
  S report yield $a --day $(d91 $a) > $R/before/$a-91.json || { echo "STOP: $a-91 exit $?"; exit 1; }
  echo "$a day=$(day $a) d91=$(d91 $a)"
done
echo "== step 1 $(date -u +%FT%TZ)"
cd /home/hermes/git/orion/.worktrees/phase3
scripts/release/deploy.sh stage orion-2026.11.15.1 > $R/deploy.log 2>&1; rc=$?
echo "deploy rc=$rc"; sed -n '/== deploy report/,$p' $R/deploy.log
[ $rc -eq 0 ] || exit 1
echo "== step 2 $(date -u +%FT%TZ)"
S status; S logs 30
