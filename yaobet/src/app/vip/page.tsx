/* ============================================================================
 * Yaobet — VIP page (route "/vip") — LUXURY VIP PROGRAM rebuild.
 * ----------------------------------------------------------------------------
 * Thin server page: it renders the <VipProgram/> client island, which owns the
 * auth-driven member↔guest split (useRequireAuth), tier-selection state, and
 * the whole luxury section tree. The legacy VIP fixtures (getVipTiers/getPerks/
 * getVipProgress) + legacy components (TierLadder/CurrentTierCard/…) are
 * intentionally NOT imported here — they still power /tier and the (member)
 * layout and must remain untouched. New data lives in @/lib/vip.
 *
 * The shell (Header + CategoryRail + BottomTab + AuthModal) is mounted once by
 * the root layout; this page is the swapped content column. The warm-near-black
 * luxury palette is scoped to a .vipPalette wrapper inside VipProgram (a visible
 * seam vs the app-canvas shell chrome is accepted & flagged to design).
 * ==========================================================================*/

import { VipProgram } from "@/components/vip/VipProgram";

export default function VipPage() {
  return <VipProgram />;
}
