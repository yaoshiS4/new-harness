/* ============================================================================
 * RedeemDialog — the redeem-confirm dialog. A lazy-mounted Modal (only rendered
 * when a product is selected). Deliberately SIMPLE and visual:
 *
 *   CONFIRM   gold-P coin + name + "Trị giá {value}"
 *             → COST CARD: hero "Điểm cần dùng" (amber ESCALATED when early),
 *               divider, then "Số dư hiện tại" / "Sau khi đổi" / "Điều kiện rút"
 *             → normal: reassurance line | early: amber caution callout
 *             → [ Hủy | Xác nhận đổi ]
 *
 *   SUCCESS   gold-ink check badge → title → "{name} đã được thêm…" → "Số dư còn lại"
 *
 * EARLY-CLAIM MATH: while the cooldown runs, the point cost
 * ESCALATES one step for the SAME voucher. The hero "Điểm cần dùng" shows the
 * ACTUAL escalated charge (amber), with the base as a "Mức thường" comparison;
 * "Sau khi đổi" and "Số dư còn lại" both subtract the ESCALATED cost — the dialog
 * NEVER quotes the base as the charge. The item/face is always paid IN FULL.
 * UI-only/mock: confirm simulates a server round-trip, then a success receipt.
 * ==========================================================================*/

"use client";

import { useState } from "react";
import type { Product } from "@/lib/types";
import { vi } from "@/lib/i18n";
import { formatVnd, formatCount } from "@/lib/format";
import { Modal, Button, Icon, Countdown } from "@/ui";
import { isCooldownRunning, pointsAtStep } from "@/lib/store/escalation";

export interface RedeemDialogProps {
  product: Product;
  /** member's redeemable points (gates affordability). */
  points: number;
  onClose: () => void;
  /** program budget breaker paused — no confirm button. */
  paused?: boolean;
}

type Phase = "idle" | "submitting" | "success";

const pts = (n: number) => `${formatCount(n)} ${vi.claim.costUnit}`;

/** Compact item header — gold-P coin + name + "Trị giá {value}". */
function ItemHeader({ product }: { product: Product }) {
  return (
    <div className="flex items-center gap-space-3">
      <span className="inline-flex items-center justify-center w-[44px] h-[44px] flex-none rounded-md [background:var(--surface-3)] [border:1px_solid_var(--brand-accent-hairline)] text-brand-accent-fg text-t-h3 font-weight-bold leading-[1]" aria-hidden="true">
        P
      </span>
      <div className="flex flex-col gap-[2px] min-w-[0]">
        <p className="m-[0] text-t-body font-weight-semi text-text-hi leading-lh-tight">{product.name}</p>
        <p className="m-[0] leading-lh-tight">
          <span className="text-t-sm text-modal-meta">{vi.claim.valueLabel}</span>{" "}
          <span className="store-type-num-md text-text-hi">{formatVnd(product.faceValue)}</span>
        </p>
      </div>
    </div>
  );
}

/** Success subline with the product name bolded (rest muted). */
function SuccessSub({ name }: { name: string }) {
  const s = vi.claim.successSub;
  const i = s.indexOf("{name}");
  if (i < 0) return <>{s}</>;
  return (
    <>
      <b className="text-text-hi font-weight-semi">{name}</b>
      {s.slice(i + "{name}".length)}
    </>
  );
}

