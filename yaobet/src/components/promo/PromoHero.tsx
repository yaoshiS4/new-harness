/* ============================================================================
 * PromoHero — featured promo band. The
 * top of the promotions page: the first time-boxed promo gets a large featured
 * card with its real server-deadline Countdown; if none is time-boxed the first
 * promo is featured statically. Image is a token-derived SLOT.
 * Server-rendered — receives resolved fixtures, no client state needed.
 * ==========================================================================*/

import Link from "next/link";
import type { Promo } from "@/lib/types";
import { vi } from "@/lib/i18n";
import { Card, Badge, Countdown, Icon } from "@/ui";

export interface PromoHeroProps {
  promos: Promo[];
}

export function PromoHero({ promos }: PromoHeroProps) {
  if (promos.length === 0) return null;

  // prefer a time-boxed promo for the hero (it carries a real Countdown)
  const featured = promos.find((p) => p.endsAt) ?? promos[0];

  return (
    <Card variant="promo" className="promo-hero-hero">
      {/* PLACEHOLDER SLOT — token-derived gradient, awaiting art */}
      <span className="promo-hero-media" aria-hidden="true" />
      <div className="promo-hero-body">
        <Badge tone="gold">{featured.category}</Badge>
        <h1 className="promo-hero-title promo-type-h1">{featured.title}</h1>
        {featured.endsAt ? (
          <div className="promo-hero-timer">
            <span className="promo-hero-timer-label">Kết thúc sau</span>
            <Countdown endsAt={featured.endsAt} zeroLabel={vi.state.ended} />
          </div>
        ) : (
          <span className="promo-hero-evergreen">Đang diễn ra</span>
        )}
        <Link href={featured.href} className="promo-hero-cta">
          Xem chi tiết <Icon name="chevronRight" size={16} />
        </Link>
      </div>
    </Card>
  );
}
