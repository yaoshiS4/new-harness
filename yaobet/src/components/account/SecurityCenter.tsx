/* ============================================================================
 * SecurityCenter — "Bảo mật" (安全验证 / security panel). The Bảo mật
 * member-menu item lands here. The basic-info verification rows (real name /
 * phone / email) live in the Hồ sơ section, so each menu item shows its own
 * content. This panel is the SECURITY surface:
 *
 *   score      — a security-score bar (0–100, server-issued; the island renders
 *                the figure it receives, never re-derives or inflates it).
 *   controls   — three collapsible security controls:
 *     1. Đổi mật khẩu đăng nhập   — cũ / mới / xác nhận
 *     2. Mật khẩu rút tiền (fund) — mới / xác nhận (set or change)
 *     3. Mã xác thực động (2FA)   — enable affordance
 *   Each control's status (set / unset) comes from the truthful verification
 *   fixture; opening one reveals a UI-only form that stops at an honest no-BE
 *   notice on submit (no fake success).
 *
 * Truthful-only (§F): the score is server-issued; the fund-pw / 2FA status is a
 * typed fixture. Mobile-first @375 (controls stack); desktop fills the column.
 * ==========================================================================*/

"use client";

import { useState } from "react";
import { vi } from "@/lib/i18n";
import type { SecurityIndex, VerificationItem } from "@/lib/types";
import { Badge, Button, Card, Icon, type BadgeTone } from "@/ui";

export interface SecurityCenterProps {
  index: SecurityIndex;
  /** verification fixture — read for fund-pw / 2FA status only. */
  verification: VerificationItem[];
}

function scoreBand(score: number): { label: string; tone: BadgeTone } {
  if (score >= 80) return { label: vi.account.securityScoreHigh, tone: "win" };
  if (score >= 40) return { label: vi.account.securityScoreMedium, tone: "info" };
  return { label: vi.account.securityScoreLow, tone: "danger" };
}

type ControlId = "login" | "fund" | "dynamic";

export function SecurityCenter({ index, verification }: SecurityCenterProps) {
  const [open, setOpen] = useState<ControlId | null>(null);
  const band = scoreBand(index.score);

  const fundItem = verification.find((v) => v.id === "fundPassword");
  const dynItem = verification.find((v) => v.id === "dynamicCode");
  const fundSet = fundItem?.status === "verified";
  const dynSet = dynItem?.status === "verified";

  const toggle = (id: ControlId) => setOpen((cur) => (cur === id ? null : id));

  return (
    <section className="min-w-[0]" aria-label={vi.account.securityCenter}>
      <Card variant="default" className="flex flex-col gap-space-5 p-card-pad">
        {/* header + score bar ----------------------------------------- */}
        <header className="flex flex-col gap-space-4">
          <div className="flex items-start gap-space-2">
            <Icon name="shield" size={24} className="text-brand-accent-fg flex-[0_0_auto] mt-[2px]" />
            <div className="flex flex-col gap-space-1 min-w-[0]">
              <h2 className="text-t-h1 font-(family-name:--type-h2-family) font-weight-semi text-text-hi">{vi.account.securityCenter}</h2>
              <p className="text-t-sm text-text-mid">{vi.account.securitySubtitle}</p>
            </div>
          </div>

          <div className="flex flex-col gap-space-2 p-card-pad-sm [background:var(--surface-2)] rounded-lg">
            <div className="flex items-center justify-between gap-space-3">
              <span className="text-t-sm text-text-mid">{vi.account.securityScore}</span>
              <span className="inline-flex items-baseline gap-space-2">
                <span className="text-t-h2 font-weight-bold font-brand-font-num text-brand-accent-fg">{index.score}</span>
                <span className="text-t-micro text-text-dim">/ 100</span>
                <Badge tone={band.tone} variant="subtle">
                  {band.label}
                </Badge>
              </span>
            </div>
            <div
              className="h-[8px] rounded-pill [background:var(--tint)] overflow-hidden"
              role="progressbar"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={index.score}
              aria-label={vi.account.securityScore}
            >
              <span className="block h-full rounded-pill [background:var(--brand-accent)] [transition:width_var(--dur-slow)_var(--ease-entrance)]" style={{ width: `${index.score}%` }} />
            </div>
          </div>
        </header>

        {/* security controls ------------------------------------------ */}
        <ul className="flex flex-col gap-space-3 m-[0] p-[0] list-none">
          <SecurityControl
            id="login"
            icon="lock"
            title={vi.account.changeLoginPassword}
            sub={vi.account.loginPasswordSub}
            actionLabel={vi.account.change}
            isOpen={open === "login"}
            onToggle={() => toggle("login")}
          >
            <ChangePasswordForm
              fields={[
                vi.account.oldPassword,
                vi.account.newPassword,
                vi.account.confirmPassword,
              ]}
            />
          </SecurityControl>

          <SecurityControl
            id="fund"
            icon="wallet"
            title={vi.account.fundPasswordTitle}
            sub={vi.account.fundPasswordSub}
            status={fundSet ? "verified" : "unset"}
            actionLabel={fundSet ? vi.account.change : vi.account.setupNow}
            isOpen={open === "fund"}
            onToggle={() => toggle("fund")}
          >
            <ChangePasswordForm
              fields={[vi.account.newPassword, vi.account.confirmFundPassword]}
            />
          </SecurityControl>

          <SecurityControl
            id="dynamic"
            icon="shield"
            title={vi.account.dynamicCodeTitle}
            sub={vi.account.dynamicCodeSub}
            status={dynSet ? "verified" : "unset"}
            actionLabel={dynSet ? vi.account.change : vi.account.enable}
            isOpen={open === "dynamic"}
            onToggle={() => toggle("dynamic")}
          >
            <EnableNotice />
          </SecurityControl>
        </ul>
      </Card>
    </section>
  );
}

