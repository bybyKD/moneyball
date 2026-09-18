import Link from "next/link";
import SideNav from "@/components/side-nav";

export const dynamic = "force-dynamic";

async function fetchData(id: string) {
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const [p, a] = await Promise.all([
    fetch(`${base}/api/players/${id}`, { cache: "no-store" }),
    fetch(`${base}/api/players/${id}/analytics`, { cache: "no-store" }),
  ]);
  return { player: p.ok ? await p.json() : null, analytics: a.ok ? await a.json() : null };
}

export default async function PlayerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { player, analytics } = await fetchData(id);
  return (
    <div className="flex">
      <SideNav active="/players" />
      <main className="flex-1 p-8">
        <Link href="/players" className="text-sm text-[#8fa0bd] hover:text-white">← Players</Link>
        {!player ? (
          <p className="mt-4 text-[#8fa0bd]">Player not found or API unavailable.</p>
        ) : (
          <>
            <h1 className="mb-1 mt-3 text-3xl font-bold">{player.full_name}</h1>
            <div className="mb-6 text-sm text-[#8fa0bd]">
              {player.primary_position} · {player.nationality_name} · born {player.date_of_birth}
            </div>
            {analytics?.result ? (
              <div className="max-w-lg rounded-xl border border-[#1f2c44] bg-[#0e1626] p-5">
                <div className="mb-4 flex items-baseline gap-6">
                  <div>
                    <div className="text-xs text-[#8fa0bd]">Moneyball score</div>
                    <div className="text-4xl font-bold text-[#8cbfff]">{analytics.result.score}</div>
                  </div>
                  <div>
                    <div className="text-xs text-[#8fa0bd]">Est. value</div>
                    <div className="text-xl font-semibold text-white">
                      €{(analytics.result.market_value_eur ?? 0).toLocaleString()}
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {(Object.entries(analytics.result.per90 ?? {})).map(([k, v]) => (
                    <div key={k} className="flex justify-between border-t border-[#1f2c44] py-1">
                      <span className="text-[#8fa0bd]">{k}</span>
                      <span className="text-white">{typeof v === "number" ? v : "—"}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-[#8fa0bd]">No analytics available.</p>
            )}
          </>
        )}
      </main>
    </div>
  );
}
