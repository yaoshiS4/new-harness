#!/usr/bin/env bash
# KF1: ui-slide-up is a global keyframe (the original Sheet declares slideUp outside any @media;
# Modal's only reference sits inside the same max-width 639px query, so global scope serves both).
# PM-authored; builders never edit it.
set -u
cd "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)" || exit 2
F=src/styles/keyframes.css
ok=0; n=0; fail() { echo "Fail: $1 | Expected: $2 | Got: $3"; }
# 1. ui-slide-up declared exactly once, at brace depth 0.
n=$((n+1))
d=$(awk '{ s=$0; while (length(s)) { c=substr(s,1,1); if (index(s,"@keyframes ui-slide-up")==1) { print depth; } if (c=="{") depth++; else if (c=="}") depth--; s=substr(s,2) } }' "$F" | tr '\n' ' ')
[ "$d" = "0 " ] && ok=$((ok+1)) || fail KF1-slide-up-global "depth 0, declared once" "depths: ${d:-none}"
# 2. body unchanged: translateY(100%) -> translateY(0).
n=$((n+1))
b=$(awk '/@keyframes ui-slide-up/{f=1} f{print} f&&/^}/{exit}' "$F" | tr -d ' \n')
case "$b" in *'from{transform:translateY(100%);}to{transform:translateY(0);}'*) ok=$((ok+1));; *) fail KF1-slide-up-body "from translateY(100%) to translateY(0)" "$b";; esac
# 3. no @media block left that wraps nothing but the old slide-up.
n=$((n+1))
if awk '/@media \(max-width: 639px\)/{getline nx; if (nx ~ /@keyframes/) bad=1} END{exit bad?0:1}' "$F"; then fail KF1-no-media-keyframes "no keyframe nested in @media" "one found"; else ok=$((ok+1)); fi
# 4. still 7 ui-* keyframes, each name once.
n=$((n+1))
c=$(rg -c '@keyframes ui-' "$F"); u=$(rg -o '@keyframes ui-[a-z-]+' "$F" | sort -u | wc -l | tr -d ' ')
[ "$c" = 7 ] && [ "$u" = 7 ] && ok=$((ok+1)) || fail KF1-count "7 unique" "count=$c unique=$u"
[ $ok -eq $n ] && echo "CHECKS OK KF1 $ok/$n" || { echo "CHECKS FAILED KF1 $ok/$n"; exit 1; }
