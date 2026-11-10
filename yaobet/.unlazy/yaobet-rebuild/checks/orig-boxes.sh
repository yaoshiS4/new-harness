#!/usr/bin/env bash
# Measure the shell boxes on the runnable original app copy with the rebuild's box-check (PR-43 evidence).
# Usage: ORIG_APP=<dir with the original app and node_modules> [PORT=3163] bash orig-boxes.sh
# Starts `next dev` in ORIG_APP, waits up to 120 s for an HTTP answer, runs box-check, stops the server.
set -u
ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)" || exit 2
O="${ORIG_APP:?ORIG_APP must point at the runnable original app copy}"
P="${PORT:-3163}"; LOG="/tmp/yb-orig-$P.log"
lsof -ti "tcp:$P" > /dev/null 2>&1 && { echo "Fail: orig-boxes | Expected: port $P free | Got: busy"; exit 1; }
(cd "$O" && exec npx next dev -p "$P") > "$LOG" 2>&1 &
stop() { lsof -ti "tcp:$P" | xargs kill 2> /dev/null; kill "$!" 2> /dev/null; }
up=0
for _ in $(seq 1 120); do
  curl -s -o /dev/null "http://localhost:$P/" && { up=1; break; }
  sleep 1
done
[ $up -eq 1 ] || { stop; echo "Fail: orig-boxes | Expected: original answers on $P | Got: no answer (see $LOG)"; exit 1; }
BASE="http://localhost:$P" node "$ROOT/scripts/box-check.mjs" --boxes "$ROOT/.unlazy/yaobet-rebuild/checks/boxes.json"; rc=$?
stop
exit $rc
