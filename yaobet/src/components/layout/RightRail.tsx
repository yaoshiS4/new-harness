/* ============================================================================
 * RightRail — desktop right rail. Appears only
 * ≥1240px (max-frame); below that the host page folds these figures inline at
 * their authored positions, so the rail simply renders nothing on mobile.
 *
 * Three truthful-bound surfaces, each governed by the dynamic-data contract:
 *   - member-day Countdown (Deadline envelope) — halts at the server deadline.
 *   - super-jackpot pool (Live<Jackpot>)       — the resting server value; no
 *     extrapolation past it.
 *   - opt-in leaderboard (Live<LeaderRow[]>)   — real ranks or omitted.
 * Per surface: loading → Skeleton; error → honest ErrorState; absent
 * → the card is OMITTED (never fabricated). If ALL three are absent the rail
 * renders nothing.
 * ==========================================================================*/

import type {
  DeadlineEnvelope,
  Envelope,
  Jackpot,
  LeaderRow,
} from "@/lib/types";
import { vi } from "@/lib/i18n";
import { formatVnd } from "@/lib/format";
import { Skeleton } from "@/ui/Skeleton/Skeleton";
import { Money } from "./_internal/Money";
import { Countdown } from "./_internal/Countdown";

export interface RightRailProps {
  memberDay: DeadlineEnvelope;
  jackpot: Envelope<Jackpot>;
  leaderboard: Envelope<LeaderRow[]>;
}

function ErrorLine() {
  return <p className="shell-right-rail-error-line">{vi.state.error}</p>;
}

export function RightRail({ memberDay, jackpot, leaderboard }: RightRailProps) {
  const showMemberDay = memberDay.status !== "absent";
  const showJackpot = jackpot.status !== "absent";
  const showLeaderboard = leaderboard.status !== "absent";

  if (!showMemberDay && !showJackpot && !showLeaderboard) return null;

  return (
    <aside className="shell-right-rail" aria-label="Thông tin trực tiếp">
      {/* ---- member-day countdown ---- */}
      {showMemberDay && (
        <section className="shell-right-rail-card">
          <h3 className="shell-right-rail-card-title">Ngày hội viên</h3>
          {memberDay.status === "loading" && <Skeleton width="60%" height="1.6em" />}
          {memberDay.status === "error" && <ErrorLine />}
          {memberDay.status === "live" && <Countdown deadlineAt={memberDay.deadlineAt} />}
        </section>
      )}

      {/* ---- super-jackpot ---- */}
      {showJackpot && (
        <section className="shell-right-rail-card">
          <h3 className="shell-right-rail-card-title">
            {jackpot.status === "live" ? jackpot.value.label : "Hũ vàng"}
          </h3>
          {jackpot.status === "loading" && <Skeleton width="80%" height="2em" />}
          {jackpot.status === "error" && <ErrorLine />}
          {jackpot.status === "live" && (
            <Money value={jackpot.value.pool} size="num-lg" className="shell-right-rail-jackpot" />
          )}
        </section>
      )}

      {/* ---- opt-in leaderboard ---- */}
      {showLeaderboard && (
        <section className="shell-right-rail-card">
          <h3 className="shell-right-rail-card-title">Bảng xếp hạng</h3>
          {leaderboard.status === "loading" && (
            <>
              <Skeleton width="100%" height="1.4em" className="shell-right-rail-row" />
              <Skeleton width="100%" height="1.4em" className="shell-right-rail-row" />
              <Skeleton width="100%" height="1.4em" className="shell-right-rail-row" />
            </>
          )}
          {leaderboard.status === "error" && <ErrorLine />}
          {leaderboard.status === "live" && (
            <ol className="shell-right-rail-board">
              {leaderboard.value.map((r) => (
                <li key={r.rank} className="shell-right-rail-board-row">
                  <span className="shell-right-rail-rank">{r.rank}</span>
                  <span className="shell-right-rail-player">{r.displayName}</span>
                  <span className="shell-right-rail-amount">{formatVnd(r.amount)}</span>
                </li>
              ))}
            </ol>
          )}
        </section>
      )}
    </aside>
  );
}
