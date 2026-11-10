/* ============================================================================
 * AuthModal — the single auth surface (FTD seam).
 * Centred 2-zone dialog on desktop, bottom sheet on mobile (the Overlay
 * presentation="auto" rule). PASSWORD-ONLY: số điện thoại + mật khẩu, no OTP /
 * no method tabs. Modes: login | register (useAuthModal().mode).
 *
 * Opens ONLY via useAuthModal().openAuthModal — the single mechanism. Lazy-
 * mounted (Overlay is not in the DOM until open); never a modal farm.
 *
 * MOCK auth: submit flips the session via useAuth().signIn (no network).
 *
 * Left BRAND PANEL (desktop only): logo + tagline + trust bullets that FILL the
 * dialog height — no empty placeholder boxes. aria-hidden: it is
 * decorative reassurance; the form carries the accessible name.
 *
 * FTD HANDOFF: if the open carried resumeIntent.action === 'deposit',
 * a successful REGISTER shows exactly ONE "Đăng ký thành công" confirmation,
 * then the auth overlay dismisses and the resume-intent is replayed via
 * onResumeDeposit (AppShell presents the DepositSheet's first-deposit variant).
 * Focus is NOT returned to the page behind on that handoff (skipReturnFocus) —
 * AppShell transfers focus into the deposit surface. Cancel (Esc/scrim/swipe)
 * holds the intent (not consumed), returns focus to the trigger, opens no
 * deposit. A failed register keeps the sheet open and consumes no intent.
 *
 * Transient form state lives in the inner <AuthModalBody>, KEYED by mode, so a
 * (re)open or a login↔register switch resets it via remount — no reset effect.
 * ==========================================================================*/

"use client";

import { useId, useState } from "react";
import { useAuth, useAuthModal } from "@/lib/auth";
import { vi } from "@/lib/i18n";
import { Button } from "@/ui/Button/Button";
import { Icon, type IconName } from "@/ui/Icon/Icon";
import { Overlay } from "../layout/_internal/Overlay";
import { AuthField } from "./AuthField";

export interface AuthModalProps {
  /** replay a deposit resume-intent after a successful register (handoff).
   *  AppShell supplies this; it presents the DepositSheet + moves focus in. */
  onResumeDeposit?: (opts: { isFirstDeposit: boolean }) => void;
}

/** Trust bullets shown in the brand panel — truthful, no fabricated figures. */
const TRUST_BULLETS: ReadonlyArray<{ icon: IconName; text: string }> = [
  { icon: "fast", text: vi.auth.trust.payout },
  { icon: "cashback", text: vi.auth.trust.cashback },
  { icon: "shield", text: vi.auth.trust.secure },
  { icon: "support", text: vi.auth.trust.support },
];

export function AuthModal({ onResumeDeposit }: AuthModalProps) {
  const { open, mode, closeAuthModal } = useAuthModal();
  // when true, this close is an FTD handoff → Overlay must NOT return focus to
  // the page (AppShell moves focus into the deposit surface instead).
  const [skipReturnFocus, setSkipReturnFocus] = useState(false);
  const titleId = useId();

  if (!open) return null; // lazy: not in DOM until opened

  function handleClose() {
    // Cancel at auth: intent held (not consumed). Overlay returns focus to the
    // NẠP trigger per returnFocus.
    setSkipReturnFocus(false);
    closeAuthModal();
  }

  return (
    <Overlay
      open={open}
      onClose={handleClose}
      presentation="auto"
      returnFocus={!skipReturnFocus}
      labelledBy={titleId}
      desktopMaxWidth={720}
    >
      <AuthModalBody
        // KEY on mode: reopening or switching mode remounts → state resets.
        key={mode}
        titleId={titleId}
        onHandoffClose={() => {
          setSkipReturnFocus(true);
          closeAuthModal();
        }}
        onClose={handleClose}
        onResumeDeposit={onResumeDeposit}
      />
    </Overlay>
  );
}

interface BodyProps {
  titleId: string;
  onClose: () => void;
  onHandoffClose: () => void;
  onResumeDeposit?: (opts: { isFirstDeposit: boolean }) => void;
}

