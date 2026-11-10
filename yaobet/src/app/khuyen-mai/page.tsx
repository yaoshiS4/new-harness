/* ============================================================================
 * Yaobet — PROMOTIONS (route "/khuyen-mai").
 * ----------------------------------------------------------------------------
 * A Server Component: it fetches the promo fixtures server-side (truthful, no
 * hardcoded %) and passes them to the band components. The page mounts inside
 * the shared shell (root layout's <AppShell>) — header + category nav + bottom
 * tab bar — so it needs no chrome of its own. Wide canvas (NOT the member rail).
 *
 * Bands: PromoHero (featured + real Countdown) → PromoGrid (category-filterable
 * card grid, image SLOTS, real-or-static countdowns, honest empty states). The
 * engagement layer (wheel/leaderboard/tasks) is NOT rendered — it is gated to
 * real-feed-only and Yaobet does not operate it at v1.
 * ==========================================================================*/

import { getPromos } from "@/lib/mock";
import { PromoHero, PromoGrid } from "@/components/promo";
import { vi } from "@/lib/i18n";

export const metadata = {
  title: "Khuyến mãi — Yaobet",
};

export default async function PromotionsPage() {
  const promos = await getPromos();

  return (
    <div className="promo-khuyen-mai-page">
      <PromoHero promos={promos} />

      <section className="promo-khuyen-mai-grid-section" aria-label={vi.nav.promo}>
        <h2 className="promo-khuyen-mai-heading promo-type-h2">Tất cả khuyến mãi</h2>
        <PromoGrid promos={promos} />
      </section>
    </div>
  );
}
