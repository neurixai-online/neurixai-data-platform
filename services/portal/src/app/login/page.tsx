import { LoginForm } from "./LoginForm";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 px-4">
      <div className="text-center">
        <p className="text-xs uppercase tracking-wider text-brand-cyan">NeurixAI Data Platform</p>
        <h1 className="mt-2 text-2xl font-semibold">เข้าสู่ระบบ Developer Portal</h1>
      </div>
      <LoginForm />
    </main>
  );
}
