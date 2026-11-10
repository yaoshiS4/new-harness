# genplan.py v2: builder hand-off (sa, 2026-11-05)

The lease hook denies the `sa` role any write to `genplan.py` ("non-builder subagent role must not mutate application source"). This file holds the complete replacement generator that resolves `docs/rebuild/review/PLAN-GATE.md` items 1-35.

Builder task (a `debugger` or `dev-be`, on the PM's order):

```yaml
allowed_files:
  - .unlazy/yaobet-rebuild/genplan.py
  - .unlazy/yaobet-rebuild/PLAN.md
  - .unlazy/yaobet-rebuild/GATES.md
  - .unlazy/yaobet-rebuild/gates/**
  - .unlazy/yaobet-rebuild/checks/**
verification_cmd: |
  python3 .unlazy/yaobet-rebuild/genplan.py &&
  node ~/.claude/skills/unlazy/scripts/gate-lint.mjs .unlazy/yaobet-rebuild/GATES.md .unlazy/yaobet-rebuild/gates/leaf-*.md &&
  for f in .unlazy/yaobet-rebuild/checks/*.sh; do bash -n "$f" || exit 1; done && echo V2_OK
```

1. Replace `.unlazy/yaobet-rebuild/genplan.py` with the fenced block below, byte for byte.
2. Run it from the repo root. It must print `ok 31 ledgers, 18 waves; 380 original src files, 358 owned exactly once, 22 excluded; ...`.
3. Run `verification_cmd`. Commit nothing (the PM commits).

The sa validation run executed this exact block into a scratch directory (`GENPLAN_OUT`); see the sa return for the output.

```python
#!/usr/bin/env python3
"""Generate the yaobet-rebuild plan: PLAN.md, GATES.md, gates/leaf-*.md and checks/*.

Run from anywhere: python3 .unlazy/yaobet-rebuild/genplan.py
Every output below is generated. Edit this file, never the outputs. The files a
PM or QC role fills after review (checks/shot-justify.json, checks/a11-allow.txt)
are created once and never overwritten. GENPLAN_OUT redirects all output (dry run).

Asserts (the run fails loudly if one breaks):
- leaf ids are unique, at most 2 leaves per wave, every Need is in an earlier wave;
- every OWNS entry is brace-free, comma-free and space-free, and is either an exact
  path or a `dir/**` prefix (the only form the lease hook and checks/lease.sh share);
- every OWNS entry under src/ names a real path of the original tree or a file
  that PR-01/PR-21 create (no invented files);
- every original src/ file has exactly one owner, except the listed exclusions;
- inside a wave no two leases overlap (path test and the real hook matcher).
"""
import importlib.util
import json
import os
import shlex

_SELF = os.path.dirname(os.path.abspath(globals().get("__file__", "") or "."))
HERE = os.environ.get("GENPLAN_OUT") or _SELF
REPO = os.environ.get("GENPLAN_REPO") or os.path.abspath(os.path.join(_SELF, "..", ".."))
ORIG = "/Users/maxime/Documents/Projects/Antigravity/Igaming-Agent-1/apps/web"
GUIDE = "/Users/maxime/Documents/Projects/Antigravity/Igaming-Agent-1/.hc/ui-rebuild-guide"
REF_SHOTS = GUIDE + "/shots"
HOOK = os.path.abspath(os.path.join(REPO, "..", ".claude", "hooks", "harness_lib.py"))
CK = ".unlazy/yaobet-rebuild/checks"
os.makedirs(os.path.join(HERE, "gates"), exist_ok=True)
os.makedirs(os.path.join(HERE, "checks", "owns"), exist_ok=True)

AREAS = ["shell", "home", "vertical", "promo", "auth", "member", "vip", "store", "lottery", "collection"]
AREA_CSS = [f"src/styles/areas/{a}.css" for a in AREAS]
NEW_FILES = set(AREA_CSS) | {"src/ui/ui.css", "src/styles/keyframes.css", "src/styles/tw-theme.css", "src/styles/stub.css"}
CSS_CENSUS = sorted(["src/app/globals.css"] + [f"src/styles/{s}.css" for s in
                     ["reset", "tokens", "themes", "brands", "typography", "motion", "keyframes", "tw-theme", "stub"]]
                    + ["src/ui/ui.css"] + AREA_CSS)
VERTICALS = [("casino", "Casino"), ("slots", "Nổ hũ"), ("sports", "Thể thao"), ("fishing", "Bắn cá"),
             ("card", "Game bài"), ("lottery", "Xổ số"), ("cockfight", "Đá gà"), ("table", "Bàn chơi"),
             ("arcade", "Game nhanh")]

def lay(*names):
    return [f"src/components/layout/{n}" for n in names]

def home(*names):
    return [f"src/components/home/{n}" for n in names]

def vip(*names):
    return [f"src/components/vip/{n}" for n in names]

def col(*names):
    return [f"src/components/collection/{n}" for n in names]

def ui(*names):
    return [f"src/ui/{n}/**" for n in names]

PR05 = ("Path parity (PR-05): the folders are `src/components/layout` and `src/components/category`. "
        "shell-home §5 G-02, ADR-SH-01 and every `components/shell|vertical` or `src/styles/components/` path "
        "in shell-home §7 are superseded (ADR-002 §6). ")

# id, wave, title, review, review row, owns, needs, routes, notes
L = [
 ("F0", 0, "stack, gate scripts and wipe", "foundations-core", "F0 stack-and-gates",
  ["package.json", "package-lock.json", "next.config.ts", "tsconfig.json", "eslint.config.mjs", ".gitignore",
   "scripts/**", "src/**"],
  [], [],
  "`src/**` is a deletion-only lease: delete every file under `src/` (PR-07, D4) and create nothing there. "
  "Delete the old `scripts/verify-content.mjs`, `verify-format.mjs` and `verify-tokens.mjs`; rewrite `scripts/verify-routes.mjs`. `next.config.ts` per PR-24. Pin `\"playwright\": \"1.61.1\"` exactly (PR-30). "
  "Write every gate script exactly to the contracts in ADR-002 §4 and §5: `token-lint.mjs`, `rebuild-rules.mjs`, "
  "`tw-unknown-classes.mjs`, `verify-routes.mjs`, `with-dev-server.mjs`, `capture-shots.mjs`, `shot-diff.mjs`, "
  "`box-check.mjs`, `auth-flow.mjs`. Keep the `.claude/**` ignore in `eslint.config.mjs` and add the collection "
  "ports-barrel rule the row checks. Add `/.shots/` and `/shots/` to `.gitignore`. Never edit `.unlazy/**`."),
 ("F1", 1, "styles foundation", "foundations-core", "F1 styles-foundation",
  ["src/app/globals.css", "src/styles/**", "src/ui/ui.css"],
  ["F0"], [],
  "ADR-002 §1 is the exact import list. Create `src/ui/ui.css` and the 10 `src/styles/areas/*.css` as empty files. "
  "`src/styles/stub.css` replaces the original `src/app/stub.module.css` (PR-33). Custom variants per PR-16. "
  "The 7 `ui-*` keyframes go in `src/styles/keyframes.css` (PR-18). The built-CSS checks of this row run in I1."),
 ("F2", 1, "lib core and providers", "foundations-core", "F2 lib-core-and-providers",
  ["src/lib/format.ts", "src/lib/i18n.ts", "src/lib/rg.ts", "src/lib/types.ts", "src/lib/auth/**", "src/app/providers.tsx"],
  ["F0"], [],
  "Port `i18n.ts` verbatim from the original (PR-26) and list the ported files. Token lint is not a gate here "
  "(F1 writes the definition files in the same wave); the PM runs it after the W1 merge. "
  "Drop tag tokens and regulatory references from comments only (PR-27, PR-31)."),
 ("F3a", 2, "mock data 1", "foundations-core", "F3a mock-data-1",
  [f"src/lib/mock/{n}.ts" for n in ["helpers", "types", "lobby", "games", "vip", "wallet", "promos", "store", "referral", "cashback"]],
  ["F2"], [], "Comments: PR-27, PR-31."),
 ("R1", 2, "rewards libs", "rewards", "R1 rewards-libs",
  ["src/lib/vip/**", "src/lib/store/**"],
  ["F2"], [], "Verbatim port where the guide elides code (PR-03); list the ported files. Comments: PR-27, PR-31."),
 ("F3b", 3, "mock data 2", "foundations-core", "F3b mock-data-2",
  [f"src/lib/mock/{n}.ts" for n in ["records", "messages", "notification-feed", "profile", "deposit", "medals", "contribution", "lottery", "index"]],
  ["F3a"], [], "Port `notification-feed.ts` verbatim (PR-26). Comments: PR-27, PR-31."),
 ("R2", 3, "collection lib", "rewards", "R2 collection-lib",
  ["src/lib/collection/**"],
  ["F2"], [], "Verbatim port where the guide elides code (PR-03). `adapters/fixtures.ts` carries a tag token in a string literal: see PR-32 (open)."),
 ("U1", 4, "ui base primitives", "ui-member", "UIM-L1 ui-base",
  ["src/ui/ui.css"] + ui("Icon", "Badge", "Button", "Card", "Pill", "MoneyValue", "Skeleton"),
  ["F1", "F2"], [],
  "PR-15: base rules in `src/ui/ui.css`, plain class rules only, no `@layer` wrapper (ADR-002 §1). Write the base-primitive "
  "rules only; U2 appends the composite rules below them. The spinner uses `ui-spin 700ms linear infinite` (PR-18)."),
 ("F4", 4, "public assets", "foundations-core", "F4 public-assets",
  ["public/**"],
  ["F0"], [],
  "Byte-copy the original `apps/web/public/**`: 36 files including the 3 `(1)` duplicates (PR-28; shell-home §6 last line is "
  "superseded). `favicon.ico` belongs to F5."),
 ("U2", 5, "ui composite, overlays, barrel", "ui-member", "UIM-L2 ui-composite",
  ["src/ui/ui.css"] + ui("EmptyState", "ErrorState", "Countdown", "Odometer", "Scroller", "Tabs", "Tile", "Modal", "Sheet", "Dropdown") + ["src/ui/index.ts"],
  ["U1"], [],
  "`src/ui/ui.css` passes from U1 (W4) to U2 (W5): append the composite rules below U1's. Primitive keyframes are "
  "never redeclared (PR-18)."),
 ("S1", 5, "shell internals", "shell-home", "L1 shell-internal",
  ["src/components/layout/_internal/**", "src/styles/areas/shell.css"],
  ["U1", "F3b"], [], PR05 + "All 8 shell keyframes keep their guide names (PR-29) and live in `shell.css`."),
 ("S2", 6, "header and nav", "shell-home", "L2 shell-header-nav",
  lay("Header.tsx", "MemberMenu.tsx", "NotificationBell.tsx", "BottomTabBar.tsx", "CategorySheet.tsx") + ["src/styles/areas/shell.css"],
  ["S1", "U2"], [],
  PR05 + "Reproduce SH-02 (PR-09). `shell.css` passes from S1 (W5): append only. The curl and box checks of this row run in I1."),
 ("S4", 6, "auth modal", "shell-home", "L4 auth-modal",
  ["src/components/auth/**", "src/styles/areas/auth.css"],
  ["S1", "U2"], [], "The Playwright auth flow of this row runs in I1 and A9b."),
 ("S3", 7, "frame, footer, rails", "shell-home", "L3 shell-frame-footer-rails",
  lay("AppShell.tsx", "ShellChrome.tsx", "Footer.tsx", "QuickActionRail.tsx", "RightRail.tsx", "index.ts") + ["src/styles/areas/shell.css"],
  ["S2", "S4"], [],
  PR05 + "`index.ts` is the original barrel (it does not export QuickActionRail). `shell.css` passes from S2 (W6): append only. "
  "The curl checks of this row run in I1."),
 ("S5", 7, "home bands and DEV toggle", "shell-home", "L5 home-bands",
  home("HeroBand.tsx", "CategoryLauncher.tsx", "StatsBar.tsx", "DevAuthToggle.tsx") + ["src/styles/areas/home.css"],
  ["S1", "U2"], [],
  "There is no `Home.tsx` (PR-33): the original `Home.module.css` becomes classes in `home.css`, used directly by "
  "`app/page.tsx` and `app/loading.tsx` (S6). DevAuthToggle follows foundations-core §3.9 and PR-08. The prod/dev toggle checks run in I1."),
 ("F5", 8, "root layout", "foundations-core", "F5 root-composition",
  ["src/app/layout.tsx", "src/app/favicon.ico"],
  ["F1", "F2", "S3", "S5"], [],
  "Byte-copy `favicon.ico` (25,931 bytes). F5 owns no page, so it has no route gate; its curl checks run in I1 and the "
  "capture `setState`/`checkState` check is part of A5. The PM runs the fonts preflight (G-fonts) before dispatch."),
 ("S6", 8.5, "home route", "shell-home", "L6 home-route-grid",
  home("ProviderGameGrid.tsx", "SportsLifestyle.tsx", "SportsMatchCard.tsx", "index.ts") + ["src/app/page.tsx", "src/app/loading.tsx", "src/styles/areas/home.css"],
  ["F5", "S3", "S5"], ["/"],
  "`index.ts` keeps the original barrel minus the export lines of the 8 dead bands (PR-19, PR-34). `home.css` passes from S5 (W7): append only. "
  "F0 already removed the deletions this row lists. The 1440 filler count runs in I1 (box-check)."),
 ("S7", 9, "vertical route", "shell-home", "L7 vertical-route",
  ["src/components/category/**", "src/app/[vertical]/**", "src/styles/areas/vertical.css"],
  ["F5", "S6"], [f"/{s}" for s, _ in VERTICALS] + ["/foo"], PR05),
 ("S8", 9, "promo routes", "shell-home", "L8 promo-routes",
  ["src/components/promo/**", "src/app/khuyen-mai/**", "src/styles/areas/promo.css"],
  ["F5", "S6"], ["/khuyen-mai"] + [f"/khuyen-mai/pr{i}" for i in range(1, 10)], ""),
 ("U6", 10, "contribution components", "ui-member", "UIM-L6 contribution",
  ["src/components/contribution/**"],
  ["U2", "F3b"], [], "The noscript hooks of SearchField are an inline `<style>` with `data-*` selectors (ui-member G-5); no partial."),
 ("U3", 10, "member frame and account", "ui-member", "UIM-L3 member frame + account",
  ["src/app/(member)/layout.tsx", "src/app/(member)/tai-khoan/**", "src/app/bao-mat/**", "src/app/lich-su/**",
   "src/components/account/**", "src/styles/areas/member.css"],
  ["F5", "S3"], ["/tai-khoan", "/bao-mat", "/lich-su"],
  "The member keyframes keep their guide names `pulseDot` and `progressShimmer` (PR-29) in `src/styles/areas/member.css`. "
  "The original `(member)/member.module.css` becomes classes in `member.css`. Do not build ProfileHeader, QuickActions, "
  "AccountMenu or LogoutMenuItem (PR-19); drop their barrel exports (PR-34). The port comes from with-dev-server, not 3000."),
 ("U7", 11, "trust, restricted, utility routes", "ui-member", "UIM-L7 trust routes",
  [f"src/app/{r}/**" for r in ["cuoc-hop-le", "game-han-che", "hoan-tra", "ho-tro", "tro-giup", "tai-app", "phong-cach"]]
  + ["src/components/restricted/**"],
  ["U6", "F5"], ["/cuoc-hop-le", "/game-han-che", "/hoan-tra", "/ho-tro", "/tro-giup", "/tai-app", "/phong-cach"],
  "There is no `src/components/utility` and no `StubPage` (PR-33): each stub page uses F1's `stub-*` utilities, as the "
  "original pages used `../stub.module.css`."),
 ("U4", 11, "wallet", "ui-member", "UIM-L4 wallet",
  ["src/app/(member)/vi-tien/**", "src/components/wallet/**", "src/styles/areas/member.css"],
  ["U3"], ["/vi-tien"], "`member.css` passes from U3 (W10): append only."),
 ("U5", 12, "messages and referral", "ui-member", "UIM-L5 messages + referral",
  [f"src/app/(member)/{r}/**" for r in ["tin-nhan", "gioi-thieu", "dai-ly"]]
  + ["src/components/messages/**", "src/components/referral/**", "src/styles/areas/member.css"],
  ["U3"], ["/tin-nhan", "/gioi-thieu", "/dai-ly"], "`member.css` passes from U4 (W11): append only."),
 ("R3", 12, "vip program", "rewards", "R3 vip-program",
  vip(*[f"{n}.tsx" for n in ["VipProgram", "VipSectionHeading", "VipHeroGuest", "VipHeroMember", "LevelRing", "TierDeck",
                              "PrivilegeComparison", "PrivilegeMatrix", "LevelTable", "VipFaq"]]) + ["src/app/vip/**", "src/styles/areas/vip.css"],
  ["R1", "F5"], ["/vip"],
  "No `@utility` in `vip.css` (ADR-002 §1): rewards T8 becomes plain classes `.vip-hero-guest-bg` and `.vip-hero-member-bg`. "
  "The luxury palette comes from the F1 tokens; this leaf only applies them."),
 ("R5", 13, "store", "rewards", "R5 store",
  ["src/components/store/**", "src/app/cua-hang/**", "src/styles/areas/store.css"],
  ["R1", "F5"], ["/cua-hang"], "Reproduce the module-load cooldown timing (PR-04)."),
 ("R6", 13, "lottery", "rewards", "R6 lottery",
  ["src/components/lottery/**", "src/app/ve-so/**", "src/styles/areas/lottery.css"],
  ["F3b", "S1", "F5"], ["/ve-so"],
  "The canvas reads `--brand-accent`, `--brand-accent-2`, `--canvas` and `--text-hi` (PR-13). The manual canvas erase check is part of A8."),
 ("R7", 14, "collection surface", "rewards", "R7 collection-surface",
  col("CollectionApp.tsx", "PackStage.tsx", "CardArt.tsx", "RewardCeremony.tsx", "CollectionTerms.tsx", "CollectionHistory.tsx")
  + ["src/app/bo-suu-tap/page.tsx", "src/app/bo-suu-tap/CollectionRoot.tsx", "src/styles/areas/collection.css"],
  ["R2", "S1", "F5"], ["/bo-suu-tap"],
  "CardArt's `sweep` becomes `card-foil-sweep`; every other keyframe keeps its guide name (PR-29)."),
 ("R4", 14, "vip tier and club", "rewards", "R4 vip-tier-club",
  vip("CurrentTierCard.tsx", "TierLadder.tsx", "PrivilegeTable.tsx", "PerkGallery.tsx", "VipRules.tsx", "VipSection.tsx", "copy.ts", "index.ts")
  + ["src/app/tier/**", "src/app/cau-lac-bo/**", "src/styles/areas/vip.css"],
  ["R3"], ["/tier", "/cau-lac-bo"],
  "`/cau-lac-bo` uses F1's `stub-*` utilities (PR-33). The original `VipPage.module.css` (used only by `/tier`) becomes "
  "utilities or `vip.css` classes. `vip.css` passes from R3 (W12): append only."),
 ("R8", 15, "collection mine and dev ports", "rewards", "R8 collection-mine-dev",
  col("MyCards.tsx", "CardDetail.tsx") + ["src/app/bo-suu-tap/cua-toi/**", "src/app/dev/collection-ports/**", "src/styles/areas/collection.css"],
  ["R7"], ["/bo-suu-tap/cua-toi", "/dev/collection-ports"],
  "`collection.css` passes from R7 (W14): append only. `dev/collection-ports/page.tsx` renders tag tokens in its copy: see PR-32 (open)."),
]
ALL_IDS = [l[0] for l in L]
L.append(("I1", 16, "deferred integration checks", "all", "the deferred rows",
          [], list(ALL_IDS), [],
          "Verification only: no lease, no builder. The PM (or test-runner) runs it on `main` after the last merge. "
          "It holds every acceptance check that cannot run in its leaf's own wave: built CSS (F1, PR-13, fonts), "
          "the curl checks of F5, S2, S3 and S5, the SH-02 box check and the 1440 filler count (S2, S6), and the auth flow (S4)."))

# Original files implemented by a leaf under another name (translated, not recreated).
TRANSLATES = {
    "F1": ["src/app/stub.module.css"],
    "S5": ["src/components/home/Home.module.css"],
    "U3": ["src/app/(member)/member.module.css"],
    "R4": ["src/components/vip/VipPage.module.css"],
    "R7": col("card-art.module.css", "ceremony.module.css", "collection.module.css", "history.module.css",
              "pack.module.css", "terms.module.css"),
    "R8": col("my-cards.module.css", "card-detail.module.css"),
}
DEAD_HOME = ["AuthCluster", "PromoChips", "LiveGamesBand", "JackpotTicker", "LiveMatchCard", "VipAisle", "PartnerBand", "HomeFooter"]
DEAD_ACCOUNT = ["ProfileHeader", "QuickActions", "AccountMenu"]
EXCLUDED = {}
for n in DEAD_HOME:
    for ext in (".tsx", ".module.css"):
        EXCLUDED[f"src/components/home/{n}{ext}"] = "PR-19 / shell-home §2i (dead home band)"
for n in DEAD_ACCOUNT:
    for ext in (".tsx", ".module.css"):
        EXCLUDED[f"src/components/account/{n}{ext}"] = "PR-19 (dead account component)"
COVERAGE_EXEMPT = {("F0", "src/**")}

ids = [l[0] for l in L]
assert len(ids) == len(set(ids)) == 31, len(ids)
waves = {}
for l in L:
    waves.setdefault(l[1], []).append(l[0])
assert all(len(v) <= 2 for v in waves.values()), waves
wave_of = {l[0]: l[1] for l in L}
for l in L:
    for n in l[6]:
        assert wave_of[n] < l[1], (l[0], n)

def wl(w):
    return f"W{int(w)}b" if w != int(w) else f"W{int(w)}"

PORT = {lid: 3110 + i for i, lid in enumerate(ALL_IDS)}
PORT["I1"] = 3140

# ---------------------------------------------------------------- lease form + coverage
def entry_ok(e):
    if any(c in e for c in "{},\t ") or e.startswith("/"):
        return False
    core = e[:-3] if e.endswith("/**") else e
    return not any(c in core for c in "*?")

def covers(entry, path):
    if entry.endswith("/**"):
        return path.startswith(entry[:-2])
    return path == entry

for l in L:
    for e in l[5]:
        assert entry_ok(e), (l[0], e)

orig_src = []
for dp, dn, fn in os.walk(os.path.join(ORIG, "src")):
    for f in fn:
        if not f.startswith("."):
            orig_src.append(os.path.relpath(os.path.join(dp, f), ORIG))
orig_src.sort()
assert len(orig_src) == 380, len(orig_src)
orig_public = sorted(os.path.relpath(os.path.join(dp, f), ORIG)
                     for dp, dn, fn in os.walk(os.path.join(ORIG, "public")) for f in fn if not f.startswith("."))
assert len(orig_public) == 36, len(orig_public)

def lease_of(l):
    return [e for e in l[5] if (l[0], e) not in COVERAGE_EXEMPT]

for l in L:
    for e in lease_of(l):
        if e.startswith("src/"):
            real = any(covers(e, p) for p in orig_src) or e in NEW_FILES
            assert real, ("OWNS names no original path and no PR-01/PR-21 file", l[0], e)
        elif e == "public/**":
            assert orig_public
        else:
            assert os.path.exists(os.path.join(REPO, e[:-3] if e.endswith("/**") else e)), (l[0], e)

owners = {}
for p in orig_src:
    who = set()
    for l in L:
        for e in lease_of(l):
            if covers(e, p):
                who.add(l[0])
            if p.endswith(".module.css") and covers(e, p[:-len(".module.css")] + ".tsx"):
                who.add(l[0])
        if p in TRANSLATES.get(l[0], []):
            who.add(l[0])
    owners[p] = who
unowned = [p for p in orig_src if p not in EXCLUDED and len(owners[p]) == 0]
double = [(p, sorted(owners[p])) for p in orig_src if p not in EXCLUDED and len(owners[p]) > 1]
assert not unowned, unowned
assert not double, double
assert all(p in orig_src for p in EXCLUDED), [p for p in EXCLUDED if p not in orig_src]

for w, members in waves.items():
    if len(members) < 2:
        continue
    a, b = [next(x for x in L if x[0] == m) for m in members]
    for ea in a[5]:
        for eb in b[5]:
            pa, pb = ea[:-3] if ea.endswith("/**") else ea, eb[:-3] if eb.endswith("/**") else eb
            clash = pa == pb or (ea.endswith("/**") and pb.startswith(pa + "/")) or (eb.endswith("/**") and pa.startswith(pb + "/"))
            assert not clash, (wl(w), a[0], ea, b[0], eb)

# The real lease hook: every entry must accept a representative path, and no
# entry of a leaf may accept a path owned by its wave partner.
spec = importlib.util.spec_from_file_location("harness_lib", HOOK)
hl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hl)
WS = "/ws/yaobet"

def rep(e):
    if e.endswith("/**"):
        pre = e[:-2]
        for p in orig_src + orig_public + sorted(NEW_FILES):
            if p.startswith(pre):
                return p
        return pre + "probe.ts"
    return e

probe = ["# OWNS probe: .claude/hooks/harness_lib.py:matches_allowed_file(target, entry, ws)",
         "# generated by genplan.py; ws=" + WS, "# leaf | entry | representative path | result"]
neg = []
for l in L:
    for e in l[5]:
        r = rep(e)
        res = hl.matches_allowed_file(WS + "/" + r, e, WS)
        assert res, (l[0], e, r)
        probe.append(f"{l[0]} | {e} | {r} | {res}")
for w, members in waves.items():
    if len(members) < 2:
        continue
    a, b = [next(x for x in L if x[0] == m) for m in members]
    for x, y in ((a, b), (b, a)):
        for ey in y[5]:
            r = rep(ey)
            hit = [ex for ex in x[5] if hl.matches_allowed_file(WS + "/" + r, ex, WS)]
            assert not hit, (wl(w), x[0], hit, y[0], r)
            neg.append(f"{x[0]} | {r} (owned by {y[0]}) | False")
probe += ["# negative probes: a wave partner's path is denied by every entry of the other leaf"] + neg
open(os.path.join(HERE, "checks", "owns-probe.txt"), "w").write("\n".join(probe) + "\n")

for l in L:
    open(os.path.join(HERE, "checks", "owns", f"{l[0]}.txt"), "w").write("".join(e + "\n" for e in l[5]))

# ---------------------------------------------------------------- check script DSL
def q(x):
    x = str(x)
    if x.startswith("$") and not any(c in x for c in "\"'`\\ "):
        return '"' + x + '"'  # shell variables ($CHECKS_DIR, $PORT) must expand
    return shlex.quote(x)

def cmd(name, *args):
    return name + " " + " ".join(q(a) for a in args)

def has(i, s, *p): return cmd("has", i, s, *p)
def hasre(i, s, *p): return cmd("hasre", i, s, *p)
def lacks(i, s, *p): return cmd("lacks", i, s, *p)
def lacksF(i, s, *p): return cmd("lacksF", i, s, *p)
def count(i, op, n, s, *p): return cmd("count", i, op, n, s, *p)
def present(i, *p): return cmd("present", i, *p)
def absent(i, *p): return cmd("absent", i, *p)
def ts(i, exp, body): return cmd("ts", i, exp, body)
def run(i, exp, *c): return cmd("run", i, exp, *c)
def serve(mode, *urls): return f'serve {mode} "$PORT" ' + " ".join(q(u) for u in urls)
def code(i, u, c): return cmd("code", i, u, c)
def loc(i, u, s): return cmd("loc", i, u, s)
def html(i, u, s): return cmd("html", i, u, s)
def nohtml(i, u, s): return cmd("nohtml", i, u, s)
def same_main(i, a, b): return cmd("same_main", i, a, b)

def strings(prefix, items, *paths):
    return [has(f"{prefix}-s{k + 1}", s, *paths) for k, s in enumerate(items)]

C = {}
C["F0"] = [
    'ref=rb-F0; git rev-parse -q --verify "$ref" >/dev/null || ref=HEAD',
    'eq F0-wipe 0 "$(git ls-tree -r --name-only "$ref" -- src | wc -l | tr -d " ")"',
    'eq F0-lint-tokens-script "node scripts/token-lint.mjs" "$(jq -r \'.scripts["lint:tokens"] // "missing"\' package.json)"',
    'nonempty F0-self-test-script "$(jq -r \'.scripts["lint:tokens:self-test"] // empty\' package.json)"',
    'eq F0-seed-lines 8 "$(lines_matching "$(npm run -s lint:tokens:self-test 2>&1)" \'\\bseed\\b\')"',
    lacks("F0-no-cacheComponents", "cacheComponents", "next.config.ts"),
    lacks("F0-no-partialPrefetching", "partialPrefetching", "next.config.ts"),
    count("F0-turbopack-rule", "eq", 1, "@tailwindcss/turbopack", "next.config.ts"),
    count("F0-ports-barrel-rule", "eq", 1, "Collection components import the ports barrel", "eslint.config.mjs"),
    has("F0-eslint-ignores-claude", ".claude/**", "eslint.config.mjs"),
    'eq F0-no-stray-verify "" "$(rg --files scripts -g "verify-*.mjs" | rg -v "^scripts/verify-routes\\.mjs$" || true)"',
    absent("F0-old-verify-gone", "scripts/verify-content.mjs", "scripts/verify-format.mjs", "scripts/verify-tokens.mjs", "verify-app-ds.mjs"),
    'eq F0-deps "next,react,react-dom" "$(jq -r \'.dependencies|keys|join(",")\' package.json)"',
    'eq F0-playwright-pin 1.61.1 "$(jq -r \'.devDependencies.playwright // "missing"\' package.json)"',
    'eq F0-playwright-lock 1.61.1 "$(jq -r \'.packages["node_modules/playwright"].version // "missing"\' package-lock.json)"',
    cmd("hasline", "F0-gitignore-dotshots", "/.shots/", ".gitignore"),
    cmd("hasline", "F0-gitignore-shots", "/shots/", ".gitignore"),
    present("F0-scripts", *[f"scripts/{s}.mjs" for s in ["token-lint", "rebuild-rules", "tw-unknown-classes", "verify-routes",
                                                          "with-dev-server", "capture-shots", "shot-diff", "box-check", "auth-flow"]]),
    run("F0-rules-self-test", "SELF-TEST OK", "node", "scripts/rebuild-rules.mjs", "--self-test"),
    run("F0-tw-self-test", "SELF-TEST OK", "node", "scripts/tw-unknown-classes.mjs", "--self-test"),
    run("F0-wds-self-test", "WITH-DEV-SERVER SELF-TEST OK", "node", "scripts/with-dev-server.mjs", "--self-test"),
    run("F0-shot-diff-self-test", "SHOT-DIFF SELF-TEST OK", "node", "scripts/shot-diff.mjs", "--self-test"),
    'eq F0-route-inventory 43 "$(lines_matching "$(node scripts/verify-routes.mjs --list 2>&1)" "^/")"',
    cmd("fails", "F0-routes-unknown-flag", "node", "scripts/verify-routes.mjs", "--bogus"),
    cmd("fails", "F0-routes-only-outside", "node", "scripts/verify-routes.mjs", "--base", "http://127.0.0.1:9", "--only", "/not-in-inventory"),
    has("F0-capture-out-env", "process.env.SHOTS_OUT", "scripts/capture-shots.mjs"),
    has("F0-capture-base", "const BASE = 'http://localhost:3107';", "scripts/capture-shots.mjs"),
    run("F0-fonts", "CHECKS OK fonts", "bash", "$CHECKS_DIR/fonts-preflight.sh"),
]
C["F1"] = [
    count("F1-tokens", "eq", 163, r"^\s*--[a-z0-9-]+\s*:", "src/styles/tokens.css"),
    count("F1-brands", "ge", 24, "--brand-", "src/styles/brands.css"),
    count("F1-layer-base", "eq", 6, r"layer\(base\)", "src/app/globals.css"),
    lacks("F1-no-preflight", r'tailwindcss/preflight|@import "tailwindcss"', "src/app/globals.css"),
    count("F1-ui-keyframes", "eq", 7, "@keyframes ui-", "src/styles/keyframes.css"),
    count("F1-theme-keys", "eq", 115, "--color-|--spacing-|--text-t-|--leading-|--font-weight-|--font-brand-|--radius-|--ease-", "src/styles/tw-theme.css"),
    'eq F1-components-imports ' + q(" ".join(f'@import "{p}" layer(components)' for p in ["../ui/ui.css"] + [f"../styles/areas/{a}.css" for a in AREAS]) + " ")
    + ' "$(rg -o \'@import "[^"]+" layer\\(components\\)\' src/app/globals.css | tr "\\n" " ")"',
    present("F1-partials", "src/ui/ui.css", *AREA_CSS),
    has("F1-stub-import", '@import "../styles/stub.css";', "src/app/globals.css"),
    has("F1-hover-plain", "@custom-variant hover (&:hover)", "src/app/globals.css"),
] + [hasre(f"F1-variant-{v}", rf"@custom-variant {v}\b", "src/app/globals.css") for v in ["hover-fine", "touch", "max-420", "max-639", "max-900"]] + [
    hasre(f"F1-stub-{u}", rf"@utility stub-{u}\b", "src/styles/stub.css") for u in ["page", "heading", "body"]] + [
    'out=$(node scripts/tw-unknown-classes.mjs --emit "group-hover:bg-surface" 2>&1)',
    'contains F1-group-hover-plain ":hover" "$out"; not_contains F1-group-hover-no-media "@media (hover" "$out"',
    'out=$(node scripts/tw-unknown-classes.mjs --emit "hover:bg-surface" 2>&1)',
    'contains F1-hover-emits ":hover" "$out"; not_contains F1-hover-no-media "@media (hover" "$out"',
    'eq F1-no-module-css "" "$(rg --files src -g "*.module.css" || true)"',
]
TS_FMT = ('const f=await load("src/lib/format.ts"); return [f.formatVnd(1234567), f.formatVnd(-0.4), f.formatSignedVnd(1234567), '
          'f.formatOdds(3.6), f.formatPercent(12.5,1), f.formatPresetChip(6888000)].join("|")')
TS_RT = ('const f=await load("src/lib/format.ts"); const now=Date.parse("2026-01-01T00:00:00Z"); '
         'return [0.5,90,1439].map(m=>f.relativeTime(new Date(now-m*60000).toISOString(), now)).join("|")')
TS_I18N = ('const i=await load("src/lib/i18n.ts"); const n=o=>typeof o==="string"?1:(o&&typeof o==="object"?'
           'Object.values(o).reduce((a,v)=>a+n(v),0):0); return String(n(i.vi))')
C["F2"] = [
    ts("F2-formatters", "1.234.567 ₫|-0 ₫|+1.234.567 ₫|3.60|12,5%|6.888K", TS_FMT),
    ts("F2-relative-time", "1 phút trước|2 giờ trước|1 ngày trước", TS_RT),
    ts("F2-i18n-leaves", "398", TS_I18N),
    count("F2-provider-tiered", "eq", 1, 'initialState="tiered"', "src/app/providers.tsx"),
    count("F2-session-guest", "eq", 1, 'initialState = "guest"', "src/lib/auth/session.tsx"),
    count("F2-use-auth-guard", "eq", 1, "useAuth must be used within <MockAuthProvider>", "src/lib/auth/session.tsx"),
]
M = 'const m=await load("src/lib/mock/index.ts"); '
C["F3a"] = [
    ts("F3a-verticals", "9 /?v=casino", M + 'const v=await m.getVerticals(); return v.length+" "+v[0].href'),
    ts("F3a-games-providers", "16 6", M + 'return (await m.getGames()).length+" "+(await m.getProviders()).length'),
    ts("F3a-promo-order", "pr1,pr2,pr3,pr7,pr8,pr4,pr5,pr6", M + 'return (await m.getPromos()).map(p=>p.id).join(",")'),
    ts("F3a-store", "11 3250", M + 'return (await m.getProducts()).length+" "+(await m.getPointsBalance())'),
    ts("F3a-leaderboard", "1,2,3,5,6,7,8", M + 'return (await m.getLeaderboard()).value.map(r=>r.rank).join(",")'),
    ts("F3a-jackpot", "28686888000 15000", M + 'const j=await m.getJackpot(); return j.value.pool.amount+" "+j.freshnessMs'),
    ts("F3a-vip-progress", "18600000", M + 'return String((await m.getVipProgress()).value.current)'),
]
C["F3b"] = [
    ts("F3b-bell", "34 6 f01", M + 'const b=await m.getNotificationBell(); return b.length+" "+b.filter(x=>!x.read).length+" "+b[0].id'),
    ts("F3b-catalogue", "240", M + 'return String((await m.getContributionCatalogue()).length)'),
    ts("F3b-providers", "19 BTi", 'const c=await load("src/lib/mock/contribution.ts"); ' + M +
       'const d=c.deriveProviders(await m.getContributionCatalogue()); return d.length+" "+(typeof d[0]==="string"?d[0]:d[0].name)'),
    ts("F3b-restricted", "30", M + 'return String((await m.getRestrictedGames()).games.length)'),
    ts("F3b-security", "40", M + 'return String((await m.getSecurityIndex()).score)'),
    ts("F3b-lottery", "sc-v7zqd9py 8000 2.541,70 ₫", 'const l=await load("src/lib/mock/lottery.ts"); l.selfTest(); '
       'const c=l.makeScratchCard(undefined,1); return c.id+" "+c.dust+" "+l.SCRATCH_ODDS.rungCost'),
]
C["R1"] = [
    has("R1-copy", "Đặc quyền dành riêng cho hội viên VIP", "src/lib/vip/copy.ts"),
    has("R1-gift-mult", "GIFT_MULT = [0.6, 0.8, 1.0, 1.4, 2.0]", "src/lib/vip/formulas.ts"),
    has("R1-warn-step", "RG_UNLIMITED_WARN_STEP = 4", "src/lib/store/escalation.ts"),
    ts("R1-units", "1000,1429,2041,2916,4165,5950 50", 'const e=await load("src/lib/store/escalation.ts"); const f=await load("src/lib/vip/formulas.ts"); '
       'return [1,2,3,4,5,6].map(k=>e.pointsAtStep(1000,0.7,k,null)).join(",")+" "+f.giftAt(2,1)'),
]
C["R2"] = [
    has("R2-store-key", "yaobet.collection.v1", "src/lib/collection/adapters/store.ts"),
    has("R2-pity", "DEMO_PITY_BACKSTOP = 12", "src/lib/collection"),
    has("R2-no-draw", "Không tìm thấy lượt mở.", "src/lib/collection"),
    ts("R2-rate", "0.1212", 'const c=await load("src/lib/collection/fixtures/epl.ts"); return c.rateInSet("vandijk","set-defenders").toFixed(4)'),
    ts("R2-set-sums", "1,1,1", 'const c=await load("src/lib/collection/fixtures/epl.ts"); return c.DEMO_SETS.map(s=>{const t=c.cardsInSet(s.id)'
       '.reduce((a,k)=>a+(c.rateInSet(k.id,s.id)??0),0); return Math.abs(t-1)<1e-9?"1":String(t)}).join(",")'),
]
NO_LAYER = [lacks("ui-css-plain", "@layer|@utility|@apply|@theme|@custom-variant|@keyframes", "src/ui/ui.css")]
C["U1"] = [
    count("U1-icon-paths", "eq", 44, r"^\s+[a-zA-Z]+: <path", "src/ui/Icon/Icon.tsx"),
    has("U1-ui-css-import", '@import "../ui/ui.css" layer(components);', "src/app/globals.css"),
    hasre("U1-hover-fine", r"\(hover: ?hover\) and \(pointer: ?fine\)", "src/ui/ui.css"),
    hasre("U1-spin", "ui-spin 700ms linear infinite", "src/ui/ui.css"),
    hasre("U1-color-mix", r"color-mix\(in srgb, var\(--brand-accent\) 12%, var\(--surface-2\)\)", "src/ui/ui.css"),
    has("U1-money-stale-label", "Giá trị tạm dừng cập nhật", "src/ui/MoneyValue/MoneyValue.tsx"),
    has("U1-money-stale", "tạm dừng", "src/ui/MoneyValue/MoneyValue.tsx"),
    has("U1-skeleton-label", '"Đang tải"', "src/ui/Skeleton/Skeleton.tsx", "src/ui/Skeleton/TileSkeleton.tsx"),
    hasre("U1-grid-fill", r"targetRows \* cols - occupiedCells", "src/ui/Skeleton/useGridFill.ts"),
] + NO_LAYER
FOCUSABLE = 'a[href],button:not([disabled]),textarea,input,select,[tabindex]:not([tabindex="-1"])'
C["U2"] = [
    count("U2-barrel-exports", "eq", 39, "^export", "src/ui/index.ts"),
] + strings("U2", ["Chưa có dữ liệu", "Không có kết quả", "Đặt lại bộ lọc", "Không tải được dữ liệu", "Đã xảy ra lỗi. Vui lòng thử lại.",
                   "Mất kết nối mạng. Kiểm tra kết nối rồi thử lại.", "Thử lại", "Đã kết thúc", "Còn lại ", "Sắp ra mắt", "Thêm trò chơi mới"], "src/ui") + [
    has("U2-close-modal", 'aria-label="Đóng"', "src/ui/Modal/Modal.tsx"),
    has("U2-close-sheet", 'aria-label="Đóng"', "src/ui/Sheet/Sheet.tsx"),
    has("U2-odometer-dur", "const dur = 700", "src/ui/Odometer/Odometer.tsx"),
    has("U2-focusable-modal", FOCUSABLE, "src/ui/Modal/Modal.tsx"),
    has("U2-focusable-sheet", FOCUSABLE, "src/ui/Sheet/Sheet.tsx"),
    has("U2-focusable-dropdown", FOCUSABLE, "src/ui/Dropdown/Dropdown.tsx"),
    hasre("U2-tab-ids", r"tab-\$\{it.id\}", "src/ui/Tabs/Tabs.tsx"),
    has("U2-sheet-swipe", "dy > 80", "src/ui/Sheet/Sheet.tsx"),
] + NO_LAYER
INT = "src/components/layout/_internal/"
C["S1"] = [
    count("S1-keyframes", "eq", 8, r"@keyframes (scrim-in|sheet-up|dialog-in|panel-in|menu-in|notif-in|bell-swing|badge-pulse)\b", "src/styles/areas/shell.css"),
    has("S1-countdown-ended", "Đã kết thúc", INT + "Countdown.tsx"),
    has("S1-countdown-timer", 'role="timer"', INT + "Countdown.tsx"),
] + [has(f"S1-icon-{s}", s, INT + "verticalIcon.ts") for s, _ in VERTICALS] + [
    hasre("S1-overlay-swipe", r"\b96\b", INT + "Overlay.tsx"),
    hasre("S1-hover-intent", r"HOVER_INTENT_MS = 120\b", INT + "NavDropdown.tsx"),
    absent("S1-no-shell-folder", "src/components/shell"),
]
C["S2"] = [
    has("S2-utility-label", 'aria-label="Tiện ích"', "src/components/layout/Header.tsx"),
    has("S2-category-nav", "Danh mục trò chơi", "src/components/layout/Header.tsx"),
    has("S2-main-nav", "Điều hướng chính", "src/components/layout/BottomTabBar.tsx"),
    present("S2-files", *lay("Header.tsx", "MemberMenu.tsx", "NotificationBell.tsx", "BottomTabBar.tsx", "CategorySheet.tsx")),
]
C["S3"] = [
    'eq S3-hex-only-qr "src/components/layout/QuickActionRail.tsx " "$(rg -l -g "*.ts" -g "*.tsx" -e "#fff|#171a21" src/components/layout | LC_ALL=C sort | tr "\\n" " ")"',
    has("S3-rail-promo-key", "yb.rail.promo.dismissed", "src/components/layout/QuickActionRail.tsx"),
    has("S3-rail-jackpot-key", "yb.rail.jackpot.dismissed", "src/components/layout/QuickActionRail.tsx"),
    hasre("S3-appshell-props", r"rightRail\?", "src/components/layout/AppShell.tsx"),
    count("S3-barrel", "eq", 14, "^export", "src/components/layout/index.ts"),
    lacks("S3-barrel-no-qar", "QuickActionRail", "src/components/layout/index.ts"),
]
C["S4"] = strings("S4", ["Nạp nhanh · Rút nhanh · Hoàn trả mỗi ngày", "Mật khẩu xác nhận không khớp",
                         "Đã gửi hướng dẫn đặt lại mật khẩu. Vui lòng kiểm tra email hoặc tin nhắn.", "Mã giới thiệu (tùy chọn)",
                         "desktopMaxWidth={720}"], "src/components/auth/AuthModal.tsx", "src/lib/i18n.ts") + [
    hasre("S4-timer-600", r"\b600\b", "src/components/auth/AuthModal.tsx"),
    hasre("S4-timer-700", r"\b700\b", "src/components/auth/AuthModal.tsx"),
    has("S4-show-password", "Hiện mật khẩu", "src/components/auth/AuthField.tsx"),
]
C["S5"] = [
    count("S5-hero-keyframes", "eq", 2, r"@keyframes heroSeg(Grid)?\b", "src/styles/areas/home.css"),
    hasre("S5-cycle", r"\bcycle\b", "src/components/home/DevAuthToggle.tsx"),
    hasre("S5-state-label", r"\bstateLabel\b", "src/components/home/DevAuthToggle.tsx"),
    has("S5-dwell", "DWELL_MS = 6000", "src/components/home/HeroBand.tsx"),
    has("S5-swipe", "SWIPE_THRESHOLD = 48", "src/components/home/HeroBand.tsx"),
    absent("S5-no-home-tsx", "src/components/home/Home.tsx"),
]
HOME_SSR = ["Khuyến mãi nổi bật", "Chọn khuyến mãi", "Tất cả", "PG Soft", "Baccarat Kim Cương", "Thể thao",
            "Kèo bóng đá trực tiếp", "TRỰC TIẾP", "Cược ngay", 'href="/?v=sports&amp;m=sm-live-1"']
C["S6"] = [
    lacks("S6-no-search-params", "searchParams", "src/app/page.tsx"),
    has("S6-loading-copy", "Đang tải trang chủ", "src/app/loading.tsx"),
    absent("S6-no-root-error-files", "src/app/not-found.tsx", "src/app/error.tsx", "src/app/global-error.tsx"),
    absent("S6-dead-bands", *[f"src/components/home/{n}.tsx" for n in DEAD_HOME]),
    lacks("S6-barrel-no-dead", r"^export .*\b(" + "|".join(DEAD_HOME) + r")\b", "src/components/home/index.ts"),
    serve("dev", "/", "/?v=casino"),
    code("S6-home-200", "/", "200"),
    code("S6-v-200", "/?v=casino", "200"),
    same_main("S6-v-same-main", "/", "/?v=casino"),
] + [html(f"S6-ssr-{k + 1}", "/", s) for k, s in enumerate(HOME_SSR)]
KICKERS = ["Sòng bài trực tiếp đẳng cấp", "Quay là trúng, nổ hũ mỗi ngày", "Kèo bóng đá & thể thao trực tiếp", "Săn cá thưởng lớn",
           "Game bài dân gian quen thuộc", "Xổ số & lô đề đa dạng", "Trường gà trực tiếp", "Bàn chơi cổ điển", "Game nhanh giải trí tức thì"]
C["S7"] = strings("S7-kicker", KICKERS, "src/components/category/CategoryBanner.tsx") + [
    has("S7-loading", "Đang tải hạng mục", "src/app/[vertical]/loading.tsx"),
] + strings("S7-copy", ["Tìm trò chơi", "Tên A→Z", "Không tìm thấy trò chơi phù hợp."], "src/components/category", "src/lib/i18n.ts") + [
    absent("S7-no-vertical-folder", "src/components/vertical"),
    serve("dev", *[f"/{s}" for s, _ in VERTICALS], "/foo"),
] + sum([[code(f"S7-{s}-200", f"/{s}", "200"), html(f"S7-{s}-title", f"/{s}", f"<title>{lab} — Yaobet</title>")] for s, lab in VERTICALS], []) + [
    html("S7-sports-live", "/sports", "Trận đấu trực tiếp"),
] + [nohtml(f"S7-{s}-no-live", f"/{s}", "Trận đấu trực tiếp") for s, _ in VERTICALS if s != "sports"] + [
    code("S7-foo-404", "/foo", "404"),
    html("S7-foo-copy", "/foo", "Không tìm thấy hạng mục"),
    html("S7-foo-title", "/foo", "<title>Không tìm thấy — Yaobet</title>"),
]
PR = [f"/khuyen-mai/pr{i}" for i in range(1, 10)]
C["S8"] = [
    absent("S8-no-detail-not-found", "src/app/khuyen-mai/[id]/not-found.tsx"),
    absent("S8-no-loading", "src/app/khuyen-mai/loading.tsx"),
    serve("dev", "/khuyen-mai", *PR),
    code("S8-list-200", "/khuyen-mai", "200"),
    html("S8-list-title", "/khuyen-mai", "<title>Khuyến mãi — Yaobet</title>"),
] + [html(f"S8-list-s{k + 1}", "/khuyen-mai", s) for k, s in enumerate(["Tất cả khuyến mãi", "Xem chi tiết", "Lọc khuyến mãi theo danh mục", "Kết thúc sau"])] + sum(
    [[code(f"S8-pr{i}-200", f"/khuyen-mai/pr{i}", "200"), html(f"S8-pr{i}-title", f"/khuyen-mai/pr{i}", "<title>Yaobet</title>")] for i in range(1, 9)], []) + [
    code("S8-pr9-404", "/khuyen-mai/pr9", "404"),
    html("S8-pr9-default", "/khuyen-mai/pr9", "This page could not be found."),
    html("S8-detail-join", "/khuyen-mai/pr1", "Tham gia ngay"),
    html("S8-detail-info", "/khuyen-mai/pr1", "Thông tin chương trình"),
]
C["U6"] = strings("U6", ["Tỷ lệ tính cược theo trò chơi", "Tìm tên trò chơi…", "Gõ không dấu cũng được (vd: no hu)", "Tìm trò chơi cần có mạng.",
                         "Xóa nội dung tìm kiếm", "Chúng tôi chưa khớp được tên bạn gõ.", "Vẫn chưa rõ? Xem Trợ giúp",
                         "Không có trò chơi nào khớp với bộ lọc đang chọn.", "Phân trang danh sách trò chơi",
                         "Tỷ lệ có thể thay đổi, chúng tôi báo trước 30 ngày.",
                         "0% — vẫn chơi bình thường, chỉ là cược không cộng vào cược hợp lệ."], "src/components/contribution", "src/lib/i18n.ts") + [
    has("U6-debounce", "DEBOUNCE_MS = 250", "src/components/contribution"),
    has("U6-page-size", "PAGE_SIZE = 25", "src/components/contribution"),
    has("U6-search-id", "contribution-search", "src/components/contribution"),
    has("U6-noscript", "<noscript>", "src/components/contribution"),
    hasre("U6-border-separate", "border-collapse:separate|border-separate", "src/components/contribution/RateTable.tsx"),
]
ACC = "src/components/account"
C["U3"] = strings("U3", ["Nhận huy hiệu", "Đã sao chép", "Nạp tích lũy", "Số dư: 0 ₫", "Cửa hàng điểm", "Trung tâm nhiệm vụ", "Chờ mở khóa",
                         "Thăng hạng toàn dân", "Bạn có chắc muốn đăng xuất khỏi tài khoản?", "Huỷ", "Hồ sơ cá nhân", "Trung tâm an toàn",
                         "Điểm an toàn", "Đây là bản giao diện mẫu — chưa kết nối hệ thống.", "Liên kết thẻ ngân hàng", "Địa chỉ ví", "Mặc định"],
                  ACC, "src/lib/i18n.ts") + [
    has("U3-title", "Tài khoản — Yaobet", "src/app/(member)/tai-khoan/page.tsx"),
    hasre("U3-sidebar-clip", r"polygon\(0[ _]0", f"{ACC}/MemberSidebar.tsx", "src/styles/areas/member.css"),
    has("U3-page-bloom", "page-bloom", "src/app/(member)/layout.tsx", "src/styles/areas/member.css"),
    count("U3-member-keyframes", "eq", 2, r"@keyframes (pulseDot|progressShimmer)\b", "src/styles/areas/member.css"),
    absent("U3-dead-account", *[f"{ACC}/{n}.tsx" for n in DEAD_ACCOUNT]),
    lacks("U3-no-dead-exports", r"^export .*\b(ProfileHeader|QuickActions|AccountMenu|LogoutMenuItem)\b", f"{ACC}/index.ts"),
    lacks("U3-no-logout-menu-item", r"export function LogoutMenuItem\b", f"{ACC}/LogoutButton.tsx"),
    serve("dev", "/tai-khoan", "/bao-mat", "/lich-su"),
    code("U3-account-200", "/tai-khoan", "200"),
    code("U3-bao-mat-307", "/bao-mat", "307"), loc("U3-bao-mat-target", "/bao-mat", "/tai-khoan"),
    code("U3-lich-su-307", "/lich-su", "307"), loc("U3-lich-su-target", "/lich-su", "/tai-khoan"),
]
WAL = "src/components/wallet"
C["U4"] = strings("U4", ["Mục ví tiền", "Chọn hình thức nạp", "Số tiền gợi ý", "Tôi đã chuyển", "Nạp thẻ cào", "Đang chờ xác nhận", "Yêu cầu rút tiền",
                         "Số tiền vượt quá số dư khả dụng.", "Quỹ nguồn và quỹ đích phải khác nhau.", "Đổi chiều chuyển", "Lọc giao dịch",
                         "Chưa có giao dịch"], WAL, "src/lib/i18n.ts") + [
    has("U4-title", "Ví tiền — Yaobet", "src/app/(member)/vi-tien"),
    has("U4-fund-amount", "{formatVnd(f.amount)} ₫", f"{WAL}/FundTransferPanel.tsx"),
    lacks("U4-tabs-no-keys", "onKeyDown", f"{WAL}/WalletTabs.tsx"),
    has("U4-tab-ids", "wallet-tab-", f"{WAL}/WalletTabs.tsx"),
    hasre("U4-tabs-420", "max-width: ?420px|max-420", f"{WAL}/WalletTabs.tsx", "src/styles/areas/member.css"),
    serve("dev", "/vi-tien"), code("U4-wallet-200", "/vi-tien", "200"),
]
C["U5"] = strings("U5", ["Đánh dấu đã đọc tất cả", "Xóa tất cả", "Lọc tin nhắn", "Đã đọc tất cả", "Chưa có tin nhắn", "Tổng quan thưởng", "Công cụ mời bạn bè",
                         "Lưu mã QR", "Hoa hồng giới thiệu", "Chi tiết hoạt động", "Cách hoạt động", "Cấp đại lý", "Đại lý Bạch kim",
                         "Hoa hồng theo điều khoản chương trình"], "src/components/messages", "src/components/referral", "src/lib/i18n.ts") + [
    has("U5-title-msg", "Tin nhắn — Yaobet", "src/app/(member)/tin-nhan"),
    has("U5-title-ref", "Giới thiệu bạn bè — Yaobet", "src/app/(member)/gioi-thieu"),
    has("U5-title-agent", "Đại lý — Yaobet", "src/app/(member)/dai-ly"),
    hasre("U5-agent-level", r"currentLevel=\{0\}", "src/app/(member)/dai-ly/page.tsx"),
    has("U5-poster", "/assets/placeholders/poster.svg", "src/components/referral", "src/lib"),
    serve("dev", "/tin-nhan", "/gioi-thieu", "/dai-ly"),
    code("U5-msg-200", "/tin-nhan", "200"), code("U5-ref-200", "/gioi-thieu", "200"), code("U5-agent-200", "/dai-ly", "200"),
]
UTIL = [("/ho-tro", "Hỗ trợ khách hàng", "Hỗ trợ — Yaobet"), ("/tro-giup", "Trung tâm trợ giúp", "Trung tâm trợ giúp — Yaobet"),
        ("/tai-app", "Tải ứng dụng", "Tải ứng dụng — Yaobet"), ("/phong-cach", "Phong cách", "Phong cách — Yaobet")]
C["U7"] = [
    has("U7-scroll-hint", "Danh sách game hạn chế — vuốt ngang để xem thêm cột", "src/components/restricted", "src/lib/i18n.ts"),
    absent("U7-no-utility-folder", "src/components/utility"),
] + [hasre(f"U7-stub-{r[1:]}", r"\bstub-page\b", f"src/app{r}/page.tsx") for r, _, _ in UTIL] + [
    serve("dev", "/cuoc-hop-le", "/cuoc-hop-le?tab=han-che", "/game-han-che", "/hoan-tra", *[r for r, _, _ in UTIL]),
    code("U7-rates-200", "/cuoc-hop-le", "200"),
    html("U7-rates-copy", "/cuoc-hop-le", "Tỷ lệ tính cược theo trò chơi"),
    html("U7-rates-title", "/cuoc-hop-le", "<title>Tỷ lệ tính cược theo trò chơi — Yaobet</title>"),
    code("U7-restricted-200", "/cuoc-hop-le?tab=han-che", "200"),
    html("U7-restricted-copy", "/cuoc-hop-le?tab=han-che", "Game hạn chế trong khuyến mãi"),
    html("U7-stamp-rates", "/cuoc-hop-le", "09/08/2026 09:30"),
    html("U7-stamp-restricted", "/cuoc-hop-le?tab=han-che", "08/08/2026 10:00"),
    code("U7-ghc-307", "/game-han-che", "307"), loc("U7-ghc-target", "/game-han-che", "/cuoc-hop-le?tab=han-che"),
    code("U7-hoan-tra-307", "/hoan-tra", "307"), loc("U7-hoan-tra-target", "/hoan-tra", "/khuyen-mai"),
] + sum([[code(f"U7-{r[1:]}-200", r, "200"), html(f"U7-{r[1:]}-h1", r, h1), html(f"U7-{r[1:]}-title", r, f"<title>{t}</title>")] for r, h1, t in UTIL], [])
VIPS = ["src/components/vip", "src/lib/vip", "src/app/vip"]
C["R3"] = strings("R3", ["Hành trình VIP", "Bạn ở đây", "Cược tuần", "Làm sao để thăng hạng VIP?"], *VIPS) + [
    has("R3-ring-grad", "vipRingGrad", "src/components/vip/LevelRing.tsx"),
    has("R3-drag", "DRAG_PER_CARD = 120", "src/components/vip/TierDeck.tsx"),
    has("R3-page-bg-token", "vip-page-bg", "src/styles/tokens.css"),
    count("R3-hero-bg-classes", "ge", 2, r"^\s*\.vip-hero-(guest|member)-bg\b", "src/styles/areas/vip.css"),
    serve("dev", "/vip"), code("R3-vip-200", "/vip", "200"),
]
C["R4"] = strings("R4", ["Bậc thang VIP", "Vòng cược lên hạng kế tiếp", "Chương trình câu lạc bộ đại lý sẽ sớm ra mắt.", "Tích lũy bằng vòng cược"],
                  "src/components/vip", "src/lib/vip", "src/app/tier", "src/app/cau-lac-bo") + [
    has("R4-tier-link", 'href="/vip"', "src/app/tier/page.tsx"),
    hasre("R4-club-stub", r"\bstub-page\b", "src/app/cau-lac-bo/page.tsx"),
    absent("R4-no-stub-component", "src/components/utility"),
    serve("dev", "/tier", "/cau-lac-bo"), code("R4-tier-200", "/tier", "200"), code("R4-club-200", "/cau-lac-bo", "200"),
]
C["R5"] = strings("R5", ["Điểm tích lũy của bạn", "Thiếu", "Hết lượt đổi", "Xác nhận đổi quà", "Đổi quà thành công", "Cập nhật lần cuối · —"],
                  "src/components/store", "src/lib/store", "src/lib/i18n.ts") + [
    has("R5-redeem-timeout", "setTimeout", "src/components/store/RedeemDialog.tsx"),
    hasre("R5-redeem-600", r"\b600\b", "src/components/store/RedeemDialog.tsx"),
    serve("dev", "/cua-hang"), code("R5-store-200", "/cua-hang", "200"),
]
C["R6"] = strings("R6", ["Tỷ lệ công bố", "Cào để mở", "Mở tất cả", "Buộc kết quả", "Bù thẻ không trúng"], "src/components/lottery", "src/lib/mock/lottery.ts") + [
    has("R6-threshold", "CLEAR_THRESHOLD = 0.58", "src/components/lottery"),
    has("R6-data-token", "data-token", "src/components/lottery"),
    hasre("R6-token-pulse", r"@keyframes token-pulse\b", "src/styles/areas/lottery.css"),
] + [has(f"R6-runtime-token{k + 1}", n, "src/components/lottery") for k, n in enumerate(["--brand-accent", "--brand-accent-2", "--canvas", "--text-hi"])] + [
    serve("dev", "/ve-so"), code("R6-lottery-200", "/ve-so", "200"),
]
C["R7"] = strings("R7", ["BỘ SƯU TẬP", "Lượt mở còn lại: ", "MỞ TIẾP", "Xác nhận · dùng", "Đang chuyển vào ví…"], "src/components/collection") + [
    hasre("R7-foil-sweep", r"@keyframes card-foil-sweep\b", "src/styles/areas/collection.css"),
    lacks("R7-no-bare-sweep", r"@keyframes sweep\b", "src/styles/areas/collection.css"),
    hasre("R7-bob", r"@keyframes bob\b", "src/styles/areas/collection.css"),
    serve("dev", "/bo-suu-tap"), code("R7-collection-200", "/bo-suu-tap", "200"),
]
C["R8"] = strings("R8", ["Bạn đang giữ", "Chưa có thẻ nào", "Tỷ lệ ra thẻ khi mở cho bộ:"], "src/components/collection") + [
    has("R8-dev-title", "Collection ports — harness", "src/app/dev/collection-ports/page.tsx"),
    has("R8-suspense", "Suspense", "src/app/bo-suu-tap/cua-toi/page.tsx"),
    serve("dev", "/bo-suu-tap/cua-toi", "/bo-suu-tap/cua-toi?tab=lich-su", "/dev/collection-ports"),
    code("R8-mine-200", "/bo-suu-tap/cua-toi", "200"), code("R8-history-200", "/bo-suu-tap/cua-toi?tab=lich-su", "200"),
    code("R8-dev-200", "/dev/collection-ports", "200"),
]
C["F4"] = [
    'eq F4-file-count 36 "$(rg --files --hidden --no-ignore public | wc -l | tr -d " ")"',
    'n=0; while IFS= read -r f; do cmp -s "$ORIG_WEB/$f" "$f" || { fail F4-byte-equal "$f equal to the original" "differs or missing"; n=1; }; done < <(cd "$ORIG_WEB" && rg --files --hidden --no-ignore public); [ $n -eq 0 ] && ok',
    'eq F4-logo-size 5859 "$(wc -c < public/assets/logo.svg | tr -d " ")"',
    absent("F4-no-old-assets", "public/assets/images", "public/placeholders"),
]
C["F5"] = [
    count("F5-font-subsets", "eq", 2, r'^\s*subsets: \["latin", "vietnamese"\],', "src/app/layout.tsx"),
    'eq F5-favicon-size 25931 "$(wc -c < src/app/favicon.ico | tr -d " ")"',
    'cmp -s "$ORIG_WEB/src/app/favicon.ico" src/app/favicon.ico && ok || fail F5-favicon-bytes "byte-equal to the original" differs',
    has("F5-shell-import", 'from "@/components/layout"', "src/app/layout.tsx"),
    has("F5-rail-import", 'from "@/components/layout/QuickActionRail"', "src/app/layout.tsx"),
    run("F5-fonts", "CHECKS OK fonts", "bash", "$CHECKS_DIR/fonts-preflight.sh"),
]
S2_SSR = ['aria-label="Danh mục"', 'aria-label="Tiện ích"', 'aria-label="Ví tiền"', "Danh mục trò chơi", "Điều hướng chính", "Trang chủ",
          "Tài khoản", "Bộ sưu tập", "Phong cách", "CLB", "Nạp", 'href="/dai-ly"', 'href="/cau-lac-bo"']
S3_SSR = ["Đối tác", "Về chúng tôi", "Tải ứng dụng", "Thao tác nhanh", "8.688.888.000 ₫", "Quay ngay", "Thông tin trực tiếp", "Bảng xếp hạng"]
C["I1"] = [
    'npm run build > /tmp/yb-build-I1.log 2>&1 && ok || fail I1-build "npm run build exit 0" "see /tmp/yb-build-I1.log"',
    run("I1-built-css", "CHECKS OK built-css", "bash", "$CHECKS_DIR/built-css.sh"),
    serve("dev", "/", "/tai-app", "/cuoc-hop-le"),
    html("I1-F5-html-attrs", "/", 'lang="vi" data-brand="yaobet" data-theme="obsidian"'),
    html("I1-F5-title", "/", "<title>Yaobet</title>"),
    html("I1-F5-description", "/", "Yaobet — nhà cái trực tuyến."),
    html("I1-F5-theme-color", "/", 'content="#0a0a0a"'),
] + [html(f"I1-S2-ssr-{k + 1}", "/", s) for k, s in enumerate(S2_SSR)] + [
    'cmp_num I1-S2-tier2-raw-anchors ge 9 "$(page_count /tai-app \'<a href="/?v=\')" "raw /?v= anchors on /tai-app"',
] + [html(f"I1-S3-ssr-{k + 1}", "/", s) for k, s in enumerate(S3_SSR)] + [
    nohtml("I1-S3-rail-suppressed", "/cuoc-hop-le", "Thao tác nhanh"),
    html("I1-S5-dev-toggle-dev", "/", "chuyển trạng thái đăng nhập"),
    'PORT=$((PORT + 1))',
    serve("start", "/"),
    nohtml("I1-S5-no-dev-toggle-prod", "/", "chuyển trạng thái đăng nhập"),
    html("I1-S5-prod-page", "/", "<title>Yaobet</title>"),
    'PORT=$((PORT - 1))',
    run("I1-S2-boxes", "BOXES OK", "node", "scripts/with-dev-server.mjs", "--port", "$PORT", "--", "node", "scripts/box-check.mjs", "--boxes", f"{CK}/boxes.json"),
    run("I1-S4-auth-flow", "AUTH FLOW OK 5/5", "node", "scripts/with-dev-server.mjs", "--port", "$PORT", "--", "node", "scripts/auth-flow.mjs"),
]
assert set(C) == set(ids), set(ids) ^ set(C)

LIB_SH = r'''#!/usr/bin/env bash
# Shared helpers for the leaf checks. Generated by .unlazy/yaobet-rebuild/genplan.py; do not edit.
# Contract: each failure prints "Fail: <id> | Expected: <A> | Got: <B>"; finish prints
# "CHECKS OK <leaf> n/n" and exits 0 only when every check ran and passed.
set -u
CHECKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${CHECK_ROOT:-$(git -C "$CHECKS_DIR" rev-parse --show-toplevel 2>/dev/null)}"
ORIG_WEB="${ORIG_WEB:-__ORIG__}"
cd "$ROOT" || { echo "Fail: setup | Expected: repo root | Got: '$ROOT'"; exit 2; }
LEAF="${LEAF:?LEAF must be set}"
PORT="${PORT:-0}"
N_OK=0; N_FAIL=0; N_SKIP=0; SERVED=0; PAGES=""
TMPD="$(mktemp -d "${TMPDIR:-/tmp}/yb-check-$LEAF.XXXXXX")"
trap 'rm -rf "$TMPD"' EXIT

ok() { N_OK=$((N_OK + 1)); }
fail() { printf 'Fail: %s | Expected: %s | Got: %s\n' "$1" "$2" "$3"; N_FAIL=$((N_FAIL + 1)); }
need() { local id=$1 p; shift; for p in "$@"; do [ -e "$p" ] || { fail "$id" "path $p exists" "missing"; return 1; }; done; }
eq() { if [ "$3" = "$2" ]; then ok; else fail "$1" "$2" "$3"; fi; }
nonempty() { if [ -n "$2" ]; then ok; else fail "$1" "a value" "empty"; fi; }
cmp_num() { if [ "${4:-x}" -"$2" "$3" ] 2>/dev/null; then ok; else fail "$1" "$5 $2 $3" "${4:-none}"; fi; }
contains() { case "$3" in *"$2"*) ok ;; *) fail "$1" "output contains '$2'" "$(printf '%s' "$3" | head -c 160)" ;; esac; }
not_contains() { case "$3" in *"$2"*) fail "$1" "output without '$2'" "present" ;; *) ok ;; esac; }
lines_matching() { printf '%s\n' "$1" | rg -c -e "$2" || echo 0; }
has() { local id=$1 s=$2; shift 2; need "$id" "$@" || return 0; if rg -q -F -- "$s" "$@"; then ok; else fail "$id" "'$s' in $*" "absent"; fi; }
hasre() { local id=$1 s=$2; shift 2; need "$id" "$@" || return 0; if rg -q -e "$s" -- "$@"; then ok; else fail "$id" "/$s/ in $*" "absent"; fi; }
hasline() { need "$1" "$3" || return 0; if rg -q -x -F -- "$2" "$3"; then ok; else fail "$1" "line '$2' in $3" "absent"; fi; }
lacks() { local id=$1 s=$2 hit; shift 2; need "$id" "$@" || return 0; hit=$(rg -n -m 3 -e "$s" -- "$@" | head -n 3 | tr '\n' ' '); if [ -z "$hit" ]; then ok; else fail "$id" "no match for /$s/" "$hit"; fi; }
lacksF() { local id=$1 s=$2 hit; shift 2; need "$id" "$@" || return 0; hit=$(rg -n -m 3 -F -- "$s" "$@" | head -n 3 | tr '\n' ' '); if [ -z "$hit" ]; then ok; else fail "$id" "no '$s'" "$hit"; fi; }
count() { local id=$1 op=$2 n=$3 s=$4 got; shift 4; need "$id" "$@" || return 0; got=$(rg -c --no-filename -e "$s" -- "$@" | awk '{t += $1} END {print t + 0}'); cmp_num "$id" "$op" "$n" "$got" "lines matching /$s/"; }
present() { need "$@" && ok; }
absent() { local id=$1 p; shift; for p in "$@"; do if [ -e "$p" ]; then fail "$id" "$p absent" "present"; return 0; fi; done; ok; }
run() { local id=$1 exp=$2 out rc; shift 2; out=$("$@" 2>&1); rc=$?; if [ $rc -eq 0 ] && case "$out" in *"$exp"*) true ;; *) false ;; esac; then ok; else fail "$id" "exit 0 and '$exp'" "exit $rc: $(printf '%s' "$out" | tail -n 3 | tr '\n' ' ' | head -c 240)"; fi; }
fails() { local id=$1; shift; if "$@" >/dev/null 2>&1; then fail "$id" "non-zero exit" "exit 0"; else ok; fi; }
sha256_list() { if command -v shasum >/dev/null; then shasum -a 256 "$@"; else sha256sum "$@"; fi | awk '{print $1}' | LC_ALL=C sort | tr '\n' ' '; }

TS_RUNNER=$(cat <<'JS'
import { registerHooks } from "node:module";
import { existsSync, statSync } from "node:fs";
import { pathToFileURL, fileURLToPath } from "node:url";
import path from "node:path";
const SRC = path.resolve(process.cwd(), "src");
const EXT = ["", ".ts", ".tsx", "/index.ts", "/index.tsx"];
const isFile = (f) => existsSync(f) && statSync(f).isFile();
const tryFile = (b) => { for (const e of EXT) if (isFile(b + e)) return b + e; return null; };
registerHooks({ resolve(spec, ctx, next) {
  let base = null;
  if (spec.startsWith("@/")) base = path.join(SRC, spec.slice(2));
  else if ((spec.startsWith("./") || spec.startsWith("../")) && ctx.parentURL && ctx.parentURL.startsWith("file:"))
    base = path.resolve(path.dirname(fileURLToPath(ctx.parentURL)), spec);
  if (base) { const f = tryFile(base); if (f) return { url: pathToFileURL(f).href, format: "module-typescript", shortCircuit: true }; }
  return next(spec, ctx);
} });
const load = (p) => import(pathToFileURL(path.resolve(p)).href);
const AF = Object.getPrototypeOf(async () => {}).constructor;
const out = await new AF("load", process.env.BODY)(load);
console.log(typeof out === "string" ? out : JSON.stringify(out));
JS
)
ts() { local got; got=$(BODY="$3" node --no-warnings --input-type=module -e "$TS_RUNNER" 2>&1 | tail -n 1); eq "$1" "$2" "$got"; }

# Served checks: fetch every URL once under scripts/with-dev-server.mjs, then assert on the saved pages.
serve() {
  local mode=$1 port=$2; shift 2
  PAGES="$TMPD/pages-$mode-$port"; mkdir -p "$PAGES"; printf '%s\n' "$@" > "$PAGES/urls"
  if [ -n "${SKIP_SERVE:-}" ]; then SERVED=0; N_SKIP=$((N_SKIP + 1)); return 0; fi
  need "serve-$mode" scripts/with-dev-server.mjs || { SERVED=0; return 0; }
  if node scripts/with-dev-server.mjs --port "$port" --mode "$mode" -- bash "$CHECKS_DIR/fetch.sh" "$PAGES" > "$TMPD/serve.log" 2>&1; then
    SERVED=1; ok
  else
    SERVED=0; fail "serve-$mode:$port" "with-dev-server exit 0" "$(tail -n 3 "$TMPD/serve.log" | tr '\n' ' ' | head -c 240)"
  fi
}
_pg() { awk -v u="$1" '$0 == u { print NR; exit }' "$PAGES/urls"; }
_skip() { [ -n "${SKIP_SERVE:-}" ] && { N_SKIP=$((N_SKIP + 1)); return 0; }; return 1; }
code() { _skip && return 0; local n; n=$(_pg "$2"); eq "$1" "$3" "$(cut -d' ' -f1 "$PAGES/$n.meta" 2>/dev/null || echo none)"; }
loc() { _skip && return 0; local n got; n=$(_pg "$2"); got=$(cut -d' ' -f2- "$PAGES/$n.meta" 2>/dev/null); case "$got" in *"$3") ok ;; *) fail "$1" "redirect to ...$3" "${got:-none}" ;; esac; }
html() { _skip && return 0; local n; n=$(_pg "$2"); if rg -q -F -- "$3" "$PAGES/$n.html" 2>/dev/null; then ok; else fail "$1" "'$3' in $2" "absent"; fi; }
nohtml() { _skip && return 0; local n; n=$(_pg "$2"); [ -s "$PAGES/$n.html" ] || { fail "$1" "page $2 fetched" "empty"; return 0; }; if rg -q -F -- "$3" "$PAGES/$n.html"; then fail "$1" "no '$3' in $2" "present"; else ok; fi; }
page_count() { local n; n=$(_pg "$1"); rg -o -F -- "$2" "$PAGES/$n.html" 2>/dev/null | wc -l | tr -d ' '; }
_main() { perl -0777 -ne 'print $1 if /(<main\b.*?<\/main>)/s' "$1" 2>/dev/null; }
same_main() { _skip && return 0; local a b; a=$(_main "$PAGES/$(_pg "$2").html"); b=$(_main "$PAGES/$(_pg "$3").html"); if [ -n "$a" ] && [ "$a" = "$b" ]; then ok; else fail "$1" "identical <main> on $2 and $3" "differs or empty"; fi; }

finish() {
  local n=$((N_OK + N_FAIL))
  if [ "$N_SKIP" -gt 0 ]; then echo "CHECKS PARTIAL $LEAF $N_OK/$n ($N_SKIP served checks skipped; never a pass)"; exit 1; fi
  if [ "$N_FAIL" -eq 0 ] && [ "$N_OK" -gt 0 ]; then echo "CHECKS OK $LEAF $N_OK/$n"; exit 0; fi
  echo "CHECKS FAILED $LEAF $N_FAIL/$n"; exit 1
}
'''.replace("__ORIG__", ORIG)

FETCH_SH = '''#!/usr/bin/env bash
# Fetch each URL in <dir>/urls from $BASE (exported by scripts/with-dev-server.mjs). Generated; do not edit.
set -u
D=$1; B="${BASE:?with-dev-server must export BASE}"; i=0
while IFS= read -r u; do
  i=$((i + 1))
  curl -s -o "$D/$i.html" -w '%{http_code} %{redirect_url}' --max-time 180 "$B$u" > "$D/$i.meta" 2>/dev/null || echo "000 " > "$D/$i.meta"
done < "$D/urls"
'''

def script(leaf, title, body):
    return (f"#!/usr/bin/env bash\n# {title}\n# Generated by .unlazy/yaobet-rebuild/genplan.py; do not edit by hand.\n"
            f"LEAF={leaf}; PORT={PORT.get(leaf, 0)}\n. \"$(dirname \"${{BASH_SOURCE[0]}}\")/lib.sh\"\n\n"
            + "\n".join(body) + "\n\nfinish\n")

def write(rel, text, mode=None, once=False):
    p = os.path.join(HERE, rel)
    if once and os.path.exists(p):
        return
    open(p, "w").write(text)
    if mode:
        os.chmod(p, mode)

write("checks/lib.sh", LIB_SH, 0o755)
write("checks/fetch.sh", FETCH_SH, 0o755)
for l in L:
    i, w, title, rev, row = l[:5]
    src = f"`{row}` row of review/{rev}.md (leaves table)" if i != "I1" else "the deferred rows of every leaf"
    write(f"checks/{i}.sh", script(i, f"Leaf {i} ({title}): mechanised acceptance checks from {src}, with PM-RULINGS and leaf-note normalisations.", C[i]), 0o755)

TAGS = (r"\b(SPEC|GC|BR|UT|ST|FR|DEFECT|CASE|UC|NFR|AC|OD|SH|UIM|FC|REWARDS|ADR|RG)-[0-9]+\b|\bJ[0-9]+\b|\bWave [0-9]"
        r"|\bruling [A-Z][0-9]+\b|\bPR-[0-9]{2}\b|\bleaf-[A-Z][0-9]")
LEGAL = r"decree|nghị định|giấy phép|statute|regulat|licen[cs]|complian|pháp luật|thông tư"
write("checks/census.sh", script("census", "CSS file census: src/ holds exactly the planned CSS files (ADR-002 §1, PLAN-GATE item 15).", [
    'eq census-css ' + q(" ".join(CSS_CENSUS) + " ") + ' "$(rg --files src -g "*.css" | LC_ALL=C sort | tr "\\n" " ")"',
]), 0o755)
write("checks/fonts-preflight.sh", script("fonts", "Google Fonts reachability from the build environment (PR-35). next build fails without it; next dev silently falls back.", [
    'UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"',
    'c1=$(curl -s -o "$TMPD/css" -m 20 -A "$UA" -w "%{http_code}" "https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro&family=Montserrat&display=swap" || true)',
    'eq fonts-css 200 "$c1"',
    'u=$(rg -o -m 1 "https://fonts.gstatic.com/[^)]+\\.woff2" "$TMPD/css" 2>/dev/null | head -n 1)',
    'c2=$(curl -s -o /dev/null -m 20 -w "%{http_code}" "${u:-https://fonts.gstatic.com/}" || true)',
    'eq fonts-woff2 200 "$c2"',
]), 0o755)
WOFF2 = ("0b00fbd6edcc84cd5f77364bbeb06b75ed263c740061eba34511f1e2ac1a82d3 141f6c45010274d7d3625d0554476ec1161274d9eb09a38135977ea1b2b84895 "
         "14950d0af319bbc1f7a26ed08bf1ba7a9e18324111056bb0c81eef0983a931c0 6438d7b8ea9c7c3992d5e2fd2afdb1ff948570a3ef0bedae76247b51632960ba "
         "744830a0e77dd14dd543a4230d6e3ce67ca961634074b5d536ebafc66c732301 843908240371827470dd178e284ffbbeb85f1563bf47e5b9c9db58526fb7f6e0 "
         "90c10a1f4fdd8aa634b70bfc22ca991f12bba15b1661ea2390443e31888e1f5b 920711de9ae96c18970fa4faca73cd302b93ac5ed57ebeb6bfec2ddeff930082 "
         "9e2672d100bc36a37073fb250abfaa7394f5151bf5dda3f4d5fc281345eb391b b0d9b8aec7f47207ce4065be34286203e0741c8329be6d05986b149f991f84c1 "
         "c2ae124f149371e1b6209cbba234852310caeee3c32990a56ccb93ac1c7edb9a cf841d2b615f068e77a918114f44c17d51d0b73314fdff81eae95f528387c391 "
         "d25f70ff7404fddbeb150c9c687bf37069468a5cdf59117b2a30226d1ebfa5c0 f446d28e986c5695283afcb13a7719dabd9f2cec28ab49ecb43a328efa009f05 ")
write("checks/built-css.sh", script("built-css", "Built-CSS checks after npm run build: F1 deferred row, PR-13 runtime token names, vietnamese subset, font drift.", [
    'need built-css-build .next/BUILD_ID .next/static || finish',
    'BC=(rg --no-ignore --hidden -g "*.css")',
    '"${BC[@]}" -q -F -- "--canvas:#0a0a0a" .next/static && ok || fail F1-built-canvas "--canvas:#0a0a0a in .next/static CSS" absent',
    'eq F1-built-no-spacing-var 0 "$("${BC[@]}" -c --no-filename -e "var\\(--spacing\\)" .next/static | awk \'{t+=$1} END {print t+0}\')"',
    'for n in --brand-accent --brand-accent-2 --canvas --text-hi; do "${BC[@]}" -q -F -- "$n:" .next/static && ok || fail "PR13-$n" "$n: declared in the built CSS" absent; done',
    '"${BC[@]}" -q -e "U\\+1EA0-1EF9" .next/static && ok || fail A7-vietnamese-subset "unicode-range with U+1EA0-1EF9" absent',
    'eq fonts-woff2-unchanged ' + q(WOFF2) + ' "$(sha256_list .next/static/media/*.woff2)"',
]), 0o755)
write("checks/hygiene.sh", script("hygiene", "A11 hygiene: tag families and legal terms in src/ (minus PM-approved a11-allow.txt lines), exact dependency set, no runtime artefacts.", [
    f'TAGS={q(TAGS)}', f'LEGAL={q(LEGAL)}',
    '{ rg -n -e "$TAGS" src; rg -n -i -e "$LEGAL" src; } > "$TMPD/hits" 2>/dev/null || true',
    'bad=0; while IFS= read -r h; do f=${h%%:*}; allowed=0; while IFS=$(printf "\\t") read -r af as; do case "$af" in ""|"#"*) continue ;; esac; [ "$f" = "$af" ] && case "$h" in *"$as"*) allowed=1 ;; esac; done < "$CHECKS_DIR/a11-allow.txt"; [ $allowed -eq 1 ] || { fail hygiene-term "no tag or legal term" "$h"; bad=1; }; done < "$TMPD/hits"; [ $bad -eq 0 ] && ok',
    'eq hygiene-deps "next,react,react-dom" "$(jq -r \'.dependencies|keys|join(",")\' package.json)"',
    'eq hygiene-dev-deps "@tailwindcss/turbopack,@types/node,@types/react,@types/react-dom,eslint,eslint-config-next,playwright,tailwindcss,typescript" "$(jq -r \'.devDependencies|keys|join(",")\' package.json)"',
    'eq hygiene-playwright-pin 1.61.1 "$(jq -r \'.devDependencies.playwright\' package.json)"',
    'eq hygiene-artefacts "" "$(git ls-files | rg -e "\\.(log|sqlite|db|tsbuildinfo)$|(^|/)\\.?shots/|__pycache__" || true)"',
]), 0o755)
write("checks/no-dev-toggle.sh", script("no-dev-toggle", "A9a: the production home page has no DEV toggle (run under with-dev-server --mode start).", [
    'curl -s --max-time 120 "${BASE:?}/" > "$TMPD/home.html"',
    has("A9-prod-page", "<title>Yaobet</title>", "$TMPD/home.html"),
    lacksF("A9-no-dev-toggle", "chuyển trạng thái đăng nhập", "$TMPD/home.html"),
]), 0o755)
write("checks/lease.sh", '''#!/usr/bin/env bash
# Lease gate: every path the branch adds, changes, deletes or leaves untracked is inside checks/owns/<leaf>.txt.
# Entries are exact paths or dir/** prefixes (genplan.py asserts this form). Generated; do not edit.
set -u
LEAF=${1:?leaf id}; DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; OWNS="$DIR/owns/$LEAF.txt"
cd "$(git -C "$DIR" rev-parse --show-toplevel)" || exit 2
base=$(git merge-base "${LEASE_BASE:-main}" HEAD) || { echo "Fail: lease-$LEAF | Expected: a merge-base with ${LEASE_BASE:-main} | Got: none"; exit 1; }
paths=$( { git diff --name-only "$base" HEAD; git diff --name-only HEAD; git ls-files --others --exclude-standard; } | LC_ALL=C sort -u)
bad=0; n=0
while IFS= read -r p; do
  [ -z "$p" ] && continue; n=$((n + 1)); hit=0
  while IFS= read -r o; do
    [ -z "$o" ] && continue
    case "$o" in */\\*\\*) pre="${o%/\\*\\*}"; [ "${p#"$pre"/}" != "$p" ] && hit=1 ;; *) [ "$p" = "$o" ] && hit=1 ;; esac
  done < "$OWNS"
  [ $hit -eq 1 ] || { echo "Fail: lease-$LEAF | Expected: $p inside OWNS | Got: outside"; bad=$((bad + 1)); }
