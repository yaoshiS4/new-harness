/* ============================================================================
 * Yaobet — client provider tree
 * ----------------------------------------------------------------------------
 * Mounts the MockAuthProvider + AuthModalProvider (the openAuthModal API) at
 * the client boundary so the rest of the tree (server components included)
 * renders beneath one client island root. The AuthModal *content* and the
 * Toast host are composed by the shell agent inside <AppShell> — this file
 * owns only the context providers.
 * ==========================================================================*/

"use client";

import type { ReactNode } from "react";
import { MockAuthProvider } from "@/lib/auth/session";
import { AuthModalProvider } from "@/lib/auth/modal";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <MockAuthProvider initialState="tiered">
      <AuthModalProvider>{children}</AuthModalProvider>
    </MockAuthProvider>
  );
}
