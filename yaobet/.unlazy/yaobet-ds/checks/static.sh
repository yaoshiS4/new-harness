#!/usr/bin/env bash
# The 29 static rebuild leaf checks of the tree in the cwd (PLAN.md STATIC). Retired and not
# run: orig-boxes.sh. Helpers, not checks: lib.sh, fetch.sh, lease.sh, no-dev-toggle.sh,
# fonts-preflight.sh. Prints STATIC OK 29/29.
LEAF=static; PORT=0
. "$(dirname "${BASH_SOURCE[0]}")/ds.sh"

CHECKS=(F0 F1 F2 F3a F3b F4 F5 FTfix HF1 HF2 HF3 HF4 HF5 HF7 KF1 R1 R2 S1 S2 S3 S4 S5 S6fix U1 U2 U6 built-css census hygiene)
RB=.unlazy/yaobet-rebuild/checks
eq static-count 29 "${#CHECKS[@]}"
pass=0
for c in "${CHECKS[@]}"; do
  need "static-$c" "$RB/$c.sh" || continue
  out=$(bash "$RB/$c.sh" 2>&1); rc=$?
  last=$(printf '%s\n' "$out" | tail -n 1)
  case "$last" in "CHECKS OK $c "* | "$c OK") okline=1 ;; *) okline=0 ;; esac
  if [ "$rc" -eq 0 ] && [ "$okline" -eq 1 ]; then
    ok; pass=$((pass + 1))
  else
    printf '%s\n' "$out" | rg -m 5 '^Fail'
    fail "static-$c" "exit 0 and the $c OK line" "exit $rc: $last"
  fi
done
if [ "$N_FAIL" -eq 0 ] && [ "$pass" -eq 29 ]; then echo "STATIC OK $pass/29"; exit 0; fi
echo "STATIC FAILED $pass/29"; exit 1
