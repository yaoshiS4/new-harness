#!/usr/bin/env bash
# Fetch each URL in <dir>/urls from $BASE (exported by scripts/with-dev-server.mjs). Generated; do not edit.
set -u
D=$1; B="${BASE:?with-dev-server must export BASE}"; i=0
while IFS= read -r u; do
  i=$((i + 1))
  curl -s -o "$D/$i.html" -w '%{http_code} %{redirect_url}' --max-time 180 "$B$u" > "$D/$i.meta" 2>/dev/null || echo "000 " > "$D/$i.meta"
done < "$D/urls"
