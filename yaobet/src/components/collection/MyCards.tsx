/* ============================================================================
 * Yaobet — THẺ CỦA TÔI · the INVENTORY surface (/bo-suu-tap/cua-toi).
 * ----------------------------------------------------------------------------
 * The rails at /bo-suu-tap are the CATALOGUE: every card that exists, ghosts
 * included, set-scoped, and the only place money is named. This page is the
 * INVENTORY: what the player actually holds, card-scoped. They answer
 * different questions; neither replaces the other.
 *
 * Rules this is built to, not decorated with:
 *
 *   · A FLAT GRID, never grouped by set. `setIds` is multi-membership — van
 *     Dijk is in all three sets — so a set-grouped page renders him three
 *     times, each carrying `×4`, and STATES four while LOOKING like it states
 *     twelve. That is a wrong-number bug, not a taste question. One card, one
 *     tile, one place; membership is a badge, never a heading.
 *
 *   · Quantity is silent until it is a fact. No badge when not held. NO BADGE
 *     AT `count === 1` — a `×1` on every card turns a collection into a
 *     spreadsheet and makes "one" look deficient, which is a manufactured
 *     dissatisfaction. `×N` for N ≥ 2 only, top-LEFT so it never shares a
 *     corner with the `N bộ` set badge (`3 bộ` and `×3` adjacent at 9px read
 *     as one number).
 *
 *   · Ownership is not left to a CSS filter. The tile's accessible name
 *     carries state and count; the art inside it is aria-hidden so the name is
 *     announced once, not twice.
 *
 *   · NO MONEY, EVER. No reward amount, no `Đổi thưởng`. Rewards are
 *     set-scoped; printing one on a card-scoped surface puts a price on an
 *     individual card, which is a different economy from the designed one.
 *
 *   · No sort by rarity, by reward, or by "closest to completing a set". The
 *     first two are spend recommendations by another name; the third is a
 *     chase nudge dressed as a convenience.
 *
 *   · No bet CTA in the empty state. "Đặt cược ngay" here would be the single
 *     most inducing pixel in the feature.
 *
 *   · Tab state lives in the QUERY STRING, not in component state. "Send me
 *     the link to your history" is a real support sentence, and a component
 *     tab has no link. That linkability is the entire point.
 *
 *   · Tiles are ≥140px wide. The rails' 104px renders the card's own 19px
 *     nameplate at ≈6.6px; this page is where the art is finally legible.
 * ==========================================================================*/

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Tabs } from "@/ui";
import type { CollectionPorts, CollectionState, HeldCard } from "@/lib/collection";
import { DEMO_CARDS, type DemoCard } from "@/lib/collection/fixtures/epl";
import { CardArt } from "./CardArt";
import { CardDetail } from "./CardDetail";
import { CollectionHistory } from "./CollectionHistory";

const PLAYER = "demo-player";

/* The two tabs. Query values are the player-facing Vietnamese slug, so a
   pasted URL is readable by the person receiving it. */
type Tab = "the-cua-toi" | "lich-su";

/** Only `lich-su` opens the history; anything else (incl. absent) = inventory. */
function toTab(value: string | null | undefined): Tab {
  return value === "lich-su" ? "lich-su" : "the-cua-toi";
}

/** `Đang giữ` (default) or `Tất cả`. Not a URL concern — the tab is. */
type Filter = "holding" | "all";

/** The three permitted orders. See the ban list in the header. */
type Sort = "recent" | "count" | "name";

const SORT_LABELS: { id: Sort; label: string }[] = [
  { id: "recent", label: "Mới nhất" },
  { id: "count", label: "Số lượng" },
  { id: "name", label: "Tên" },
];

interface Props {
  ports: CollectionPorts;
}

