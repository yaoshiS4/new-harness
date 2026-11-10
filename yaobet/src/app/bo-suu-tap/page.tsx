/* ============================================================================
 * Yaobet — /bo-suu-tap : the collection route.
 * A thin server shell; the composition root is the client boundary.
 * ==========================================================================*/

import type { Metadata } from "next";
import { CollectionRoot } from "./CollectionRoot";

export const metadata: Metadata = {
  title: "Bộ sưu tập — Yaobet",
};

export default function CollectionPage() {
  return <CollectionRoot />;
}
