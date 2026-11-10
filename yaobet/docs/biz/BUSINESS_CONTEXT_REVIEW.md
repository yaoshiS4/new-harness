# Yaobet Business Context — Senior PM Review

**Reviewed:** `Igaming-Agent-1/.agent/guidelines/yaobet-business-context.md` v1.0 (254 lines, 2026-11-04)
**Cross-read:** `Technical/Projects/Igaming/docs/vietnam_igaming_final_strategy.md` §1–6, `docs/biz/PRD.md`, `docs/biz/PRODUCT_BRIEF.md`; path-existence check on all 32 canonical files cited (31 exist, `docs/biz/CONTEXT.md` is gone as stated).
**Reviewer:** pm (Claude Code harness). **Date:** 2026-11-04.
**Independent audit of the derived SOT:** `hallucination-auditor` (read-only, H_env) traced every figure, path and ruling in `BUSINESS_CONTEXT_SOT.md` to v1.0: 39/39 paths exist, zero fabricated references; 7 major tag-drift findings (untagged §1.1/§1.2 claims promoted to `[OWNER]`, pm sentences under the owner-binding header) and 10 over-condensed owner rulings, all fixed in v2.0 before delivery.
**Verdict:** NOT READY as the business SOT for a new build. It is a good *portfolio status board for the loyalty and engagement layer of an already-live operator*. It is not a business context for "building an iGaming platform". Rewrite as `BUSINESS_CONTEXT_SOT.md` with the open questions closed or defaulted.

---

## 1. Executive assessment

What is strong:
- The `[OWNER] / [SPEC] / [APP]` tagging discipline and the status legend are the best thing in the file. Keep them.
- The money invariants (§2) are the most rigorous part of any Yaobet document I have read: Eligible-TO, the odds-1.50 gate, the two-line cashback, the 1.5% give-back ceiling, the farm-economics proof, and the "weights are throttles, not pricing" ruling are real product decisions with reasons.
- The contradictions table (§5) is honest. Most teams hide this.
- Named personas and the 10-stage journey are reusable.
- The standing rules (§6) encode painful lessons (invented mascots, 88-type notification catalogue, hallucinated 40% pyramid).

What is wrong, in order of damage:
1. **It does not say what the project is.** A new brand on the shared backend, a rebuild of the Yaobet player web app, or a greenfield platform? The file describes a live operator with production data and 10+ brands; your brief says "we are going to build an iGaming platform". These are different companies with different scopes.
2. **The brief contradicts the recorded design decision.** §1.2: hype trends (liquid glass, win-juice, FOMO tickers, infinite scroll) were evaluated and *rejected*; the chosen language is trust-first "Lucky Obsidian". Your brief asks for "modern, fancy, hype, engage to play more". Either the decision is reopened, or "hype" needs a definition that lives inside Lucky Obsidian. Nobody should write a line of UI until this is settled.
3. **The moat has no spec.** The file says the #1 desire and durable moat is "provably fast, freeze-free withdrawal" and the app promises "Rút tiền trong vài phút". There is no withdrawal SLA, no status model, no liquidity or approval path, no failure story, no rail list for withdrawal (only deposit rails are listed). Fourteen products are specified; the one the business depends on is not.
4. **There is no acquisition section.** Telegram is blocked, Zalo is "high-exposure", the micro-influencer plan is dead, SEO belongs to OKVip, CAC pool is "waiting on owner data". So who arrives to be hyped? A platform "that makes users feel hype" with no traffic plan is a demo.
5. **No one knows what production pays today.** The live `/vip` rebate code inverts slots above sports; today's loss-secure cap and live VIP thresholds are "to confirm". Every reward spec is "shape-only until B2". The business is operating on numbers no document can state. That is the single biggest risk to any redesign: the new app will encode one of three contradictory ladders.
6. **The portfolio is 90% draft.** Of 14 products, 2 are SPEC-FINAL (points store, notifications). VIP, cashback, contribution, referral, scratch card, collection, monthly challenge are all SPEC-DRAFT with 13 + 22 + 12 + 6 open decisions between them. Rule 8 says "make the product decisions, default to a recommendation". The document violates its own rule on every product.
7. **The highest-value persona earns nothing from the headline promise.** Tuấn (41, nightly baccarat, 60M đ/month) earns 0 cashback and 0 money-weight because hedgeable casino is weighted 0. The brand promise "Hoàn trả mỗi ngày" is false for him. Casino is listed first in the lobby. That is a product contradiction, not a tuning issue.
8. **The VIP ladder is decorative.** Tier 4 entry needs 688B đ Eligible-TO; the file itself computes about 229 years for the average user. "Parked on B2" is not a launch posture for the retention product.
9. **Two SOTs exist in two repos and disagree.** The March-2026 strategy (`Technical/Projects/Igaming`) still says Telegram/Zalo community, dual referral + agent tools, 25–35% agent commission, 45% of GGR promo budget, "Stake-Lite" premium design. The context file says all of that is superseded, but nothing in the Igaming project says so. An agent grounding on the wrong repo will rebuild the pyramid.
10. **The engagement layer you want is unapproved and unfunded.** Collection: "randomness does not earn its price", 5-card set fails economically, M and R unset. Monthly Challenge: gated on a BI query, upkeep unfunded. Scratch card: "Nothing approved", funding blocked. Lucky Wheel: advertised, not operated. The "always-on activity surface" is a demo with no economics behind it.

