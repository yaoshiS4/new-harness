/* ============================================================================
 * verticalIcon — map a Vertical.iconId (from the lib/mock lobby fixture) to its
 * distinct Icon-sprite glyph. The fixture's 9-vertical taxonomy is
 * now matched 1:1 to a dedicated inline-SVG glyph in ui/Icon — one per gaming
 * vertical, matching the reference's iconographic category nav: casino chip, slot machine,
 * football, fish, cards, lottery ticket, rooster, game table, lightning (fast
 * games). Defaults to `grid` for any unknown id. Type-safe against IconName.
 * ==========================================================================*/

import type { IconName } from "@/ui/Icon/Icon";

const MAP: Record<string, IconName> = {
  casino: "chip",
  slots: "slots",
  sports: "sports",
  fishing: "fish",
  card: "card",
  lottery: "ticket",
  cockfight: "rooster",
  table: "table",
  arcade: "fast",
};

export function verticalIcon(iconId: string): IconName {
  return MAP[iconId] ?? "grid";
}
