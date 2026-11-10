/* ============================================================================
 * Yaobet — ROOT layout
 * ----------------------------------------------------------------------------
 * <html lang="vi" data-brand="yaobet"> — Vietnamese-first, default Yaobet
 * brand, Wine-Gold :root theme (obsidian is opt-in via [data-theme]). Imports
 * the single global token sheet and wraps the tree in <Providers> (MockAuth +
 * AuthModal).
 *
 * <AppShell> (two-tier Header + CategoryRail/Sheet + BottomTabBar + AuthModal,
 * with Footer/SupportWidget slots owned by their agents) composes BELOW
 * <Providers> so the whole tree sits under one client-context root while the
 * shell itself stays a Server Component that fetches its truthful data (§F).
 * ==========================================================================*/

import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { Providers } from "./providers";
import { AppShell, Footer } from "@/components/layout";
import { QuickActionRail } from "@/components/layout/QuickActionRail";

/* The display face (--brand-font-display -> --font-head) is Playfair Display
 * because it ships a `vietnamese` subset. A latin-only display face drops
 * U+1EA0–1EF1 mid-word (`Đồng` loses `ồ`, `Bạc` loses `ạ` on /vip). */

/* ---- The Vietnamese-complete app faces ------------------------------------
 * The WOFF2 files are self-hosted under ./fonts (source URLs and sha256 in
 * ./fonts/SOURCE.md), so builds are offline and byte-stable. Each
 * family loads as one localFont call per subset (latin, latin-ext,
 * vietnamese). The calls share the real family name and carry Google's
 * unicode-range, so the browser fetches only the slices a page uses and
 * every toned vowel (Ộ ổ ậ ư ợ …) resolves INSIDE the face, with no mid-word
 * fallback anywhere in the product. Outfit is rejected outright: it ships
 * latin/latin-ext only and skips U+1EA0–1EF1.
 * The latin call of each family owns the CSS variable, consumed through
 * tokens.css → --wg-type-family-* → --font-body / --font-num / --font-head →
 * --brand-font-*. Latin and vietnamese files are preloaded; latin-ext is
 * not. The three app faces load 400/500/600 only, so nothing asks for a
 * synthesized 700. */

/* Body, h2-h6 and uppercase labels. */
const beVietnamPro = localFont({
  src: [
    { path: "./fonts/be-vietnam-pro/latin-400.woff2", weight: "400", style: "normal" },
    { path: "./fonts/be-vietnam-pro/latin-500.woff2", weight: "500", style: "normal" },
    { path: "./fonts/be-vietnam-pro/latin-600.woff2", weight: "600", style: "normal" },
  ],
  variable: "--font-be-vietnam",
  display: "swap",
  declarations: [
    { prop: "font-family", value: "'Be Vietnam Pro'" },
    {
      prop: "unicode-range",
      value:
        "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
    },
  ],
});

const beVietnamProLatinExt = localFont({
  src: [
    { path: "./fonts/be-vietnam-pro/latin-ext-400.woff2", weight: "400", style: "normal" },
    { path: "./fonts/be-vietnam-pro/latin-ext-500.woff2", weight: "500", style: "normal" },
    { path: "./fonts/be-vietnam-pro/latin-ext-600.woff2", weight: "600", style: "normal" },
  ],
  display: "swap",
  preload: false,
  declarations: [
    { prop: "font-family", value: "'Be Vietnam Pro'" },
    {
      prop: "unicode-range",
      value:
        "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF",
    },
  ],
});

const beVietnamProVietnamese = localFont({
  src: [
    { path: "./fonts/be-vietnam-pro/vietnamese-400.woff2", weight: "400", style: "normal" },
    { path: "./fonts/be-vietnam-pro/vietnamese-500.woff2", weight: "500", style: "normal" },
    { path: "./fonts/be-vietnam-pro/vietnamese-600.woff2", weight: "600", style: "normal" },
  ],
  display: "swap",
  declarations: [
    { prop: "font-family", value: "'Be Vietnam Pro'" },
    {
      prop: "unicode-range",
      value:
        "U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB",
    },
  ],
});

/* Display: h1 and /vip headings. */
const playfairDisplay = localFont({
  src: [
    { path: "./fonts/playfair-display/latin.woff2", weight: "400", style: "normal" },
    { path: "./fonts/playfair-display/latin.woff2", weight: "500", style: "normal" },
    { path: "./fonts/playfair-display/latin.woff2", weight: "600", style: "normal" },
  ],
  variable: "--font-playfair",
  display: "swap",
  declarations: [
    { prop: "font-family", value: "'Playfair Display'" },
    {
      prop: "unicode-range",
      value:
        "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
    },
  ],
});

const playfairDisplayLatinExt = localFont({
  src: [
    { path: "./fonts/playfair-display/latin-ext.woff2", weight: "400", style: "normal" },
    { path: "./fonts/playfair-display/latin-ext.woff2", weight: "500", style: "normal" },
    { path: "./fonts/playfair-display/latin-ext.woff2", weight: "600", style: "normal" },
  ],
  display: "swap",
  preload: false,
  declarations: [
    { prop: "font-family", value: "'Playfair Display'" },
    {
      prop: "unicode-range",
      value:
        "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF",
    },
  ],
});

