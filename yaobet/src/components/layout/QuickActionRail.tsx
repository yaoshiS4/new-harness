"use client";

/* ============================================================================
 * QuickActionRail — reference floating right-edge QUICK-ACTION RAIL (the `.service` /
 * `toTop` suspended column on the reference site). Fixed to the viewport's right edge on
 * desktop; on mobile (<1024px) it collapses to the bare icon stack only (no
 * promo cards), staying out of the BottomTabBar's way.
 *
 * COMPACT (reference-exact): a narrow column the width of one icon button + small
 * promo cards — NOT a wide marketing panel.
 *
 * Stack, top → bottom (reference order):
 *   1. World-Cup promo thumbnail — DISMISSABLE via a corner × (session-persisted).
 *   2. Super-jackpot promo card  — a LUCKY-SAFE jackpot figure (6/8, no 4) + a
 *      gold "Quay ngay" CTA. The figure is DATA-BOUND (passed in / mock), never
 *      animated/extrapolated — truthful-only. Also DISMISSABLE.
 *   3. Icon stack: cards (sưu tập), ticket (vé số), trophy (giải đấu), QR (tải
 *      app), CSKH headset (hỗ trợ), back-to-top (^). The two activity surfaces
 *      sit together at the top.
 *
 * UI-ONLY: no network, mock data. Opaque surfaces, reduced-motion safe,
 * z-index strictly below --z-modal so dialogs always cover it.
 * ==========================================================================*/

