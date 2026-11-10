/* ============================================================================
 * Yaobet — /tai-khoan loading UI (App Router Suspense fallback). Branded
 * Skeletons in each section's reserved footprint — never placeholder content
 * dressed as real. Reduced-motion → static tint sweep (motion.css).
 * ==========================================================================*/

import { Skeleton } from "@/ui";

export default function AccountLoading() {
  return (
    <section className="flex flex-col gap-band-gap min-w-[0]" aria-busy="true" aria-label="Đang tải tài khoản">
      <h1>Tài khoản</h1>
      {/* profile header */}
      <Skeleton shape="block" width="100%" height={112} />
      {/* quick actions */}
      <Skeleton shape="block" width="100%" height={96} />
      {/* menu list */}
      <Skeleton shape="block" width="100%" height={300} />
    </section>
  );
}
