/* ============================================================================
 * BottomTabBar (MOBILE) — explicit 5 tabs:
 *   Trang chủ · Khuyến mãi · NẠP (center, raised) · Ví · Tài khoản
 * Wallet (Ví) is a first-class persistent destination → /vi-tien, so a member
 * reaches balance + Nạp + Rút + Lịch sử in ONE tap from any screen (the chips
 * live on the /vi-tien WalletBalanceHeader, owned by the wallet agent).
 *
 * - member: NẠP → deposit (here: open auth modal carrying a deposit resume-
 *   intent is the guest path; for a member NẠP routes to /nap-tien via onDeposit
 *   supplied by AppShell). Ví → /vi-tien. Tài khoản → /tai-khoan (account hub).
 * - guest: NẠP / Ví / Tài khoản open the auth modal with a resume-intent (the
 *   FTD seam). Trang chủ tap while already on `/` opens the CategorySheet
 *   — handled by onHomeTap from AppShell.
 *
 * Mobile only (<768px); hidden desktop; honors safe-area-inset-bottom; tap
 * targets ≥--tap-bar (48px).
 * ==========================================================================*/

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth, useAuthModal } from "@/lib/auth";
import { vi } from "@/lib/i18n";
import { Icon } from "@/ui/Icon/Icon";

export interface BottomTabBarProps {
  /** member NẠP handler (opens the deposit sheet/route). Provided by AppShell. */
  onDeposit: () => void;
  /** tapping Trang chủ while already on `/` opens the CategorySheet. */
  onHomeTap: () => void;
}

export function BottomTabBar({ onDeposit, onHomeTap }: BottomTabBarProps) {
  const pathname = usePathname();
  const { authState } = useAuth();
  const { openAuthModal } = useAuthModal();
  const isMember = authState !== "guest";

  const isActive = (href?: string) =>
    href ? (href === "/" ? pathname === "/" : pathname.startsWith(href)) : false;

  // guest taps that need auth carry a resume-intent (the FTD seam).
  const guardedDeposit = () => {
    if (isMember) onDeposit();
    else openAuthModal({ mode: "register", resumeIntent: { action: "deposit", isFirstDeposit: true } });
  };
  const guardedWallet = (e: React.MouseEvent) => {
    if (!isMember) {
      e.preventDefault();
      openAuthModal({ mode: "login", resumeIntent: { action: "none" } });
    }
  };
  const guardedAccount = (e: React.MouseEvent) => {
    if (!isMember) {
      e.preventDefault();
      openAuthModal({ mode: "login", resumeIntent: { action: "none" } });
    }
  };

  return (
    <nav className="shell-bottom-tab-bar" aria-label="Điều hướng chính">
      <Link
        className={["shell-bottom-tab-bar-tab", isActive("/") ? "shell-bottom-tab-bar-active" : ""].filter(Boolean).join(" ")}
        href="/"
        aria-current={isActive("/") ? "page" : undefined}
        onClick={(e) => {
          // Trang chủ tap while already on `/` → CategorySheet, not a no-op
          if (pathname === "/") {
            e.preventDefault();
            onHomeTap();
          }
        }}
      >
        <Icon name="home" size={22} />
        <span className="shell-bottom-tab-bar-label">{vi.nav.home}</span>
      </Link>

      <Link
        className={["shell-bottom-tab-bar-tab", isActive("/khuyen-mai") ? "shell-bottom-tab-bar-active" : ""].filter(Boolean).join(" ")}
        href="/khuyen-mai"
        aria-current={isActive("/khuyen-mai") ? "page" : undefined}
      >
        <Icon name="promo" size={22} />
        <span className="shell-bottom-tab-bar-label">{vi.nav.promo}</span>
      </Link>

      {/* center raised NẠP */}
      <button type="button" className="shell-bottom-tab-bar-deposit" onClick={guardedDeposit}>
        <span className="shell-bottom-tab-bar-deposit-circle">
          <Icon name="deposit" size={26} />
        </span>
        <span className="shell-bottom-tab-bar-deposit-label">{vi.nav.deposit}</span>
      </button>

      <Link
        className={["shell-bottom-tab-bar-tab", isActive("/vi-tien") ? "shell-bottom-tab-bar-active" : ""].filter(Boolean).join(" ")}
        href="/vi-tien"
        aria-current={isActive("/vi-tien") ? "page" : undefined}
        onClick={guardedWallet}
      >
        <Icon name="wallet" size={22} />
        <span className="shell-bottom-tab-bar-label">{vi.nav.wallet}</span>
      </Link>

      <Link
        className={["shell-bottom-tab-bar-tab", isActive("/tai-khoan") ? "shell-bottom-tab-bar-active" : ""].filter(Boolean).join(" ")}
        href="/tai-khoan"
        aria-current={isActive("/tai-khoan") ? "page" : undefined}
        onClick={guardedAccount}
      >
        <Icon name="account" size={22} />
        <span className="shell-bottom-tab-bar-label">{vi.nav.account}</span>
      </Link>
    </nav>
  );
}
