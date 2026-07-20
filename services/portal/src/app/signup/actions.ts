"use server";

import { redirect } from "next/navigation";

import { CoreApiError, coreApi } from "@/lib/coreApi";

export type SignupState = { error?: string };

export async function signupAction(_prevState: SignupState, formData: FormData): Promise<SignupState> {
  const email = String(formData.get("email") ?? "");
  const password = String(formData.get("password") ?? "");

  try {
    await coreApi.signup(email, password);
  } catch (error) {
    if (error instanceof CoreApiError && error.status === 409) {
      return { error: "อีเมลนี้ถูกใช้สมัครแล้ว" };
    }
    if (error instanceof CoreApiError && error.status === 422) {
      return { error: "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร และอีเมลต้องถูกต้อง" };
    }
    throw error;
  }

  // Account now requires email verification before it can log in (see core-api
  // POST /v1/platform/auth/login) — no more auto-signIn here.
  redirect(`/check-email?email=${encodeURIComponent(email)}`);
}
