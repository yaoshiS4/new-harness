/* ============================================================================
 * Yaobet — /ve-so : the VÉ SỐ hub.
 * A thin server shell; the composition root is the client boundary.
 *
 * NAMING, decided and load-bearing: the lobby vertical "Xổ số" (/?v=lottery)
 * is provider lottery GAMES. This route is "Vé số" — a ticket you hold and
 * open yourself. The two must never collapse into one word.
 * ==========================================================================*/

import type { Metadata } from "next";
import { LotteryRoot } from "@/components/lottery/LotteryRoot";

export const metadata: Metadata = {
  title: "Vé số — Yaobet",
};

export default function LotteryPage() {
  return <LotteryRoot />;
}
