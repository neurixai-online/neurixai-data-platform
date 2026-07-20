"use client";

import Link from "next/link";
import { useActionState } from "react";

import { signupAction, type SignupState } from "./actions";

const initialState: SignupState = {};

export function SignupForm() {
  const [state, formAction, isPending] = useActionState(signupAction, initialState);

  return (
    <form action={formAction} className="flex w-full max-w-sm flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <label htmlFor="email" className="nx-label">
          อีเมล
        </label>
        <input id="email" name="email" type="email" required autoComplete="email" className="nx-input" />
      </div>
      <div className="flex flex-col gap-1.5">
        <label htmlFor="password" className="nx-label">
          รหัสผ่าน (อย่างน้อย 8 ตัวอักษร)
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          className="nx-input"
        />
      </div>

      {state.error && <p className="text-sm text-red-500 dark:text-red-400">{state.error}</p>}

      <button type="submit" disabled={isPending} className="nx-btn-primary mt-2">
        {isPending ? "กำลังสมัครสมาชิก..." : "สมัครสมาชิก"}
      </button>

      <p className="nx-muted text-center text-sm">
        มีบัญชีอยู่แล้ว?{" "}
        <Link href="/login" className="nx-link">
          เข้าสู่ระบบ
        </Link>
      </p>
    </form>
  );
}
