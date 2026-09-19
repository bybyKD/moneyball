import { cookies } from "next/headers";
import SideNav from "@/components/side-nav";

export const dynamic = "force-dynamic";
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default async function AgentsPage() {
  const cookieStore = await cookies();
  const cookie = cookieStore.toString();
  let runs: any[] = [];
  if (cookie) {
    try {
      const r = await fetch(`${BASE}/api/agents/runs`, { cache: "no-store", headers: { Cookie: cookie } });
      runs = r.ok ? await r.json() : [];
    } catch { /* ignore */ }
  }

  return (
    <div className="flex">
      <SideNav active="/agents" />
      <main className="flex-1 p-8">
        <h1 className="mb-1 text-3xl font-bold">AI Agents</h1>
        <p className="mb-5 text-sm text-[#8fa0bd]">Deterministic reference pipeline (orchestrator → collector → analyst → reviewer → writer) · 0 LLM calls in fallback mode</p>

        {!cookie && <p className="text-[#8fa0bd]">Sign in on the Scouting page, then run a mission to invoke agents.</p>}
        {cookie && !runs.length && <p className="text-[#8fa0bd]">No agent runs yet — run one from the Scouting page.</p>}

        <div className="max-w-2xl space-y-2">
          {runs.map((r: any) => (
            <div key={r.id} className="flex items-center gap-3 rounded-lg border border-[#1f2c44] bg-[#0e1626] p-3 text-sm">
              <span className="font-semibold">#{r.id}</span>
              <span className="flex-1">{r.request}</span>
              <span className={`rounded-full px-2 py-0.5 text-xs ${r.status === "complete" ? "bg-[#1a3326] text-[#7ce3a1]" : "bg-[#33291a] text-[#ffcb8f]"}`}>{r.status}</span>
              <span className="text-xs text-[#8fa0bd]">{r.llm_calls} calls</span>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}