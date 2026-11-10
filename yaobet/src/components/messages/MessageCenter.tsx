/* ============================================================================
 * MessageCenter — the "/tin-nhan" inbox island (消息中心 / Message Center).
 * ----------------------------------------------------------------------------
 * The right content column of the (member) area: an outer Card panel with a
 * header row (accent message glyph + "Tin nhắn" + unread-count subtitle on the
 * left; a mark-all-read pill + delete-all pill + a filter Dropdown pinned
 * right) over a hairline-divided list of message rows. "Tin nhắn" is the
 * page h1 (the route renders no other).
 *
 * State model mirrors the header NotificationBell EXACTLY: the list + the
 * read/deleted state are CLIENT-only local React state (UI-only / mock — there
 * is NO BE write-back). The server hands the seed in via `initial`; this island
 * renders only what it was given and never fabricates a message or a count.
 *
 * Truthful-only, three honest states:
 *   • guest    → an honest login prompt (the rail shows its own guest prompt);
 *   • empty    → EmptyState 'default' (natural / DEMO_EMPTY / after delete-all);
 *   • filtered → EmptyState 'filtered' with a reset (filter excludes all but
 *                items still exist).
 *
 * Reduced-motion safe; every interactive target is ≥ --tap-min.
 * ==========================================================================*/

"use client";

import { useMemo, useState } from "react";
import type { Message } from "@/lib/types";
import { vi } from "@/lib/i18n";
import { relativeTime } from "@/lib/format";
import { useRequireAuth } from "@/lib/auth";
import { Card, Button, Dropdown, EmptyState, Icon } from "@/ui";

type Filter = "all" | "unread" | "read";

const FILTER_LABEL: Record<Filter, string> = {
  all: vi.messages.filterAll,
  unread: vi.messages.filterUnread,
  read: vi.messages.filterRead,
};

const FILTER_ORDER: readonly Filter[] = ["all", "unread", "read"] as const;

export interface MessageCenterProps {
  initial: Message[];
}

export function MessageCenter({ initial }: MessageCenterProps) {
  const { allowed, promptAuth } = useRequireAuth();
  const [items, setItems] = useState<Message[]>(initial);
  const [filter, setFilter] = useState<Filter>("all");

  const unread = useMemo(() => items.filter((m) => !m.read).length, [items]);

  const filtered = useMemo(() => {
    if (filter === "unread") return items.filter((m) => !m.read);
    if (filter === "read") return items.filter((m) => m.read);
    return items;
  }, [items, filter]);

  const markRead = (id: string) =>
    setItems((prev) =>
      prev.map((m) => (m.id === id ? { ...m, read: true } : m)),
    );
  const markAllRead = () =>
    setItems((prev) => prev.map((m) => ({ ...m, read: true })));
  const deleteAll = () => setItems([]);

  const subtitle =
    unread > 0
      ? `${unread} ${vi.messages.subtitleUnread}`
      : vi.messages.subtitleAllRead;

  /* ----- header (always rendered for the member/empty/filtered states) ----- */
  // The filter + bulk actions are only meaningful when there is something to
  // act on, so they are suppressed in the zero-items state (and for guests).
  const hasItems = items.length > 0;
  const header = (
    <div className="flex items-center justify-between gap-space-3 flex-wrap">
      <div className="flex items-start gap-space-2 min-w-[0]">
        <Icon name="message" size={24} className="text-brand-accent-fg flex-[0_0_auto] mt-[2px]" />
        <div className="flex flex-col gap-space-1 min-w-[0]">
          <h1 className="promo-type-h1 text-text-hi">{vi.messages.title}</h1>
          <span className="text-t-sm text-text-mid">{subtitle}</span>
        </div>
      </div>

      {hasItems && (
        <div className="inline-flex items-center gap-space-2 ml-auto flex-wrap">
          {unread > 0 && (
            <Button
              variant="ghost"
              size="sm"
              icon="check"
              className="text-brand-accent-fg"
              onClick={markAllRead}
            >
              {vi.notifications.markAllRead}
            </Button>
          )}
          <Button
            variant="destructive"
            size="sm"
            icon="close"
            onClick={deleteAll}
          >
            {vi.messages.deleteAll}
          </Button>
          <Dropdown
            label={vi.messages.filterLabel}
            placement="bottom-end"
            trigger={
              <button type="button" className="inline-flex items-center gap-space-1 min-h-tap-min py-[0] px-space-3 [background:var(--surface-2)] border border-border rounded-pill text-text-hi text-t-sm font-weight-semi cursor-pointer [transition:background_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),transform_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--surface-hover)] hover:border-brand-accent-hairline hover:[transform:scale(1.05)] [&_svg]:[transition:transform_var(--dur-fast)_var(--ease-standard)] hover:[&_svg]:[transform:scale(1.1)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px] motion-reduce:[transition:none] motion-reduce:[&_svg]:[transition:none] motion-reduce:hover:[transform:none] motion-reduce:hover:[&_svg]:[transform:none]">
                <span>{FILTER_LABEL[filter]}</span>
                <Icon name="chevronDown" size={16} aria-hidden="true" />
              </button>
            }
          >
            <ul className="list-none m-[0] p-[0] flex flex-col gap-space-1">
              {FILTER_ORDER.map((value) => (
                <li key={value}>
                  <button
                    type="button"
                    role="menuitem"
                    aria-current={filter === value || undefined}
                    className={
                      filter === value
                        ? "block w-full min-h-tap-min py-space-2 px-space-3 text-left [background:transparent] [border:0] rounded-md text-t-sm cursor-pointer hover:[background:var(--tint)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[-2px] text-brand-accent-fg font-weight-semi"
                        : "block w-full min-h-tap-min py-space-2 px-space-3 text-left [background:transparent] [border:0] rounded-md text-text text-t-sm cursor-pointer hover:[background:var(--tint)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[-2px]"
                    }
                    onClick={() => setFilter(value)}
                  >
                    {FILTER_LABEL[value]}
                  </button>
                </li>
              ))}
            </ul>
          </Dropdown>
        </div>
      )}
    </div>
  );

  /* ----- body — exactly one honest branch ----- */
  let body: React.ReactNode;
  if (!allowed) {
    // GUEST: never a message list — an honest login invite.
    body = (
      <EmptyState
        icon="message"
        title={vi.messages.guestPrompt}
        message={
          <Button variant="primary" size="sm" onClick={() => promptAuth()}>
            {vi.auth.login}
          </Button>
        }
      />
    );
  } else if (!hasItems) {
    // No data (natural / DEMO_EMPTY / after delete-all).
    body = (
      <EmptyState
        icon="message"
        title={vi.messages.empty}
        message={vi.messages.emptyHint}
      />
    );
  } else if (filtered.length === 0) {
    // Items exist but the active filter excludes them all.
    body = (
      <EmptyState variant="filtered" onReset={() => setFilter("all")} />
    );
  } else {
    body = (
      <ul className="list-none m-[0] p-[0] flex flex-col">
        {filtered.map((m) => (
          <MessageItem key={m.id} message={m} onRead={markRead} />
        ))}
      </ul>
    );
  }

  return (
    <Card variant="default" className="flex flex-col gap-space-5 p-card-pad">
      {header}
      {body}
    </Card>
  );
}

