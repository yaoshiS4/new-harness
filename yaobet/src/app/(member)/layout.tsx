/* ============================================================================
 * Yaobet — (member) ROUTE GROUP layout.
 * ----------------------------------------------------------------------------
 * The (member) group composes the desktop two-column member area ONCE around
 * every member surface (profile.html .user_info_box | content split):
 *
 *     ┌──────────────┬──────────────────────────────┐
 *     │ MemberSidebar│  children (page content col)  │
 *     │  (304px rail)│  /tai-khoan → SecurityCenter  │
 *     │  identity    │  /vi-tien   → WalletSurface   │
 *     │  balance     │                               │
 *     │  points/rebate                               │
 *     │  icon-grid   │                               │
 *     └──────────────┴──────────────────────────────┘
 *
 * The sidebar is hosted HERE so /tai-khoan AND /vi-tien (the wallet agent's
 * surface) share it without re-mounting it — chrome renders once, the content
 * column swaps (App-Router nested layouts).
 *
 * This is a Server Component: it fetches the live balance envelope (§F) and the
 * account summary server-side and hands them to the MemberSidebar client island
 * — the truthful seam (the island cannot fabricate a figure it never receives).
 * Mobile-first @375: the rail stacks ABOVE the content; ≥992 it becomes a fixed
 * 304px sticky left column.
 * ==========================================================================*/

import type { ReactNode } from "react";
import { getBalance, getAccountSummary, getVipProgress } from "@/lib/mock";
import { MemberSidebar } from "@/components/account";

export default async function MemberLayout({
  children,
}: {
  children: ReactNode;
}) {
  // server fetches — typed truthful envelope (§F) + fixture. The real-API swap
  // replaces these bodies, not the call sites. getVipProgress() backs the
  // membership progress bar in the rail's fused hero card; it is an §F Envelope
  // so the bar renders a live track ONLY when status==='live' (absent/loading →
  // an honest "đang cập nhật", never a fabricated fill).
  const [balance, summary, progress] = await Promise.all([
    getBalance(),
    getAccountSummary(),
    getVipProgress(),
  ]);

  return (
    <div className="flex flex-col gap-space-4 min-w-[0] [background:var(--page-bloom)] min-[992px]:flex-row min-[992px]:items-start min-[992px]:gap-gap">
      <MemberSidebar balance={balance} summary={summary} progress={progress} />
      <div className="block min-w-[0] [background:var(--member-canvas)] min-[992px]:[flex:1_1_0]">{children}</div>
    </div>
  );
}
