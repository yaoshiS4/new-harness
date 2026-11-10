/* ============================================================================
 * Footer — reference-exact site footer. Structure transcribed from the reference's
 * real markup (sources/VIP.html .footer_wrap):
 *
 *   .footer_wrap (bg --surface, padding 32px 0 16px)
 *     .footer-box (1424px, flex — equal columns, each grid gap:16px)
 *       col 1  Đối tác / Partners   — partner-logo band (.bottom-box)
 *       col 2  Về chúng tôi / About — 4 socials (.bottom-box.connect, img 30px)
 *       col 3  Yaobet               — text link list (.bottom-box.text, --text-mid)
 *       col 4  Chơi game có trách nhiệm — RG column
 *     <p class="bottom"> copyright
 *
 * Vietnamese-first copy from lib/i18n. The RG column is the
 * addition to the reference's 3-col band (dedicated, never buried, plain VN):
 * it carries the same 18+ / limits / self-exclusion / hotline / T&C content the
 * home footer shipped, so this single app-wide footer fully replaces the in-page
 * HomeFooter (the hoist anticipated in HomeFooter's own note).
 *
 * Partner imagery reuses the user's owned assets (sports/casino — duplicates OK).
 * Socials are inline self-contained SVGs (no network request, CSP-safe).
 * UI-only / mock; links are placeholders.
 * ==========================================================================*/

import type { ReactNode } from "react";
import Link from "next/link";
import { vi } from "@/lib/i18n";
import { Icon } from "@/ui/Icon/Icon";

/* Reference .footer-box col-1 partner band — reuse owned provider art (duplicates OK).
 * These stand in for the reference's partner/sponsor lockups (e.g. its FIBA/club marks). */
const PARTNERS: { src: string; alt: string }[] = [
  { src: "/assets/sports/saba-sports.png", alt: "Saba Sports" },
  { src: "/assets/sports/k-sports.png", alt: "K-Sports" },
  { src: "/assets/casino/mg_baccarat_landscape.png", alt: "Microgaming" },
];

/* Reference .footer-box col-3 link list (.bottom-box.text). UI-only placeholders. The
 * game-contribution rate table (/cuoc-hop-le) is a standalone reference / T&C
 * surface CS can link to — the freshness stamp is repeated there. */
const BRAND_LINKS: { href: string; label: string }[] = [
  { href: "/tai-app", label: vi.footer.appDownload },
  { href: "/phong-cach", label: vi.footer.glamor },
  { href: "/gioi-thieu", label: vi.footer.about },
  { href: "/cuoc-hop-le", label: vi.contribution.footerLink },
  { href: "/cuoc-hop-le?tab=han-che", label: vi.restricted.footerLink },
  { href: "/tro-giup", label: vi.footer.helpCenter },
];

/* Inline social glyphs (24×24, currentColor) — self-contained, no remote fetch.
 * The reference's col-2 .connect: Facebook, YouTube, TikTok, Instagram, img width:30px. */
