/* ============================================================================
 * Yaobet — LUXURY VIP program — TIER data + demo member constants.
 * ----------------------------------------------------------------------------
 * 5 tiers (bronze..diamond), each 10 levels. grad/acc are var(--vip-*) token
 * refs (declared in src/styles/tokens.css, the only file allowed literals).
 * Rebate/cash are BASE (level-10 / 100%) values scaled per-level by formulas.
 * `perks` is the CUMULATIVE count of PRIVILEGES unlocked at the tier (1..4).
 * ==========================================================================*/

import type { CurrentUser, PrivilegeKey, VipTierDef } from "./types";

/** The 4 privileges in cumulative unlock order (row order in the matrices). */
export const PRIVILEGES: PrivilegeKey[] = ["bnPoints", "bnShop", "bnEvent", "bnHost"];

export const TIERS: VipTierDef[] = [
  {
    id: "bronze",
    index: 0,
    nameKey: "tBronze",
    grad: "var(--vip-tier-bronze-grad)",
    acc: "var(--vip-tier-bronze-acc)",
    gift: 50,
    rebate: { live: 0.5, sports: 0.4, slots: 0.7, table: 0.4 },
    cash: 5,
    unlock: "50,000",
    perks: 1,
  },
  {
    id: "silver",
    index: 1,
    nameKey: "tSilver",
    grad: "var(--vip-tier-silver-grad)",
    acc: "var(--vip-tier-silver-acc)",
    gift: 99,
    rebate: { live: 0.6, sports: 0.5, slots: 0.8, table: 0.5 },
    cash: 8,
    unlock: "150,000",
    perks: 2,
  },
  {
    id: "gold",
    index: 2,
    nameKey: "tGold",
    grad: "var(--vip-tier-gold-grad)",
    acc: "var(--vip-tier-gold-acc)",
    gift: 199,
    rebate: { live: 0.75, sports: 0.6, slots: 1.0, table: 0.6 },
    cash: 15,
    unlock: "500,000",
    perks: 2,
  },
  {
    id: "platinum",
    index: 3,
    nameKey: "tPlatinum",
    grad: "var(--vip-tier-platinum-grad)",
    acc: "var(--vip-tier-platinum-acc)",
    gift: 399,
    rebate: { live: 0.8, sports: 0.8, slots: 1.0, table: 0.7 },
    cash: 20,
    unlock: "1,000,000",
    perks: 3,
  },
  {
    id: "diamond",
    index: 4,
    nameKey: "tDiamond",
    grad: "var(--vip-tier-diamond-grad)",
    acc: "var(--vip-tier-diamond-acc)",
    gift: 799,
    rebate: { live: 0.9, sports: 0.9, slots: 1.1, table: 0.8 },
    cash: 25,
    unlock: "3,000,000",
    perks: 4,
  },
];

/** Demo member (screenshot fidelity — independent of the auth fixture). */
export const CURRENT_USER: CurrentUser = {
  name: "Jordan Rivera",
  currentTierIndex: 2, // Gold / Vàng
  currentLevel: 7,
  points: 86880,
  wagerProgressPctToNextTier: 72,
  pointsToNextTier: 33120,
  nextTierIndex: 3, // Platinum / Bạch Kim
};

/** Current tier index of the demo member (Gold). */
export const CUR = 2;
/** Current level of the demo member within the Gold tier. */
export const CUR_LEVEL = 7;
