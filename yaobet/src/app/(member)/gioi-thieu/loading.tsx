/* ============================================================================
 * Yaobet — /gioi-thieu loading UI (App Router Suspense fallback). Branded
 * Skeletons in each band's reserved footprint — never placeholder content
 * dressed as real. Reduced-motion → static tint sweep (motion.css).
 * Mirrors the page bands: reward-overview · referral-method · commission · steps.
 * ==========================================================================*/

import { Skeleton } from "@/ui";
import { vi } from "@/lib/i18n";

export default function ReferralLoading() {
  return (
    <div className="flex flex-col gap-space-5 min-w-[0]" aria-busy="true" aria-label="Đang tải giới thiệu">
      <h1 className="promo-type-h1 text-text-hi">{vi.referral.pageHeading}</h1>
      {/* reward-overview band */}
      <Skeleton shape="block" width="100%" height={120} />
      {/* referral-method band (code/link + QR tile) */}
      <Skeleton shape="block" width="100%" height={176} />
      {/* commission band */}
      <Skeleton shape="block" width="100%" height={96} />
      {/* how-it-works step grid */}
      <Skeleton shape="block" width="100%" height={240} />
    </div>
  );
}
