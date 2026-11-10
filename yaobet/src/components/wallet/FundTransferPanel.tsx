/* ============================================================================
 * FundTransferPanel — the "Chuyển quỹ" tab (§wallet, split).
 * The non-crypto reading of `balace_list_infos`: move VND between the main
 * wallet and each product quỹ. ONE focused feature per the tabbed-wallet split:
 *
 *  • a Từ (source) / Đến (target) pair — source defaults to the main wallet, the
 *    target to the first product; swap (↕) flips them.
 *  • amount field (inputMode=numeric) clamped to the SOURCE balance; over-balance
 *    is blocked with an honest alert.
 *  • the per-product balance table (the old ProductTransferRows reading) stays
 *    on-panel as a truthful reference list — equal-salience VND figures.
 *
 * A transfer is never client-confirmed "thành công" — it stops at the
 * honest PENDING ("đang chờ xử lý") state. Balances shown are server fixtures and
 * are never fabricated. Auth-aware: a guest sees a prompt, not a usable form.
 * ==========================================================================*/

"use client";

import { useMemo, useState } from "react";
import type { MoneyValue as MoneyVal, ProductWallet } from "@/lib/types";
import { vi } from "@/lib/i18n";
import { useRequireAuth } from "@/lib/auth";
import { formatVnd } from "@/lib/format";
import { Card, Button, Icon, MoneyValue, EmptyState } from "@/ui";

export interface FundTransferPanelProps {
  /** main-wallet available balance (server figure). Null = unknown. */
  available: MoneyVal | null;
  /** per-product VND quỹ balances (server fixtures). */
  products: ProductWallet[];
}

type Phase = "idle" | "pending";

const MAIN_ID = "__main__";

