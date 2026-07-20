import Link from "next/link";

import { CoreApiError, coreApi } from "@/lib/coreApi";

export default async function VerifyEmailPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>;
}) {
  const { token } = await searchParams;

  let success = false;
  let message = "ลิงก์ยืนยันไม่ถูกต้อง";

  if (token) {
    try {
      const result = await coreApi.verifyEmail(token);
      success = true;
      message = result.message;
    } catch (error) {
      message = error instanceof CoreApiError ? "ลิงก์ยืนยันไม่ถูกต้องหรือหมดอายุแล้ว" : "เกิดข้อผิดพลาด กรุณาลองใหม่";
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 px-4 text-center">
      <div className="nx-card max-w-sm p-6">
        <p className="text-xs uppercase tracking-wider text-brand-blue dark:text-brand-cyan">
          NeurixAI Data Platform
        </p>
        <h1 className="mt-2 text-xl font-semibold">{success ? "ยืนยันอีเมลสำเร็จ" : "ยืนยันอีเมลไม่สำเร็จ"}</h1>
        <p className="nx-muted mt-3 text-sm">{message}</p>
        <p className="nx-muted mt-4 text-sm">
          <Link href="/login" className="nx-link">
            ไปหน้าเข้าสู่ระบบ
          </Link>
        </p>
      </div>
    </main>
  );
}
