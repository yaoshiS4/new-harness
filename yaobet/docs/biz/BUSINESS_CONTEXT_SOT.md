# Yaobet Business Context — Source of Truth (v2.0 DRAFT)

**Scope:** the single business SOT for the Yaobet player platform project run on the Claude Code harness. Supersedes `Igaming-Agent-1/.agent/guidelines/yaobet-business-context.md` v1.0 for this project and the March-2026 strategy, PRD and product brief in `Technical/Projects/Igaming/docs/` (see OQ-16).
**Version:** 2.1, 2026-11-04, maintained by pm. Status: the owner answered all 16 open questions on 2026-11-04 (§5). Phase 1 is defined in §1. Items the owner said to ignore stay recorded as deferred, not resolved.
**Tags:** `[OWNER]` stated by the owner, binding · `[SPEC]` proposed in a document, pending sign-off or data · `[APP]` what the mock prototype shows · `[UNVERIFIED]` claimed live production value with no config export behind it · `[PROVISIONAL]` placeholder adopted for build, re-priced on data · `[OWNER DATA]` figure the owner must supply, never invent · `[DEFAULT OQ-nn]` pm recommendation in force until the owner overrides.
**Source root:** `SRC = /Users/maxime/Documents/Projects/Antigravity/Igaming-Agent-1` (Antigravity repo). All `.hc/` and `apps/web` pointers are relative to `SRC`.

## 0. How to use

1. Load this file first on any Yaobet task. Do not open BRDs "for context"; open a product's canonical file (§4) only when the task is about that product.
2. Status legend: **BUILT** mock screen exists in `SRC/apps/web` · **SPEC-FINAL** owner decisions locked · **SPEC-DRAFT** open owner decisions · **CONCEPT** no BRD · **PARKED** waiting on owner · **EXPIRED** window passed.
3. Never treat `[APP]` as a business decision, `[UNVERIFIED]` as a fact, or a CONCEPT as a product.
4. §5 is the decision register. Build on the defaults; never silently pick a side on an open question.
5. §6 standing rules override generic practice.

## 1. What this project is

- **Yaobet** is one brand of a Vietnam-targeting online betting operator run from offshore, with 10+ brands on one shared backend (the May-2026 cost simulation named Fabet, Sin, Debet, Zbet and Vin as siblings). `[OWNER]`
- **This project** = a **from-scratch rebuild of the Yaobet player-facing web app** with a new, better visual design. The existing `SRC/apps/web` mock is reference material, not the codebase. `[OWNER 2026-11-04, OQ-01]`
- **Phase 1** = the complete UI layout on mock data, no backend: home page (modern, attractive layout), game lobby, profile and account, deposit and withdraw, VIP, notifications, points and store, referral, promotions, cashback receipt, collection, messages, support stubs. Backend, risk engine, payment operations and back-office are out of scope. `[OWNER 2026-11-04, OQ-04]`
- Brand name stays **Yaobet**; everything else is re-skinned. A new design system replaces the Lucky Obsidian token contract. `[OWNER 2026-11-04, OQ-07]` pm note `[DEFAULT]`: design the new tokens so sibling brands can re-skin later.
- **Fiat-play.** Players wager in đồng. Crypto is a deposit rail converted to đồng. Stake.com is a mechanics reference, not evidence of crypto-native play. `[OWNER]`
- **Delivery:** a responsive web app, mobile-first (about 87% of users on mobile `[OWNER]`), Vietnamese everywhere, 375 px first and 1440 px desktop. No native app, PWA or APK in phase 1. `[OWNER 2026-11-04, OQ-12]` Mirror domains to survive ISP blocks remain a platform requirement outside phase 1 `[OWNER]`.
- **Acquisition channels:** ads, CPD (cost-per-deposit affiliate deals) and in-product referral. `[OWNER 2026-11-04, OQ-08]` Budgets and CAC pool `[OWNER DATA]`. pm note: CPD partners are an external marketing arrangement; they do not create an in-product agent ladder (the referral ruling in §4 stands). Telegram is blocked in Vietnam and Zalo is high-exposure `[SPEC (untagged in v1.0)]`.
- **Products in the lobby** `[APP]`: sports (football first, esports), live casino (Baccarat, Tài Xỉu, Dragon Tiger, Xóc Đĩa), slots (Nổ hũ), fish shooting (Bắn cá), card games incl. PvP (Game bài), lottery (Xổ số), cockfighting (Đá gà), table games, fast games. 9 categories.
- **Deposit rails** `[OWNER / APP]`: bank transfer, MoMo, ViettelPay, phone cards (Thẻ cào), crypto. Withdrawal rails: `[OWNER DATA]` (pm addition; not in the v1.0 data list).
- **Competitors watched** `[OWNER]`: OKVip alliance (OK9, FLY88, CM88), Stake.com, 1xBet, M88/W88. SHBET = budget benchmark for VIP rewards. J9 = layout-density reference only; never copy its art, logos or pixel UI.

