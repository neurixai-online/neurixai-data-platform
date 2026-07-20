"use server";

import { AuthError } from "next-auth";

import { CoreApiError, coreApi } from "@/lib/coreApi";
import { signIn } from "@/lib/auth";

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

  try {
    // Signup only creates the account in core-api — go through the same login path as
    // everyone else to actually establish the NextAuth session, rather than duplicating
    // session-creation logic here.
    await signIn("credentials", { email, password, redirectTo: "/dashboard" });
    return {};
  } catch (error) {
    if (error instanceof AuthError) {
      return { error: "สมัครสำเร็จแต่เข้าสู่ระบบอัตโนมัติไม่สำเร็จ กรุณาเข้าสู่ระบบด้วยตนเอง" };
    }
    throw error;
  }
}
