/* ============================================================================
 * Yaobet — Tier ladder detail page (route "/tier")
 * (the ladder-detail companion to /vip).
 * ----------------------------------------------------------------------------
 * The whale-aspiration deep-dive on the bậc-thang: every tier laid out in full
 * (badge SLOT + level + name + %-of-play rate + the per-tier perk list), the
 * full privilege matrix (frozen-first-column scroll @375), the perk gallery,
 * and the upgrade/rebate rules. Truthful throughout — rates are VIP-BRD fixture
 * marketing copy, never a fabricated ledger figure; the current-tier card's
 * turnover-to-next-tier is data-gated (Live | loading | error | absent).
 *
 * A Server Component fetching the fixtures + the progress envelope; the shell
 * is mounted ONCE by the root layout. Auth-aware via useAuth inside the client
 * feature components (member tier highlight / guest join-prompt).
 * ==========================================================================*/

import Link from "next/link";
import { getVipTiers, getPerks, getVipProgress } from "@/lib/mock";
import { Icon } from "@/ui";
import {
  CurrentTierCard,
  TierLadder,
  PrivilegeTable,
  PerkGallery,
  VipRules,
  VipSection,
  vipCopy,
} from "@/components/vip";

export default async function TierPage() {
  const [tiers, perks, progress] = await Promise.all([
    getVipTiers(),
    getPerks(),
    getVipProgress(),
  ]);

  return (
    <div className="flex flex-col gap-space-6 pt-space-4 px-[0] pb-space-8 min-w-[0]">
      <Link href="/vip" className="inline-flex items-center gap-space-1 self-start text-t-sm text-text-mid no-underline min-h-tap-min hover:text-text-hi">
        <Icon name="chevronLeft" size={16} /> {vipCopy.backToVip}
      </Link>

      {/* intro */}
      <header className="flex flex-col gap-space-2">
        <h1 className="inline-flex items-center gap-space-2 text-t-h1 font-weight-bold text-text-hi">
          <Icon name="trophy" size={26} className="text-brand-accent-fg" />
          {vipCopy.ladderHeading}
        </h1>
        <p className="text-t-body leading-lh-body text-text-mid max-w-[64ch]">{vipCopy.pageIntro}</p>
      </header>

      {/* current-tier card — data-gated turnover-to-next-tier */}
      <CurrentTierCard tiers={tiers} progress={progress} />

      {/* the full ladder (non-compact: shows per-tier perk lines) */}
      <VipSection title={vipCopy.ladderHeading} icon="vip">
        <TierLadder tiers={tiers} />
      </VipSection>

      {/* full privilege matrix */}
      <VipSection title={vipCopy.privilegeHeading} icon="grid">
        <PrivilegeTable tiers={tiers} />
      </VipSection>

      {/* perks */}
      <VipSection title={vipCopy.perksHeading} icon="gift">
        <PerkGallery perks={perks} />
      </VipSection>

      {/* rules */}
      <VipSection title={vipCopy.rulesHeading} icon="info">
        <VipRules />
      </VipSection>
    </div>
  );
}
