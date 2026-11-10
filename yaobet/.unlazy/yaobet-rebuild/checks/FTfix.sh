#!/usr/bin/env bash
# Hot-fix FTfix: the original eslint-disable line in useFocusTrap is ported verbatim (PR-42).
set -u -o pipefail
O=/Users/maxime/Documents/Projects/Antigravity/Igaming-Agent-1/apps/web/src
F=src/components/layout/_internal/useFocusTrap.ts
r=$(rg -c 'eslint-disable' src | awk -F: '{s+=$2} END{print s+0}')
o=$(rg -c 'eslint-disable' "$O" | awk -F: '{s+=$2} END{print s+0}')
echo "census rebuild=$r original=$o"
[ "$r" = "$o" ] || { echo "FTfix FAIL census"; exit 1; }
diff <(rg -n -B1 -A1 'eslint-disable' "$O/components/layout/_internal/useFocusTrap.ts" | sed 's/^[0-9]*[:-]//') <(rg -n -B1 -A1 'eslint-disable' "$F" | sed 's/^[0-9]*[:-]//') || { echo "FTfix FAIL context"; exit 1; }
echo "FTfix OK"
