/* ============================================================================
 * Yaobet — collection COMPOSITION ROOT.
 * ----------------------------------------------------------------------------
 * The one place adapters are constructed. Everything below this line receives
 * the `CollectionPorts` declaration and nothing else — enforced by lint, which
 * bans adapter imports from components/collection/**.
 *
 * Swapping fixtures for HTTP adapters is a change to this file alone.
 * ==========================================================================*/

"use client";

import { useCallback, useMemo, useState } from "react";
import { FixtureCollectionAdapters } from "@/lib/collection/adapters/fixtures";
import { CollectionApp } from "@/components/collection/CollectionApp";
import { DEMO_SETS } from "@/lib/collection/fixtures/epl";

/** Opens the demo account starts with. Configuration, not an economy figure. */
const SEED_OPENS = 3;

export function CollectionRoot() {
  const adapters = useMemo(() => {
    const a = new FixtureCollectionAdapters("demo-a", {
      // The demo keeps latency honest but does not fail the happy path on
      // camera — failure injection is exercised on the ports harness instead.
      latencyMs: 220,
      readFailureRate: 0,
      writeFailureRate: 0,
    });
    // Seed a few opens so the surface is not empty on first paint — GUARDED.
    // Collection state is persisted per account and shared across routes, so a
    // seed that ran on every mount would make navigating away and back a way
    // to earn. `ensureSeeded` is a no-op against a store that has been played.
    a.ensureSeeded(SEED_OPENS);
    return a;
  }, []);

  const [nonce, setNonce] = useState(0);
  const ports = useMemo(() => adapters.toPorts(), [adapters]);

  const fire = useCallback(() => {
    adapters.fireActivity(1);
    adapters.mintEarnedOpens();
    setNonce((n) => n + 1);
  }, [adapters]);

  const reset = useCallback(() => {
    adapters.resetDemo();
    adapters.ensureSeeded(SEED_OPENS);
    setNonce((n) => n + 1);
  }, [adapters]);

  /* Completes the smallest set that is not ALREADY FULL, so repeated presses
     walk the catalogue. Sets are repeatable, so a set that has been exchanged
     before is a valid target again — it is empty now. */
  const completeSet = useCallback(() => {
    const progress = adapters.store.read().progress;
    const target =
      [...DEMO_SETS]
        .sort((a, b) => a.size - b.size)
        .find((s) => !progress.find((p) => p.setId === s.id)?.complete) ??
      DEMO_SETS[0];
    adapters.completeSet(target.id);
    setNonce((n) => n + 1);
  }, [adapters]);

  return (
    <CollectionApp
      key={nonce}
      ports={ports}
      onFireActivity={fire}
      onCompleteSet={completeSet}
      onReset={reset}
    />
  );
}
