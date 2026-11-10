/* ============================================================================
 * Yaobet — the pack-opening stage (Zone 1).
 * ----------------------------------------------------------------------------
 * A row of foil packs on a lit stage. Tap one to select it, then tear it open.
 * The card scales out of the torn pack and stays on the stage until the next
 * open, so the surface is never empty.
 *
 * One honesty rule the code keeps: THE DRAW IS RESOLVED BEFORE THE TEAR
 * ANIMATION RUNS. Which pack you pick does not change what is inside — the
 * pick is a ritual, and the UI never suggests otherwise. Resolving on tap
 * would make pack position appear to matter, which is a lie with a prize
 * attached.
 *
 * NO REWARD VALUE IS PASSED INTO THIS COMPONENT. That is the information
 * firewall: money lives in Zone 2, chance lives here, and the separation is
 * enforced by the props rather than by anyone remembering the rule. The terms
 * button below is a ZERO-ARGUMENT CALLBACK for the same reason: the stage asks
 * for the terms to be opened and never learns what they say. The overlay and
 * its content are rendered by the parent, as a SIBLING of this component.
 * ==========================================================================*/

"use client";

import { useEffect, useState } from "react";
import type { OpenOutcome } from "@/lib/collection";
import { cardById } from "@/lib/collection/fixtures/epl";
import { Icon } from "@/ui/Icon/Icon";
import { CardArt } from "./CardArt";

type Phase = "idle" | "tearing" | "revealed";

interface Props {
  opens: number;
  last: OpenOutcome | null;
  busy: boolean;
  onOpen: () => void | Promise<void>;
  /** carries NO data, in either direction — see the firewall note above */
  onOpenInfo: () => void;
  onOpenHistory: () => void;
}

const PACKS = [0, 1, 2, 3, 4];

export function PackStage({
  opens,
  last,
  busy,
  onOpen,
  onOpenInfo,
  onOpenHistory,
}: Props) {
  const [picked, setPicked] = useState(2);
  const [phase, setPhase] = useState<Phase>(last ? "revealed" : "idle");
  const card = last ? cardById(last.cardId) : null;
  const rare = card?.tierId === "rare";

  // A new outcome arriving drives the tear → reveal sequence. The rule guards
  // against render loops from synchronous setState in an effect; this is a
  // one-shot transition keyed on a new outcome, not a loop.
  useEffect(() => {
    if (!last) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPhase("tearing");
    const t = setTimeout(() => setPhase("revealed"), 620);
    return () => clearTimeout(t);
  }, [last]);

  const canOpen = opens > 0 && !busy;

  return (
    <section className="collection-pack-stage" aria-label="Mở thẻ">
      <Stadium />

      {/* Two reference affordances, paired. Both are ZERO-ARGUMENT callbacks —
          the overlays and their content are rendered by the parent, so no
          reward value can reach this component. That is the firewall, and it
          holds at two buttons exactly as it held at one.

          History became a modal only once it was PAGINATED (50 rows behind
          `Xem thêm`). The original objection was an unbounded list inside a
          focus-trapped, scroll-locked sheet — a phone scroll-trap with no
          floor. The panel still carries a link to its own URL, because
          "send me the link to my history" is a real support sentence. */}
      <div className="collection-pack-chrome">
        <button
          type="button"
          className="collection-pack-info"
          onClick={onOpenHistory}
          aria-label="Lịch sử"
        >
          <Icon name="history" size={20} />
        </button>
        <button
          type="button"
          className="collection-pack-info"
          onClick={onOpenInfo}
          aria-label="Điều khoản"
        >
          <Icon name="info" size={20} />
        </button>
      </div>

      {/* ── the stage ──────────────────────────────────────────────────── */}
      <div className="collection-pack-floor">
        {phase !== "revealed" && (
          <ul className="collection-pack-packs">
            {PACKS.map((i) => (
              <li key={i} className="collection-pack-pack-slot">
                <button
                  type="button"
                  className={`collection-pack-pack ${picked === i ? "collection-pack-picked" : ""} ${
                    phase === "tearing" && picked === i ? "collection-pack-tear" : ""
                  } ${phase === "tearing" && picked !== i ? "collection-pack-dim" : ""}`}
                  style={{ ["--i" as string]: String(i - 2) }}
                  onClick={() => phase === "idle" && setPicked(i)}
                  aria-label={`Túi ${i + 1}`}
                  aria-pressed={picked === i}
                  disabled={phase !== "idle"}
                >
                  <Foil />
                </button>
              </li>
            ))}
          </ul>
        )}

        {/* ONE reveal treatment, for every card. `rare` still reaches `CardArt`
            — the face draws its own gold stroke and foil — and it still changes
            the line of copy. What it no longer does is buy the prize a looping
            gold glow the common cards do not get: that is rarity-differentiated
            motion, which is the pack-stage form of the size-ranking this
            feature refuses on the rails. */}
        {phase === "revealed" && card && (
          <div className="collection-pack-prize">
            <div className="collection-pack-prize-card">
              <CardArt card={card} rare={rare} />
            </div>
            <p className="collection-pack-prize-line">
              {last?.duplicate ? "Trùng thẻ" : rare ? "Thẻ hiếm!" : "Thẻ mới"}
            </p>
            {/* A duplicate used to be announced as a gain — `+N mảnh` — in the
                win colour, for a currency with no sink and no balance shown
                anywhere. Telling a player they received something they cannot
                use is the defect support find first. The
                true statement is that they already hold it. */}
            {last?.duplicate && (
              <p className="collection-pack-prize-sub">Bạn đã có thẻ này.</p>
            )}
          </div>
        )}
      </div>

      {/* ── the action ─────────────────────────────────────────────────── */}
      <div className="collection-pack-action-wrap">
        <button
          type="button"
          className="collection-pack-cta"
          onClick={() => {
            if (phase === "revealed") setPhase("idle");
            void onOpen();
          }}
          disabled={!canOpen}
        >
          {phase === "revealed" ? "MỞ TIẾP" : "MỞ"}
        </button>
        <p className="collection-pack-turns">
          Lượt mở còn lại: <strong>{opens}</strong>
        </p>
      </div>
    </section>
  );
}

