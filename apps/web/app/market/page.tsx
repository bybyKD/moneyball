import Link from "next/link";
import SideNav from "@/components/side-nav";

export const dynamic = "force-dynamic";

const POS = ["GK", "CB", "FB", "DM", "CM", "AM", "W", "ST"];

async function fetchPicks(position: string) {
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const qs = position && position !== "all" ? `?position=${position}&k=15` : "?k=15";
  const r = await fetch(`${base}/api/market/value-picks${qs}`, { cache: "no-store" });
  return r.ok ? r.json() : null;
}

export default async function MarketPage({ searchParams }: { searchParams: Promise<{ position?: string }> }) {
  const { position = "all" } = await searchParams;
  const data = await fetchPicks(position);

  return (
    <div className="flex">
      <SideNav active="/market" />
      <main className="flex-1 p-8">
        <h1 className="mb-1 text-3xl font-bold">Market — Value Picks</h1>
        <p className="mb-5 text-sm text-[#8fa0bd]">Production-per-euro scan · {data?.method}</p>

        <div className="mb-5 flex flex-wrap gap-2">
          {["all", ...POS].map((p) => (
            <Link key={p} href={p === "all" ? "/market" : `/market?position=${p}`}
              className={`rounded-full px-3 py-1 text-sm ${p === position ? "bg-[#8cbfff] text-[#0e1626]" : "bg-[#1f2c44] text-white"}`}>
              {p}
            </Link>
          ))}
        </div>

        {!data?.picks?.length ? (
          <p className="text-[#8fa0bd]">No data — is the API up?</p>
        ) : (
          <div className="max-w-4xl overflow-hidden rounded-xl border border-[#1f2c44]">
            <table className="w-full text-sm">
              <thead className="bg-[#1f2c44] text-left text-xs text-[#8fa0bd]">
                <tr>{["Value ratio", "Score", "Age", "Position", "Est. value", "Player"].map((h) => (
                  <th key={h} className="px-4 py-2 font-medium">{h}</th>))}</tr>
              </thead>
              <tbody>
                {data.picks.map((p: any, i: number) => (
                  <tr key={p.player_id} className={i % 2 ? "bg-[#0c1322]" : "bg-[#0e1626]"}>
                    <td className="px-4 py-2 font-semibold text-[#8cbfff]">{p.value_ratio}</td>
                    <td className="px-4 py-2">{p.score}</td>
                    <td className="px-4 py-2 text-[#8fa0bd]">{p.age}</td>
                    <td className="px-4 py-2">{p.position}</td>
                    <td className="px-4 py-2">€{p.market_value_eur.toLocaleString()}</td>
                    <td className="px-4 py-2">
                      <Link href={`/players/${p.player_id}`} className="hover:text-[#8cbfff]">{p.name}</Link>
                      <span className="ml-2 text-xs text-[#8fa0bd]">{p.nationality}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}