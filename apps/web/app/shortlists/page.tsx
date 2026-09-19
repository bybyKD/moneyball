import { cookies } from "next/headers";
import SideNav from "@/components/side-nav";

export const dynamic = "force-dynamic";
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default async function ShortlistsPage() {
  const cookieStore = await cookies();
  const cookie = cookieStore.toString();
  let lists: any[] = [];
  if (cookie) {
    try {
      const r = await fetch(`${BASE}/api/shortlists`, { cache: "no-store", headers: { Cookie: cookie } });
      lists = r.ok ? await r.json() : [];
    } catch { /* ignore */ }
  }

  const details = await Promise.all(
    lists.map(async (l: any) => {
      try {
        const r = await fetch(`${BASE}/api/shortlists/${l.id}`, { cache: "no-store", headers: { Cookie: cookie } });
        const d = r.ok ? await r.json() : { players: [] };
        return { ...l, players: d.players ?? [] };
      } catch {
        return { ...l, players: [] };
      }
    })
  );

  return (
    <div className="flex">
      <SideNav active="/shortlists" />
      <main className="flex-1 p-8">
        <h1 className="mb-1 text-3xl font-bold">Shortlists</h1>
        <p className="mb-5 text-sm text-[#8fa0bd]">Candidates saved from scouting missions</p>

        {!cookie && <p className="text-[#8fa0bd]">Sign in on the Scouting page to set up shortlists.</p>}
        {cookie && !details.length && <p className="text-[#8fa0bd]">No shortlists yet — add a candidate from a mission.</p>}

        <div className="max-w-3xl space-y-4">
          {details.map((l: any) => (
            <div key={l.id} className="rounded-xl border border-[#1f2c44] bg-[#0e1626] p-5">
              <h2 className="mb-1 font-semibold">{l.name}</h2>
              {l.description && <p className="mb-3 text-sm text-[#8fa0bd]">{l.description}</p>}
              {!l.players.length && <p className="text-sm text-[#8fa0bd]">Empty shortlist.</p>}
              {l.players.map((p: any, i: number) => (
                <div key={i} className="flex items-center gap-3 border-t border-[#1f2c44] py-2 text-sm">
                  <span className="flex-1 text-[#8fa0bd]">player {p.player_id}</span>
                  <span className="text-xs text-[#8cbfff]">{p.status}</span>
                  {p.priority && <span className="text-xs text-[#ffcb8f]">pri {p.priority}</span>}
                </div>
              ))}
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}