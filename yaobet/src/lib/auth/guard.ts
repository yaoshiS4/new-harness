/* ============================================================================
 * Yaobet — route guard / view-state helpers (lib/auth/guard)
 * ----------------------------------------------------------------------------
 * "logged-out vs level-0 vs tiered" helpers. (member) routes use useRequireAuth
 * to decide between an honest logged-out prompt + auth trigger vs rendering
 * member data. Member-only data shows honest empty-states, never fabricated
 * activity.
 * ==========================================================================*/

"use client";

import { useAuth } from "./session";
import { useAuthModal } from "./modal";
import type { AuthState, ResumeIntent } from "../types";

export interface RequireAuthResult {
  authState: AuthState;
  /** true when a member (level-0 or tiered) — gated content may render. */
  allowed: boolean;
  /** call to surface the auth modal (optionally carrying a resume-intent). */
  promptAuth: (resumeIntent?: ResumeIntent) => void;
}

/**
 * Guard hook for (member) surfaces. Does NOT redirect (UI-only/mock) — it
 * returns `allowed=false` for guests so the page can render an honest
 * logged-out prompt wired to `promptAuth`.
 */
export function useRequireAuth(): RequireAuthResult {
  const { authState, isAuthenticated } = useAuth();
  const { openAuthModal } = useAuthModal();

  return {
    authState,
    allowed: isAuthenticated,
    promptAuth: (resumeIntent?: ResumeIntent) =>
      openAuthModal({ mode: "login", resumeIntent }),
  };
}

/** Coarse view-state predicates for conditional rendering. */
export function isGuest(state: AuthState): boolean {
  return state === "guest";
}
export function isLevelZero(state: AuthState): boolean {
  return state === "level-0";
}
export function isTiered(state: AuthState): boolean {
  return state === "tiered";
}
