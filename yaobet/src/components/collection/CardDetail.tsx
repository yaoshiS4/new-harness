/* ============================================================================
 * Yaobet — CARD DETAIL overlay.
 * ----------------------------------------------------------------------------
 * The card-scoped view. Four facts the feature already captured and never once
 * showed a player: how many copies they hold, which sets the card serves, when
 * they first got it, and — the expensive one — its PUBLISHED DRAW RATE.
 *
 * ⛔ NO MONEY IN THIS FILE. No reward amount, no `Đổi thưởng`, no set reward.
 * Rewards are set-scoped (`CollectionSet.reward`); printing one against a
 * single card puts a price on that card, which is a different economy from the
 * one that was designed. Completion and claiming stay on the rails.
 *
 * ⛔ THE RATE IS NEVER HAND-AUTHORED, AND IT IS ALWAYS SET-SCOPED. It comes
 * from `ratesBySet()` in `epl.ts`, which is derived and dev-time checked to sum
 * to 1 within each set. That apparatus exists because an earlier draft
 * hand-authored both rates, they summed to 163.5%, and the screen advertised
 * 11.5% on a card whose real probability was 7.03%.
 *
 * The set scoping is the SECOND form of that same defect, found later: the
 * engine resolves an allocation and then rolls INSIDE that set, renormalising
 * (`adapters/fixtures.ts`). So the whole-pool weight in `drawTable()` is the
 * probability of no open a player ever receives, and a card in three sets has
 * three rates rather than one. Publishing a single number here would have been
 * false through allocation instead of through arithmetic — which is why this
 * component publishes one line per set and never a headline figure.
 *
 * The overlay is the house `Overlay` at `presentation="auto"` — sheet <640px,
 * dialog ≥640px, focus-trapped, Esc / scrim / swipe dismiss, body-scroll lock.
 * A bespoke modal would lose all five.
 *
 * It is also the first place `CardArt`'s 300×420 face renders at 300+px, so
 * the nameplate the file header has always promised is finally legible.
 * ==========================================================================*/

"use client";

import { useId, useMemo } from "react";
import Link from "next/link";
import { formatPercent } from "@/lib/format";
import type { HeldCard } from "@/lib/collection";
import { ratesBySet, setById, type DemoCard } from "@/lib/collection/fixtures/epl";
import { Overlay } from "@/components/layout/_internal/Overlay";
import { CardArt } from "./CardArt";
// One formatter, one clock reading. `Nhận lần đầu` and a history row must never
// disagree about what "12/08 21:04" means.
import { formatTime } from "./CollectionHistory";

interface Props {
  card: DemoCard;
  /** absent = the player does not hold this card */
  held: HeldCard | undefined;
  onClose: () => void;
}

