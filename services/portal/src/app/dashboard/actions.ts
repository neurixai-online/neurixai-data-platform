"use server";

import { revalidatePath } from "next/cache";

import { auth } from "@/lib/auth";
import { coreApi } from "@/lib/coreApi";

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
