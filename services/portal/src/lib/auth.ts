import NextAuth, { CredentialsSignin } from "next-auth";
import Credentials from "next-auth/providers/credentials";

import { CoreApiError, coreApi } from "@/lib/coreApi";

class InvalidLoginError extends CredentialsSignin {
  code = "invalid_credentials";
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  session: { strategy: "jwt" },
  pages: { signIn: "/login" },
  providers: [
    Credentials({
      credentials: { email: {}, password: {} },
      authorize: async (credentials) => {
        const email = credentials?.email as string | undefined;
        const password = credentials?.password as string | undefined;
        if (!email || !password) return null;

        try {
          const { access_token } = await coreApi.login(email, password);
          return { id: email, email, accessToken: access_token };
        } catch (err) {
          if (err instanceof CoreApiError && err.status === 401) {
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
