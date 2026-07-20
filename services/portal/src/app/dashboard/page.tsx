import { redirect } from "next/navigation";

import { auth, signOut } from "@/lib/auth";
import { coreApi } from "@/lib/coreApi";

import { CreateKeyForm } from "./CreateKeyForm";
import { revokeApiKeyAction } from "./actions";

export default async function DashboardPage() {
  const session = await auth();
  if (!session?.accessToken) {
    redirect("/login");
  }

  const me = await coreApi.me(session.accessToken);

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-8 px-4 py-12">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-brand-cyan">NeurixAI Data Platform</p>
          <h1 className="mt-1 text-2xl font-semibold">{me.email}</h1>
        </div>
        <form
          action={async () => {
            "use server";
            await signOut({ redirectTo: "/login" });
          }}
        >
          <button type="submit" className="text-sm text-white/50 hover:text-white">
            ออกจากระบบ
          </button>
        </form>
      </header>

      <section className="rounded-lg border border-white/10 bg-white/5 p-5">
        <h2 className="text-sm font-medium text-white/70">แพ็กเกจ</h2>
        {me.subscriptions.map((s) => (
          <p key={s.plan_name} className="mt-2 text-lg">
            {s.plan_name} <span className="text-sm text-white/40">({s.status})</span>
          </p>
        ))}
      </section>

      <section className="rounded-lg border border-white/10 bg-white/5 p-5">
        <div className="flex items-start justify-between gap-4">
          <h2 className="text-sm font-medium text-white/70">API Keys</h2>
          <CreateKeyForm />
        </div>

        <ul className="mt-4 flex flex-col gap-2">
          {me.api_keys.length === 0 && (
            <li className="text-sm text-white/40">ยังไม่มี API key — กดสร้างด้านบน</li>
          )}
          {me.api_keys.map((key) => (
            <li
              key={key.id}
              className="flex items-center justify-between rounded-md border border-white/10 px-3 py-2 text-sm"
            >
              <div>
                <code className="text-brand-cyan">{key.key_prefix}...</code>
                <span className="ml-2 text-white/40">
                  {key.revoked_at
                    ? "ยกเลิกแล้ว"
                    : `สร้างเมื่อ ${new Date(key.created_at).toLocaleDateString("th-TH")}`}
                </span>
              </div>
              {!key.revoked_at && (
                <form
                  action={async () => {
                    "use server";
                    await revokeApiKeyAction(key.id);
                  }}
                >
                  <button type="submit" className="text-xs text-red-400 hover:underline">
                    ยกเลิก
                  </button>
                </form>
              )}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
