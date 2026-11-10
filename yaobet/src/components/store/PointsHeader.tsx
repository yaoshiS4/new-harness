/* ============================================================================
 * PointsHeader — points-balance header.
 * Renders the member's redeemable points as a count-kind MoneyValue (tabular,
 * no ₫ — points, not currency-symbol money). Auth-aware: a guest sees an honest
 * prompt instead of a fabricated balance. Server-rendered shell with a small
 * client island for the guest/member split.
 * ==========================================================================*/

"use client";

import { vi } from "@/lib/i18n";
import { useRequireAuth } from "@/lib/auth";
import { Card, Icon, Button } from "@/ui";

export interface PointsHeaderProps {
  /** redeemable points balance (truthful fixture; count kind, never massaged) */
  points: number;
}

export function PointsHeader({ points }: PointsHeaderProps) {
  const { allowed, promptAuth } = useRequireAuth();

  return (
    <Card variant="default" className="flex items-center gap-space-3 p-space-4">
      <span className="inline-flex items-center justify-center w-[48px] h-[48px] flex-[0_0_auto] rounded-pill [background:var(--surface-3)] [border:1px_solid_var(--brand-accent-hairline)] text-brand-accent-fg" aria-hidden="true">
        <Icon name="gift" size={24} />
      </span>
      <div className="flex flex-col gap-space-1 flex-[1] min-w-[0]">
        <span className="text-t-sm text-text-mid">Điểm tích lũy của bạn</span>
        {allowed ? (
          <span className="store-type-num-lg text-brand-accent-fg" data-truthful="true">
            {/* points are a count, not VND — render with VN grouping, no ₫ */}
            {points.toLocaleString("vi-VN")} <span className="text-t-body font-weight-reg text-text-mid">điểm</span>
          </span>
        ) : (
          <span className="text-t-body text-text">
            Đăng nhập để xem điểm và đổi quà
          </span>
        )}
      </div>
      {!allowed && (
        <Button variant="primary" size="sm" onClick={() => promptAuth()}>
          {vi.auth.login}
        </Button>
      )}
    </Card>
  );
}
