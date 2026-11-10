/* ============================================================================
 * Yaobet — COLLECTION ports harness (demonstrable proxy).
 * ----------------------------------------------------------------------------
 * Calls all eleven interfaces and renders, for each, which of the four
 * envelope states came back. This is the story's acceptance evidence: the seam
 * exists, it is exercisable, and the loading and error paths are visible
 * before any real surface consumes them.
 *
 * It also proves two acceptance conditions:
 *   · a loading state is visible for at least the configured delay
 *   · a double-submitted mutation is rejected once and succeeds once
 *
 * THROWAWAY. Deleted when lands. Dev-only route, not linked from
 * anywhere in the product.
 * ==========================================================================*/

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { Envelope } from "@/lib/types";
import { FixtureCollectionAdapters } from "@/lib/collection/adapters/fixtures";

type StateName = "live" | "loading" | "error" | "absent";

interface Probe {
  port: string;
  state: StateName;
  detail: string;
}

const PLAYER = "demo-player";

const PORT_NAMES = [
  "activity",
  "entitlement",
  "outcome",
  "wallet",
  "risk",
  "rg",
  "catalogue",
  "state",
  "clock",
  "audit",
  "holdout",
] as const;

export default function CollectionPortsHarness() {
  const adapters = useMemo(() => new FixtureCollectionAdapters("demo-a"), []);
  const ports = useMemo(() => adapters.toPorts(), [adapters]);

  const [probes, setProbes] = useState<Probe[]>(() =>
    PORT_NAMES.map((port) => ({ port, state: "loading" as StateName, detail: "…" })),
  );
  const [dupeLog, setDupeLog] = useState<string[]>([]);

  const runAll = useCallback(async () => {
    // Yield before the first setState so the initial probe does not cascade
    // renders synchronously inside the mount effect.
    await Promise.resolve();
    setProbes(
      PORT_NAMES.map((port) => ({ port, state: "loading" as StateName, detail: "…" })),
    );

    const settle = (port: string, state: StateName, detail: string) =>
      setProbes((prev) =>
        prev.map((p) => (p.port === port ? { port, state, detail } : p)),
      );

    const readInto = async <T,>(port: string, run: () => Promise<Envelope<T>>) => {
      const env = await run();
      settle(port, env.status, describe(env));
    };

    await Promise.all([
      readInto("activity", () => ports.activity.getPosition(PLAYER)),
      readInto("entitlement", () => ports.entitlement.list(PLAYER)),
      readInto("risk", () => ports.risk.check(PLAYER)),
      readInto("rg", () => ports.rg.renderVerdict(PLAYER)),
      readInto("catalogue", () => ports.catalogue.getCatalogue()),
      readInto("state", () => ports.state.get(PLAYER)),
      readInto("audit", () => ports.audit.trace(PLAYER)),
      readInto("holdout", () => ports.holdout.isHeldOut(PLAYER)),
      (async () => {
        const r = await ports.outcome.draw(PLAYER, "none", "probe-outcome");
        settle(
          "outcome",
          r.status === "rejected" ? "absent" : "live",
          r.status === "rejected" ? r.reason : "drew",
        );
      })(),
      (async () => {
        const r = await ports.wallet.credit(
          PLAYER,
          "probe-set",
          "cash-like",
          `probe-wallet-${Date.now()}`,
        );
        settle(
          "wallet",
          r.status === "rejected" ? "error" : "live",
          r.status === "rejected" ? r.reason : `txn ${r.value.transactionId}`,
        );
      })(),
      (async () => {
        settle("clock", "live", `${ports.clock.now()} · ${ports.clock.timezone()}`);
      })(),
    ]);
  }, [ports]);

  useEffect(() => {
    // The rule guards against cascading renders from synchronous setState in
    // an effect. `runAll` awaits before its first setState, so this is a
    // one-shot probe on mount, not a render loop — and probing on open is the
    // whole point of a harness page.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void runAll();
  }, [runAll]);

  /* the same key twice: applied once, duplicate once. */
  const testIdempotency = useCallback(async () => {
    const key = `dup-test-${Date.now()}`;
    setDupeLog(["submitting the same key twice…"]);
    const [a, b] = await Promise.all([
      ports.state.setPriorityOrder(PLAYER, ["s1", "s2"], key),
      ports.state.setPriorityOrder(PLAYER, ["s1", "s2"], key),
    ]);
    setDupeLog([`first  → ${a.status}`, `second → ${b.status}`]);
  }, [ports]);

  const fire = useCallback(() => {
    adapters.fireActivity(1);
    adapters.mintEarnedOpens();
    void runAll();
  }, [adapters, runAll]);

  const reset = useCallback(() => {
    adapters.resetDemo();
    setDupeLog([]);
    void runAll();
  }, [adapters, runAll]);

  return (
    <main className="p-space-4 max-w-[900px] [margin:0_auto] text-text">
      <header className="[border-bottom:1px_solid_var(--border)] pb-space-3 mb-space-4">
        <h1 className="font-brand-font-body text-t-h2 font-weight-bold leading-lh-tight text-text-hi [margin:0_0_var(--space-2)]">Collection ports — harness</h1>
        <p className="text-t-sm text-text-mid leading-lh-body m-[0]">
          GC-101 proxy. Eleven ports, four envelope states. Fixtures inject
          latency and seeded failure by default, so loading and error paths are
          visible here before any surface consumes them. Catalogue and outcome
          refuse on purpose — they are blocked on BR-03, BR-04 and BR-05.
        </p>
      </header>

      <div className="flex flex-wrap gap-space-2 mb-space-4">
        <button type="button" className="min-h-tap-min [padding:0_var(--space-3)] [border:1px_solid_var(--border)] rounded-md [background:var(--surface-2)] text-text text-t-sm cursor-pointer hover:[background:var(--surface-hover)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px]" onClick={() => void runAll()}>
          Re-probe all 11
        </button>
        <button type="button" className="min-h-tap-min [padding:0_var(--space-3)] [border:1px_solid_var(--border)] rounded-md [background:var(--surface-2)] text-text text-t-sm cursor-pointer hover:[background:var(--surface-hover)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px]" onClick={fire}>
          Fire simulated activity
        </button>
        <button type="button" className="min-h-tap-min [padding:0_var(--space-3)] [border:1px_solid_var(--border)] rounded-md [background:var(--surface-2)] text-text text-t-sm cursor-pointer hover:[background:var(--surface-hover)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px]" onClick={() => void testIdempotency()}>
          Double-submit one key
        </button>
        <button
          type="button"
          className="min-h-tap-min [padding:0_var(--space-3)] [border:1px_solid_var(--border)] rounded-md [background:var(--surface-2)] text-text text-t-sm cursor-pointer hover:[background:var(--surface-hover)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px]"
          onClick={() => {
            adapters.clock.shift(24 * 60 * 60 * 1000);
            void runAll();
          }}
        >
          Clock +1 day
        </button>
        <button type="button" className="min-h-tap-min [padding:0_var(--space-3)] [border:1px_solid_var(--border)] rounded-md [background:var(--surface-2)] text-text text-t-sm cursor-pointer hover:[background:var(--surface-hover)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px]" onClick={reset}>
          Reset demo account
        </button>
      </div>

      {dupeLog.length > 0 && (
        <div className="grid grid-cols-[1fr_auto] gap-space-3 items-center p-space-3 [border:1px_solid_var(--border)] rounded-md [background:var(--surface)]">
          <div className="flex flex-col gap-[2px] min-w-[0]">
            <span className="text-t-body text-text-hi font-weight-semi">Idempotency</span>
            <span className="text-t-micro text-text-dim leading-lh-body [word-break:break-word]">{dupeLog.join("  ·  ")}</span>
          </div>
        </div>
      )}

      <div className="grid gap-space-2">
        {probes.map((p) => (
          <div key={p.port} className="grid grid-cols-[1fr_auto] gap-space-3 items-center p-space-3 [border:1px_solid_var(--border)] rounded-md [background:var(--surface)]">
            <div className="flex flex-col gap-[2px] min-w-[0]">
              <span className="text-t-body text-text-hi font-weight-semi">{p.port}</span>
              <span className="text-t-micro text-text-dim leading-lh-body [word-break:break-word]">{p.detail}</span>
            </div>
            <span className={`text-t-micro font-weight-semi tracking-[0.06em] uppercase [padding:4px_var(--space-2)] rounded-pill [border:1px_solid_var(--border)] whitespace-nowrap ${{ live: "text-win", loading: "text-text-dim", error: "text-error", absent: "text-caution" }[p.state]}`}>{p.state}</span>
          </div>
        ))}
      </div>
    </main>
  );
}

function describe<T>(env: Envelope<T>): string {
  if (env.status === "live") return preview(env.value);
  if (env.status === "error") return "error envelope — retryable";
  if (env.status === "absent") return "no real source — surface omits";
  return "…";
}

function preview(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (Array.isArray(value)) return `${value.length} item(s)`;
  if (typeof value === "object") {
    const json = JSON.stringify(value);
    return json.length > 140 ? `${json.slice(0, 140)}…` : json;
  }
  return String(value);
}
