#!/usr/bin/env bash
set -euo pipefail

KEY="${STITCH_API_KEY:-${GEMINI_API_KEY:-}}"

if [ -z "$KEY" ] && [ -r "$HOME/.gemini/.stitch_key" ]; then
  KEY="$(cat "$HOME/.gemini/.stitch_key" | tr -d '\r\n[:space:]')"
fi

if [ -z "$KEY" ]; then
  echo "Error: STITCH_API_KEY or GEMINI_API_KEY is not set and ~/.gemini/.stitch_key is missing." >&2
  exit 1
fi

exec npx -y mcp-remote https://stitch.googleapis.com/mcp --header "X-Goog-Api-Key: $KEY"