## 2. The player and the promise

- **#1 desire and the moat:** provably fast, freeze-free withdrawal. "I get my money out, fast, first time." Governing fear: **bị bùng** (not getting paid). Quick deposit is table stakes. In Vietnam the product is trust plus payments, not games. `[SPEC (v1.0 §1.1 is untagged; owner to confirm)]`
- **Withdrawal promise:** "Rút tiền trong vài phút" is marketing copy, not an SLA; no withdrawal SLA is defined for phase 1. `[OWNER 2026-11-04, OQ-05]` pm note `[DEFAULT]`: the UI still shows a visible status model (requested → checking → paid / needs action) because the mock must show what happens to money (rule 12); the SLA question returns when the backend is in scope.
- **Trust beats:** first deposit and first withdrawal. Brand promise: "Nạp nhanh · Rút nhanh · Hoàn trả mỗi ngày". The cashback headline carries the qualifier "thể thao và nổ hũ" until house-banked casino earns a non-zero weight. `[APP copy; qualifier DEFAULT OQ-11]`
- **Personas (reuse verbatim):** **Hùng** 29, office job, weekend football, about 3M đ/month · **Tuấn** 41, self-employed, nightly baccarat, about 60M đ/month · **Linh** 34, plays wherever the value is, about 8M đ/month · **Mai** 26, lapsed six weeks, 0 đ now. Known gap `[pm inference]`: today only Hùng is fully served; Tuấn earns no cashback (casino weight 0), Linh has no value product, Mai has no reactivation product.
- **Segments:** REGULAR (VIP Tier 1–2), MID (Tier 3), WHALE (Tier 4–5), Exploiter X (defended at the funding entrance, not the withdrawal exit).
- **Journey:** Discover → Register → Onboard → First deposit → First play → Habitual loop → Withdraw → Retain/Loyalty → At-risk → Reactivate, plus Support and Safety lanes. VIP is a layer on the deposit-play-withdraw loop, not a step in it. Canonical: `SRC/.hc/platform/PLATFORM_CUSTOMER_JOURNEY.md`.
- **Attraction goal ("hype")** `[OWNER 2026-11-04, OQ-02]`: a visitor wants to play or explore the site at first sight. The new design is judged on first-impression pull, not on the 2026 "trust-first restraint" brief.
- **Phase-1 engagement goal ("play more")** `[OWNER 2026-11-04, OQ-03]`: get players to play more games and more genres (cross-genre exploration: lobby, discovery, recommendations, category entry points). The success metric is deferred.
- **Superseded experience principle (recorded per rule 10):** "Lucky Obsidian" (OLED-dark `#0F1115`, trust-first, modular cards, red-gold accent, token contract in `SRC/apps/web/src/styles/`) and its rejection of hype trends `[SPEC, untagged in v1.0]` are overridden by OQ-02 and OQ-07. What still binds `[OWNER rule 12 + pm DEFAULT]`: money shown truthfully (skeleton while loading, error state on error, "tạm dừng" when stale), celebration only after money has landed, no fabricated activity (fake tickers, fake player counts), no hidden outcomes; anti-slop invariants L-01, L-13, D-09, L-16, T-12, W-07 apply to the new design.

