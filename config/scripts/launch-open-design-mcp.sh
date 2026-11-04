#!/usr/bin/env bash
# Auto-starting MCP wrapper for OpenDesign stdio proxy.
# Ensures the OpenDesign daemon is alive before running stdio MCP.

DAEMON_URL="${OD_DAEMON_URL:-http://127.0.0.1:7456}"
CLI_PATH="${OPEN_DESIGN_CLI_PATH:-$HOME/Projects/open-design/apps/daemon/dist/cli.js}"

if [ -f "$CLI_PATH" ]; then
  # Check if daemon is responding
  if ! curl -s -m 1 "$DAEMON_URL/health" >/dev/null 2>&1 && ! curl -s -m 1 "$DAEMON_URL" >/dev/null 2>&1; then
    # Auto-start daemon in background with --no-open
    nohup /usr/bin/node "$CLI_PATH" --no-open --port 7456 >/dev/null 2>&1 &
    # Wait briefly for daemon port to bind (max 3s)
    for _ in {1..15}; do
      if curl -s -m 1 "$DAEMON_URL" >/dev/null 2>&1; then
        break
      fi
      sleep 0.2
    done
  fi
  exec /usr/bin/node "$CLI_PATH" mcp --daemon-url "$DAEMON_URL" "$@"
else
  echo '{"jsonrpc":"2.0","error":{"code":-32603,"message":"OpenDesign CLI not found at '"$CLI_PATH"'"},"id":null}'
  exit 1
fi
