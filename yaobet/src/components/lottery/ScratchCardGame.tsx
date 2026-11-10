/* ============================================================================
 * ScratchCardGame — the scratch-card surface itself (modal).
 *
 * INTEGRATION. LotteryRoot owns a `playing` flag and CONDITIONALLY MOUNTS the
 * game in its GAME MOUNT POINT — `<ScratchCardStage onExit={…} />` is that
 * seam, and it is the export LotteryRoot uses. ScratchCardGame underneath it
 * takes the `open` / `onClose` pair, so a host that would rather keep the
 * component mounted and toggle a boolean can do that instead; both land on the
 * same body. Composes the shell Overlay (scrim + role="dialog" + aria-modal +
 * focus trap + Esc + return-focus to the `Cào ngay` trigger + --z-modal)
 * exactly as AuthModal does — no second trap, no second scrim.
 *
 * THE TICKET
 *   Two labelled sections on one warm panel, and BOTH are coated:
 *     • SỐ TRÚNG THƯỞNG — the small precious band, four medallions.
 *     • SỐ CỦA BẠN      — the main field, twelve medallions, 4 across x 3 down.
 *   Every cell whose number matches ANY of the four winning numbers pays; there
 *   is no "best line", they all count.
 *
 * THE REVEAL IS A REAL SCRATCH-OFF
 *   Each section carries ONE canvas coating (ScratchSurface) that is erased by
 *   dragging — a single sweep clears several medallions at once. There is no
 *   per-cell click target: clicking a cell to flip it is exactly what this
 *   replaces. The two sections settle INDEPENDENTLY and the outcome resolves
 *   only when both are open.
 *
 *   The coating is painted, not shipped: coverArt strikes each medallion from
 *   the same custom properties the stylesheets read, so it re-skins with the
 *   brand instead of baking one palette into a PNG.
 *
 * HONESTY
 *   The card states, before anything is touched, that the result was fixed
 *   before the first stroke, and publishes the odds and the prize ladder. No
 *   urgency, no countdown, no "cược thêm", no loss-chasing — and a compensation
 *   is never presented as a win.
 *
 * NO HYDRATION MISMATCH
 *   makeScratchCard() is random. It is called in an effect / from a user
 *   action ONLY — never during render — so the server and the first client
 *   paint agree (the Overlay is not even in the DOM until `open`).
 *
 * REDUCED MOTION
 *   usePrefersReducedMotion drives `data-motion="off"` on the root (every
 *   keyframe/transition in this tree is killed by it), removes the coating's
 *   fade-out in JS, and disables the count-up tween. Result: an instant state
 *   change with no movement.
 * ==========================================================================*/

"use client";

import { useCallback, useEffect, useId, useRef, useState, type CSSProperties } from "react";
import { formatCount, formatVnd } from "@/lib/format";
import {
  LADDER,
  SCRATCH_ODDS,
  makeScratchCard,
  type ScratchCard,
  type ScratchOutcome,
} from "@/lib/mock/lottery";
import { Button } from "@/ui/Button/Button";
import { Icon } from "@/ui/Icon/Icon";
import { Overlay } from "../layout/_internal/Overlay";
import { usePrefersReducedMotion } from "../layout/_internal/usePrefersReducedMotion";
import { OutcomeFrame } from "./_internal/OutcomeFrame";
import { ScratchSurface } from "./_internal/ScratchSurface";

export interface ScratchCardGameProps {
  /** default-closed; LotteryRoot flips this from its play control:
   *  `<ScratchCardGame open={playing} onClose={() => setPlaying(false)} />` */
  open: boolean;
  onClose: () => void;
  /** fired whenever a fresh card is dealt (the "play" seam) */
  onPlay?: (card: ScratchCard) => void;
  /** fired once, when both sections are open and the result is final */
  onSettled?: (card: ScratchCard) => void;
}