export function MyCards({ ports }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [state, setState] = useState<CollectionState | null>(null);
  const [status, setStatus] = useState<"loading" | "error" | "ready">("loading");
  const [filter, setFilter] = useState<Filter>("holding");
  const [sort, setSort] = useState<Sort>("recent");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [nonce, setNonce] = useState(0);

  /* The tab is DERIVED from the URL on every render — a tab click, a pasted
     link, the terms-modal footer link and browser back/forward all flow
     through the same query and cannot disagree. */
  const tab = toTab(searchParams.get("tab"));

  const refresh = useCallback(async () => {
    const env = await ports.state.get(PLAYER);
    if (env.status === "live") {
      setState(env.value);
      setStatus("ready");
    } else if (env.status === "error") {
      setStatus("error");
    } else if (env.status === "absent") {
      // No stored holdings is a truthful zero here, not a failure: the store's
      // seed IS an empty collection. Render the empty state, not an error.
      setState(null);
      setStatus("ready");
    }
  }, [ports]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refresh]);

  /* THE ROOT DERIVATION. A Map, not a Set — `count` and `firstAcquiredAt` are
     the two fields this whole page exists to show, and collapsing to a Set of
     ids on the first line of derived state is exactly how they were lost. */
  const heldById = useMemo(
    () =>
      new Map<string, HeldCard>(
        (state?.heldCards ?? []).map((h) => [h.cardId, h] as const),
      ),
    [state],
  );

  /* Distinct cards held. No denominator: the universe size is and is not
     published here — a `/18` regresses every player's number overnight when
     the pool grows, with no event to explain it. */
  const heldCount = heldById.size;

  const cards = useMemo(() => {
    const held: DemoCard[] = [];
    const rest: DemoCard[] = [];
    for (const c of DEMO_CARDS) (heldById.has(c.id) ? held : rest).push(c);

    const byName = (a: DemoCard, b: DemoCard) => a.name.localeCompare(b.name, "vi");

    const ordered = [...held].sort((a, b) => {
      if (sort === "name") return byName(a, b);
      const ha = heldById.get(a.id)!;
      const hb = heldById.get(b.id)!;
      if (sort === "count") return hb.count - ha.count || byName(a, b);
      // `Mới nhất` — firstAcquiredAt desc. ISO strings sort lexicographically.
      return hb.firstAcquiredAt.localeCompare(ha.firstAcquiredAt) || byName(a, b);
    });

    // `Tất cả` APPENDS the not-held cards, ghosted, after the held ones. It
    // does not interleave them: a page the owner asked for so a player can see
    // what they collected must not open as a wall of grey.
    return filter === "holding" ? ordered : [...ordered, ...rest.sort(byName)];
  }, [heldById, sort, filter]);

  const onTab = useCallback(
    (id: string) => {
      const next = toTab(id);
      if (next === tab) return;
      // Shallow query sync — a soft update, no reload. Always write an explicit
      // tab so returning to the inventory is unambiguous.
      router.replace(`${pathname}?tab=${next}`, { scroll: false });
    },
    [tab, pathname, router],
  );

  // Stable identity: `useFocusTrap` re-runs its effect when `onClose` changes,
  // and a fresh closure every render would re-record the trigger and fight the
  // overlay for focus.
  const closeDetail = useCallback(() => setSelectedId(null), []);

  const selected = selectedId ? DEMO_CARDS.find((c) => c.id === selectedId) : undefined;

  return (
    <div className="[padding:var(--space-3)_var(--gutter)_calc(var(--bottombar-h)+var(--space-6))] max-w-[760px] [margin:0_auto] text-text min-w-[0] min-[900px]:max-w-[980px]">
      <nav className="flex items-center min-h-tap-min">
        <Link href="/bo-suu-tap" className="inline-flex items-center min-h-tap-min pr-space-2 text-text-mid text-t-sm font-weight-semi no-underline hover:text-text-hi focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px]">
          ← Bộ sưu tập
        </Link>
      </nav>

      <h1 className="[margin:0_0_var(--space-3)] text-t-h1 font-weight-bold text-text-hi leading-lh-tight">Thẻ của tôi</h1>

      <Tabs
        items={[
          { id: "the-cua-toi", label: "Thẻ của tôi" },
          { id: "lich-su", label: "Lịch sử" },
        ]}
        active={tab}
        onChange={onTab}
        scrollable={false}
        label="Thẻ của tôi và lịch sử"
        className="mb-space-3"
      />

      {tab === "lich-su" ? (
        <div
          role="tabpanel"
          id="panel-lich-su"
          aria-labelledby="tab-lich-su"
          className="min-w-[0]"
        >
          {/* Self-contained: its own trace read, its own loading/empty/error
              states, its own pagination. Not a modal — an unbounded log inside
              a focus-trapped, scroll-locked overlay is a scroll-trap with no
              floor, and support needs a URL to read the same rows at. */}
          <CollectionHistory ports={ports} nonce={nonce} />
        </div>
      ) : (
        <div
          role="tabpanel"
          id="panel-the-cua-toi"
          aria-labelledby="tab-the-cua-toi"
          className="min-w-[0]"
        >
          {status === "loading" && <p className="m-[0] text-text-mid text-t-body">Đang tải…</p>}

          {status === "error" && (
            <div className="grid justify-items-start gap-space-3">
              <p className="m-[0] text-text-mid text-t-body">Không tải được thẻ của bạn.</p>
              <button
                type="button"
                className="min-h-tap-min [padding:0_var(--space-4)] rounded-md [border:1px_solid_var(--border)] [background:var(--surface-2)] text-text text-t-sm font-weight-semi cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--surface-hover)] hover:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:hover:[transform:none]"
                onClick={() => {
                  setStatus("loading");
                  setNonce((n) => n + 1);
                  void refresh();
                }}
              >
                Thử lại
              </button>
            </div>
          )}

          {status === "ready" && (
            <>
              <p className="[margin:0_0_var(--space-3)] text-t-body text-text-mid leading-lh-tight [&_strong]:text-text-hi [&_strong]:font-weight-bold [&_strong]:tabular-nums">
                Bạn đang giữ <strong>{heldCount}</strong> thẻ
              </p>

              <div className="flex flex-wrap items-center justify-between gap-space-2 mb-space-3">
                <div className="flex gap-space-2 min-w-[0]" role="group" aria-label="Lọc thẻ">
                  <button
                    type="button"
                    className={`min-h-tap-min [padding:0_var(--space-4)] rounded-md text-t-sm font-weight-semi tabular-nums whitespace-nowrap cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--surface-hover)] hover:text-text hover:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:hover:[transform:none] ${filter === "holding" ? "[border:1px_solid_var(--brand-accent)] [background:var(--tint)] text-text-hi" : "[border:1px_solid_var(--border)] [background:var(--surface-2)] text-text-mid"}`}
                    aria-pressed={filter === "holding"}
                    onClick={() => setFilter("holding")}
                  >
                    Đang giữ ({heldCount})
                  </button>
                  {/* No count on `Tất cả` — the universe size is. */}
                  <button
                    type="button"
                    className={`min-h-tap-min [padding:0_var(--space-4)] rounded-md text-t-sm font-weight-semi tabular-nums whitespace-nowrap cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--surface-hover)] hover:text-text hover:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:hover:[transform:none] ${filter === "all" ? "[border:1px_solid_var(--brand-accent)] [background:var(--tint)] text-text-hi" : "[border:1px_solid_var(--border)] [background:var(--surface-2)] text-text-mid"}`}
                    aria-pressed={filter === "all"}
                    onClick={() => setFilter("all")}
                  >
                    Tất cả
                  </button>
                </div>

                <div className="flex items-center gap-space-2 min-w-[0]">
                  <label htmlFor="my-cards-sort" className="text-t-micro text-text-dim whitespace-nowrap">
                    Sắp xếp
                  </label>
                  <select
                    id="my-cards-sort"
                    className="min-h-tap-min [padding:0_var(--space-3)] rounded-md [border:1px_solid_var(--border)] [background:var(--surface-2)] text-text text-t-sm font-weight-semi cursor-pointer [transition:background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--surface-hover)] hover:border-brand-accent focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none]"
                    value={sort}
                    onChange={(e) => setSort(e.target.value as Sort)}
                  >
                    {SORT_LABELS.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {cards.length === 0 ? (
                <EmptyHolding />
              ) : (
                <ul className="grid grid-cols-[repeat(auto-fill,minmax(140px,1fr))] gap-space-3 list-none m-[0] p-[0] min-w-[0] min-[900px]:grid-cols-[repeat(6,minmax(0,1fr))]">
                  {cards.map((c) => (
                    <CardTile
                      key={c.id}
                      card={c}
                      held={heldById.get(c.id)}
                      onOpen={setSelectedId}
                    />
                  ))}
                </ul>
              )}
            </>
          )}
        </div>
      )}

      {selected && (
        <CardDetail
          card={selected}
          held={heldById.get(selected.id)}
          onClose={closeDetail}
        />
      )}
    </div>
  );
}

