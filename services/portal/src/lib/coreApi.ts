// Server-side only client for core-api. CORE_API_URL is never exposed to the browser —
// the portal is a pure HTTP client of core-api, which stays the only thing that touches
// Postgres (see services/core-api/app/domains/platform).
const CORE_API_URL = process.env.CORE_API_URL ?? "http://core-api:8000";

export class CoreApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit & { token?: string }): Promise<T> {
  const { token, headers, ...rest } = init ?? {};
  const res = await fetch(`${CORE_API_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new CoreApiError(res.status, await res.text());
  }
  return (await res.json()) as T;
}

export type TokenResponse = { access_token: string; token_type: string };
export type MessageResponse = { message: string };
export type SubscriptionOut = { plan_name: string; status: string };
export type ApiKeyOut = { id: string; key_prefix: string; created_at: string; revoked_at: string | null };
export type MeResponse = {
  id: string;
  email: string;
  totp_enabled: boolean;
  subscriptions: SubscriptionOut[];
  api_keys: ApiKeyOut[];
};
export type ApiKeyCreatedOut = ApiKeyOut & { raw_key: string };
export type MfaSetupResponse = { secret: string; otpauth_uri: string };

export const coreApi = {
  signup: (email: string, password: string) =>
    request<MessageResponse>("/v1/platform/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string, totpCode?: string) =>
    request<TokenResponse>("/v1/platform/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password, totp_code: totpCode ?? null }),
    }),
  verifyEmail: (token: string) =>
    request<MessageResponse>("/v1/platform/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ token }),
    }),
  resendVerification: (email: string) =>
    request<MessageResponse>("/v1/platform/auth/resend-verification", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  me: (token: string) => request<MeResponse>("/v1/platform/me", { token }),
  createApiKey: (token: string) => request<ApiKeyCreatedOut>("/v1/platform/api-keys", { method: "POST", token }),
  revokeApiKey: (token: string, id: string) =>
    request<ApiKeyOut>(`/v1/platform/api-keys/${id}`, { method: "DELETE", token }),
  mfaSetup: (token: string) => request<MfaSetupResponse>("/v1/platform/mfa/setup", { method: "POST", token }),
  mfaVerify: (token: string, code: string) =>
    request<MessageResponse>("/v1/platform/mfa/verify", { method: "POST", token, body: JSON.stringify({ code }) }),
  mfaDisable: (token: string, code: string) =>
    request<MessageResponse>("/v1/platform/mfa/disable", { method: "POST", token, body: JSON.stringify({ code }) }),
};
