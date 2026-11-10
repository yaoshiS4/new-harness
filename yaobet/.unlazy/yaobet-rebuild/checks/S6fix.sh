#!/usr/bin/env bash
# Hot-fix S6fix: sports lifestyle cards take the Card base (PR-44); the S6 acceptance checks still hold.
set -u -o pipefail
bash "$(dirname "${BASH_SOURCE[0]}")/S6.sh" || { echo "S6fix FAIL S6"; exit 1; }
echo "S6fix OK"