import { useCallback, useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { formatCount, formatVnd, isLuckySafe } from "@/lib/format";

/* Routes on which the floating promo rail is suppressed. Both are login-free
 * reference/T&C surfaces, NOT inducements — no promo cards, no super-jackpot
 * card, no icon stack there: `/cuoc-hop-le` (game-contribution rates) and
 * `/game-han-che` (the published bonus-restricted games list). Scoped to these
 * routes only; every other route is unaffected. */
const RAIL_SUPPRESSED_PATHS = new Set<string>(["/cuoc-hop-le", "/game-han-che"]);

/* ---- mock, truthful-shaped data (would arrive via an Envelope in real BE) ---- */

/** Super-jackpot pool — a resting, lucky-safe figure (888… favours 6/8, no 4). */
const JACKPOT_POOL = 8_688_888_000;

/** sessionStorage keys — dismissals persist for the browser session only. */
const SS_PROMO = "yb.rail.promo.dismissed";
const SS_JACKPOT = "yb.rail.jackpot.dismissed";

const COMPACT_UNITS = [
  { size: 1_000_000_000, unit: "tỷ ₫" },
  { size: 1_000_000, unit: "triệu ₫" },
] as const;

// Card figure: the unit is the largest size the amount reaches (tỷ from 1e9, triệu from 1e6,
// else the full figure); the amount is then rounded half up to 2 decimals in that unit, comma
// separator. A rounded result of 1000 or more moves up to the next larger unit when there is one
// (999_995_000 shows 1,00 tỷ, not 1.000,00 triệu).
function compactVnd(amount: number): { num: string; unit: string } {
  let i = COMPACT_UNITS.findIndex(({ size }) => amount >= size);
  if (i < 0) return { num: formatCount(amount), unit: "₫" };
  const toHundredths = (size: number) => Math.floor((amount * 100 + size / 2) / size);
  let hundredths = toHundredths(COMPACT_UNITS[i].size);
  if (hundredths >= 100_000 && i > 0) {
    i -= 1;
    hundredths = toHundredths(COMPACT_UNITS[i].size);
  }
  const frac = String(hundredths % 100).padStart(2, "0");
  return { num: `${formatCount(Math.floor(hundredths / 100))},${frac}`, unit: COMPACT_UNITS[i].unit };
}

/* sessionStorage is an EXTERNAL STORE, so it is read through
 * useSyncExternalStore rather than mirrored into state from an effect. The old
 * shape (useState(true) + a useEffect that immediately setState(false)) is the
 * cascading-render pattern react-hooks/set-state-in-effect flags: it renders
 * the card, then throws it away one commit later. useSyncExternalStore gives
 * the same hydration-safe behaviour — getServerSnapshot for SSR and the first
 * client paint, the real snapshot immediately after hydration — with no
 * setState in an effect and no hydration mismatch. */

/** In-memory mirror: sessionStorage writes can throw (private mode / quota), and
 *  a dismissal must still hold for the life of the tab when they do. */
const memoryDismissed = new Set<string>();

/** Same-tab subscribers — the `storage` event does NOT fire in the writing tab. */
const dismissListeners = new Set<() => void>();

function subscribeDismissed(onStoreChange: () => void): () => void {
  dismissListeners.add(onStoreChange);
  window.addEventListener("storage", onStoreChange);
  return () => {
    dismissListeners.delete(onStoreChange);
    window.removeEventListener("storage", onStoreChange);
  };
}

/** Read a session dismissal flag (SSR-safe; defaults to "not dismissed"). */
function readDismissed(key: string): boolean {
  if (memoryDismissed.has(key)) return true;
  if (typeof window === "undefined") return false;
  try {
    return window.sessionStorage.getItem(key) === "1";
  } catch {
    return false;
  }
}

/** Persist a session dismissal flag (best-effort; storage may be unavailable). */
function persistDismissed(key: string): void {
  memoryDismissed.add(key);
  try {
    window.sessionStorage.setItem(key, "1");
  } catch {
    /* ignore — private mode / quota; the memory mirror still holds it */
  }
  for (const notify of dismissListeners) notify();
}

/** Server + first-paint snapshot: nothing is dismissed, so the card renders and
 *  the client/server markup agree. Must be a stable constant fn. */
const notDismissed = () => false;

export function QuickActionRail() {
  // usePathname is SSR-safe (deterministic on server + first client paint), so
  // the guard introduces no hydration mismatch. All hooks below run every render
  // (rules-of-hooks); only the final output is suppressed on the guarded route.
  const pathname = usePathname();
  // Shown on both server + first client paint (no hydration mismatch), then
  // reconciled from sessionStorage on the post-hydration render.
  const showPromo = !useSyncExternalStore(
    subscribeDismissed,
    () => readDismissed(SS_PROMO),
    notDismissed,
  );
  const showJackpot = !useSyncExternalStore(
    subscribeDismissed,
    () => readDismissed(SS_JACKPOT),
    notDismissed,
  );
  const [openPanel, setOpenPanel] = useState<"qr" | "cskh" | null>(null);

  const dismissPromo = useCallback(() => persistDismissed(SS_PROMO), []);
  const dismissJackpot = useCallback(() => persistDismissed(SS_JACKPOT), []);

  const backToTop = useCallback(() => {
    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
  }, []);

  // Jackpot figure is a marketing numeral → must be lucky-safe; fall back to a
  // safe constant rather than ever rendering a taboo (digit-4) display value.
  const jackpot = isLuckySafe(JACKPOT_POOL) ? JACKPOT_POOL : 8_888_888_000;
  const jackpotCompact = compactVnd(jackpot);

  // Reference/T&C surfaces suppress the promo rail entirely (all hooks above
  // still ran, so this early return is rules-of-hooks safe).
  if (RAIL_SUPPRESSED_PATHS.has(pathname)) return null;

  return (
    <aside className="shell-quick-action-rail" aria-label="Thao tác nhanh">
      {/* ---------- 1 · World-Cup promo thumbnail (dismissable) ---------- */}
      {showPromo && (
        <div className="shell-quick-action-rail-promo-thumb">
          <button
            type="button"
            className="shell-quick-action-rail-promo-close"
            aria-label="Đóng quảng cáo World Cup"
            onClick={dismissPromo}
          >
            ×
          </button>
          <Link className="shell-quick-action-rail-promo-link" href="/khuyen-mai" aria-label="Khuyến mãi World Cup">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/assets/banners/pc-hero-banner-UCLfinal.jpg"
              alt="Khuyến mãi mùa giải lớn"
              className="shell-quick-action-rail-promo-img"
              width={64}
              height={48}
              loading="lazy"
            />
            <span className="shell-quick-action-rail-promo-tag">World Cup</span>
          </Link>
        </div>
      )}

      {/* ---------- 2 · Super-jackpot promo card (dismissable) ---------- */}
      {showJackpot && (
        <section className="shell-quick-action-rail-jackpot-card" aria-label="Hũ vàng siêu cấp">
          <button
            type="button"
            className="shell-quick-action-rail-promo-close"
            aria-label="Đóng hũ vàng siêu cấp"
            onClick={dismissJackpot}
          >
            ×
          </button>
          <p className="shell-quick-action-rail-jackpot-kicker">Hũ vàng</p>
          <p className="shell-quick-action-rail-jackpot-figure">
            <span className="shell-quick-action-rail-sr-only">{formatVnd(jackpot)}</span>
            <span aria-hidden="true">
              <span className="shell-quick-action-rail-jackpot-num">{jackpotCompact.num}</span>{" "}
              <span className="shell-quick-action-rail-jackpot-num">{jackpotCompact.unit}</span>
            </span>
          </p>
          <Link className="shell-quick-action-rail-jackpot-cta" href="/khuyen-mai">
            Quay ngay
          </Link>
        </section>
      )}

      {/* ---------- 3 · Icon stack ---------- */}
      <nav className="shell-quick-action-rail-icon-stack" aria-label="Tiện ích nhanh">
        {/* collection — the always-on surface */}
        <Link className="shell-quick-action-rail-icon-btn" href="/bo-suu-tap" aria-label="Bộ sưu tập">
          <CardsIcon />
          <span className="shell-quick-action-rail-icon-label">Sưu tập</span>
        </Link>

        {/* vé số — the other always-on activity surface, next to its sibling.
            "Vé số" (a ticket you hold and open), NOT the "Xổ số" lobby vertical
            (provider lottery games) — the labels stay distinct on purpose. */}
        <Link className="shell-quick-action-rail-icon-btn" href="/ve-so" aria-label="Vé số">
          <TicketIcon />
          <span className="shell-quick-action-rail-icon-label">Vé số</span>
        </Link>

        {/* trophy / tournaments */}
        <Link className="shell-quick-action-rail-icon-btn" href="/tier" aria-label="Giải đấu">
          <TrophyIcon />
          <span className="shell-quick-action-rail-icon-label">Giải đấu</span>
        </Link>

        {/* QR / app download (popover) */}
        <div
          className="shell-quick-action-rail-icon-group"
          onMouseEnter={() => setOpenPanel("qr")}
          onMouseLeave={() => setOpenPanel((p) => (p === "qr" ? null : p))}
        >
          <button
            type="button"
            className="shell-quick-action-rail-icon-btn"
            aria-label="Tải ứng dụng"
            aria-expanded={openPanel === "qr"}
            onClick={() => setOpenPanel((p) => (p === "qr" ? null : "qr"))}
          >
            <QrIcon />
            <span className="shell-quick-action-rail-icon-label">Tải app</span>
          </button>
          {openPanel === "qr" && (
            <div className="shell-quick-action-rail-popover" role="dialog" aria-label="Tải ứng dụng">
              <div className="shell-quick-action-rail-qr-box" aria-hidden="true">
                <QrGlyph />
              </div>
              <p className="shell-quick-action-rail-popover-text">Quét mã để tải ứng dụng</p>
            </div>
          )}
        </div>

        {/* CSKH / headset support (popover) */}
        <div
          className="shell-quick-action-rail-icon-group"
          onMouseEnter={() => setOpenPanel("cskh")}
          onMouseLeave={() => setOpenPanel((p) => (p === "cskh" ? null : p))}
        >
          <button
            type="button"
            className="shell-quick-action-rail-icon-btn"
            aria-label="Chăm sóc khách hàng"
            aria-expanded={openPanel === "cskh"}
            onClick={() => setOpenPanel((p) => (p === "cskh" ? null : "cskh"))}
          >
            <HeadsetIcon />
            <span className="shell-quick-action-rail-icon-label">CSKH</span>
          </button>
          {openPanel === "cskh" && (
            <div className="shell-quick-action-rail-popover" role="dialog" aria-label="Chăm sóc khách hàng">
              <p className="shell-quick-action-rail-popover-head">Hỗ trợ 24/7</p>
              <p className="shell-quick-action-rail-popover-text">Trực tuyến mọi lúc, mọi nơi</p>
            </div>
          )}
        </div>

        {/* back-to-top */}
        <button
          type="button"
          className="shell-quick-action-rail-icon-btn"
          aria-label="Lên đầu trang"
          onClick={backToTop}
        >
          <CaretUpIcon />
          <span className="shell-quick-action-rail-icon-label">Lên đầu</span>
        </button>
      </nav>
    </aside>
  );
}

/* ---- inline glyphs (no external requests; currentColor = gold/dim per state) ---- */

function CardsIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
      <rect
        x="8.5"
        y="4"
        width="11"
        height="15"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.6"
      />
      <path
        d="M6 6.5 4.6 7a2 2 0 0 0-1.3 2.5l2.6 8a2 2 0 0 0 2.5 1.3l1-.3"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
      <path
        d="M14 8.5v6M11 11.5h6"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  );
}

