import SideNav from "@/components/side-nav";

export const runtime = "nodejs";

export default function SettingsPage() {
  const env = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  return (
    <div className="flex">
      <SideNav active="/settings" />
      <main className="flex-1 p-8">
        <h1 className="mb-1 text-3xl font-bold">Settings</h1>
        <p className="mb-5 text-sm text-[#8fa0bd]">Platform configuration</p>

        <div className="max-w-md space-y-2 rounded-xl border border-[#1f2c44] bg-[#0e1626] p-5 text-sm">
          {[
            ["Web → API", env],
            ["Demo data", "5,000 players · 220 clubs · 18 leagues · 5 seasons (`make seed`)"],
            ["Embeddings", "pgvector 512-dim HNSW — moneyball_v1 (`make embed`)"],
            ["Analytics", "deterministic per-90 + position-cohort percentiles (no LLM)"],
            ["Agent mode", "reference pipeline · 0 LLM calls · provider-agnostic (§38)"],
            ["Auth", "cookie session · PBKDF2 password · demo scope only"],
          ].map(([k, v]) => (
            <div key={k} className="flex justify-between gap-4 border-b border-[#1f2c44] py-2">
              <span className="text-[#8fa0bd]">{k}</span>
              <span className="text-left text-white">{v}</span>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}