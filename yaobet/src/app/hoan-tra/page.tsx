/* ============================================================================
 * /hoan-tra — cashback. Repointed to the promotions hub (/khuyen-mai), which
 * carries the cashback promotion. Redirect so no internal link 404s.
 * ==========================================================================*/

import { redirect } from "next/navigation";

export default function CashbackRedirect() {
  redirect("/khuyen-mai");
}
