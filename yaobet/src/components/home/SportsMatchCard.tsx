/* ============================================================================
 * SportsMatchCard — COMPACT match card (sits UNDER each sports lifestyle
 * card, 4 across). A small "TRỰC TIẾP"-sized footprint, NOT the big
 * two-column card.
 *
 * Layout (compact, UNIFORM HEIGHT — all 4 cards line up regardless of content):
 *   ┌────────────────────────────────┐
 *   │ league name                     │  ← tiny kicker
 *   │ 🏳 Team A · [VS | Live + 1–0] · Team B 🏳 │  ← fixture row (fixed height)
 *   │ Kèo chấp   [c][c][c]            │  ← market (handicap, 3 tight cells)
 *   │        [ Cược ngay ]            │  ← small gold CTA
 *   └────────────────────────────────┘
 *
 * Only the handicap market ("Kèo chấp") is shown; "Kèo tài xỉu" is omitted on
 * the home card. The fixture centre reserves a fixed height so a live score
 * row and a "VS" row produce IDENTICAL card heights.
 *
 * TRUTHFUL-ONLY: every figure is data-bound.
 *   • phase "pre"  → centre = "VS", NO score is drawn.
 *   • phase "live" → "Live" text label (never colour-only) + the real score.
 *   • an odds cell with price === null renders a dash, never a fabricated price.
 * Reads --brand-* / semantic tokens only (gold-on-dark; 16px gap).
 * ==========================================================================*/

"use client";

import type { SportsMatch, OddsCell } from "@/lib/types";
import { vi } from "@/lib/i18n";
import { formatOdds } from "@/lib/format";

export interface SportsMatchCardProps {
  match: SportsMatch;
}

export function SportsMatchCard({ match }: SportsMatchCardProps) {
  const live = match.phase === "live";

  return (
    <article className="home-sports-match-card-card" aria-label={`${match.home.name} – ${match.away.name}`}>
      {/* league / competition kicker */}
      <span className="home-sports-match-card-league">{match.league}</span>

      {/* fixture row: Team A · centre status · Team B */}
      <div className="home-sports-match-card-fixture">
        <Team side="home" team={match.home} />

        <div className="home-sports-match-card-center">
          {live ? (
            <>
              <span className="home-sports-match-card-live-tag">
                <span className="home-sports-match-card-live-dot" aria-hidden />
                {vi.state.live}
              </span>
              {match.score && (
                <span className="home-sports-match-card-score" aria-label="Tỷ số">
                  {match.score[0]}
                  <span className="home-sports-match-card-score-sep" aria-hidden>
                    –
                  </span>
                  {match.score[1]}
                </span>
              )}
            </>
          ) : (
            <span className="home-sports-match-card-vs" aria-label="Chưa diễn ra">
              VS
            </span>
          )}
        </div>

        <Team side="away" team={match.away} />
      </div>

      {/* market — Kèo chấp (handicap) ONLY. "Kèo tài xỉu" intentionally omitted
       *  from the home card to keep all 4 cards compact + uniform. */}
      <Market market={match.markets[0]} />

      {/* small gold CTA — "Cược ngay" */}
      <a className="home-sports-match-card-cta" href={`/?v=sports&m=${match.id}`}>
        Cược ngay
      </a>
    </article>
  );
}

function Team({ team, side }: { team: SportsMatch["home"]; side: "home" | "away" }) {
  return (
    <div className="home-sports-match-card-team" data-side={side}>
      {team.flag && (
        <span className="home-sports-match-card-flag" aria-hidden>
          {team.flag}
        </span>
      )}
      <span className="home-sports-match-card-team-name">{team.name}</span>
    </div>
  );
}

function Market({ market }: { market: SportsMatch["markets"][number] }) {
  return (
    <div className="home-sports-match-card-market">
      <span className="home-sports-match-card-market-name">{market.name}</span>
      <div className="home-sports-match-card-cells">
        {market.cells.map((c, i) => (
          <OddsCellView key={`${c.label}-${i}`} cell={c} />
        ))}
      </div>
    </div>
  );
}

function OddsCellView({ cell }: { cell: OddsCell }) {
  const suspended = cell.price === null;
  return (
    <div className="home-sports-match-card-cell" data-suspended={suspended || undefined}>
      <span className="home-sports-match-card-cell-label">{cell.label}</span>
      <span className="home-sports-match-card-cell-price">
        {suspended ? <span aria-label="Tạm dừng">—</span> : formatOdds(cell.price as number)}
      </span>
    </div>
  );
}
