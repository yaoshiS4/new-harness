/* ============================================================================
 * Yaobet — REWARD CEREMONY: the completed-set exchange.
 * ----------------------------------------------------------------------------
 * WHAT THIS IS, AND WHAT IT DELIBERATELY IS NOT.
 *
 * The house rules ban win-juice: no particle bursts, no coin fountains, no
 * variable-ratio reinforcement. This animation is allowed inside that ban, and
 * the distinction is not a loophole — it is the whole design:
 *
 *   · A DRAW is random. Dressing a random outcome in celebration is exactly the
 *     reinforcement schedule the house rules exist to refuse. That is why the
 *     pack stage stays plain and never learns a reward value.
 *   · A COMPLETION is DETERMINISTIC. The player already holds every card. They
 *     already saw this amount on the rail, before they pressed anything. There
 *     is no outcome to suspend, because nothing is being decided here.
 *
 * So this is a RECEIPT CEREMONY, not a jackpot. Three consequences follow, and
 * each one is a thing this file refuses to do:
 *
 *   1. THE AMOUNT IS NEVER HIDDEN AND NEVER COUNTS UP. It is on screen from the
 *      first frame. A count-up ticker on a number the player already knows
 *      manufactures suspense about a settled quantity — the same manipulation
 *      as a slot reel, applied to a payout that was never in doubt.
 *   2. NOTHING IS REVEALED. What animates is the player's OWN CARDS gathering
 *      and a seal closing over them. The material is what they earned, not a
 *      surprise the house produces.
 *   3. IT ENDS ON THE RECEIPT, not on the money — transaction id, wallet
 *      destination, and the no-wagering statement. The last frame a player
 *      looks at should be the one they would screenshot for support.
 *
 * AND IT OPENS ON A CONFIRMATION, because the exchange is DESTRUCTIVE. Sets are
 * repeatable: exchanging spends one copy of every card in the set, so the set
 * empties and must be collected again. Cards belong to several sets at once, so
 * this can also cut into sets the player has not finished. Every one of those
 * facts is stated before the press, never discovered after it.
 *
 * `R` is an owner parameter. The figure rendered here is the set's provisional
 * demo reward, carrying its provisional label; the GRANT supplies only the
 * transaction id, because the port does not decide what R is.
 * ==========================================================================*/

"use client";

import { useEffect, useId, useReducer } from "react";
import { formatVnd } from "@/lib/format";
import type { ExchangeImpact, RewardGrant } from "@/lib/collection";
import type { DemoCard } from "@/lib/collection/fixtures/epl";
import type { CollectionSet } from "@/lib/collection";
import { Overlay } from "@/components/layout/_internal/Overlay";
import { CardArt } from "./CardArt";

/* The beats. Bounded and finite — a ceremony that can be waited out is a
   ceremony; one that loops is an attention trap. */
type Beat = "gather" | "seal" | "receipt";

const TIMINGS: Record<Exclude<Beat, "receipt">, number> = {
  gather: 900,
  seal: 700,
};

interface Props {
  set: CollectionSet;
  /** the player's own cards for this set — the material of the animation */
  cards: DemoCard[];
  /** present once the credit succeeded; the receipt waits for it */
  grant: RewardGrant | null;
  /** set when the credit was refused — the ceremony becomes a plain message */
  error: string | null;
  /**
   * What the exchange will cost. Rendered BEFORE anything is spent — see the
   * confirm phase below. Null once the exchange has been authorised.
   */
  impact: ExchangeImpact | null;
  /** names for the collateral rows, resolved by the caller */
  setNameOf: (setId: string) => string;
  /** how many times this set has already been completed and exchanged */
  exchangeCount: number;
  onConfirm: () => void;
  onClose: () => void;
}

