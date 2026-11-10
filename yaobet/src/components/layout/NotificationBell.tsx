/* ============================================================================
 * NotificationBell — THE notification surface.
 * ----------------------------------------------------------------------------
 * The header bell is the product. /thong-bao, its list and its row are
 * deleted; this panel is the whole feature, so it carries the WHOLE feed and
 * scrolls rather than showing a slice behind a "see all" link.
 *
 * The row design is the owner's, approved as-is and NOT to be redesigned: a
 * coloured category icon, a title, a detail line, the relative time
 * ("18 phút trước"), an unread dot, and a left accent edge on unread rows.
 *
 * The row's kinds are the owner's eight types, not the legacy four
 * (promo · deposit · event · system): Balance Update (Deposit, Withdrawal) ·
 * Reward (Point, Money, Gift Code) · Announcement (New Event/Promotion/Mini
 * game, General) · Profile (Level up / Rank up). Eight glyphs, tinted by their
 * four categories. A failed deposit and a rejected withdrawal are those SAME
 * two types carrying a different status, never types of their own.
 *
 * There is no per-row "Đánh dấu đã đọc". Tapping the row marks it read,
 * and EVERY row does so — including one that leads nowhere, which used to be an
 * inert <div> with no handler at all. The panel-level "Đánh dấu đã đọc tất cả"
 * stays.
 *
 * One non-navigational control per row: DELETE. Permanent and immediate,
 * with no confirmation and no undo. Deleting an unread row drops the unread
 * count with it (the count is derived, so this cannot drift). The gap closes;
 * nothing reorders. Singular only — there is no delete-all here.
 *
 * ⚠ Every player-facing string comes from vi.notifications, and the eight
 *   types' wording is PLACEHOLDER copy awaiting the owner's final version.
 *
 * Read state and deletion are held locally (UI-only / mock — no BE write-back).
 * Esc + outside-click close; the panel is reduced-motion safe. Mirrors
 * MemberMenu's popover mechanics so the two header popovers behave identically.
 * ==========================================================================*/

"use client";

import Link from "next/link";
import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import { getNotificationBell } from "@/lib/mock";
import type {
  NotificationCategory,
  NotificationFeedItem,
  NotificationFeedType,
  NotificationSlots,
} from "@/lib/types";
import { vi } from "@/lib/i18n";
import { relativeTime } from "@/lib/format";
import { Icon, type IconName } from "@/ui/Icon/Icon";

const copy = vi.notifications.feed;

/* One glyph per TYPE (eight), drawn from the existing @/ui Icon set — own
 * inline SVGs, no icon library and no new network asset:
 *   deposit    → "deposit"  (arrow down into a line — money coming in)
 *   withdrawal → "wallet"   (the wallet the money leaves from)
 *   rewardPoint→ "chip"     (a token/point counter)
 *   rewardMoney→ "cashback" (money returning to the player)
 *   giftCode   → "gift"
 *   annEvent   → "promo"    (the promotion/event banner glyph)
 *   annGeneral → "info"
 *   levelUp    → "vip"                                                       */
const TYPE_ICON: Record<NotificationFeedType, IconName> = {
  deposit: "deposit",
  withdrawal: "wallet",
  rewardPoint: "chip",
  rewardMoney: "cashback",
  rewardGiftCode: "gift",
  announcementEvent: "promo",
  announcementGeneral: "info",
  profileLevelUp: "vip",
};

/* …and one TINT per CATEGORY (four), in the style the bell already used. The
 * tint groups; the glyph separates. Colour is never the only cue — the row
 * prints the type's name as its title. */
const CATEGORY_TINT: Record<NotificationCategory, string> = {
  balance: "shell-notification-bell-cat-balance",
  reward: "shell-notification-bell-cat-reward",
  announcement: "shell-notification-bell-cat-announcement",
  profile: "shell-notification-bell-cat-profile",
};

/** Fill the `{amount}` `{status}` `{name}` `{date}` `{level}` value slots. An
 *  absent slot collapses away rather than printing a raw `{token}`. */