/** Shape-holders for the single paint before the mount effect deals a card. */
const PLACEHOLDER_WINNING = [0, 1, 2, 3];
const PLACEHOLDER_PANELS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];

/** The forceable outcomes for the dev control (NOT part of the player flow). */
const DEV_OUTCOMES: ReadonlyArray<{ value: ScratchOutcome; label: string }> = [
  { value: "lose", label: "Thua" },
  { value: "partial", label: "Thưởng nhỏ" },
  { value: "win", label: "Thắng" },
];

/** Two-digit face value: 7 → "07". */
function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

/**
 * Short form of a LADDER rung for the narrow grid cell: 10.000 → "10K",
 * 20.000.000 → "20Tr". LOSSLESS by construction — every rung of the published
 * 1-2-5 ladder divides exactly, so no digit is rounded away. The full figure is
 * printed alongside it from 480px up, and always carried in the cell's
 * screen-reader sentence, so the truthful number is never only an abbreviation.
 */
function shortVnd(amount: number): string {
  return amount >= 1_000_000 ? `${amount / 1_000_000}Tr` : `${amount / 1_000}K`;
}

export function ScratchCardGame({ open, onClose, onPlay, onSettled }: ScratchCardGameProps) {
  const titleId = useId();

  if (!open) return null; // lazy: not in the DOM until opened (no modal farm)

  return (
    <Overlay
      open={open}
      onClose={onClose}
      presentation="auto"
      labelledBy={titleId}
      desktopMaxWidth={560}
      /* the whole card is a drag surface — a swipe-to-dismiss on the panel
       * would fight every downward scratch stroke on mobile. Esc, the scrim and
       * the Đóng button remain. */
      swipeDismiss={false}
    >
      {/* fresh body per open — the card, the section states and the dev
       *  override all reset by unmount, with no reset effect. */}
      <ScratchCardBody
        titleId={titleId}
        onClose={onClose}
        onPlay={onPlay}
        onSettled={onSettled}
      />
    </Overlay>
  );
}

export interface ScratchCardStageProps {
  /** hand control back to the hub (LotteryRoot's `setPlaying(false)`) */
  onExit: () => void;
}

/**
 * Conditional-mount alias for LotteryRoot's GAME MOUNT POINT, so both seams
 * compile against the same component:
 *   {playing ? <ScratchCardStage onExit={() => setPlaying(false)} /> : null}
 */
export function ScratchCardStage({ onExit }: ScratchCardStageProps) {
  return <ScratchCardGame open onClose={onExit} />;
}

interface BodyProps {
  titleId: string;
  onClose: () => void;
  onPlay?: (card: ScratchCard) => void;
  onSettled?: (card: ScratchCard) => void;
}

