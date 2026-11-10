/* ============================================================================
 * OutcomeFrame — the settled result. Three registers, deliberately unequal in
 * volume and deliberately equal in honesty:
 *
 *   win     — count-up to the total, gold ring, the matched cells still beating
 *             in unison with their winning number. Restrained: no confetti.
 *   partial — a real win, stated as a real win, at SMALL volume. No count-up,
 *             no ring, no pulse. "Again", not "never mind" — and never dressed
 *             up as a large win.
 *   lose    — the near-miss is stated plainly (the biggest prize the card
 *             actually held, and the number it needed) and the dust is paid in
 *             the SAME container, under ONE animation, so the disappointment
 *             and its compensation land in the same frame. The dust figure is
 *             typeset as neutral text, never as --win: a compensation is not a
 *             win and must not be coloured like one.
 *
 * role="status" — the result is announced once, calmly, on settle.
 * ==========================================================================*/

"use client";

import { formatVnd } from "@/lib/format";
import type { ScratchCard } from "@/lib/mock/lottery";
import { Icon } from "@/ui/Icon/Icon";
import { useCountUp } from "./useCountUp";

/** Two-digit face value: 7 → "07". */
function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

export interface OutcomeFrameProps {
  card: ScratchCard;
  /** OS reduced-motion — kills the count-up tween (the figure is shown at once) */
  reduced: boolean;
}

export function OutcomeFrame({ card, reduced }: OutcomeFrameProps) {
  const isWin = card.outcome === "win";
  const isLose = card.outcome === "lose";
  const hits = card.panels.filter((p) => p.matched).length;

  // count-up is the WIN register only — a floor prize is never inflated by
  // borrowing the big-win animation.
  const shown = useCountUp(card.totalPrize, isWin, reduced);

  // the near-miss: the largest prize this card actually carried, and — when the
  // generator put it one digit off a winning number — WHICH number it missed.
  const top = card.panels.reduce((a, b) => (b.prize > a.prize ? b : a), card.panels[0]);
  const missedBy = card.winning.find((w) => {
    const d = Math.abs(w - top.n);
    return d === 1 || d === 99; // 99 = the 0/99 wrap the generator can produce
  });

  return (
    <section
      className="lottery-outcome-frame-frame mt-space-5 py-space-5 px-space-4 rounded-card text-center"
      data-outcome={card.outcome}
      role="status"
      aria-live="polite"
    >
      {isWin && (
        <>
          <p className="inline-flex items-center gap-gap-xs text-t-h3 font-weight-semi leading-lh-body text-text-hi">
            <Icon name="check" size={20} className="text-win" />
            Bạn trúng {hits} ô.
          </p>
          <p className="mt-space-3 text-t-micro tracking-[0.06em] uppercase text-text-mid">Tổng thưởng</p>
          <p className="lottery-outcome-frame-total-win mt-space-1 font-brand-font-num text-t-num-lg font-weight-bold [font-variant-numeric:tabular-nums] leading-lh-tight text-win">{formatVnd(shown)}</p>
          <p className="mt-space-3 text-t-sm leading-lh-body text-text-mid">Đã cộng vào số dư của bạn.</p>
        </>
      )}

      {card.outcome === "partial" && (
        <>
          <p className="text-t-body font-weight-semi leading-lh-body text-text-hi">Thẻ này có thưởng.</p>
          <p className="mt-space-2 font-brand-font-num text-t-h1 font-weight-semi [font-variant-numeric:tabular-nums] leading-lh-tight text-win">{formatVnd(card.totalPrize)}</p>
          <p className="mt-space-3 text-t-sm leading-lh-body text-text-mid">
            Không lớn, nhưng là thưởng thật — đã cộng vào số dư của bạn.
          </p>
          <p className="mt-space-2 text-t-micro leading-lh-body text-text-dim">
            Bạn có thể mở thẻ khác khi nào bạn muốn, hoặc dừng ở đây.
          </p>
        </>
      )}

      {isLose && (
        /* ONE container, ONE animation: the near-miss and the dust are siblings
         * inside it, so they arrive together — never sequenced. */
        <div className="lottery-outcome-frame-lose-block">
          <p className="text-t-body font-weight-semi leading-lh-body text-loss">Thẻ này không trúng.</p>
          <div className="grid grid-cols-[1fr] gap-space-3 mt-space-4 text-left min-[480px]:grid-cols-[1fr_1fr]">
            <div className="p-space-3 [border:1px_solid_var(--border)] rounded-md [background:var(--surface)]">
              <p className="text-t-micro tracking-[0.05em] uppercase text-text-mid">Giải lớn nhất trên thẻ</p>
              <p className="mt-space-1 font-brand-font-num text-t-h2 font-weight-semi [font-variant-numeric:tabular-nums] text-text-hi">{formatVnd(top.prize)}</p>
              <p className="mt-space-2 text-t-micro leading-lh-body text-text-mid">
                {missedBy === undefined
                  ? `Nằm ở ô số ${pad2(top.n)}, và số đó không nằm trong bốn số trúng thưởng của thẻ.`
                  : `Nằm ở ô số ${pad2(top.n)} — lệch đúng một số so với ${pad2(missedBy)}.`}
              </p>
            </div>
            {card.dust > 0 && (
              <div className="p-space-3 [border:1px_solid_var(--border)] rounded-md [background:var(--surface)]">
                <p className="text-t-micro tracking-[0.05em] uppercase text-text-mid">Bù thẻ không trúng</p>
                <p className="mt-space-1 font-brand-font-num text-t-h2 font-weight-semi [font-variant-numeric:tabular-nums] text-text-hi">{formatVnd(card.dust)}</p>
                <p className="mt-space-2 text-t-micro leading-lh-body text-text-mid">
                  Khoản bù, không phải tiền thưởng. Đã cộng ngay cùng lúc.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* dust on a paying card is stated, quietly, and still not called a win */}
      {!isLose && card.dust > 0 && (
        <p className="mt-space-2 text-t-micro leading-lh-body text-text-dim">
          Kèm {formatVnd(card.dust)} tiền bù — khoản bù, không phải tiền thưởng.
        </p>
      )}
    </section>
  );
}