export function RedeemDialog({
  product,
  points,
  onClose,
  paused = false,
}: RedeemDialogProps) {
  const [phase, setPhase] = useState<Phase>("idle");
  // One client-clock reading; advancing it when the cooldown hits zero drops the
  // "early" surcharge back to the normal price (Countdown onZeroState contract).
  const [nowMs, setNowMs] = useState(() => Date.now());

  // Redeeming while the cooldown runs = an early redeem → the point cost escalates
  // one step (same voucher). Otherwise it is the normal (base) cost.
  const early = isCooldownRunning(product, nowMs);
  const step = early ? product.currentStep + 1 : 1;
  const pointCost = pointsAtStep(
    product.basePoints,
    product.repeatFraction,
    step,
    product.maxSteps,
  );
  const affordable = points >= pointCost;
  // "Sau khi đổi" / "Số dư còn lại" ALWAYS subtract the ACTUAL charged cost
  // (escalated when early) — never the base.
  const balanceAfter = points - pointCost;

  const isVoucher = product.category === "voucher";

  // Cost emphasis: red when unaffordable, amber when merely escalated (early).
  const costTone = !affordable ? "alert" : early ? "caution" : "normal";

  const confirm = () => {
    if (phase === "submitting" || !affordable) return;
    setPhase("submitting");
    window.setTimeout(() => setPhase("success"), 600); // UI-only/mock round-trip
  };

  // ---- SUCCESS — gold badge + remaining balance ---------------------------
  if (phase === "success") {
    return (
      <Modal open onClose={onClose} size="sm">
        <div className="flex flex-col items-center text-center gap-space-4 py-space-2 px-[0]">
          <span className="inline-flex items-center justify-center w-[64px] h-[64px] rounded-pill [background:var(--surface-3)] [border:1px_solid_var(--brand-accent-hairline)] text-brand-accent-fg" aria-hidden="true">
            <Icon name="check" size={32} />
          </span>
          <div className="flex flex-col gap-space-1">
            <h3 className="m-[0] store-type-h3 text-text-hi">{vi.claim.successTitle}</h3>
            <p className="m-[0] text-t-sm leading-lh-body text-modal-meta">
              <SuccessSub name={product.name} />
            </p>
          </div>

          <span className="inline-flex items-baseline gap-space-1 py-space-2 px-space-3 rounded-pill [background:var(--surface-2)] [border:1px_solid_var(--modal-border)]">
            <span className="text-t-sm text-text-mid">
              {vi.claim.successBalanceLeft}
            </span>{" "}
            <span className="text-t-body font-weight-bold text-brand-accent-fg tabular-nums">{pts(balanceAfter)}</span>
          </span>

          <Button variant="gold" fullWidth onClick={onClose}>
            {vi.claim.btnClose}
          </Button>
        </div>
      </Modal>
    );
  }

  // ---- PAUSED (breaker) — no confirm button ---------------------------------
  if (paused) {
    return (
      <Modal open onClose={onClose} title={vi.claim.dialogTitle} size="sm">
        <div className="flex flex-col gap-space-4">
          <ItemHeader product={product} />
          <p className="text-t-sm leading-lh-body p-space-3 rounded-md [border:1px_solid_color-mix(in_srgb,var(--info)_36%,transparent)] text-text-hi [background:color-mix(in_srgb,var(--info)_12%,transparent)]" data-tone="info" role="status">
            Đổi quà đang tạm dừng, sẽ mở lại {vi.store.pausedReopen}.
          </p>
          <div className="flex gap-space-3 mt-space-1 *:flex-[1_1_0]">
            <Button variant="ghost" fullWidth onClick={onClose}>
              {vi.claim.btnCancel}
            </Button>
          </div>
        </div>
      </Modal>
    );
  }

  // ---- CONFIRM (normal or early) --------------------------------------------
  return (
    <Modal open onClose={onClose} title={vi.claim.dialogTitle} size="sm">
      <div className="flex flex-col gap-space-4">
        <ItemHeader product={product} />

        {/* COST CARD — hero "Điểm cần dùng" (ACTUAL charge: escalated amber when
            early, red when unaffordable), then a divider and the breakdown rows. */}
        <div className="store-redeem-dialog-cost" data-tone={costTone}>
          <div className="flex items-baseline justify-between gap-space-3">
            <span className="text-t-sm text-text-mid">{vi.claim.costLabel}</span>
            <span className="store-redeem-dialog-cost-value">
              {formatCount(pointCost)}
              <span className="text-t-body font-weight-semi text-text-mid">{vi.claim.costUnit}</span>
            </span>
          </div>

          <div className="h-[1px] my-space-3 mx-[0] [background:var(--border)]" />

          <div className="flex items-baseline justify-between gap-space-3 text-t-sm">
            <span className="text-text-mid">{vi.claim.rowBalanceNow}</span>
            <span className="text-text-hi font-weight-semi tabular-nums">{pts(points)}</span>
          </div>
          <div className="flex items-baseline justify-between gap-space-3 text-t-sm mt-space-2">
            <span className="text-text-mid">{vi.claim.rowBalanceAfter}</span>
            <span className="text-brand-accent-fg font-weight-semi tabular-nums">{pts(balanceAfter)}</span>
          </div>
          {/* Rolling row — VOUCHERS only (physical products omit it). */}
          {isVoucher && (
            <div className="flex items-baseline justify-between gap-space-3 text-t-sm mt-space-2">
              <span className="text-text-mid">{vi.claim.rowRolling}</span>
              <span className="text-text-hi font-weight-semi tabular-nums">
                {vi.claim.rollingValue.replace(
                  "{n}",
                  formatCount(product.rollingRequired),
                )}
              </span>
            </div>
          )}
        </div>

        {/* EARLY: amber caution callout — costs more + the cooldown resets. */}
        {early && product.cooldownEndsAt && (
          <div className="flex gap-space-2 p-space-3 [border-top:1px_solid_color-mix(in_srgb,var(--caution)_40%,var(--border))] [border-right:1px_solid_color-mix(in_srgb,var(--caution)_40%,var(--border))] [border-bottom:1px_solid_color-mix(in_srgb,var(--caution)_40%,var(--border))] [border-left:2px_solid_color-mix(in_srgb,var(--caution)_70%,transparent)] rounded-md">
            <Icon name="history" size={18} className="flex-none mt-[1px] text-caution" aria-hidden />
            <p className="m-[0] text-t-sm leading-lh-body text-modal-meta min-w-[0]">
              <EarlyCallout
                cooldownEndsAt={product.cooldownEndsAt}
                onZero={() => setNowMs(Date.now())}
              />
            </p>
          </div>
        )}

        {/* Unaffordable — one quiet neutral hint under the (red) hero cost. */}
        {!affordable && (
          <p className="m-[0] text-t-sm leading-lh-body text-modal-meta">{vi.claim.insufficientHint}</p>
        )}

        <div className="flex gap-space-3 mt-space-1 *:flex-[1_1_0]">
          <Button variant="ghost" onClick={onClose}>
            {vi.claim.btnCancel}
          </Button>
          <Button
            variant="gold"
            loading={phase === "submitting"}
            disabled={!affordable}
            onClick={confirm}
          >
            {early ? vi.claim.btnEarlyConfirm : vi.claim.btnConfirm}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

/** Early-callout copy with a live {time} countdown + both point figures spliced
 *  in. The countdown is a live component, so the string is split around {time}. */
function EarlyCallout({
  cooldownEndsAt,
  onZero,
}: {
  cooldownEndsAt: string;
  onZero: () => void;
}) {
  const [before, after] = vi.claim.earlyCallout.split("{time}");
  return (
    <>
      {before}
      <Countdown
        endsAt={cooldownEndsAt}
        zeroLabel={vi.store.fullRateReady}
        onZeroState={onZero}
        className="text-caution font-weight-semi tabular-nums"
      />
      {after}
    </>
  );
}