function fillSlots(template: string, slots: NotificationSlots): string {
  const values: Record<string, string | undefined> = {
    amount: slots.amount,
    status: slots.status ? copy.status[slots.status] : undefined,
    name: slots.name,
    date: slots.date,
    level: slots.level,
  };
  return template
    .replace(/\{(\w+)\}/g, (_match, key: string) => values[key] ?? "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

/** The row's detail line, resolved from the item's type + its value slots. The
 *  stylesheet's two-line clamp is what stops a long one from growing the row. */
function detailOf(item: NotificationFeedItem): string {
  return fillSlots(copy.content[item.type], item.slots);
}

/** Where a tap leads: the CTA destination, else the plain URL, else nowhere —
 *  and "nowhere" is a real case, not a missing one. */
function destinationOf(item: NotificationFeedItem): string | null {
  return item.ctaHref ?? item.url ?? null;
}

function unreadLabel(count: number): string {
  if (count === 0) return vi.notifications.allRead;
  if (count === 1) return vi.notifications.unreadOne;
  return `${count} ${vi.notifications.unreadMany}`;
}

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationFeedItem[] | null>(null);
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);
  const panelId = useId();

  /* Delete removes the control the player is standing on, so keyboard focus
   * would fall to <body> and the panel would be lost. These two refs hand it to
   * the row that took the deleted one's place instead (or, when the last row
   * goes, to the panel itself). "" means "nothing left — focus the panel". */
  const delRefs = useRef(new Map<string, HTMLButtonElement | null>());
  const focusAfterDelete = useRef<string | null>(null);

  // mock fetch on mount (mimics the server data seam; replaced by real API).
  useEffect(() => {
    let alive = true;
    getNotificationBell().then((n) => {
      if (alive) setItems(n);
    });
    return () => {
      alive = false;
    };
  }, []);

  // outside-click + Esc close (mirrors MemberMenu).
  useEffect(() => {
    if (!open) return;
    function onDown(e: MouseEvent) {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  // place focus after a delete has re-rendered the list (see delRefs above).
  useEffect(() => {
    const target = focusAfterDelete.current;
    if (target === null) return;
    focusAfterDelete.current = null;
    const next = target ? delRefs.current.get(target) : null;
    if (next) next.focus();
    else panelRef.current?.focus();
  }, [items]);

  /* Derived, never stored: an unread count that is counted cannot disagree with
   * the list. Marking read and DELETING an unread row both drop it by one for
   * the same reason. */
  const unread = useMemo(
    () => (items ? items.filter((n) => !n.read).length : 0),
    [items],
  );

  const markRead = useCallback((id: string) => {
    setItems((prev) =>
      prev ? prev.map((n) => (n.id === id ? { ...n, read: true } : n)) : prev,
    );
  }, []);

  const markAllRead = () =>
    setItems((prev) => (prev ? prev.map((n) => ({ ...n, read: true })) : prev));

  /* Permanent and immediate. No dialog, no undo, one row at a time. */
  const remove = useCallback(
    (id: string) => {
      const list = items ?? [];
      const index = list.findIndex((n) => n.id === id);
      if (index === -1) return;
      const rest = list.filter((n) => n.id !== id);
      // the row that slides up into this slot, else the one above it, else none
      focusAfterDelete.current = rest[index]?.id ?? rest[rest.length - 1]?.id ?? "";
      delRefs.current.delete(id);
      setItems(rest);
    },
    [items],
  );

  const hasItems = !!items && items.length > 0;
  // badge caps at 9+ so a wide count never blows out the 72px tier-1 row.
  const badgeText = unread > 9 ? "9+" : String(unread);

  return (
    <div ref={wrapRef} className="shell-notification-bell">
      <button
        type="button"
        className={
          unread > 0
            ? "shell-notification-bell-bell-btn shell-notification-bell-bell-unread"
            : "shell-notification-bell-bell-btn"
        }
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={
          unread > 0
            ? `${vi.notifications.open} — ${unreadLabel(unread)}`
            : vi.notifications.open
        }
        onClick={() => setOpen((o) => !o)}
      >
        <span className="shell-notification-bell-bell-icon">
          <Icon name="message" size={24} />
        </span>
        {unread > 0 && (
          <span className="shell-notification-bell-badge" aria-hidden="true">
            {badgeText}
          </span>
        )}
      </button>

      {open && (
        <div
          id={panelId}
          ref={panelRef}
          tabIndex={-1}
          role="dialog"
          aria-label={vi.notifications.title}
          className="shell-notification-bell-panel"
        >
          <div className="shell-notification-bell-head">
            <span className="shell-notification-bell-head-title">{vi.notifications.title}</span>
            <span className="shell-notification-bell-head-meta">{unreadLabel(unread)}</span>
            {unread > 0 && (
              <button
                type="button"
                className="shell-notification-bell-mark-all"
                onClick={markAllRead}
              >
                {vi.notifications.markAllRead}
              </button>
            )}
          </div>

          {hasItems ? (
            <ul className="shell-notification-bell-list">
              {items.map((n) => {
                /* The type's name is the row's TITLE, so the icon beside it is
                   decorative — labelling it would say the same word twice. */
                const title = copy.typeName[n.type];
                const time = relativeTime(n.at);
                const destination = destinationOf(n);

                const row = (
                  <>
                    <span
                      className={`shell-notification-bell-row-icon ${CATEGORY_TINT[n.category]}`}
                    >
                      <Icon name={TYPE_ICON[n.type]} size={20} />
                    </span>
                    {/* The title, the unread dot and the time share ONE line —
                        the time used to sit on a line of its own above the
                        title, which read as two rows of heading. The title
                        takes the slack and ellipsizes; the dot and the time are
                        fixed, so a long title never pushes the time out. */}
                    <span className="shell-notification-bell-row-body">
                      <span className="shell-notification-bell-row-top">
                        <span className="shell-notification-bell-row-title">{title}</span>
                        {!n.read && (
                          <>
                            <span className="shell-notification-bell-unread-dot" aria-hidden="true" />
                            <span className="shell-notification-bell-sr-only">{copy.unreadMark}</span>
                          </>
                        )}
                        <span className="shell-notification-bell-row-time">{time}</span>
                      </span>
                      <span className="shell-notification-bell-row-detail">{detailOf(n)}</span>
                    </span>
                  </>
                );

                return (
                  <li
                    key={n.id}
                    className={
                      n.read
                        ? "shell-notification-bell-row-read"
                        : "shell-notification-bell-row-unread"
                    }
                  >
                    {/* A row that LEADS somewhere is a link; one that leads
                        nowhere is a BUTTON, not an inert <div>. Either way the
                        tap marks it read — that was the bug: a hrefless
                        row carried no handler and did nothing at all. */}
                    {destination ? (
                      <Link
                        href={destination}
                        className="shell-notification-bell-row"
                        onClick={() => {
                          markRead(n.id);
                          setOpen(false);
                        }}
                      >
                        {row}
                      </Link>
                    ) : (
                      <button
                        type="button"
                        className="shell-notification-bell-row shell-notification-bell-row-btn"
                        onClick={() => markRead(n.id)}
                      >
                        {row}
                      </button>
                    )}

                    {/* The row's ONE non-navigational control. It is a
                        SIBLING of the link, never a child: a control nested
                        inside a link is invalid markup and unreachable. Its
                        accessible name carries the notification's own title and
                        time, so "which one does this delete?" is answered
                        without sight of the row. */}
                    <button
                      type="button"
                      ref={(el) => {
                        delRefs.current.set(n.id, el);
                      }}
                      className="shell-notification-bell-row-delete"
                      aria-label={`${vi.notifications.deleteOne}: ${title} — ${time}`}
                      onClick={() => remove(n.id)}
                    >
                      {/* An X, not a bin: it sits on the title line as a
                          dismissal, and reads quieter than a bin glyph beside
                          eight category icons that are already pictorial. */}
                      <Icon name="close" size={16} />
                    </button>
                  </li>
                );
              })}
            </ul>
          ) : (
            <div className="shell-notification-bell-empty">
              <span className="shell-notification-bell-empty-icon" aria-hidden="true">
                <Icon name="message" size={28} />
              </span>
              <span className="shell-notification-bell-empty-title">{vi.notifications.empty}</span>
              <span className="shell-notification-bell-empty-hint">{vi.notifications.emptyHint}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