/* ----------------------------------------------------------------------------
 * One message row: rows are split by the hairline inside the panel, never
 * boxed as cards of their own. An UNREAD row is a button on the --surface-2
 * step (clicking it marks it read — the dot + step + accent edge drop and the
 * subject de-emphasizes). A READ row has no action, so it is a plain
 * non-interactive container.
 * --------------------------------------------------------------------------*/
function MessageItem({
  message,
  onRead,
}: {
  message: Message;
  onRead: (id: string) => void;
}) {
  const { id, subject, body, read, at } = message;

  const inner = (
    <>
      <div className="flex items-center gap-space-2">
        <span
          className={
            read
              ? "text-t-body font-weight-reg text-text leading-lh-tight min-w-[0]"
              : "text-t-body font-weight-semi text-text-hi leading-lh-tight min-w-[0]"
          }
        >
          {subject}
        </span>
        <span className="ml-auto text-t-micro text-text-mid whitespace-nowrap flex-none">{relativeTime(at)}</span>
        {!read && <span className="flex-none w-[8px] h-[8px] rounded-pill [background:var(--brand-accent)]" aria-hidden="true" />}
      </div>
      <p className="text-t-sm text-text-mid leading-lh-tight">{body}</p>
    </>
  );

  if (read) {
    return (
      <li className="relative border-b border-b-border last:[border-bottom:0]">
        <div className="flex flex-col gap-space-1 w-full min-h-tap-min p-card-pad-sm">{inner}</div>
      </li>
    );
  }

  return (
    <li className="relative [background:var(--surface-2)] border-b border-b-border last:[border-bottom:0] member-message-center-item-unread">
      <button
        type="button"
        className="flex flex-col gap-space-1 w-full min-h-tap-min p-card-pad-sm [background:transparent] [border:0] text-left [font:inherit] [color:inherit] cursor-pointer [transition:background_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--surface-hover)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[-2px] motion-reduce:[transition:none]"
        aria-label={`${vi.notifications.markRead}: ${subject}`}
        onClick={() => onRead(id)}
      >
        {inner}
      </button>
    </li>
  );
}
