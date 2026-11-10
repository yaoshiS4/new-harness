# Gates: Yaobet phase-1 UI (root)

Scope: integrate branches 1.1 Foundation, 1.2 Shell, 1.3 Surfaces into one verified phase-1 build on mock data

- [ ] G1: every branch is reverified from its exact ledger
  CHECK: node ~/.claude/skills/unlazy/scripts/gate-check.mjs --root . --cwd . --reverify --jobs 1 .unlazy/yaobet-p1/gates/node-1.1.md .unlazy/yaobet-p1/gates/node-1.2.md .unlazy/yaobet-p1/gates/node-1.3.md
  EXPECT: ALL MET
  EVIDENCE: pending

- [ ] G2: the whole app lints, typechecks and builds from a clean tree
  CHECK: npm run lint && npx next typegen && npx tsc --noEmit && npm run build && echo ROOT_BUILD_OK
  EXPECT: ROOT_BUILD_OK
  EVIDENCE: pending

- [ ] G3: no new runtime or dev dependency was added in phase 1 (package.json dependency keys equal the scaffold set)
  CHECK: node -e "const p=require('./package.json');const d=Object.keys(p.dependencies).sort().join(',');const v=Object.keys(p.devDependencies).sort().join(',');const okD='next,react,react-dom';const okV='@tailwindcss/turbopack,@types/node,@types/react,@types/react-dom,eslint,eslint-config-next,tailwindcss,typescript';if(d!==okD||v!==okV){console.log('DEPS CHANGED',d,v);process.exit(1)}console.log('deps unchanged')"
  EXPECT: deps unchanged
  EVIDENCE: pending

- [ ] G4: no plan or audit tags and no legal or regulatory terms in application code and copy
  CHECK: node -e "const {execSync}=require('child_process');let out='';try{out=execSync('rg -n -i \"Wave [0-9]|UG-[0-9]|OQ-[0-9]|leaf-1\\\\.|nghị định|decree|giấy phép|licen[cs]e|statute|regulat\" src',{encoding:'utf8'})}catch(e){out=e.stdout||''}if(out.trim()){console.log(out);process.exit(1)}console.log('tag and legal scan clean')"
  EXPECT: tag and legal scan clean
  EVIDENCE: pending

- [ ] G5: no competitor art or hotlinked images (every image src is local and under public/placeholders or a static import)
  CHECK: node -e "const {execSync}=require('child_process');let out='';try{out=execSync('rg -n \"src=\\\\\\\"https?://|hotlink|okvip|ok9|fly88|shbet|stake\\\\.com|j9\" src public',{encoding:'utf8'})}catch(e){out=e.stdout||''}if(out.trim()){console.log(out);process.exit(1)}console.log('asset scan clean')"
  EXPECT: asset scan clean
  EVIDENCE: pending

- [ ] G6: oracle-review and hallucination-auditor PASS on the final diff (claims trace to SOT and ADR; no fabricated routes, tokens or copy)
  EVIDENCE: pending

- [ ] G7: owner has viewed the home and lobby at 375 and 1440 in the placeholder greyscale ramp and accepted the layout direction (ADR-001 §3)
  EVIDENCE: pending