/* ----------------------------------------------------------------------------
 * One tile. A card is an OBJECT here — it carries its own count and its own
 * membership, and it appears exactly once no matter how many sets claim it.
 * --------------------------------------------------------------------------*/

function CardTile({
  card,
  held,
  onOpen,
}: {
  card: DemoCard;
  held: HeldCard | undefined;
  onOpen: (id: string) => void;
}) {
  const sets = card.setIds.length;
  const count = held?.count ?? 0;

  return (
    <li className="min-w-[0]">
      <button
        type="button"
        className="block w-full p-[0] [border:0] [background:none] rounded-md cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard)] hover:[transform:scale(1.02)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:hover:[transform:none]"
        onClick={() => onOpen(card.id)}
        aria-label={accessibleName(card.name, count)}
      >
        {/* The art's own <svg aria-label> would double-announce the name under
            the button's label, so the whole visual is hidden from AT and the
            button's accessible name is the single source of truth. */}
        <span className="relative block" aria-hidden="true">
          <CardArt card={card} rare={card.tierId === "rare"} ghost={!held} />

          {/* Never `×0`, never `×1`. Top-LEFT, so it can never be read as a
              continuation of the `N bộ` badge in the opposite corner. */}
          {count >= 2 && <span className="absolute top-[4px] left-[4px] text-[10px] font-weight-bold tabular-nums tracking-[0.02em] [padding:2px_6px] rounded-pill [background:var(--surface-3)] text-text-hi [border:1px_solid_var(--border)]">×{count}</span>}

          {sets > 1 && <span className="absolute top-[4px] right-[4px] text-[10px] tracking-[0.04em] [padding:2px_5px] rounded-pill [background:var(--surface-3)] text-text-mid [border:1px_solid_var(--border)]">{sets} bộ</span>}
        </span>
      </button>
    </li>
  );
}

