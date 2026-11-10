/* ============================================================================
 * WalletHistory — transaction history rows (§records RecordsList /
 * §wallet) [RG]. A compact recent-activity list for /vi-tien.
 *
 * EQUAL win/loss salience: every signed figure uses DeltaAmount (sign + the
 * luminance-matched pair, loss never dimmer). To make the brief's "hue carries
 * ZERO info" concrete, each row ALSO shows a direction arrow (↑/↓) + a plain
 * Vietnamese type word — so a colour-blind user reads the in/out direction from
 * the sign, arrow and word, not from colour. A type/scope filter is provided;
 * empty + filtered-empty render the honest EmptyState primitive.
 *
 * Auth-aware: a guest sees a prompt instead of fabricated history.
 * ==========================================================================*/

"use client";

import { useState } from "react";
import type { Transaction, TransactionType } from "@/lib/types";
import { vi } from "@/lib/i18n";
import { useRequireAuth } from "@/lib/auth";
import { Card, DeltaAmount, EmptyState, Tabs, Button } from "@/ui";

export interface WalletHistoryProps {
  records: Transaction[];
  /** show all rows; default trims to a recent slice for the wallet surface. */
  limit?: number;
}

/** plain-VN type word per transaction type (read alongside sign + arrow). */
const TYPE_WORD: Record<TransactionType, string> = {
  deposit: "Nạp tiền",
  withdraw: "Rút tiền",
  win: "Thắng",
  loss: "Thua",
  transfer: "Chuyển quỹ",
  cashback: "Hoàn trả",
};

type Scope = "all" | "in" | "out";

const SCOPES: { id: Scope; label: string }[] = [
  { id: "all", label: "Tất cả" },
  { id: "in", label: "Tiền vào" },
  { id: "out", label: "Tiền ra" },
];

function formatWhen(iso: string): string {
  return new Date(iso).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function WalletHistory({ records, limit = 6 }: WalletHistoryProps) {
  const { allowed, promptAuth } = useRequireAuth();
  const [scope, setScope] = useState<Scope>("all");

  const filtered = records.filter((r) => {
    if (scope === "in") return r.amount.amount >= 0;
    if (scope === "out") return r.amount.amount < 0;
    return true;
  });
  const shown = filtered.slice(0, limit);

  return (
    <Card variant="default" className="flex flex-col gap-space-4 p-space-4">
      <div className="flex items-center justify-between">
        <h2 className="text-t-h3 text-text-hi font-weight-semi">{vi.wallet.history}</h2>
      </div>

      {!allowed ? (
        <div className="flex flex-col items-start gap-space-3">
          <p className="text-t-sm text-text-mid">{vi.auth.login} để xem lịch sử giao dịch.</p>
          <Button variant="primary" size="sm" onClick={() => promptAuth()}>
            {vi.auth.login}
          </Button>
        </div>
      ) : (
        <>
          <Tabs
            items={SCOPES.map((s) => ({ id: s.id, label: s.label }))}
            active={scope}
            onChange={(id) => setScope(id as Scope)}
            label="Lọc giao dịch"
          />

          {records.length === 0 ? (
            <EmptyState
              icon="history"
              title="Chưa có giao dịch"
              message="Các giao dịch nạp, rút và cược của bạn sẽ hiển thị tại đây."
            />
          ) : shown.length === 0 ? (
            <EmptyState
              variant="filtered"
              icon="history"
              message="Không có giao dịch khớp với bộ lọc."
              onReset={() => setScope("all")}
            />
          ) : (
            <ul className="flex flex-col gap-space-1 list-none m-[0] p-[0]">
              {shown.map((tx) => {
                const isIn = tx.amount.amount >= 0;
                return (
                  <li key={tx.id} className="flex items-center justify-between gap-space-3 py-space-3 px-[0] border-b border-b-border min-h-tap-min last:[border-bottom:0]">
                    <div className="flex flex-col gap-space-1 min-w-[0]">
                      <span className="inline-flex items-center gap-space-2 text-t-body text-text-hi font-weight-semi">
                        <span className="text-t-sm text-text-mid font-weight-bold" aria-hidden="true">
                          {isIn ? "↑" : "↓"}
                        </span>
                        {TYPE_WORD[tx.type]}
                      </span>
                      <span className="text-t-micro text-text-mid font-brand-font-num">{formatWhen(tx.at)}</span>
                    </div>
                    <DeltaAmount value={tx.amount} className="shrink-0" />
                  </li>
                );
              })}
            </ul>
          )}
        </>
      )}
    </Card>
  );
}
