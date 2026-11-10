#!/usr/bin/env bash
# No raw hex and no numeric rgb()/rgba()/hsl()/hsla() literal in src/ outside the three
# token definition files, comments included; hex-allow.txt rows carry the exact hit count.
# Usage: hex.sh [files or dirs]   (default: src)
LEAF=hex; PORT=0
. "$(dirname "${BASH_SOURCE[0]}")/ds.sh"

HEX='(?<!&)#[0-9a-fA-F]{3,8}(?![0-9A-Za-z_-])'
FN='\b(?:rgba?|hsla?)\(\s*[-+]?\.?[0-9]'
ALLOW="$DS_DIR/hex-allow.txt"
need hex-allow "$ALLOW" || finish
[ "$#" -gt 0 ] && SCOPE_ARGS=("$@") || SCOPE_ARGS=(src)
need hex-scope "${SCOPE_ARGS[@]}" || finish

# Every file in scope, minus the definition files.
rg --files -- "${SCOPE_ARGS[@]}" | LC_ALL=C sort -u > "$TMPD/files"; rc=$?
[ "$rc" -eq 0 ] || fail hex-files "rg --files exit 0" "exit $rc"
: > "$TMPD/scope"
while IFS= read -r f; do is_def "$f" || printf '%s\n' "$f" >> "$TMPD/scope"; done < "$TMPD/files"
ok

# Hits per file (each pattern match counts once, not each line).
: > "$TMPD/hits"
while IFS= read -r f; do
  rg -o --pcre2 -N -e "$HEX" -e "$FN" -- "$f" > "$TMPD/match"; rc=$?
  [ "$rc" -le 1 ] || { fail "hex-scan $f" "rg exit 0 or 1" "exit $rc"; continue; }
  n=$(wc -l < "$TMPD/match" | tr -d ' ')
  [ "$n" -gt 0 ] && printf '%s\t%s\n' "$f" "$n" >> "$TMPD/hits"
done < "$TMPD/scope"

allowed_count() { awk -F'\t' -v f="$1" '$0 !~ /^(#|$)/ && $1 == f { print $3; exit }' "$ALLOW"; }
in_scope() { awk -v f="$1" '$0 == f { found = 1 } END { exit !found }' "$TMPD/scope"; }

while IFS=$(printf '\t') read -r f n; do
  want=$(allowed_count "$f")
  if [ -z "$want" ]; then
    fail "hex $f" "0 hex/rgb/hsl literals (no hex-allow.txt row)" "$n: $(rg -n -o --pcre2 -m 3 -e "$HEX" -e "$FN" -- "$f" | head -n 3 | tr '\n' ' ')"
  else
    eq "hex $f" "$want" "$n"
  fi
done < "$TMPD/hits"

# Allow rows in scope whose file has no hit at all still fail on their count.
while IFS=$(printf '\t') read -r f label want; do
  case "$f" in ""|"#"*) continue ;; esac
  [ -n "$label" ] && [ -n "$want" ] || { fail "hex-allow-row $f" "path<TAB>label<TAB>count" "malformed"; continue; }
  in_scope "$f" || continue
  awk -F'\t' -v f="$f" '$1 == f { found = 1 } END { exit !found }' "$TMPD/hits" || eq "hex $f" "$want" 0
done < "$ALLOW"

# themeColor equals the built page token and the DS page primitive.
if in_scope src/app/layout.tsx; then
  tc=$(rg -o -N -m 1 'themeColor:\s*"[^"]*"' src/app/layout.tsx | sed -E 's/.*"([^"]*)"/\1/')
  nonempty hex-themecolor "$tc"
  [ -n "$tc" ] && helper themecolor "$tc"
fi

# The D-DS13 hsl() lines of the card art stay byte-unchanged since BASE_REF.
ART=(src/components/collection/CardArt.tsx src/components/collection/PackStage.tsx)
art_in=0; for f in "${ART[@]}"; do in_scope "$f" && art_in=1; done
if [ "$art_in" -eq 1 ]; then
  git diff "$BASE_REF" -- "${ART[@]}" > "$TMPD/art.diff"; grc=$?
  if [ "$grc" -ne 0 ]; then
    fail hex-hsl-diff "git diff $BASE_REF exit 0" "exit $grc"
  else
    D=$(rg -c '^[-+][^-+].*hsl\(' "$TMPD/art.diff"); rc=$?
    if [ "$rc" = 1 ] && [ -z "$D" ]; then ok; else fail hex-hsl-same "no changed hsl( line since $BASE_REF (rg exit 1)" "rg exit $rc, ${D:-0} lines"; fi
  fi
fi

finish
