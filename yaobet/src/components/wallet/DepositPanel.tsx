/* ============================================================================
 * DepositPanel — VN-rail deposit (§deposit DepositPanel) [RG].
 * Vietnamese rails FIRST: Ngân hàng · Momo · ViettelPay · Thẻ cào.
 *
 *  • rail selector (Tabs) → amount field (inputMode=numeric) + lucky 6/8 preset
 *    chips that AVOID digit-4 (LUCKY_DEPOSIT_PRESETS, marketing numerals only —
 *    the user's typed amount is never massaged).
 *  • rail-specific surface:
 *      bank        = dest account + COPYABLE transfer memo (tap-to-copy) +
 *                    "Tôi đã chuyển" → PENDING (returnable, server-confirmed).
 *      momo/viettel= QR/deep-link placeholder slot → pending.
 *      thẻ cào     = provider/denomination + serial + PIN (inputMode=numeric).
 *
 * `success` is only ever server-confirmed — this UI stops at the
 * honest PENDING ("đang chờ xác nhận") state; no client-side "thành công".
 * Auth-aware: a guest sees a prompt instead of a usable form.
 * ==========================================================================*/

"use client";

import { useState } from "react";
import type { DepositOffer, DepositRail } from "@/lib/types";
import { vi } from "@/lib/i18n";
import { useRequireAuth } from "@/lib/auth";
import {
  LUCKY_DEPOSIT_PRESETS,
  formatPresetChip,
  formatVnd,
} from "@/lib/format";
import { Card, Button, Tabs, Pill, Icon, MoneyValue } from "@/ui";

export interface DepositPanelProps {
  /** copyable bank-transfer destination (server-sourced). */
  bankMemo: { account: string; bank: string; memo: string };
  /** first-deposit T&C offer — server-sourced, no hardcoded %; null = none. */
  offer: DepositOffer | null;
  /** zero-balance member → present the first-deposit variant copy. */
  isFirstDeposit?: boolean;
}

const RAILS: { id: DepositRail; label: string }[] = [
  { id: "bank", label: vi.deposit.railBank },
  { id: "momo", label: vi.deposit.railMomo },
  { id: "viettelpay", label: vi.deposit.railViettel },
  { id: "card", label: vi.deposit.railCard },
];

type Phase = "idle" | "pending";

