#!/usr/bin/env bash
# HF5 gate hot-fix: the I1 member-menu link and identity box expectations follow the original (PR-43).
set -u
cd "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)" || exit 2
U=.unlazy/yaobet-rebuild; I1="$U/checks/I1.sh"; GP="$U/genplan.py"; BX="$U/checks/boxes.json"
pass=0; fail=0; n=0
ok()  { n=$((n + 1)); pass=$((pass + 1)); }
bad() { n=$((n + 1)); fail=$((fail + 1)); echo "Fail: HF5 $1"; }
has()   { rg -q -F -- "$2" "$3" && ok || bad "$1 | Expected: '$2' in $3 | Got: absent"; }
lacks() { rg -q -F -- "$2" "$3" && bad "$1 | Expected: no '$2' in $3 | Got: present" || ok; }

# member menu link: closed-state HTML lacks it, as in the original
has   i1-menu-closed "nohtml I1-S2-member-menu-closed / 'href=\"/cau-lac-bo\"'" "$I1"
lacks i1-no-ssr13  "html I1-S2-ssr-13 " "$I1"
has   gp-menu-closed "I1-S2-member-menu-closed" "$GP"
for k in 1 2 3 4 5 6 7 8 9 10 11 12; do has "i1-ssr-$k" "html I1-S2-ssr-$k /" "$I1"; done
has   i1-dai-ly "html I1-S2-ssr-12 / 'href=\"/dai-ly\"'" "$I1"

# identity box: the div.identity cluster right after the utility list
sel=$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["boxes"]["identity"]["selector"])' "$BX") || sel="(unreadable)"
[ "$sel" = 'header ul[aria-label="Tiện ích"] + div' ] && ok || bad "boxes-identity | Expected: header ul[aria-label=\"Tiện ích\"] + div | Got: $sel"
has gp-identity-sel 'header ul[aria-label=\"Tiện ích\"] + div' "$GP"
lacks gp-assumption '"components/layout/Header.tsx:112 (assumption)"' "$GP"
python3 -I -c 'import json,sys; b=json.load(open(sys.argv[1], encoding="utf-8"))["boxes"]; assert set(b) == {"header","logo","identity","main","rightRail","quickActionRail","bottomTabBar","footerHeight"}' "$BX" && ok || bad "boxes-keys | Expected: the 8 box names unchanged | Got: differ"

# syntax
bash -n "$I1" && ok || bad "i1-syntax | Expected: bash -n rc 0 | Got: error"
python3 -I -c 'import ast,sys; ast.parse(open(sys.argv[1], encoding="utf-8").read())' "$GP" && ok || bad "gp-syntax | Expected: parses | Got: error"

[ $fail -eq 0 ] && { echo "CHECKS OK HF5 $pass/$n"; exit 0; }
echo "CHECKS FAILED HF5 $fail/$n"; exit 1