/* ----------------------------------------------------------------------------
 * The stadium. Drawn, not photographed — it themes with the season and costs
 * nothing to ship.
 * --------------------------------------------------------------------------*/

function Stadium() {
  return (
    <svg className="collection-pack-stadium" viewBox="0 0 390 460" preserveAspectRatio="xMidYMid slice" aria-hidden>
      <defs>
        <linearGradient id="st-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="hsl(214 52% 16%)" />
          <stop offset="70%" stopColor="hsl(210 46% 22%)" />
          <stop offset="100%" stopColor="hsl(206 40% 28%)" />
        </linearGradient>
        <linearGradient id="st-grass" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="hsl(122 34% 30%)" />
          <stop offset="100%" stopColor="hsl(128 40% 20%)" />
        </linearGradient>
        <radialGradient id="st-flood" cx="0.5" cy="0" r="0.8">
          <stop offset="0%" stopColor="currentColor" stopOpacity="0.34" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
        </radialGradient>
      </defs>

      <rect width="390" height="460" fill="url(#st-sky)" />

      {/* stands */}
      <path d="M0 0 h390 v150 l-90 26 h-210 l-90 -26 z" fill="hsl(218 40% 13%)" />
      {[0, 1, 2, 3, 4, 5, 6, 7].map((r) =>
        Array.from({ length: 26 }).map((_, c) => (
          <circle
            key={`${r}-${c}`}
            cx={8 + c * 15 + (r % 2) * 7}
            cy={22 + r * 16}
            r="2.6"
            fill="currentColor"
            opacity={0.05 + ((r * 7 + c) % 5) * 0.02}
          />
        )),
      )}

      {/* floodlights */}
      {[58, 195, 332].map((x) => (
        <g key={x}>
          <ellipse cx={x} cy="8" rx="46" ry="18" fill="url(#st-flood)" />
          <rect x={x - 22} y="2" width="44" height="12" rx="3" fill="hsl(48 90% 78%)" opacity="0.85" />
        </g>
      ))}

      {/* pitch */}
      <path d="M0 176 h390 v284 h-390 z" fill="url(#st-grass)" />
      {Array.from({ length: 9 }).map((_, i) => (
        <path
          key={i}
          d={`M${-60 + i * 62} 176 L${-160 + i * 118} 460 L${-60 + i * 118} 460 L${-28 + i * 62} 176 z`}
          fill="currentColor"
          opacity={i % 2 ? 0.05 : 0}
        />
      ))}
      <path d="M0 176 h390" stroke="currentColor" strokeOpacity="0.22" strokeWidth="2" />

      {/* goal */}
      <g stroke="currentColor" strokeOpacity="0.5" strokeWidth="3" fill="none">
        <path d="M118 300 h154 v66 h-154 z" />
        <path d="M118 300 l-16 -14 h186 l-16 14" />
      </g>
      <path d="M118 300 h154 v66 h-154 z" fill="currentColor" opacity="0.04" />
    </svg>
  );
}

/** A foil pack face. Drawn, so it costs nothing and themes with the season. */
function Foil() {
  return (
    <svg viewBox="0 0 120 168" className="collection-pack-foil" aria-hidden>
      <defs>
        <linearGradient id="pk" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="hsl(268 78% 62%)" />
          <stop offset="45%" stopColor="hsl(282 72% 52%)" />
          <stop offset="100%" stopColor="hsl(258 70% 42%)" />
        </linearGradient>
        <linearGradient id="pkSheen" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="currentColor" stopOpacity="0" />
          <stop offset="50%" stopColor="currentColor" stopOpacity="0.42" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
        </linearGradient>
      </defs>
      <rect x="4" y="2" width="112" height="164" rx="8" fill="url(#pk)" />
      <rect className="collection-pack-sheen" x="4" y="2" width="112" height="164" rx="8" fill="url(#pkSheen)" />
      <circle cx="60" cy="78" r="34" fill="none" stroke="currentColor" strokeOpacity="0.55" strokeWidth="2.5" />
      <circle cx="60" cy="78" r="26" fill="currentColor" fillOpacity="0.12" />
      {/* trophy mark */}
      <g transform="translate(60 78)" fill="currentColor" fillOpacity="0.9">
        <path d="M-11 -16 h22 v9 a11 11 0 0 1 -22 0 z" />
        <path d="M-11 -14 h-6 v5 a7 7 0 0 0 7 7 M11 -14 h6 v5 a7 7 0 0 1 -7 7" fill="none" stroke="currentColor" strokeWidth="2.4" strokeOpacity="0.9" />
        <path d="M-4 2 h8 v6 h5 v4 h-18 v-4 h5 z" />
      </g>
      <path d="M4 26 h112 M4 142 h112" stroke="currentColor" strokeOpacity="0.22" strokeWidth="1.5" strokeDasharray="4 5" />
    </svg>
  );
}
