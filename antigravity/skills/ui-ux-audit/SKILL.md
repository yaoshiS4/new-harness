---
name: ui-ux-audit
description: Audit UI/UX visual symmetry, breathability, token compliance, motion sync, and anti-slop HCI invariants.
metadata:
  short-description: Comprehensive UI/UX, visual symmetry, token compliance, and anti-slop audit
---

# UI/UX & Anti-Slop Audit Framework

Authoritative quality gate, forensic evaluation, and anti-slop verification standard enforcing **Google/W3C DTCG Token Contracts (`DESIGN.md`)**, **The 34 Master Invariants (`AGENTS.md`)**, **Bastien & Scapin (INRIA) Ergonomic Criteria**, **Nielsen Norman Group (NN/g) Usability Heuristics**, and the **5 Feels** (**Zero Hesitation**, **Calm & Trust**, **Brain Relax**, **Feels Instant**, **Effortless**).

## Operational Audit Workflow & Gates

### 1. Visual Audit & Violation Classification
1. Capture screenshots of current state across pages, viewports, and interaction states.
2. Classify violations into clear risk tiers:
   - **Critical**: Broken layout, overlapping text, inaccessible contrast (< 3:1), missing core states.
   - **High**: Token deviations, inconsistent rhythm/spacing, broken spring physics, raw inline styles.
   - **Low**: Minor hairline or sub-element optical alignment issues.
3. Apply fixes in low-risk sequence: typography/tokens -> spacing & vertical rhythm -> color harmony -> motion -> full block recomposition only if unsalvageable. Keep diffs surgical and minimal.

### 2. QC Finish Gate
Ship only when ALL checklist criteria pass:
- [ ] Screen purpose and visual anchor obvious within 3 seconds
- [ ] Exactly one primary action clearly leads visual hierarchy
- [ ] Every visible control/button has a working destination or real handler (zero dead ends)
- [ ] Content and labels belong specifically to product (no generic filler)
- [ ] All critical states implemented and reachable: loading skeleton, empty state, error fallback, retry
- [ ] Responsive collapse: mobile (<=412dp) 2-column max telemetry, no horizontal spill, zero text clipping
- [ ] Accessibility: WCAG AA contrast (>= 4.5:1 body, >= 3:1 large), keyboard focus visible, reduced-motion respected
- [ ] Anti-slop invariants: no nested card soup, no redundant parenthetical echoes, no unanchored punctuation marks

---

## 3. Tailwind CSS & shadcn Design System Linter Contracts (@shadcn/lint)

When authoring or modifying UI components, enforce design system contracts to eliminate arbitrary styles:
- **Component Contracts (`shadcn/no-restyle`)**: Components manage their own internal styling (padding, background, border). Never override component internals via `className` (e.g. adding `p-4` or custom `bg-*` to `<Button>` instead of using variants `size="lg"` / `variant="outline"`).
- **Semantic Theme Tokens (`shadcn/no-raw-colors`)**: Disallow raw color palette classes (e.g. `bg-pink-500`, `text-blue-600`) in favor of semantic theme tokens (`bg-primary`, `text-muted-foreground`, `text-accent-foreground`).
- **No Arbitrary Values (`shadcn/no-arbitrary-values`)**: Prohibit arbitrary bracket dimensions (`p-[13px]`, `w-[320px]`) that break design scale rhythm. Use standard spacing scale or parent layout flex/grid gap.
- **No Inline Styles (`shadcn/no-inline-styles`)**: Block `style={{ ... }}` on design system components.
- **Static Class Names (`shadcn/require-static-classes`)**: Prohibit dynamic string interpolation (`` `bg-${color}` ``) that defeats static AST analysis.
- **Remediation Order**:
  1. Use existing component variants and props (`size`, `variant`).
  2. Use parent layout containers and flex/grid gap for positioning/spacing.
  3. Use semantic CSS variables and design tokens (`bg-muted`, `border-border`).

---

## Full Protocol
Load `references/protocol.md` before executing beyond the core rules above.