export function RewardCeremony({
  set,
  cards,
  grant,
  error,
  impact,
  setNameOf,
  exchangeCount,
  onConfirm,
  onClose,
}: Props) {
  const titleId = useId();
  const [beat, advance] = useReducer(
    (b: Beat): Beat => (b === "gather" ? "seal" : "receipt"),
    "gather",
  );

  /* Reduced motion skips to the receipt. It does not merely disable the
     transitions — a player who asked for less motion should not have to sit
     through the same 1.6s of nothing happening. */
  const reduced =
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

  useEffect(() => {
    if (reduced || beat === "receipt") return;
    const t = setTimeout(advance, TIMINGS[beat]);
    return () => clearTimeout(t);
  }, [beat, reduced]);

  const settled = reduced || beat === "receipt";

  /* ── CONFIRM. Nothing has been spent yet. ─────────────────────────────────
     The exchange consumes one copy of every card in the set, and cards belong
     to several sets at once — so this can also reduce sets the player has not
     finished. That is a destructive action on something they earned, for real
     money, and it is disclosed before the press rather than explained after. */
  if (impact) {
    const spare = impact.covered.length;
    return (
      <Overlay open onClose={onClose} presentation="auto" labelledBy={titleId}>
        <div className="collection-ceremony-panel grid gap-space-2 justify-items-center text-center [padding:var(--space-4)_var(--space-3)_var(--space-3)]">
          <p className="m-[0] text-t-micro tracking-[0.08em] uppercase text-brand-accent-fg">Xác nhận đổi thưởng</p>
          <h2 id={titleId} className="m-[0] text-t-h2 font-weight-bold text-text-hi text-balance">{set.name}</h2>
          {set.reward && <p className="[margin:var(--space-1)_0_0] collection-num-lg text-text-hi">{formatVnd(set.reward)}</p>}
          <p className="m-[0] text-t-micro text-text-dim">Số liệu demo — chưa phải mức thưởng công bố.</p>

          <div className="w-full mt-space-2 p-space-4 [border:1px_solid_var(--brand-accent-hairline)] rounded-lg [background:var(--surface-2)] grid gap-space-2 text-left">
            <p className="m-[0] text-t-sm text-text leading-lh-body [&_strong]:text-text-hi [&_strong]:font-weight-semi">
              Đổi thưởng sẽ <strong>dùng hết {set.size} thẻ</strong> của bộ này.
              Bộ trở về <strong>0/{set.size}</strong> và bạn có thể sưu tầm lại từ đầu.
            </p>

            {spare > 0 && (
              <p className="m-[0] text-t-micro text-win leading-lh-body">
                Bạn có thẻ dự phòng cho <strong>{spare}</strong> thẻ — những thẻ này
                bạn vẫn giữ lại.
              </p>
            )}

            {impact.collateral.length > 0 && (
              <>
                <p className="m-[0] text-t-micro font-weight-semi text-caution">Các bộ khác cũng bị ảnh hưởng:</p>
                <ul className="list-none m-[0] p-[0] grid gap-[4px] [&_li]:text-t-micro [&_li]:text-text-mid [&_li]:leading-lh-tight [&_strong]:text-caution [&_strong]:tabular-nums">
                  {impact.collateral.map((c) => (
                    <li key={c.setId}>
                      {setNameOf(c.setId)} — mất <strong>{c.loses}</strong> thẻ
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>

          {/* NOT "Đổi thưởng" — that is the label of the rail button that
              opened this panel. A confirm step that repeats its trigger's
              wording reads as "did my tap register?" rather than as a decision,
              and it is the destructive half of the pair. */}
          <button type="button" className="w-full min-h-tap-min [border:0] rounded-md [background:var(--brand-accent)] text-brand-on-accent text-t-body font-weight-bold cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--brand-accent-2)] hover:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:hover:[transform:none]" onClick={onConfirm}>
            Xác nhận · dùng {set.size} thẻ
          </button>
          <button type="button" className="w-full min-h-tap-min [border:1px_solid_var(--border)] rounded-md [background:transparent] text-text-mid text-t-sm cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--surface-hover)] hover:text-text hover:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:hover:[transform:none]" onClick={onClose}>
            Để sau
          </button>
        </div>
      </Overlay>
    );
  }

  if (error) {
    return (
      <Overlay open onClose={onClose} presentation="auto" labelledBy={titleId}>
        <div className="collection-ceremony-panel grid gap-space-2 justify-items-center text-center [padding:var(--space-4)_var(--space-3)_var(--space-3)]">
          <h2 id={titleId} className="m-[0] text-t-h2 font-weight-bold text-text-hi">Chưa đổi được thưởng</h2>
          <p className="m-[0] text-t-body text-text">{error}</p>
          <p className="m-[0] text-t-sm text-text-dim">
            Bộ sưu tập của bạn không thay đổi. Vui lòng thử lại.
          </p>
          <button type="button" className="w-full min-h-tap-min [border:0] rounded-md [background:var(--brand-accent)] text-brand-on-accent text-t-body font-weight-bold cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--brand-accent-2)] hover:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:hover:[transform:none]" onClick={onClose}>
            Đóng
          </button>
        </div>
      </Overlay>
    );
  }

  return (
    <Overlay open onClose={onClose} presentation="auto" labelledBy={titleId}>
      <div className="collection-ceremony-panel grid gap-space-2 justify-items-center text-center [padding:var(--space-4)_var(--space-3)_var(--space-3)]" data-beat={settled ? "receipt" : beat}>
        {/* ── the player's own cards, gathering ─────────────────────────── */}
        <div className="relative w-full h-[190px] grid place-items-center mb-space-2" aria-hidden="true">
          <div className="relative w-[120px] h-[168px]">
            {cards.map((c, i) => (
              <div
                key={c.id}
                className="collection-ceremony-card"
                style={{
                  /* Spread before, stacked after. Index drives both, so a
                     5-card set and an 11-card set gather identically. */
                  "--i": i - (cards.length - 1) / 2,
                  "--n": cards.length,
                } as React.CSSProperties}
              >
                <CardArt card={c} rare={c.tierId === "rare"} />
              </div>
            ))}
          </div>

          {/* The seal draws itself closed over the gathered cards. */}
          <svg className="collection-ceremony-seal" viewBox="0 0 120 120" role="presentation">
            <circle className="collection-ceremony-seal-ring" cx="60" cy="60" r="52" />
            <circle className="collection-ceremony-seal-ring-inner" cx="60" cy="60" r="44" />
            <path className="collection-ceremony-seal-tick" d="M42 61 l13 13 l24 -26" />
          </svg>
        </div>

        {/* ── what happened, stated plainly ─────────────────────────────── */}
        <p className="m-[0] text-t-micro tracking-[0.08em] uppercase text-brand-accent-fg">Hoàn thành bộ sưu tập</p>
        <h2 id={titleId} className="m-[0] text-t-h2 font-weight-bold text-text-hi text-balance">{set.name}</h2>
        <p className="m-[0] text-t-sm text-text-mid [&_strong]:text-text [&_strong]:tabular-nums">
          Đủ <strong>{set.size}/{set.size}</strong> thẻ
        </p>

        {/* ── the amount. On screen from the first frame, never counting up.
               It was on the rail before the player pressed anything. ─────── */}
        {set.reward && (
          <p className="[margin:var(--space-1)_0_0] collection-num-lg text-text-hi">{formatVnd(set.reward)}</p>
        )}
        <p className="m-[0] text-t-micro text-text-dim">Số liệu demo — chưa phải mức thưởng công bố.</p>

        {/* ── the receipt: the frame worth screenshotting ───────────────── */}
        <div className="collection-ceremony-receipt" data-ready={settled && Boolean(grant)}>
          {settled && grant ? (
            <>
              <p className="m-[0] text-t-body text-text [&_strong]:text-text-hi [&_strong]:font-weight-semi">Đã cộng vào <strong>ví chính</strong></p>
              <ul className="list-none m-[0] p-[0] grid gap-[4px] [&_li]:text-t-micro [&_li]:text-text-mid [&_li]:leading-lh-body [&_strong]:text-text [&_strong]:font-weight-semi">
                <li>Dùng được ngay, <strong>không kèm điều kiện cược</strong>.</li>
                {/* The set was SPENT. Stating it on the receipt matters more
                    than stating it in the terms: this is the frame the player
                    is looking at when their collection empties. */}
                <li>
                  Đã dùng <strong>{set.size} thẻ</strong> — bộ này trở về{" "}
                  <strong>0/{set.size}</strong>, sưu tầm lại để đổi tiếp.
                </li>
                <li>
                  Đây là lần đổi thứ <strong>{exchangeCount}</strong> của bộ này.
                </li>
              </ul>
              <p className="m-[0] text-t-micro text-text-dim [&_code]:text-text-mid [&_code]:tabular-nums [&_code]:wrap-anywhere">
                Mã giao dịch: <code>{grant.transactionId}</code>
              </p>
              <button type="button" className="w-full min-h-tap-min [border:0] rounded-md [background:var(--brand-accent)] text-brand-on-accent text-t-body font-weight-bold cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--brand-accent-2)] hover:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:hover:[transform:none]" onClick={onClose}>
                Xong
              </button>
            </>
          ) : (
            <p className="m-[0] text-t-sm text-text-dim min-h-tap-min grid place-items-center">Đang chuyển vào ví…</p>
          )}
        </div>
      </div>
    </Overlay>
  );
}
