/* ============================================================================
 * ContributionTabs — the client wrapper that turns /cuoc-hop-le into a two-tab
 * surface: "Tỷ lệ tính cược" (the per-game rate table) and "Game hạn chế" (the
 * bonus-restricted list). It reuses the accessible ui/Tabs strip and renders ONE
 * active panel. The panels themselves (intro + island) are built by the SERVER
 * page and handed in as props, so BOTH datasets are server-fetched and the RSC
 * payload carries both panels — switching tabs streams no new data.
 *
 * URL is the source of truth (deep-linkable + SSR/JS-off friendly): the active
 * tab is DERIVED from the `?tab=` query (`han-che` = restricted; absent/anything
 * else = rate). No local mirror state — deriving in render keeps the tab honest
 * for every URL change: a tab click, the promo next/link, the footer link, and
 * browser back/forward all flow through the same query. The server page reads the
 * SAME param and SSR-renders the matching panel, so /cuoc-hop-le?tab=han-che
 * shows the restricted list even with JS disabled. `initialTab` is the server
 * seed used until the URL query is present (the clean /cuoc-hop-le default).
 *
 * On a tab click we sync the query via router.replace (scroll preserved) — a
 * shallow soft update, no full reload; useSearchParams then re-derives `active`.
 * ==========================================================================*/

"use client";

import { type ReactNode } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Tabs } from "@/ui";
import { vi } from "@/lib/i18n";

export type ContributionTab = "ty-le" | "han-che";

/** Only "han-che" opens the restricted list; anything else (incl. absent) = rate. */
function toTab(value: string | null | undefined): ContributionTab {
  return value === "han-che" ? "han-che" : "ty-le";
}

export function ContributionTabs({
  initialTab,
  ratePanel,
  restrictedPanel,
}: {
  initialTab: ContributionTab;
  ratePanel: ReactNode;
  restrictedPanel: ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Derive from the URL. On first paint the query already matches `initialTab`
  // (dynamic route), so hydration is clean; when the query key is absent the
  // server seed (`initialTab`) stands in for the clean /cuoc-hop-le default.
  const active: ContributionTab = toTab(searchParams.get("tab") ?? initialTab);

  const onChange = (id: string) => {
    const next = toTab(id);
    if (next === active) return;
    // Shallow query sync — a soft update, no full reload; useSearchParams then
    // re-derives `active`. We always write an explicit tab so returning to the
    // rate tab is unambiguous (never falls back to a stale seed).
    router.replace(`${pathname}?tab=${next}`, { scroll: false });
  };

  const items = [
    { id: "ty-le", label: vi.contribution.tabRate },
    { id: "han-che", label: vi.contribution.tabRestricted },
  ];

  return (
    <div className="flex flex-col gap-space-5 min-w-[0]">
      <Tabs
        items={items}
        active={active}
        onChange={onChange}
        label={vi.contribution.tabsLabel}
      />

      {active === "han-che" ? (
        <div
          role="tabpanel"
          id="panel-han-che"
          aria-labelledby="tab-han-che"
          className="flex flex-col gap-space-5 min-w-[0]"
        >
          {restrictedPanel}
        </div>
      ) : (
        <div
          role="tabpanel"
          id="panel-ty-le"
          aria-labelledby="tab-ty-le"
          className="flex flex-col gap-space-5 min-w-[0]"
        >
          {ratePanel}
        </div>
      )}
    </div>
  );
}