function AuthModalBody({ titleId, onClose, onHandoffClose, onResumeDeposit }: BodyProps) {
  const { mode, resumeIntent, openAuthModal, consumeResumeIntent } = useAuthModal();
  const { signIn } = useAuth();
  const isRegister = mode === "register";
  const isForgot = mode === "forgot";

  // `phone` doubles as the LOGIN identifier (phone OR username) and the REGISTER
  // phone field; `reset` is the forgot field (email OR phone). No OTP.
  const [username, setUsername] = useState("");
  const [phone, setPhone] = useState("");
  const [secret, setSecret] = useState("");
  const [confirm, setConfirm] = useState("");
  const [referral, setReferral] = useState("");
  const [reset, setReset] = useState("");
  const [confirmError, setConfirmError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [registered, setRegistered] = useState(false);
  const [sent, setSent] = useState(false);

  // dynamic prefix icons: the login identifier swaps account↔phone as the user
  // types letters vs digits; the reset field swaps mail/phone (@ vs digits).
  const looksNumeric = (v: string) => v.length > 0 && /^[\d+\s().-]+$/.test(v);
  const idIcon: IconName = looksNumeric(phone) ? "phone" : "user";
  const resetIcon: IconName = reset.includes("@")
    ? "mail"
    : looksNumeric(reset)
      ? "phone"
      : "mail";

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (submitting) return; // single-flight

    // forgot: MOCK-send a reset link to the email/phone, then confirm. No OTP.
    if (isForgot) {
      setSubmitting(true);
      window.setTimeout(() => {
        setSent(true);
        setSubmitting(false);
      }, 600);
      return;
    }

    // register: the two passwords must match (the only client-side rule; the
    // rest is native `required`). Mã giới thiệu is optional.
    if (isRegister && secret !== confirm) {
      setConfirmError("Mật khẩu xác nhận không khớp");
      return;
    }

    setSubmitting(true);

    // MOCK: resolve immediately (no network). A real provider drops in here.
    const wantsDeposit = resumeIntent.action === "deposit";

    if (isRegister && wantsDeposit) {
      // show ONE honest confirmation, THEN hand off (single-confirmation).
      setRegistered(true);
      const intent = consumeResumeIntent();
      window.setTimeout(() => {
        signIn("level-0"); // a fresh register is a level-0 member
        onHandoffClose();
        onResumeDeposit?.({ isFirstDeposit: intent.isFirstDeposit ?? true });
      }, 700);
      return;
    }

    // plain login/register without a deposit intent: sign in + close.
    signIn(isRegister ? "level-0" : "tiered");
    onClose();
  }

  return (
    <div className="auth-modal-layout">
      {/* ZONE 1 — brand panel (desktop only). Logo + tagline + trust bullets
       *  fill the full dialog height; no empty placeholder boxes. */}
      <aside className="auth-modal-brand-zone" aria-hidden="true">
        <div className="auth-modal-brand-top">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/assets/logo.svg" alt="" className="auth-modal-brand-logo" />
          <p className="auth-modal-brand-tag">{vi.auth.brandTag}</p>
        </div>
        <ul className="auth-modal-trust-list">
          {TRUST_BULLETS.map((b) => (
            <li key={b.text} className="auth-modal-trust-item">
              <span className="auth-modal-trust-icon">
                <Icon name={b.icon} size={18} />
              </span>
              <span className="auth-modal-trust-text">{b.text}</span>
            </li>
          ))}
        </ul>
        {/* Decorative brand fill — GROWS to consume whatever height the form
         *  leaves (small beside the 2-field login, large beside the 5-field
         *  register), so the panel always reads as a finished branded surface
         *  rather than a short content cluster over a void. Inert/decorative. */}
        <div className="auth-modal-brand-art" aria-hidden="true">
          <Icon name="chip" size={160} className="auth-modal-brand-art-mark" />
        </div>
      </aside>

      {/* ZONE 2 — form */}
      <div className="auth-modal-form-zone">
        <div className="auth-modal-head">
          <h2 id={titleId} className="auth-modal-title">
            {isForgot
              ? vi.auth.forgotTitle
              : isRegister
                ? vi.auth.register
                : vi.auth.login}
          </h2>
          <button
            type="button"
            className="auth-modal-close-btn"
            aria-label="Đóng"
            onClick={onClose}
          >
            <Icon name="close" size={22} />
          </button>
        </div>

        {registered || (isForgot && sent) ? (
          // success confirmation — register OR forgot-link-sent (no win-juice)
          <div className="auth-modal-success" role="status">
            <Icon name="check" size={28} className="auth-modal-success-icon" />
            <p className="auth-modal-success-text">
              {isForgot ? vi.auth.forgotSuccess : vi.auth.registerSuccess}
            </p>
            {isForgot && (
              <button
                type="button"
                className="auth-modal-switch-btn"
                onClick={() => openAuthModal({ mode: "login", resumeIntent })}
              >
                {vi.auth.backToLogin}
              </button>
            )}
          </div>
        ) : isForgot ? (
          // FORGOT-PASSWORD: reset by email OR phone (prefix icon swaps). No OTP.
          <>
            <form className="auth-modal-form" onSubmit={onSubmit}>
              <p className="auth-modal-reset-prompt">{vi.auth.forgotPrompt}</p>
              <AuthField
                label={vi.auth.resetIdentifier}
                type="text"
                prefixIcon={resetIcon}
                value={reset}
                onChange={setReset}
                autoComplete="username"
                required
              />
              <Button type="submit" variant="primary" size="lg" fullWidth loading={submitting}>
                {vi.auth.forgotSubmit}
              </Button>
            </form>
            <p className="auth-modal-switch">
              <button
                type="button"
                className="auth-modal-switch-btn"
                onClick={() => openAuthModal({ mode: "login", resumeIntent })}
              >
                {vi.auth.backToLogin}
              </button>
            </p>
          </>
        ) : (
          <>
            {/* PASSWORD-ONLY (no method tabs, no OTP). LOGIN = số điện thoại / tên
             *  đăng nhập + mật khẩu. REGISTER additionally collects tên đăng nhập,
             *  xác nhận mật khẩu and an optional mã giới thiệu. */}
            <form className="auth-modal-form" onSubmit={onSubmit}>
              {isRegister && (
                <AuthField
                  label="Tên đăng nhập"
                  type="text"
                  prefixIcon="user"
                  value={username}
                  onChange={setUsername}
                  autoComplete="username"
                  required
                />
              )}

              {/* LOGIN: ONE identifier accepting phone OR username — the prefix
               *  icon swaps to match what is typed. REGISTER: a phone field. */}
              <AuthField
                label={isRegister ? "Số điện thoại" : vi.auth.loginIdentifier}
                type={isRegister ? "tel" : "text"}
                inputMode={isRegister ? "tel" : undefined}
                prefixIcon={isRegister ? "phone" : idIcon}
                value={phone}
                onChange={setPhone}
                autoComplete={isRegister ? "tel" : "username"}
                required
              />

              <AuthField
                label="Mật khẩu"
                type="password"
                prefixIcon="lock"
                revealable
                value={secret}
                onChange={setSecret}
                autoComplete={isRegister ? "new-password" : "current-password"}
                required
              />

              {isRegister && (
                <>
                  <AuthField
                    label="Xác nhận mật khẩu"
                    type="password"
                    prefixIcon="lock"
                    revealable
                    value={confirm}
                    onChange={(v) => {
                      setConfirm(v);
                      if (confirmError) setConfirmError(""); // clear on edit
                    }}
                    autoComplete="new-password"
                    error={confirmError}
                    required
                  />

                  <AuthField
                    label="Mã giới thiệu (tùy chọn)"
                    type="text"
                    prefixIcon="gift"
                    value={referral}
                    onChange={setReferral}
                    autoComplete="off"
                  />
                </>
              )}

              {/* LOGIN-only: forgot-password entry → switches to the reset mode */}
              {!isRegister && (
                <div className="auth-modal-forgot-row">
                  <button
                    type="button"
                    className="auth-modal-forgot-link"
                    onClick={() => openAuthModal({ mode: "forgot", resumeIntent })}
                  >
                    {vi.auth.forgot}
                  </button>
                </div>
              )}

              <Button type="submit" variant="primary" size="lg" fullWidth loading={submitting}>
                {isRegister ? vi.auth.register : vi.auth.login}
              </Button>
            </form>

            {/* mode switch — preserves the resume-intent so the FTD seam
             *  survives a login↔register switch. */}
            <p className="auth-modal-switch">
              {isRegister ? "Đã có tài khoản?" : "Chưa có tài khoản?"}{" "}
              <button
                type="button"
                className="auth-modal-switch-btn"
                onClick={() =>
                  openAuthModal({
                    mode: isRegister ? "login" : "register",
                    resumeIntent,
                  })
                }
              >
                {isRegister ? vi.auth.login : vi.auth.register}
              </button>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
