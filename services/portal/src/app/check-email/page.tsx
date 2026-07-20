import Link from "next/link";

export default async function CheckEmailPage({
  searchParams,
}: {
  searchParams: Promise<{ email?: string }>;
}) {
  const { email } = await searchParams;

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 px-4 text-center">
      <div className="nx-card max-w-sm p-6">
        <p className="text-xs uppercase tracking-wider text-brand-blue dark:text-brand-cyan">
          NeurixAI Data Platform
        </p>
        <h1 className="mt-2 text-xl font-semibold">ตรวจสอบอีเมลของคุณ</h1>
        <p className="nx-muted mt-3 text-sm">
          เราได้ส่งลิงก์ยืนยันไปที่{" "}
          {email ? <span className="font-medium text-inherit">{email}</span> : "อีเมลของคุณ"} แล้ว
          กรุณาคลิกลิงก์ในอีเมลเพื่อเปิดใช้งานบัญชี ก่อนเข้าสู่ระบบ
        </p>
        <p className="nx-muted mt-4 text-sm">
          <Link href="/login" className="nx-link">
            กลับไปหน้าเข้าสู่ระบบ
          </Link>
        </p>
      </div>
    </main>
  );
}
