/* ============================================================================
 * CurrentTierCard — the member's current-tier panel + turnover-to-next-tier
 * (tier deck and progress meter, bound to the dynamic-data contract).
 * ----------------------------------------------------------------------------
 * The truthful centerpiece of the VIP page. It is auth-aware and data-bound:
 *   • guest        → an honest join prompt (NO fabricated tier/progress number);
 *                    CTA opens the auth modal in register mode.
 *   • member +
 *     progress.absent  → tier identity only; the progress bar is OMITTED
 *                        (never a fabricated 0% / made-up target).
 *   • progress.loading → Skeleton in the bar's reserved footprint.
 *   • progress.error   → ErrorState + retry — never a stale/fake number.
 *   • progress.live    → a TRUTHFUL fill = real current/target; the remaining
 *                        turnover renders via the Money primitive (balance kind,
 *                        a real ledger figure — never digit-4-massaged). Fill is
 *                        a static CSS width; reduced-motion zeroes the transition
 *                        (no fake 5s climb).
 * The progress NUMBER is gated behind the Live envelope: there is no code path
 * that prints a turnover figure the server did not hand us.
 * ==========================================================================*/

"use client";

import type { Envelope, VipProgress, VipTier } from "@/lib/types";
import { useAuth } from "@/lib/auth/session";
import { useAuthModal } from "@/lib/auth/modal";
import { Card, Button, Badge, Skeleton, ErrorState, Icon, MoneyValue } from "@/ui";
import { vipCopy } from "./copy";

export interface CurrentTierCardProps {
  tiers: VipTier[];
  progress: Envelope<VipProgress>;
}

/** Truthful turnover-to-next-tier bar — data-bound, never a fabricated number. */
function ProgressBar({ progress }: { progress: Envelope<VipProgress> }) {
  // No real source → OMIT the bar entirely (never a fake 0%/target).
  if (progress.status === "absent") return null;

  if (progress.status === "loading") {
    return (
      <div className="flex flex-col gap-space-2" aria-busy="true">
        <Skeleton width="40%" height="0.9em" />
        <Skeleton width="100%" height="10px" className="block rounded-pill" />
        <Skeleton width="60%" height="0.9em" />
      </div>
    );
  }

  if (progress.status === "error") {
    return (
      <div className="flex flex-col gap-space-2">
        <ErrorState title={vipCopy.progressError} />
      </div>
    );
  }

  const { current, target, nextTierName } = progress.value;
  const pct = target > 0 ? Math.min(100, Math.max(0, (current / target) * 100)) : 0;
  const remaining = Math.max(0, target - current);

  // Max tier: no next target → honest "highest tier" state, no fabricated bar.
  if (!nextTierName) {
    return (
      <div className="flex flex-col gap-space-2">
        <p className="inline-flex items-center gap-space-2 text-t-body text-text">
          <Icon name="trophy" size={18} className="text-brand-accent-fg" />
          {vipCopy.atMaxTier}
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-space-2">
      <div className="flex items-baseline justify-between gap-space-3">
        <span className="text-t-sm text-text-mid">{vipCopy.turnoverToNext}</span>
        <span className="text-t-sm font-weight-bold text-brand-accent-fg font-brand-font-num tabular-nums">{Math.round(pct)}%</span>
      </div>
      <div
        className="h-[10px] rounded-pill [background:var(--surface-disabled)] overflow-hidden"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={target}
        aria-valuenow={current}
        aria-label={vipCopy.turnoverToNext}
      >
        <span className="block h-full rounded-pill [background-image:var(--progress-fill-grad)] [transition:width_var(--dur-base)_var(--ease-standard)] motion-reduce:[transition:none]" style={{ width: `${pct}%` }} />
      </div>
      <p className="text-t-sm leading-lh-body text-text [&_strong]:text-text-hi [&_strong]:font-weight-semi">
        {vipCopy.remainingPrefix}{" "}
        <MoneyValue value={{ amount: remaining, currency: "VND" }} kind="balance" />{" "}
        {vipCopy.remainingSuffix} <strong>{nextTierName}</strong>
      </p>
    </div>
  );
}

export function CurrentTierCard({ tiers, progress }: CurrentTierCardProps) {
  const { isAuthenticated, user } = useAuth();
  const { openAuthModal } = useAuthModal();

  /* GUEST — honest join prompt, NO tier/progress number fabricated. */
  if (!isAuthenticated || !user) {
    return (
      <Card variant="vip" className="flex flex-col gap-space-5 p-space-5 items-center text-center min-[768px]:flex-row min-[768px]:text-left min-[768px]:items-center min-[768px]:[&_button]:w-auto min-[768px]:[&_button]:flex-[0_0_auto]">
        <span className="flex-[0_0_auto] w-[64px] h-[64px] rounded-pill grid place-items-center text-brand-accent-fg [background:var(--surface-3)] [border:1px_solid_var(--brand-accent-hairline)]" aria-hidden>
          <Icon name="vip" size={32} />
        </span>
        <div className="flex flex-col gap-space-2 items-center min-[768px]:items-start min-[768px]:flex-1">
          <h2 className="text-t-h2 font-weight-bold text-text-hi">{vipCopy.guestTitle}</h2>
          <p className="text-t-body leading-lh-body text-text-mid max-w-[38ch]">{vipCopy.guestCopy}</p>
        </div>
        <Button
          variant="gold"
          size="lg"
          fullWidth
          onClick={() =>
            openAuthModal({ mode: "register", resumeIntent: { action: "none" } })
          }
        >
          {vipCopy.joinCta}
        </Button>
      </Card>
    );
  }

  /* MEMBER — real tier identity + data-gated progress. */
  const tier =
    tiers.find((t) => t.level === user.vipLevel) ?? tiers[0];

  return (
    <Card variant="vip" active className="flex flex-col gap-space-5 p-space-5">
      <div className="flex items-center gap-space-4">
        <span className="flex-[0_0_auto] w-[64px] h-[64px] rounded-pill grid place-items-center text-brand-accent-fg [background:var(--surface-3)] [border:1px_solid_var(--brand-accent-hairline)]" aria-hidden>
          {/* badge SLOT — token-gradient disc awaiting tier art */}
          <Icon name="vip" size={36} />
        </span>
        <div className="flex flex-col gap-space-2 items-start">
          <span className="text-t-micro tracking-[0.04em] uppercase text-text-mid">{vipCopy.currentTier}</span>
          <span className="text-t-h1 font-weight-bold text-brand-accent-fg leading-lh-tight">{tier.name}</span>
          <Badge tone="gold" variant="subtle">
            {vipCopy.cashbackRate(tier.cashbackRate)}
          </Badge>
        </div>
      </div>

      <ProgressBar progress={progress} />
    </Card>
  );
}
