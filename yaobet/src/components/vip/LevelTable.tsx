/* ============================================================================
 * Luxury VIP — LevelTable. 6 metric rows × levels 1..10 of the SELECTED tier,
 * every value single-sourced from formulas.ts. Sticky first col + header + corner,
 * horizontal scroll on narrow screens.
 *
 * Member highlight (currentTierIndex !== null):
 *   - selected tier === current tier → spotlight the currentLevel column
 *     (gold band, bold), dim + lock levels ABOVE currentLevel;
 *   - selected tier ABOVE current tier → dim ALL cells (unreached);
 *   - selected tier BELOW current tier → plain.
 * Guest (currentTierIndex === null) → plain, bare "CẤP n" headers, no highlight.
 * ==========================================================================*/
import {
  fmtCash,
  fmtGift,
  fmtRate,
  getVipCopy,
  giftAt,
  rate,
  type Lang,
  type VipTierDef,
} from "@/lib/vip";

const LEVELS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

export function LevelTable({
  tier,
  selectedTierIndex,
  currentTierIndex,
  currentLevel,
  lang,
}: {
  tier: VipTierDef;
  selectedTierIndex: number;
  currentTierIndex: number | null;
  currentLevel: number | null;
  lang: Lang;
}) {
  const copy = getVipCopy(lang);

  const isOwnTier =
    currentTierIndex !== null && selectedTierIndex === currentTierIndex;
  const isAboveCurrent =
    currentTierIndex !== null && selectedTierIndex > currentTierIndex;

  /** `money` rows keep a neutral ink in the spotlight column: money is never gold. */
  const rows: { key: string; label: string; money?: boolean; cell: (level: number) => string }[] =
    [
      { key: "gift", label: copy.rbGift, money: true, cell: (l) => fmtGift(giftAt(selectedTierIndex, l)) },
      { key: "live", label: copy.rbLive, cell: (l) => fmtRate(rate(tier.rebate.live, l)) },
      { key: "sports", label: copy.rbSports, cell: (l) => fmtRate(rate(tier.rebate.sports, l)) },
      { key: "slots", label: copy.rbSlots, cell: (l) => fmtRate(rate(tier.rebate.slots, l)) },
      { key: "table", label: copy.rbTable, cell: (l) => fmtRate(rate(tier.rebate.table, l)) },
      { key: "cash", label: copy.rbCashback, cell: (l) => fmtCash(rate(tier.cash, l)) },
    ];

  /** true → gold spotlight column (only the member's own current level). */
  const isSpotlight = (level: number) =>
    isOwnTier && currentLevel !== null && level === currentLevel;

  /** true → locked-ahead within own tier (dim + lock glyph in header). */
  const isLockedAhead = (level: number) =>
    isOwnTier && currentLevel !== null && level > currentLevel;

  /** true → value should render in the disabled/unreached colour. */
  const isDimmed = (level: number) => isAboveCurrent || isLockedAhead(level);

  return (
    <div className="overflow-x-auto rounded-vip-radius-table border border-vip-hairline [background:var(--vip-panel-bg)] [-webkit-overflow-scrolling:touch]">
      <table className="[border-collapse:separate] [border-spacing:0] table-fixed w-full min-w-[900px] font-brand-font-num tabular-nums">
        <thead>
          <tr>
            <th
              className="py-space-3 px-space-4 max-900:px-space-3 text-left border-b-2 border-b-vip-hairline border-l border-l-transparent border-r border-r-vip-hairline whitespace-nowrap text-vip-text-muted [background:var(--vip-inner-bg)] text-t-sm sticky left-[0] top-[0] z-(--z-sticky) w-[200px] font-brand-font-body font-weight-semi"
              scope="col"
            />
            {LEVELS.map((level) => (
              <th
                key={level}
                scope="col"
                className={
                  isSpotlight(level)
                    ? "py-space-3 px-space-4 max-900:px-space-3 text-center border-l border-r whitespace-nowrap text-t-sm sticky top-[0] z-(--z-sticky) text-vip-text-muted border-b-2 font-weight-bold border-l-[color-mix(in_srgb,var(--vip-gold-mid)_55%,transparent)] border-r-[color-mix(in_srgb,var(--vip-gold-mid)_55%,transparent)] border-b-vip-gold-mid [background:color-mix(in_srgb,var(--vip-gold-mid)_16%,var(--vip-inner-bg))]"
                    : "py-space-3 px-space-4 max-900:px-space-3 text-center border-l border-r whitespace-nowrap text-t-sm sticky top-[0] z-(--z-sticky) text-vip-text-muted border-b-2 font-weight-semi border-l-transparent border-r-transparent border-b-vip-hairline [background:var(--vip-inner-bg)]"
                }
              >
                <span
                  className={
                    isSpotlight(level)
                      ? "block font-brand-font-body text-t-micro tracking-[0.14em] uppercase leading-[1] text-[color-mix(in_srgb,var(--vip-gold-mid)_75%,transparent)]"
                      : isDimmed(level)
                        ? "block font-brand-font-body text-t-micro tracking-[0.14em] uppercase leading-[1] text-vip-text-disabled"
                        : "block font-brand-font-body text-t-micro tracking-[0.14em] uppercase leading-[1] text-vip-text-faint"
                  }
                >{copy.levelWord}</span>
                <span
                  className={
                    isSpotlight(level)
                      ? "block mt-[2px] vip-type-h4 text-vip-gold-end"
                      : isDimmed(level)
                        ? "block mt-[2px] vip-type-h4 text-vip-text-disabled"
                        : "block mt-[2px] vip-type-h4 text-vip-text-primary"
                  }
                >{level}</span>
                {isLockedAhead(level) && (
                  <span className="block mt-[2px] text-t-micro leading-[1] opacity-[0.7]" aria-hidden="true">
                    &#128274;
                  </span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key}>
              <th scope="row" className="py-space-3 px-space-4 max-900:py-space-2 max-900:px-space-3 text-left border-b border-b-vip-hairline border-l border-l-transparent border-r border-r-vip-hairline whitespace-nowrap text-vip-text-primary [background:var(--vip-panel-alt)] text-t-sm sticky left-[0] z-(--z-content) w-[200px] font-brand-font-body font-weight-semi [tbody_tr:last-child_&]:[border-bottom:none]">
                {row.label}
              </th>
              {LEVELS.map((level) => (
                <td
                  key={level}
                  className={
                    isSpotlight(level) && row.money
                      ? "py-space-3 px-space-4 max-900:py-space-2 max-900:px-space-3 text-center border-b border-b-vip-hairline border-l border-r whitespace-nowrap text-t-sm [tbody_tr:last-child_&]:[border-bottom:none] border-l-[color-mix(in_srgb,var(--vip-gold-mid)_45%,transparent)] border-r-[color-mix(in_srgb,var(--vip-gold-mid)_45%,transparent)] text-vip-text-primary font-weight-bold [background:color-mix(in_srgb,var(--vip-gold-mid)_12%,var(--vip-panel-bg))]"
                      : isSpotlight(level)
                      ? "py-space-3 px-space-4 max-900:py-space-2 max-900:px-space-3 text-center border-b border-b-vip-hairline border-l border-r whitespace-nowrap text-t-sm [tbody_tr:last-child_&]:[border-bottom:none] border-l-[color-mix(in_srgb,var(--vip-gold-mid)_45%,transparent)] border-r-[color-mix(in_srgb,var(--vip-gold-mid)_45%,transparent)] text-vip-gold-mid font-weight-bold [background:color-mix(in_srgb,var(--vip-gold-mid)_12%,var(--vip-panel-bg))]"
                      : isDimmed(level)
                        ? "py-space-3 px-space-4 max-900:py-space-2 max-900:px-space-3 text-center border-b border-b-vip-hairline border-l border-r whitespace-nowrap text-t-sm [tbody_tr:last-child_&]:[border-bottom:none] border-l-transparent border-r-transparent text-vip-text-disabled [background:var(--vip-panel-bg)]"
                        : "py-space-3 px-space-4 max-900:py-space-2 max-900:px-space-3 text-center border-b border-b-vip-hairline border-l border-r whitespace-nowrap text-t-sm [tbody_tr:last-child_&]:[border-bottom:none] border-l-transparent border-r-transparent text-vip-text-secondary [background:var(--vip-panel-bg)]"
                  }
                >
                  {row.cell(level)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
