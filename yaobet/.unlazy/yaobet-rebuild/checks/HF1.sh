#!/usr/bin/env bash
# HF1 gate hot-fix: string literals that are arguments of a non class-combiner call
# inside className (e.g. isActive("/")) are not class tokens; real tokens still are.
set -u
cd "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)" || exit 2
T=$(mktemp -d "${TMPDIR:-/tmp}/hf1.XXXXXX") || exit 2
trap 'rm -rf "$T"' EXIT
pass=0; fail=0; n=0
ok()  { n=$((n + 1)); pass=$((pass + 1)); }
bad() { n=$((n + 1)); fail=$((fail + 1)); echo "Fail: HF1 $1"; }
run() { node scripts/tw-unknown-classes.mjs "$1" > "$T/out.txt" 2>&1; }

# 1. built-in self-test still passes
node scripts/tw-unknown-classes.mjs --self-test > "$T/st.txt" 2>&1 && ok || bad "self-test | Expected: rc 0 | Got: $(tail -1 "$T/st.txt")"
# 2. the whole merged src tree is still clean
node scripts/tw-unknown-classes.mjs src > "$T/src.txt" 2>&1 && ok || bad "src tree | Expected: CLASSES OK | Got: $(tail -1 "$T/src.txt")"

# 3. call argument inside className is ignored (the BottomTabBar shape)
cat > "$T/a.tsx" <<'EOF'
export const A = ({ isActive }: { isActive: (p: string) => boolean }) => (
  <a className={["flex", isActive("/khuyen-mai") ? "grid" : ""].filter(Boolean).join(" ")} />
);
EOF
run "$T/a.tsx" && ok || bad "call-arg | Expected: rc 0 | Got: $(tail -1 "$T/out.txt")"

# 4-7. real unknown tokens are still reported
probe() { # $1 name, $2 jsx expression, $3 token that must be reported
  printf 'export const B = ({ f, c }: { f: (s: string) => boolean; c: boolean }) => <a className=%s />;\n' "$2" > "$T/$1.tsx"
  if run "$T/$1.tsx"; then bad "$1 | Expected: unknown-class $3 | Got: rc 0"
  elif rg -q -m 1 -F "unknown-class $3" "$T/out.txt"; then ok
  else bad "$1 | Expected: unknown-class $3 | Got: $(tail -1 "$T/out.txt")"; fi
}
probe b1 '{c ? "hf1-bogus-ternary" : ""}' hf1-bogus-ternary
probe b2 '{[f("x") ? "flex" : "", "hf1-bogus-after-call"].join(" ")}' hf1-bogus-after-call
probe b3 '"hf1-bogus-plain"' hf1-bogus-plain
probe b4 '{f("x") ? "hf1-bogus-branch" : "flex"}' hf1-bogus-branch

# 8. cn/clsx/cx arguments are still class tokens
cat > "$T/c.tsx" <<'EOF'
import { cn } from "./x";
export const C = () => <a className={cn("flex", "hf1-bogus-cn")} />;
EOF
if run "$T/c.tsx"; then bad "cn-arg | Expected: unknown-class hf1-bogus-cn | Got: rc 0"
elif rg -q -m 1 -F "unknown-class hf1-bogus-cn" "$T/out.txt"; then ok
else bad "cn-arg | Expected: unknown-class hf1-bogus-cn | Got: $(tail -1 "$T/out.txt")"; fi

[ $fail -eq 0 ] || { echo "CHECKS FAILED HF1 $fail/$n"; exit 1; }
echo "CHECKS OK HF1 $pass/$n"