const playfairDisplayVietnamese = localFont({
  src: [
    { path: "./fonts/playfair-display/vietnamese.woff2", weight: "400", style: "normal" },
    { path: "./fonts/playfair-display/vietnamese.woff2", weight: "500", style: "normal" },
    { path: "./fonts/playfair-display/vietnamese.woff2", weight: "600", style: "normal" },
  ],
  display: "swap",
  declarations: [
    { prop: "font-family", value: "'Playfair Display'" },
    {
      prop: "unicode-range",
      value:
        "U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB",
    },
  ],
});

/* Tabular numerals (money, odds, counters). */
const inter = localFont({
  src: [
    { path: "./fonts/inter/latin.woff2", weight: "400", style: "normal" },
    { path: "./fonts/inter/latin.woff2", weight: "500", style: "normal" },
    { path: "./fonts/inter/latin.woff2", weight: "600", style: "normal" },
  ],
  variable: "--font-inter",
  display: "swap",
  declarations: [
    { prop: "font-family", value: "'Inter'" },
    {
      prop: "unicode-range",
      value:
        "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
    },
  ],
});

const interLatinExt = localFont({
  src: [
    { path: "./fonts/inter/latin-ext.woff2", weight: "400", style: "normal" },
    { path: "./fonts/inter/latin-ext.woff2", weight: "500", style: "normal" },
    { path: "./fonts/inter/latin-ext.woff2", weight: "600", style: "normal" },
  ],
  display: "swap",
  preload: false,
  declarations: [
    { prop: "font-family", value: "'Inter'" },
    {
      prop: "unicode-range",
      value:
        "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF",
    },
  ],
});

const interVietnamese = localFont({
  src: [
    { path: "./fonts/inter/vietnamese.woff2", weight: "400", style: "normal" },
    { path: "./fonts/inter/vietnamese.woff2", weight: "500", style: "normal" },
    { path: "./fonts/inter/vietnamese.woff2", weight: "600", style: "normal" },
  ],
  display: "swap",
  declarations: [
    { prop: "font-family", value: "'Inter'" },
    {
      prop: "unicode-range",
      value:
        "U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB",
    },
  ],
});

/* The emerald brand keeps Montserrat for headings and display (brands.css).
 * Only that brand reads it, so none of its files is preloaded. */
const montserrat = localFont({
  src: [
    { path: "./fonts/montserrat/latin.woff2", weight: "700", style: "normal" },
    { path: "./fonts/montserrat/latin.woff2", weight: "800", style: "normal" },
  ],
  variable: "--font-montserrat",
  display: "swap",
  preload: false,
  declarations: [
    { prop: "font-family", value: "'Montserrat'" },
    {
      prop: "unicode-range",
      value:
        "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
    },
  ],
});

const montserratLatinExt = localFont({
  src: [
    { path: "./fonts/montserrat/latin-ext.woff2", weight: "700", style: "normal" },
    { path: "./fonts/montserrat/latin-ext.woff2", weight: "800", style: "normal" },
  ],
  display: "swap",
  preload: false,
  declarations: [
    { prop: "font-family", value: "'Montserrat'" },
    {
      prop: "unicode-range",
      value:
        "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF",
    },
  ],
});

const montserratVietnamese = localFont({
  src: [
    { path: "./fonts/montserrat/vietnamese.woff2", weight: "700", style: "normal" },
    { path: "./fonts/montserrat/vietnamese.woff2", weight: "800", style: "normal" },
  ],
  display: "swap",
  preload: false,
  declarations: [
    { prop: "font-family", value: "'Montserrat'" },
    {
      prop: "unicode-range",
      value:
        "U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB",
    },
  ],
});

export const metadata: Metadata = {
  title: "Yaobet",
  description: "Yaobet — nhà cái trực tuyến.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  // mobile-first @375 base; the browser chrome takes the page primitive,
  // the value --canvas resolves to.
  themeColor: "#1C1A17",
};

/* localFont's `declarations` names every @font-face with the real family,
 * while each `.variable` class carries the loader's generated family name.
 * These inline values put the real family first and keep the generated
 * stack, with its size-adjusted fallback face, behind it. */
const fontVariables = {
  "--font-be-vietnam": `'Be Vietnam Pro', ${beVietnamPro.style.fontFamily}`,
  "--font-playfair": `'Playfair Display', ${playfairDisplay.style.fontFamily}`,
  "--font-inter": `'Inter', ${inter.style.fontFamily}`,
  "--font-montserrat": `'Montserrat', ${montserrat.style.fontFamily}`,
} as React.CSSProperties;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="vi"
      data-brand="yaobet"
      className={`${beVietnamPro.variable} ${playfairDisplay.variable} ${inter.variable} ${montserrat.variable}`}
      style={fontVariables}
    >
      <body>
        <Providers>
          <AppShell footer={<Footer />}>{children}</AppShell>
          <QuickActionRail />
        </Providers>
      </body>
    </html>
  );
}
