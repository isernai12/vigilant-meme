import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "Telegram MCQ Admin",
  description: "Admin panel for Telegram MCQ practice bot"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
