/* ============================================================================
 * AppShell — the build-once chrome wrapper. A Server
 * Component: it fetches the truthful shell data server-side (verticals, the
 * member balance envelope) and passes them as typed props to the ShellChrome
 * client island — the SC-by-default seam that makes the dynamic-data contract
 * structural (the client cannot fabricate a number it was never handed).
 *
 * Chrome renders ONCE; the content column (children) swaps without re-rendering
 * the shell (App-Router nested layouts). The desktop RightRail is a slot the
 * host route can fill (home only at v1); Footer + SupportWidget are owned by
 * their own agents and composed by the root layout below
 * AppShell, or passed via `footer`.
 *
 * Usage (root layout):
 *   <AppShell footer={<Footer/>}>{children}</AppShell>
 * A route that wants the desktop right rail passes it explicitly:
 *   <AppShell rightRail={<RightRail .../>}>{page}</AppShell>
 * ==========================================================================*/

import type { ReactNode } from "react";
import { getVerticals, getBalance } from "@/lib/mock";
import { ShellChrome } from "./ShellChrome";

export interface AppShellProps {
  children: ReactNode;
  /** desktop right rail (≥1240) — typically only the home route fills it. */
  rightRail?: ReactNode;
  /** Footer slot — owned by the footer agent. */
  footer?: ReactNode;
}

export async function AppShell({ children, rightRail, footer }: AppShellProps) {
  // server fetches — typed truthful envelopes. The real-API swap replaces
  // these bodies, not the call sites.
  const [verticals, balance] = await Promise.all([getVerticals(), getBalance()]);

  return (
    <ShellChrome
      verticals={verticals}
      balance={balance}
      rightRail={rightRail}
      footer={footer}
    >
      {children}
    </ShellChrome>
  );
}
