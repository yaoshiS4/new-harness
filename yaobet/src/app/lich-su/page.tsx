/* ============================================================================
 * /lich-su — history. Repointed to the account hub (/tai-khoan), which carries
 * the transaction/bet history surface. Redirect so no internal link 404s.
 * ==========================================================================*/

import { redirect } from "next/navigation";

export default function HistoryRedirect() {
  redirect("/tai-khoan");
}
