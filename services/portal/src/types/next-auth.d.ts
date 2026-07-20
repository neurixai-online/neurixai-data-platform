// This file must contain a top-level import/export to be treated as a module — without
// one, TS treats `declare module "next-auth" { ... }` below as a full REPLACEMENT of the
// package's types instead of an augmentation, silently deleting every real export
// (AuthError, the default export, etc.). Confirmed by direct repro — not a next-auth bug.
export {};

declare module "next-auth" {
  interface Session {
    accessToken?: string;
  }

  interface User {
    accessToken?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
  }
}
