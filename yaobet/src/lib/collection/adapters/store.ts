/* ============================================================================
 * Yaobet — COLLECTION persistence.
 * ----------------------------------------------------------------------------
 * Items, shards, opens, set progress and pity position survive a reload and a
 * browser restart. Without this, everything about this feature is unstorable:
 * the only persistence in the application today is one session-storage key for
 * a dismissal, so a stakeholder who closes the tab loses their collection and
 * the demo reads as a prototype rather than a product.
 *
 * Namespaced per demo account so two seeded accounts can be shown side by side
 * — which is how the suppressed, holdout and blocked paths get demonstrated
 * next to a normal one.
 *
 * SSR-safe: this runs inside an App Router app, so every access is guarded.
 * On the server the store is an in-memory shim and reads return the seed.
 * ==========================================================================*/

import type { CollectionState } from "../types";

const NAMESPACE = "yaobet.collection.v1";

const memory = new Map<string, string>();

function hasWindow(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function keyFor(accountId: string): string {
  return `${NAMESPACE}.${accountId}`;
}

/** The known seed a demo reset returns to. Empty, not fabricated progress. */
export function seedState(): CollectionState {
  return {
    heldCards: [],
    progress: [],
    shards: { pooled: 0, locked: {} },
    entitlements: [],
    pityPosition: 0,
    priorityOrder: [],
    earmarkSetId: null,
    audit: [],
    auditSeq: 0,
  };
}

/**
 * The record is capped so one browser cannot grow the blob without bound. The
 * cap is generous, and the UI pages at 50, so a player never reaches it in a
 * session — but a stored array with no ceiling is the defect that only ever
 * appears on the heaviest accounts, which is the worst place to find it.
 */
const AUDIT_CAP = 500;

export function capAudit(state: CollectionState): CollectionState {
  return state.audit.length <= AUDIT_CAP
    ? state
    : { ...state, audit: state.audit.slice(0, AUDIT_CAP) };
}

export class CollectionStore {
  private accountId: string;

  constructor(accountId: string) {
    this.accountId = accountId;
  }

  /** Switch the account view without a login. */
  setAccount(accountId: string): void {
    this.accountId = accountId;
  }

  getAccount(): string {
    return this.accountId;
  }

  read(): CollectionState {
    const key = keyFor(this.accountId);
    const raw = hasWindow() ? window.localStorage.getItem(key) : memory.get(key);
    if (!raw) return seedState();
    try {
      /* Merged over the seed, not cast onto it. A blob written before a field
         existed is otherwise missing that field at runtime while the type says
         it is present — `audit` was added after accounts already had state, and
         `state.audit.slice()` on such a blob throws. */
      return { ...seedState(), ...(JSON.parse(raw) as Partial<CollectionState>) };
    } catch {
      // A corrupt blob is a demo-reset condition, never a crash.
      return seedState();
    }
  }

  write(state: CollectionState): void {
    const key = keyFor(this.accountId);
    const raw = JSON.stringify(state);
    if (hasWindow()) window.localStorage.setItem(key, raw);
    else memory.set(key, raw);
  }

  /** Read, transform, persist — the only mutation path. */
  update(fn: (prev: CollectionState) => CollectionState): CollectionState {
    const next = fn(this.read());
    this.write(next);
    return next;
  }

  /** The single dev action that returns this account to the known seed. */
  reset(): CollectionState {
    const seed = seedState();
    this.write(seed);
    return seed;
  }

  /** Every demo account this browser has state for — powers side-by-side. */
  static listAccounts(): string[] {
    if (!hasWindow()) return [...memory.keys()].map(stripNamespace);
    const out: string[] = [];
    for (let i = 0; i < window.localStorage.length; i += 1) {
      const k = window.localStorage.key(i);
      if (k && k.startsWith(`${NAMESPACE}.`)) out.push(stripNamespace(k));
    }
    return out;
  }
}

function stripNamespace(key: string): string {
  return key.slice(NAMESPACE.length + 1);
}
