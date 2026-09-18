import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Moneyball — AI Scouting Platform",
  description: "Moneyball AI-native football scouting & recruitment intelligence.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
