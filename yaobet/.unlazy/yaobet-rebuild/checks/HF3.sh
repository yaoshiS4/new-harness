#!/usr/bin/env bash
# HF3 gate hot-fix: /foo and /khuyen-mai/pr9 are a streamed soft 404 (200 + noindex), as in the original.
set -u
cd "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)" || exit 2
U=.unlazy/yaobet-rebuild; VR=scripts/verify-routes.mjs
pass=0; fail=0; n=0
ok()  { n=$((n + 1)); pass=$((pass + 1)); }
bad() { n=$((n + 1)); fail=$((fail + 1)); echo "Fail: HF3 $1"; }
has()  { rg -q -F -- "$2" "$3" && ok || bad "$1 | Expected: '$2' in $3 | Got: absent"; }
lacks() { rg -q -F -- "$2" "$3" && bad "$1 | Expected: no '$2' in $3 | Got: present" || ok; }

# inventory rows and marker probe
has  vr-foo  '["/foo", 200, null, "noindex"]' "$VR"
has  vr-pr9  '["/khuyen-mai/pr9", 200, null, "noindex"]' "$VR"
lacks vr-no404-foo '["/foo", 404' "$VR"
lacks vr-no404-pr9 '["/khuyen-mai/pr9", 404' "$VR"
has  vr-marker 'name="robots" content="' "$VR"
node --check "$VR" > /dev/null 2>&1 && ok || bad "vr-syntax | Expected: node --check rc 0 | Got: rc $?"
node "$VR" --list > /dev/null 2>&1 && ok || bad "vr-list | Expected: --list rc 0 | Got: rc $?"

# generated S7 and S8 checks, and the generator itself
for f in "$U/checks/S7.sh" "$U/genplan.py"; do
  has   "s7-200 $f"     'S7-foo-200' "$f"
  has   "s7-noidx $f"   'S7-foo-noindex' "$f"
  has   "s7-index $f"   'S7-casino-indexable' "$f"
  has   "s7-title $f"   'S7-foo-title' "$f"
  lacks "s7-no404 $f"   'S7-foo-404' "$f"
done
for f in "$U/checks/S8.sh" "$U/genplan.py"; do
  has   "s8-200 $f"     'S8-pr9-200' "$f"
  has   "s8-noidx $f"   'S8-pr9-noindex' "$f"
  has   "s8-index $f"   'S8-pr1-indexable' "$f"
  lacks "s8-no404 $f"   'S8-pr9-404' "$f"
  lacks "s8-nodef $f"   'S8-pr9-default' "$f"
done
has s7-copy-file "has S7-foo-copy 'Không tìm thấy hạng mục' 'src/app/[vertical]/not-found.tsx'" "$U/checks/S7.sh"
has s7-noidx-line "html S7-foo-noindex /foo 'name=\"robots\" content=\"noindex\"'" "$U/checks/S7.sh"
has s8-noidx-line "html S8-pr9-noindex /khuyen-mai/pr9 'name=\"robots\" content=\"noindex\"'" "$U/checks/S8.sh"
bash -n "$U/checks/S7.sh" && ok || bad "s7-syntax | Expected: bash -n rc 0 | Got: error"
bash -n "$U/checks/S8.sh" && ok || bad "s8-syntax | Expected: bash -n rc 0 | Got: error"

# A4 wording
lacks a4-no404 '/khuyen-mai/pr9 404' "$U/GATES.md"
has   a4-pr40  'PR-40' "$U/GATES.md"

[ $fail -eq 0 ] || { echo "CHECKS FAILED HF3 $fail/$n"; exit 1; }
echo "CHECKS OK HF3 $pass/$n"