/* -- one collapsible security control row ---------------------------------- */
function SecurityControl({
  id,
  icon,
  title,
  sub,
  status,
  actionLabel,
  isOpen,
  onToggle,
  children,
}: {
  id: ControlId;
  icon: "lock" | "wallet" | "shield";
  title: string;
  sub: string;
  status?: "verified" | "unset";
  actionLabel: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  const panelId = `sec-panel-${id}`;
  return (
    <li className="border border-border rounded-lg [background:var(--surface-2)] overflow-hidden">
      <button
        type="button"
        className="group flex flex-wrap items-center gap-space-3 w-full min-h-tap-min py-space-3 px-card-pad-sm [background:transparent] [border:0] text-left cursor-pointer text-text-hi hover:[background:var(--tint)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[-2px]"
        aria-expanded={isOpen}
        aria-controls={panelId}
        onClick={onToggle}
      >
        <span className="[transition:transform_var(--dur-fast)_var(--ease-standard)] grid place-items-center w-[36px] h-[36px] rounded-md [background:var(--tint)] text-brand-accent-fg flex-[0_0_auto] [.group:hover_&]:[transform:scale(1.1)] motion-reduce:[transform:none] motion-reduce:[.group:hover_&]:[transform:none]" aria-hidden="true">
          <Icon name={icon} size={20} />
        </span>
        <span className="flex flex-col gap-space-1 min-w-[0] flex-[1_1_140px]">
          <span className="text-t-sm font-weight-semi text-text-hi">{title}</span>
          <span className="text-t-micro text-text-mid">{sub}</span>
        </span>
        {/* status + action: one cluster that wraps below the title on a narrow row */}
        <span className="inline-flex items-center gap-space-3 ml-auto min-w-[0] flex-[0_1_auto]">
          {status && (
            <Badge tone={status === "verified" ? "win" : "neutral"} variant="subtle">
              {status === "verified" ? vi.account.statusVerified : vi.account.statusUnset}
            </Badge>
          )}
          <span className="inline-flex items-center gap-space-1 flex-[0_1_auto] min-w-[0] text-right text-t-micro font-weight-semi text-brand-accent-fg">
            <span className="min-w-[0]">{actionLabel}</span>
            <Icon name="chevronDown" size={14} className={isOpen ? "flex-[0_0_auto] [transform:rotate(180deg)] [transition:transform_var(--dur-fast)_var(--ease-standard)]" : "flex-[0_0_auto]"} />
          </span>
        </span>
      </button>
      {isOpen && (
        <div id={panelId} role="region" className="p-card-pad-sm border-t border-t-border">
          {children}
        </div>
      )}
    </li>
  );
}

/* -- password form (UI-only; honest no-BE notice on submit) ---------------- */
function ChangePasswordForm({ fields }: { fields: string[] }) {
  const [show, setShow] = useState(false);
  const [notice, setNotice] = useState(false);

  return (
    <form
      className="flex flex-col gap-space-4"
      onSubmit={(e) => {
        e.preventDefault();
        setNotice(true);
      }}
    >
      {fields.map((label) => (
        <Field key={label} label={label} type={show ? "text" : "password"} />
      ))}

      <button
        type="button"
        className="inline-flex items-center gap-space-1 self-start py-space-1 px-[0] [background:transparent] [border:0] text-text-mid text-t-micro cursor-pointer hover:text-brand-accent-fg"
        onClick={() => setShow((s) => !s)}
        aria-pressed={show}
      >
        <Icon name={show ? "eyeOff" : "eye"} size={16} />
        <span>{show ? vi.account.hidePassword : vi.account.showPassword}</span>
      </button>

      {notice && (
        <p className="text-t-micro text-text-mid py-space-2 px-space-3 rounded-md [background:var(--tint)] border border-border" role="status">
          {vi.account.uiOnlyNotice}
        </p>
      )}

      <Button variant="primary" size="md" type="submit" fullWidth>
        {vi.account.save}
      </Button>
    </form>
  );
}

/* -- 2FA enable (UI-only) -------------------------------------------------- */
function EnableNotice() {
  const [notice, setNotice] = useState(false);
  return (
    <div className="flex flex-col gap-space-4">
      <p className="text-t-micro text-text-mid py-space-2 px-space-3 rounded-md [background:var(--tint)] border border-border" role="status">
        {notice ? vi.account.uiOnlyNotice : vi.account.dynamicCodeSub}
      </p>
      <Button variant="primary" size="md" fullWidth onClick={() => setNotice(true)}>
        {vi.account.enable}
      </Button>
    </div>
  );
}

function Field({ label, type }: { label: string; type: string }) {
  return (
    <label className="flex flex-col gap-space-1">
      <span className="text-t-micro text-input-label">{label}</span>
      <input className="w-full min-h-tap-min py-[0] px-space-3 border [border-color:var(--line-default)] rounded-md [background:var(--surface-2)] text-input-text text-t-sm font-brand-font-body [transition:border-color_var(--dur-fast)_var(--ease-standard)] placeholder:text-input-helper focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 focus-visible:border-focus-ring" type={type} autoComplete="off" placeholder={label} />
    </label>
  );
}
