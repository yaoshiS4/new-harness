/* ============================================================================
 * Yaobet — HOME / LOBBY (route "/").
 * ----------------------------------------------------------------------------
 * A Server Component: it fetches every dynamic surface server-side as typed §F
 * envelopes (jackpot, member-day, leaderboard, live-match, vip-progress,
 * balance) and the static fixtures (verticals, promos, games, providers, tiers),
 * then passes them as props to the band components — the SC-by-default seam that
 * makes the truthful-only rule structural (the client islands can only render a
 * number the server handed them; an absent surface self-omits, never fabricated).
 *
 * Bands compose in the authored order:
 *   hero carousel + promo chips → mobile round-icon launcher → auth/identity →
 *   live-games band (jackpot ticker + live-match) → provider tabs + game grid →
 *   sports/esports lifestyle + inline live-odds → footer.
 *   (The home composition has no VIP luxury aisle and no partner/provider
 *    band: VIP lives on its own route, and the ProviderGameGrid tab strip
 *    already lists the providers.)
 *   The desktop RightRail (≥1240) carries
 *   the member-day countdown + super-jackpot + opt-in leaderboard; below 1240 it
 *   is not rendered (those figures fold inline / live in their own bands).
 *
 * Auth-aware: guest vs member differences are resolved inside the client bands
 * via useAuth; gated game-tile launches call openAuthModal (the FTD seam entry).
 * A collapsed dev auth toggle is mounted top-left (dev-only) to QA each state.
 * ==========================================================================*/

import {
  getPromos,
  getVerticals,
  getJackpot,
  getMemberDayCountdown,
  getLeaderboard,
  getSportsMatches,
  getProviders,
  getGames,
} from "@/lib/mock";
import { RightRail } from "@/components/layout";
import {
  HeroBand,
  CategoryLauncher,
  StatsBar,
  ProviderGameGrid,
  SportsLifestyle,
  DevAuthToggle,
} from "@/components/home";

export default async function Home() {
  // Server-side truthful fetches (§F). The real-API swap replaces these bodies.
  const [
    promos,
    verticals,
    jackpot,
    memberDay,
    leaderboard,
    sportsMatches,
    providers,
    games,
  ] = await Promise.all([
    getPromos(),
    getVerticals(),
    getJackpot(),
    getMemberDayCountdown(),
    getLeaderboard(),
    getSportsMatches(),
    getProviders(),
    getGames(),
  ]);

  // No settled-stats feed exists at v1 → StatsBar receives `absent` and OMITS
  // the strip (truthful posture — never a fabricated social-proof figure).
  const stats = { status: "absent" } as const;

  return (
    <div className="home-page">
      <DevAuthToggle />

      <div className="home-main">
        {/* 1 — hero carousel (home main column: hero → game sections directly).
         *  Only promos carrying a real user banner JPG (/assets/banners/*) are
         *  hero slides — the token-slot promo cards (pr4-6) are NOT banner art and
         *  would render as blank placeholders in the full-bleed hero, so they are
         *  excluded here (truthful: a slide is JUST the self-contained banner). */}
        <HeroBand
          slides={promos.filter((p) => p.imageSrc.startsWith("/assets/banners/"))}
        />

        {/* 2 — mobile round-icon vertical launcher (desktop → CategoryRail) */}
        <CategoryLauncher verticals={verticals} />

        {/* 3 — settled social-proof (omitted unless a real feed exists) */}
        <StatsBar stats={stats} />

        {/* 4 — provider tab strip + game grid (image SLOTS, auth-gated launch) */}
        <ProviderGameGrid providers={providers} games={games} />

        {/* 5 — sports / esports lifestyle + one compact match card per sport */}
        <SportsLifestyle matches={sportsMatches} />
      </div>

      {/* desktop right rail (≥1240) — member-day + jackpot + leaderboard ONLY */}
      <RightRail memberDay={memberDay} jackpot={jackpot} leaderboard={leaderboard} />

      {/* The footer is the single app-wide footer, rendered by the root layout
       *  via AppShell's `footer` slot. The home page renders no footer of its
       *  own, so there is never a duplicate. */}
    </div>
  );
}
