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
        <label htmlFor="email" className="text-sm text-white/70">
          อีเมล
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          className="rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-brand-blue"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <label htmlFor="password" className="text-sm text-white/70">
          รหัสผ่าน (อย่างน้อย 8 ตัวอักษร)
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          className="rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-brand-blue"
        />
      </div>

      {state.error && <p className="text-sm text-red-400">{state.error}</p>}

      <button
        type="submit"
        disabled={isPending}
        className="mt-2 rounded-md bg-brand-blue px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-glow disabled:opacity-50"
      >
        {isPending ? "กำลังสมัครสมาชิก..." : "สมัครสมาชิก"}
      </button>

      <p className="text-center text-sm text-white/50">
        มีบัญชีอยู่แล้ว?{" "}
        <Link href="/login" className="text-brand-cyan hover:underline">
          เข้าสู่ระบบ
        </Link>
      </p>
    </form>
  );
}
