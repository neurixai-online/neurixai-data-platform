"use server";

import { revalidatePath } from "next/cache";
import QRCode from "qrcode";

import { auth } from "@/lib/auth";
import { CoreApiError, coreApi } from "@/lib/coreApi";

export type CreateKeyState = { error?: string; rawKey?: string };

export async function createApiKeyAction(_prevState: CreateKeyState): Promise<CreateKeyState> {
  const session = await auth();
  if (!session?.accessToken) {
    return { error: "เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่" };
  }

  const created = await coreApi.createApiKey(session.accessToken);
  revalidatePath("/dashboard");
  return { rawKey: created.raw_key };
}

export async function revokeApiKeyAction(apiKeyId: string): Promise<void> {
  const session = await auth();
  if (!session?.accessToken) return;

  await coreApi.revokeApiKey(session.accessToken, apiKeyId);
  revalidatePath("/dashboard");
}

function mfaCodeErrorMessage(error: unknown): string {
  if (error instanceof CoreApiError && error.status === 401) return "รหัสยืนยันไม่ถูกต้อง";
  if (error instanceof CoreApiError && error.status === 429) return "กรอกรหัสผิดหลายครั้งเกินไป กรุณารอสักครู่";
  throw error;
}

export type MfaSetupState = { secret?: string; qrDataUri?: string; error?: string };

export async function mfaSetupAction(_prevState: MfaSetupState): Promise<MfaSetupState> {
  const session = await auth();
  if (!session?.accessToken) {
    return { error: "เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่" };
  }

  try {
    const { secret, otpauth_uri } = await coreApi.mfaSetup(session.accessToken);
    const qrDataUri = await QRCode.toDataURL(otpauth_uri);
    return { secret, qrDataUri };
  } catch (error) {
    if (error instanceof CoreApiError) {
      return { error: "ไม่สามารถเริ่มตั้งค่า MFA ได้ กรุณาลองใหม่" };
    }
    throw error;
  }
}

export type MfaCodeState = { success?: boolean; error?: string };

export async function mfaVerifyAction(_prevState: MfaCodeState, formData: FormData): Promise<MfaCodeState> {
  const session = await auth();
  if (!session?.accessToken) {
    return { error: "เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่" };
  }

  try {
    await coreApi.mfaVerify(session.accessToken, String(formData.get("code") ?? ""));
  } catch (error) {
    return { error: mfaCodeErrorMessage(error) };
  }

  revalidatePath("/dashboard");
  return { success: true };
}

export async function mfaDisableAction(_prevState: MfaCodeState, formData: FormData): Promise<MfaCodeState> {
  const session = await auth();
  if (!session?.accessToken) {
    return { error: "เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่" };
  }

  try {
    await coreApi.mfaDisable(session.accessToken, String(formData.get("code") ?? ""));
  } catch (error) {
    return { error: mfaCodeErrorMessage(error) };
  }

  revalidatePath("/dashboard");
  return { success: true };
}
