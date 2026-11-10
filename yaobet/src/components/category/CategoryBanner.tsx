/* ============================================================================
 * CategoryBanner — the vertical landing hero (home banner + asset-slot rule).
 * A token-derived gradient SLOT (no reference-site art) carrying the
 * vertical label + a short plain-VN kicker. The banner is static navigation
 * furniture — it hosts no live figure, so it has no loading/error state of its
 * own (the page's dynamic surfaces own those).
 *
 * The vertical icon resolves from the inline icon sprite; verticals whose
 * fixture iconId has no glyph yet fall back to a safe sprite icon (never a
 * broken/empty glyph, never a network icon-font request).
 * ==========================================================================*/

import type { Vertical } from "@/lib/types";
import { Icon, type IconName } from "@/ui";

export interface CategoryBannerProps {
  vertical: Vertical;
}

/** Plain-VN one-line kicker per vertical (marketing copy, never a number). */
const KICKERS: Record<string, string> = {
  casino: "Sòng bài trực tiếp đẳng cấp",
  slots: "Quay là trúng, nổ hũ mỗi ngày",
  sports: "Kèo bóng đá & thể thao trực tiếp",
  fishing: "Săn cá thưởng lớn",
  card: "Game bài dân gian quen thuộc",
  lottery: "Xổ số & lô đề đa dạng",
  cockfight: "Trường gà trực tiếp",
  table: "Bàn chơi cổ điển",
  arcade: "Game nhanh giải trí tức thì",
};

/** iconId → sprite glyph, with a safe fallback for not-yet-drawn verticals. */
function resolveIcon(iconId: string): IconName {
  const known: Record<string, IconName> = {
    casino: "card",
    slots: "slots",
    sports: "sports",
    fishing: "live",
    card: "card",
    lottery: "grid",
    cockfight: "trophy",
    table: "grid",
    arcade: "slots",
  };
  return known[iconId] ?? "grid";
}

export function CategoryBanner({ vertical }: CategoryBannerProps) {
  return (
    <section
      className="vertical-category-banner-banner"
      data-vertical={vertical.id}
      aria-label={vertical.label}
    >
      {/* token-derived gradient SLOT — awaiting final art */}
      <span className="vertical-category-banner-slot" aria-hidden="true" />
      <div className="vertical-category-banner-content">
        <span className="vertical-category-banner-icon-wrap" aria-hidden="true">
          <Icon name={resolveIcon(vertical.iconId)} size={28} />
        </span>
        <h1 className="vertical-category-banner-title">{vertical.label}</h1>
        {KICKERS[vertical.id] && (
          <p className="vertical-category-banner-kicker">{KICKERS[vertical.id]}</p>
        )}
      </div>
    </section>
  );
}
