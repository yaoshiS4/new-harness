#!/usr/bin/env bash
# Lease gate: every path the branch adds, changes, deletes or leaves untracked is inside checks/owns/<leaf>.txt.
# Entries are exact paths or dir/** prefixes (genplan.py asserts this form). Generated; do not edit.
set -u
LEAF=${1:?leaf id}; DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; OWNS="$DIR/owns/$LEAF.txt"
cd "$(git -C "$DIR" rev-parse --show-toplevel)" || exit 2
base=$(git merge-base "${LEASE_BASE:-main}" HEAD) || { echo "Fail: lease-$LEAF | Expected: a merge-base with ${LEASE_BASE:-main} | Got: none"; exit 1; }
paths=$( { git diff --name-only "$base" HEAD; git diff --name-only HEAD; git ls-files --others --exclude-standard; } | LC_ALL=C sort -u)
bad=0; n=0
while IFS= read -r p; do
  [ -z "$p" ] && continue; n=$((n + 1)); hit=0
  while IFS= read -r o; do
    [ -z "$o" ] && continue
    case "$o" in */\*\*) pre="${o%/\*\*}"; [ "${p#"$pre"/}" != "$p" ] && hit=1 ;; *) [ "$p" = "$o" ] && hit=1 ;; esac
  done < "$OWNS"
  [ $hit -eq 1 ] || { echo "Fail: lease-$LEAF | Expected: $p inside OWNS | Got: outside"; bad=$((bad + 1)); }
done <<< "$paths"
[ $bad -eq 0 ] || { echo "LEASE FAILED $LEAF $bad/$n"; exit 1; }
echo "LEASE OK $LEAF $n paths"