---

## 2. Point-by-point critique

### §0 How to use
- "Load FIRST" + 31.7 KB (about 8k tokens) is too heavy for a Turn-1 load in a token-bounded runtime. SOT must be <= 150 lines with pointers.
- "today is 2026-11-04" hard-coded in the status legend rots immediately. Use "as of <version date>" once in the header.
- Paths are relative to the Antigravity repo (`.hc/...`, `apps/web`). The new project runs on Claude Code in a different tree; every pointer must be absolute or vendored.

### §1 What Yaobet is
- "10+ brands on one shared backend" and "Yaobet is the brand this repo's web app represents": does the new platform serve one brand or all? White-label theming is a day-1 architecture decision, not a later feature. Unanswered.
- "Fiat-play, crypto is a deposit rail": withdrawal rails are not listed anywhere. Deposit rails are. The promise is about withdrawal.
- "Lobby has 9 categories [APP]": PRD says 8, strategy says 8, app shows 9 (Bàn chơi / Game nhanh added). Which is the business decision? Tagged [APP] correctly, so nobody owns it.
- Competitors: watched, never analysed. No answer to "why would Hùng leave OK9 for Yaobet" beyond withdrawal speed, which every competitor also claims. The hype brief needs an engagement-layer competitor teardown (OKVip brands, SHBET, Stake) and there is none.
- Mobile-first 87% [OWNER]; PWA + APK; no iOS story (APK is Android only, 375 px base is iPhone SE/mini). Decide: iOS = PWA only.

### §1.1 The player
- Personas are good. Coverage is not: Hùng is served; Tuấn gets nothing (see above); Linh (value-seeker) is the exploiter-adjacent segment with no product and no detection story; Mai (lapsed) has no reactivation product in the entire portfolio. Three of four personas have no product.
- "Trust is behavioural": agreed, and then the first-withdrawal beat has no spec, no SLA, and KYC (identity-cost moat, 5-day KYC for referral) sits on the path to that beat. First-withdrawal speed vs KYC friction is the central UX trade-off of the business and is not discussed.

### §1.2 Visual language
- Decision record for Lucky Obsidian "no longer in the repo"; the living source is a CSS token contract. A design rationale that lives only in CSS cannot be argued with. Reconstruct a one-page decision record or accept that the decision is reopened by your brief.
- "Hype rejected" vs your brief: see executive point 2. My recommendation: keep Lucky Obsidian as the base (trust is the moat) and define **bounded hype** = energy tied to real events (match moments, settled win-streaks, collection drops, level-ups), motion <= 200 ms, never fabricated activity (fake tickers, fake player counts, countdown pressure). Measure it by sessions/week and D7/D30 retention per segment, with withdrawal SLA as a guardrail metric.

### §2 Money invariants
- Internally consistent and well-reasoned. Three issues:
  - "50M đ deposit and 250M đ stake per active user per month" is a blended average over a whale-skewed base; the file later says the base is probably bimodal and the deposit distribution is unknown. A blended average that nobody trusts should not be the only production number in the SOT.
  - Universal 1% cashback > 0.45% minimum-edge hold is resolved by weighting casino to 0, which means the "daily cashback for everyone" promise silently excludes the casino player. The invariant is correct; the marketing is not.
  - Lucky-number rule (amounts end in 6 or 8, no digit 4) vs the points store's generated 1-2-5 package ladder (100K / 200K / 500K end in 0). One of them must yield. Recommend: exempt generated store packages, enforce on hand-set rewards.
- North-star "recycle >= 5x plus net deposit" is a volume metric. Nothing defines margin: GGR, NGR, hold by vertical, promo cost as % of NGR. "đồng per joiner" is a cost unit, not a return. A business context with no margin target cannot size any reward.

