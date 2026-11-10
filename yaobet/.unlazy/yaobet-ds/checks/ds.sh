#!/usr/bin/env bash
# Shared header for the Wine-Gold shell checks. Set LEAF before sourcing.
# Target tree: the git top level of the cwd (its src/ and built .next/static).
# Doc inputs (allow lists, pins, the CSS helper): this checks directory and its repo.
set -o pipefail
DS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DS_ROOT="$(git -C "$DS_DIR" rev-parse --show-toplevel)" || { echo "Fail: setup | Expected: $DS_DIR inside a git repo | Got: none"; exit 2; }
CHECK_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || CHECK_ROOT="$PWD"
export CHECK_ROOT DS_DIR DS_ROOT
. "$DS_ROOT/.unlazy/yaobet-rebuild/checks/lib.sh"
DEFS=(src/styles/tokens.css src/styles/themes.css src/styles/brands.css)
BASE_REF=635a4dc

is_def() { local d; for d in "${DEFS[@]}"; do [ "$1" = "$d" ] && return 0; done; return 1; }
# Run the CSS helper and fold its "OK <id>" / "Fail: ..." lines into the lib.sh counters.
helper() {
  local out rc l nok=0 nfail=0
  out="$TMPD/helper-$1.out"
  node "$DS_DIR/css-lib.mjs" "$@" > "$out" 2>&1; rc=$?
  while IFS= read -r l; do
    case "$l" in
      "OK "*) ok; nok=$((nok + 1)) ;;
      "Fail: "*) printf '%s\n' "$l"; N_FAIL=$((N_FAIL + 1)); nfail=$((nfail + 1)) ;;
      *) printf '%s\n' "$l" ;;
    esac
  done < "$out"
  # A crash (exit != 0 with no Fail line) or a silent run (exit 0 with no OK line) never passes.
  if [ "$rc" -ne 0 ] && [ "$nfail" -eq 0 ]; then fail "helper-$1" "css-lib.mjs $1 ran" "exit $rc, no Fail line"; fi
  if [ "$rc" -eq 0 ] && [ "$nok" -eq 0 ]; then fail "helper-$1" "at least one OK line from css-lib.mjs $1" "exit 0, no OK line"; fi
  if [ "$rc" -eq 0 ] && [ "$nfail" -gt 0 ]; then fail "helper-$1" "a non-zero exit with Fail lines" "exit 0"; fi
  [ "$rc" -le 1 ] || fail "helper-$1" "css-lib.mjs $1 exit 0 or 1" "exit $rc"
}
