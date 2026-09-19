import Link from "next/link";
import SideNav from "@/components/side-nav";

export const dynamic = "force-dynamic";

export default async function AnalyticsPage() {
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const r = await fetch(`${base}/api/market/position-summary`, { cache: "no-store" });
  const data = r.ok ? await r.json() : null;

  return (
    <div className="flex">
      <SideNav active="/analytics" />
      <main className="flex-1 p-8">
        <h1 className="mb-1 text-3xl font-bold">Analytics — Position Overview</h1>
        <p className="mb-5 text-sm text-[#8fa0bd]">Moneyball composite distributions per position (deterministic, no LLM)</p>
        {!data?.positions && !data?.GK ? (
          <p className="text-[#8fa0bd]">No data — is the API up?</p>
        ) : (
          <div className="max-w-3xl overflow-hidden rounded-xl border border-[#1f2c44]">
            <table className="w-full text-sm">
              <thead className="bg-[#1f2c44] text-left text-xs text-[#8fa0bd]">
                <tr>{["Position", "Players", "Median score", "Max score", "Top player"].map((h) => (
                  <th key={h} className="px-4 py-2 font-medium">{h}</th>))}</tr>
              </thead>
              <tbody>
                {Object.entries(data ?? {}).map(([pos, s]: any, i: number) => (
                  <tr key={pos} className={i % 2 ? "bg-[#0c1322]" : "bg-[#0e1626]"}>
                    <td className="px-4 py-2 font-semibold">{pos}</td>
                    <td className="px-4 py-2 text-[#8fa0bd]">{s.players}</td>
                    <td className="px-4 py-2">{s.median_score}</td>
                    <td className="px-4 py-2">{s.max_score}</td>
                    <td className="px-4 py-2">
                      <Link href={`/players/${s.top.player_id}`} className="hover:text-[#8cbfff]">{s.top.name}</Link>
                      <span className="ml-2 text-xs text-[#8cbfff]">{s.top.score}</span>
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