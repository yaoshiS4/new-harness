# Assets inventory and usage map

Owner-supplied on 2026-11-04, served from `public/assets/` as `/assets/...`. Rights: supplied by the owner; third-party provider and game marks (MG, Sunwin, Saba, K-Sports, Vietlott, Betgaming) are used only because the owner supplied them, and clearance is the owner's confirmation `[OWNER DATA]`. Nothing here is copied from a competitor. Builders append rows when they add generated placeholders under `public/placeholders/`.

| Path | Size (px) | KB | Use |
|---|---|---|---|
| `/assets/images/logo.png` | 1774×887 | 2112 | Brand logo: shell top bar (height-constrained, `next/image` with explicit dimensions, `preload`), footer. Oversized for the web; leaf 1.2.1 may add a resized copy under `public/placeholders/logo-*.png` and note it here |
| `/assets/images/banners/hero-banner-1.jpg` | 1556×620 | 768 | Home hero (promo flagship art) |
| `/assets/images/banners/pc-hero-banner-UCLfinal.jpg` | 1556×620 | 1024 | Promotions hero / sports promo art |
| `/assets/images/banners/pc-banner-vpn.jpg` | 1556×620 | 768 | Promotions grid, neutral art only: never paired with app-download, VPN or access copy (no app in phase 1, OQ-12; content describes what is built) |
| `/assets/images/casino/mg_baccarat_landscape.png` | 702×480 | 448 | Lobby tile: Casino → Baccarat |
| `/assets/images/casino/mg_roulette_landscape.png` | 702×480 | 448 | Lobby tile: Casino → Roulette |
| `/assets/images/casino/mg_sicbo_landscape.png` | 702×480 | 512 | Lobby tile: Casino → Tài Xỉu / Sic Bo |
| `/assets/images/casino/sunwin_taixiu-live-landscape.png` | 234×160 | 128 | Lobby tile: Casino → Tài Xỉu live (small; use at tile size only) |
| `/assets/images/casino/keno_vietlott.png` | 234×160 | 128 | Lobby tile: Xổ số → Keno |
| `/assets/images/sports/saba-sports.png` | 702×480 | 512 | Lobby tile: Thể thao → Saba |
| `/assets/images/sports/k-sports.png` | 468×320 | 256 | Lobby tile: Thể thao → K-Sports |
| `/assets/images/sports/Betgming_football_grid.png` | 702×480 | 576 | Lobby tile: Thể thao → football grid |
| `/assets/images/sports/e-vitualsports.png` | 702×480 | 448 | Lobby tile: Thể thao → virtual sports |
| `/assets/players/images (1).jpeg` … `(9).jpeg` | 399×501 (1–5), 201×251 (6), 683×449 (7), 739×415 (8), 554×554 (9) | 12–36 | Collection card art (neutral, named by position only); avatars |
| `/assets/thumb/thumb-reward-4.jpg` | 524×416 | 192 | Reward / promo thumbnail (points store or referral reward card) |

Duplicates ` (1).png` of `keno_vietlott`, `mg_baccarat_landscape`, `sunwin_taixiu-live-landscape` are byte-identical copies and are not referenced.

Rules for builders: reference by the exact path with spaces URL-encoded (`/assets/players/images%20(1).jpeg`) or rename only inside your own leaf's lease with the row updated here; always pass `width`/`height` from this table; `alt` describes the game or promo in Vietnamese; never hotlink; never add competitor art.

Generated placeholders (neutral, token-coloured, no external source), served from `public/placeholders/` as `/placeholders/...`:

| Path | Size (px) | KB | Use |
|---|---|---|---|
| `/placeholders/game-4x3.svg` | 400×300 | 1 | Fallback game art (4:3) when a `Game.art` has no owner asset; rendered by `Tile` / `Art` |
| `/placeholders/provider-3x1.svg` | 300×100 | 1 | Fallback provider logo (3:1); rendered by `Art` with `family="provider"` |
| `/placeholders/promo-16x9.svg` | 480×270 | 1 | Fallback promo art (16:9) for promo tiles and banners without an owner asset |
| `/placeholders/avatar-1x1.svg` | 160×160 | 1 | Fallback avatar (1:1) for account and referral surfaces |
| `/placeholders/logo-240.png` | 240×120 | 52 | Web-sized copy of `/assets/images/logo.png`, made with `sips -Z 240` (read-only use of the owner file); shell top bar and footer |
