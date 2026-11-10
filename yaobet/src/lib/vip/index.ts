/* ============================================================================
 * Yaobet — LUXURY VIP program — foundation barrel.
 * Downstream components import from "@/lib/vip".
 * ==========================================================================*/

export type {
  Lang,
  PrivilegeKey,
  TierId,
  TierNameKey,
  RebateBases,
  VipTierDef,
  CurrentUser,
  FaqItem,
} from "./types";

export { TIERS, PRIVILEGES, CURRENT_USER, CUR, CUR_LEVEL } from "./tiers";
export { GIFT_MULT, giftAt, rate, rebateAtLevel, fmtGift, fmtCash, fmtRate } from "./formulas";
export {
  VIP_COPY,
  getVipCopy,
  FAQ_ITEMS,
  type VipCopy,
  type VipCopyKey,
} from "./copy";
