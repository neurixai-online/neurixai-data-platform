"use client";

import { useActionState } from "react";

import { createApiKeyAction, type CreateKeyState } from "./actions";

const initialState: CreateKeyState = {};

export function CreateKeyForm() {
  const [state, formAction, isPending] = useActionState(createApiKeyAction, initialState);

  return (
    <div className="flex flex-col items-end gap-2">
      <form action={formAction}>
        <button
          type="submit"
          disabled={isPending}
          className="rounded-md bg-brand-blue px-3 py-1.5 text-xs font-medium text-white transition hover:bg-brand-glow disabled:opacity-50"
        >
          {isPending ? "กำลังสร้าง..." : "+ สร้าง API Key"}
        </button>
      </form>

      {state.error && <p className="text-xs text-red-500 dark:text-red-400">{state.error}</p>}

      {state.rawKey && (
        <div className="max-w-sm rounded-md border border-brand-blue/40 bg-brand-blue/5 p-3 text-xs dark:border-brand-cyan/40 dark:bg-brand-cyan/10">
          <p className="font-medium text-brand-blue dark:text-brand-cyan">
            คัดลอก key นี้ไว้ตอนนี้ — จะไม่แสดงให้ดูอีก
          </p>
          <code className="mt-1 block break-all">{state.rawKey}</code>
        </div>
      )}
    </div>
  );
}
