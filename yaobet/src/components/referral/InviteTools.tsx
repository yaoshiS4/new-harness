/* ============================================================================
 * InviteTools — referral code + link + copy actions
 * A client island: copy-to-clipboard with an honest,
 * equal-salience inline confirmation (no win-juice). Auth-aware: a guest sees a
 * prompt instead of a usable code. Shared by /dai-ly AND /gioi-thieu.
 *
 * Referral-method panel (.top_left, the NARROWER 430px panel): a 2-col layout
 * — code + link stacked LEFT (~71%, .box_left), a white QR tile RIGHT
 * (.box_right .QR-code) with a "Lưu mã QR" action beneath. The 2-col grid is
 * gated at the band breakpoint (640px) and collapses to a stack in /dai-ly's
 * narrow column (beside the 304px rail).
 *
 * QR HONESTY: referral.posterSrc is wired through next/image inside the white
 * tile, but ONLY when it is a REAL asset — the current mock points at a dark
 * placeholder SVG (not a scannable QR), so the tile shows the honest placeholder
 * and the save button stays DISABLED. We never ship a blank/fabricated QR or a
 * fake download; the tile lights up automatically when a real QR asset lands.
 * ==========================================================================*/

"use client";

import { useState } from "react";
import Image from "next/image";
import type { Referral } from "@/lib/types";
import { vi } from "@/lib/i18n";
import { useRequireAuth } from "@/lib/auth";
import { Card, Button, Icon } from "@/ui";

const t = vi.referral;

/* The placeholder asset shipped with the mock — a dark "Poster" graphic, NOT a
 * scannable QR. Treat it as absent so we render the honest placeholder and keep
 * the save action disabled until a real QR asset replaces this path. */
const PLACEHOLDER_POSTER = "/assets/placeholders/poster.svg";

export interface InviteToolsProps {
  referral: Referral;
}

type Copied = "none" | "code" | "link";

export function InviteTools({ referral }: InviteToolsProps) {
  const { allowed, promptAuth } = useRequireAuth();
  const [copied, setCopied] = useState<Copied>("none");

  // a REAL QR asset (not the placeholder) → render it + enable save.
  const hasRealPoster =
    Boolean(referral.posterSrc) && referral.posterSrc !== PLACEHOLDER_POSTER;

  const copy = async (what: "code" | "link", value: string) => {
    if (!allowed) {
      promptAuth();
      return;
    }
    try {
      await navigator.clipboard.writeText(value);
      setCopied(what);
      window.setTimeout(() => setCopied("none"), 2000);
    } catch {
      // clipboard blocked — leave UI honest, no fake success
      setCopied("none");
    }
  };

  return (
    <Card variant="default" className="flex flex-col gap-space-4 p-card-pad">
      <h2 className="promo-type-h4 text-text-hi">{t.invitePanelTitle}</h2>

      <div className="flex flex-col gap-space-5 min-[640px]:flex-row min-[640px]:items-start min-[640px]:gap-space-4">
        {/* LEFT — code + link stacked (.box_left, ~71%) */}
        <div className="flex flex-col gap-space-4 min-w-[0] min-[640px]:flex-[1_1_auto]">
          <div className="flex flex-col gap-space-2">
            <span className="text-t-sm text-text-mid">{t.inviteCodeLabel}</span>
            <div className="flex items-center gap-space-2 py-space-2 px-space-3 rounded-md [background:var(--surface-2)] border border-border">
              <span className="flex-[1] font-brand-font-num [font-variant-numeric:tabular-nums] tracking-[0.02em] text-t-h3 font-weight-bold text-brand-accent-fg min-w-[0] [overflow-wrap:anywhere]">{referral.code}</span>
              <Button
                variant="ghost"
                size="sm"
                icon="copy"
                onClick={() => copy("code", referral.code)}
              >
                {copied === "code" ? t.inviteCopied : t.inviteCopy}
              </Button>
            </div>
          </div>

          <div className="flex flex-col gap-space-2">
            <span className="text-t-sm text-text-mid">{t.inviteLinkLabel}</span>
            <div className="flex items-center gap-space-2 py-space-2 px-space-3 rounded-md [background:var(--surface-2)] border border-border">
              <span className="flex-[1] text-t-sm text-text [overflow-wrap:anywhere] min-w-[0]">{referral.link}</span>
              <Button
                variant="ghost"
                size="sm"
                icon="copy"
                onClick={() => copy("link", referral.link)}
              >
                {copied === "link" ? t.inviteCopied : t.inviteCopy}
              </Button>
            </div>
          </div>
        </div>

        {/* RIGHT — white QR tile (.box_right .QR-code) + "Lưu mã QR" beneath */}
        <div className="flex flex-col items-center gap-space-2 min-[640px]:flex-[0_0_auto] min-[640px]:w-[116px]">
          <span className="flex items-center justify-center w-[84px] h-[84px] flex-[0_0_auto] rounded-md [background:var(--qr-surface)]">
            {hasRealPoster ? (
              <Image
                src={referral.posterSrc}
                alt={t.invitePosterTitle}
                width={90}
                height={90}
                className="w-[90%] h-[90%] object-contain"
              />
            ) : (
              // honest placeholder — never a fabricated/blank QR
              <span className="inline-flex items-center justify-center text-shell opacity-[0.35]" aria-hidden="true">
                <Icon name="grid" size={32} />
              </span>
            )}
          </span>
          <span className="text-t-sm text-text-hi font-weight-semi">{t.invitePosterTitle}</span>
          <Button
            variant="ghost"
            size="sm"
            icon="deposit"
            disabled={!hasRealPoster}
          >
            {t.inviteSaveQr}
          </Button>
          {!hasRealPoster && (
            <span className="text-t-micro text-text-mid text-center max-w-[100%]">{t.invitePosterHint}</span>
          )}
        </div>
      </div>

      {!allowed && <p className="text-t-sm text-text-mid">{t.inviteGuestNote}</p>}
    </Card>
  );
}
