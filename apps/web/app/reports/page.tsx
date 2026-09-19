import { cookies } from "next/headers";
import Link from "next/link";
import SideNav from "@/components/side-nav";

export const dynamic = "force-dynamic";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchRuns() {
  const cookieStore = await cookies();
  const cookie = cookieStore.toString();
  if (!cookie) return null;
  try {
    const r = await fetch(`${BASE}/api/agents/runs`, { cache: "no-store", headers: { Cookie: cookie } });
    return r.ok ? r.json() : null;
  } catch {
    return null;
  }
}

async function fetchRun(id: number, cookie: string) {
  const r = await fetch(`${BASE}/api/agents/runs/${id}`, { cache: "no-store", headers: { Cookie: cookie } });
  return r.ok ? r.json() : null;
}

export default async function ReportsPage() {
  const runs = await fetchRuns();
  const cookieStore = await cookies();
  const cookie = cookieStore.toString();
  const first = runs?.length ? await fetchRun(runs[0].id, cookie) : null;

  return (
    <div className="flex">
      <SideNav active="/reports" />
      <main className="flex-1 p-8">
        <h1 className="mb-1 text-3xl font-bold">Reports</h1>
        <p className="mb-5 text-sm text-[#8fa0bd]">Agent-generated scouting reports (deterministic pipeline, 0 LLM calls)</p>

        {!runs && <p className="text-[#8fa0bd]">Sign in on the Scouting page to generate reports.</p>}
        {runs && !runs.length && <p className="text-[#8fa0bd]">No reports yet — run a mission and an agent report on the Scouting page.</p>}

        {first?.report && (
          <div className="mb-6 max-w-2xl rounded-xl border border-[#1f2c44] bg-[#0e1626] p-5">
            <h2 className="mb-1 text-xl font-bold">{first.report.title}</h2>
            <p className="mb-4 text-sm text-[#8fa0bd]">{first.report.verdict} · {first.report.doctrine_total_flags} doctrine flags · {first.duration_ms} ms</p>
            {(first.report.candidates ?? []).slice(0, 8).map((c: any) => (
              <div key={c.player_id} className="flex items-center gap-3 border-t border-[#1f2c44] py-2 text-sm">
                <span className="w-6 text-[#8fa0bd]">#{c.rank}</span>
                <Link href={`/players/${c.player_id}`} className="flex-1 font-semibold hover:text-[#8cbfff]">{c.name}</Link>
                <span className="text-[#8cbfff]">{c.moneyball_score}</span>
                <span className="text-xs text-[#8fa0bd]">{c.position} · {c.age}y</span>
                <span className="text-xs text-[#ffcb8f]">{(c.flags ?? []).join(", ") || "—"}</span>
              </div>
            ))}
          </div>
        )}

        {runs?.length > 1 && (
          <div className="max-w-2xl">
            {runs.slice(1).map((r: any) => (
              <div key={r.id} className="mb-2 rounded-lg border border-[#1f2c44] bg-[#0e1626] p-3 text-sm">
                <span className="font-semibold">#{r.id}</span> · {r.request}
                <span className="ml-2 text-xs text-[#8fa0bd]">{r.status} · {r.llm_calls} LLM calls</span>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}