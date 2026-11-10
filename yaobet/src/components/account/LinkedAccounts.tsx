/* ============================================================================
 * BankAccounts + CryptoAddresses — the member-menu money surfaces (钱包设置
 * "wallet settings"). Both are anchored sections in the member account area so
 * the rail's "Ngân hàng" / "Ví tiền ảo" tiles scroll to them.
 *
 *   BankAccounts   — Liên kết thẻ ngân hàng: each linked card shows bank, masked
 *                    number (masked at source), holder, and a Mặc định badge.
 *   CryptoAddresses— Địa chỉ ví: each address shows asset · network · masked
 *                    address + Mặc định badge.
 *
 * Truthful-only (§F): values are typed fixtures already masked at source; an
 * empty list renders an honest empty-state (never a fabricated card). Add/remove
 * are UI-only affordances (no BE) — "Thêm" surfaces an honest no-BE notice.
 * ==========================================================================*/

"use client";

import { useState } from "react";
import { vi } from "@/lib/i18n";
import type { BankCard, CryptoAddress } from "@/lib/types";
import { Badge, Button, Card, Icon } from "@/ui";

function NoBackendNotice() {
  return (
    <p className="text-t-micro text-text-mid py-space-2 px-space-3 rounded-md [background:var(--tint)] border border-border" role="status">
      Đây là bản giao diện mẫu — chưa kết nối hệ thống.
    </p>
  );
}

export function BankAccounts({ cards }: { cards: BankCard[] }) {
  const [adding, setAdding] = useState(false);

  return (
    <section className="min-w-[0]" id="ngan-hang" aria-label={vi.account.bankTitle}>
      <Card variant="default" className="flex flex-col gap-space-4 p-card-pad">
        <header className="flex items-center justify-between gap-space-3 flex-wrap">
          <div className="flex items-start gap-space-2">
            <Icon name="card" size={20} className="text-brand-accent-fg flex-[0_0_auto] mt-[2px]" />
            <div className="flex flex-col gap-space-1 min-w-[0]">
              <h2 className="text-t-h2 font-weight-semi text-text-hi">{vi.account.bankTitle}</h2>
              <p className="text-t-micro text-text-mid">{vi.account.bankSubtitle}</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" icon="check" onClick={() => setAdding(true)}>
            {vi.account.bankAdd}
          </Button>
        </header>

        {cards.length === 0 ? (
          <p className="text-t-sm text-text-mid py-space-5 px-[0] text-center">{vi.account.bankEmpty}</p>
        ) : (
          <ul className="flex flex-col gap-space-3 m-[0] p-[0] list-none">
            {cards.map((c) => (
              <li key={c.id} className="flex items-start gap-space-3 p-card-pad-sm [background:var(--surface-2)] border border-border rounded-lg">
                <span className="flex-[0_0_auto] w-[40px] h-[40px] grid place-items-center rounded-md [background:var(--tint)] text-brand-accent-fg" aria-hidden="true">
                  <Icon name="card" size={22} />
                </span>
                <div className="flex flex-col gap-space-1 min-w-[0]">
                  <div className="flex items-center gap-space-2 flex-wrap">
                    <span className="text-t-body font-weight-semi text-text-hi">{c.bankName}</span>
                    {c.isDefault && (
                      <Badge tone="gold" variant="subtle">
                        {vi.account.default}
                      </Badge>
                    )}
                  </div>
                  <span className="text-t-sm font-brand-font-num text-text tracking-[0.04em] break-all">{c.maskedNumber}</span>
                  <span className="text-t-micro text-text-mid">
                    {vi.account.bankHolder}: {c.holderName}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}

        {adding && <NoBackendNotice />}
      </Card>
    </section>
  );
}

export function CryptoAddresses({ addresses }: { addresses: CryptoAddress[] }) {
  const [adding, setAdding] = useState(false);

  return (
    <section className="min-w-[0]" id="vi-tien-ao" aria-label={vi.account.cryptoTitle}>
      <Card variant="default" className="flex flex-col gap-space-4 p-card-pad">
        <header className="flex items-center justify-between gap-space-3 flex-wrap">
          <div className="flex items-start gap-space-2">
            <Icon name="chip" size={20} className="text-brand-accent-fg flex-[0_0_auto] mt-[2px]" />
            <div className="flex flex-col gap-space-1 min-w-[0]">
              <h2 className="text-t-h2 font-weight-semi text-text-hi">{vi.account.cryptoTitle}</h2>
              <p className="text-t-micro text-text-mid">{vi.account.cryptoSubtitle}</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" icon="check" onClick={() => setAdding(true)}>
            {vi.account.cryptoAdd}
          </Button>
        </header>

        {addresses.length === 0 ? (
          <p className="text-t-sm text-text-mid py-space-5 px-[0] text-center">{vi.account.cryptoEmpty}</p>
        ) : (
          <ul className="flex flex-col gap-space-3 m-[0] p-[0] list-none">
            {addresses.map((a) => (
              <li key={a.id} className="flex items-start gap-space-3 p-card-pad-sm [background:var(--surface-2)] border border-border rounded-lg">
                <span className="flex-[0_0_auto] w-[40px] h-[40px] grid place-items-center rounded-md [background:var(--tint)] text-brand-accent-fg" aria-hidden="true">
                  <Icon name="chip" size={22} />
                </span>
                <div className="flex flex-col gap-space-1 min-w-[0]">
                  <div className="flex items-center gap-space-2 flex-wrap">
                    <span className="text-t-body font-weight-semi text-text-hi">
                      {a.asset} · {a.network}
                    </span>
                    {a.isDefault && (
                      <Badge tone="gold" variant="subtle">
                        {vi.account.default}
                      </Badge>
                    )}
                  </div>
                  <span className="text-t-sm font-brand-font-num text-text tracking-[0.04em] break-all">{a.maskedAddress}</span>
                  <span className="text-t-micro text-text-mid">
                    {vi.account.cryptoNetwork}: {a.network}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}

        {adding && <NoBackendNotice />}
      </Card>
    </section>
  );
}
