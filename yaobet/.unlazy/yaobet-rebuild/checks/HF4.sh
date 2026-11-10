#!/usr/bin/env bash
# HF4 gate hot-fix: the four redirect pages are a streamed client redirect (200 + meta refresh), as in the original.
set -u
cd "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)" || exit 2
U=.unlazy/yaobet-rebuild; VR=scripts/verify-routes.mjs
pass=0; fail=0; n=0
ok()  { n=$((n + 1)); pass=$((pass + 1)); }
bad() { n=$((n + 1)); fail=$((fail + 1)); echo "Fail: HF4 $1"; }
has()  { rg -q -F -- "$2" "$3" && ok || bad "$1 | Expected: '$2' in $3 | Got: absent"; }
lacks() { rg -q -F -- "$2" "$3" && bad "$1 | Expected: no '$2' in $3 | Got: present" || ok; }

# inventory rows and refresh probe
has   vr-rows    '...REDIRECTS.map(([from, to]) => [from, 200, null, null, to])' "$VR"
lacks vr-no307   '[from, 307, to]' "$VR"
has   vr-marker  'http-equiv="refresh" content="1;url=' "$VR"
has   vr-noindex '["/foo", 200, null, "noindex"]' "$VR"
node --check "$VR" > /dev/null 2>&1 && ok || bad "vr-syntax | Expected: node --check rc 0 | Got: rc $?"
node "$VR" --list > /dev/null 2>&1 && ok || bad "vr-list | Expected: --list rc 0 | Got: rc $?"

# generated U3 and U7 checks, and the generator itself
for f in "$U/checks/U3.sh" "$U/genplan.py"; do
  for id in U3-bao-mat-200 U3-bao-mat-refresh U3-lich-su-200 U3-lich-su-refresh U3-tai-khoan-direct; do has "u3 $id $f" "$id" "$f"; done
  for id in U3-bao-mat-307 U3-bao-mat-target U3-lich-su-307 U3-lich-su-target; do lacks "u3-gone $id $f" "$id" "$f"; done
done
for f in "$U/checks/U7.sh" "$U/genplan.py"; do
  for id in U7-ghc-200 U7-ghc-refresh U7-hoan-tra-200 U7-hoan-tra-refresh; do has "u7 $id $f" "$id" "$f"; done
  for id in U7-ghc-307 U7-ghc-target U7-hoan-tra-307 U7-hoan-tra-target; do lacks "u7-gone $id $f" "$id" "$f"; done
done
has u3-bm-line "html U3-bao-mat-refresh /bao-mat 'http-equiv=\"refresh\" content=\"1;url=/tai-khoan\"'" "$U/checks/U3.sh"
has u3-ls-line "html U3-lich-su-refresh /lich-su 'http-equiv=\"refresh\" content=\"1;url=/tai-khoan\"'" "$U/checks/U3.sh"
has u3-tk-line "nohtml U3-tai-khoan-direct /tai-khoan 'http-equiv=\"refresh\"'" "$U/checks/U3.sh"
has u7-ghc-line "html U7-ghc-refresh /game-han-che 'http-equiv=\"refresh\" content=\"1;url=/cuoc-hop-le?tab=han-che\"'" "$U/checks/U7.sh"
has u7-ht-line "html U7-hoan-tra-refresh /hoan-tra 'http-equiv=\"refresh\" content=\"1;url=/khuyen-mai\"'" "$U/checks/U7.sh"
bash -n "$U/checks/U3.sh" && ok || bad "u3-syntax | Expected: bash -n rc 0 | Got: error"
bash -n "$U/checks/U7.sh" && ok || bad "u7-syntax | Expected: bash -n rc 0 | Got: error"

# A4 wording
lacks a4-no307 'the four redirects 307' "$U/GATES.md"
has   a4-pr41  'PR-41' "$U/GATES.md"

[ $fail -eq 0 ] || { echo "CHECKS FAILED HF4 $fail/$n"; exit 1; }
echo "CHECKS OK HF4 $pass/$n"
