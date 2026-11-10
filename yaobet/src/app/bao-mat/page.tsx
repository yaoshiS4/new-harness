/* ============================================================================
 * /bao-mat — security. Repointed to the account hub (/tai-khoan), which carries
 * the security surface. Permanent redirect so no internal link 404s.
 * ==========================================================================*/

import { redirect } from "next/navigation";

export default function SecurityRedirect() {
  redirect("/tai-khoan");
}
