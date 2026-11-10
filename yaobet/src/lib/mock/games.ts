/* Yaobet mock — games / providers / brand showcase.
 *
 * REAL ART: every tile points at the USER'S served
 * landscape key-art under /assets/casino/*. The single grey PLACEHOLDER
 * constant that produced the wireframe look is GONE. The 5 source landscapes
 * are cycled/duplicated to fill the 8-up lobby grid (root-cause explicitly
 * permits duplicates) so no cell is ever a grey token-gradient slot.
 *
 * Tile.tsx:51 already prefers `imageSrc` → zero component change; this is a
 * data-layer-only fix. Names are real-looking, truthful-SHAPED Vietnamese
 * titles (mock 'server' values), never client-fabricated live figures. */

import type { GameTile, Provider } from "../types";
import { simulateFetch } from "./helpers";

/* The user's served casino key-art (clean names; ignore the (1) duplicates). */
const ART = {
  baccarat: "/assets/casino/mg_baccarat_landscape.png",
  roulette: "/assets/casino/mg_roulette_landscape.png",
  sicbo: "/assets/casino/mg_sicbo_landscape.png",
  keno: "/assets/casino/keno_vietlott.png",
  taixiu: "/assets/casino/sunwin_taixiu-live-landscape.png",
} as const;

/** The live-dealer feature tile (the 418px feature slot, §3.3). */
export const FEATURE_GAME_ART = ART.taixiu;

/* Provider logos: no user logo asset maps → honest reserved slot (§3.5). */
const PROVIDER_LOGO = "/assets/placeholders/tile.svg";

const PROVIDERS: Provider[] = [
  { id: "pg", name: "PG Soft", logoSrc: PROVIDER_LOGO },
  { id: "pp", name: "Pragmatic", logoSrc: PROVIDER_LOGO },
  { id: "jili", name: "JILI", logoSrc: PROVIDER_LOGO },
  { id: "cq9", name: "CQ9", logoSrc: PROVIDER_LOGO },
  { id: "evo", name: "Evolution", logoSrc: PROVIDER_LOGO },
  { id: "sexy", name: "Sexy", logoSrc: PROVIDER_LOGO },
];

/* Real-looking lobby roster: each entry carries genuine art + a truthful VN
 * title + provider. The art cycles across the 5 landscapes so a full 8-up grid
 * (and the [vertical] route's longer grids) is fully populated with cover art.
 * Lucky 6/8 figures elsewhere; here the count is 16 (a full 8-up double-row). */
type Seed = { name: string; art: string; provider: string };
const SEEDS: Seed[] = [
  { name: "Baccarat Kim Cương", art: ART.baccarat, provider: "Evolution" },
  { name: "Tài Xỉu Trực Tiếp", art: ART.taixiu, provider: "Sexy" },
  { name: "Roulette Châu Âu", art: ART.roulette, provider: "Evolution" },
  { name: "Sicbo May Mắn", art: ART.sicbo, provider: "PG Soft" },
  { name: "Keno Vietlott", art: ART.keno, provider: "JILI" },
  { name: "Baccarat Tốc Hành", art: ART.baccarat, provider: "Pragmatic" },
  { name: "Tài Xỉu Sunwin", art: ART.taixiu, provider: "CQ9" },
  { name: "Roulette Vàng", art: ART.roulette, provider: "Evolution" },
  { name: "Sicbo Lộc Phát", art: ART.sicbo, provider: "JILI" },
  { name: "Keno Siêu Tốc", art: ART.keno, provider: "PG Soft" },
  { name: "Baccarat VIP", art: ART.baccarat, provider: "Sexy" },
  { name: "Tài Xỉu Phú Quý", art: ART.taixiu, provider: "Pragmatic" },
  { name: "Roulette Kim Cương", art: ART.roulette, provider: "CQ9" },
  { name: "Sicbo Tài Lộc", art: ART.sicbo, provider: "Evolution" },
  { name: "Keno Thần Tài", art: ART.keno, provider: "JILI" },
  { name: "Baccarat Hoàng Gia", art: ART.baccarat, provider: "Sexy" },
];

const GAMES: GameTile[] = SEEDS.map((s, i) => ({
  id: `g${i + 1}`,
  name: s.name,
  imageSrc: s.art,
  provider: s.provider,
}));

export async function getProviders(): Promise<Provider[]> {
  return simulateFetch(PROVIDERS);
}

export async function getGames(): Promise<GameTile[]> {
  return simulateFetch(GAMES);
}
