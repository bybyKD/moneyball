import Link from "next/link";
import SideNav from "@/components/side-nav";

const CARDS = [
  { title: "Players", desc: "5,000-player seeded demo roster with per-90 metrics.", href: "/players" },
  { title: "Scouting Missions", desc: "Live missions tracking candidate shortlists.", href: "/missions" },
  { title: "Market", desc: "Tranfermarkt-style valuations & trends.", href: "/market" },
  { title: "Semantic Search", desc: "pgvector similarity over player profiles.", href: "/embedding" },
];

export default function Home() {
  return (
    <div className="flex">
      <SideNav active="/" />
      <main className="flex-1 p-8">
        <h1 className="mb-1 text-3xl font-bold">Home</h1>
        <p className="mb-8 text-[#8fa0bd]">
          Welcome to your Moneyball scouting workplace. This is the Phase 2 web
          shell — module pages land incrementally.
        </p>
        <div className="grid max-w-3xl grid-cols-1 gap-4 sm:grid-cols-2">
          {CARDS.map((c) => (
            <Link
              key={c.title}
              href={c.href}
              className="group rounded-xl border border-[#1f2c44] bg-[#0e1626] p-5 transition-colors hover:border-[#2268f0]"
            >
              <div className="mb-1 text-lg font-semibold text-white group-hover:text-[#8cbfff]">
                {c.title}
              </div>
              <div className="text-sm text-[#8fa0bd]">{c.desc}</div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
