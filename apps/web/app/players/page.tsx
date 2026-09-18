import Link from "next/link";
import SideNav from "@/components/side-nav";

export const dynamic = "force-dynamic";

async function fetchPlayers() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/players?limit=10`, {
    cache: "no-store",
  });
  if (!res.ok) return null;
  return res.json();
}

export default async function PlayersPage() {
  const players = await fetchPlayers();
  return (
    <div className="flex">
      <SideNav active="/players" />
      <main className="flex-1 p-8">
        <h1 className="mb-6 text-3xl font-bold">Players</h1>
        {!players ? (
          <p className="text-[#8fa0bd]">API unavailable — start the backend (make api-dev).</p>
        ) : (
          <div className="max-w-2xl overflow-hidden rounded-xl border border-[#1f2c44]">
            <table className="w-full text-left text-sm">
              <thead className="bg-[#0e1626] text-[#8fa0bd]">
                <tr>
                  <th className="px-4 py-2">Player</th>
                  <th className="px-4 py-2">Pos</th>
                  <th className="px-4 py-2">Nation</th>
                </tr>
              </thead>
              <tbody>
                {players.map((p: any) => (
                  <tr key={p.id} className="border-t border-[#1f2c44]">
                    <td className="px-4 py-2 text-white">{p.full_name}</td>
                    <td className="px-4 py-2">{p.primary_position}</td>
                    <td className="px-4 py-2">{p.nationality_code}</td>
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
