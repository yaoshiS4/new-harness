#!/usr/bin/env bash
# HF2 gate hot-fix: string literals that are operands of ===, !==, ==, != inside
# className are not class tokens; branches and other literals still are.
set -u
cd "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)" || exit 2
T=$(mktemp -d "${TMPDIR:-/tmp}/hf2.XXXXXX") || exit 2
trap 'rm -rf "$T"' EXIT
pass=0; fail=0; n=0
ok()  { n=$((n + 1)); pass=$((pass + 1)); }
bad() { n=$((n + 1)); fail=$((fail + 1)); echo "Fail: HF2 $1"; }
run() { node scripts/tw-unknown-classes.mjs "$1" > "$T/out.txt" 2>&1; }
mk()  { printf 'export const B = ({ d }: { d: string }) => <a className=%s />;\n' "$2" > "$T/$1.tsx"; }

# 1. built-in self-test still passes
node scripts/tw-unknown-classes.mjs --self-test > "$T/st.txt" 2>&1 && ok || bad "self-test | Expected: rc 0 | Got: $(tail -1 "$T/st.txt")"
# 2. the whole merged src tree is still clean
node scripts/tw-unknown-classes.mjs src > "$T/src.txt" 2>&1 && ok || bad "src tree | Expected: CLASSES OK | Got: $(tail -1 "$T/src.txt")"

# 3-6. comparison operands are ignored (the LiveOddsBoard shape and its variants)
clean() { mk "$1" "$2"; run "$T/$1.tsx" && ok || bad "$1 | Expected: rc 0 | Got: $(tail -1 "$T/out.txt")"; }
clean c1 '{d === "hf2-op-a" ? "flex" : "grid"}'
clean c2 '{d !== "hf2-op-b" ? "flex" : "grid"}'
clean c3 '{"hf2-op-c" == d ? "flex" : "grid"}'
clean c4 '{d != `hf2-op-d` ? "flex" : "grid"}'

# 7-10. real unknown tokens are still reported
probe() { # $1 name, $2 jsx expression, $3 token that must be reported
  mk "$1" "$2"
  if run "$T/$1.tsx"; then bad "$1 | Expected: unknown-class $3 | Got: rc 0"
  elif rg -q -m 1 -F "unknown-class $3" "$T/out.txt"; then ok
  else bad "$1 | Expected: unknown-class $3 | Got: $(tail -1 "$T/out.txt")"; fi
}
probe b1 '{d === "up" ? "hf2-bogus-then" : "flex"}' hf2-bogus-then
probe b2 '{d === "up" ? "flex" : "hf2-bogus-else"}' hf2-bogus-else
probe b3 '{[d === "up" && "hf2-bogus-and", "flex"].join(" ")}' hf2-bogus-and
probe b4 '{["hf2-bogus-item", d === "up" ? "flex" : ""].join(" ")}' hf2-bogus-item

[ $fail -eq 0 ] || { echo "CHECKS FAILED HF2 $fail/$n"; exit 1; }
echo "CHECKS OK HF2 $pass/$n"
