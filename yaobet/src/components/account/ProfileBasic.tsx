/* ============================================================================
 * ProfileBasic — "Hồ sơ" (个人资料 / profile basic-info panel). The Hồ sơ
 * member-menu item lands here: it shows ONLY the account's basic identity —
 * avatar, display name + masked member ID, real name, phone, email. Bank-card
 * linking and crypto-wallet addresses live in their own member-menu sections
 * (Ngân hàng / Ví), so each menu item shows its own content.
 *
 * Truthful-only (§F): identity comes from the mock session (useAuth); the
 * contact rows (real name / phone / email) are typed verification fixtures
 * already masked at source. A guest never reaches this island (the rail shows
 * the honest login prompt), so this renders for an authenticated mock user only.
 * "Đổi ảnh đại diện" / row edits are UI-only affordances — no BE.
 * ==========================================================================*/

"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { vi } from "@/lib/i18n";
import type { VerificationItem } from "@/lib/types";
import { Badge, Button, Card, type BadgeTone } from "@/ui";

export interface ProfileBasicProps {
  /** real name / phone / email rows (masked at source). */
  contact: VerificationItem[];
}

const ROW_LABEL: Partial<Record<VerificationItem["id"], string>> = {
  realName: vi.account.realName,
  phone: vi.account.phone,
  email: vi.account.email,
};

const STATUS_TONE: Record<VerificationItem["status"], BadgeTone> = {
  verified: "win",
  pending: "info",
  unset: "neutral",
  error: "danger",
};

const STATUS_TEXT: Record<VerificationItem["status"], string> = {
  verified: vi.account.statusVerified,
  pending: vi.account.statusPending,
  unset: vi.account.statusUnset,
  error: vi.state.error,
};

export function ProfileBasic({ contact }: ProfileBasicProps) {
  const { user } = useAuth();
  const [notice, setNotice] = useState(false);

  if (!user) return null;

  /* only basic-info contact rows — bank/crypto live in their own sections. */
  const rows = contact.filter((c) => c.id === "realName" || c.id === "phone" || c.id === "email");

  return (
    <section className="min-w-[0]" aria-label={vi.account.profileTitle}>
      <Card variant="default" className="flex flex-col gap-space-5 p-card-pad">
        <header className="flex flex-col gap-space-1">
          <h2 className="text-t-h1 font-(family-name:--type-h2-family) font-weight-semi text-text-hi">{vi.account.profileTitle}</h2>
          <p className="text-t-sm text-text-mid">{vi.account.profileSubtitle}</p>
        </header>

        {/* avatar + identity ------------------------------------------- */}
        <div className="flex items-center gap-space-3 flex-wrap p-card-pad-sm [background:var(--surface-2)] rounded-lg">
          <span className="grid place-items-center w-[56px] h-[56px] rounded-pill [background:var(--surface-3)] [border:1px_solid_var(--brand-accent-hairline)] flex-[0_0_auto]" aria-hidden="true">
            <span className="text-t-h2 font-weight-bold font-brand-font-num text-brand-accent-fg">
              {user.displayName.trim().charAt(0).toUpperCase() || "Y"}
            </span>
          </span>
          <div className="flex flex-col gap-space-1 min-w-[0] flex-[1_1_auto]">
            <span className="text-t-body font-weight-semi text-text-hi">{user.displayName}</span>
            <span className="text-t-micro text-text-mid">
              {vi.account.memberId}: <span className="font-brand-font-num text-text-hi">{user.memberId}</span>
            </span>
          </div>
          <Button variant="ghost" size="sm" onClick={() => setNotice(true)}>
            {vi.account.avatarChange}
          </Button>
        </div>

        {/* contact rows ------------------------------------------------- */}
        <ul className="flex flex-col m-[0] p-[0] list-none">
          {rows.map((item) => (
            <li key={item.id} className="flex items-center justify-between gap-space-3 flex-wrap py-space-3 px-[0] border-b border-b-border last:[border-bottom:0]">
              <div className="flex flex-col gap-space-1 min-w-[0]">
                <span className="text-t-sm text-text-hi">{ROW_LABEL[item.id]}</span>
                <span className="text-t-sm text-text-mid font-brand-font-num overflow-hidden text-ellipsis">
                  {item.value ?? <span className="text-text-dim">—</span>}
                </span>
              </div>
              <div className="flex items-center gap-space-3 flex-[0_0_auto]">
                <Badge tone={STATUS_TONE[item.status]} variant="subtle">
                  {STATUS_TEXT[item.status]}
                </Badge>
                <Button variant="ghost" size="sm" onClick={() => setNotice(true)}>
                  {item.status === "unset" ? vi.account.setupNow : vi.account.edit}
                </Button>
              </div>
            </li>
          ))}
        </ul>

        {notice && (
          <p className="text-t-micro text-text-mid py-space-2 px-space-3 rounded-md [background:var(--tint)] border border-border" role="status">
            {vi.account.uiOnlyNotice}
          </p>
        )}
      </Card>
    </section>
  );
}
