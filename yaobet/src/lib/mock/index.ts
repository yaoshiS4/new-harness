/* ============================================================================
 * Yaobet — mock data layer barrel
 * ----------------------------------------------------------------------------
 * All `getX()` async accessors mimic server fetches. Downstream agents import
 * from "@/lib/mock". The real-API migration replaces these bodies, not the
 * call sites. Types come from "@/lib/types" (re-exported via ./types).
 * ==========================================================================*/

export * from "./types";
export { DEMO_EMPTY } from "./helpers";

// lobby / home dynamic surfaces
export {
  getVerticals,
  getJackpot,
  getMemberDayCountdown,
  getLeaderboard,
  getLiveMatch,
  getSportsMatches,
} from "./lobby";

// games / providers (+ the live-dealer feature-tile art for the 418px slot)
export { getGames, getProviders, FEATURE_GAME_ART } from "./games";

// vip / club
export {
  getVipTiers,
  getClubTiers,
  getPerks,
  getVipProgress,
} from "./vip";

// wallet
export { getWallet, getBalance } from "./wallet";

// promos
export { getPromos } from "./promos";

// store
export { getProducts, getPointsBalance } from "./store";

// referral
export { getReferral, getReferralKpi, getCommissions } from "./referral";

// cashback (core 1%)
export { getCashback } from "./cashback";

// game-contribution rate table (/cuoc-hop-le)
export {
  getContributionRates,
  getContributionCatalogue,
  deriveProviders,
  resolveTierRates,
  coalesceAdjacentEqual,
  rateBucket,
  CONTRIB_TIERS,
} from "./contribution";
export type {
  ContributionRates,
  ContributionCategory,
  ContributionTitle,
  CategoryRate,
  RateBucket,
  TierRateLeg,
  TierGroup,
  ContribTier,
} from "./contribution";

// bonus-restricted games list (/game-han-che) — orthogonal to the rate above
export { getRestrictedGames, BONUS_RESTRICTED_IDS } from "./contribution";
export type { RestrictedGame, RestrictedList } from "./contribution";

// records / messages
export { getRecords } from "./records";
export { getMessages } from "./messages";

// notifications — ONE inventory on the owner's eight types, feeding the header
// bell, which is the only notification surface. The
// legacy four-kind ./notifications.ts fixture is deleted.
export { getNotificationBell } from "./notification-feed";

// profile / security / linked accounts
export {
  getSecurityIndex,
  getVerification,
  getAccountSummary,
  getBankCards,
  getCryptoAddresses,
} from "./profile";

// deposit
export { getDepositOffer, getBankTransferMemo } from "./deposit";

// medals
export { getMedals } from "./medals";
