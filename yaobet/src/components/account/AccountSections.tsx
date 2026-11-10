/* ============================================================================
 * AccountSections — the RIGHT content column of the member area. It reorganizes
 * the member account so EACH member-menu item shows ITS OWN content instead of
 * stacking every panel at once (the old behaviour). The active section is driven
 * by the URL hash the left rail (MemberSidebar) already sets:
 *
 *   (none) / #ho-so   → Hồ sơ      : ProfileBasic   (avatar · real name · phone · email)
 *   #bao-mat          → Bảo mật     : SecurityCenter (đổi MK đăng nhập · MK rút tiền · 2FA)
 *   #ngan-hang        → Ngân hàng   : BankAccounts   (liên kết thẻ ngân hàng)
 *   #vi-tien-ao       → Ví          : CryptoAddresses(địa chỉ ví)
 *
 * A client island: it listens to `hashchange` (and reads the initial hash on
 * mount) so navigating between rail tiles swaps the panel without a full reload.
 * Server-fetched truthful fixtures (§F) are passed in as props; this island only
 * picks which one to render — it never invents data.
 * ==========================================================================*/

"use client";

import { useEffect, useState } from "react";
import type {
  BankCard,
  CryptoAddress,
  SecurityIndex,
  VerificationItem,
} from "@/lib/types";
import { ProfileBasic } from "./ProfileBasic";
import { SecurityCenter } from "./SecurityCenter";
import { BankAccounts, CryptoAddresses } from "./LinkedAccounts";

export interface AccountSectionsProps {
  index: SecurityIndex;
  verification: VerificationItem[];
  bankCards: BankCard[];
  cryptoAddresses: CryptoAddress[];
}

type SectionId = "ho-so" | "bao-mat" | "ngan-hang" | "vi-tien-ao";

const HASH_TO_SECTION: Record<string, SectionId> = {
  "ho-so": "ho-so",
  "bao-mat": "bao-mat",
  "ngan-hang": "ngan-hang",
  "vi-tien-ao": "vi-tien-ao",
};

function readHash(): SectionId {
  if (typeof window === "undefined") return "ho-so";
  const raw = window.location.hash.replace(/^#/, "");
  return HASH_TO_SECTION[raw] ?? "ho-so";
}

export function AccountSections({
  index,
  verification,
  bankCards,
  cryptoAddresses,
}: AccountSectionsProps) {
  /* default to Hồ sơ on first paint (SSR-safe); sync to the hash on mount. */
  const [section, setSection] = useState<SectionId>("ho-so");

  useEffect(() => {
    const sync = () => setSection(readHash());
    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  switch (section) {
    case "bao-mat":
      return <SecurityCenter index={index} verification={verification} />;
    case "ngan-hang":
      return <BankAccounts cards={bankCards} />;
    case "vi-tien-ao":
      return <CryptoAddresses addresses={cryptoAddresses} />;
    case "ho-so":
    default:
      return <ProfileBasic contact={verification} />;
  }
}