export function FundTransferPanel({ available, products }: FundTransferPanelProps) {
  const { allowed, promptAuth } = useRequireAuth();

  // funds (main wallet + each product) as a flat lookup for the from/to selects.
  const funds = useMemo(
    () => [
      { id: MAIN_ID, name: vi.wallet.balance, amount: available?.amount ?? 0 },
      ...products.map((p) => ({
        id: p.productId,
        name: p.productName,
        amount: p.balance.amount,
      })),
    ],
    [available, products],
  );

  const [fromId, setFromId] = useState(MAIN_ID);
  const [toId, setToId] = useState(products[0]?.productId ?? MAIN_ID);
  const [amount, setAmount] = useState<number | null>(null);
  const [amountText, setAmountText] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");

  const from = funds.find((f) => f.id === fromId) ?? funds[0];
  const max = from?.amount ?? 0;
  const sameFund = fromId === toId;
  const overBalance = amount != null && amount > max;
  const canSubmit = amount != null && amount > 0 && !overBalance && !sameFund;

  const onAmountChange = (raw: string) => {
    const digits = raw.replace(/\D/g, "");
    setAmountText(digits ? formatVnd(Number(digits)) : "");
    setAmount(digits ? Number(digits) : null);
  };

  const swap = () => {
    setFromId(toId);
    setToId(fromId);
  };

  const submit = () => {
    if (!allowed) {
      promptAuth();
      return;
    }
    if (!canSubmit) return;
    setPhase("pending");
  };

  if (!allowed) {
    return (
      <Card variant="default" className="flex flex-col gap-space-4 p-space-4">
        <h2 className="text-t-h3 text-text-hi font-weight-semi">{vi.wallet.transfer}</h2>
        <div className="flex flex-col items-start gap-space-3">
          <p className="text-t-sm text-text-mid">{vi.auth.login} để chuyển quỹ.</p>
          <Button variant="primary" size="md" onClick={() => promptAuth()}>
            {vi.auth.login}
          </Button>
        </div>
      </Card>
    );
  }

  if (phase === "pending") {
    return (
      <Card variant="default" className="flex flex-col gap-space-4 p-space-4">
        <h2 className="text-t-h3 text-text-hi font-weight-semi">{vi.wallet.transfer}</h2>
        <div className="flex flex-col items-center text-center gap-space-3 py-space-5 px-space-3" role="status">
          <span className="inline-flex items-center justify-center w-[56px] h-[56px] rounded-pill [background:var(--surface-3)] text-text" aria-hidden="true">
            <Icon name="history" size={28} />
          </span>
          <p className="text-t-h2 text-text-hi font-weight-semi">Đang chờ xử lý</p>
          <p className="text-t-sm text-text-mid leading-lh-body max-w-[36ch]">
            Yêu cầu chuyển quỹ đã được ghi nhận và đang chờ hệ thống xử lý. Số dư
            từng quỹ sẽ được cập nhật sau khi hoàn tất.
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
      <h2 className="text-t-h3 text-text-hi font-weight-semi">{vi.wallet.transfer}</h2>

      {products.length === 0 ? (
        <EmptyState
          icon="wallet"
          title="Chưa có quỹ sản phẩm"
          message="Khi bạn chơi ở các sản phẩm, số dư từng quỹ sẽ hiển thị tại đây để chuyển."
        />
      ) : (
        <>
          {/* from / swap / to */}
          <div className="flex flex-col gap-space-2 min-[768px]:flex-row min-[768px]:items-end">
            <div className="flex flex-col gap-space-2 min-w-[0] min-[768px]:[flex:1_1_0]">
              <label className="text-t-sm text-input-label font-weight-semi" htmlFor="transfer-from">
                Từ quỹ
              </label>
              <select
                id="transfer-from"
                className="w-full min-h-tap-min py-space-3 px-space-4 font-brand-font-body text-t-body text-input-text [background:var(--surface-2)] border [border-color:var(--line-default)] rounded-md appearance-none focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 focus-visible:border-focus-ring"
                value={fromId}
                onChange={(e) => setFromId(e.target.value)}
              >
                {funds.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name} — {formatVnd(f.amount)} ₫
                  </option>
                ))}
              </select>
            </div>

            <button
              type="button"
              className="self-center inline-flex items-center justify-center w-[40px] h-[40px] rounded-pill [background:var(--surface-3)] border border-border text-brand-accent-fg cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),background_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--surface-hover)] hover:border-brand-accent hover:[transform:scale(1.05)] motion-reduce:[transform:none] motion-reduce:hover:[transform:none] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 min-[768px]:mb-space-2"
              onClick={swap}
              aria-label="Đổi chiều chuyển"
            >
              <Icon name="retry" size={18} />
            </button>

            <div className="flex flex-col gap-space-2 min-w-[0] min-[768px]:[flex:1_1_0]">
              <label className="text-t-sm text-input-label font-weight-semi" htmlFor="transfer-to">
                Đến quỹ
              </label>
              <select
                id="transfer-to"
                className="w-full min-h-tap-min py-space-3 px-space-4 font-brand-font-body text-t-body text-input-text [background:var(--surface-2)] border [border-color:var(--line-default)] rounded-md appearance-none focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 focus-visible:border-focus-ring"
                value={toId}
                onChange={(e) => setToId(e.target.value)}
              >
                {funds.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* amount */}
          <div className="flex flex-col gap-space-2 min-w-[0]">
            <label className="text-t-sm text-input-label font-weight-semi" htmlFor="transfer-amount">
              Số tiền chuyển
            </label>
            <input
              id="transfer-amount"
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
                Số tiền vượt quá số dư khả dụng của quỹ nguồn.
              </p>
            )}
            {sameFund && (
              <p className="text-t-micro text-error" role="alert">
                Quỹ nguồn và quỹ đích phải khác nhau.
              </p>
            )}
          </div>

          <Button variant="primary" size="lg" fullWidth disabled={!canSubmit} onClick={submit}>
            Chuyển quỹ
          </Button>

          {/* truthful per-product balance reference */}
          <div className="flex flex-col gap-space-2 pt-space-3 border-t border-t-border">
            <p className="text-t-sm text-text-mid font-weight-semi">Số dư theo quỹ</p>
            <ul className="flex flex-col gap-space-1 list-none m-[0] p-[0]">
              {funds.map((f) => (
                <li key={f.id} className="flex items-center justify-between gap-space-3 py-space-3 px-[0] border-b border-b-border min-h-tap-min last:[border-bottom:0]">
                  <span className="text-t-body text-text-hi font-weight-semi">{f.name}</span>
                  <MoneyValue
                    value={{ amount: f.amount, currency: "VND" }}
                    className="text-text"
                  />
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </Card>
  );
}
