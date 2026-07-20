import NextAuth, { CredentialsSignin } from "next-auth";
import Credentials from "next-auth/providers/credentials";

import { CoreApiError, coreApi } from "@/lib/coreApi";

class InvalidLoginError extends CredentialsSignin {
  code = "invalid_credentials";
}

class EmailNotVerifiedError extends CredentialsSignin {
  code = "email_not_verified";
}

class MfaRequiredError extends CredentialsSignin {
  code = "mfa_required";
}

class InvalidMfaCodeError extends CredentialsSignin {
  code = "invalid_mfa_code";
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  session: { strategy: "jwt" },
  pages: { signIn: "/login" },
  providers: [
    Credentials({
      credentials: { email: {}, password: {}, totpCode: {} },
      authorize: async (credentials) => {
        const email = credentials?.email as string | undefined;
        const password = credentials?.password as string | undefined;
        const totpCode = (credentials?.totpCode as string | undefined) || undefined;
        if (!email || !password) return null;

        try {
          const { access_token } = await coreApi.login(email, password, totpCode);
          return { id: email, email, accessToken: access_token };
        } catch (err) {
          if (err instanceof CoreApiError && err.status === 401) {
            // core-api's error body is `{"detail": "..."}` — each detail needs a distinct
            // client-side message/action, anything unrecognized collapses to "invalid".
            let detail: string | undefined;
            try {
              detail = (JSON.parse(err.message) as { detail?: string }).detail;
            } catch {
              // body wasn't JSON — fall through to the generic invalid-login error
            }
            if (detail === "email_not_verified") {
              throw new EmailNotVerifiedError();
            }
            if (detail === "mfa_required") {
              throw new MfaRequiredError();
            }
            if (detail === "invalid_mfa_code") {
              throw new InvalidMfaCodeError();
            }
            throw new InvalidLoginError();
          }
          throw err;
        }
      },
    }),
  ],
  callbacks: {
    jwt: async ({ token, user }) => {
      if (user) {
        token.accessToken = user.accessToken;
      }
      return token;
    },
    session: async ({ session, token }) => {
      session.accessToken = token.accessToken as string;
      return session;
    },
  },
});
