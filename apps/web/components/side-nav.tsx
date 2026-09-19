"use client";

import Link from "next/link";

const SECTIONS = [
  { href: "/", label: "Home" },
  { href: "/players", label: "Players" },
  { href: "/scouting", label: "Scouting Missions" },
  { href: "/shortlists", label: "Shortlists" },
  { href: "/market", label: "Market" },
  { href: "/analytics", label: "Analytics" },
  { href: "/embedding", label: "Semantic Search" },
  { href: "/agents", label: "AI Agents" },
  { href: "/reports", label: "Reports" },
  { href: "/players/compare", label: "Compare Players" },
  { href: "/settings", label: "Settings" },
];

export default function SideNav({ active }: { active?: string }) {
  return (
    <nav className="flex h-screen w-64 shrink-0 flex-col border-r border-[#1f2c44] bg-[#0e1626] p-4">
      <div className="mb-6">
        <div className="text-xl font-bold tracking-tight text-white">Moneyball</div>
        <div className="text-xs text-[#8fa0bd]">AI Scouting Platform</div>
      </div>
      <ul className="flex flex-1 flex-col gap-1 overflow-y-auto">
        {SECTIONS.map((s) => {
          const isActive = active === s.href;
          return (
            <li key={s.href}>
              <Link
                href={s.href}
                className={`block rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-[#2268f0] text-white"
                    : "text-[#c6d2e6] hover:bg-[#1a2440] hover:text-white"
                }`}
              >
                {s.label}
              </Link>
            </li>
          );
        })}
      </ul>
      <div className="mt-4 border-t border-[#1f2c44] pt-3 text-xs text-[#8fa0bd]">
        <div className="mb-1 font-medium text-[#c6d2e6]">Environment</div>
        <div>API: localhost:8000</div>
        <div>DB: postgres (demo seed)</div>
      </div>
    </nav>
  );
}
