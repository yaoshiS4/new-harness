/* ============================================================================
 * Yaobet — MY-CARDS COMPOSITION ROOT.
 * ----------------------------------------------------------------------------
 * The one place adapters are constructed for this route. Everything below this
 * line receives the `CollectionPorts` declaration and nothing else — enforced
 * by lint, which bans adapter imports from components/collection/**.
 *
 * ⛔ THIS ROOT DOES NOT SEED, AND MUST NOT.
 *
 * Store state is persisted per account key in localStorage, so it is SHARED
 * across routes. `CollectionRoot` seeds the demo (`fireActivity` +
 * `mintEarnedOpens`) on mount; if this root seeded too, every
 * /bo-suu-tap → /cua-toi → back round trip would grant free opens and the
 * inventory would quietly disagree with the rails about how the player got
 * there. Seeding is the collection route's job (guarded there). This
 * route is a READER: it constructs the adapters against the same account key
 * and reads what is already stored.
 *
 * A player who lands here first therefore sees the honest empty state — which
 * is the correct answer, not a bug: they hold no cards.
 *
 * Swapping fixtures for HTTP adapters is a change to this file alone.
 * ==========================================================================*/

"use client";

import { useMemo } from "react";
import { FixtureCollectionAdapters } from "@/lib/collection/adapters/fixtures";
import { MyCards } from "@/components/collection/MyCards";

export function MyCardsRoot() {
  const ports = useMemo(() => {
    const a = new FixtureCollectionAdapters("demo-a", {
      // Same account key as the collection route — one store, two surfaces.
      // Latency stays honest so the loading branch is a path we have seen;
      // failure injection is exercised on the ports harness instead.
      latencyMs: 220,
      readFailureRate: 0,
      writeFailureRate: 0,
    });
    // No fireActivity, no mintEarnedOpens, no resetDemo. See the header.
    return a.toPorts();
  }, []);

  return <MyCards ports={ports} />;
}
