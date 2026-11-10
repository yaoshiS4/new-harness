/* Yaobet mock — promotions. No hardcoded bonus %.
 *
 * HERO ART: the first FIVE promos carry the USER'S
 * real banner JPGs (native ~2.5:1, /assets/banners/*) so HeroBand renders them
 * full-bleed `cover` instead of an empty gradient slot — 5 banner slides → 5
 * navigator items. Only three source JPGs exist, so two
 * slides reuse an existing JPG (duplicate art approved) but each carries a
 * DISTINCT promo title. Remaining promo cards have no user banner asset →
 * honest token slot (§3.5). */

import type { Promo } from "../types";
import { DEMO_EMPTY, isoIn, simulateFetch } from "./helpers";

/* The user's served hero banners (native ~1556×620, 2.5:1). */
const BANNER = {
  welcome: "/assets/banners/hero-banner-1.jpg",
  ucl: "/assets/banners/pc-hero-banner-UCLfinal.jpg",
  vpn: "/assets/banners/pc-banner-vpn.jpg",
} as const;

/* No user banner art maps → honest reserved slot (§3.5). */
const SLOT = "/assets/placeholders/promo.svg";

const PROMOS: Promo[] = [
  /* --- hero carousel slides (real banner art, full-bleed cover) — FIVE
   *     banner-backed promos → 5 hero slides → 5 navigator items. The
   *     two extra slides reuse an existing JPG (approved) with a DISTINCT
   *     title each. --- */
  { id: "pr1", title: "Thưởng chào mừng thành viên mới", category: "Thành viên mới", imageSrc: BANNER.welcome, endsAt: null, href: "/khuyen-mai/pr1" },
  { id: "pr2", title: "Cúp C1 Châu Âu — Đặt cược nhận thưởng", category: "Thể thao", imageSrc: BANNER.ucl, endsAt: isoIn(2880), href: "/khuyen-mai/pr2" },
  { id: "pr3", title: "Tải app — Tăng tốc & bảo mật", category: "Sự kiện", imageSrc: BANNER.vpn, endsAt: null, href: "/khuyen-mai/pr3" },
  { id: "pr7", title: "Hoàn trả mỗi ngày — Cược càng nhiều, nhận càng cao", category: "Hoàn trả", imageSrc: BANNER.welcome, endsAt: null, href: "/khuyen-mai/pr7" },
  { id: "pr8", title: "Vòng quay vàng — Trúng thưởng cực lớn", category: "Sự kiện", imageSrc: BANNER.ucl, endsAt: isoIn(1440), href: "/khuyen-mai/pr8" },

  /* --- promo-grid cards (honest token slot; no user banner art) --- */
  { id: "pr4", title: "Hoàn trả không giới hạn", category: "Hoàn trả", imageSrc: SLOT, endsAt: null, href: "/khuyen-mai/pr4" },
  { id: "pr5", title: "Vòng quay may mắn mỗi ngày", category: "Sự kiện", imageSrc: SLOT, endsAt: isoIn(660), href: "/khuyen-mai/pr5" },
  { id: "pr6", title: "Nạp lần đầu — Quà tặng đặc biệt", category: "Nạp tiền", imageSrc: SLOT, endsAt: null, href: "/khuyen-mai/pr6" },
];

export async function getPromos(): Promise<Promo[]> {
  return simulateFetch(DEMO_EMPTY ? [] : PROMOS);
}
