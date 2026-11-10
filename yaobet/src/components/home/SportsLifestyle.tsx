/* ============================================================================
 * SportsLifestyle — sports / esports lifestyle cards, each with ONE compact
 * match card stacked beneath it.
 *
 * Four sports-provider lifestyle cards (the user's real key-art: SABA,
 * K-Sports, BetGaming football, e-Virtual sports) render as filled image cards
 * (object-fit: cover, no empty slots). UNDER EACH card sits one COMPACT
 * SportsMatchCard, so the section is a 4-column grid of {lifestyle card +
 * match card} columns. Esports is a SUB-TAB under sports per the Yaobet IA
 * decision — the e-Virtual card links into that sub-tab.
 *
 * Truthful-only §F: the match strip is bound to an Envelope<SportsMatch[]>.
 *   • loading → compact Skeletons under each lifestyle card.
 *   • live data → one compact card per column (paired by index).
 *   • absent/error → the match cards are omitted; the lifestyle cards (static
 *     navigation) still render. A card with no live feed shows "VS", never a
 *     fabricated score.
 * ==========================================================================*/

"use client";

import type { Envelope, SportsMatch } from "@/lib/types";
import { Card, Skeleton } from "@/ui";
import { SportsMatchCard } from "./SportsMatchCard";

export interface SportsLifestyleProps {
  /** Truthful-only §F envelope: the compact match cards rendered BELOW each
   *  lifestyle card. Absent/error → the match cards are omitted, the lifestyle
   *  cards (static navigation) still render. */
  matches?: Envelope<SportsMatch[]>;
}

/* The user's real sports key-art. Each card is a filled image
 * SLOT — object-fit:cover, no empty cards. Hrefs route into the sports vertical
 * (esports is a sub-tab). */
const SPORT_CARDS = [
  {
    id: "saba",
    src: "/assets/sports/saba-sports.png",
    kicker: "Thể thao",
    title: "SABA Sports",
    href: "/?v=sports&p=saba",
  },
  {
    id: "ksports",
    src: "/assets/sports/k-sports.png",
    kicker: "Thể thao",
    title: "K-Sports",
    href: "/?v=sports&p=ksports",
  },
  {
    id: "football",
    src: "/assets/sports/Betgming_football_grid.png",
    kicker: "Bóng đá",
    title: "Kèo bóng đá trực tiếp",
    href: "/?v=sports&sub=football",
  },
  {
    id: "evirtual",
    src: "/assets/sports/e-vitualsports.png",
    kicker: "Esports",
    title: "Thi đấu điện tử & thể thao ảo",
    href: "/?v=sports&sub=esports",
  },
] as const;

export function SportsLifestyle({ matches }: SportsLifestyleProps) {
  const loading = matches?.status === "loading";
  const liveMatches =
    matches?.status === "live" && matches.value.length > 0 ? matches.value : null;

  return (
    <section className="home-sports-lifestyle-section" aria-label="Thể thao & Esports">
      <h2 className="home-sports-lifestyle-title">Thể thao</h2>

      <div className="home-sports-lifestyle-grid">
        {SPORT_CARDS.map((c, i) => {
          const m = liveMatches?.[i];
          return (
            <div key={c.id} className="home-sports-lifestyle-column">
              {/* lifestyle entry card — filled image SLOT (user key-art) */}
              <Card
                variant="promo"
                href={c.href}
                interactive
                className="home-sports-lifestyle-life-card"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={c.src} alt={c.title} className="home-sports-lifestyle-life-img" loading="lazy" />
                <span className="home-sports-lifestyle-life-overlay" aria-hidden />
                <span className="home-sports-lifestyle-life-kicker">{c.kicker}</span>
                <span className="home-sports-lifestyle-life-title">{c.title}</span>
              </Card>

              {/* ONE compact match card under each lifestyle card (§F-bound).
               *  The slot grows so all 4 match cards equalize to one height. */}
              {loading ? (
                <div className="home-sports-lifestyle-match-slot">
                  <Skeleton width="100%" height="168px" />
                </div>
              ) : m ? (
                <div className="home-sports-lifestyle-match-slot">
                  <SportsMatchCard match={m} />
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </section>
  );
}
