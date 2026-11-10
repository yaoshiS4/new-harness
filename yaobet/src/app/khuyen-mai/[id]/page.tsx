/* ============================================================================
 * Yaobet — PROMOTION DETAIL (route "/khuyen-mai/[id]").
 * ----------------------------------------------------------------------------
 * A Server Component: fetches the promo fixtures and resolves the [id] match,
 * then hands the single truthful Promo to the PromoDetail client island (whose
 * "Tham gia" CTA is auth-aware). An unknown id → notFound (no fabricated promo).
 * Mounts inside the shared shell (root <AppShell>).
 * ==========================================================================*/

import { notFound } from "next/navigation";
import { getPromos } from "@/lib/mock";
import { PromoDetail } from "@/components/promo";

export default async function PromoDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const promos = await getPromos();
  const promo = promos.find((p) => p.href.endsWith(`/${id}`) || p.id === id);

  if (!promo) notFound();

  return <PromoDetail promo={promo} />;
}
