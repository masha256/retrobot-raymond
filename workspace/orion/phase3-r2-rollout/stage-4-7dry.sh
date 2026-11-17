#!/bin/bash
# R2 release block steps 4-8 DRY RUNS on stage (no --yes here). Prints STOP lines; exits 1 on the first stop.
set -u
E=stage; K=~/.ssh/orion-stage_ed25519
S() { ssh -i $K -o IdentitiesOnly=yes orion-stage@192.168.0.12 "$@"; }
A="aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv"
R=~/r2-$E
day() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["day"])' $R/before/$1.json; }
d91() { python3 -c 'import datetime,sys; print(datetime.date.fromisoformat(sys.argv[1]) - datetime.timedelta(days=91))' "$(day $1)"; }
stop=0
echo "== step 4 mid $(date -u +%FT%TZ)"
for a in $A; do
  S report yield $a --day $(day $a) > $R/mid/$a.json || { echo "STOP: $a exit $?"; stop=1; }
  S report yield $a --day $(d91 $a) > $R/mid/$a-91.json || { echo "STOP: $a-91 exit $?"; stop=1; }
done
echo "== step 5 compare-usd $(date -u +%FT%TZ)"
for a in $A; do S data compare-usd $a --days 400 > $R/dry/compare-usd-$a.json || { echo "STOP: compare-usd $a exit $?"; stop=1; }; done
for a in $A; do python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); bad=[m["metric"] for m in r if m["unpriced"]>0]; print(sys.argv[2], "STOP: unpriced in "+",".join(bad) if bad else "ok", " | ".join("%s gap=%s p50=%s p90=%s" % (m["metric"], m.get("gapPct"), m.get("p50DayGapPct"), m.get("p90DayGapPct")) for m in r))' $R/dry/compare-usd-$a.json $a; done | tee $R/dry/step5.txt
grep -q STOP $R/dry/step5.txt && stop=1
echo "== step 6 reprice dry $(date -u +%FT%TZ)"
for a in $A; do
  S data reprice $a > $R/dry/reprice-$a.json; rc=$?
  [ $rc -eq 0 ] || { echo "STOP: $a reprice dry run exit $rc"; stop=1; }
done
echo "== step 7 pre-check $(date -u +%FT%TZ)"
echo "(stage has no sql-ro; R39 pre-check needs Mike's sudo -iu orion-stage o db query-ro, or is covered by the 8b purge refusal)"
for a in $A; do
  S data rebuild-price-levels $a > $R/dry/rebuild-$a.json; rc=$?
  [ $rc -eq 0 ] || { echo "STOP: $a rebuild dry run exit $rc"; stop=1; }
done
for a in $A; do python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); a=sys.argv[2]; pm=r["perMetric"]; bad=[m["metric"] for m in pm if m["refused"]]; bvf=sum(len(m["beforeValidFrom"]) for m in pm); want=25 if a=="aero" else 0; s="STOP: refused in "+",".join(bad) if bad else ("STOP: beforeValidFrom %d, expected %d" % (bvf, want) if bvf != want else "ok"); print(a, " ".join("%s rows=%d rebuild=%d refused=%d beforeValidFrom=%d" % (m["metric"], m["rows"], m["rebuilt"], len(m["refused"]), len(m["beforeValidFrom"])) for m in pm), s)' $R/dry/rebuild-$a.json $a; done | tee $R/dry/step7.txt
grep -q STOP $R/dry/step7.txt && stop=1
echo "stop=$stop"
exit $stop