export function DepositPanel({ bankMemo, offer, isFirstDeposit }: DepositPanelProps) {
  const { allowed, promptAuth } = useRequireAuth();
  const [rail, setRail] = useState<DepositRail>("bank");
  const [amount, setAmount] = useState<number | null>(null);
  const [amountText, setAmountText] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [copied, setCopied] = useState(false);
  // thẻ cào fields
  const [serial, setSerial] = useState("");
  const [pin, setPin] = useState("");

  const onAmountChange = (raw: string) => {
    const digits = raw.replace(/\D/g, "");
    setAmountText(digits ? formatVnd(Number(digits)) : "");
    setAmount(digits ? Number(digits) : null);
  };

  const pickPreset = (preset: number) => {
    setAmount(preset);
    setAmountText(formatVnd(preset));
  };

  const copyMemo = async () => {
    try {
      await navigator.clipboard.writeText(bankMemo.memo);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false); // clipboard blocked — stay honest, no fake confirm
    }
  };

  // "Tôi đã chuyển" / submit → returnable PENDING (NOT a client success).
  const submit = () => {
    if (!allowed) {
      promptAuth({ action: "deposit", isFirstDeposit });
      return;
    }
    setPhase("pending");
  };

  if (!allowed) {
    return (
      <Card variant="default" className="flex flex-col gap-space-4 p-space-4">
        <h2 className="text-t-h3 text-text-hi font-weight-semi">{vi.deposit.title}</h2>
        <div className="flex flex-col items-start gap-space-3">
          <p className="text-t-sm text-text-mid">{vi.auth.login} để nạp tiền.</p>
          <Button variant="primary" size="md" onClick={() => promptAuth({ action: "deposit", isFirstDeposit })}>
            {vi.auth.login}
          </Button>
        </div>
      </Card>
    );
  }

  if (phase === "pending") {
    return (
      <Card variant="default" className="flex flex-col gap-space-4 p-space-4">
        <h2 className="text-t-h3 text-text-hi font-weight-semi">{vi.deposit.title}</h2>
        <div className="flex flex-col items-center text-center gap-space-3 py-space-5 px-space-3" role="status">
          <span className="inline-flex items-center justify-center w-[56px] h-[56px] rounded-pill [background:var(--surface-3)] text-brand-accent-fg" aria-hidden="true">
            <Icon name="history" size={28} />
          </span>
          <p className="text-t-h2 text-text-hi font-weight-semi">{vi.deposit.pending}</p>
          <p className="text-t-sm text-text-mid leading-lh-body max-w-[36ch]">
            Yêu cầu nạp đang chờ hệ thống xác nhận. Số dư sẽ được cập nhật sau khi
            xác nhận — bạn có thể quay lại màn hình nạp bất cứ lúc nào.
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
      <h2 className="text-t-h3 text-text-hi font-weight-semi">{vi.deposit.title}</h2>

      {/* first-deposit offer — server-sourced T&C, no hardcoded % */}
      {isFirstDeposit && offer && (
        <div className="flex flex-col gap-space-1 p-space-3 border border-brand-accent-hairline rounded-md [background:var(--tint)]">
          <p className="text-t-body text-brand-accent-fg font-weight-semi">{offer.title}</p>
          <p className="text-t-sm text-text-mid leading-lh-body">{offer.body}</p>
          <p className="text-t-sm text-text inline-flex gap-space-1 items-baseline">
            Tối thiểu để đủ điều kiện:{" "}
            <MoneyValue value={offer.minToQualify} className="text-text-hi" />
          </p>
        </div>
      )}

      {/* VN rails FIRST */}
      <Tabs
        items={RAILS.map((r) => ({ id: r.id, label: r.label }))}
        active={rail}
        onChange={(id) => setRail(id as DepositRail)}
        label="Chọn hình thức nạp"
      />

      {/* amount field + lucky 6/8 presets (marketing chips; avoid 4) */}
      <div className="flex flex-col gap-space-3">
        <label className="text-t-sm text-input-label font-weight-semi" htmlFor="deposit-amount">
          {vi.deposit.amount}
        </label>
        <input
          id="deposit-amount"
          className="w-full min-h-tap-min py-space-3 px-space-4 font-brand-font-num text-t-h3 text-input-text [background:var(--surface-2)] border [border-color:var(--line-default)] rounded-md placeholder:text-input-helper focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 focus-visible:border-focus-ring"
          inputMode="numeric"
          autoComplete="off"
          placeholder="0 ₫"
          value={amountText}
          onChange={(e) => onAmountChange(e.target.value)}
        />
        <div className="flex flex-wrap gap-space-2" role="group" aria-label="Số tiền gợi ý">
          {LUCKY_DEPOSIT_PRESETS.map((p) => (
            <Pill key={p} active={amount === p} onClick={() => pickPreset(p)}>
              {formatPresetChip(p)}
            </Pill>
          ))}
        </div>
      </div>

      {/* rail-specific surface */}
      {rail === "bank" && (
        <div className="flex flex-col gap-space-3 pt-space-2 border-t border-t-border">
          <div className="flex flex-col gap-space-1">
            <span className="text-t-micro text-text-mid">Ngân hàng</span>
            <span className="text-t-body text-text-hi font-weight-semi font-brand-font-num">{bankMemo.bank}</span>
          </div>
          <div className="flex flex-col gap-space-1">
            <span className="text-t-micro text-text-mid">Số tài khoản</span>
            <span className="text-t-body text-text-hi font-weight-semi font-brand-font-num">{bankMemo.account}</span>
          </div>
          <div className="flex flex-col gap-space-1">
            <span className="text-t-micro text-text-mid">Nội dung chuyển khoản</span>
            <span className="flex items-center gap-space-3 flex-wrap">
              <span className="text-t-h3 text-brand-accent-fg font-weight-bold font-brand-font-num tracking-[0.04em]">{bankMemo.memo}</span>
              <Button variant="ghost" size="sm" icon="copy" onClick={copyMemo}>
                {copied ? "Đã sao chép" : vi.deposit.copyMemo}
              </Button>
            </span>
          </div>
          <p className="text-t-micro text-text-mid leading-lh-body">
            Chuyển khoản đúng nội dung trên để hệ thống tự động đối soát.
          </p>
          <Button variant="primary" size="lg" fullWidth onClick={submit}>
            {vi.deposit.iHaveTransferred}
          </Button>
        </div>
      )}

      {(rail === "momo" || rail === "viettelpay") && (
        <div className="flex flex-col gap-space-3 pt-space-2 border-t border-t-border">
          {/* QR/deep-link PLACEHOLDER SLOT — token-derived, awaiting real asset */}
          <div className="flex items-center justify-center w-[160px] h-[160px] self-center border border-dashed border-border rounded-md [background:var(--surface-2)] text-text-mid" aria-hidden="true">
            <Icon name="grid" size={40} />
          </div>
          <p className="text-t-micro text-text-mid leading-lh-body">
            Quét mã QR hoặc mở ứng dụng {rail === "momo" ? "Momo" : "ViettelPay"} để
            hoàn tất. Mã sẽ hiển thị tại đây khi sẵn sàng.
          </p>
          <Button variant="primary" size="lg" fullWidth onClick={submit}>
            {vi.deposit.iHaveTransferred}
          </Button>
        </div>
      )}

      {rail === "card" && (
        <div className="flex flex-col gap-space-3 pt-space-2 border-t border-t-border">
          <label className="text-t-sm text-input-label font-weight-semi" htmlFor="card-serial">
            Số seri
          </label>
          <input
            id="card-serial"
            className="w-full min-h-tap-min py-space-3 px-space-4 font-brand-font-num text-t-h3 text-input-text [background:var(--surface-2)] border [border-color:var(--line-default)] rounded-md placeholder:text-input-helper focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 focus-visible:border-focus-ring"
            inputMode="numeric"
            autoComplete="off"
            placeholder="Nhập số seri"
            value={serial}
            onChange={(e) => setSerial(e.target.value.replace(/\D/g, ""))}
          />
          <label className="text-t-sm text-input-label font-weight-semi" htmlFor="card-pin">
            Mã thẻ
          </label>
          <input
            id="card-pin"
            className="w-full min-h-tap-min py-space-3 px-space-4 font-brand-font-num text-t-h3 text-input-text [background:var(--surface-2)] border [border-color:var(--line-default)] rounded-md placeholder:text-input-helper focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 focus-visible:border-focus-ring"
            inputMode="numeric"
            autoComplete="off"
            placeholder="Nhập mã thẻ"
            value={pin}
            onChange={(e) => setPin(e.target.value.replace(/\D/g, ""))}
          />
          <Button
            variant="primary"
            size="lg"
            fullWidth
            disabled={!serial || !pin}
            onClick={submit}
          >
            Nạp thẻ cào
          </Button>
        </div>
      )}
    </Card>
  );
}