const SOCIALS: { id: string; href: string; label: string; path: ReactNode }[] = [
  {
    id: "facebook",
    href: "https://facebook.com/",
    label: "Facebook",
    path: (
      <path
        d="M22 12a10 10 0 1 0-11.56 9.88v-6.99H7.9V12h2.54V9.8c0-2.5 1.49-3.89 3.78-3.89 1.09 0 2.24.2 2.24.2v2.46h-1.26c-1.24 0-1.63.77-1.63 1.56V12h2.78l-.44 2.89h-2.34v6.99A10 10 0 0 0 22 12z"
        fill="currentColor"
      />
    ),
  },
  {
    id: "youtube",
    href: "https://youtube.com/",
    label: "YouTube",
    path: (
      <path
        d="M21.6 7.2a2.6 2.6 0 0 0-1.83-1.84C18.16 4.92 12 4.92 12 4.92s-6.16 0-7.77.44A2.6 2.6 0 0 0 2.4 7.2 27 27 0 0 0 2 12a27 27 0 0 0 .4 4.8 2.6 2.6 0 0 0 1.83 1.84c1.61.44 7.77.44 7.77.44s6.16 0 7.77-.44A2.6 2.6 0 0 0 21.6 16.8 27 27 0 0 0 22 12a27 27 0 0 0-.4-4.8zM10 15V9l5.2 3z"
        fill="currentColor"
      />
    ),
  },
  {
    id: "tiktok",
    href: "https://tiktok.com/",
    label: "TikTok",
    path: (
      <path
        d="M16.5 3c.3 2.1 1.5 3.4 3.5 3.6v2.5c-1.2.1-2.4-.2-3.5-.8v5.7a5.6 5.6 0 1 1-5.6-5.6c.3 0 .6 0 .9.1v2.6a3 3 0 1 0 2.1 2.9V3z"
        fill="currentColor"
      />
    ),
  },
  {
    id: "instagram",
    href: "https://instagram.com/",
    label: "Instagram",
    path: (
      <path
        d="M12 7.4A4.6 4.6 0 1 0 12 16.6 4.6 4.6 0 0 0 12 7.4zm0 7.6A3 3 0 1 1 12 9a3 3 0 0 1 0 6zm5.8-7.8a1.07 1.07 0 1 1-2.14 0 1.07 1.07 0 0 1 2.14 0zM21 7.85c-.05-1.43-.38-2.7-1.43-3.74C18.53 3.06 17.26 2.73 15.83 2.66 14.36 2.58 9.64 2.58 8.17 2.66 6.74 2.73 5.48 3.06 4.43 4.11 3.38 5.15 3.06 6.42 2.99 7.85c-.08 1.47-.08 6.18 0 7.65.05 1.43.38 2.7 1.43 3.74 1.05 1.05 2.31 1.38 3.74 1.45 1.47.08 6.19.08 7.66 0 1.43-.05 2.7-.38 3.74-1.43 1.05-1.05 1.38-2.31 1.43-3.74.08-1.47.08-6.18 0-7.65zm-1.9 9.23a3.04 3.04 0 0 1-1.71 1.71c-1.18.47-3.99.36-5.31.36s-4.13.1-5.31-.36a3.04 3.04 0 0 1-1.71-1.71c-.47-1.18-.36-3.99-.36-5.31s-.1-4.13.36-5.31a3.04 3.04 0 0 1 1.71-1.71c1.18-.47 3.99-.36 5.31-.36s4.13-.1 5.31.36a3.04 3.04 0 0 1 1.71 1.71c.47 1.18.36 3.99.36 5.31s.11 4.13-.36 5.31z"
        fill="currentColor"
      />
    ),
  },
];

export function Footer() {
  return (
    <footer className="shell-footer">
      <div className="shell-footer-footer-box">
        {/* col 1 — Đối tác / Partners */}
        <div className="shell-footer-col">
          <div className="shell-footer-title">{vi.footer.partners}</div>
          <div className="shell-footer-bottom-box">
            {PARTNERS.map((p) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img key={p.src} src={p.src} alt={p.alt} className="shell-footer-partner" />
            ))}
          </div>
        </div>

        {/* col 2 — Về chúng tôi / About + socials */}
        <div className="shell-footer-col">
          <div className="shell-footer-title">{vi.footer.aboutUs}</div>
          <div className="shell-footer-bottom-box shell-footer-connect">
            {SOCIALS.map((s) => (
              <a
                key={s.id}
                href={s.href}
                target="_blank"
                rel="noopener noreferrer"
                className="shell-footer-social"
                aria-label={s.label}
              >
                <svg viewBox="0 0 24 24" width={30} height={30} aria-hidden="true" focusable="false">
                  {s.path}
                </svg>
              </a>
            ))}
          </div>
        </div>

        {/* col 3 — Yaobet brand link list */}
        <div className="shell-footer-col">
          <div className="shell-footer-title">{vi.footer.brandCol}</div>
          <div className="shell-footer-bottom-box shell-footer-text">
            {BRAND_LINKS.map((l) => (
              <Link key={l.href} href={l.href} className="shell-footer-text-link">
                {l.label}
              </Link>
            ))}
          </div>
        </div>

        {/* col 4 — RG column (never buried, plain VN) */}
        <section className="shell-footer-col shell-footer-rg" aria-label={vi.rg.columnTitle}>
          <div className="shell-footer-title">
            <Icon name="shield" size={18} className="shell-footer-rg-icon" />
            {vi.rg.columnTitle}
          </div>
          <div className="shell-footer-rg-body">
            <span className="shell-footer-age-mark">18+</span>
            <ul className="shell-footer-rg-list">
              <li>{vi.rg.ageLimit}</li>
              <li>{vi.rg.limits}</li>
              <li><Link href="/tai-khoan" className="shell-footer-rg-link">{vi.rg.selfExclusion}</Link></li>
              <li>{vi.rg.hotline}: 1900 0000</li>
              <li><Link href="/khuyen-mai" className="shell-footer-rg-link">{vi.rg.terms}</Link></li>
            </ul>
          </div>
        </section>
      </div>

      <p className="shell-footer-copyright">{vi.footer.copyright}</p>
    </footer>
  );
}
