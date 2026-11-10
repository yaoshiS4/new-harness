/* ============================================================================
 * RestrictedIntro — the h1 + lead + the load-bearing "Lưu ý" note for the
 * bonus-restricted games list (/game-han-che). Sibling of the contribution
 * PageIntro but there is NO "Cần biết" fence block and NO rate copy — this page
 * publishes ONE list, not a rate table.
 *
 * The note is critical: it states the list applies ONLY inside a
 * promotion and that the games are otherwise played normally (it prevents the
 * "I can never play these" misread). Server-safe, no props: reads i18n only. The
 * h1 reads the h1 type role (the brand display face at the role size, 0
 * tracking). The note is one surface step in the page column, never a card
 * inside another card.
 * ==========================================================================*/

import { vi } from "@/lib/i18n";

export function RestrictedIntro() {
  return (
    <header className="flex flex-col gap-space-2 min-w-[0]">
      <h1 className="type-h1 text-text-hi">{vi.restricted.title}</h1>
      <p className="text-text text-t-body leading-lh-body">{vi.restricted.lead}</p>

      <p className="mt-space-2 p-space-3 [background:var(--surface-2)] [border:1px_solid_var(--border)] rounded-md text-text-mid text-t-sm leading-lh-body min-w-[0]">
        <b className="text-text-hi font-brand-font-body font-weight-semi">{vi.restricted.noteLabel}</b>
        {" — "}
        {vi.restricted.note}
      </p>
    </header>
  );
}
