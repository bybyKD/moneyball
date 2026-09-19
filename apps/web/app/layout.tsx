import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Moneyball — AI Scouting Platform",
  description: "Moneyball AI-native football scouting & recruitment intelligence.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <div className="flex min-h-screen flex-col">
          <div className="flex-1">{children}</div>
          <footer className="border-t border-[#1f2c44] px-8 py-4 text-xs text-[#475877]">
            Moneyball · player data from <a href="https://github.com/statsbomb/open-data" className="text-[#8fa0bd] hover:text-white">StatsBomb open data</a>{" "}
            (CC BY-NC-SA 4.0) unless marked demo ·{" "}
            <a href="https://github.com/statsbomb/open-data/blob/main/LICENSE.pdf" className="text-[#8fa0bd] hover:text-white">
              license
            </a>
          </footer>
        </div>
      </body>
    </html>
  );
}
