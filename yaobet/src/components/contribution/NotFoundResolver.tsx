/* ============================================================================
 * NotFoundResolver — the only screen that must NOT read as "excluded".
 * It renders ABOVE the table so the reader is never left
 * holding a negation with nothing beside it. It leads positive (the subject is
 * OUR matching, no negation), then
 * resolves to an action: all EIGHT categories as tappable chips in lobby order,
 * WRAPPED (never a horizontal scroller — a scroller hides members of a list that
 * must be complete), then a tip, then a help link to /tro-giup.
 *
 * NO chip carries a percentage (the rate lives only in the table). The
 * banned "games not in the list count 100%" banner appears in no wording. There
 * is no position:fixed / visualViewport machinery — keyboard occlusion is solved
 * by placement (the field scrolls to top, the chips sit directly beneath).
 * The title reads the h4 type role (body face): it heads this block one step
 * under the page h1. The block is one surface step in the page column, a
 * sibling of the table frame, never nested in a card.
 * ==========================================================================*/

import Link from "next/link";
import { Pill } from "@/ui/Pill/Pill";
import { Icon } from "@/ui/Icon/Icon";
import { vi } from "@/lib/i18n";

export function NotFoundResolver({
  categories,
  onPick,
}: {
  /** all 8 categories in lobby order — {id, name}; NO rate is passed in */
  categories: { id: string; name: string }[];
  /** apply a category as the filter (and clear the search) */
  onPick: (id: string) => void;
}) {
  return (
    <section className="flex flex-col gap-space-3 [background:var(--surface-2)] [border:1px_solid_var(--border)] rounded-md p-space-4" aria-label={vi.contribution.notFoundTitle}>
      <p className="type-h4 text-text-hi">{vi.contribution.notFoundTitle}</p>
      <p className="text-text text-t-body leading-lh-body">{vi.contribution.notFoundResolve}</p>

      <div className="flex flex-wrap gap-space-2">
        {categories.map((cat) => (
          <Pill key={cat.id} onClick={() => onPick(cat.id)}>
            {cat.name}
          </Pill>
        ))}
      </div>

      <p className="text-text-mid text-t-sm leading-lh-body">{vi.contribution.notFoundTip}</p>
      <Link href="/tro-giup" className="inline-flex items-center gap-space-1 self-start min-h-tap-min text-text-mid text-t-sm [text-decoration:none] hover:text-text-hi focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2">
        <span>{vi.contribution.notFoundHelp}</span>
        <Icon name="chevronRight" aria-hidden />
      </Link>
    </section>
  );
}
