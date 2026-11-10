/* ============================================================================
 * CategoryLauncher — mobile round-icon vertical launcher (inline
 * presentation). The primary MOBILE category entry on Home: a round-icon grid
 * (Ø64 target + plain-VN label), one tap per vertical. Hidden ≥768 where the
 * desktop CategoryRail (Tier-2) takes over.
 *
 * Verticals are public game categories — NOT auth-gated; tapping routes to the
 * vertical. The same content also drives the pinned `Danh mục` CategorySheet in
 * the shell chrome — this is the inline twin.
 * ==========================================================================*/

import Link from "next/link";
import type { Vertical } from "@/lib/types";
import { vi } from "@/lib/i18n";
import { Icon } from "@/ui";
import { verticalIcon } from "@/components/layout/_internal/verticalIcon";

export interface CategoryLauncherProps {
  verticals: Vertical[];
}

export function CategoryLauncher({ verticals }: CategoryLauncherProps) {
  if (verticals.length === 0) return null;

  return (
    <nav className="home-category-launcher-launcher" aria-label={vi.nav.categories}>
      <ul className="home-category-launcher-grid">
        {verticals.map((v) => (
          <li key={v.id}>
            <Link href={v.href} className="home-category-launcher-item">
              <span className="home-category-launcher-icon-wrap" aria-hidden>
                <Icon name={verticalIcon(v.iconId)} size={26} />
              </span>
              <span className="home-category-launcher-label">{v.label}</span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
