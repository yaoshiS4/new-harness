/* ============================================================================
 * Yaobet — trading-card art.
 * ----------------------------------------------------------------------------
 * Hand-authored SVG, not photography. The mechanic must not depend on any
 * particular asset — art is CONTENT and swaps with the theme, and there is a
 * gate on real player likenesses before production. This renders a
 * card FACE (kit colours, shirt number, rating, foil on rares) so the demo
 * reads as a real collectible without shipping a likeness.
 * ==========================================================================*/

"use client";

import type { DemoCard } from "@/lib/collection/fixtures/epl";
import { CLUB_ACCENT } from "@/lib/collection/fixtures/epl";

interface Props {
  card: DemoCard;
  rare: boolean;
  /** dimmed treatment for a card the player does not own */
  ghost?: boolean;
  /**
   * Accessible name override. Ownership is conveyed by a CSS filter alone —
   * invisible to assistive tech — so the caller that knows the holding passes
   * the full sentence ("… — đang giữ 4 thẻ"). Defaults to the card's name, and
   * the label replaces it rather than adding a second announcement.
   */
  label?: string;
}

/** Deterministic shirt number from the id — stable across renders. */
function shirtNumber(id: string): number {
  let h = 0;
  for (let i = 0; i < id.length; i += 1) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return (h % 32) + 1;
}

/** Deterministic rating, 78–95, weighted up for rares. */
function rating(id: string, rare: boolean): number {
  let h = 0;
  for (let i = 0; i < id.length; i += 1) h = (h * 17 + id.charCodeAt(i)) >>> 0;
  return rare ? 88 + (h % 8) : 78 + (h % 10);
}

