/* ============================================================================
 * Icon — Yaobet inline-SVG icon set (own SVGs, no
 * iconfont, no network request). Every glyph is a 24×24 stroke/fill path drawn
 * with `currentColor` so it inherits the consuming component's color token.
 * Add an entry to ICON_PATHS to extend the set; the union `IconName` is derived
 * from it so callers are type-checked against the available glyphs.
 *
 * The <svg> carries a `data-icon="<name>"` attribute purely as a STABLE styling
 * hook: CSS-Module class names are hashed, so a parent stylesheet (e.g. Card's
 * "icons in cards scale 1.10 on hover" rule) has no other way to reach it.
 * Presentational only — no public prop or behaviour changes.
 * ==========================================================================*/

/* Each entry is the inner markup of a 0 0 24 24 viewBox. `currentColor` only. */
const ICON_PATHS = {
  home: <path d="M3 11.5 12 4l9 7.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z" fill="currentColor" />,
  promo: <path d="M4 5h16v4a2 2 0 0 0 0 6v4H4v-4a2 2 0 0 0 0-6zm8 1v12" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinejoin="round" />,
  wallet: <path d="M3 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v1h2v8h-2v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zm14 5a1 1 0 1 0 0-2 1 1 0 0 0 0 2z" fill="currentColor" />,
  deposit: <path d="M12 3v12m0 0 4-4m-4 4-4-4M4 19h16" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  account: <path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-7 8a7 7 0 0 1 14 0z" fill="currentColor" />,
  user: <path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-7 8a7 7 0 0 1 14 0z" fill="currentColor" />,
  phone: <path d="M6.5 4h-2A1.5 1.5 0 0 0 3 5.6 16 16 0 0 0 18.4 21 1.5 1.5 0 0 0 20 19.5v-2.1a1 1 0 0 0-.8-1l-3-.6a1 1 0 0 0-1 .4l-.9 1.3a12 12 0 0 1-5.3-5.3l1.3-.9a1 1 0 0 0 .4-1l-.6-3a1 1 0 0 0-1-.8z" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinejoin="round" strokeLinecap="round" />,
  mail: <path d="M3 6.5A1.5 1.5 0 0 1 4.5 5h15A1.5 1.5 0 0 1 21 6.5v11A1.5 1.5 0 0 1 19.5 19h-15A1.5 1.5 0 0 1 3 17.5zM4 7l8 6 8-6" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinejoin="round" strokeLinecap="round" />,
  history: <path d="M12 5a7 7 0 1 0 7 7m-7-7V2m0 3 3 0M12 8v4l3 2" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  message: <path d="M4 5h16v11H8l-4 3z" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinejoin="round" />,
  referral: <path d="M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm8 0a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zM3 20a6 6 0 0 1 12 0zm14 0a5 5 0 0 0-3-4.58" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  shield: <path d="M12 3 5 6v6c0 4 3 6.5 7 9 4-2.5 7-5 7-9V6z" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinejoin="round" />,
  cashback: <path d="M3 8a8 8 0 0 1 14-3m1-2v4h-4M21 16a8 8 0 0 1-14 3m-1 2v-4h4" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  vip: <path d="M3 8l4 3 5-6 5 6 4-3-2 11H5z" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinejoin="round" />,
  gift: <path d="M4 11h16v9H4zm0-4h16v4H4zm8 0v13M8 7a2 2 0 1 1 4 0 2 2 0 1 1 4 0" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinejoin="round" />,
  support: <path d="M5 12a7 7 0 0 1 14 0v4a2 2 0 0 1-2 2h-1v-6h3M5 12v4H4a1 1 0 0 1-1-1v-2a1 1 0 0 1 1-1zm0 0H4" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  grid: <path d="M4 4h7v7H4zm9 0h7v7h-7zm-9 9h7v7H4zm9 0h7v7h-7z" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinejoin="round" />,
  search: <path d="M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zm5 12 5 5" stroke="currentColor" strokeWidth="1.7" fill="none" strokeLinecap="round" />,
  close: <path d="M6 6l12 12M18 6 6 18" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" />,
  /* A bin, not an ×: the notification row's delete is PERMANENT, and an × on a
   * list row reads as "dismiss this from view" rather than "remove it". */
  trash: <path d="M4 7h16M10 7V5h4v2m-8 0 1 13h10l1-13M10 11v5m4-5v5" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  check: <path d="M5 12.5 10 17l9-10" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  chevronDown: <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  chevronRight: <path d="M9 6l6 6-6 6" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  chevronLeft: <path d="M15 6l-6 6 6 6" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  eye: <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7zm10 3a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinejoin="round" />,
  eyeOff: <path d="M4 4l16 16M9.5 9.6a3 3 0 0 0 4.2 4.2M6.7 6.8C4 8.4 2 12 2 12s4 7 10 7a9.7 9.7 0 0 0 4.3-1M11 5.1A9.6 9.6 0 0 1 12 5c6 0 10 7 10 7a18 18 0 0 1-2.4 3" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  copy: <path d="M9 9h10v10H9zM5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinejoin="round" />,
  info: <path d="M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zm0 8v5m0-8.5v.5" stroke="currentColor" strokeWidth="1.7" fill="none" strokeLinecap="round" />,
  warning: <path d="M12 4 2 20h20zM12 10v4m0 3v.5" stroke="currentColor" strokeWidth="1.7" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  empty: <path d="M4 8h16l-1.5 11H5.5zm3 0V6a5 5 0 0 1 10 0v2" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinejoin="round" />,
  retry: <path d="M20 11A8 8 0 1 0 19 15m1 5v-5h-5" stroke="currentColor" strokeWidth="1.7" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  trophy: <path d="M7 4h10v4a5 5 0 0 1-10 0zM7 6H4v1a3 3 0 0 0 3 3m10-4h3v1a3 3 0 0 1-3 3m-5 3v4m-3 4h6l-1-4h-4z" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinejoin="round" />,
  slots: <path d="M4 5h16v14H4zm0 4h16M8 5v14m8-14v14" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinejoin="round" />,
  sports: <path d="M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zm0 0v18m-9-9h18" stroke="currentColor" strokeWidth="1.5" fill="none" />,
  live: <path d="M12 9a3 3 0 1 1 0 6 3 3 0 0 1 0-6zM6.5 6.5a8 8 0 0 0 0 11M17.5 6.5a8 8 0 0 1 0 11" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />,
  card: <path d="M3 6h18v12H3zm0 4h18" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinejoin="round" />,
  lock: <path d="M6 11h12v9H6zm2 0V8a4 4 0 0 1 8 0v3" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinejoin="round" />,
  /* up-trend arrow — "Sinh lời" (yield/interest) member-hub tile */
  yield: <path d="M4 16l5-5 4 4 7-7m0 0h-5m5 0v5" stroke="currentColor" strokeWidth="1.7" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  /* ---- vertical-nav glyphs (one per gaming category) ---- */
  chip: <path d="M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zm0 5a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm0-5v4m0 10v4M3 12h4m10 0h4M5.6 5.6l2.8 2.8m7.2 7.2 2.8 2.8m0-12.8-2.8 2.8M8.4 15.6l-2.8 2.8" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  fish: <path d="M16 12c0-3-3-5-7-5-3.5 0-6 1.5-7 5 1 3.5 3.5 5 7 5 4 0 7-2 7-5zm0 0 4-3v6zM6 11.5h.01" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  ticket: <path d="M4 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2 2 2 0 0 0 0 4 2 2 0 0 1-2 2 2 2 0 0 0 0 4 2 2 0 0 1-2 2H6a2 2 0 0 1-2-2 2 2 0 0 0 0-4 2 2 0 0 1 0-4zm6 0v12" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinejoin="round" strokeDasharray="0.5 3" />,
  rooster: <path d="M14 6a3 3 0 0 0-3 3c-3 0-5 2-5 5a4 4 0 0 0 4 4h5a4 4 0 0 0 4-4c0-2-1-3-1-3l1-2-3 1c0-2-1-3-2-4zm-3 7h.01M9 21l1-2m4 2 1-2" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  table: <path d="M4 6h16v8a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3zm2 11v3m12-3v3M9 11h.01M15 13h.01" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  fast: <path d="M13 2 4 14h7l-2 8 9-12h-7z" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinejoin="round" />,
} as const;

export type IconName = keyof typeof ICON_PATHS;

export interface IconProps {
  name: IconName;
  /** pixel size; defaults to 1em so it scales with surrounding font-size */
  size?: number | string;
  /** decorative icons get aria-hidden; pass a label to expose to AT */
  label?: string;
  className?: string;
}

export function Icon({ name, size = "1em", label, className }: IconProps) {
  const dim = typeof size === "number" ? `${size}px` : size;
  return (
    <svg
      className={["ui-icon", className].filter(Boolean).join(" ")}
      data-icon={name}
      viewBox="0 0 24 24"
      width={dim}
      height={dim}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      focusable="false"
    >
      {ICON_PATHS[name]}
    </svg>
  );
}
