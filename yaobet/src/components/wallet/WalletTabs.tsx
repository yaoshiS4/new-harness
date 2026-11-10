/* ============================================================================
 * WalletTabs — the /vi-tien client orchestrator (§wallet).
 * The balance header stays pinned at the top; below it a card-style tab strip
 * switches between FOUR focused, single-purpose panels — ONE feature per view:
 *
 *   Nạp tiền   → DepositPanel       (VN rails: Ngân hàng/Momo/ViettelPay/Thẻ cào)
 *   Rút tiền   → WithdrawPanel       (bank target + amount + fund-password gate)
 *   Lịch sử    → WalletHistory       (equal win/loss DeltaAmount rows + filters)
 *   Chuyển quỹ → FundTransferPanel   (from/to product + amount + honest pending)
 *
 * This card-style strip is the SINGLE control for switching wallet views — the
 * balance header carries no chips of its own, and the member sidebar's
 * Nạp / Rút are plain `/vi-tien#deposit|#withdraw` deep-links that this strip
 * honours (initial tab + live `hashchange`) instead of adding more buttons. One
 * clear path per action. Labels read --tab-text-rest; the selected tab lifts
 * to the --surface-3 step with a --tab-text-active label and a 2px indicator
 * edge in the same ink, so the state never rests on colour alone.
 *
 * Owns NO data — only the in-page tab state. All figures are server fixtures
 * handed down as typed props (truthful-only).
 * ==========================================================================*/

"use client";

import { useEffect, useState } from "react";
import type {
  DepositOffer,
  Envelope,
  LiveMoney,
  MoneyValue as MoneyVal,
  ProductWallet,
  Transaction,
} from "@/lib/types";
import { vi } from "@/lib/i18n";
import { Icon, type IconName } from "@/ui";
import { WalletBalanceHeader } from "./WalletBalanceHeader";
import { DepositPanel } from "./DepositPanel";
import { WithdrawPanel } from "./WithdrawPanel";
import { WalletHistory } from "./WalletHistory";
import { FundTransferPanel } from "./FundTransferPanel";

export interface WalletTabsProps {
  balance: Envelope<LiveMoney>;
  available: MoneyVal | null;
  products: ProductWallet[];
  records: Transaction[];
  bankMemo: { account: string; bank: string; memo: string };
  offer: DepositOffer | null;
  isFirstDeposit: boolean;
  withdrawDestination: { bank: string; account: string } | null;
}

type WalletTab = "deposit" | "withdraw" | "history" | "transfer";

const TABS: { id: WalletTab; label: string; icon: IconName }[] = [
  { id: "deposit", label: vi.deposit.title, icon: "deposit" },
  { id: "withdraw", label: "Rút tiền", icon: "wallet" },
  { id: "history", label: vi.wallet.history, icon: "history" },
  { id: "transfer", label: vi.wallet.transfer, icon: "chip" },
];

/** map a `/vi-tien#…` hash to a tab (sidebar deep-links), else null. */
function tabFromHash(hash: string): WalletTab | null {
  const id = hash.replace(/^#/, "");
  return TABS.some((t) => t.id === id) ? (id as WalletTab) : null;
}

export function WalletTabs({
  balance,
  available,
  products,
  records,
  bankMemo,
  offer,
  isFirstDeposit,
  withdrawDestination,
}: WalletTabsProps) {
  const [tab, setTab] = useState<WalletTab>("deposit");

  /* sidebar Nạp / Rút are `/vi-tien#deposit|#withdraw` deep-links — adopt the
   * arriving hash and follow later in-page hash changes (when already on the
   * page) so those global shortcuts switch this strip, not add more buttons. */
  useEffect(() => {
    const sync = () => {
      const next = tabFromHash(window.location.hash);
      if (next) setTab(next);
    };
    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  return (
    <div className="flex flex-col gap-space-4 min-w-[0]">
      <WalletBalanceHeader balance={balance} />

      {/* el-tabs--card style strip — gold-active, one focused feature each */}
      <div
        className="flex gap-space-2 p-space-1 [background:var(--surface-2)] border border-border rounded-md overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        role="tablist"
        aria-label="Mục ví tiền"
      >
        {TABS.map((t) => {
          const selected = t.id === tab;
          return (
            <button
              key={t.id}
              type="button"
              role="tab"
              id={`wallet-tab-${t.id}`}
              aria-selected={selected}
              aria-controls={`wallet-panel-${t.id}`}
              tabIndex={selected ? 0 : -1}
              className={`flex-[1_1_0] inline-flex items-center justify-center gap-space-2 min-h-tap-min py-[0] px-space-3 whitespace-nowrap [border-style:solid] [border-width:0_0_2px] rounded-sm font-brand-font-body text-t-body font-weight-semi cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard),background_var(--dur-fast)_var(--ease-standard)] hover:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[-2px] motion-reduce:[transform:none] motion-reduce:hover:[transform:none] max-420:px-space-2 max-420:text-t-sm ${selected ? "text-tab-text-active [background:var(--surface-3)] [border-color:currentColor]" : "text-tab-text-rest [background:transparent] [border-color:transparent] hover:text-text-hi hover:[background:var(--surface-hover)]"}`}
              onClick={() => setTab(t.id)}
            >
              <Icon name={t.icon} size={18} />
              <span className="min-w-[0]">{t.label}</span>
            </button>
          );
        })}
      </div>

      <div
        className="min-w-[0]"
        role="tabpanel"
        id={`wallet-panel-${tab}`}
        aria-labelledby={`wallet-tab-${tab}`}
      >
        {tab === "deposit" && (
          <DepositPanel bankMemo={bankMemo} offer={offer} isFirstDeposit={isFirstDeposit} />
        )}
        {tab === "withdraw" && (
          <WithdrawPanel available={available} destination={withdrawDestination} />
        )}
        {tab === "history" && <WalletHistory records={records} limit={50} />}
        {tab === "transfer" && (
          <FundTransferPanel available={available} products={products} />
        )}
      </div>
    </div>
  );
}
