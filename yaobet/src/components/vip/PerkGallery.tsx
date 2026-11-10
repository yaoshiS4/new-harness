/* ============================================================================
 * PerkGallery — per-tier perk tiles (the club page, reused on the
 * VIP/ladder pages). Each perk Card carries an illustration SLOT + name +
 * description + an "unlocks at hạng N" line. For a member, perks above their
 * level render with a lock veil (.mask) — an HONEST locked status, never a
 * fabricated unlock. NO toxic perks (hostess / loss-as-status / luxury) — the
 * fixture already excludes them. Empty fixture → EmptyState.
 * ==========================================================================*/

"use client";

import type { Perk } from "@/lib/types";
import { useAuth } from "@/lib/auth/session";
import { Card, Badge, Icon, EmptyState } from "@/ui";
import { vipCopy } from "./copy";

export interface PerkGalleryProps {
  perks: Perk[];
}

export function PerkGallery({ perks }: PerkGalleryProps) {
  const { isAuthenticated, user } = useAuth();
  const currentLevel = isAuthenticated && user ? user.vipLevel : null;

  if (perks.length === 0) {
    return <EmptyState icon="gift" message={vipCopy.perksHeading} />;
  }

  return (
    <ul className="list-none m-[0] p-[0] grid grid-cols-[1fr] gap-space-3 min-[640px]:grid-cols-[1fr_1fr] min-[1024px]:grid-cols-[1fr_1fr]">
      {perks.map((perk) => {
        const locked = currentLevel != null && perk.unlocksAtLevel > currentLevel;
        return (
          <li key={perk.id} className="flex">
            <Card variant="tile" className="flex gap-space-3 p-space-3 w-full items-stretch">
              {/* illustration SLOT — token-gradient panel awaiting art */}
              <div className="relative flex-[0_0_auto] w-[72px] h-[72px] rounded-md grid place-items-center text-brand-accent-fg [background:var(--surface-3)] [border:1px_solid_var(--brand-accent-hairline)]" aria-hidden>
                <Icon name="gift" size={28} />
                {locked && (
                  <span className="absolute inset-[0] rounded-md grid place-items-center text-text-mid [background:var(--scrim)]">
                    <Icon name="lock" size={20} />
                  </span>
                )}
              </div>
              <div className="flex flex-col gap-space-1 min-w-[0]">
                <div className="flex items-center gap-space-2 flex-wrap">
                  <span className="text-t-body font-weight-semi text-text-hi">{perk.name}</span>
                  <Badge tone={locked ? "neutral" : "gold"} variant="subtle">
                    {vipCopy.perkUnlockAt(perk.unlocksAtLevel)}
                  </Badge>
                </div>
                <p className="text-t-sm leading-lh-body text-text-mid">{perk.description}</p>
                {locked && <p className="text-t-micro text-text-dim">{vipCopy.perkLockedNote}</p>}
              </div>
            </Card>
          </li>
        );
      })}
    </ul>
  );
}
