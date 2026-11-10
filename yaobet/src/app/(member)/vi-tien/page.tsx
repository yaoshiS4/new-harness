/* ============================================================================
 * Yaobet — VÍ / WALLET (route "/vi-tien") — §wallet/§deposit.
 * ----------------------------------------------------------------------------
 * A Server Component in the (member) route group: fetches the wallet fixtures
 * server-side as typed values/§F envelopes and hands them to the WalletTabs
 * client orchestrator (tabbed wallet — Nạp / Rút / Lịch sử / Chuyển
 * quỹ, one focused feature per view). Mounts inside the shared shell (root
 * <AppShell> → header + category nav + bottom tab bar) and the (member) layout —
 * so the Wallet is a first-class destination reached in ONE tap from the
 * bottom-bar `Ví` tab.
 *
 * Truthful-only (§F): the balance is a Live envelope (Skeleton/ErrorState/absent
 * handled in WalletBalanceHeader); per-product balances + history are truthful
 * fixtures rendered on the equal-salience money role; deposit/withdraw stop at
 * honest PENDING states (no client-confirmed success). Bottom-bar `Ví` already
 * routes here (BottomTabBar.tsx).
 * ==========================================================================*/

import {
  getWallet,
  getBalance,
  getRecords,
  getDepositOffer,
  getBankTransferMemo,
} from "@/lib/mock";
import { WalletTabs } from "@/components/wallet";
import { vi } from "@/lib/i18n";

export const metadata = {
  title: "Ví tiền — Yaobet",
};

export default async function WalletPage() {
  const [wallet, balance, records, offer, bankMemo] = await Promise.all([
    getWallet(),
    getBalance(),
    getRecords(),
    getDepositOffer(),
    getBankTransferMemo(),
  ]);

  // zero main balance → present the deposit panel's first-deposit variant.
  const isFirstDeposit = wallet.balance.amount === 0;

  // server-reflected payout destination (read-only in the withdraw panel). In a
  // real API this is the member's verified bank account; here we surface the
  // same bank fixture so the happy path renders, or null when none is on file.
  const withdrawDestination = bankMemo
    ? { bank: bankMemo.bank, account: bankMemo.account }
    : null;

  return (
    <section className="flex flex-col gap-space-5 min-w-[0]" aria-label={vi.wallet.title}>
      <WalletTabs
        balance={balance}
        available={{ amount: wallet.balance.amount, currency: "VND" }}
        products={wallet.products}
        records={records}
        bankMemo={bankMemo}
        offer={offer}
        isFirstDeposit={isFirstDeposit}
        withdrawDestination={withdrawDestination}
      />
    </section>
  );
}
