/* ============================================================================
 * PageIntro — the h1 + a per-game lifted lead + the "how to read" line + a single
 * plain-language caveats paragraph (owner override, decisions/2026-08-11: the old
 * bordered "Cần biết" fence block is GONE — no box, no heading, no label-dash
 * grid, just muted sentences). The one inline link inside the caveats points at
 * the Game-hạn-chế tab of THIS page (/cuoc-hop-le?tab=han-che).
 * Server-safe, no props: reads the i18n catalog only. NO accordion, NO hero,
 * NO CTA, NO /vip link, NO percentage. The h1 reads the h1 type role (the
 * brand display face at the role size, 0 tracking).
 * ==========================================================================*/

import Link from "next/link";
import { vi } from "@/lib/i18n";

export function PageIntro() {
  /* The caveats paragraph carries ONE inline link: split its text around the
   * exact link phrase so the phrase renders as a next/link to the restricted tab.
   * If the phrase is ever absent, split returns the whole string as [before] and
   * the link simply does not render (graceful). */
  const [caveatsBefore, caveatsAfter = ""] = vi.contribution.caveats.split(
    vi.contribution.fencePromoLinkText,
  );
  const hasPromoLink =
    caveatsAfter !== "" || caveatsBefore !== vi.contribution.caveats;

  return (
    <header className="flex flex-col gap-space-2 min-w-[0]">
      <h1 className="type-h1 text-text-hi">{vi.contribution.title}</h1>
      <p className="text-text text-t-body leading-lh-body">{vi.contribution.lead}</p>
      <p className="text-text-mid text-t-sm leading-lh-body">{vi.contribution.howToRead}</p>

      <p className="mt-space-2 text-text-mid text-t-sm leading-lh-body min-w-[0]">
        {hasPromoLink ? (
          <>
            {caveatsBefore}
            <Link href="/cuoc-hop-le?tab=han-che" className="text-text-hi font-weight-semi [text-decoration:underline] underline-offset-[0.2em] rounded-sm hover:text-text-hi hover:[text-decoration:none] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2">
              {vi.contribution.fencePromoLinkText}
            </Link>
            {caveatsAfter}
          </>
        ) : (
          vi.contribution.caveats
        )}
      </p>
    </header>
  );
}
