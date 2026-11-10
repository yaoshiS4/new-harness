/* ============================================================================
 * MemberSidebar — the LEFT member rail hosted ONCE by (member)/layout.tsx so
 * every member surface (/tai-khoan, /vi-tien, …) shares it (.user_info_box +
 * .memberMenu, profile.html). A client island: reads the mock session (useAuth)
 * and the active route (usePathname) for menu highlighting.
 *
 * Composition (top → bottom) — the signature premium member stack:
 *   1. PROFILE CARD — identity + membership progress (.user_info_box):
 *                     · identity     — avatar initial · displayName · tier
 *                       ribbon Badge · verified/activation status chip ·
 *                       copyable ID chip · "Nhận huy hiệu" link (→ /vip)
 *                     · progress bar — membership track (header anchor):
 *                       groove + brand-accent fill + glowing dot + next-tier
 *                       pill + caption. Envelope-gated (live only).
 *   2. WALLET CARD  — its OWN card (NOT fused into the profile): the
 *                     "Ví của tôi" title + near-white balance + Nạp/Rút.
 *   3. ACTION CARDS — 2-up style cards: Cửa hàng điểm (→ /cua-hang) ·
 *                     Trung tâm nhiệm vụ (→ /hoan-tra).
 *   4. ICON GRID  — 12 tiles, 3-col × 4-row (.menu_box reconciled to real
 *                   routes). Tin nhắn carries a red unread dot; Bảo mật is a
 *                   persistent gold-active tile when user.verified.
 *   5. LOGOUT ROW — <LogoutButton/> full-width, OUTSIDE the grid.
 *
 * Truthful-only (§F): a guest sees an honest login prompt (no fabricated
 * identity/balance/points/progress); the live balance arrives as a §F Envelope,
 * the membership progress as its OWN §F Envelope, and the account summary as a
 * typed fixture — the island cannot invent a figure it never receives. The
 * progress bar renders a fill ONLY when progress.status==='live'; loading → a
 * neutral skeleton groove; absent/error → a quiet "đang cập nhật" with an empty
 * track and NO fabricated fill. Money renders on the equal-salience role.
 * ==========================================================================*/

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth, useRequireAuth } from "@/lib/auth";
import { vi } from "@/lib/i18n";
import { formatVnd, formatCount } from "@/lib/format";
import type {
  AccountSummary,
  Envelope,
  LiveMoney,
  VipProgress,
} from "@/lib/types";
import { Button, Icon, type IconName } from "@/ui";
import { LogoutButton } from "./LogoutButton";

export interface MemberSidebarProps {
  /** live balance envelope (server-issued) — never a client guess. */
  balance: Envelope<LiveMoney>;
  /** points + accrued rebate (truthful fixture). */
  summary: AccountSummary;
  /** membership turnover-to-next-tier (server-issued §F envelope). The bar
   *  renders a live fill ONLY when status==='live'. */
  progress: Envelope<VipProgress>;
}

interface MenuItem {
  id: string;
  label: string;
  icon: IconName;
  href: string;
}

/* The 12-tile grid: the .menu_box reconciled to our REAL routes (no invented
 * destinations). Two mappings are approximate by design — Sinh lời → /hoan-tra
 * and Bán xu → /cua-hang reuse the nearest real economic surface. Bảo mật is
 * an in-page hash section on /tai-khoan (native <a> so hashchange fires). */
