/* ============================================================================
 * Yaobet — CATEGORY / VERTICAL landing (route "/[vertical]") — home
 * game-grid, [vertical] route. The 9 Yaobet verticals (Casino, Nổ hũ,
 * Thể thao, Bắn cá, Game bài, Xổ số, Đá gà, Bàn chơi, Game nhanh).
 *
 * A Server Component: it resolves the vertical from the slug and fetches the
 * typed payload server-side (providers, games, and — for sports/esports — the
 * truthful Envelope<LiveMatch>), then passes them to the CategoryPage band
 * composition. This is the SC-by-default seam: the client islands can only
 * render a figure the server handed them.
 *
 * Unknown slug → notFound() (the [vertical]/not-found.tsx 404 surface). Static
 * sibling routes (khuyen-mai, cua-hang, the (member) group) take precedence over
 * this dynamic segment, so the dynamic route only ever resolves real verticals.
 *
 * The shared shell (Header + CategoryRail/Sheet + BottomTabBar) is mounted by
 * the ROOT layout; this page renders only the content column.
 * ==========================================================================*/

import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CategoryPage, resolveVertical, getCategoryPayload } from "@/components/category";

interface RouteParams {
  params: Promise<{ vertical: string }>;
}

export async function generateMetadata({ params }: RouteParams): Promise<Metadata> {
  const { vertical: slug } = await params;
  const vertical = await resolveVertical(slug);
  if (!vertical) return { title: "Không tìm thấy — Yaobet" };
  return {
    title: `${vertical.label} — Yaobet`,
    description: `${vertical.label} tại Yaobet — nhà cái trực tuyến.`,
  };
}

export default async function VerticalLanding({ params }: RouteParams) {
  const { vertical: slug } = await params;

  // resolve the vertical from the slug — unknown → 404 (not-found.tsx).
  const vertical = await resolveVertical(slug);
  if (!vertical) notFound();

  // server-side truthful fetch. The real-API swap replaces the bodies.
  const payload = await getCategoryPayload(vertical);

  return <CategoryPage payload={payload} />;
}
