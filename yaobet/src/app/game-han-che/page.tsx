/* ============================================================================
 * /game-han-che — MERGED into /cuoc-hop-le as the "Game hạn chế" tab (owner
 * merge 2026-08-11). This standalone route is kept ONLY as a permanent redirect
 * so existing promotion / CS links to /game-han-che keep working — it now
 * lands on the restricted tab of the merged page. The list markup + island live
 * in components/restricted/, rendered inside that tab.
 * ==========================================================================*/

import { redirect } from "next/navigation";

export default function RestrictedGamesRedirect() {
  redirect("/cuoc-hop-le?tab=han-che");
}
