"use client";

import { useActionState, useState } from "react";

import {
  mfaDisableAction,
  mfaSetupAction,
  mfaVerifyAction,
  type MfaCodeState,
  type MfaSetupState,
} from "./actions";

const initialSetupState: MfaSetupState = {};
const initialCodeState: MfaCodeState = {};

export function MfaSection({ totpEnabled }: { totpEnabled: boolean }) {
  const [setupState, setupAction, isSettingUp] = useActionState(mfaSetupAction, initialSetupState);
  const [verifyState, verifyAction, isVerifying] = useActionState(mfaVerifyAction, initialCodeState);
  const [disableState, disableAction, isDisabling] = useActionState(mfaDisableAction, initialCodeState);
  const [confirmingDisable, setConfirmingDisable] = useState(false);

  if (totpEnabled) {
    return (
      <section className="nx-card">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="nx-label font-medium">ยืนยันตัวตนสองขั้นตอน (MFA)</h2>
            <p className="nx-muted mt-1 text-sm">เปิดใช้งานอยู่</p>
          </div>
          {!confirmingDisable && (
            <button
              type="button"
              onClick={() => setConfirmingDisable(true)}
              className="text-xs text-red-500 hover:underline dark:text-red-400"
            >
              ปิดใช้งาน
            </button>
          )}
        </div>

        {confirmingDisable && (
          <form action={disableAction} className="mt-4 flex items-end gap-2">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="disable-code" className="nx-label">
                กรอกรหัส 6 หลักเพื่อยืนยันการปิดใช้งาน
              </label>
              <input
                id="disable-code"
                name="code"
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                required
                autoComplete="one-time-code"
                className="nx-input"
              />
            </div>
            <button type="submit" disabled={isDisabling} className="nx-btn-primary bg-red-500 hover:bg-red-600">
              {isDisabling ? "กำลังปิด..." : "ยืนยันปิดใช้งาน"}
            </button>
          </form>
        )}
        {disableState.error && <p className="mt-2 text-sm text-red-500 dark:text-red-400">{disableState.error}</p>}
      </section>
    );
  }

  return (
    <section className="nx-card">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="nx-label font-medium">ยืนยันตัวตนสองขั้นตอน (MFA)</h2>
          <p className="nx-muted mt-1 text-sm">ยังไม่ได้เปิดใช้งาน</p>
        </div>
        {!setupState.qrDataUri && (
          <form action={setupAction}>
            <button type="submit" disabled={isSettingUp} className="nx-btn-primary">
              {isSettingUp ? "กำลังเริ่ม..." : "เปิดใช้งาน"}
            </button>
          </form>
        )}
      </div>

      {setupState.error && <p className="mt-2 text-sm text-red-500 dark:text-red-400">{setupState.error}</p>}

      {setupState.qrDataUri && (
        <div className="mt-4 flex flex-col items-center gap-3 text-center">
          <p className="nx-muted text-sm">สแกน QR นี้ด้วยแอป authenticator (เช่น Google Authenticator, Authy)</p>
          {/* eslint-disable-next-line @next/next/no-img-element -- data: URI, no next/image benefit */}
          <img src={setupState.qrDataUri} alt="MFA QR code" className="h-40 w-40 rounded-md bg-white p-2" />
          <p className="nx-muted text-xs">
            หรือกรอกรหัสด้วยตนเอง: <code className="break-all">{setupState.secret}</code>
          </p>

          <form action={verifyAction} className="mt-2 flex w-full max-w-[220px] flex-col items-stretch gap-2">
            <input
              name="code"
              inputMode="numeric"
              pattern="[0-9]{6}"
              maxLength={6}
              required
              autoFocus
              autoComplete="one-time-code"
              placeholder="รหัส 6 หลัก"
              className="nx-input text-center"
            />
            <button type="submit" disabled={isVerifying} className="nx-btn-primary">
              {isVerifying ? "กำลังยืนยัน..." : "ยืนยันและเปิดใช้งาน"}
            </button>
          </form>
          {verifyState.error && <p className="text-sm text-red-500 dark:text-red-400">{verifyState.error}</p>}
        </div>
      )}
    </section>
  );
}