function TicketIcon() {
  // Scratch ticket: perforated tear-off edge + a lifted foil corner, so it
  // reads as a ticket you open rather than as a card or a coupon.
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
      <path
        d="M8 5h11a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H8"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M8 5v2M8 9v2M8 13v2M8 19v-2"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
      <path d="M11 9h6v6h-6z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M17 9l-3.4 3.4L17 13.2z" fill="currentColor" />
    </svg>
  );
}

function TrophyIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
      <path
        d="M7 4h10v3a5 5 0 0 1-10 0V4Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path
        d="M7 5H4v2a3 3 0 0 0 3 3M17 5h3v2a3 3 0 0 1-3 3M10 13h4M9 20h6M12 14v3"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function QrIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
      <rect x="4" y="4" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.6" />
      <rect x="14" y="4" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.6" />
      <rect x="4" y="14" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.6" />
      <path d="M14 14h2v2M20 14v6h-6M18 18h2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function HeadsetIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
      <path
        d="M5 13v-1a7 7 0 0 1 14 0v1"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
      <rect x="3" y="12" width="4" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
      <rect x="17" y="12" width="4" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
      <path d="M19 18v1a3 3 0 0 1-3 3h-3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function CaretUpIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
      <path d="m6 14 6-6 6 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function QrGlyph() {
  // Decorative QR placeholder (no real payload) — pure CSS-grid blocks.
  return (
    <svg viewBox="0 0 40 40" width="96" height="96" aria-hidden="true">
      <rect className="shell-quick-action-rail-qr-surface" width="40" height="40" fill="currentColor" />
      <g className="shell-quick-action-rail-qr-modules" fill="currentColor">
        <path d="M4 4h10v10H4zM6 6v6h6V6z" />
        <rect x="7" y="7" width="4" height="4" />
        <path d="M26 4h10v10H26zM28 6v6h6V6z" />
        <rect x="29" y="7" width="4" height="4" />
        <path d="M4 26h10v10H4zM6 28v6h6v-6z" />
        <rect x="7" y="29" width="4" height="4" />
        <rect x="18" y="4" width="3" height="3" />
        <rect x="18" y="10" width="3" height="3" />
        <rect x="18" y="18" width="3" height="3" />
        <rect x="26" y="18" width="3" height="3" />
        <rect x="33" y="18" width="3" height="3" />
        <rect x="18" y="26" width="3" height="3" />
        <rect x="26" y="26" width="3" height="3" />
        <rect x="33" y="33" width="3" height="3" />
        <rect x="26" y="33" width="3" height="3" />
      </g>
    </svg>
  );
}
