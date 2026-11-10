/* ============================================================================
 * Yaobet — MockAuthProvider + useAuth (lib/auth/session)
 * ----------------------------------------------------------------------------
 * Mock session context with the three view-states (guest / level-0 / tiered).
 * Login/logout are mock toggles; no real credentials, tokens or network. The
 * contract is shaped (signIn/signOut/useAuth) so a real auth provider drops in
 * behind it unchanged.
 * ==========================================================================*/

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { AuthState, Session, User } from "../types";
import { SESSIONS } from "./fixtures";

interface AuthContextValue {
  session: Session;
  user: User | null;
  authState: AuthState;
  isAuthenticated: boolean;
  /** mock sign-in: flips to a chosen view-state (default tiered). */
  signIn: (as?: Exclude<AuthState, "guest">) => void;
  signOut: () => void;
  /** dev toggle — cycle guest → level-0 → tiered → guest. */
  cycleDevState: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function MockAuthProvider({
  children,
  initialState = "guest",
}: {
  children: ReactNode;
  initialState?: AuthState;
}) {
  const [state, setState] = useState<AuthState>(initialState);

  const signIn = useCallback((as: Exclude<AuthState, "guest"> = "tiered") => {
    setState(as);
  }, []);

  const signOut = useCallback(() => setState("guest"), []);

  const cycleDevState = useCallback(() => {
    setState((prev) =>
      prev === "guest" ? "level-0" : prev === "level-0" ? "tiered" : "guest",
    );
  }, []);

  const value = useMemo<AuthContextValue>(() => {
    const session = SESSIONS[state];
    return {
      session,
      user: session.user,
      authState: state,
      isAuthenticated: state !== "guest",
      signIn,
      signOut,
      cycleDevState,
    };
  }, [state, signIn, signOut, cycleDevState]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within <MockAuthProvider>");
  }
  return ctx;
}
