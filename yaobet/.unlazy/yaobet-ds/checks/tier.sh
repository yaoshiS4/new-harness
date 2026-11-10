#!/usr/bin/env bash
# Tier rule (TOKENS.md:14, ADR-003 §3.3): only the three definition files read --wg-*;
# every --wg-* value is a literal or a next/font --font-* loader var; --wg-* is declared
# only in the :root of tokens.css; the ADR-003 §3.4 component names never read --wg-*.
# Usage: tier.sh [files or dirs]   (default: src; the declaration rules always scan src)
LEAF=tier; PORT=0
. "$(dirname "${BASH_SOURCE[0]}")/ds.sh"

[ "$#" -gt 0 ] && SCOPE_ARGS=("$@") || SCOPE_ARGS=(src)
need tier-scope "${SCOPE_ARGS[@]}" || finish
READS='var\(\s*--wg-|\(--wg-'
rg -l -e "$READS" -- "${SCOPE_ARGS[@]}" > "$TMPD/readers"; rc=$?
[ "$rc" -le 1 ] || fail tier-scan "rg exit 0 or 1" "exit $rc"
bad=0
while IFS= read -r f; do
  is_def "$f" && continue
  fail "tier-reader $f" "no var(--wg-*) outside ${DEFS[*]}" "$(rg -n -m 3 -e "$READS" -- "$f" | head -n 3 | tr '\n' ' ')"
  bad=1
done < "$TMPD/readers"
[ "$bad" -eq 0 ] && ok
helper tier

finish
