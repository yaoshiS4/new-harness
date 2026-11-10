/* ============================================================================
 * Yaobet — TÀI KHOẢN / ACCOUNT (route "/tai-khoan") — §account.
 * ----------------------------------------------------------------------------
 * The RIGHT content column of the member area. The LEFT member rail
 * (MemberSidebar: identity, balance + Nạp/Rút, points/rebate, icon-grid menu)
 * is hosted ONCE by (member)/layout.tsx and shared with /vi-tien.
 *
 * Reorganized so EACH member-menu item shows ITS OWN content (one section at a
 * time, switched by the URL hash the rail sets) instead of stacking every panel:
 *   • Hồ sơ      (#ho-so)      — ProfileBasic   : avatar · real name · phone · email
 *   • Bảo mật    (#bao-mat)    — SecurityCenter : đổi MK đăng nhập · MK rút tiền · 2FA
 *   • Ngân hàng  (#ngan-hang)  — BankAccounts   : liên kết thẻ ngân hàng
 *   • Ví         (#vi-tien-ao) — CryptoAddresses: địa chỉ ví
 *
 * This Server Component fetches the truthful fixtures (§F) server-side and hands
 * them to the AccountSections client island, which picks the active section by
 * hash. Member-gated: the rail shows a guest the honest login prompt; fixtures
 * are masked at source and fall back to honest empty-states under DEMO_EMPTY.
 * ==========================================================================*/

import {
  getSecurityIndex,
  getVerification,
  getBankCards,
  getCryptoAddresses,
} from "@/lib/mock";
import { AccountSections } from "@/components/account";
import { vi } from "@/lib/i18n";

export const metadata = {
  title: "Tài khoản — Yaobet",
};

export default async function AccountPage() {
  const [index, verification, bankCards, cryptoAddresses] = await Promise.all([
    getSecurityIndex(),
    getVerification(),
    getBankCards(),
    getCryptoAddresses(),
  ]);

  return (
    <section className="flex flex-col gap-band-gap min-w-[0]" aria-label={vi.nav.account}>
      <AccountSections
        index={index}
        verification={verification}
        bankCards={bankCards}
        cryptoAddresses={cryptoAddresses}
      />
    </section>
  );
}
