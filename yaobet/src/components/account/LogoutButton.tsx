/* ============================================================================
 * LogoutButton — sign-out with a CONFIRM step (§account). NEVER one-tap:
 * tapping "Đăng xuất" opens a lazy confirm Modal (the Dialog primitive,
 * focus-trapped, Esc/scrim closable) with an explicit cancel/confirm pair. Only
 * the confirm actually calls signOut(). Hidden entirely for a guest.
 *
 * Two trigger shapes share one confirm Modal: <LogoutButton/> (a full-width
 * row, used on the mobile hub) and <LogoutMenuItem/> (an icon-grid tile, the
 * last entry in the MemberSidebar menu — the 退出 menu entry).
 * ==========================================================================*/

"use client";

import { useState } from "react";
import { vi } from "@/lib/i18n";
import { useAuth } from "@/lib/auth";
import { Button, Modal } from "@/ui";

/** Shared confirm Modal chrome for both trigger shapes. */
function LogoutModal({
  open,
  onClose,
  onConfirm,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
}) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={vi.auth.logout}
      size="sm"
      footer={
        <div className="flex justify-end gap-space-3">
          <Button variant="ghost" size="md" onClick={onClose}>
            Huỷ
          </Button>
          <Button variant="destructive" size="md" onClick={onConfirm}>
            {vi.auth.logout}
          </Button>
        </div>
      }
    >
      <p className="text-t-body text-text leading-lh-body">Bạn có chắc muốn đăng xuất khỏi tài khoản?</p>
    </Modal>
  );
}

export function LogoutButton() {
  const { isAuthenticated, signOut } = useAuth();
  const [confirming, setConfirming] = useState(false);

  if (!isAuthenticated) return null;

  return (
    <>
      <Button
        variant="ghost"
        size="lg"
        fullWidth
        icon="account"
        onClick={() => setConfirming(true)}
        className="mt-space-2"
      >
        {vi.auth.logout}
      </Button>

      <LogoutModal
        open={confirming}
        onClose={() => setConfirming(false)}
        onConfirm={() => {
          setConfirming(false);
          signOut();
        }}
      />
    </>
  );
}