### §3 Owner data
- Good list. No owner, no date, no fallback. "Shape-only until B2" has been the state long enough that two production months (May–June) are cited while the 90-day pull is still pending. Set a date; if it slips, ship with provisional figures tagged `[PROVISIONAL]` and a re-price clause, which is what the No-Harm Floor already enables.

### §4 Portfolio
- 4.1 VIP: "Retained architecture: optimise it, never replace it" [OWNER] plus a ladder nobody can climb plus a second ladder in the app (`/tier`). Decision needed: re-anchor now with provisional milestones or ship with the SHBET anchors and accept a decorative ladder.
- 4.2 Cashback: base 1% live, promo opt-in SPEC. `/hoan-tra` redirects; the universal wedge has no screen. This is the one product that already pays real money and it has no receipt surface. Should be the first screen built.
- 4.3 Contribution page: launch day shows 2 of 8 rows non-zero. The owner accepted farm-enumerability. Fine, but PG-01 (live rebate code reconciliation) blocks it, and PG-01 is the same "what does production pay" question as executive point 5.
- 4.4 Points store: SPEC-FINAL, structural margin 0 by design. Accepted. Needs Budget B. OK.
- 4.5 Referral: single-level, 0.15–0.23%. Consistent with the anti-pyramid ruling. 22 open items; first-deposit reward blocked on Dq. With Telegram dead, referral is the acquisition engine. It should be prioritised above every engagement feature, and it is a stub.
- 4.6 Monthly Challenge: PROCEED WITH CHANGES gated on a free BI query that has not been run. Returns about 1.025% of exposed turnover, so any product below that edge is a farm. Not launchable.
- 4.7 Scratch card: strongest trust idea in the portfolio (real withdrawable money in 30 seconds to test the withdrawal promise). "Nothing approved." This is the feature that proves the moat; it should not be last.
- 4.8 Collection: the owner's stated purpose is "site looks dead". The honest finding is that an honest gacha converges on a transparent album. Recommend: ship it as a transparent album (deterministic progress, published prices) and drop the randomness; keep the EPL theme only if image rights clear.
- 4.9 Notifications: SPEC-FINAL, small, good. Confirm in app.
- 4.10–4.12 Calendars: mostly EXPIRED, overlapping dates with no governing document. Decide: H2-2026 calendar governs to 31 Dec 2026, Tết runway governs from 1 Jan 2027.
- 4.13 Second Space: parked on 12 questions. Leave parked; exclude from scope.
- 4.14 Wallet/account: BUILT mock. The deposit panel omits crypto, contradicting the business model. Withdrawal stops at "đang chờ xác nhận" by design in mock; the real status model does not exist.

### §5 Contradictions
- Ten contradictions, nine about money. The table is correct and the conclusion is missing: **the app is not a source of truth for money and the specs are not a source of truth for production.** Until a production config export exists, every money figure is `[UNVERIFIED]`.

### §6 Standing rules
- Rule 1 (no legal or regulatory analysis, ever) is the owner's call and is respected in the SOT. As a PM I note once, without analysis: it removes the largest category of business risk from every deliverable by decree. The product still needs resilience requirements (mirror domains, PWA/APK distribution, payment-rail failover, player privacy, data minimisation) stated as product requirements, which the file partly does. The SOT keeps them in scope under "player trust and continuity".
- Rules 2, 3, 6, 9, 11 are good and are carried verbatim.
- Rule 8 ("make the product decisions") is violated by the file itself (13 + 22 + 12 + 6 open decisions handed back). The SOT carries each open question with a recommended default.
- Rule 13 (restructure folders so only the latest is visible) conflicts with the fact that superseded docs still exist in a second repo with no "superseded" banner.

### §7 Pointers
- All 31 cited files exist. Good. The "do not read" column is valuable; carry it.

### §8 Glossary
- Fine. Carry, trimmed.

---

## 3. What the file never mentions and a business context must

