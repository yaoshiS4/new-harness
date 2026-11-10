/* ============================================================================
 * WalletBalanceHeader — VND balance hero (§wallet). The headline of
 * /vi-tien: a large balance figure, nothing more. Switching between Nạp / Rút /
 * Lịch sử / Chuyển quỹ is the WalletTabs strip's single job — the header used to
 * carry its own Nạp · Rút · Lịch sử chips, which triplicated those actions
 * alongside the tab strip and the member sidebar. Removed: ONE path per action.
 *
 * §F: the balance is a server-fetched `Envelope<LiveMoney>`. It
 * renders Skeleton while loading, ErrorState on failure (retry re-issues the
 * fetch), and is OMITTED-as-figure (honest "tạm chưa có số dư") when absent —
 * NEVER a fabricated/stale number presented as live. A client island so the
 * retry can re-issue the fetch.
 * ==========================================================================*/

"use client";

import { useRouter } from "next/navigation";
import type { Envelope, LiveMoney } from "@/lib/types";
import { vi } from "@/lib/i18n";
import { useRequireAuth } from "@/lib/auth";
import { Card, MoneyValue, Skeleton, ErrorState, Button } from "@/ui";

export interface WalletBalanceHeaderProps {
  balance: Envelope<LiveMoney>;
}

export function WalletBalanceHeader({ balance }: WalletBalanceHeaderProps) {
  const router = useRouter();
  const { allowed, promptAuth } = useRequireAuth();

  return (
    <Card variant="vip" className="flex flex-col gap-space-5 p-space-5">
      <div className="flex flex-col gap-space-2 min-w-[0]">
        <span className="text-t-sm text-text-mid font-weight-semi tracking-[0.02em]">{vi.wallet.balance}</span>

        {!allowed ? (
          // guest — honest prompt, never a fabricated balance
          <div className="flex flex-col items-start gap-space-3">
            <p className="text-t-sm text-text-mid">
              {vi.auth.login} để xem số dư của bạn.
            </p>
            <Button variant="primary" size="md" onClick={() => promptAuth()}>
              {vi.auth.login}
            </Button>
          </div>
        ) : balance.status === "loading" ? (
          // §F2 — Skeleton in the reserved footprint; never a "0" dressed as live
          <Skeleton width="11ch" height="1.2em" className="inline-block" />
        ) : balance.status === "error" ? (
          // §F3 — ErrorState + retry; never a stale number as live
          <ErrorState
            title="Không tải được số dư"
            onRetry={() => router.refresh()}
            className="items-start text-left"
          />
        ) : balance.status === "absent" ? (
          // §F1 — no real source: honest message, NOT a fabricated figure
          <p className="text-t-body text-text-mid">Tạm chưa có số dư.</p>
        ) : (
          // live — the real, server-issued figure (stale → "tạm dừng" via Money)
          <MoneyValue
            value={balance.value}
            kind="balance"
            size="num-lg"
            freshnessMs={balance.freshnessMs}
            className="text-text-hi"
          />
        )}
      </div>
    </Card>
  );
}
