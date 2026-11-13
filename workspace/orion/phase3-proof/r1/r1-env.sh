#!/bin/bash
# Phase 3 R1 release block helper (controller). Usage: r1-env.sh <env> <step: before|check|mid|purged>
set -u
ENV=$1; STEP=$2
KEY=$HOME/.ssh/orion-${ENV}_ed25519
S() { ssh -i $KEY -o IdentitiesOnly=yes orion-${ENV}@192.168.0.12 "$@"; }
W=$HOME/r1-$ENV; mkdir -p $W/before $W/after $W/mid $W/purged
T=/home/hermes/git/orion/.worktrees/phase3/tools/phase3-proof
day() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["day"])' "$1"; }
ALL="aero cake crv cvxcrv hype link lit pump sdcrv sky uni vvv ycrv"
case $STEP in
  before)
    for a in $ALL; do S report yield $a > $W/before/$a.json || echo "STOP: $a exit $?"; echo "$a $(day $W/before/$a.json)"; done ;;
  check)
    rc=0
    for a in $ALL; do
      d=$(day $W/before/$a.json); S report yield $a --day $d > $W/after/$a.json
      if [ $a = aero ]; then cmp -s $W/before/aero.json $W/after/aero.json && echo "aero cmp identical" || { echo "STOP: aero differs"; rc=1; }
      else python3 $T/flatdiff.py $W/before/$a.json $W/after/$a.json --allow $T/r1-allowlist.json --asset $a > $W/after/$a.flatdiff 2>&1; e=$?; echo "$a exit $e $(tail -1 $W/after/$a.flatdiff)"; [ $e = 0 ] || rc=1; fi
    done; echo "check rc=$rc" ;;
  mid|purged)
    for a in $ALL; do d=$(day $W/before/$a.json); S report yield $a --day $d > $W/$STEP/$a.json || echo "STOP: $a exit $?"; done
    if [ $STEP = purged ]; then for a in $ALL; do cmp -s $W/mid/$a.json $W/purged/$a.json && echo "$a identical" || echo "STOP: $a differs from mid/"; done; fi ;;
esac