| Missing | Why it matters | Default in SOT |
|---|---|---|
| Project identity and phase scope | Determines everything else | Rebuild of the Yaobet player web on the existing shared backend; backend out of scope (OQ-01) |
| Withdrawal product spec and SLA | It is the moat | Median < 5 min, P95 < 30 min, visible status timeline, failure states; owner to confirm (OQ-05) |
| Acquisition posture and CAC pool | No traffic, no hype | Referral + app retention first; paid pending CAC pool (OQ-08) |
| Margin targets (GGR, NGR, hold, promo % of NGR) | Sizes every reward | `[OWNER DATA]`; interim ceiling stays 1.5% of Eligible-TO |
| Production config truth | App encodes one of three ladders | All live figures `[UNVERIFIED]` until a config export (OQ-09) |
| Launch definition and date | Nothing is sequenced | Phase 1 scope proposal (SOT §5) |
| Multi-brand vs single-brand | Day-1 architecture | Yaobet only, tokens re-skinnable (OQ-07) |
| Back-office and risk operations | Who approves withdrawals, who flags rings | Out of scope for the player app; interfaces assumed to exist |
| Core products (sportsbook, casino lobby, KYC) | They are "BUILT (mock)" or absent | Listed as core with status, not as portfolio extras |
| Reactivation (Mai) and value-seeker (Linh) products | Two personas unserved | Deferred, recorded as gaps |
| iOS distribution | APK is Android only | PWA on iOS (OQ-12) |
| Success criteria for "hype / engage" | Unmeasurable brief | Sessions/week, D7/D30 by segment, withdrawal SLA guardrail (OQ-03) |

---

## 4. Open questions returned to the owner (with my default)

Answered by the owner on 2026-11-04; the answers and resulting state are recorded in `BUSINESS_CONTEXT_SOT.md` §5. Headlines: from-scratch rebuild with a new visual design (OQ-01, OQ-07), hype reopened as first-sight attraction (OQ-02), phase 1 = complete UI on mock data with no backend (OQ-04), responsive web only (OQ-12), acquisition via ads, CPD and referral (OQ-08); withdrawal SLA, production truth, calendar governance and lucky-number rule deferred (OQ-05, OQ-09, OQ-10, OQ-13). The list below is kept as the record of what was asked.

1. **OQ-01 Project identity.** Greenfield platform, new brand on the shared backend, or rebuild of the Yaobet player web? Default: rebuild the player web (`apps/web` scope) against the existing backend; backend, risk engine, and back-office out of scope for phase 1.
2. **OQ-02 "Hype" definition.** Is the Lucky Obsidian rejection of hype trends reopened? Default: no. "Bounded hype" as defined in §2 above.
3. **OQ-03 "Play more" metric.** Which engagement KPI is allowed given balance-retention KPIs are forbidden? Default: sessions/week and D7/D30 retention per segment; recycle >= 5x and net deposit remain north-star; withdrawal SLA is a guardrail that cannot be traded.
4. **OQ-04 Phase-1 scope.** Which of the 14 products launch? Default: wallet with withdrawal status model, lobby, cashback receipt screen, VIP with provisional ladder, notifications, points store, referral (turnover share only); collection as a transparent album; scratch card and monthly challenge after B2.
5. **OQ-05 Withdrawal SLA.** What does "vài phút" mean in numbers? Default: median < 5 min, P95 < 30 min, every state visible.
6. **OQ-06 B2 data.** Owner and date for the 90-day pull. Default: provisional figures tagged `[PROVISIONAL]`, re-price clause via No-Harm Floor.
7. **OQ-07 Brands.** One brand or white-label? Default: Yaobet only, token contract designed for re-skin.
8. **OQ-08 Acquisition.** CAC pool and channels with Telegram dead. Default: referral + retention; no paid plan assumed.
9. **OQ-09 Production truth.** Who can export today's live VIP, cashback, loss-secure config? Default: all live figures `[UNVERIFIED]`; the SOT never cites them as facts.
10. **OQ-10 Calendar governance.** H2-2026 vs Tết runway overlap. Default: H2 governs to 31 Dec 2026; Tết runway from 1 Jan 2027.
11. **OQ-11 Casino cashback.** Accept that the casino player earns 0 from "Hoàn trả mỗi ngày"? Default: headline carries the qualifier "thể thao và nổ hũ" until house-banked casino weight 0.20 is live with hedge controls.
12. **OQ-12 iOS.** Default: PWA only on iOS; APK on Android.
13. **OQ-13 Lucky numbers vs store ladder.** Default: generated store packages exempt; hand-set rewards comply.
14. **OQ-14 VIP ladder.** Ship SHBET anchors (decorative) or provisional re-anchor? Default: provisional re-anchor tagged `[PROVISIONAL]`, revisited on B2; the app's second ladder (`/tier`) is deleted.
15. **OQ-15 Collection randomness.** Keep gacha or ship as a transparent album? Default: transparent album.
16. **OQ-16 Supersession.** Mark the March-2026 strategy and PRD in `Technical/Projects/Igaming` as superseded with a banner, or delete. Default: banner.

---

## 5. Recommendation

Adopt `BUSINESS_CONTEXT_SOT.md` v2.0 as the single business SOT for the new project, with the 16 defaults applied. Reopen only the questions you disagree with. Do not start UI work until OQ-01, OQ-02 and OQ-05 are confirmed; everything else can proceed under the defaults.
