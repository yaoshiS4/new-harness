/* ============================================================================
 * Yaobet — BỘ SƯU TẬP · "Tủ Kính" (The Cabinet). THE SHIPPED SURFACE.
 * ----------------------------------------------------------------------------
 * WHAT IS ACTUALLY ON THIS PAGE, top to bottom:
 *
 *   Zone 1 · <PackStage>   — chance. A lit stage, five foil packs, one CTA and
 *                            one number (opens remaining), plus a terms button
 *                            that fires a ZERO-ARGUMENT callback.
 *   · the entry row        — `Thẻ của tôi · N thẻ ›` → the inventory page.
 *   Zone 2 · the rails     — contract. One horizontal rail per set: every card
 *                            in the set at 104px, owned in colour and unowned
 *                            ghosted; the set's `owned/size`, a progress bar,
 *                            its reward, and one `Đổi thưởng` button.
 *   · the demo controls, and a toast that carries the payout transaction id.
 *
 * THE FIREWALL. Money exists in Zone 2 and nowhere else, and that is enforced
 * by props, not by discipline: `PackStage` receives `{ opens, last, busy,
 * onOpen, onOpenInfo }` and no reward value can reach it. The terms overlay is
 * rendered HERE, as a sibling of the stage, for the same reason.
 *
 * Rules this is built to, not decorated with:
 *   · Cards are on screen at arrival. Nothing is hidden behind a tap.
 *   · No `???` card, ever. The rails are the CATALOGUE and every card in them
 *     is named and ghosted rather than hidden. (They are not the inventory —
 *     that is /bo-suu-tap/cua-toi, and it is a different question.)
 *   · Ownership is a TREATMENT on one tile, not a separate view — and it is
 *     also in the tile's accessible name, because a CSS filter is invisible to
 *     a screen reader.
 *   · Copies show as a `×N` badge and NOTHING else. Completion is
 *     distinct-only; duplicates must never appear to advance a set.
 *   · One reveal, one duration, for every card. No rarity-differentiated
 *     ceremony — that is win-juice by another name.
 *   · The reward is prominent by POSITION AND REPETITION, never by size.
 *     The card art always outranks the number.
 *   · No bet CTA. No "best value" badge. No sort-by-reward. Ranking sets by
 *     return is a spend recommendation.
 *
 * NOT here, deliberately: aggregate stat tiles (`3/18` and `17%` are one fact
 * printed twice, and `/18` publishes a universe size has not ruled), and
 * the history log (it is unbounded, it is what support reads, and it needs a
 * URL — it lives on the inventory page).
 * ==========================================================================*/

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { formatVnd } from "@/lib/format";
import type {
  CollectionPorts,
  CollectionState,
  HeldCard,
  ExchangeImpact,
  OpenOutcome,
  RewardGrant,
} from "@/lib/collection";
import { exchangeImpact, meanOpensForRemaining } from "@/lib/collection";
import {
  DEMO_SETS,
  DEMO_TIERS,
  cardById,
  cardsInSet,
  type DemoCard,
} from "@/lib/collection/fixtures/epl";
import { Icon } from "@/ui/Icon/Icon";
import { Overlay } from "@/components/layout/_internal/Overlay";
import { CardArt } from "./CardArt";
import { PackStage } from "./PackStage";
import { CollectionTerms } from "./CollectionTerms";
import { CollectionHistory } from "./CollectionHistory";
import { RewardCeremony } from "./RewardCeremony";

const PLAYER = "demo-player";

/** Mean opens still needed to finish a set, given what is already held. */
function opensToFinish(setId: string, held: ReadonlySet<string>): number {
  const missing = cardsInSet(setId).filter((c) => !held.has(c.id));
  if (missing.length === 0) return 0;
  return Math.ceil(
    meanOpensForRemaining(
      missing.map((c) => DEMO_TIERS.find((t) => t.id === c.tierId)!.drawRate),
    ),
  );
}

/**
 * Rail order, decided ONCE per session from the holding at arrival: least
 * additional effort first. Frozen thereafter, because a rail that changes
 * position at the exact moment it is being highlighted is a rail the player
 * was reaching for. Ordering by reward would be an inducement in any order.
 */