/**
 * The tile's accessible name. Ownership currently reads only through a CSS
 * grayscale filter, which is invisible to a screen reader — so state and count
 * travel in the name.
 */
function accessibleName(name: string, count: number): string {
  if (count === 0) return `${name} — chưa có`;
  if (count === 1) return `${name} — đang giữ`;
  return `${name} — đang giữ ${count} thẻ`;
}

/* ----------------------------------------------------------------------------
 * Zero cards held. One route out, and it is NOT a bet.
 * --------------------------------------------------------------------------*/

function EmptyHolding() {
  return (
    <div className="grid justify-items-center gap-space-2 text-center [padding:var(--space-6)_var(--space-4)] [border:1px_solid_var(--brand-accent-hairline)] rounded-lg [background:var(--surface)]">
      <h2 className="m-[0] text-t-h3 font-weight-semi text-text-hi">Chưa có thẻ nào</h2>
      <p className="m-[0] max-w-[40ch] text-t-sm text-text-mid leading-lh-body">
        Mỗi lượt mở luôn cho đúng một thẻ. Bạn nhận lượt mở từ cược thể thao đã
        kết toán.
      </p>
      {/* The only action. No "đặt cược ngay" — this surface does not induce. */}
      <Link href="/bo-suu-tap" className="inline-flex items-center justify-center min-h-tap-min mt-space-2 [padding:0_var(--space-4)] rounded-md [border:1px_solid_var(--brand-accent-hairline)] [background:var(--tint)] text-text-hi text-t-sm font-weight-semi no-underline [transition:transform_var(--dur-fast)_var(--ease-standard),background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--surface-hover)] hover:border-brand-accent hover:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:hover:[transform:none]">
        Về trang mở thẻ
      </Link>
    </div>
  );
}
