/* ============================================================================
 * Luxury VIP — LevelRing. SVG track + luxury-gold gradient arc + centered
 * "CẤP {level}" (small-caps word over a large display-face numeral). Arc length
 * reflects `percent` (wager progress toward the next tier).
 * ==========================================================================*/

export function LevelRing({
  level,
  percent,
  size = 108,
  levelWord = "CẤP",
}: {
  level: number;
  percent: number;
  size?: number;
  /** i18n level word ("CẤP" / "LEVEL"). Optional; defaults to VI. */
  levelWord?: string;
}) {
  const stroke = 7;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const dash = (Math.max(0, Math.min(100, percent)) / 100) * c;
  const mid = size / 2;

  return (
    <svg
      className="inline-grid place-items-center flex-none"
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      role="img"
      aria-label={`${levelWord} ${level}`}
    >
      <defs>
        <linearGradient id="vipRingGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" className="[stop-color:var(--vip-gold-start)]" />
          <stop offset="52%" className="[stop-color:var(--vip-gold-mid)]" />
          <stop offset="100%" className="[stop-color:var(--vip-gold-end)]" />
        </linearGradient>
      </defs>

      <circle
        className="stroke-vip-hairline fill-none"
        cx={mid}
        cy={mid}
        r={r}
        strokeWidth={stroke}
      />
      <circle
        className="[stroke:url(#vipRingGrad)] fill-none [stroke-linecap:round] [transition:stroke-dasharray_var(--dur-slow)_var(--ease-entrance)]"
        cx={mid}
        cy={mid}
        r={r}
        strokeWidth={stroke}
        strokeDasharray={`${dash} ${c}`}
        transform={`rotate(-90 ${mid} ${mid})`}
      />

      <text
        className="fill-vip-text-muted font-brand-font-body font-weight-semi tracking-[0.18em] uppercase"
        x="50%"
        y="40%"
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={size * 0.13}
      >
        {levelWord}
      </text>
      <text
        className="fill-vip-gold-mid vip-ring-numeral"
        x="50%"
        y="60%"
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={size * 0.3}
      >
        {level}
      </text>
    </svg>
  );
}
