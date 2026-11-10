/* ============================================================================
 * /cuoc-hop-le — the public game surface, now ONE page with TWO tabs (owner
 * merge 2026-08-11):
 *   · "Tỷ lệ tính cược" (default) — the per-game contribution rate table.
 *   · "Game hạn chế"              — the bonus-restricted games list (merged in
 *                                   from the old standalone /game-han-che).
 * ----------------------------------------------------------------------------
 * A Server Component, SSR — it renders the ACTIVE tab's panel as real markup that
 * works with JavaScript disabled. No login, no auth branch, no personalisation:
 * a guest and a member receive byte-identical HTML (no useAuth / tier branch
 * anywhere in this feature). No promo, no CTA, no /vip link, no đồng figure.
 *
 * Deep-linkable + JS-off friendly: the active tab follows `?tab=` (`han-che` =
 * restricted; absent/anything else = rate). This page reads searchParams, fetches
 * BOTH datasets, resolves `initialTab`, and hands both fully-built panels to the
 * ContributionTabs client wrapper — which SSR-renders ONLY the active panel, so
 * /cuoc-hop-le?tab=han-che shows the restricted list even with JS off. The two
 * islands (ContributionRoot, RestrictedRoot) never fetch; they consume payloads.
 * ==========================================================================*/

import {
  getContributionCatalogue,
  getContributionRates,
  getRestrictedGames,
} from "@/lib/mock";
import {
  ContributionRoot,
  ContributionTabs,
  PageIntro,
  type ContributionTab,
} from "@/components/contribution";
import { RestrictedIntro, RestrictedRoot } from "@/components/restricted";

export const metadata = {
  title: "Tỷ lệ tính cược theo trò chơi — Yaobet",
};

/** Format an ISO instant to the minute (DD/MM/YYYY HH:mm) using UTC getters so
 *  the stamp is deterministic regardless of the runtime timezone. */
function formatStamp(iso: string): string {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${pad(d.getUTCDate())}/${pad(d.getUTCMonth() + 1)}/${d.getUTCFullYear()} ` +
    `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`
  );
}

export default async function ContributionRatePage({
  searchParams,
}: {
  searchParams: Promise<{ tab?: string | string[] }>;
}) {
  const sp = await searchParams;
  const tabParam = Array.isArray(sp.tab) ? sp.tab[0] : sp.tab;
  const initialTab: ContributionTab = tabParam === "han-che" ? "han-che" : "ty-le";

  // BOTH payloads load here regardless of the active tab, so the RSC payload
  // carries both panels and a client tab switch is instant (no refetch). Each
  // island consumes its payload; neither fetches.
  const [rates, catalogue, restricted] = await Promise.all([
    getContributionRates(),
    getContributionCatalogue(),
    getRestrictedGames(),
  ]);

  const rateStamp = formatStamp(rates.effectiveAt);
  const restrictedStamp = formatStamp(restricted.effectiveAt);

  return (
    <div className="[background:var(--canvas)] flex flex-col gap-space-5 min-w-[0] pb-[calc(var(--bottombar-h)+env(safe-area-inset-bottom)+var(--space-5))] min-[768px]:pb-space-6">
      <ContributionTabs
        initialTab={initialTab}
        ratePanel={
          <>
            <PageIntro />
            <ContributionRoot
              rates={rates}
              catalogue={catalogue}
              stampDate={rateStamp}
              version={rates.version}
            />
          </>
        }
        restrictedPanel={
          <>
            <RestrictedIntro />
            <RestrictedRoot
              list={restricted}
              stampDate={restrictedStamp}
              version={restricted.version}
            />
          </>
        }
      />
    </div>
  );
}
