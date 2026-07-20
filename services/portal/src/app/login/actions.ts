"use server";

import { AuthError } from "next-auth";

import { coreApi } from "@/lib/coreApi";
import { signIn } from "@/lib/auth";

export type LoginState = { error?: string; emailNotVerified?: boolean; mfaRequired?: boolean };

export async function loginAction(_prevState: LoginState, formData: FormData): Promise<LoginState> {
  const email = String(formData.get("email") ?? "");
  const password = String(formData.get("password") ?? "");
  const totpCode = String(formData.get("totpCode") ?? "") || undefined;

  try {
    await signIn("credentials", { email, password, totpCode, redirectTo: "/dashboard" });
    return {};
  } catch (error) {
    if (error instanceof AuthError) {
      const code = (error as unknown as { code?: string }).code;
      if (code === "email_not_verified") {
        return { error: "กรุณายืนยันอีเมลก่อนเข้าสู่ระบบ", emailNotVerified: true };
      }
      if (code === "mfa_required") {
        return { error: undefined, mfaRequired: true };
      }
      if (code === "invalid_mfa_code") {
        return { error: "รหัสยืนยันไม่ถูกต้อง", mfaRequired: true };
      }
      return { error: "อีเมลหรือรหัสผ่านไม่ถูกต้อง" };
    }
    throw error; // NEXT_REDIRECT and genuinely unexpected errors must propagate
  }
}

export type ResendState = { sent?: boolean };

export async function resendVerificationAction(
  _prevState: ResendState,
  formData: FormData,
): Promise<ResendState> {
  const email = String(formData.get("email") ?? "");
  if (email) {
    await coreApi.resendVerification(email);
  }
  return { sent: true };
}
