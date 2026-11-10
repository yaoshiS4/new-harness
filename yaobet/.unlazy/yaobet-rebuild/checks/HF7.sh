#!/usr/bin/env bash
# HF7 gate hot-fix: a pair may be justified by a framework or original dev-build cause, a size mismatch included (PR-48).
set -u
cd "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)" || exit 2
export PATH="$HOME/.nvm/versions/node/v24.14.0/bin:$PATH"
U=.unlazy/yaobet-rebuild; G="$U/GATES.md"; J="$U/checks/shot-justify.json"; SD=scripts/shot-diff.mjs
pass=0; fail=0; n=0
ok()  { n=$((n + 1)); pass=$((pass + 1)); }
bad() { n=$((n + 1)); fail=$((fail + 1)); echo "Fail: HF7 $1"; }
has()   { rg -q -F -- "$2" "$3" && ok || bad "$1 | Expected: '$2' in $3 | Got: absent"; }

# justify rows: exactly the seven pairs, each reason cites a path:line
python3 -I -c '
import json, re, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
want = {"d1440-tiered-hoan-tra.jpg", "d1440-tiered-lich-su.jpg", "m375-tiered-lich-su.jpg",
        "m375-tiered-tin-nhan.jpg", "m375-tiered-vi-tien.jpg", "m375-tiered-tai-khoan.jpg",
        "m375-tiered-gioi-thieu.jpg"}
rows = {k: v for k, v in d.items() if not k.startswith("_")}
assert set(rows) == want, sorted(set(rows) ^ want)
for k, v in rows.items():
    assert isinstance(v, str) and re.search(r"[\w./-]+\.(js|ts|tsx|css|mjs):\d+", v), k
' "$J" && ok || bad "justify-rows | Expected: the 7 pairs, each with a path:line reason | Got: differ"

# gate wording; the A5 command and expectation stay as they were
has a5-size 'or a size mismatch justified in `checks/shot-justify.json`' "$G"
has a6-cause 'or a framework or dev-build cause proven on the original app with path:line evidence' "$G"
has a5-check '--masks .unlazy/yaobet-rebuild/checks/shot-masks.json --justify .unlazy/yaobet-rebuild/checks/shot-justify.json' "$G"
has a5-expect 'EXPECT: SHOTS OK 72/72' "$G"
git diff --quiet 2dd6cd2^ -- "$U/checks/shot-masks.json" && ok || bad "masks | Expected: shot-masks.json unchanged | Got: changed"

# shot-diff: a justified size mismatch passes and is labelled; an unjustified one still fails
has sd-label 'size mismatch (justified)' "$SD"
has sd-case-unjust '"size mismatch fails"' "$SD"
has sd-case-just '"justified size mismatch passes"' "$SD"
out=$(node "$SD" --self-test 2>&1); last=$(printf '%s\n' "$out" | tail -n 1)
[ "$last" = "SHOT-DIFF SELF-TEST OK" ] && ok || bad "self-test | Expected: SHOT-DIFF SELF-TEST OK | Got: $last"

[ $fail -eq 0 ] && { echo "CHECKS OK HF7 $pass/$n"; exit 0; }
echo "CHECKS FAILED HF7 $fail/$n"; exit 1
