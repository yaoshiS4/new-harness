/* ============================================================================
 * CommissionPanel — referral earnings list
 * Per-referral rows (masked name · turnover · commission ·
 * when), all truthful fixture figures on the money role (equal salience). When
 * there are no commissions the panel shows the honest EmptyState primitive —
 * NEVER fabricated activity. Auth-aware: a guest sees a prompt.
 *
 * Shared by /dai-ly AND /gioi-thieu. Two optional props let /gioi-thieu match
 * the refer page WITHOUT changing the /dai-ly composition:
 *   • showHeldRow — render the held-commission head row (a left "Hoa hồng
 *     hiện có" label + the held total in ivory + a low-salience "Chi tiết hoạt
 *     động" details link). The held figure is derived from the REAL rows
 *     (sum of commissions) and is OMITTED when there are none (no fabricated 0).
 *   • hideEmpty — suppress the EmptyState branch (the page falls through to the
 *     StepExplainer onboarding empty state instead). /dai-ly keeps the default
 *     (EmptyState shown), so this prop is purely additive.
 * ==========================================================================*/

"use client";

import type { Commission, MoneyValue as Money } from "@/lib/types";
import { vi } from "@/lib/i18n";
import { useRequireAuth } from "@/lib/auth";
import { Card, MoneyValue, EmptyState, Button, Icon } from "@/ui";

const t = vi.referral;

export interface CommissionPanelProps {
  commissions: Commission[];
  /** render the held-commission head row (label + ivory total + details link).
   *  Default OFF → /dai-ly is unaffected. */
  showHeldRow?: boolean;
  /** suppress the EmptyState branch so the page can fall through to a steps
   *  onboarding state. Default OFF → /dai-ly keeps its EmptyState. */
  hideEmpty?: boolean;
}

function formatWhen(iso: string): string {
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

/** Held total = sum of the REAL commission rows (truthful; never fabricated). */
function sumHeld(commissions: Commission[]): Money | null {
  if (commissions.length === 0) return null;
  return {
    amount: commissions.reduce((acc, c) => acc + c.commission.amount, 0),
    currency: commissions[0].commission.currency,
  };
}

export function CommissionPanel({
  commissions,
  showHeldRow = false,
  hideEmpty = false,
}: CommissionPanelProps) {
  const { allowed, promptAuth } = useRequireAuth();

  // held figure (ivory money role): real data only (sum of live rows), omitted when none.
  const held = allowed ? sumHeld(commissions) : null;

  return (
    <Card variant="default" className="flex flex-col gap-space-4 p-card-pad">
      <h2 className="promo-type-h4 text-text-hi">{t.commissionPanelTitle}</h2>

      {/* Held-commission head row — opt-in (/gioi-thieu). The ivory held total
          renders ONLY when there is real data; the details link has no route so
          it stays low-salience and non-navigating (never an invented dest). */}
      {showHeldRow && (
        <div className="flex items-center justify-between gap-space-3 flex-wrap">
          <span className="inline-flex items-baseline gap-space-2 min-w-[0]">
            <span className="text-t-sm text-text-mid">{t.commissionHeldLabel}</span>
            {held && (
              <MoneyValue value={held} />
            )}
          </span>
          <span className="inline-flex items-center gap-space-1 text-t-sm text-brand-accent-fg whitespace-nowrap" aria-disabled="true">
            {t.commissionDetailsLink}
            <Icon name="chevronRight" size={14} />
          </span>
        </div>
      )}

      {!allowed ? (
        <div className="flex flex-col items-start gap-space-3">
          <p className="text-t-sm text-text-mid">{t.commissionGuestPrompt}</p>
          <Button variant="primary" size="sm" onClick={() => promptAuth()}>
            {vi.auth.login}
          </Button>
        </div>
      ) : commissions.length === 0 ? (
        hideEmpty ? null : (
          <EmptyState
            icon="referral"
            title={t.commissionEmptyTitle}
            message={t.commissionEmptyMessage}
          />
        )
      ) : (
        <ul className="flex flex-col gap-space-1 list-none m-[0] p-[0]">
          {commissions.map((c) => (
            <li key={c.id} className="flex items-center justify-between gap-space-3 py-space-3 px-[0] border-b border-b-border last:[border-bottom:0]">
              <div className="flex flex-col gap-space-1 min-w-[0]">
                <span className="text-t-body text-text-hi font-weight-semi">{c.referredName}</span>
                <span className="text-t-micro text-text-mid">{formatWhen(c.at)}</span>
              </div>
              <div className="flex flex-col items-end gap-space-1">
                <span className="text-t-micro text-text-mid inline-flex gap-space-1">
                  {t.commissionRowTurnover} <MoneyValue value={c.turnover} />
                </span>
                <span className="text-t-sm text-text-mid inline-flex items-baseline gap-space-1">
                  {t.commissionRowCommission}{" "}
                  <MoneyValue value={c.commission} />
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
