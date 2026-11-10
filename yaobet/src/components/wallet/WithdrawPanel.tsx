/* ============================================================================
 * WithdrawPanel — VND withdrawal request (§wallet). The Rút
 * surface the chip routes to. Amount field (inputMode=numeric) bound to the
 * available balance, a server-reflected payout destination (read-only — the user
 * does not set it here), and a request submit that stops at an honest PENDING /
 * awaiting-confirmation state.
 *
 * A withdrawal is never client-confirmed "thành công"; it stops at
 * "đang chờ xử lý". The available balance is the server figure passed in — it is
 * never fabricated, and an over-balance request is blocked. Auth-aware.
 * ==========================================================================*/

"use client";

import { useState } from "react";
import type { MoneyValue as MoneyVal } from "@/lib/types";
import { vi } from "@/lib/i18n";
import { useRequireAuth } from "@/lib/auth";
import { formatVnd } from "@/lib/format";
import { Card, Button, Icon, MoneyValue } from "@/ui";

export interface WithdrawPanelProps {
  /** available balance (server figure) — the request ceiling. Null = unknown. */
  available: MoneyVal | null;
  /** server-reflected payout destination (read-only here). */
  destination: { bank: string; account: string } | null;
}

type Phase = "idle" | "pending";

export function WithdrawPanel({ available, destination }: WithdrawPanelProps) {
  const { allowed, promptAuth } = useRequireAuth();
  const [amount, setAmount] = useState<number | null>(null);
  const [amountText, setAmountText] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");

  const max = available?.amount ?? 0;
  const overBalance = amount != null && amount > max;
  const canSubmit = amount != null && amount > 0 && !overBalance;

  const onAmountChange = (raw: string) => {
    const digits = raw.replace(/\D/g, "");
    setAmountText(digits ? formatVnd(Number(digits)) : "");
    setAmount(digits ? Number(digits) : null);
  };

  const submit = () => {
    if (!allowed) {
      promptAuth({ action: "withdraw" });
      return;
    }
    if (!canSubmit) return;
    setPhase("pending");
  };

  if (!allowed) {
    return (
      <Card variant="default" className="flex flex-col gap-space-4 p-space-4">
        <h2 className="text-t-h3 text-text-hi font-weight-semi">{vi.wallet.withdraw}</h2>
        <div className="flex flex-col items-start gap-space-3">
          <p className="text-t-sm text-text-mid">{vi.auth.login} để rút tiền.</p>
          <Button variant="primary" size="md" onClick={() => promptAuth({ action: "withdraw" })}>
            {vi.auth.login}
          </Button>
        </div>
      </Card>
    );
  }

  if (phase === "pending") {
    return (
      <Card variant="default" className="flex flex-col gap-space-4 p-space-4">
        <h2 className="text-t-h3 text-text-hi font-weight-semi">{vi.wallet.withdraw}</h2>
        <div className="flex flex-col items-center text-center gap-space-3 py-space-5 px-space-3" role="status">
          <span className="inline-flex items-center justify-center w-[56px] h-[56px] rounded-pill [background:var(--surface-3)] text-text" aria-hidden="true">
            <Icon name="history" size={28} />
          </span>
          <p className="text-t-h2 text-text-hi font-weight-semi">Đang chờ xử lý</p>
          <p className="text-t-sm text-text-mid leading-lh-body max-w-[36ch]">
            Yêu cầu rút tiền đã được ghi nhận và đang chờ hệ thống xử lý. Bạn sẽ
            nhận được thông báo khi hoàn tất.
          </p>
          <Button variant="ghost" size="md" onClick={() => setPhase("idle")}>
            Quay lại
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card variant="default" className="flex flex-col gap-space-4 p-space-4">
      <h2 className="text-t-h3 text-text-hi font-weight-semi">{vi.wallet.withdraw}</h2>

      <p className="text-t-sm text-text-mid inline-flex gap-space-1 items-baseline">
        Số dư khả dụng:{" "}
        {available ? (
          <MoneyValue value={available} className="text-text-hi font-weight-semi" />
        ) : (
          <span className="text-text-hi font-weight-semi">—</span>
        )}
      </p>

      <div className="flex flex-col gap-space-2">
        <label className="text-t-sm text-input-label font-weight-semi" htmlFor="withdraw-amount">
          Số tiền rút
        </label>
        <input
          id="withdraw-amount"
          className="w-full min-h-tap-min py-space-3 px-space-4 font-brand-font-num text-t-h3 text-input-text [background:var(--surface-2)] border [border-color:var(--line-default)] rounded-md placeholder:text-input-helper focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 focus-visible:border-focus-ring aria-[invalid=true]:border-(--error)"
          inputMode="numeric"
          autoComplete="off"
          placeholder="0 ₫"
          value={amountText}
          onChange={(e) => onAmountChange(e.target.value)}
          aria-invalid={overBalance || undefined}
        />
        {overBalance && (
          <p className="text-t-micro text-error" role="alert">
            Số tiền vượt quá số dư khả dụng.
          </p>
        )}
      </div>

      <div className="flex flex-col gap-space-1 p-space-3 [background:var(--surface-2)] rounded-md">
        <span className="text-t-micro text-text-mid">Tài khoản nhận</span>
        {destination ? (
          <span className="text-t-body text-text-hi font-weight-semi font-brand-font-num">
            {destination.bank} · {destination.account}
          </span>
        ) : (
          <span className="text-t-sm text-text-mid leading-lh-body">
            Chưa có tài khoản nhận — thêm trong mục Bảo mật trước khi rút.
          </span>
        )}
      </div>

      <Button variant="primary" size="lg" fullWidth disabled={!canSubmit || !destination} onClick={submit}>
        Yêu cầu rút tiền
      </Button>
    </Card>
  );
}
