/* ============================================================================
 * CategorySheet — the mobile category spine. A round-icon
 * grid of the verticals presented in the Overlay sheet. Opened from the
 * persistent `Danh mục` trigger in the sticky chrome on EVERY mobile page AND
 * from a `Trang chủ`-tap-when-already-home — so any vertical is reachable in
 * ≤1 tap from anywhere on mobile, WITHOUT scrolling a page to its top or
 * routing through Home. Focus-trapped, swipe-down/Esc/scrim dismiss (Overlay).
 * ==========================================================================*/

"use client";

import Link from "next/link";
import { useId } from "react";
import type { Vertical } from "@/lib/types";
import { vi } from "@/lib/i18n";
import { Icon } from "@/ui/Icon/Icon";
import { Overlay } from "./_internal/Overlay";
import { verticalIcon } from "./_internal/verticalIcon";

export interface CategorySheetProps {
  open: boolean;
  onClose: () => void;
  verticals: Vertical[];
}

export function CategorySheet({ open, onClose, verticals }: CategorySheetProps) {
  const titleId = useId();
  return (
    <Overlay open={open} onClose={onClose} presentation="sheet" labelledBy={titleId}>
      <div className="shell-category-sheet">
        <h2 id={titleId} className="shell-category-sheet-title">
          {vi.nav.categories}
        </h2>
        <ul className="shell-category-sheet-grid">
          {verticals.map((v) => (
            <li key={v.id}>
              <Link href={v.href} className="shell-category-sheet-tile" onClick={onClose}>
                <span className="shell-category-sheet-icon-circle" aria-hidden="true">
                  <Icon name={verticalIcon(v.iconId)} size={28} />
                </span>
                <span className="shell-category-sheet-label">{v.label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </Overlay>
  );
}
