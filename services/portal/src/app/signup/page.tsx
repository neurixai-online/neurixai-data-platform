import { SignupForm } from "./SignupForm";

export default function SignupPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 px-4">
      <div className="text-center">
        <p className="text-xs uppercase tracking-wider text-brand-blue dark:text-brand-cyan">
          NeurixAI Data Platform
        </p>
        <h1 className="mt-2 text-2xl font-semibold">สมัครสมาชิก Developer Portal</h1>
        <p className="nx-muted mt-1 text-sm">เริ่มต้นด้วยแพ็กเกจ Free ฟรี ไม่ต้องใช้บัตรเครดิต</p>
      </div>
      <SignupForm />
    </main>
  );
}
