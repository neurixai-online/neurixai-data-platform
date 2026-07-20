"use client";

import Link from "next/link";
import { useActionState } from "react";

import { loginAction, type LoginState } from "./actions";

const initialState: LoginState = {};

export function LoginForm() {
  const [state, formAction, isPending] = useActionState(loginAction, initialState);

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
          รหัสผ่าน
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          autoComplete="current-password"
          className="rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-brand-blue"
        />
      </div>

      {state.error && <p className="text-sm text-red-400">{state.error}</p>}

      <button
        type="submit"
        disabled={isPending}
        className="mt-2 rounded-md bg-brand-blue px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-glow disabled:opacity-50"
      >
        {isPending ? "กำลังเข้าสู่ระบบ..." : "เข้าสู่ระบบ"}
      </button>

      <p className="text-center text-sm text-white/50">
        ยังไม่มีบัญชี?{" "}
        <Link href="/signup" className="text-brand-cyan hover:underline">
          สมัครสมาชิก
        </Link>
      </p>
    </form>
  );
}
