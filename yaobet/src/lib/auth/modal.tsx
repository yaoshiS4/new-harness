/* ============================================================================
 * Yaobet — AuthModal provider + useAuthModal
 * ----------------------------------------------------------------------------
 * The openAuthModal API the shell/nav and FTD seam call. Carries the
 * resume-intent (e.g. {action:'deposit'}) so the guest→auth→deposit handoff is
 * driven by ONE mechanism. This provider owns ONLY the
 * open/close + intent state; the AuthModal *content* (a lazy Dialog/Sheet) is
 * built separately and reads this context. No modal farm is pre-rendered.
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
import type { ResumeIntent } from "../types";

export type AuthModalMode = "login" | "register" | "forgot";

interface AuthModalState {
  open: boolean;
  mode: AuthModalMode;
  resumeIntent: ResumeIntent;
}

interface AuthModalContextValue extends AuthModalState {
  /** open the auth modal in a mode, optionally carrying a resume-intent. */
  openAuthModal: (opts?: {
    mode?: AuthModalMode;
    resumeIntent?: ResumeIntent;
  }) => void;
  closeAuthModal: () => void;
  /** consume + clear the resume-intent (the deposit handoff reads this). */
  consumeResumeIntent: () => ResumeIntent;
}

const NO_INTENT: ResumeIntent = { action: "none" };

const AuthModalContext = createContext<AuthModalContextValue | null>(null);

export function AuthModalProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthModalState>({
    open: false,
    mode: "login",
    resumeIntent: NO_INTENT,
  });

  const openAuthModal = useCallback<AuthModalContextValue["openAuthModal"]>(
    (opts) => {
      setState({
        open: true,
        mode: opts?.mode ?? "login",
        resumeIntent: opts?.resumeIntent ?? NO_INTENT,
      });
    },
    [],
  );

  const closeAuthModal = useCallback(() => {
    setState((prev) => ({ ...prev, open: false }));
  }, []);

  const consumeResumeIntent = useCallback<
    AuthModalContextValue["consumeResumeIntent"]
  >(() => {
    let intent = NO_INTENT;
    setState((prev) => {
      intent = prev.resumeIntent;
      return { ...prev, resumeIntent: NO_INTENT };
    });
    return intent;
  }, []);

  const value = useMemo<AuthModalContextValue>(
    () => ({ ...state, openAuthModal, closeAuthModal, consumeResumeIntent }),
    [state, openAuthModal, closeAuthModal, consumeResumeIntent],
  );

  return (
    <AuthModalContext.Provider value={value}>
      {children}
    </AuthModalContext.Provider>
  );
}

export function useAuthModal(): AuthModalContextValue {
  const ctx = useContext(AuthModalContext);
  if (!ctx) {
    throw new Error("useAuthModal must be used within <AuthModalProvider>");
  }
  return ctx;
}