export function CardDetail({ card, held, onClose }: Props) {
  const titleId = useId();

  /* The DERIVED rates, looked up — never re-authored, never rounded twice.
     One per set, because that is the grain at which the engine actually rolls. */
  const rates = useMemo(() => ratesBySet(card.id), [card.id]);

  const sets = card.setIds
    .map((id) => setById(id))
    .filter((s): s is NonNullable<typeof s> => Boolean(s));

  const count = held?.count ?? 0;

  return (
    <Overlay open onClose={onClose} presentation="auto" labelledBy={titleId}>
      <div className="grid gap-space-2 [padding:var(--space-3)_var(--space-4)_var(--space-4)] min-w-[0]">
        <header className="flex items-center justify-between gap-space-3 min-w-[0]">
          <h2 id={titleId} className="m-[0] text-t-h2 font-weight-bold text-text-hi leading-lh-tight wrap-anywhere min-w-[0]">
            {card.name}
          </h2>
          <button type="button" className="flex-[0_0_auto] min-h-tap-min [padding:0_var(--space-4)] rounded-md [border:1px_solid_var(--border)] [background:var(--surface-2)] text-text-mid text-t-sm font-weight-semi cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--surface-hover)] hover:text-text hover:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:hover:[transform:none]" onClick={onClose}>
            Đóng
          </button>
        </header>

        <div className="w-full max-w-[300px] [margin:0_auto_var(--space-2)]">
          <CardArt card={card} rare={card.tierId === "rare"} ghost={!held} />
        </div>

        <p className="m-[0] text-t-sm text-text-mid leading-lh-tight">
          {card.club} · {card.position}
        </p>

        {/* — the holding. `Trong đó N thẻ trùng.` only at count ≥ 2; a card
            held once is not a card with zero duplicates, it is just a card. */}
        {held ? (
          <div className="grid gap-space-1 p-space-4 [border:1px_solid_var(--brand-accent-hairline)] rounded-lg [background:var(--surface-2)]">
            <p className="m-[0] text-t-sm text-text-mid leading-lh-body [&_strong]:text-text-hi [&_strong]:font-weight-semi [&_strong]:tabular-nums">
              Đang giữ: <strong>{count} thẻ</strong>
            </p>
            {count >= 2 && (
              <p className="m-[0] text-t-micro text-text-dim leading-lh-body">Trong đó {count - 1} thẻ trùng.</p>
            )}
            <p className="m-[0] text-t-sm text-text-mid leading-lh-body [&_strong]:text-text-hi [&_strong]:font-weight-semi [&_strong]:tabular-nums">
              Nhận lần đầu: <strong>{formatTime(held.firstAcquiredAt)}</strong>
            </p>
          </div>
        ) : (
          <div className="grid gap-space-1 p-space-4 [border:1px_solid_var(--brand-accent-hairline)] rounded-lg [background:var(--surface-2)]">
            <p className="m-[0] text-t-sm text-text-mid leading-lh-body [&_strong]:text-text-hi [&_strong]:font-weight-semi [&_strong]:tabular-nums">Chưa có thẻ này.</p>
          </div>
        )}

        {/* — membership, in full. This is where multi-set membership is stated
            plainly, so the flat grid never has to repeat a card to express it.
            The links land on the catalogue; each rail carries its set id as an
            anchor. */}
        {sets.length > 0 && (
          <p className="m-[0] text-t-sm text-text-mid leading-lh-body [&_strong]:text-text-hi [&_strong]:font-weight-semi [&_strong]:tabular-nums">
            Có trong:{" "}
            {sets.map((s, i) => (
              <span key={s.id}>
                {i > 0 && <span className="text-text-dim"> · </span>}
                <Link href={`/bo-suu-tap#${s.id}`} className="text-text font-weight-semi underline underline-offset-[2px] hover:text-text-hi focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px]">
                  {s.name}
                </Link>
              </span>
            ))}
          </p>
        )}

        {/* — the published rate. The restoration point for.
             SET-SCOPED, because that is the only form in which it is true: the
             engine allocates an open to a set and rolls inside it, so a card in
             several sets has several rates and no single one. */}
        {rates.length > 0 && (
          <div className="m-[0] pt-space-2 [border-top:1px_solid_var(--border)] text-t-sm text-text-mid [&_strong]:text-text-hi [&_strong]:font-weight-bold [&_strong]:tabular-nums">
            <p className="[margin:0_0_var(--space-1)]">Tỷ lệ ra thẻ khi mở cho bộ:</p>
            <ul className="list-none m-[0] p-[0] grid gap-[2px]">
              {rates.map((r) => (
                <li key={r.setId}>
                  {r.name}: <strong>{formatPercent(r.rate * 100, 2)}</strong>
                </li>
              ))}
            </ul>
          </div>
        )}

        <p className="m-[0] text-t-micro text-text-dim leading-lh-body">
          Số liệu demo — tỷ lệ là tạm tính, chưa phải tỷ lệ công bố.
        </p>
      </div>
    </Overlay>
  );
}
