/* ============================================================================
 * Yaobet — LUXURY VIP program — the SINGLE numeric source for level cells.
 * ----------------------------------------------------------------------------
 * Every gift/rebate/cashback figure in the level table + comparison flows
 * through here so the math is single-sourced (guideline formulas, verbatim).
 *
 *   giftAt(tierIndex, level) → $, rounded to the nearest $5
 *   rate(base, level)        → base scaled 82% at L1 → 100% at L10
 *   fmtGift / fmtCash / fmtRate → the display strings
 *
 * Self-checks (see guideline acceptance):
 *   giftAt(2,7) === 200 ; rate(x,1) === 0.82x ; rate(x,10) === x
 *   fmtGift(200) === "$200"
 * ==========================================================================*/

/** Per-tier gift multiplier (bronze..diamond). */
export const GIFT_MULT = [0.6, 0.8, 1.0, 1.4, 2.0] as const;

/**
 * Promotion-gift amount ($) for a tier/level, rounded to the nearest $5.
 * @param tierIndex 0..4
 * @param level     1..10
 */
export function giftAt(tierIndex: number, level: number): number {
  return Math.round(((50 + (level - 1) * 25) * GIFT_MULT[tierIndex]) / 5) * 5;
}

/**
 * Scale a tier BASE value (a level-10 / 100% figure) down to a given level:
 * 82% at L1 → 100% at L10. Used for every rebate + weekly-cashback cell.
 * @param base  the tier's level-10 (100%) base value
 * @param level 1..10
 */
export function rate(base: number, level: number): number {
  return base * (0.82 + (0.18 * (level - 1)) / 9);
}

/** Alias for `rate` under the guideline's alternate name. */
export const rebateAtLevel = rate;

/** "$1,234" — gift display (thousands-grouped, no decimals). */
export function fmtGift(n: number): string {
  return "$" + n.toLocaleString("en-US");
}

/** "14%" — weekly-cashback display (whole percent). */
export function fmtCash(r: number): string {
  return Math.round(r) + "%";
}

/** "0.62%" — per-category rebate display (2 decimals). */
export function fmtRate(r: number): string {
  return r.toFixed(2) + "%";
}
