"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import SideNav from "@/components/side-nav";

export default function ComparePage() {
  const [players, setPlayers] = useState<any[]>([]);
  const [a, setA] = useState<number | 0>(0);
  const [b, setB] = useState<number | 0>(0);
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    fetch("/api/players?limit=200").then((r) => r.json()).then(setPlayers).catch(() => setErr("API unavailable"));
  }, []);

  async function run() {
    if (!a || !b) { setErr("Pick two players."); return; }
    setErr("");
    try {
      const r = await fetch(`/api/compare?player_a=${a}&player_b=${b}`);
      if (!r.ok) throw new Error(String(r.status));
      setData(await r.json());
    } catch (e: any) { setErr(String(e.message)); }
  }

  const sel = (val: number, set: any) => (
    <select value={val} onChange={(e) => set(Number(e.target.value))}
      className="flex-1 rounded bg-[#1f2c44] p-2 text-white">
      <option value={0}>— pick player —</option>
      {players.map((p: any) => <option key={p.id} value={p.id}>{p.full_name} ({p.primary_position})</option>)}
    </select>
  );

  const side = data?.players ?? [];
  return (
    <div className="flex">
      <SideNav active="/players/compare" />
      <main className="flex-1 p-8">
        <h1 className="mb-4 text-3xl font-bold">Compare Players</h1>
        <div className="mb-4 flex max-w-2xl gap-3">
          {sel(a, setA)}
          {sel(b, setB)}
          <button onClick={run} className="rounded bg-[#8cbfff] px-4 py-2 font-semibold text-[#0e1626]">Compare</button>
        </div>
        {err && <p className="mb-4 text-sm text-[#ff9d8f]">{err}</p>}

        {data?.winner && (
          <p className="mb-4 text-sm text-[#8cbfff]">
            Winner by Moneyball score: {data.winner.name} ({data.winner.score})
          </p>
        )}

        {side.length === 2 && (
          <div className="max-w-3xl overflow-hidden rounded-xl border border-[#1f2c44]">
            <table className="w-full text-sm">
              <thead className="bg-[#1f2c44] text-xs text-[#8fa0bd]">
                <tr>
                  <th className="px-4 py-2 text-left font-medium">Metric</th>
                  {side.map((s: any) => (
                    <th key={s.player_id} className="px-4 py-2 text-right font-medium">
                      <Link href={`/players/${s.player_id}`} className="text-white hover:text-[#8cbfff]">{s.name}</Link>
                      <div className="font-normal">score {s.score} · €{s.market_value_eur?.toLocaleString()}</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr className="bg-[#0c1322]">
                  <td className="px-4 py-2 text-[#8fa0bd]">Position / minutes</td>
                  {side.map((s: any) => <td key={s.player_id} className="px-4 py-2 text-right">{s.position} · {s.minutes}</td>)}
                </tr>
                {(data.metrics ?? []).map((k: string, i: number) => (
                  <tr key={k} className={(i % 2 ? "bg-[#0c1322]" : "bg-[#0e1626]")}>
                    <td className="px-4 py-1.5 text-[#8fa0bd]">{k}</td>
                    {side.map((s: any) => (
                      <td key={s.player_id} className="px-4 py-1.5 text-right text-[#8cbfff]">
                        {s.percentiles?.[k] != null ? Math.round(s.percentiles[k] * 100) + "%" : "—"}
                      </td>
                    ))}
                  </tr>
                ))}
                <tr className="bg-[#0c1322]">
                  <td className="px-4 py-2 text-[#8fa0bd]">per-90 goals</td>
                  {side.map((s: any) => <td key={s.player_id} className="px-4 py-2 text-right">{s.per90?.goals ?? "—"}</td>)}
                </tr>
              </tbody>
            </table>
            {data.metrics?.length === 0 && <p className="p-4 text-sm text-[#8fa0bd]">Different positions — no overlapping percentile metrics. Compare per-90 output instead.</p>}
          </div>
        )}
      </main>
    </div>
  );
}