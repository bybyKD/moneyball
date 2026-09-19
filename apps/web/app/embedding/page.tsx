"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import SideNav from "@/components/side-nav";

export default function EmbeddingPage() {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<any[]>([]);
  const [picked, setPicked] = useState<number | null>(null);
  const [similar, setSimilar] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);

  const search = useCallback(async (q: string) => {
    if (q.trim().length < 2) { setHits([]); return; }
    try {
      const r = await fetch(`/api/players?q=${encodeURIComponent(q)}&limit=8`);
      setHits(r.ok ? await r.json() : []);
    } catch { setHits([]); }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => search(query), 250);
    return () => clearTimeout(t);
  }, [query, search]);

  async function explore(playerId: number) {
    setPicked(playerId); setBusy(true); setSimilar([]);
    try {
      const r = await fetch(`/api/players/${playerId}/similar?k=6`);
      if (r.ok) {
        const d = await r.json();
        setHits([]);
        setSimilar(d.neighbors ?? []);
      }
    } catch { /* ignore */ }
    setBusy(false);
  }

  return (
    <div className="flex">
      <SideNav active="/embedding" />
      <main className="flex-1 p-8">
        <h1 className="mb-1 text-3xl font-bold">Semantic Search</h1>
        <p className="mb-5 text-sm text-[#8fa0bd]">pgvector lookalikes from the moneyball_demo_v1 tactical-profile embedding</p>

        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search a player by name…"
          className="mb-4 w-full max-w-md rounded bg-[#1f2c44] p-2 text-white placeholder:text-[#8fa0bd]" autoFocus />

        {hits.length > 0 && (
          <div className="mb-6 max-w-md space-y-1">
            {hits.map((p: any) => (
              <div key={p.id} className="flex items-center justify-between rounded border border-[#1f2c44] bg-[#0e1626] p-2 text-sm">
                <Link href={`/players/${p.id}`} className="text-[#8cbfff] hover:underline">{p.full_name}</Link>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-[#8fa0bd]">{p.primary_position}</span>
                  <button onClick={() => explore(p.id)} className="rounded bg-[#1f2c44] px-2 py-1 text-xs hover:bg-[#24344f]">
                    Lookalikes
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {busy && <p className="text-sm text-[#8fa0bd]">Nearest neighbors…</p>}

        {similar.length > 0 && (
          <div className="max-w-md rounded-xl border border-[#1f2c44] bg-[#0e1626] p-5">
            <div className="mb-3 text-xs text-[#8fa0bd]">moneyball_demo_v1 · L2 distance ≈ cosine similarity</div>
            {similar.map((n: any) => (
              <li key={n.player_id} className="flex items-center gap-3 py-1.5 text-sm">
                <span className="w-10 text-[#8cbfff]">{Math.round(n.similarity * 100)}%</span>
                <Link href={`/players/${n.player_id}`} className="hover:text-[#8cbfff]">{n.name}</Link>
              </li>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}