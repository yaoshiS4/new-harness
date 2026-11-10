#!/usr/bin/env bash
# Fonts (D-DS3, D-DS8): the built CSS has the U+1EA0-1EF9 @font-face slice at 400/500/600 for
# Be Vietnam Pro, Playfair Display and Inter, none of the three at 700 or 800, Montserrat
# still present; layout.tsx loads Playfair_Display and Inter with the vietnamese subset.
# Family names match case-insensitively; next/font emits `font-family:<Name>` (quoted or not).
LEAF=fonts; PORT=0
. "$(dirname "${BASH_SOURCE[0]}")/ds.sh"

need fonts-build .next/BUILD_ID .next/static src/app/layout.tsx || finish
# One line per @font-face: family<TAB>weight-low<TAB>weight-high<TAB>vietnamese-slice(0|1)
rg -o -N --no-filename --no-ignore --hidden -g '*.css' '@font-face\{[^}]*\}' .next/static > "$TMPD/faces"; rc=$?
[ "$rc" -le 1 ] || fail fonts-scan "rg exit 0 or 1" "exit $rc"
awk '{
  fam = $0; sub(/.*font-family:[ ]*/, "", fam); sub(/;.*|}.*/, "", fam); gsub(/["\047]/, "", fam); fam = tolower(fam)
  w = $0; lo = 400; hi = 400
  if (w ~ /font-weight:/) { sub(/.*font-weight:[ ]*/, "", w); sub(/;.*|}.*/, "", w); n = split(w, a, " "); lo = a[1] + 0; hi = (n > 1 ? a[2] : a[1]) + 0 }
  vi = ($0 ~ /U\+1EA0-1EF9/) ? 1 : 0
  printf "%s\t%d\t%d\t%d\n", fam, lo, hi, vi
}' "$TMPD/faces" > "$TMPD/table"
nonempty fonts-faces "$(head -n 1 "$TMPD/table")"

has_face() { awk -F'\t' -v f="$1" -v w="$2" -v v="$3" '$1 == f && $2 <= w && $3 >= w && (v == "" || $4 == v) { found = 1 } END { exit !found }' "$TMPD/table"; }
for fam in "be vietnam pro" "playfair display" "inter"; do
  for w in 400 500 600; do
    if has_face "$fam" "$w" 1; then ok; else fail "fonts-$fam-$w" "@font-face $fam $w with U+1EA0-1EF9" absent; fi
  done
  for w in 700 800; do
    if has_face "$fam" "$w" ""; then fail "fonts-$fam-no-$w" "no $fam face at $w" present; else ok; fi
  done
done
if has_face montserrat 700 "" || has_face montserrat 800 ""; then ok; else fail fonts-montserrat "a Montserrat @font-face (emerald)" absent; fi

# layout.tsx: next/font/local only, with a Playfair Display and an Inter call that carry the vietnamese range.
if rg -q '^import localFont from "next/font/local";$' src/app/layout.tsx; then ok; else fail fonts-import-local 'import localFont from "next/font/local"' absent; fi
if rg -q 'next/font/google' src/app/layout.tsx; then fail fonts-import-google "no next/font/google import" present; else ok; fi
for fam in "Playfair Display" Inter; do
  n=$(FAM="$fam" perl -0777 -ne 'my $n = 0; for (split /\blocalFont\(/) { $n++ if /value:\s*"\x27\Q$ENV{FAM}\E\x27"/ && /U\+1EA0-1EF9/ } print $n' src/app/layout.tsx)
  if [ "${n:-0}" -ge 1 ]; then ok; else fail "fonts-subset-${fam// /_}" "a localFont call for '$fam' with U+1EA0-1EF9" "${n:-0} calls"; fi
done

finish