function railOrderFor(heldCards: HeldCard[]): string[] {
  const held = new Set(heldCards.map((h) => h.cardId));
  return DEMO_SETS.map((s) => ({ id: s.id, opens: opensToFinish(s.id, held) }))
    .sort((a, b) => a.opens - b.opens)
    .map((r) => r.id);
}

interface Props {
  ports: CollectionPorts;
  onFireActivity: () => void;
  /** DEV — grant every card in one set so the exchange case is reachable */
  onCompleteSet: () => void;
  onReset: () => void;
}

export function CollectionApp({ ports, onFireActivity, onCompleteSet, onReset }: Props) {
  const [state, setState] = useState<CollectionState | null>(null);
  const [status, setStatus] = useState<"loading" | "error" | "ready">("loading");
  const [last, setLast] = useState<OpenOutcome | null>(null);
  const [pulsed, setPulsed] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [railOrder, setRailOrder] = useState<string[] | null>(null);
  const [termsOpen, setTermsOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  /** the exchange in progress — null when no ceremony is on screen */
  const [ceremony, setCeremony] = useState<{
    setId: string;
    grant: RewardGrant | null;
    error: string | null;
    /** non-null = the confirm phase; nothing has been spent yet */
    impact: ExchangeImpact | null;
  } | null>(null);
  const timers = useRef<number[]>([]);

  const refresh = useCallback(async () => {
    const env = await ports.state.get(PLAYER);
    if (env.status === "live") {
      setState(env.value);
      // Frozen at the FIRST successful load and never recomputed.
      setRailOrder((prev) => prev ?? railOrderFor(env.value.heldCards));
      setStatus("ready");
    } else if (env.status === "error") {
      setStatus("error");
    }
  }, [ports]);

  useEffect(() => {
    const pending = timers.current;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
    return () => pending.forEach(clearTimeout);
  }, [refresh]);

  /* THE HOLDING, as objects. `count` and `firstAcquiredAt` are carried, not
     collapsed away on the first line of derived state — a card is an object
     here, and the `×N` badge, the accessible name and the whole inventory page
     all hang off that one decision. */
  const heldById = useMemo(
    () => new Map((state?.heldCards ?? []).map((h) => [h.cardId, h] as const)),
    [state],
  );
  const vested = useMemo(
    () => state?.entitlements.filter((e) => e.state === "vested") ?? [],
    [state],
  );

  const rails = useMemo(() => {
    const built = DEMO_SETS.map((s) => {
      const cards = cardsInSet(s.id);
      // DISTINCT cards held, never copies. Duplicates do not advance a set and
      // must not appear to: `heldById.has()` is the whole guarantee.
      const missing = cards.filter((c) => !heldById.has(c.id));
      return {
        set: s,
        cards,
        owned: cards.length - missing.length,
        remaining: missing.length,
      };
    });
    if (!railOrder) return built;
    return built.sort(
      (a, b) => railOrder.indexOf(a.set.id) - railOrder.indexOf(b.set.id),
    );
  }, [heldById, railOrder]);

  const openOne = useCallback(async () => {
    if (busy || vested.length === 0) return;
    setBusy(true);
    const ent = vested[0];
    const res = await ports.outcome.draw(PLAYER, ent.id, `draw-${ent.id}`);
    if (res.status === "applied" || res.status === "duplicate") {
      const outcome = res.value;
      setLast(outcome);
      await refresh();
      // The rails this card belongs to pulse in a stagger — that teaches
      // multi-set membership without a word of copy.
      const card = cardById(outcome.cardId);
      (card?.setIds ?? []).forEach((sid, i) => {
        timers.current.push(
          window.setTimeout(() => setPulsed((p) => [...p, sid]), i * 80),
        );
      });
      timers.current.push(
        window.setTimeout(() => setPulsed([]), 900),
      );
    } else {
      setToast(res.reason);
    }
    setBusy(false);
  }, [busy, vested, ports, refresh]);

  /**
   * Exchange. The ceremony OPENS FIRST, on the click, and the credit runs
   * underneath it — the player is looking at their own completed set while the
   * wallet call is in flight, and the receipt fills in when it lands. Waiting
   * on the network before showing anything would put a dead half-second on the
   * one action in this feature that is a payout.
   */
  /**
   * PHASE 1 — ask. Nothing is spent yet.
   *
   * The exchange is destructive: it consumes a copy of every card in the set,
   * and cards belong to several sets at once. The cost is computed from the
   * holding and shown before the player commits.
   */
  const proposeClaim = useCallback(
    (setId: string) => {
      if (busy) return;
      const counts = new Map([...heldById].map(([id, h]) => [id, h.count]));
      const impact = exchangeImpact(
        cardsInSet(setId).map((c) => c.id),
        counts,
        DEMO_SETS.filter((s) => s.id !== setId).map((s) => ({
          setId: s.id,
          cardIds: cardsInSet(s.id).map((c) => c.id),
        })),
      );
      setCeremony({ setId, grant: null, error: null, impact });
    },
    [busy, heldById],
  );

  /**
   * PHASE 2 — spend. The ceremony plays while the credit is in flight; waiting
   * on the network first would put a dead half-second on a payout.
   */
  const confirmClaim = useCallback(async () => {
    if (busy || !ceremony) return;
    const { setId } = ceremony;
    setBusy(true);
    // Drops `impact`, which is what switches the overlay from ask to ceremony.
    setCeremony({ setId, grant: null, error: null, impact: null });

    /* The key carries the exchange COUNT. Sets are repeatable now, so a key of
       `claim-<setId>` would make every exchange after the first a replay of the
       first one — the player would collect the set again and be handed the
       original receipt with no new credit. */
    const n = state?.progress.find((p) => p.setId === setId)?.exchangeCount ?? 0;
    const res = await ports.wallet.credit(
      PLAYER,
      setId,
      "cash-like",
      `claim-${setId}-${n}`,
    );

    if (res.status === "rejected") {
      setCeremony({ setId, grant: null, error: res.reason, impact: null });
    } else {
      setCeremony({ setId, grant: res.value, error: null, impact: null });
      // Re-read: the set has just emptied and every rail it touches moved.
      await refresh();
    }
    setBusy(false);
  }, [busy, ceremony, ports, refresh, state]);

  if (status === "loading") {
    return <div className="[padding:var(--space-3)_var(--gutter)_calc(var(--bottombar-h)+var(--space-6))] max-w-[760px] [margin:0_auto] text-text min-[900px]:max-w-[980px]"><p className="text-text-mid text-t-body">Đang tải…</p></div>;
  }
  if (status === "error") {
    return (
      <div className="[padding:var(--space-3)_var(--gutter)_calc(var(--bottombar-h)+var(--space-6))] max-w-[760px] [margin:0_auto] text-text min-[900px]:max-w-[980px]">
        <p className="text-text-mid text-t-body">Không tải được bộ sưu tập.</p>
        <button className="min-h-tap-min [padding:0_var(--space-4)] rounded-md text-t-sm font-weight-semi cursor-pointer [border:1px_solid_var(--border)] [background:var(--surface-2)] text-text [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:not-disabled:[background:var(--surface-hover)] hover:not-disabled:[transform:scale(1.05)] disabled:[background:var(--surface-disabled)] disabled:text-text-dim disabled:border-border disabled:cursor-not-allowed focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:hover:not-disabled:[transform:none]" onClick={() => void refresh()}>Thử lại</button>
      </div>
    );
  }


  return (
    <div className="[padding:var(--space-3)_var(--gutter)_calc(var(--bottombar-h)+var(--space-6))] max-w-[760px] [margin:0_auto] text-text min-[900px]:max-w-[980px]">
      {/* ══ ZONE 1 · the pack stage — chance. No reward value is passed in.
             `onOpenInfo` carries no argument: the stage asks, this component
             answers, and the terms render as a SIBLING below. ══ */}
      <PackStage
        opens={vested.length}
        last={last}
        busy={busy}
        onOpen={openOne}
        onOpenInfo={() => setTermsOpen(true)}
        onOpenHistory={() => setHistoryOpen(true)}
      />

      <Overlay
        open={termsOpen}
        onClose={() => setTermsOpen(false)}
        presentation="auto"
        labelledBy="collection-terms-title"
      >
        <div className="sticky top-[0] z-[1] flex items-center gap-space-2 [padding:var(--space-2)_var(--space-3)] [background:var(--surface)] [border-bottom:1px_solid_var(--border)]">
          <h2 id="collection-terms-title" className="m-[0] collection-heading-h4 text-text-hi">
            Điều khoản
          </h2>
          <button
            type="button"
            className="ml-auto grid place-items-center w-tap-min h-tap-min rounded-md [border:1px_solid_var(--border)] [background:var(--surface-2)] text-text-hi cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] [&_svg]:[transition:transform_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--surface-hover)] hover:border-brand-accent hover:[transform:scale(1.05)] hover:[&_svg]:[transform:scale(1.1)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:[&_svg]:[transition:none] motion-reduce:hover:[transform:none] motion-reduce:hover:[&_svg]:[transform:none]"
            onClick={() => setTermsOpen(false)}
            aria-label="Đóng"
          >
            <Icon name="close" size={20} />
          </button>
        </div>
        <div className="max-h-[min(85vh,calc(92vh-108px))] overflow-y-auto [-webkit-overflow-scrolling:touch] p-space-3">
          <CollectionTerms />
        </div>
      </Overlay>

      {/* ══ ZONE 2 · BỘ SƯU TẬP — contract. Rewards live only here. ══ */}
      <section className="mt-space-4 grid grid-cols-[minmax(0,1fr)] gap-space-2 min-w-[0]" aria-label="Bộ sưu tập">
        <div className="collection-collection-plate grid grid-cols-[1fr_auto_1fr] items-center gap-space-2 [margin:var(--space-4)_0_var(--space-2)]">
          <span className="collection-collection-plate-wing" aria-hidden />
          <h2 className="m-[0] [padding:var(--space-2)_var(--space-4)] rounded-md [border:1px_solid_var(--brand-accent-hairline)] [background:var(--surface-2)] text-t-sm font-weight-bold tracking-[0.14em] text-brand-accent-fg whitespace-nowrap">BỘ SƯU TẬP</h2>
          <span className="collection-collection-plate-wing" aria-hidden />
        </div>
        {/* The section header line: what the rails are, and the way into the
            player's own inventory. The entry was a full-width row here, which
            put a heavy block between the note and the rails; as a compact pill
            it shares the line instead of interrupting it.

            It stays a LINK to a page, not a modal. An inventory needs a URL, a
            sort control, a scroll position and a back button — a modal has none
            of those, and the page already exists with all four. The count is
            DISTINCT cards; no denominator, because the universe size is
            and unruled. */}
        <div className="flex items-start justify-between gap-space-3 flex-wrap mb-space-3 [@media(max-width:1023px)]:pr-[calc(48px+var(--space-2))]">
          <p className="m-[0] text-t-micro text-text-dim leading-lh-body flex-[1_1_240px]">
            Đủ toàn bộ thẻ trong bộ mới đổi được thưởng. Số liệu demo — tỷ lệ và
            phần thưởng là tạm tính, chưa phải tỷ lệ công bố.
          </p>
          <Link className="inline-flex items-center gap-space-2 min-h-tap-min [padding:0_var(--space-4)] [border:1px_solid_var(--border)] rounded-md [background:var(--surface)] text-text-hi text-t-sm font-weight-semi no-underline whitespace-nowrap flex-[0_0_auto] ml-auto [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] [&_svg]:[transition:transform_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--surface-hover)] hover:border-brand-accent hover:[transform:scale(1.05)] hover:[&_svg]:[transform:scale(1.1)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:[&_svg]:[transition:none] motion-reduce:hover:[transform:none] motion-reduce:hover:[&_svg]:[transform:none]" href="/bo-suu-tap/cua-toi">
            <Icon name="card" size={16} />
            <span>Thẻ của tôi</span>
            <span className="[padding:2px_var(--space-2)] rounded-pill [background:var(--tint)] text-text-hi font-weight-bold tabular-nums">{heldById.size}</span>
            <Icon name="chevronRight" size={14} />
          </Link>
        </div>

        {rails.map(({ set, cards, owned, remaining }) => {
          const complete = remaining === 0;
          /* How many times this set has already paid. Sets are REPEATABLE, so
             this is a history line, never a reason to disable the button —
             exchanging empties the set and `complete` goes false by itself. */
          const times =
            state?.progress.find((p) => p.setId === set.id)?.exchangeCount ?? 0;
          const pct = Math.round((owned / set.size) * 100);
          return (
            <article
              key={set.id}
              /* The anchor `CardDetail`'s `Có trong:` links target. Without it
                 those links land at the top of this page instead of the rail. */
              id={set.id}
              className={`[--rail-pad:var(--space-4)] min-[900px]:[--rail-pad:var(--space-5)] min-w-[0] rounded-lg [padding:var(--rail-pad)_0] [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard)] hover:[transform:scale(1.02)] motion-reduce:[transition:none] motion-reduce:hover:[transform:none] ${pulsed.includes(set.id) ? "[border:1px_solid_var(--brand-accent)] [background:var(--surface-hover)]" : "[border:1px_solid_var(--brand-accent-hairline)] [background:var(--surface)]"}`}
            >
              <header className="[padding:0_var(--rail-pad)] grid grid-cols-[minmax(0,1fr)] gap-space-2">
                <div className="flex items-baseline justify-between gap-space-2">
                  <h2 className="m-[0] collection-heading-h4 text-text-hi">{set.name}</h2>
                  <span className="text-t-sm text-text-mid tabular-nums whitespace-nowrap">
                    {owned}/{set.size}
                  </span>
                </div>

                <div className="h-[4px] rounded-pill [background:var(--surface-3)] overflow-hidden" aria-hidden>
                  <span className="block h-full [background:var(--text-mid)]" style={{ width: `${pct}%` }} />
                </div>

                {/* Same five fields, same order, same x-offset on every rail —
                    scanning the right edge IS the comparison. */}
                <div className="grid grid-cols-[1fr_auto] items-baseline gap-space-2">
                  <span className="text-t-micro text-text-dim tabular-nums leading-lh-tight min-w-[0]">
                    {complete ? "Sẵn sàng đổi" : ""}
                  </span>
                  <span className="text-t-micro text-text-dim whitespace-nowrap [&_strong]:text-t-sm [&_strong]:text-text-hi [&_strong]:font-weight-semi [&_strong]:tabular-nums">
                    Thưởng{" "}
                    <strong>
                      {set.reward ? formatVnd(set.reward.amount) : "—"}
                    </strong>
                  </span>
                </div>
              </header>

              <div className="overflow-x-auto [-webkit-overflow-scrolling:touch]">
                <ul className="flex gap-space-2 list-none [margin:var(--space-2)_0_0] [padding:0_var(--rail-pad)]">
                  {cards.map((c) => (
                    <Tile key={c.id} card={c} held={heldById.get(c.id)} />
                  ))}
                </ul>
              </div>

              {/* One action per set. Enabled only once every card is held —
                  a set you cannot exchange says so by being unavailable, not
                  by explaining itself. */}
              <div className="[padding:var(--space-3)_var(--rail-pad)_0] [&>*]:w-full">
                <button
                  className="min-h-tap-min [padding:0_var(--space-4)] rounded-md text-t-sm font-weight-semi cursor-pointer [border:1px_solid_var(--brand-accent-hairline)] [background:var(--tint)] text-text-hi [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:not-disabled:[background:var(--surface-hover)] hover:not-disabled:[transform:scale(1.05)] disabled:[background:var(--surface-disabled)] disabled:text-text-dim disabled:border-border disabled:cursor-not-allowed focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:hover:not-disabled:[transform:none] hover:not-disabled:border-brand-accent"
                  onClick={() => proposeClaim(set.id)}
                  disabled={busy || !complete}
                >
                  Đổi thưởng
                </button>
                {times > 0 && (
                  <span className="text-t-micro text-text-dim tabular-nums self-center">Đã đổi {times} lần</span>
                )}
              </div>
            </article>
          );
        })}
      </section>

      <div className="flex items-center gap-space-2 mt-space-5 pt-space-3 [border-top:1px_dashed_var(--border)]">
        <span className="text-t-micro uppercase tracking-[0.1em] text-text-dim">Demo</span>
        <button className="min-h-tap-min [padding:0_var(--space-4)] rounded-md text-t-sm font-weight-semi cursor-pointer [border:1px_solid_var(--border)] [background:var(--surface-2)] text-text [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:not-disabled:[background:var(--surface-hover)] hover:not-disabled:[transform:scale(1.05)] disabled:[background:var(--surface-disabled)] disabled:text-text-dim disabled:border-border disabled:cursor-not-allowed focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:hover:not-disabled:[transform:none]" onClick={onFireActivity}>+1 lượt mở</button>
        {/* Reaches the completed/claimable case in one click instead of ~60
            opens. It grants CARDS, never the reward — the exchange is still a
            deliberate action the player takes. */}
        <button className="min-h-tap-min [padding:0_var(--space-4)] rounded-md text-t-sm font-weight-semi cursor-pointer [border:1px_solid_var(--border)] [background:var(--surface-2)] text-text [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:not-disabled:[background:var(--surface-hover)] hover:not-disabled:[transform:scale(1.05)] disabled:[background:var(--surface-disabled)] disabled:text-text-dim disabled:border-border disabled:cursor-not-allowed focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:hover:not-disabled:[transform:none]" onClick={onCompleteSet}>Hoàn thành 1 bộ</button>
        <button className="min-h-tap-min [padding:0_var(--space-4)] rounded-md text-t-sm font-weight-semi cursor-pointer [border:1px_solid_var(--border)] [background:var(--surface-2)] text-text [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:not-disabled:[background:var(--surface-hover)] hover:not-disabled:[transform:scale(1.05)] disabled:[background:var(--surface-disabled)] disabled:text-text-dim disabled:border-border disabled:cursor-not-allowed focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:hover:not-disabled:[transform:none]" onClick={onReset}>Đặt lại</button>
      </div>

      {/* History, opened by the stage's zero-argument callback. It carries a
          link to its own URL: support asks for one, and a modal has none. */}
      <Overlay
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        presentation="auto"
        labelledBy="collection-history-title"
      >
        <div className="sticky top-[0] z-[1] flex items-center gap-space-2 [padding:var(--space-2)_var(--space-3)] [background:var(--surface)] [border-bottom:1px_solid_var(--border)]">
          <h2 id="collection-history-title" className="m-[0] collection-heading-h4 text-text-hi">
            Lịch sử
          </h2>
          <button
            type="button"
            className="ml-auto grid place-items-center w-tap-min h-tap-min rounded-md [border:1px_solid_var(--border)] [background:var(--surface-2)] text-text-hi cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] [&_svg]:[transition:transform_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--surface-hover)] hover:border-brand-accent hover:[transform:scale(1.05)] hover:[&_svg]:[transform:scale(1.1)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:[&_svg]:[transition:none] motion-reduce:hover:[transform:none] motion-reduce:hover:[&_svg]:[transform:none]"
            onClick={() => setHistoryOpen(false)}
            aria-label="Đóng"
          >
            <Icon name="close" size={20} />
          </button>
        </div>
        <div className="max-h-[min(85vh,calc(92vh-108px))] overflow-y-auto [-webkit-overflow-scrolling:touch] p-space-3">
          {/* Mounted only while open, so it re-reads the trace on every open
              rather than serving a page cached before the last few draws. */}
          {historyOpen && (
            <CollectionHistory ports={ports} nonce={state?.heldCards.length ?? 0} />
          )}
          <p className="[margin:var(--space-3)_0_0] pt-space-3 [border-top:1px_dashed_var(--border)] text-center">
            <Link
              className="text-text-hi text-t-sm font-weight-semi no-underline hover:underline focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px]"
              href="/bo-suu-tap/cua-toi?tab=lich-su"
              onClick={() => setHistoryOpen(false)}
            >
              Mở trang lịch sử →
            </Link>
          </p>
        </div>
      </Overlay>

      {/* The exchange ceremony. A SIBLING of the rails, holding the grant — the
          rail button only calls `claim`, exactly as the pack stage only calls
          `onOpenInfo`. */}
      {ceremony && (
        <RewardCeremony
          set={DEMO_SETS.find((s) => s.id === ceremony.setId)!}
          cards={cardsInSet(ceremony.setId)}
          grant={ceremony.grant}
          error={ceremony.error}
          impact={ceremony.impact}
          setNameOf={(id) => DEMO_SETS.find((s) => s.id === id)?.name ?? id}
          exchangeCount={
            state?.progress.find((p) => p.setId === ceremony.setId)?.exchangeCount ?? 0
          }
          onConfirm={() => void confirmClaim()}
          onClose={() => setCeremony(null)}
        />
      )}

      {/* The receipt carries the payout transaction id — a payout-proof moment
          assistive tech never heard. Polite, never assertive: interrupting the
          reveal to read a transaction id is its own defect. */}
      <div className="fixed left-[50%] bottom-[calc(var(--bottombar-h)+var(--space-3))] [transform:translateX(-50%)] max-w-[90vw] z-(--z-toast) pointer-events-none" role="status" aria-live="polite">
        {toast && (
          <button type="button" className="pointer-events-auto max-w-full [padding:var(--space-3)_var(--space-4)] rounded-md [border:1px_solid_var(--border)] [background:var(--surface-3)] text-text text-t-micro cursor-pointer" onClick={() => setToast(null)}>
            {toast}
          </button>
        )}
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------------------
 * One tile. Ownership is a treatment, not a separate view — never a `???`.
 *
 * Three states, and the silence in the middle one is deliberate:
 *   no row   → ghost art, NO badge. A `×0` reads as a stock-out and makes an
 *              empty catalogue feel like a failure rather than a start.
 *   count 1  → colour, NO badge. A `×1` on every card turns the catalogue into
 *              a spreadsheet and makes "one" look deficient.
 *   count ≥2 → `×N`, top-left. A fact, stated once, in the smallest legible
 *              form — and never in the corner the `N bộ` set badge occupies.
 * --------------------------------------------------------------------------*/

function Tile({ card, held }: { card: DemoCard; held: HeldCard | undefined }) {
  const multi = card.setIds.length > 1;
  const copies = held?.count ?? 0;
  return (
    <li className="flex-[0_0_104px] grid gap-[4px]">
      <div className="relative">
        <CardArt
          card={card}
          rare={card.tierId === "rare"}
          ghost={!held}
          label={ownershipLabel(card.name, copies)}
        />
        {copies >= 2 && (
          // aria-hidden: the count is already in the art's accessible name, and
          // announcing it twice is worse than not announcing it at all.
          <span className="absolute top-[4px] left-[4px] text-[10px] font-weight-bold tabular-nums tracking-[0.02em] [padding:2px_5px] rounded-pill [background:var(--surface-3)] text-text-hi [border:1px_solid_var(--border)]" aria-hidden>
            ×{copies}
          </span>
        )}
        {multi && <span className="absolute top-[4px] right-[4px] text-[9px] tracking-[0.04em] [padding:2px_5px] rounded-pill [background:var(--surface-3)] text-text-mid [border:1px_solid_var(--border)]">{card.setIds.length} bộ</span>}
      </div>
    </li>
  );
}

/** Ownership carried in the accessible name — it is CSS-only otherwise. */
function ownershipLabel(name: string, copies: number): string {
  if (copies === 0) return `${name} — chưa có`;
  if (copies === 1) return `${name} — đang giữ`;
  return `${name} — đang giữ ${copies} thẻ`;
}
