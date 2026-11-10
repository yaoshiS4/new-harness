/* ============================================================================
 * StatsBar — social-proof strip. Shows real, settled figures only ("đã trả
 * thưởng tháng này" + participant count), net-framed and equal-salience. Hard
 * rule: a field with no real source is OMITTED, and if NEITHER field is real
 * the whole strip is OMITTED (never fabricated). loading → Skeleton;
 * error/absent → omit.
 *
 * The home page passes `{status:'absent'}` when no settled-stats feed exists, so
 * by default this band is simply not rendered — the truthful posture. Wire a
 * real `getStats()` envelope to light it up.
 * ==========================================================================*/

import type { Envelope, MoneyValue } from "@/lib/types";
import { formatVnd, formatCount } from "@/lib/format";
import { Skeleton } from "@/ui";

export interface HomeStats {
  /** real settled payout this period (net-framed) */
  paidThisMonth?: MoneyValue;
  /** real concurrency / participant count */
  participants?: number;
}

export interface StatsBarProps {
  stats: Envelope<HomeStats>;
}

export function StatsBar({ stats }: StatsBarProps) {
  if (stats.status === "absent" || stats.status === "error") return null;

  if (stats.status === "loading") {
    return (
      <div className="home-stats-bar-bar" aria-busy="true">
        <Skeleton width="40%" height="1.4em" />
        <Skeleton width="30%" height="1.4em" />
      </div>
    );
  }

  const { paidThisMonth, participants } = stats.value;
  const hasPaid = paidThisMonth != null;
  const hasParticipants = participants != null;
  // both real fields absent → omit the whole strip (never fabricate).
  if (!hasPaid && !hasParticipants) return null;

  return (
    <dl className="home-stats-bar-bar" aria-label="Số liệu nền tảng">
      {hasPaid && (
        <div className="home-stats-bar-stat">
          <dt className="home-stats-bar-label">Đã trả thưởng tháng này</dt>
          <dd className="home-stats-bar-value">{formatVnd(paidThisMonth)}</dd>
        </div>
      )}
      {hasParticipants && (
        <div className="home-stats-bar-stat">
          <dt className="home-stats-bar-label">Người tham gia</dt>
          <dd className="home-stats-bar-value">{formatCount(participants)}</dd>
        </div>
      )}
    </dl>
  );
}