const MENU: MenuItem[] = [
  { id: "wallet", label: vi.member.wallet, icon: "wallet", href: "/vi-tien" },
  { id: "cashback", label: vi.member.cashback, icon: "cashback", href: "/hoan-tra" },
  { id: "yield", label: vi.member.yield, icon: "yield", href: "/hoan-tra" },
  { id: "sellCoin", label: vi.member.sellCoin, icon: "card", href: "/cua-hang" },
  { id: "history", label: vi.member.history, icon: "history", href: "/lich-su" },
  { id: "messages", label: vi.member.messages, icon: "message", href: "/tin-nhan" },
  { id: "referral", label: vi.member.referral, icon: "referral", href: "/gioi-thieu" },
  { id: "security", label: vi.member.security, icon: "shield", href: "/tai-khoan#bao-mat" },
  { id: "universalUpgrade", label: vi.member.universalUpgrade, icon: "vip", href: "/vip" },
  { id: "promo", label: vi.member.promo, icon: "gift", href: "/khuyen-mai" },
  { id: "tutorial", label: vi.member.tutorial, icon: "info", href: "/tro-giup" },
  { id: "honor", label: vi.member.honor, icon: "trophy", href: "/cau-lac-bo" },
];

/* ----------------------------------------------------------------------------
 * ProgressBar — the membership track inside the hero (header anchor).
 * Takes the FULL §F envelope and gates rendering on its status: a fill is drawn
 * ONLY for status==='live'. This is the single place the rebuild could regress
 * truthfulness (§F), so the gate lives here, explicit and total.
 * --------------------------------------------------------------------------*/
function ProgressBar({ progress }: { progress: Envelope<VipProgress> }) {
  /* loading → a neutral skeleton groove (no dot, no fill, no caption). */
  if (progress.status === "loading") {
    return (
      <div className="flex flex-col gap-space-2">
        <div className="relative flex-[1_1_auto] min-w-[0] w-full h-[4px] rounded-sm [background-image:linear-gradient(90deg,var(--progress-track)_0%,var(--surface-hover)_50%,var(--progress-track)_100%)] [background-size:200%_100%] motion-safe:animate-[progressShimmer_var(--dur-slow)_var(--ease-standard)_infinite]" aria-hidden="true" />
      </div>
    );
  }

  /* absent / error → an empty track + a quiet "đang cập nhật". NEVER a fill. */
  if (progress.status !== "live") {
    return (
      <div className="flex flex-col gap-space-2">
        <div className="relative flex-[1_1_auto] min-w-[0] w-full h-[4px] rounded-sm [background:var(--progress-track)]" />
        <p className="text-t-micro leading-lh-tight text-text-mid">{vi.account.progressUpdating}</p>
      </div>
    );
  }

  const { current, target, currentTierName, nextTierName } = progress.value;

  /* max tier (nextTierName === null): a full lit track labelled by the current
   * tier; no next-tier tag, no goal caption. */
  if (nextTierName === null) {
    return (
      <div className="flex flex-col gap-space-2">
        <div className="flex items-center gap-space-2">
          <div className="relative flex-[1_1_auto] min-w-[0] w-full h-[4px] rounded-sm [background:var(--progress-track)]">
            <span className="absolute inset-y-[0] left-[0] h-[4px] rounded-sm bg-progress-fill [background-image:var(--progress-fill-grad)]" style={{ width: "100%" }} />
            <span className="absolute top-[50%] w-[6px] h-[6px] rounded-pill [background:var(--progress-dot)] [transform:translate(-50%,-50%)] motion-safe:animate-[pulseDot_1.6s_var(--ease-standard)_infinite_alternate]" style={{ left: "100%" }} aria-hidden="true" />
          </div>
          <span className="inline-flex items-center py-[3px] pr-space-2 pl-[11px] [clip-path:polygon(0_0,100%_0,100%_100%,0_100%,6px_50%)] [background:color-mix(in_srgb,var(--brand-accent)_14%,var(--surface-3))] text-progress-tag-text text-t-micro font-weight-semi leading-lh-tight whitespace-nowrap">{currentTierName}</span>
        </div>
      </div>
    );
  }

  /* clamped live percentage — the ONLY inline style; everything else is class
   * driven. Guard target<=0 so a malformed seam never divides by zero. */
  const pct =
    target > 0 ? Math.min(100, Math.max(0, (current / target) * 100)) : 0;
  const remaining = Math.max(0, target - current);

  return (
    <div className="flex flex-col gap-space-2">
      <div className="flex items-center gap-space-2">
        <div
          className="relative flex-[1_1_auto] min-w-[0] w-full h-[4px] rounded-sm [background:var(--progress-track)]"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(pct)}
          aria-label={`${currentTierName} → ${nextTierName}`}
        >
          <span className="absolute inset-y-[0] left-[0] h-[4px] rounded-sm bg-progress-fill [background-image:var(--progress-fill-grad)]" style={{ width: `${pct}%` }} />
          <span className="absolute top-[50%] w-[6px] h-[6px] rounded-pill [background:var(--progress-dot)] [transform:translate(-50%,-50%)] motion-safe:animate-[pulseDot_1.6s_var(--ease-standard)_infinite_alternate]" style={{ left: `${pct}%` }} aria-hidden="true" />
        </div>
        <span className="inline-flex items-center py-[3px] pr-space-2 pl-[11px] [clip-path:polygon(0_0,100%_0,100%_100%,0_100%,6px_50%)] [background:color-mix(in_srgb,var(--brand-accent)_14%,var(--surface-3))] text-progress-tag-text text-t-micro font-weight-semi leading-lh-tight whitespace-nowrap">{nextTierName}</span>
      </div>
      <p className="text-t-micro leading-lh-tight text-text-mid">
        {vi.account.progressPrefix} {formatVnd(remaining)} {vi.account.progressSuffix}{" "}
        <span className="text-brand-accent-fg font-weight-semi">{nextTierName}</span>
      </p>
    </div>
  );
}

