/* ============================================================================
 * Yaobet — /bo-suu-tap/cua-toi : the INVENTORY route.
 * ----------------------------------------------------------------------------
 * A thin server shell; the composition root is the client boundary. Nested
 * under the feature so back-navigation is obvious and the route dies with the
 * feature.
 *
 * The Suspense boundary is not decoration: the surface derives its active tab
 * from `?tab=`, and `useSearchParams()` inside a client component must sit
 * under a boundary or the route cannot be prerendered.
 * ==========================================================================*/

import type { Metadata } from "next";
import { Suspense } from "react";
import { MyCardsRoot } from "./MyCardsRoot";

export const metadata: Metadata = {
  title: "Thẻ của tôi — Yaobet",
};

export default function MyCardsPage() {
  return (
    <Suspense fallback={null}>
      <MyCardsRoot />
    </Suspense>
  );
}
