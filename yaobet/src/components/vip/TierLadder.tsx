/* ============================================================================
 * TierLadder — the VIP bậc-thang. A horizontally
 * scrollable deck (Scroller, 16px peek @375) of tier Cards: badge SLOT + tier
 * name + truthful %-of-play rate (from the Yaobet VIP-BRD fixture — NOT
 * 0.40–1.00% numbers) + a short perk line. Auth-aware highlighting:
 *   • the member's CURRENT tier is marked (active glow + "Hiện tại" badge);
 *   • tiers ABOVE the member's level read as "Chưa mở" (locked) — an honest
 *     status, NOT a fabricated progress promise.
 * Rates are static marketing copy; no ledger figure is fabricated here.
 * The compact variant (home/aisle-style) drops the perk line for density.
 * ==========================================================================*/

"use client";

import type { VipTier } from "@/lib/types";
import { useAuth } from "@/lib/auth/session";
import { Card, Badge, Icon, Scroller } from "@/ui";
import { vipCopy } from "./copy";

export interface TierLadderProps {
  tiers: VipTier[];
  /** drop the perk line for a denser deck (default false) */
  compact?: boolean;
}

export function TierLadder({ tiers, compact = false }: TierLadderProps) {
  const { isAuthenticated, user } = useAuth();
  const currentLevel = isAuthenticated && user ? user.vipLevel : null;

  return (
    <Scroller snap peek label={vipCopy.ladderHeading} className="min-[768px]:[&>div]:w-full min-[768px]:[&>div]:pr-[0]">
      <ul className="flex gap-space-3 list-none m-[0] p-[0] min-[768px]:w-full">
        {tiers.map((t) => {
          const isCurrent = currentLevel != null && t.level === currentLevel;
          const isLocked = currentLevel != null && t.level > currentLevel;
          return (
            <li key={t.id} className="flex-[0_0_auto] min-[768px]:flex-[1_1_0] min-[768px]:min-w-[0]">
              <Card
                variant="vip"
                active={isCurrent}
                className={[
                  "flex flex-col items-center gap-space-2 w-[168px] min-h-full p-space-4 snap-start min-[768px]:w-full",
                  isLocked ? "opacity-[0.66]" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                aria-label={`${t.name} — ${vipCopy.levelLabel(t.level)}`}
              >
                <span className="min-h-[22px] flex items-center justify-center">
                  {isCurrent && (
                    <Badge tone="gold" variant="solid">
                      {vipCopy.currentBadge}
                    </Badge>
                  )}
                  {isLocked && (
                    <span className="inline-flex items-center gap-space-1 text-t-micro text-text-mid">
                      <Icon name="lock" size={13} /> {vipCopy.lockedBadge}
                    </span>
                  )}
                </span>

                {/* badge SLOT — token-gradient disc awaiting tier art */}
                <span className="w-space-8 h-space-8 rounded-pill grid place-items-center text-brand-accent-fg [background:var(--surface-3)] [border:1px_solid_var(--brand-accent-hairline)]" aria-hidden>
                  <Icon name="vip" size={30} />
                </span>

                <span className="text-t-micro tracking-[0.03em] uppercase text-text-mid">{vipCopy.levelLabel(t.level)}</span>
                <span className="text-t-h3 font-weight-bold text-text-hi text-center">{t.name}</span>
                <span className="text-t-sm font-weight-semi text-brand-accent-fg">{vipCopy.cashbackRate(t.cashbackRate)}</span>

                {!compact && t.perks.length > 0 && (
                  <ul className="list-none [margin:var(--space-2)_0_0] p-[0] flex flex-col gap-space-1 w-full">
                    {t.perks.map((p) => (
                      <li key={p} className="flex items-start gap-space-1 text-t-micro leading-lh-tight text-text">
                        <Icon name="check" size={13} className="flex-[0_0_auto] mt-[2px] text-win" />
                        {p}
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            </li>
          );
        })}
      </ul>
    </Scroller>
  );
}
