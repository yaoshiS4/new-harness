/* ============================================================================
 * category/data — per-vertical resolver for the category/vertical landing
 * (home game-grid + [vertical] route). It COMPOSES the shared,
 * forbidden-to-edit mock accessors (getVerticals / getProviders / getGames /
 * getLiveMatch from "@/lib/mock") into the shape the category page needs —
 * resolving the vertical from the slug and shaping a truthful payload.
 *
 * Truthful-only: the live-odds board is bound to the same
 * Envelope<LiveMatch> the home LiveMatchCard uses (loading→Skeleton,
 * error/absent→omitted, stale→"tạm dừng"). No fabricated game counts; an empty
 * provider filter yields an honest EmptyState in the component, not filler.
 * ==========================================================================*/

import {
  getVerticals,
  getProviders,
  getGames,
  getLiveMatch,
} from "@/lib/mock";
import type {
  Envelope,
  GameTile,
  LiveMatch,
  Provider,
  Vertical,
} from "@/lib/types";

/** Verticals that render an inline live-odds board (sports + esports sub-tab). */
export const ODDS_VERTICALS = new Set(["sports"]);

export interface CategoryPayload {
  vertical: Vertical;
  providers: Provider[];
  games: GameTile[];
  /** present only for odds-bearing verticals; else null (board not rendered) */
  odds: Envelope<LiveMatch> | null;
}

/**
 * Resolve the vertical from a route slug. Returns `null` for an unknown slug so
 * the page calls notFound(). The slug is the Vertical.id (Yaobet IA taxonomy)
 * — the canonical list is sourced from the Yaobet vertical fixture, never a
 * reference-site category set.
 */
export async function resolveVertical(slug: string): Promise<Vertical | null> {
  const verticals = await getVerticals();
  return verticals.find((v) => v.id === slug) ?? null;
}

/** Fetch everything the category landing needs for a resolved vertical. */
export async function getCategoryPayload(
  vertical: Vertical,
): Promise<CategoryPayload> {
  const wantsOdds = ODDS_VERTICALS.has(vertical.id);
  const [providers, games, odds] = await Promise.all([
    getProviders(),
    getGames(),
    wantsOdds ? getLiveMatch() : Promise.resolve(null),
  ]);
  return { vertical, providers, games, odds };
}
