/* ============================================================================
 * Yaobet — TIN NHẮN / MESSAGES (route "/tin-nhan") — 消息中心 / Message Center.
 * ----------------------------------------------------------------------------
 * Moved INTO the (member) route group so it inherits the shared MemberSidebar
 * rail hosted once by (member)/layout.tsx (the same frame /tai-khoan and
 * /vi-tien use). The URL is unchanged — route groups never change the URL — so
 * the rail's "messages" tile (id 'messages', href '/tin-nhan') lights active and
 * shows its unread dot for free.
 *
 * A thin async Server Component: it fetches the message seed (honors
 * DEMO_EMPTY → []) and hands it to the MessageCenter client island as `initial`.
 * This is the truthful seam: the island renders only what the
 * server gives it — never a fabricated message or count. All mutations
 * (mark-read, mark-all-read, delete-all, filter) are CLIENT-only / UI-only.
 * ==========================================================================*/

import { getMessages } from "@/lib/mock";
import { MessageCenter } from "@/components/messages";
import { vi } from "@/lib/i18n";

export const metadata = {
  title: "Tin nhắn — Yaobet",
};

export default async function MessagesPage() {
  const initial = await getMessages();

  return (
    <section aria-label={vi.messages.title}>
      <MessageCenter initial={initial} />
    </section>
  );
}
