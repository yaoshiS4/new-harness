/* ============================================================================
 * PrivilegeTable — the wide privilege-overview matrix.
 * Built column-per-tier so the Scroller `freezeFirstColumn`
 * mode can pin the row-label column while the tier columns scroll horizontally
 * @375. The member's current tier column is highlighted.
 * All figures are truthful fixture values (%-of-play rate + perk list) — no
 * imported rates, no fabricated number.
 * ==========================================================================*/

"use client";

import type { VipTier } from "@/lib/types";
import { useAuth } from "@/lib/auth/session";
import { Icon, Scroller } from "@/ui";
import { vipCopy } from "./copy";

export interface PrivilegeTableProps {
  tiers: VipTier[];
}

export function PrivilegeTable({ tiers }: PrivilegeTableProps) {
  const { isAuthenticated, user } = useAuth();
  const currentLevel = isAuthenticated && user ? user.vipLevel : null;

  // union of all perk labels across tiers → the perk rows
  const perkRows = Array.from(new Set(tiers.flatMap((t) => t.perks)));

  return (
    <Scroller
      freezeFirstColumn
      snap={false}
      peek={false}
      label={vipCopy.privilegeHeading}
      className="rounded-card [border:1px_solid_var(--border)] overflow-hidden min-[768px]:[&>div]:w-full"
    >
      {/* COLUMN 0 — sticky row labels (pinned by Scroller freezeFirstColumn) */}
      <div className="flex flex-col flex-[0_0_auto] min-w-[148px] [border-left:1px_solid_transparent] [border-right:1px_solid_transparent] min-[768px]:flex-[0_0_auto] min-[768px]:min-w-[180px]">
          <div className="flex items-center justify-start min-h-[56px] py-space-2 px-space-3 [border-bottom:1px_solid_var(--border)] text-t-sm text-text-hi text-left [background:var(--surface-3)] font-weight-bold">
            {vipCopy.colTier}
          </div>
          <div className="flex items-center justify-start min-h-[52px] py-space-2 px-space-3 [border-bottom:1px_solid_var(--border)] text-t-sm text-text-mid text-left">
            {vipCopy.colCashback}
          </div>
          {perkRows.map((p) => (
            <div key={p} className="flex items-center justify-start min-h-[52px] py-space-2 px-space-3 [border-bottom:1px_solid_var(--border)] text-t-sm text-text-mid text-left">
              {p}
            </div>
          ))}
        </div>

        {/* one column per tier */}
        {tiers.map((t) => {
          const isCurrent = currentLevel != null && t.level === currentLevel;
          return (
            <div
              key={t.id}
              className={[
                "flex flex-col flex-[0_0_auto] min-w-[132px] min-[768px]:flex-[1_1_0] min-[768px]:min-w-[0]",
                isCurrent
                  ? "[background:var(--tint)] [border-left:1px_solid_var(--brand-accent-hairline)] [border-right:1px_solid_var(--brand-accent-hairline)]"
                  : "[border-left:1px_solid_transparent] [border-right:1px_solid_transparent]",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <div className="flex flex-col items-center justify-center gap-[2px] min-h-[56px] py-space-2 px-space-3 [border-bottom:1px_solid_var(--border)] text-t-sm text-text-hi text-center [background:var(--surface-3)] font-weight-bold">
                <span className="text-t-sm text-brand-accent-fg">{t.name}</span>
                <span className="text-t-micro text-text-mid font-weight-reg">{vipCopy.levelLabel(t.level)}</span>
              </div>
              <div className="flex items-center justify-center min-h-[52px] py-space-2 px-space-3 [border-bottom:1px_solid_var(--border)] text-t-sm font-weight-semi text-brand-accent-fg text-center">
                {vipCopy.cashbackRate(t.cashbackRate)}
              </div>
              {perkRows.map((p) => (
                <div key={p} className="flex items-center justify-center min-h-[52px] py-space-2 px-space-3 [border-bottom:1px_solid_var(--border)] text-t-sm text-text text-center">
                  {t.perks.includes(p) ? (
                    <Icon name="check" size={18} className="text-win" label="Có" />
                  ) : (
                    <span className="text-text-dim tabular-nums" aria-label="Không">
                      —
                    </span>
                  )}
                </div>
              ))}
            </div>
          );
        })}
    </Scroller>
  );
}
