/* ============================================================================
 * Luxury VIP — PrivilegeMatrix (guest). Rows = 4 privileges, cols = the 5 TIERS
 * (never 10). Cell unlocked when rowIndex < tier.perks (cumulative). Selected
 * tier column is gold-tinted. Per-tier gem header (tier accent),
 * green ✓ / grey lock cells. Sticky first column for horizontal scroll.
 * ==========================================================================*/
import { getVipCopy, PRIVILEGES, type Lang, type VipTierDef } from "@/lib/vip";

function CheckIcon() {
  return (
    <svg viewBox="0 0 24 24" className="w-[16px] h-[16px] block" aria-hidden focusable="false">
      <path
        d="M5 12.5l4.2 4.2L19 7"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg viewBox="0 0 24 24" className="w-[16px] h-[16px] block" aria-hidden focusable="false">
      <rect
        x="5"
        y="10.5"
        width="14"
        height="9.5"
        rx="1.8"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
      />
      <path
        d="M8 10.5V8a4 4 0 018 0v2.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function PrivilegeMatrix({
  tiers,
  selected,
  lang,
}: {
  tiers: VipTierDef[];
  selected: number;
  lang: Lang;
}) {
  const copy = getVipCopy(lang);

  return (
    <div className="overflow-x-auto rounded-vip-radius-table border border-vip-hairline [background:var(--vip-panel-bg)] [-webkit-overflow-scrolling:touch]">
      <table className="[border-collapse:separate] [border-spacing:0] table-fixed w-full min-w-[760px]">
        <caption className="absolute w-[1px] h-[1px] p-[0] m-[-1px] overflow-hidden [clip:rect(0,0,0,0)] whitespace-nowrap [border:0]">{copy.tierMatrixTitle}</caption>
        <thead>
          <tr>
            <th className="p-space-3 max-900:p-space-2 [vertical-align:middle] text-left border-b-2 border-b-vip-hairline text-vip-text-primary sticky left-[0] z-[3] w-[200px] font-weight-semi whitespace-nowrap [background:var(--vip-inner-bg)] border-r border-r-vip-hairline" scope="col">
              <span className="absolute w-[1px] h-[1px] p-[0] m-[-1px] overflow-hidden [clip:rect(0,0,0,0)] whitespace-nowrap [border:0]">{copy.tierMatrixTitle}</span>
            </th>
            {tiers.map((tier, i) => (
              <th
                key={tier.id}
                scope="col"
                className={
                  i === selected
                    ? "p-space-3 max-900:p-space-2 [vertical-align:middle] text-center border-b-2 text-vip-text-secondary border-b-vip-gold-mid [background:color-mix(in_srgb,var(--vip-gold-mid)_14%,var(--vip-inner-bg))]"
                    : "p-space-3 max-900:p-space-2 [vertical-align:middle] text-center border-b-2 text-vip-text-secondary border-b-vip-hairline [background:var(--vip-inner-bg)]"
                }
              >
                <span
                  className="block mx-auto w-[18px] h-[18px] rounded-vip-radius-gem [border:1px_solid_color-mix(in_srgb,var(--vip-text-primary)_22%,transparent)] [transform:rotate(45deg)] mb-space-2"
                  style={{ background: tier.acc }}
                  aria-hidden
                />
                <span className={i === selected ? "block mx-auto vip-type-body font-weight-semi tracking-[0.02em] text-vip-gold-end" : "block mx-auto vip-type-body font-weight-semi tracking-[0.02em] text-vip-text-primary"}>{copy[tier.nameKey]}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {PRIVILEGES.map((key, rowIdx) => (
            <tr key={key}>
              <th scope="row" className="p-space-3 max-900:p-space-2 [vertical-align:middle] text-left border-b border-b-vip-hairline text-vip-text-primary sticky left-[0] z-[2] w-[200px] font-weight-semi whitespace-nowrap [background:var(--vip-panel-bg)] border-r border-r-vip-hairline">
                {copy[key]}
              </th>
              {tiers.map((tier, i) => {
                const unlocked = rowIdx < tier.perks;
                return (
                  <td
                    key={tier.id}
                    className={
                      i === selected
                        ? "p-space-3 max-900:p-space-2 [vertical-align:middle] text-center border-b border-b-vip-hairline text-vip-text-secondary tabular-nums [background:var(--vip-gold-tint)]"
                        : "p-space-3 max-900:p-space-2 [vertical-align:middle] text-center border-b border-b-vip-hairline text-vip-text-secondary tabular-nums"
                    }
                  >
                    <span
                      className={
                        unlocked
                          ? "inline-flex items-center justify-center w-[28px] h-[28px] rounded-pill text-vip-positive [background:color-mix(in_srgb,var(--vip-positive)_14%,transparent)]"
                          : "inline-flex items-center justify-center w-[28px] h-[28px] rounded-pill text-vip-text-muted [background:color-mix(in_srgb,var(--vip-text-muted)_10%,transparent)]"
                      }
                      title={
                        unlocked ? copy[key] : `${copy[key]} — ${copy.needWager} ${tier.unlock}`
                      }
                    >
                      {unlocked ? <CheckIcon /> : <LockIcon />}
                    </span>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
