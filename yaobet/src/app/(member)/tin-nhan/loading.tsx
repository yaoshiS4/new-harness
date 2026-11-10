/* ============================================================================
 * Yaobet — /tin-nhan loading UI (App Router Suspense fallback; the page is now
 * an async Server Component). Branded Skeletons in the message panel footprint
 * — a header bar + three card rows — NEVER placeholder text dressed as data.
 * Reduced-motion → the Skeleton sweep falls back to a static tint (motion.css).
 * Mirrors apps/web/src/app/(member)/vi-tien/loading.tsx.
 * ==========================================================================*/

import { Skeleton } from "@/ui";

export default function MessagesLoading() {
  return (
    <section aria-busy="true" aria-label="Đang tải tin nhắn">
      {/* header bar (title + actions cluster) */}
      <Skeleton shape="block" width="100%" height={56} />
      {/* message card rows */}
      <div
        style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)", marginTop: "var(--space-5)" }}
      >
        <Skeleton shape="block" width="100%" height={84} />
        <Skeleton shape="block" width="100%" height={84} />
        <Skeleton shape="block" width="100%" height={84} />
      </div>
    </section>
  );
}
