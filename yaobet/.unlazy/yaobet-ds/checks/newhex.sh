#!/usr/bin/env bash
# No new colour value (D-DS2, D-DS5): every colour (hex, rgb, hsl, normalised to RGBA) on a
# line added since 635a4dc in src/styles/{tokens,themes,brands}.css is in the union of
# design-tokens.all.json, overlay.proposal.json and the 635a4dc versions of those files.
LEAF=newhex; PORT=0
. "$(dirname "${BASH_SOURCE[0]}")/ds.sh"

need newhex-defs "${DEFS[@]}" || finish
helper newhex

finish