function ScratchCardBody({ titleId, onClose, onPlay, onSettled }: BodyProps) {
  const reduced = usePrefersReducedMotion();

  const [card, setCard] = useState<ScratchCard | null>(null);
  /** the two coatings settle independently */
  const [bandOpen, setBandOpen] = useState(false);
  const [fieldOpen, setFieldOpen] = useState(false);
  /** polite announcement — canvas erasing says nothing to a screen reader */
  const [notice, setNotice] = useState("");
  /** dev override, sticky across re-deals within one open. undefined = random */
  const [forced, setForced] = useState<ScratchOutcome | undefined>(undefined);

  const deal = useCallback((force?: ScratchOutcome) => {
    // makeScratchCard() is random — only ever called from here, and this is
    // only ever reached from an effect or a click. Never during render.
    setCard(makeScratchCard(force));
    setBandOpen(false);
    setFieldOpen(false);
    setNotice("");
  }, []);

  // FIRST CARD — in an effect, never during render (no hydration mismatch).
  // One-shot on mount (the body remounts per open), not a render loop.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    deal();
  }, [deal]);

  // the "play" seam: one notification per dealt card. Kept out of `deal` so no
  // ref is written during render (react-hooks/refs).
  const onPlayRef = useRef(onPlay);
  useEffect(() => {
    onPlayRef.current = onPlay;
  });
  useEffect(() => {
    if (card) onPlayRef.current?.(card);
  }, [card]);

  const settled = card != null && bandOpen && fieldOpen;

  // announce the settled result to the host exactly once per card
  const settledFor = useRef<string | null>(null);
  useEffect(() => {
    if (!settled || !card) return;
    if (settledFor.current === card.id) return;
    settledFor.current = card.id;
    onSettled?.(card);
  }, [settled, card, onSettled]);

  const revealBand = useCallback(() => {
    setBandOpen(true);
    setNotice("Đã cào xong vùng số trúng thưởng.");
  }, []);
  const revealField = useCallback(() => {
    setFieldOpen(true);
    setNotice("Đã cào xong vùng số của bạn.");
  }, []);
  const revealAll = useCallback(() => {
    setBandOpen(true);
    setFieldOpen(true);
    setNotice("Đã mở cả hai vùng của thẻ.");
  }, []);

  /* Matched cells and the winning-number medallion they answer to share a pulse
   * RUNG (--k), so the two beat in unison once both sections are open — that
   * unison is the visible link, and each cell's sentence is the same link in
   * words for a screen reader. */
  const matchedNumbers = new Set(
    settled ? (card?.panels.filter((p) => p.matched).map((p) => p.n) ?? []) : [],
  );

  /* Remount the coatings per card: a fresh canvas, a fresh cover, and every
   * latch inside the surface reset without a single reset effect. */
  const cardKey = card?.id ?? "pending";

  return (
    <div className="lottery-scratch-card-game-body pt-space-2 px-space-4 pb-space-5 min-[480px]:px-space-5" data-motion={reduced ? "off" : "on"}>
      <header className="flex items-center justify-between mb-space-2">
        <h2 id={titleId} className="lottery-type-h2 text-text-hi">
          Thẻ cào
        </h2>
        <button type="button" className="lottery-scratch-card-game-close-btn inline-flex items-center justify-center min-w-tap-min min-h-tap-min mr-[calc(var(--space-2)*-1)] [border:0] [background:transparent] text-text-mid cursor-pointer rounded-md hover:text-text-hi focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2" aria-label="Đóng" onClick={onClose}>
          <Icon name="close" size={22} />
        </button>
      </header>

      {/* the honesty line, stated BEFORE the first stroke */}
      <p className="mb-space-4 text-t-micro leading-lh-body text-text-mid">
        Kết quả của thẻ này đã được ấn định trước khi bạn cào nhát đầu tiên. Cào nhanh
        hay chậm, theo thứ tự nào, kết quả không đổi.
      </p>

      {/* ══ THE TICKET ══════════════════════════════════════════════════════ */}
      <div className="lottery-scratch-card-game-ticket relative py-space-5 px-space-4 min-[480px]:px-space-5 [border:1px_solid_var(--border)] rounded-card select-none">
        <div className="absolute inset-space-2 [border:1px_solid_color-mix(in_srgb,var(--brand-accent)_20%,transparent)] rounded-lg pointer-events-none" aria-hidden="true" />

        {/* ── the precious band: four winning numbers ──────────────────── */}
        <section className="relative" aria-label="Vùng số trúng thưởng">
          <div className="flex items-center gap-space-3">
            <h3 className="lottery-type-label flex-none text-brand-accent-fg">Số trúng thưởng</h3>
            <span className="flex-[1_1_auto] h-[1px] min-w-space-4 [background:linear-gradient(90deg,color-mix(in_srgb,var(--brand-accent)_45%,transparent),transparent)]" aria-hidden="true" />
            <span className="lottery-scratch-card-game-section-state flex-none py-[2px] px-space-2 rounded-pill text-t-micro leading-lh-tight" data-open={bandOpen || undefined}>
              {bandOpen ? "Đã mở" : "Cào để mở"}
            </span>
          </div>

          <ScratchSurface
            key={`band-${cardKey}`}
            variant="band"
            className="lottery-scratch-card-game-band-well mt-space-3 py-space-3 px-space-4 [border:1px_solid_color-mix(in_srgb,var(--brand-accent)_58%,transparent)] rounded-lg"
            revealed={bandOpen}
            onReveal={revealBand}
            reduced={reduced}
          >
            <ul className="grid grid-cols-[repeat(4,minmax(0,1fr))] gap-gap-sm m-[0] p-[0] list-none" aria-hidden={bandOpen ? undefined : true}>
              {card
                ? card.winning.map((n, k) => (
                    <li key={`${n}-${k}`} className="flex justify-center min-w-[0]">
                      <span
                        className="lottery-scratch-card-game-band-coin relative grid place-items-center w-full aspect-[1] rounded-pill font-brand-font-num font-weight-bold [font-variant-numeric:tabular-nums] leading-lh-tight max-w-[72px] [border:1px_solid_color-mix(in_srgb,var(--brand-accent-2)_72%,var(--canvas))] text-brand-on-accent text-t-h2"
                        data-token
                        data-hit={matchedNumbers.has(n) || undefined}
                        style={{ "--k": k } as CSSProperties}
                      >
                        <span className="relative">{pad2(n)}</span>
                      </span>
                    </li>
                  ))
                : /* pre-deal: keep the footprint so the ticket never jumps */
                  PLACEHOLDER_WINNING.map((k) => (
                    <li key={k} className="flex justify-center min-w-[0]">
                      <span className="lottery-scratch-card-game-band-coin relative grid place-items-center w-full aspect-[1] rounded-pill font-brand-font-num font-weight-bold [font-variant-numeric:tabular-nums] leading-lh-tight max-w-[72px] [border:1px_solid_color-mix(in_srgb,var(--brand-accent-2)_72%,var(--canvas))] text-brand-on-accent text-t-h2" data-token />
                    </li>
                  ))}
            </ul>
          </ScratchSurface>
        </section>

        {/* the tear line between the two halves of the ticket */}
        <div className="lottery-scratch-card-game-perf relative h-[0] my-space-5 mx-[0] [border-top:1px_dashed_color-mix(in_srgb,var(--brand-accent)_34%,transparent)]" aria-hidden="true" />

        {/* ── the main field: twelve cells, 4 across x 3 down ──────────── */}
        <section className="relative" aria-label="Vùng số của bạn">
          <div className="flex items-center gap-space-3">
            <h3 className="lottery-type-label flex-none text-brand-accent-fg">Số của bạn</h3>
            <span className="flex-[1_1_auto] h-[1px] min-w-space-4 [background:linear-gradient(90deg,color-mix(in_srgb,var(--brand-accent)_45%,transparent),transparent)]" aria-hidden="true" />
            <span className="lottery-scratch-card-game-section-state flex-none py-[2px] px-space-2 rounded-pill text-t-micro leading-lh-tight" data-open={fieldOpen || undefined}>
              {fieldOpen ? "Đã mở" : "Cào để mở"}
            </span>
          </div>

          <ScratchSurface
            key={`field-${cardKey}`}
            variant="field"
            className="mt-space-3 p-space-3 [border:1px_solid_color-mix(in_srgb,var(--brand-accent)_26%,transparent)] rounded-lg [background:var(--canvas)]"
            revealed={fieldOpen}
            onReveal={revealField}
            reduced={reduced}
          >
            <ul className="grid grid-cols-[repeat(4,minmax(0,1fr))] gap-y-space-3 gap-x-gap-sm min-[480px]:gap-y-space-4 min-[480px]:gap-x-space-3 m-[0] p-[0] list-none" aria-hidden={fieldOpen ? undefined : true}>
              {card
                ? card.panels.map((panel, i) => {
                    // which of the four winning numbers this cell answers to;
                    // the pulse rung the cell and that medallion share.
                    const rung = Math.max(0, card.winning.indexOf(panel.n));
                    const hit = settled && panel.matched;
                    return (
                      <li
                        key={`${card.id}-${i}`}
                        className="lottery-scratch-card-game-field-cell flex flex-col items-center gap-gap-xs min-w-[0]"
                        data-hit={hit || undefined}
                        style={{ "--k": rung } as CSSProperties}
                      >
                        <span className="lottery-scratch-card-game-field-coin relative grid place-items-center w-full aspect-[1] rounded-pill font-brand-font-num font-weight-bold [font-variant-numeric:tabular-nums] leading-lh-tight max-w-[58px] text-t-h3" data-token aria-hidden="true">
                          <span className="relative">{pad2(panel.n)}</span>
                        </span>
                        <span className="lottery-scratch-card-game-field-prize font-brand-font-num text-t-micro [font-variant-numeric:tabular-nums] leading-lh-tight whitespace-nowrap" aria-hidden="true">
                          <span className="min-[560px]:hidden">{shortVnd(panel.prize)}</span>
                          <span className="hidden min-[560px]:inline">{formatVnd(panel.prize)}</span>
                        </span>
                        {/* the whole truth, in one sentence, for a screen
                         *  reader — including WHICH winning number was hit */}
                        <span className="absolute w-[1px] h-[1px] m-[-1px] p-[0] overflow-hidden [clip:rect(0,0,0,0)] whitespace-nowrap [border:0]">
                          {panel.matched
                            ? `Ô ${i + 1}: số ${pad2(panel.n)}, trùng số trúng thưởng ${pad2(panel.n)}, thưởng ${formatVnd(panel.prize)}.`
                            : `Ô ${i + 1}: số ${pad2(panel.n)}, không trùng. Giải của ô này là ${formatVnd(panel.prize)}.`}
                        </span>
                      </li>
                    );
                  })
                : /* pre-deal: twelve inert cells, so the grid never resizes */
                  PLACEHOLDER_PANELS.map((i) => (
                    <li key={i} className="lottery-scratch-card-game-field-cell flex flex-col items-center gap-gap-xs min-w-[0]">
                      <span className="lottery-scratch-card-game-field-coin relative grid place-items-center w-full aspect-[1] rounded-pill font-brand-font-num font-weight-bold [font-variant-numeric:tabular-nums] leading-lh-tight max-w-[58px] text-t-h3" data-token aria-hidden="true" />
                      <span className="lottery-scratch-card-game-field-prize font-brand-font-num text-t-micro [font-variant-numeric:tabular-nums] leading-lh-tight whitespace-nowrap" aria-hidden="true">
                        &nbsp;
                      </span>
                    </li>
                  ))}
            </ul>
          </ScratchSurface>
        </section>
      </div>

      <p className="mt-space-4 mx-[0] mb-[0] text-t-sm leading-lh-body text-text-mid">
        Giữ và kéo qua lớp phủ để cào — một nhát kéo mở được nhiều ô liền nhau. Cào cả
        hai vùng thì thẻ mới ra kết quả.
      </p>

      {/* canvas erasing announces nothing on its own; this line does */}
      <p className="absolute w-[1px] h-[1px] m-[-1px] p-[0] overflow-hidden [clip:rect(0,0,0,0)] whitespace-nowrap [border:0]" role="status" aria-live="polite">
        {notice}
      </p>

      {settled && card && <OutcomeFrame card={card} reduced={reduced} />}

      <footer className="mt-space-5 pt-space-4 [border-top:1px_solid_var(--border)]">
        {/* published odds + the printed prize ladder — on the card itself,
         *  not behind a terms link. The strings are the published sentences. */}
        <h3 className="text-t-micro font-weight-semi tracking-[0.06em] uppercase text-text-mid">Tỷ lệ công bố</h3>
        {/* SCRATCH_ODDS ships BARE values — the strip supplies the labels. */}
        <dl className="grid grid-cols-[1fr] gap-space-2 mt-space-2 mx-[0] mb-[0] min-[480px]:grid-cols-[repeat(3,1fr)] min-[480px]:gap-gap-sm">
          <div className="lottery-scratch-card-game-odds-row flex items-baseline justify-between gap-space-3 min-w-[0] min-[480px]:block">
            <dt>Tỷ lệ trúng</dt>
            <dd>{SCRATCH_ODDS.hitRate}</dd>
          </div>
          <div className="lottery-scratch-card-game-odds-row flex items-baseline justify-between gap-space-3 min-w-[0] min-[480px]:block">
            <dt>Giải cao nhất</dt>
            <dd>{SCRATCH_ODDS.topPrize}</dd>
          </div>
          <div className="lottery-scratch-card-game-odds-row flex items-baseline justify-between gap-space-3 min-w-[0] min-[480px]:block">
            <dt>Chi phí mỗi bậc giải</dt>
            <dd>{SCRATCH_ODDS.rungCost}</dd>
          </div>
        </dl>
        <p className="mt-space-3 text-t-micro leading-lh-body text-text-dim">
          Mọi bậc giải tốn như nhau, nên không bậc nào là bậc rẻ mà hệ thống lặng lẽ
          đẩy bạn về. Các mức giải: {LADDER.map((v) => formatCount(v)).join(" · ")} ₫
        </p>

        {/* "Mở tất cả" — the keyboard and screen-reader path, and the way out
         *  for anyone who cannot drag. Deliberately SECONDARY and physically
         *  away from the ticket, so scratching stays the natural path. */}
        {!settled && (
          <button type="button" className="lottery-scratch-card-game-reveal-all inline-block mt-space-3 py-space-2 px-[0] min-h-tap-min [border:0] [background:transparent] text-t-sm text-text-mid underline underline-offset-[3px] cursor-pointer hover:text-text-hi focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 focus-visible:rounded-sm" onClick={revealAll}>
            Mở tất cả
          </button>
        )}

        <div className="flex flex-wrap gap-gap-sm mt-space-4">
          <Button variant="ghost" size="md" onClick={onClose}>
            Đóng
          </Button>
          {settled && (
            <Button variant="ghost" size="md" onClick={() => deal(forced)}>
              Mở thẻ mới
            </Button>
          )}
        </div>

        {/* ---- DEV ONLY: force an outcome so all three can be demoed. Clearly
         *  fenced off and labelled; not part of the player's flow. ---- */}
        <div className="flex flex-wrap items-center gap-gap-sm mt-space-5 p-space-3 [border:1px_dashed_var(--text-dim)] rounded-md [background:var(--surface-2)]">
          <span className="py-[2px] px-space-2 rounded-pill bg-info text-shell text-t-micro font-weight-bold tracking-[0.06em] uppercase">dev</span>
          <span className="text-t-micro text-text-mid">Buộc kết quả</span>
          <div className="flex flex-wrap gap-gap-xs" role="group" aria-label="Dev: buộc kết quả thẻ">
            {DEV_OUTCOMES.map((o) => (
              <button
                key={o.value}
                type="button"
                className="lottery-scratch-card-game-dev-btn py-space-1 px-space-3 min-h-tap-min rounded-pill [background:transparent] text-t-micro cursor-pointer focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2"
                data-active={forced === o.value || undefined}
                aria-pressed={forced === o.value}
                onClick={() => {
                  setForced(o.value);
                  deal(o.value);
                }}
              >
                {o.label}
              </button>
            ))}
            <button
              type="button"
              className="lottery-scratch-card-game-dev-btn py-space-1 px-space-3 min-h-tap-min rounded-pill [background:transparent] text-t-micro cursor-pointer focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2"
              data-active={forced === undefined || undefined}
              aria-pressed={forced === undefined}
              onClick={() => {
                setForced(undefined);
                deal();
              }}
            >
              Ngẫu nhiên
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