export function CardArt({ card, rare, ghost = false, label }: Props) {
  const accent = CLUB_ACCENT[card.club] ?? "40 10% 60%";
  const num = shirtNumber(card.id);
  const rtg = rating(card.id, rare);
  const uid = `c-${card.id}`;

  return (
    <div
      className={`relative w-full aspect-[300/420] rounded-md overflow-hidden [background:var(--surface-2)] ${rare ? "[outline:1px_solid_var(--brand-accent-hairline)] outline-offset-[-1px]" : ""} ${ghost ? "[filter:grayscale(0.85)_brightness(0.62)] opacity-[0.72]" : ""}`}
      style={{ ["--accent" as string]: accent }}
    >
      <svg viewBox="0 0 300 420" className="block w-full h-full text-text-hi" role="img" aria-label={label ?? card.name}>
        <defs>
          <linearGradient id={`${uid}-bg`} x1="0" y1="0" x2="0.4" y2="1">
            <stop offset="0%" stopColor={`hsl(${accent} / 0.9)`} />
            <stop offset="55%" stopColor={`hsl(${accent} / 0.42)`} />
            <stop offset="100%" stopColor="hsl(220 24% 9%)" />
          </linearGradient>
          <linearGradient id={`${uid}-foil`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="hsl(48 100% 72%)" stopOpacity="0.85" />
            <stop offset="35%" stopColor="hsl(320 90% 70%)" stopOpacity="0.5" />
            <stop offset="65%" stopColor="hsl(190 95% 68%)" stopOpacity="0.5" />
            <stop offset="100%" stopColor="hsl(48 100% 72%)" stopOpacity="0.85" />
          </linearGradient>
          <radialGradient id={`${uid}-spot`} cx="0.5" cy="0.3" r="0.7">
            <stop offset="0%" stopColor="currentColor" stopOpacity="0.22" />
            <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
          </radialGradient>
          <linearGradient id={`${uid}-scrim`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="hsl(220 30% 6%)" stopOpacity="0" />
            <stop offset="60%" stopColor="hsl(220 30% 6%)" stopOpacity="0.72" />
            <stop offset="100%" stopColor="hsl(220 30% 6%)" stopOpacity="0.95" />
          </linearGradient>
          <clipPath id={`${uid}-clip`}>
            <rect x="0" y="0" width="300" height="420" rx="18" />
          </clipPath>
        </defs>

        <g clipPath={`url(#${uid}-clip)`}>
          <rect width="300" height="420" fill={`url(#${uid}-bg)`} />

          {card.artSrc ? (
            <>
              {/* Supplied photography. `slice` fills the card and crops rather
                  than letterboxing; the nameplate sits over the bottom strip,
                  which is also where agency watermarks land. */}
              <image
                href={card.artSrc}
                x="0"
                y="0"
                width="300"
                height="420"
                preserveAspectRatio="xMidYMin slice"
              />
              {/* club wash + bottom scrim, so the nameplate stays readable
                  over any photograph without hand-tuning each one */}
              <rect width="300" height="420" fill={`hsl(${accent} / 0.16)`} />
              <rect y="250" width="300" height="170" fill={`url(#${uid}-scrim)`} />
            </>
          ) : (
            <>
              <rect width="300" height="420" fill={`url(#${uid}-spot)`} />

              {/* pitch arcs — subtle depth, not decoration for its own sake */}
              <circle cx="150" cy="150" r="118" fill="none" stroke="currentColor" strokeOpacity="0.07" strokeWidth="2" />
              <circle cx="150" cy="150" r="76" fill="none" stroke="currentColor" strokeOpacity="0.05" strokeWidth="2" />

              {/* player silhouette */}
              <g transform="translate(150 250)" fill="hsl(220 30% 6%)" fillOpacity="0.92">
                <circle cx="0" cy="-118" r="30" />
                <path d="M-52 -84 q52 -22 104 0 l16 84 q-70 20 -136 0 z" />
                <path d="M-52 -84 l-26 74 18 10 26 -60 z" />
                <path d="M52 -84 l26 74 -18 10 -26 -60 z" />
                <path d="M-40 0 l-6 96 26 0 20 -74 20 74 26 0 -6 -96 z" />
              </g>

              {/* kit stripe + shirt number */}
              <g transform="translate(150 166)">
                <rect x="-46" y="-4" width="92" height="70" rx="8" fill="currentColor" fillOpacity="0.1" />
                <text
                  x="0"
                  y="46"
                  textAnchor="middle"
                  fontSize="52"
                  fontWeight="600"
                  fill="currentColor"
                  fillOpacity="0.9"
                >
                  {num}
                </text>
              </g>
            </>
          )}

          {rare && (
            <rect
              className="animate-[card-foil-sweep_4.5s_ease-in-out_infinite] mix-blend-screen motion-reduce:animate-none motion-reduce:opacity-[0.28]"
              width="300"
              height="420"
              fill={`url(#${uid}-foil)`}
              opacity="0.28"
            />
          )}

          {/* rating badge */}
          <g transform="translate(30 34)">
            <rect x="-18" y="-20" width="64" height="52" rx="10" fill="hsl(220 30% 8%)" fillOpacity="0.82" />
            <text x="14" y="6" textAnchor="middle" fontSize="26" fontWeight="600" fill="currentColor">
              {rtg}
            </text>
            <text x="14" y="22" textAnchor="middle" fontSize="9" letterSpacing="1.2" fill="currentColor" fillOpacity="0.65">
              POWER
            </text>
          </g>

          {/* name plate */}
          <g>
            <rect x="0" y="336" width="300" height="84" fill="hsl(220 30% 6%)" fillOpacity="0.88" />
            <text x="150" y="368" textAnchor="middle" fontSize="19" fontWeight="600" fill="currentColor">
              {card.name}
            </text>
            <text x="150" y="392" textAnchor="middle" fontSize="12" fill="currentColor" fillOpacity="0.6">
              {card.club} · {card.position}
            </text>
          </g>

          <rect
            x="1"
            y="1"
            width="298"
            height="418"
            rx="18"
            fill="none"
            stroke={rare ? "hsl(48 100% 70%)" : `hsl(${accent} / 0.7)`}
            strokeWidth="2"
          />
        </g>
      </svg>
    </div>
  );
}

/** The face-down back, used by the pick carousel. */
export function CardBack({ dealt }: { dealt?: boolean }) {
  return (
    <div className={`relative w-full aspect-[300/420] rounded-md overflow-hidden [background:var(--surface-2)] [outline:1px_solid_var(--border)] outline-offset-[-1px] ${dealt ? "animate-[dealIn_420ms_cubic-bezier(0.2,0.8,0.2,1)_backwards] motion-reduce:animate-none" : ""}`}>
      <svg viewBox="0 0 300 420" className="block w-full h-full" role="img" aria-label="Thẻ úp">
        <defs>
          <linearGradient id="back-bg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="hsl(222 30% 16%)" />
            <stop offset="100%" stopColor="hsl(222 34% 8%)" />
          </linearGradient>
        </defs>
        <rect width="300" height="420" rx="18" fill="url(#back-bg)" />
        <g stroke="hsl(43 74% 62%)" strokeOpacity="0.5" fill="none" strokeWidth="2">
          <rect x="14" y="14" width="272" height="392" rx="12" />
          <circle cx="150" cy="210" r="58" />
          <circle cx="150" cy="210" r="38" strokeOpacity="0.3" />
          <path d="M150 152 L150 268 M92 210 L208 210" strokeOpacity="0.25" />
        </g>
        <text
          x="150"
          y="218"
          textAnchor="middle"
          fontSize="26"
          fontWeight="600"
          fill="hsl(43 74% 62%)"
          fillOpacity="0.9"
        >
          Y
        </text>
      </svg>
    </div>
  );
}
