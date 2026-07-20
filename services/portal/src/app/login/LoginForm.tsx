"use client";

import Link from "next/link";
import { useActionState, useState } from "react";

import { loginAction, resendVerificationAction, type LoginState, type ResendState } from "./actions";

const initialState: LoginState = {};
const initialResendState: ResendState = {};

export function LoginForm() {
  const [state, formAction, isPending] = useActionState(loginAction, initialState);
  const [resendState, resendAction, isResending] = useActionState(resendVerificationAction, initialResendState);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const mfaStep = Boolean(state.mfaRequired);

  return (
    <form action={formAction} className="flex w-full max-w-sm flex-col gap-4">
      {mfaStep ? (
        <>
          <input type="hidden" name="email" value={email} />
          <input type="hidden" name="password" value={password} />
          <div className="flex flex-col gap-1.5">
            <label htmlFor="totpCode" className="nx-label">
              รหัสยืนยันตัวตน 6 หลัก
            </label>
            <input
              id="totpCode"
              name="totpCode"
              inputMode="numeric"
              pattern="[0-9]{6}"
              maxLength={6}
              required
              autoFocus
              autoComplete="one-time-code"
              className="nx-input"
            />
          </div>
        </>
      ) : (
        <>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="email" className="nx-label">
              อีเมล
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              autoComplete="email"
              className="nx-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="password" className="nx-label">
              รหัสผ่าน
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              autoComplete="current-password"
              className="nx-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
        </>
      )}

      {state.error && <p className="text-sm text-red-500 dark:text-red-400">{state.error}</p>}

      {state.emailNotVerified &&
        (resendState.sent ? (
          <p className="nx-muted text-sm">ส่งลิงก์ยืนยันอีเมลใหม่แล้ว กรุณาตรวจสอบอีเมลของคุณ</p>
        ) : (
          <button
            type="submit"
            formAction={resendAction}
            formNoValidate
            disabled={isResending}
            className="nx-link text-left text-sm"
          >
            {isResending ? "กำลังส่ง..." : "ส่งอีเมลยืนยันอีกครั้ง"}
          </button>
        ))}

      <button type="submit" disabled={isPending} className="nx-btn-primary mt-2">
        {isPending ? "กำลังเข้าสู่ระบบ..." : mfaStep ? "ยืนยัน" : "เข้าสู่ระบบ"}
      </button>

      <p className="nx-muted text-center text-sm">
        ยังไม่มีบัญชี?{" "}
        <Link href="/signup" className="nx-link">
          สมัครสมาชิก
        </Link>
      </p>
    </form>
  );
}
