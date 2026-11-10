/* ============================================================================
 * Yaobet — /vi-tien loading UI (App Router Suspense fallback). Per §F the
 * MANDATORY loading state: branded Skeletons in each band's reserved footprint
 * — NEVER a placeholder digit, a "0", or a last-known balance dressed as live.
 * Reduced-motion → the Skeleton sweep falls back to a static tint (motion.css).
 * ==========================================================================*/

import { Skeleton } from "@/ui";

export default function WalletLoading() {
  return (
    <section className="flex flex-col gap-space-5 min-w-[0]" aria-busy="true" aria-label="Đang tải ví">
      <h1 className="text-t-h1 text-text-hi font-weight-bold">Ví tiền</h1>
      {/* balance hero */}
      <Skeleton shape="block" width="100%" height={168} />
      {/* deposit / withdraw pair */}
      <Skeleton shape="block" width="100%" height={280} />
      {/* product rows + history */}
      <Skeleton shape="block" width="100%" height={180} />
      <Skeleton shape="block" width="100%" height={220} />
    </section>
  );
}