done <<< "$paths"
[ $bad -eq 0 ] || { echo "LEASE FAILED $LEAF $bad/$n"; exit 1; }
echo "LEASE OK $LEAF $n paths"
''', 0o755)
write("checks/a11-allow.txt", "# PM-approved A11 exceptions, one per line: <path><TAB><exact substring of the hit line>.\n"
      "# Filled only after a PM ruling (PR-32). Empty means no exception.\n", once=True)
write("checks/shot-justify.json", "{}\n", once=True)
write("checks/shot-masks.json", json.dumps({
    "_source": "Random or time-based regions: guide 01-09-f-lib.html (timestamps from nowIso/isoIn/isoAgo at module load); "
               "countdowns render role=timer (layout/_internal/Countdown.tsx:68) or <time> (ui/Countdown/Countdown.tsx:101, "
               "collection/CollectionHistory.tsx:132); the Next dev indicator differs between 16.2.9 and 16.4.5 (PLAN-GATE item 33).",
    "channel_threshold": 16,
    "max_outside_mask_pct": 0.5,
    "_threshold_note": "LOW-CONFIDENCE ASSUMPTION: 0.5% of pixels outside masks; calibrate per PR-37 before A5 is judged.",
    "selectors": ["[role=\"timer\"]", "time", "nextjs-portal"],
}, ensure_ascii=False, indent=2) + "\n")
write("checks/boxes.json", json.dumps({
    "_source": "sections/02-01-s-shell-h.html#s-shell-grid 'Measured boxes' (member state, viewport height 900, route /, after document.fonts.ready)",
    "route": "/", "tolerance_px": 1, "viewport_height": 900,
    "_selector_note": "Selectors are structural, taken from the original markup; identity and logo selectors are assumptions F0 confirms in its return.",
    "boxes": {
        "header": {"selector": "header", "375": [0, 0, 375, 72], "768": [0, 0, 768, 121], "1024": [0, 0, 1024, 121], "1440": [0, 0, 1440, 121]},
        "logo": {"selector": "header a[href=\"/\"] img", "_src": "components/layout/Header.tsx:106 (assumption)",
                 "375": [72, 13.5, 205.8, 44], "768": [16, 13.5, 205.8, 44], "1024": [16, 13.5, 205.8, 44], "1440": [24, 13.5, 205.8, 44]},
        "identity": {"selector": "header ul[aria-label=\"Tiện ích\"]", "_src": "components/layout/Header.tsx:112 (assumption)",
                     "375": [301.8, 13.5, 321.3, 44], "768": [702, 13.5, 321.3, 44], "1024": [702, 13.5, 321.3, 44], "1440": [1094.7, 13.5, 321.3, 44]},
        "main": {"selector": "main", "_fields": "x,y,width", "375": [16, 80, 343], "768": [16, 129, 736], "1024": [16, 129, 932], "1440": [24, 129, 1332]},
        "rightRail": {"selector": "aside[aria-label=\"Thông tin trực tiếp\"]", "375": None, "768": None, "1024": None, "1440": [1052, 129, 304, 607.6]},
        "quickActionRail": {"selector": "aside[aria-label=\"Thao tác nhanh\"]", "375": None, "768": None, "1024": [956, 207.6, 60, 484.9], "1440": [1372, 207.6, 60, 484.9]},
        "bottomTabBar": {"selector": "nav[aria-label=\"Điều hướng chính\"]", "375": [0, 844, 375, 56], "768": None, "1024": None, "1440": None},
        "footerHeight": {"selector": "footer", "_fields": "height", "375": [675], "768": [403], "1024": [403], "1440": [355]},
    },
    "grid": {"_what": "home ProviderGameGrid on tab 'Tất cả': column count and child count (16 games + ComingSoonTile fillers)",
             "columns": {"375": 3, "768": 4, "1024": 6, "1440": 8}, "children": {"375": 17, "768": 17, "1024": 21, "1440": 21},
             "fillers_1440": 5},
}, ensure_ascii=False, indent=2) + "\n")

# ---------------------------------------------------------------- ledgers
UI_LEAVES = {"F1", "U1", "U2", "S1", "S2", "S3", "S4", "S5", "F5", "S6", "S7", "S8", "U3", "U4", "U5", "U6", "U7", "R3", "R4", "R5", "R6", "R7", "R8"}
for (i, w, title, rev, row, owns, needs, routes, notes) in L:
    g = [f"# Gates: {i} {title}", ""]
    if owns:
        g += ["OWNS: " + ", ".join(owns), ""]
    needs_txt = ", ".join(needs) if i != "I1" else "every leaf W0-W15"
    g += [f"Wave: {wl(w)} · Needs (merged before dispatch): {needs_txt or 'none'} · Dev-server port: {PORT[i]}", ""]
    if owns:
        g += ["Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):", "",
              "```yaml", "allowed_files:"] + [f"  - {e}" for e in owns] + ["```", ""]
        g += ["Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `" + row +
              f"` row in `docs/rebuild/review/{rev}.md` (leaves table) together with that review's §2-§5 entries for the same items, "
              "except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's "
              "Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 "
              f"that falls inside this lease (D3). The acceptance checks are mechanised in `{CK}/{i}.sh` (PM-authored; never edit it).", ""]
    if notes:
        g += ["Leaf notes: " + notes, ""]
    n = 1
    def gate(text, check=None, expect=None):
        global n
        g.append(f"- [ ] G{n}: {text}")
        if check:
            g.append(f"  CHECK: {check}")
        if expect:
            g.append(f"  EXPECT: {expect}")
        g.append("  EVIDENCE: pending")
        g.append("")
        n += 1
    gate("lint passes", "npm run lint && echo LINT_OK", "LINT_OK")
    if i in ("F0", "F1"):
        gate("typecheck passes, or no TypeScript input exists yet (an empty tree is TS18003, not an error)",
             "if [ -n \"$(rg --files src -g '*.ts' -g '*.tsx' 2>/dev/null)\" ]; then npx tsc --noEmit && echo TSC_OK; else npx tsc --noEmit 2>&1 | rg -q TS18003 && echo TSC_OK; fi",
             "TSC_OK")
    else:
        gate("typecheck passes", "npx tsc --noEmit && echo TSC_OK", "TSC_OK")
    if i == "F0":
        gate("token-lint self-test fires on every seed", "npm run lint:tokens:self-test", "SELF-TEST OK")
        gate("rule-gate self-test fires on every positive seed and passes every clean seed", "node scripts/rebuild-rules.mjs --self-test", "SELF-TEST OK")
        gate("unknown-class self-test flags stock utilities and passes repo-declared classes", "node scripts/tw-unknown-classes.mjs --self-test", "SELF-TEST OK")
        gate("Google Fonts is reachable from this build environment", f"bash {CK}/fonts-preflight.sh", "CHECKS OK fonts")
    elif i not in ("F2", "I1"):
        gate("token lint holds", "npm run lint:tokens", "token-lint OK: GROUP-A/GROUP-B contract (A1/A2/A3) holds.")
    if i not in ("F0", "F4", "I1"):
        args = " ".join(f"'{o}'" for o in owns if not o.endswith(".ico"))
        census = f" && bash {CK}/census.sh" if (w >= 2 or i == "F1") else ""
        gate("owned files have no banned class token, no silent no-op class, no tag or legal comment, and the CSS census holds",
             f"node scripts/rebuild-rules.mjs {args} && node scripts/tw-unknown-classes.mjs {args}{census} && echo RULES_OK", "RULES_OK")
    gate("the review row's acceptance checks pass, mechanised with the leaf-note normalisations", f"bash {CK}/{i}.sh", f"CHECKS OK {i}")
    if w >= 8:
        gate("production build passes", f"npm run build > /tmp/yb-build-{i}.log 2>&1; echo BUILD_EXIT=$?", "BUILD_EXIT=0")
    if routes:
        p = PORT[i]
        gate("routes answer as the inventory says, on this leaf's own dev server",
             f"node scripts/with-dev-server.mjs --port {p} -- node scripts/verify-routes.mjs --base http://localhost:{p} --only " + ",".join(routes),
             f"ROUTES OK {len(routes)}/{len(routes)}")
    if owns:
        gate("lease holds: the branch diff stays inside OWNS", f"bash {CK}/lease.sh {i}", f"LEASE OK {i}")
    if i in UI_LEAVES:
        gate("frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)")
    open(os.path.join(HERE, "gates", f"leaf-{i}.md"), "w").write("\n".join(g))

# ---------------------------------------------------------------- PLAN.md
rows = []
for (i, w, title, rev, row, owns, needs, routes, notes) in L:
    spec_row = f"`review/{rev}.md` {row}" if i != "I1" else "deferred rows (all reviews)"
    rows.append(f"| {wl(w)} | {i} | {title} | {', '.join('`' + o + '`' for o in owns) or '— (verification only)'} | "
                f"{(', '.join(needs) if i != 'I1' else 'all') or '—'} | {PORT[i]} | {spec_row} |")
excl = "\n".join(f"  - `{p}`: {r}" for p, r in sorted(EXCLUDED.items()))
PLAN = f"""# Plan: Yaobet UI rebuild, exact to the as-built guide

Scope: yaobet-rebuild (this file: .unlazy/yaobet-rebuild/PLAN.md, generated by genplan.py; edit the generator, never this file)
Depth: tree 2 (root → 30 builder leaves + 1 integration ledger)
Mode: orchestrated

## Contract

- Goal: rebuild `src/` so the app matches `{GUIDE}/` exactly ("1000%", owner D1). The delivery passes the audit in `GATES.md`: the guide's acceptance checklist (05-01, with token lint per ADR-002) plus frontend-qc, oracle-review and hallucination-auditor.
- Binding docs, in precedence order: `docs/rebuild/DECISIONS.md` (D1-D4) → `docs/rebuild/PM-RULINGS.md` (PR-01..PR-39; PR-29+ are proposed by sa until the PM confirms) → `docs/rebuild/ADR-002.md` (including §6, the superseded review statements) → `docs/rebuild/review/*.md` → `docs/rebuild/sections/*`. Read-only sources: the original `{ORIG}/**`.
- Fidelity over taste: defects are reproduced (D3) and listed in `docs/rebuild/FIX-LIST.md`. A QC finding that would change the guide's output becomes a new FIX-LIST row, never a code change.
- Stack: Next 16.4.5, React 19.3, Tailwind 4.3.4, TypeScript 5, Playwright exactly 1.61.1 (PR-30). Tailwind without preflight, per ADR-002 §1.
- Paths: every leaf path is the original source path (PR-05). `genplan.py` asserts that each OWNS entry under `src/` names a real original path or a file PR-01/PR-21 create, and that all 380 original `src/` files have exactly one owner, except these deliberate exclusions (not rebuilt):
{excl}
  Translated rather than recreated (no `*.module.css` anywhere): each `X.module.css` belongs to the leaf that owns `X.tsx`; the others are mapped in `TRANSLATES` (stub, Home, member, VipPage and the 8 collection sheets).
- Ownership: each ledger's `OWNS:` line is the lease, brace-free, one exact path or one `dir/**` per entry (`checks/owns-probe.txt` holds the hook probe). Leaves inside a wave are disjoint. A file passes from one leaf to another only across waves, append-only: `src/ui/ui.css` F1 → U1 → U2; `shell.css` F1 → S1 → S2 → S3; `home.css` F1 → S5 → S6; `member.css` F1 → U3 → U4 → U5; `vip.css` F1 → R3 → R4; `collection.css` F1 → R7 → R8. `src/**` is deleted once, by F0.
- Host launch mode: background `Agent(subagent_type: "dev-fe")`. The prompt starts with `Role: dev-fe` + the spawn contract, pastes the ledger's `allowed_files:` YAML block verbatim (bullets, never an inline comma list), and stays under 6,000 chars. The PM creates each worktree under `.claude/worktrees/<leaf>` (branch `rb-<leaf>`, kept after merge) with the hard-linked `node_modules`, proves `lint` + `tsc` on the baseline, then dispatches. At most 2 builders at once, at most 4 agents per wave. The PM merges a VERIFIED leaf into `main` with `--no-ff` before dispatching anything that needs it.
- Checks: `checks/<leaf>.sh` mechanise each review row (PLAN-GATE §3). They are PM-authored (generated here), committed before dispatch, and never edited by the leaf's builder. Each prints `Fail: <id> | Expected | Got` per failure and `CHECKS OK <leaf> n/n` only when all pass. Checks that cannot run in their leaf's wave live in I1, after the last wave.
- Dev servers: never shared. Every served check goes through `scripts/with-dev-server.mjs --port <leaf port>` (ports 3110-3140 per the table; 3107 for A4/A5/A5b, 3108-3109 for A9), which refuses a bound port and stops the server afterwards.
- Review: Stage A on every return (rerun every ledger CHECK, fresh exit codes). Stage B is a `frontend-qc` fidelity pass on every UI leaf. After the W1 merge the PM runs `npm run lint:tokens` on `main` (F2 has no token-lint gate). Builds: `npm run build` in the background with output to `/tmp/yb-build-<leaf>.log`; never pipe it through `head` or `rg -m`.
- Hot-fix lease (PLAN-GATE item 24, PR-36): on the PM's order only, a `debugger` may edit `scripts/**` and `.unlazy/yaobet-rebuild/genplan.py` (regenerating `checks/**`) to fix a gate-script false positive. After each fix the PM reruns G4 and G5 for every merged leaf.
- Fonts (PR-35): `next build` needs Google Fonts (it fails without network; `next dev` silently falls back to a local font, which breaks the box and shot gates). F0 and F5 gate reachability; I1 compares the font files with the original build.
- Content rules: Vietnamese copy is verbatim from the guide or the ported original. No invented numbers, names or mascots. No legal or regulatory text. No plan, wave or leaf tags in `src/` (PR-27, PR-31). Rendered strings that carry such terms are listed for the PM in PR-32; none is decided here.

## Owner and PM approvals needed before dispatch

1. Playwright (PR-14, APPROVED 2026-11-05), pinned exactly `1.61.1` (PR-30, proposed).
2. PR-29..PR-39 (proposed by sa) and the open question PR-32.
3. For information (reversible): PR-03/PR-26 verbatim ports; PR-19 dead components; PR-28 old mock assets deleted (kept in tag `archive/tailwind-v1`).

## Dispatch table

| Wave | Leaf | Title | OWNS | Needs | Port | Spec row |
|---|---|---|---|---|---|---|
""" + "\n".join(rows) + "\n\nLeaf ledgers: `.unlazy/yaobet-rebuild/gates/leaf-<id>.md`. Checks: `.unlazy/yaobet-rebuild/checks/`. Root audit: `GATES.md`.\n"
open(os.path.join(HERE, "PLAN.md"), "w").write(PLAN)

# ---------------------------------------------------------------- GATES.md
def A(gid, title, check=None, expect=None):
    s = f"- [ ] {gid}: {title}\n"
    if check:
        s += f"  CHECK: {check}\n"
    if expect:
        s += f"  EXPECT: {expect}\n"
    return s + "  EVIDENCE: pending\n"

GATES = "\n".join([
    "# Gates: Yaobet UI rebuild (root audit)\n",
    "Scope: all 30 leaves are merged into `main` and I1 is MET. These gates are the delivery audit: the guide's 05-01 acceptance checklist "
    "(with token lint per ADR-002) plus the harness gates. Run them in order, from a clean checkout of `main`. Generated by genplan.py.\n",
    A("A1", "every leaf ledger and the integration ledger reverify from the root (lease gates are vacuous on `main` by design; Stage A holds their evidence)",
      "node ~/.claude/skills/unlazy/scripts/gate-check.mjs --root . --cwd . --reverify --jobs 1 .unlazy/yaobet-rebuild/gates/leaf-*.md", "ALL MET"),
    A("A2", "static checks of the checklist's first block: token lint and its self-test, lint, types, build",
      "npm run lint:tokens && npm run lint:tokens:self-test && npm run lint && npx next typegen && npx tsc --noEmit && npm run build > /tmp/yb-root-build.log 2>&1 && echo STATIC_OK",
      "STATIC_OK"),
    A("A2b", "the built CSS declares the PR-13 runtime token names, the F1 built values and the vietnamese subset, and the font files equal the original build's",
      f"test -f .next/BUILD_ID && bash {CK}/built-css.sh", "CHECKS OK built-css"),
    A("A3", "the build output lists every inventory route, and the rule gates and the CSS census are clean over all of `src/`",
      f"test -s /tmp/yb-root-build.log || npm run build > /tmp/yb-root-build.log 2>&1; node scripts/verify-routes.mjs --build-log /tmp/yb-root-build.log && node scripts/rebuild-rules.mjs src && node scripts/tw-unknown-classes.mjs src && bash {CK}/census.sh && echo INVENTORY_RULES_OK",
      "INVENTORY_RULES_OK"),
    A("A4", "every inventory URL answers as specified: pages 200, the four redirects 307 to their targets, /foo and /khuyen-mai/pr9 404",
      "node scripts/with-dev-server.mjs --port 3107 -- node scripts/verify-routes.mjs --base http://localhost:3107", "ROUTES OK 43/43"),
    A("A5", "every reference shot has a same-size capture whose mismatch outside the masked time-based regions is under the threshold or justified, and the capture's state checks hold",
      "rm -rf .shots && node scripts/with-dev-server.mjs --port 3107 -- node scripts/capture-shots.mjs > /tmp/yb-capture.log 2>&1 && "
      "test \"$(rg -c 'final check: ok' /tmp/yb-capture.log)\" = 4 && rg -q 'DONE 72' /tmp/yb-capture.log && "
      f"node scripts/shot-diff.mjs --ref {REF_SHOTS} --got ./.shots --masks {CK}/shot-masks.json --justify {CK}/shot-justify.json",
      "SHOTS OK 72/72"),
    A("A5b", "the SH-02 shell boxes match the guide's measured boxes within one pixel at every width, after fonts load, and the home grid has its specified columns and fillers",
      f"node scripts/with-dev-server.mjs --port 3107 -- node scripts/box-check.mjs --boxes {CK}/boxes.json", "BOXES OK"),
    A("A6", "visual review of every pair: section order, column count, spacing rhythm, colour, type weight and wrapping match; every pair A5 reports over threshold has a justification row in `checks/shot-justify.json` naming the guide's random or time-based value; the intermediate widths match the composition notes; /vip uses the luxury palette (frontend-qc; every mismatch is a `Fail:` routed to the owning leaf)"),
    A("A7a", "the built CSS carries the vietnamese font subset (unicode-range covering U+1EA0-1EF9)",
      "rg -l --no-ignore --hidden -g '*.css' 'U\\+1EA0-1EF9' .next/static | rg -q . && echo FONT_SUBSET_OK", "FONT_SUBSET_OK"),
    A("A7b", "copy: every Vietnamese string in the guide's copy tables appears verbatim; ữ ặ ở render in a heading and a button; money and numbers go through the `lib/format` formatters only (hallucination-auditor copy pass)"),
    A("A8", "states, motion and accessibility: every component's States row has been exercised; Tab reachability, focus rings, focus traps and Escape behave as specified; durations and easing match the tokens; reduced motion applies; the lottery canvas erases and opens past its clear threshold (frontend-qc + user-tester)"),
    A("A9a", "the production build has no DEV toggle",
      f"npm run build > /tmp/yb-build-A9.log 2>&1 && node scripts/with-dev-server.mjs --port 3108 --mode start -- bash {CK}/no-dev-toggle.sh",
      "CHECKS OK no-dev-toggle"),
    A("A9b", "mock auth: a fresh load is tiered; register leads to level-0; log in leads to tiered; reload returns to tiered; Escape closes the modal and focus returns to the trigger",
      "node scripts/with-dev-server.mjs --port 3109 -- node scripts/auth-flow.mjs", "AUTH FLOW OK 5/5"),
    A("A10", "FIX-LIST is complete: every reproduced defect and every guide-conflicting QC finding has a row; no defect was silently fixed (oracle-review samples twenty FIX-LIST rows against the code)"),
    A("A11", "hygiene: no tag family and no legal term in `src/` outside PM-approved exceptions; the dependency set is exact with Playwright pinned; no committed runtime artefacts",
      f"bash {CK}/hygiene.sh", "CHECKS OK hygiene"),
    A("A12", "oracle-review and hallucination-auditor PASS on the full rebuild diff (no fabricated routes, tokens, copy or ported files; scope drift within the spawn-contract budget against the ledgers)"),
])
open(os.path.join(HERE, "GATES.md"), "w").write(GATES)

print("ok", len(L), "ledgers,", len(waves), "waves;", len(orig_src), "original src files,",
      len(orig_src) - len(EXCLUDED), "owned exactly once,", len(EXCLUDED), "excluded;",
      sum(len(l[5]) for l in L), "OWNS entries probed against the lease hook")
```
