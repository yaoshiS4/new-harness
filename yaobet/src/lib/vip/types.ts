/* ============================================================================
 * Yaobet — LUXURY VIP program (route "/vip" rebuild) — shared TYPES.
 * ----------------------------------------------------------------------------
 * Foundation contract owned by @dev-fe. These shapes are the single source the
 * new luxury VIP components consume. They are ISOLATED from the legacy VIP
 * fixtures in src/lib/mock/vip.ts (which still power /tier + the member layout);
 * do NOT cross-import the two.
 *
 * 5 tiers × 10 levels = 50 levels. Tier privileges are PER-TIER & cumulative;
 * rebate/gift scale PER-LEVEL inside a tier (see formulas.ts). Colours are
 * referenced as var(--vip-*) token strings, never raw hex (guardrail).
 * ==========================================================================*/

/** UI locale. VI is default & source of truth. */
export type Lang = "vi" | "en";

/** The 4 cumulative tier privileges, in unlock order. */
export type PrivilegeKey = "bnPoints" | "bnShop" | "bnEvent" | "bnHost";

/** Stable tier identity (order bronze → diamond, index 0..4). */
export type TierId = "bronze" | "silver" | "gold" | "platinum" | "diamond";

/** copy.ts key for a tier's display name. */
export type TierNameKey = "tBronze" | "tSilver" | "tGold" | "tPlatinum" | "tDiamond";

/** Per-category rebate BASE values (the level-10 / 100% figures). */
export interface RebateBases {
  /** Hoàn cược Live */
  live: number;
  /** Hoàn cược Thể thao */
  sports: number;
  /** Hoàn cược Nổ hũ */
  slots: number;
  /** Hoàn cược Game bàn */
  table: number;
}

export interface VipTierDef {
  /** stable id (bronze..diamond). */
  id: TierId;
  /** 0-based order index (0..4). */
  index: number;
  /** copy.ts key for the display name. */
  nameKey: TierNameKey;
  /** CSS token ref for the tier gradient, e.g. "var(--vip-tier-gold-grad)". */
  grad: string;
  /** CSS token ref for the tier accent, e.g. "var(--vip-tier-gold-acc)". */
  acc: string;
  /** headline gift ($) shown on tier summaries (dataModel value). */
  gift: number;
  /** per-category rebate BASE values (100% / level-10 figures). */
  rebate: RebateBases;
  /** weekly cashback BASE (%) — the level-10 / 100% figure. */
  cash: number;
  /** pre-formatted weekly-wager unlock string, e.g. "500,000". */
  unlock: string;
  /** count of cumulative privileges unlocked at this tier (1..4). */
  perks: number;
}

/** Demo member used by the hero/level/comparison (screenshot fidelity). */
export interface CurrentUser {
  name: string;
  /** 0..4 — which tier the member currently sits in. */
  currentTierIndex: number;
  /** 1..10 — level within the current tier. */
  currentLevel: number;
  /** VIP loyalty points balance. */
  points: number;
  /** 0..100 — wager progress toward the next tier. */
  wagerProgressPctToNextTier: number;
  /** points still required to reach the next tier. */
  pointsToNextTier: number;
  /** 0..4 — the next tier index (currentTierIndex + 1). */
  nextTierIndex: number;
}

/** One accordion FAQ entry (bilingual). */
export interface FaqItem {
  q: Record<Lang, string>;
  a: Record<Lang, string>;
}
