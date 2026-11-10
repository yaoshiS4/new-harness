/* ============================================================================
 * Yaobet — POINTS STORE (route "/cua-hang").
 * ----------------------------------------------------------------------------
 * A Server Component: fetches the points balance + product catalog server-side
 * (truthful MOCK fixtures) and passes them to the store bands. Mounts inside the
 * shared shell (root <AppShell>) — header + category nav + bottom tab bar.
 *
 * Bands: PointsHeader (redeemable points, count kind) → ProductGrid (a client
 * island: image SLOTS, the restart-cooldown escalation summary per card, and a
 * lazy claim-decision RedeemDialog). Each Product carries the full
 * shape (face / basePoints / repeatFraction / cooldown / maxSteps / per-user
 * runtime row); the escalation math lives in lib/store/escalation.ts and the
 * grid owns loading · error(onRetry) · empty · populated. A guest tap on a
 * card CTA routes through the auth modal; honest empty when the catalog is empty.
 * ==========================================================================*/

import { getProducts, getPointsBalance } from "@/lib/mock";
import type { Product } from "@/lib/types";
import { PointsHeader, ProductGrid, StoreTerms } from "@/components/store";

export const metadata = {
  title: "Cửa hàng điểm — Yaobet",
};

export default async function StorePage() {
  // The RSC fetch is kept (server-first). A catalog-fetch failure does not crash
  // the route: the island is seeded empty and owns the error/retry surface.
  const [products, points] = await Promise.all([
    getProducts().catch((): Product[] => []),
    getPointsBalance(),
  ]);

  return (
    <div className="flex flex-col gap-space-5 min-w-[0]">
      <h1 className="store-type-h1 text-text-hi">Cửa hàng điểm</h1>
      <PointsHeader points={points} />
      <section className="flex flex-col gap-space-4" aria-label="Danh sách quà đổi điểm">
        <h2 className="store-type-h3 text-text-hi">Quà đổi điểm</h2>
        <ProductGrid products={products} points={points} />
      </section>
      <StoreTerms />
    </div>
  );
}