## 3. How the money works (invariants)

Revenue = GGR (stakes minus wins); NGR = GGR minus bonuses, fees and taxes. Terms: `SRC/.hc/platform/ECONOMICS_HANDBOOK.md`.

| Invariant | Value | Tag |
|---|---|---|
| Recycle | 1M đ deposited → about 5M đ raw stake (recycle ≈ 5×). Production May–June 2026: about 50M đ deposit and 250M đ stake per active user per month, 4.9×. A blended average over a possibly bimodal base; do not size rewards on it. | `[OWNER]` |
| Eligible-TO (cược hợp lệ) | Σ(stake × category weight × G(bet)). G(bet)=0 for PvP card bets, sports below decimal odds 1.50, void, cashed-out, opposite-side hedges, games with structural edge below about 0.5%, collusion-flagged, bonus-funded. One meter feeds cashback, VIP climb, referral and promo eligibility. | `[SPEC]`; odds-1.50 gate is the #1 anti-farm control |
| Weights live | Sports 1.00; Slots 0.20 in production, 15% at Tier 1–2 / 20% at Tier 3–5 on the published page; all other categories 0. | `[OWNER]` live values `[UNVERIFIED]` until config export (OQ-09) |
| Weights proposed | Slots 0.15 / 0.20 by tier; house-banked non-hedgeable casino 0.20 (ceiling 0.30); fish 0.15; lottery 0.10; esports 0.60 and virtual sport 0.30 shipped dark; hedgeable casino (baccarat, Tài Xỉu, Xóc Đĩa) 0 until controls live; PvP cards 0 permanently. Low-tier slots cut to 6–10% awaits mandate. | `[SPEC]` |
| What a weight is | A farm throttle and payout throttle, never a pricing dial. RTP-derived weights rejected twice. Bright line = the hedge test. | `[OWNER]` |
| Cashback | Line 1: flat 1.00% of Eligible-TO, every player, every tier, no opt-in. Line 2: opt-in per-category promo, real payout = headline × weight, tier scales the headline. Apex real: +0.40% sport, +0.08% slots. "1.4%" is Tier-5 sport only; a merged percentage on the level card is forbidden. Tier ladder 0.15 / 0.20 / 0.25 / 0.30 / 0.40% of covered Eligible-TO (sport and slots at launch). | Lines, apex and 1.4% rule `[OWNER]`; tier ladder `[SPEC]` |
| No-Harm Floor | Tier 3–5 identities at launch are paid max(new capped amount, what today's programme pays); the top-up is funded outside the ceiling and self-extinguishes; new entrants get the new cap. | `[OWNER]` |
| Give-back ceiling | Base + promo + monthly cash + capped loss-secure ≤ 1.5% of Eligible-TO (1.55% at the Tier-5 bad-week apex). Lean inside the envelope; filling toward the cap is "budget bleeding". One-time crossing cash, level-up points and weekly bonus sit in separate budgets. | `[OWNER]` |
| Loss-secure | Tier 3+, weekly, casino/slots/table: min(cap% × weekly Eligible-TO, tier đồng cap, net loss), paid as re-wagerable credit. Today's live cap `[UNVERIFIED]`. | `[SPEC]` |
| Points | 1 point = 1,000 đ face value; a liability with a sink (the store); earned only by level-up, weekly bonus, monthly bonus; no expiry, no cash-out haircut. | `[OWNER]` |
| Lucky numbers | Hand-set reward amounts end in 6 or 8 and contain no digit 4. Thresholds exempt. Generated store packages exempt. | `[OWNER]`; store exemption `[DEFAULT OQ-13]` |
| Farm economics | Universal 1% cashback exceeds minimum-edge hold (about 0.45%), so no deposit- or turnover-sized cash reward is farm-safe by caps alone. Real defenses: identity-cost moat (verified identity about 150–500K đ), wager-through about 3× deposit, cross-brand identity graph, per-identity lifetime caps. Off-platform hedging on free bets (about half of face value) is priced into pool sizing, not policed. | `[SPEC, audited]` |
| Grade-0 pool | About 88% of accounts (1.49M) sit below VIP entry, heavily polluted by first-deposit farmers. Segment before sizing; never plan to "convert the 88%". | `[OWNER]` |
| North star | Recycle ≥ 5× plus net deposit. "Less withdrawal" is never a target; balance-retention KPIs are forbidden. Campaign cost in đồng per joiner, never % of turnover. | `[OWNER]` |
| Margin targets | GGR, NGR, hold by vertical, promo cost as % of NGR: none recorded (pm addition to the v1.0 data list). | `[OWNER DATA]` |
| Win-streak | "Win N consecutive singles" is hedge-proof and needs no parlay engine; most abuse-resistant instrument. Parlay (cược xiên) not in the system. | `[SPEC]` |

## 4. Product portfolio (status as of v2.0)

| # | Product | Status | Route | Canonical (under `SRC`) | Phase 1 UI on mock data? `[OWNER OQ-04]` |
|---|---|---|---|---|---|
| 4.1 | Hạng VIP (5 tiers × 10 levels) | SPEC-DRAFT + BUILT | `/vip`, `/tier` | `.hc/vip-program/VIP_NEW/BRD_VIP_LEVEL_SYSTEM.md` (start at `00-START-HERE.md`) | Yes, provisional ladder; delete the second `/tier` ladder (OQ-14) |
| 4.2 | Hoàn trả (cashback engine) | SPEC-DRAFT; 1% base live | `/hoan-tra` (redirects) | `.hc/vip-program/VIP_NEW/BRD_PROMOTION.md` | Yes, first screen: daily receipt + estimator |
| 4.3 | Cược hợp lệ (contribution page) | SPEC-DRAFT + BUILT; blocker PG-01 | `/cuoc-hop-le` (`/game-han-che` redirects to its second tab) | `.hc/game-contribution/BRD_GAME_CONTRIBUTION.md` | Yes (PG-01 is a data blocker, not a UI blocker) |
| 4.4 | Cửa hàng điểm (points store) | SPEC-FINAL + BUILT | `/cua-hang` | `.hc/business/ideation/point-exchange/BRD-point-exchange-business.md` | Yes |
| 4.5 | Giới thiệu bạn bè (referral, single level) | SPEC-DRAFT + stub | `/gioi-thieu`, `/dai-ly` | `.hc/aff-program/05-08-26-AFF_Program_Ver.18/BRD-Referral-Program-v18.md` | Yes, turnover share only; first-deposit reward after Dq |
| 4.6 | Bảng Tháng (monthly challenge) | SPEC-DRAFT, gated on BI query | none | `.hc/monthly-challenge/BRD-BANG-THANG.md` | No |
| 4.7 | Vé số cào (scratch card) | SPEC-DRAFT + BUILT; nothing approved | `/ve-so` | `.hc/scratch-card/README.md` → BRD | Yes as UI mock; economics unapproved until B2 |
| 4.8 | Bộ sưu tập (collection) | SPEC-DRAFT + demo | `/bo-suu-tap` | `.hc/gacha-collection/BRD-GACHA-COLLECTION.md` | Yes as transparent album (OQ-15) |
| 4.9 | Thông báo (notifications) | SPEC-FINAL | header bell, `/tin-nhan` | `.hc/notification-revamp/00-BRIEF.md` → BRD | Yes |
| 4.10 | Khuyến mãi H2-2026 calendar | SPEC-FINAL with 6 gates; mostly EXPIRED | `/khuyen-mai` | `.hc/engagement-2026-h2/README.md` | Promotions page UI yes; campaign content is mock (calendar governance deferred, OQ-10) |
| 4.11 | Tết runway 2027 | CONCEPT | none | `.hc/tet-runway-2027/INDEX.md` | No (deferred, OQ-10) |
| 4.12 | Tết Đinh Mùi 2027 themes | CONCEPT | none | `.hc/tet-2027/STATUS.md` | No |
| 4.13 | Second Space | PARKED | none | `.hc/second-space/00-CHARTER.md` | No |
| 4.14 | Wallet, account, messages, lobby | BUILT (mock) | `/vi-tien`, `/tai-khoan`, `/tin-nhan` | app only | Yes, with a visible withdrawal status model (pm DEFAULT) |

Core, not portfolio: sportsbook, casino lobby, KYC, deposit and withdrawal operations belong to the backend and are mocked, not built, in phase 1. `[OWNER OQ-01/OQ-04]`

Binding product rulings carried from v1.0. Each bullet mixes owner rulings and spec text; the tag names the dominant provenance, and the canonical file carries line-level tags.

- VIP: progression only goes up; never replace with an NGR-share model; entry 30M đ Eligible-TO (SHBET anchor, a commitment bar) `[OWNER]`. Ladder anchors locked to SHBET production: T1 30M→3.8B, T2 5B→52B, T3 68B→558B, T4 688B→3.188B, T5 3.588B→9.888B đ `[OWNER anchors]`; interior levels on a geometric glide; a re-anchored ladder is proposed and parked on B2 `[SPEC]`. Weekly bonus (Tier 3+) and monthly bonus (Tier 2+) pay a fixed points amount per level when weekly / monthly Eligible-TO reaches 1% / 5% of the level milestone; the gate is binary, never a scaler `[OWNER model]`. One opaque bar, concrete đồng targets, no weights or percentages on the level card; no invented tier names (specs: Tier 1–5; app: Đồng / Bạc / Vàng / Bạch Kim / Kim Cương) `[SPEC]`. Rewards: level-up points on a power law (L1 +6 … L50 +10,905; 128,888 cumulative) and one-time crossing cash at L11 / L21 / L31 / L41 of 888K / 6.888M / 68.888M / 288.888M đ, all placeholders `[SPEC placeholder, v1.0 §4.1]`. Tier benefits: host (standard → personal), withdrawal-speed pass (priority from Tier 3), loss-secure from Tier 3 `[SPEC, v1.0 §4.1; "vài phút" wording stays copy, OQ-05]`.
- Cashback headline rule: every "lên tới X%" equals a real best-case rate for a named category with the qualifier shown; the "28% daily" slots banner is withdrawn. `[SPEC]`
- Contribution page: browsable per-game table with pagination, search, category / provider / contribution-% filters, per-tier values always visible (owner override 2026-08-10, farm-enumerability accepted) `[OWNER]`. Second tab "Game hạn chế": one common list (about 30 games) blocked only while the player holds a promotion or gift code with restricted-game terms; orthogonal to the contribution rate; never shown as a marker on the rate table `[OWNER]`. Framing is always "tỷ lệ được tính", never exclusion; no đồng figures, no climb weights, no personalisation, no "best value" ranking; every figure versioned with an effective date; placed bets keep their rate; the player is paid the better of page and ledger `[SPEC]`.
- Points store: full package every claim; escalation is a point sink, not a cash haircut; face value so structural margin ≈ 0 by design; the only ceilings are the aggregate budget (80% alert / 100% pause) and identity controls; no point expiry; every package has a non-zero cooldown; never import the archived v1 constants (688,000 đ floor, 0.80 haircut). `[OWNER]` Mechanic: cash packages on a 1-2-5 ladder generated from (P_min, P_max, n), each with a fixed non-zero cooldown, repeat fraction q and optional max-claims; cooldown running → escalated cost `points_k = ceil((P/r0) × (1/q)^(k−1))`, cash = P always; one clean wait resets to base `[OWNER]`. P_min, P_max, n, q are `[OWNER DATA]`.
- Referral: single level, consumer only, no agent pyramid, no downline, no credit `[OWNER, binding]`. Reward set v18: weekly share T1 0.15% … T5 0.23% of the friend's Eligible-TO with a 3M đ per 28 days gate (miss = 0, no penalty); first-deposit reward to the referrer as a gift code with no playthrough, conditional on the friend completing KYC, depositing ≥ Dq and wagering about 3× within 5 days; tier-up lump at each VIP crossing carved from the weekly budget `[OWNER-directed shape, caps TBD]`. Display: resolved rate, never "up to"; no countdowns or "N away" nudges; never the friend's deposits, losses or game mix `[SPEC]`.
- Scratch card: cards are earned by settled betting and bought; no consolation payment `[OWNER 2026-09-18]`. As built and ruled: 12 panels, 4 winning numbers, face numbers 00–99, 11 prize rungs from 10,000 đ to 20,000,000 đ, 38.7% of cards pay `[APP + OWNER rulings 2026-09-18, v1.0 §4.7]`; rung amounts and the pay rate are `[OWNER DATA]` until priced. Face fixed and recorded before touch; money lands before the celebration frame; auto-resolve in the player's favour; fairness board, earn ledger and card history are build gates `[SPEC]`.
- Collection: theme is per-collection content, never a house mascot; entitlement is a trigger framework; opens are never purchasable ("money may schedule a pull; only a settled wager may open one"); image rights are a production gate. `[OWNER]` Mechanic: a qualifying activity mints an open; an open yields a card; duplicates become shards (◈) that buy missing cards at a published price; completing a set pays cash with no rollover `[SPEC, v1.0 §4.8]`; set rewards and shard prices are `[OWNER DATA]` (M and R unset).
- Notifications: one simple list, four owner-named types (Balance Update, Reward, Announcement, Profile); specify the small thing completely and stop. `[OWNER]`
- Campaigns: every campaign is a full spec (concept, mechanism, entry gate, qualifying action, reward and estimate, budget, abuse controls, KPIs, worked example, edge cases) `[OWNER]`; one flagship per month behind live P0 controls; 5–10% holdout; points or credit before cash `[SPEC]`.
- Tết runway 2027: every moment gets a concept, never recommend killing one `[OWNER]`; giao thừa is Fri 5 Feb 2027, mùng 1 Sat 6 Feb, there is no "30 Tết" in 2027; never invent a fixture date.
- Tết Đinh Mùi themes: the activity is the theme and only ingredients that end up inside the finished thing are cards; Vietnamese only, no Hán characters or Chinese almanac material; a goat drawn as a goat. `[OWNER]`
- Second Space: the owner's idea is a placeholder; never guess it; wait for the 12 answers in `.hc/second-space/RESEARCH-SECOND-SPACE.md` §7.
- Lucky Wheel: advertised in the app, not operated; needs its own clearance (disclosed prize table and odds) before it ships. `[SPEC/OWNER]`

## 5. Decision register (answered by the owner on 2026-11-04)

| ID | Question | pm default | Owner answer (2026-11-04) | State |
|---|---|---|---|---|
| OQ-01 | Greenfield, new brand, or rebuild of the Yaobet player web? | Rebuild on existing backend | Rebuild from scratch; enhance UI/UX with better visuals | DECIDED |
| OQ-02 | Is the rejection of hype reopened? | No; bounded hype | Yes. Hype = strong first-sight attraction; the visitor wants to play or explore immediately | DECIDED (overrides 2026 record, rule 10) |
| OQ-03 | Engagement KPI for "play more"? | Sessions/week, D7/D30 | Metric deferred. Goal for now: players play more games and more genres | DEFERRED, goal set |
| OQ-04 | Phase-1 scope | Subset | Complete UI layout, no backend: home, lobby, profile, deposit/withdraw, VIP, notifications, points, store, referral, and the rest | DECIDED |
| OQ-05 | Withdrawal SLA | Median < 5 min, P95 < 30 min | "Vài phút" is just a term; no SLA needed now | DEFERRED |
| OQ-06 | B2 data owner and date | `[PROVISIONAL]` with re-price clause | Default | DECIDED (default) |
| OQ-07 | One brand or white-label | Yaobet only, re-skinnable tokens | Keep the Yaobet name; re-skin everything | DECIDED |
| OQ-08 | Acquisition channels | Referral + retention only | Ads, CPD, referral | DECIDED; budgets `[OWNER DATA]` |
| OQ-09 | Who exports live money config | `[UNVERIFIED]` until export | Ignore | DEFERRED; tags stay, not a phase-1 blocker |
| OQ-10 | H2-2026 vs Tết runway overlap | H2 to 31 Dec, Tết from 1 Jan | Ignore | DEFERRED; promotions page uses mock content |
| OQ-11 | Casino earns 0 from the daily cashback promise | Headline qualifier "thể thao và nổ hũ" | Default | DECIDED (default) |
| OQ-12 | Mobile distribution | PWA on iOS | No mobile app yet; responsive web app only | DECIDED |
| OQ-13 | Lucky numbers vs store ladder | Store packages exempt | Ignore | DEFERRED; default applies to mock copy |
| OQ-14 | VIP ladder anchors | `[PROVISIONAL]` re-anchor; delete `/tier` | Default | DECIDED (default) |
| OQ-15 | Collection randomness | Transparent album | Default | DECIDED (default) |
| OQ-16 | Supersede the March-2026 strategy / PRD | Banner pointing here | Default | DONE 2026-11-04 (banners added) |

Owner data still required before any đồng figure is final (v1.0 §3 list): B2 (90 days turnover per category per tier), deposit distribution (median and whale tail), live VIP thresholds and caps, real MAU, CAC pool, hold and churn by tier, support-ticket baseline, slots-weight mandate, referral Dq / schedule / C_head / gift-code expiry, gacha M and R, scratch-card α and funding. pm additions: withdrawal rails, margin targets.

## 6. Standing rules (owner, binding; items marked "pm" are not owner rules)

1. No legal or regulatory analysis in any deliverable; reframe as player trust, privacy, dignity or support cost. Put an "out of scope" clause in every charter. Do not load `igaming-compliance.md` unless the owner asks by name. (pm note, `[DEFAULT]`: continuity requirements the owner already stated, such as mirror domains, stay platform requirements outside phase 1.)
2. Clean-room on any new or "from scratch" brief: inputs are the owner's words plus explicit tunables; imported constants are surfaced as owner decisions first; write the Scope Contract before the first file read.
3. Never invent business context, names, numbers or mascots. Ask, or use `[OWNER DATA]`.
4. BRD/PRD golden rule (`SRC/.agent/rules/brd-prd-standard.md`): written for the player; Business context → Purpose → Scope → How it works; named personas; six-column user stories; on-screen copy table (Vietnamese · gloss · where); edge cases; formulas with a hand-computable worked example; low-fi mockups; sources. No schemas, APIs, event names, config or process residue.
5. Every campaign or promotion is a full spec, never a card.
6. Do not send agents to read sibling BRDs for convention; put the structure in the prompt; point agents only at the current feature's folder.
7. Stay in scope; answer the question asked; "convert" means convert; engage with the owner's framing.
8. Make the product decisions; default to a recommendation (this file's §5 is the model).
9. Review finished documents line by line; trace every headline number; run every mechanic against Hùng and Tuấn; cross-check worked examples.
10. The owner is the authority; overrides of a recorded risk decision are surfaced and recorded, never silently shipped.
11. Player-facing content describes what is actually built; app-vs-doc conflicts are reported as defects, not resolved by content.
12. Player-safety gate on any real-money feature: money stated truthfully, the player can see what happened to it, self-set limits respected, no outcome hidden.
13. Only the latest version of a folder is visible; superseded work goes to `archive/` and is never built from.
14. (pm rule, `[DEFAULT]`, not owner-binding) Every money figure shown to a player traces to a tagged line in §3 or to a config export; `[UNVERIFIED]` values never ship as copy.

## 7. Known app-vs-spec contradictions (report as defects)

Full table: v1.0 §5. Headlines: `apps/web/src/lib/vip/tiers.ts` pays slots above sports and rebates casino; `lib/mock/vip.ts` carries a second ladder; `lib/mock/cashback.ts` shows per-category weekly rates; promos advertise an un-operated wheel; `/hoan-tra` has no screen; store vouchers carry playthrough; lottery pays dust; `/dai-ly` shows an agent ladder; deposit panel omits crypto while the account page manages crypto addresses; the Tết brief calls the gacha "already built"; BRD A's points haircut and expiry are overridden by the later point-exchange ruling. Rule (pm synthesis of v1.0 §5 and rule 11): the app is not a source of truth for money; the specs are not a source of truth for production.

## 8. Where to read deeper, and what never to read

| Need | Read (under `SRC`) | Never |
|---|---|---|
| VIP mechanics, weights, ladder | `.hc/vip-program/VIP_NEW/00-START-HERE.md`, BRD A, BRD B | `VIP_NEW/_archive/`, `VIP_NEW/reviews/`, `.hc/vip-program/archived/` |
| Journey and metric definitions | `.hc/platform/PLATFORM_CUSTOMER_JOURNEY.md`, `.hc/platform/ECONOMICS_HANDBOOK.md` | |
| Market thesis | `.hc/business/research/product-research/01-global-research/PRODUCT-RESEARCH.md`, `02-vietnam-research/PRODUCT-RESEARCH-VIETNAM.md` | role and evidence sub-docs; `Technical/Projects/Igaming/docs/*` (superseded) |
| Referral | `Ver.18` BRD then PRD | earlier `Ver.N`, `archived/`, debates, reviews |
| Contribution page | BRD, PRD, `prototype/README.md`, `decisions/` | `party-mode/`, `revision/` |
| Points store | `BRD-point-exchange-business.md`, `TERMS-cua-hang-diem-vi.md` | `archive/` |
| Monthly Challenge | `BRD-BANG-THANG.md`, `PRD-BANG-THANG.md` | `archive/`, `working/` |
| Scratch card | `README.md`, BRD, PRD, `FAQ-SCRATCH-CARD.md` | `diagrams/` sources |
| Collection | BRD, PRD, `backlog/` | `party-mode/`, `research/`, `audit/` |
| Notifications | `00-BRIEF.md`, BRD, PRD, `CONTENT-NOTIFICATIONS.md` | |
| Campaigns | `engagement-2026-h2/README.md`, `12-CAMPAIGN-PLAYBOOK.md`; `tet-runway-2027/INDEX.md`; `tet-2027/STATUS.md` | `engagement-2026-h2/evidence/05-*` |
| Design system | `apps/web/src/styles/` | `.hc/archive/app-yaobet/` |
| Built app | `apps/web/src/app/**/page.tsx`, `apps/web/src/lib/mock/*.ts`, `apps/web/src/lib/i18n.ts` | |
| Anything under `.hc/archive/`, `.hc/j9-rebuild/`, `*/archive/`, `*/_archive/`, `*/party-mode/`, `*/reviews/`, `.agent/guidelines/igaming-compliance.md` | | superseded, process, or out-of-scope material |

## 9. Glossary

Cược hợp lệ / Eligible-TO: weighted, gated turnover · G(bet): per-bet yes/no gate · Hoàn trả: cashback · Hoa hồng: referral commission (never for cashback) · Thẻ cào: phone-card deposit · Vé số cào: scratch card · Xổ số: provider lottery games · Nổ hũ: slots · Bắn cá: fish shooting · Game bài: card games incl. PvP · Đá gà: cockfighting · Chìa: Monthly Challenge key · Open / pull: one collection draw · Shard (◈): duplicate-card currency · Loss-secure: weekly loss rebate · No-Harm Floor: transition guarantee for existing Tier 3–5 players · B2: the 90-day production data pull · Lì xì: Tết cash gift · Xông đất: first act of the new year · Bị bùng: not getting paid.
