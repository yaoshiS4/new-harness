#!/usr/bin/env bash
# Google Fonts reachability for the Wine-Gold faces Playfair Display and Inter (the
# rebuild preflight covers Be Vietnam Pro and Montserrat). next build fails without it.
LEAF=fonts-preflight; PORT=0
. "$(dirname "${BASH_SOURCE[0]}")/ds.sh"

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
c1=$(curl -s -o "$TMPD/css" -m 20 -A "$UA" -w "%{http_code}" "https://fonts.googleapis.com/css2?family=Playfair+Display&family=Inter&display=swap")
eq fonts-css 200 "$c1"
u=$(rg -o -m 1 "https://fonts.gstatic.com/[^)]+\.woff2" "$TMPD/css" 2>/dev/null | head -n 1)
c2=$(curl -s -o /dev/null -m 20 -w "%{http_code}" "${u:-https://fonts.gstatic.com/}")
eq fonts-woff2 200 "$c2"
for fam in "Playfair Display" "Inter"; do
  if rg -q -F -- "font-family: '$fam'" "$TMPD/css"; then ok; else fail "fonts-family $fam" "an @font-face for $fam in the Google CSS" absent; fi
done

finish
