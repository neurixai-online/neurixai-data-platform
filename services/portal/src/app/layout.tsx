import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "NeurixAI Data Platform — Developer Portal",
  description: "จัดการ API key และดูปริมาณการใช้งาน Thai open-data API",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="th">
      <body className="min-h-screen font-sans antialiased">{children}</body>
    </html>
  );
}