export function MemberSidebar({ balance, summary, progress }: MemberSidebarProps) {
  const { user } = useAuth();
  const { allowed, promptAuth } = useRequireAuth();
  const pathname = usePathname();
  const [copied, setCopied] = useState(false);
  const [hash, setHash] = useState("");

  /* track the active member-section hash so the right tile highlights (the
   * content column swaps by hash; pathname alone can't tell sections apart). */
  useEffect(() => {
    const sync = () => setHash(window.location.hash.replace(/^#/, ""));
    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  /* ---- guest: honest prompt, no fabricated identity/balance/progress ---- */
  if (!allowed || !user) {
    return (
      <aside className="flex flex-col gap-space-4 w-full min-w-[0] min-[992px]:w-rail-w min-[992px]:sticky min-[992px]:top-[calc(var(--header-h)+var(--nav-h)+var(--space-4))]" aria-label={vi.nav.account}>
        <div className="flex flex-col items-center gap-space-3 p-card-pad [background:var(--surface)] border border-border rounded-card text-center">
          <span className="w-[44px] h-[44px] grid place-items-center rounded-pill [background:var(--surface-3)] [border:1px_solid_var(--brand-accent-hairline)] text-brand-accent-fg" aria-hidden="true">
            <Icon name="user" size={28} />
          </span>
          <p className="text-t-h3 font-weight-semi text-text-hi">Khách</p>
          <p className="text-t-sm text-text-mid leading-lh-body">
            {vi.auth.login} để xem tài khoản của bạn.
          </p>
          <Button variant="primary" size="md" fullWidth onClick={() => promptAuth()}>
            {vi.auth.login}
          </Button>
        </div>
      </aside>
    );
  }

  const copyId = async () => {
    try {
      await navigator.clipboard.writeText(user.memberId);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  const tierLabel = user.vipLevel === 0 ? vi.account.newMember : user.vipTierName;

  return (
    <aside className="flex flex-col gap-space-4 w-full min-w-[0] min-[992px]:w-rail-w min-[992px]:sticky min-[992px]:top-[calc(var(--header-h)+var(--nav-h)+var(--space-4))]" aria-label={vi.nav.account}>
      {/* 1. PROFILE CARD — identity + membership progress (.user_info_box).
       *  Wallet is a SEPARATE card (below), not fused here. */}
      <section className="relative isolate overflow-hidden flex flex-col gap-space-4 p-card-pad-sm [background:var(--header-card-grad)] border border-brand-accent-hairline rounded-card">
        {/* corner sheen — the ice-white upper-right glow */}
        <span className="absolute inset-[0] -z-1 pointer-events-none [background:var(--card-sheen-grad)]" aria-hidden="true" />

        {/* top-right corner — "Nhận huy hiệu" on its OWN row (never the name
         *  line: the medal link sits in the card's top-right corner). */}
        <div className="flex justify-end">
          <Link href="/vip" className="inline-flex items-center gap-space-1 m-[calc(var(--space-1)*-1)_calc(var(--space-1)*-1)_0_0] py-space-1 px-space-2 rounded-pill text-brand-accent-fg text-t-micro font-weight-semi no-underline whitespace-nowrap [transition:background_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--brand-accent-hairline)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2">
            <Icon name="trophy" size={14} />
            <span>{vi.account.getBadge}</span>
            <Icon name="chevronRight" size={14} />
          </Link>
        </div>

        {/* identity — avatar (with a verified check overlay) + name·tier on one
         *  line + plain-text ID (no chip), per .user_info. */}
        <div className="flex items-center gap-space-3 min-w-[0]">
          <span className="relative flex-[0_0_auto]">
            <span className="w-[44px] h-[44px] grid place-items-center rounded-pill [background:var(--surface-3)] [border:1px_solid_var(--brand-accent-hairline)] text-brand-accent-fg" aria-hidden="true">
              <span className="text-t-h3 font-weight-bold font-brand-font-num">
                {user.displayName.trim().charAt(0).toUpperCase() || "Y"}
              </span>
            </span>
            {user.verified && (
              <span
                className="absolute right-[-2px] bottom-[-2px] grid place-items-center w-[18px] h-[18px] rounded-pill [background:var(--green)] text-brand-on-accent [border:2px_solid_var(--surface)]"
                title={vi.account.statusVerified}
              >
                <Icon name="check" size={11} />
              </span>
            )}
          </span>

          <div className="flex flex-col gap-space-1 min-w-[0]">
            <div className="flex items-center gap-space-2 min-w-[0]">
              <span className="min-w-[0] text-t-body font-weight-semi text-text-hi overflow-hidden text-ellipsis whitespace-nowrap">{user.displayName}</span>
              <span className="flex-[0_0_auto] inline-flex items-center py-[2px] pr-space-2 pl-[11px] [clip-path:polygon(0_0,100%_0,100%_100%,0_100%,6px_50%)] [background:var(--brand-accent)] text-brand-on-accent text-t-micro font-weight-bold leading-lh-tight tracking-[0.01em] whitespace-nowrap">{tierLabel}</span>
            </div>

            <button type="button" className="relative inline-flex items-center gap-space-1 p-[0] [border:0] [background:none] text-text-mid text-t-sm cursor-pointer w-max max-w-full whitespace-nowrap [transition:color_var(--dur-fast)_var(--ease-standard)] hover:text-brand-accent-fg" onClick={copyId}>
              <span className="text-text-dim">ID</span>
              <span className="font-brand-font-num text-text tracking-[0.02em]">{user.memberId}</span>
              <Icon name="copy" size={13} />
              {copied && <span className="absolute left-[0] bottom-[calc(100%+6px)] py-[2px] px-space-2 [background:var(--shell)] border border-brand-accent-hairline rounded-sm text-brand-accent-fg whitespace-nowrap text-t-micro">Đã sao chép</span>}
            </button>
          </div>
        </div>

        {/* membership progress (envelope-gated) */}
        <ProgressBar progress={progress} />
      </section>

      {/* 2. WALLET CARD — its OWN card, separate from the profile (keeps
       *  .user_info_box and the wallet box distinct). Title + balance + Nạp/Rút. */}
      <section className="relative isolate overflow-hidden flex flex-col gap-space-2 p-card-pad-sm [background:var(--surface)] border border-border rounded-card">
        <span className="absolute inset-[0] -z-1 pointer-events-none [background:var(--wallet-sheen-grad)]" aria-hidden="true" />
        <span className="text-t-sm font-weight-semi text-text-hi">{vi.member.wallet}</span>
        <span className="text-t-balance leading-[1.1] font-weight-bold font-brand-font-num text-balance-text">
          {balance.status === "live"
            ? formatVnd(balance.value)
            : vi.wallet.zeroBalance}
        </span>
        {/* shortcuts: deep-link to /vi-tien and select the matching WalletTabs
         * tab via #hash — never a second set of action buttons. */}
        <div className="relative grid grid-cols-[1fr_1fr] gap-gap-sm mt-space-1">
          <Link href="/vi-tien#deposit" className="inline-flex items-center justify-center gap-space-1 min-h-tap-min rounded-md text-t-sm font-weight-semi no-underline [transition:transform_var(--dur-fast)_var(--ease-standard),background_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 motion-reduce:[transform:none] motion-reduce:hover:[transform:none] [background:var(--brand-accent-grad)] text-brand-on-accent hover:[background:var(--brand-accent-2)]">
            <Icon name="deposit" size={16} />
            <span>{vi.wallet.deposit}</span>
          </Link>
          <Link href="/vi-tien#withdraw" className="inline-flex items-center justify-center gap-space-1 min-h-tap-min rounded-md text-t-sm font-weight-semi no-underline [transition:transform_var(--dur-fast)_var(--ease-standard),background_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 motion-reduce:[transform:none] motion-reduce:hover:[transform:none] [background:var(--surface-3)] text-text border border-border hover:[background:var(--surface-hover)] hover:text-brand-accent-fg hover:border-brand-accent">
            <Icon name="wallet" size={16} />
            <span>{vi.wallet.withdraw}</span>
          </Link>
        </div>
      </section>

      {/* 3. ACTION CARDS — Cửa hàng điểm · Trung tâm nhiệm vụ ---------- */}
      <div className="grid grid-cols-[1fr_1fr] gap-gap-sm">
        <Link href="/cua-hang" className="relative isolate overflow-hidden flex flex-col gap-space-2 min-h-tap-min p-card-pad-sm [background:var(--surface)] border border-border rounded-card no-underline [transition:transform_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),background_var(--dur-fast)_var(--ease-standard)] hover:border-brand-accent hover:[background:var(--surface-hover)] hover:[transform:scale(1.02)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 motion-reduce:[transform:none] motion-reduce:hover:[transform:none]">
          <span className="absolute inset-[0] -z-1 pointer-events-none [background:var(--card-sheen-grad)]" aria-hidden="true" />
          <span className="flex items-center justify-between text-brand-accent-fg">
            <Icon name="gift" size={18} className="text-brand-accent-fg" />
            <Icon name="info" size={14} className="text-text-dim" />
          </span>
          <span className="text-t-sm font-weight-semi text-text-hi leading-lh-tight">{vi.account.pointsStore}</span>
          <span className="flex flex-col gap-[2px]">
            <span className="text-t-micro text-text-mid">{vi.account.myPoints}</span>
            <span className="text-t-body font-weight-bold font-brand-font-num text-text-hi">{formatCount(summary.points)}</span>
          </span>
        </Link>

        <Link href="/hoan-tra" className="relative isolate overflow-hidden flex flex-col gap-space-2 min-h-tap-min p-card-pad-sm [background:var(--surface)] border border-border rounded-card no-underline [transition:transform_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),background_var(--dur-fast)_var(--ease-standard)] hover:border-brand-accent hover:[background:var(--surface-hover)] hover:[transform:scale(1.02)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 motion-reduce:[transform:none] motion-reduce:hover:[transform:none]">
          <span className="absolute inset-[0] -z-1 pointer-events-none [background:var(--card-sheen-grad)]" aria-hidden="true" />
          <span className="flex items-center justify-between text-brand-accent-fg">
            <Icon name="cashback" size={18} className="text-brand-accent-fg" />
          </span>
          <span className="text-t-sm font-weight-semi text-text-hi leading-lh-tight">{vi.account.taskCenter}</span>
          <span className="flex flex-col gap-[2px]">
            <span className="text-t-micro text-text-mid">{vi.account.waitingUnlock}</span>
            <span className="text-t-body font-weight-bold font-brand-font-num text-text-hi">0</span>
          </span>
        </Link>
      </div>

      {/* 4. ICON GRID — 12 tiles (.menu_box) ----------------------- */}
      <nav className="p-card-pad-sm [background:var(--surface)] border border-border rounded-card" aria-label={vi.nav.account}>
        <ul className="grid grid-cols-[repeat(3,1fr)] gap-gap-sm m-[0] p-[0] list-none">
          {MENU.map((m) => {
            const [mPath, mHash = ""] = m.href.split("#");
            const isSection = mPath === "/tai-khoan" && mHash !== "";
            const onAccount = pathname === "/tai-khoan";

            let active: boolean;
            if (isSection && onAccount) {
              active = mHash === hash;
            } else {
              active = m.href === pathname;
            }

            /* Bảo mật is persistently gold-active when the member is verified
             * (the lit shield tile), independent of the current route. */
            const lit = m.id === "security" && user.verified;

            const className = `relative w-full h-[86px] flex flex-col items-center justify-center gap-space-2 rounded-lg border text-t-micro text-center no-underline cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard),background_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard)] hover:text-tab-text-active hover:[background:var(--surface-hover)] hover:border-brand-accent-hairline hover:[transform:scale(1.02)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 motion-reduce:[transform:none] motion-reduce:hover:[transform:none] ${
              lit
                ? "text-tab-text-active [background:color-mix(in_srgb,var(--brand-accent)_8%,var(--surface))] border-brand-accent-hairline"
                : active
                  ? "text-tab-text-active [background:var(--surface-hover)] border-transparent"
                  : "text-tab-text-rest [background:var(--tile)] border-transparent"
            }`;

            const showUnread = m.id === "messages" && user.unreadMessages > 0;

            /* In-page section switch while already on /tai-khoan: use a native
             * anchor. next/link does a soft history.pushState for same-page hash
             * targets and never fires `hashchange`, so the content column + tile
             * highlight (both hash-driven islands) would stay stuck. A native
             * <a href="#…"> mutates the hash through the browser, which DOES fire
             * hashchange. Path-changing tiles keep next/link. */
            const inner = (
              <>
                <span className="relative inline-flex">
                  <Icon name={m.icon} size={24} className="w-[24px] h-[24px]" />
                  {showUnread && <span className="absolute top-[-2px] right-[-4px] w-[8px] h-[8px] rounded-pill [background:var(--loss)] border border-tile" aria-hidden="true" />}
                </span>
                <span className="font-weight-semi leading-lh-tight">{m.label}</span>
              </>
            );

            return (
              <li key={m.id}>
                {isSection && onAccount ? (
                  <a
                    href={`#${mHash}`}
                    className={className}
                    aria-current={active ? "page" : undefined}
                  >
                    {inner}
                  </a>
                ) : (
                  <Link
                    href={m.href}
                    className={className}
                    aria-current={active ? "page" : undefined}
                  >
                    {inner}
                  </Link>
                )}
              </li>
            );
          })}
        </ul>
      </nav>

      {/* 5. LOGOUT ROW — full-width, OUTSIDE the grid ----------------- */}
      <div className="block">
        <LogoutButton />
      </div>
    </aside>
  );
}
