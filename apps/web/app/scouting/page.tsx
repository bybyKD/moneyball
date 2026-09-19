"use client";

import { useEffect, useState } from "react";
import SideNav from "@/components/side-nav";

type Cand = { rank: number; player_id: number; score: number; evidence: any };
type Mission = { id: number; title: string; status: string; constraints: any; candidates: Cand[] };
type Rep = { title?: string; verdict?: string; candidates?: any[]; doctrine_total_flags?: number };

const POSITIONS = ["GK", "CB", "FB", "DM", "CM", "AM", "W", "ST"];

export default function ScoutingPage() {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [shortlists, setShortlists] = useState<any[]>([]);
  const [report, setReport] = useState<Rep | null>(null);
  const [running, setRunning] = useState(false);
  const [draft, setDraft] = useState({ title: "Find my next #9", position: "ST", top_n: 5 });
  const [msg, setMsg] = useState("");
  const [authForm, setAuthForm] = useState({ email: "", password: "", display_name: "Demo Scout" });

  async function api(method: string, path: string, body?: any) {
    const r = await fetch(`/api${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
      credentials: "same-origin",
    });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error?.message ?? `${r.status}`);
    return r.json();
  }

  async function refresh() {
    try {
      setMissions(await api("GET", "/missions"));
      setShortlists(await api("GET", "/shortlists"));
      setAuthed(true);
    } catch {
      setAuthed(false);
    }
  }

  useEffect(() => { refresh(); }, []);

  async function doAuth(register: boolean) {
    try {
      await api("POST", `/auth/${register ? "register" : "login"}`, authForm);
      setMsg(""); await refresh();
    } catch (e: any) { setMsg(String(e.message)); }
  }

  async function createMission() {
    setRunning(true); setMsg("");
    try {
      const m = await api("POST", "/missions", draft);
      setMsg(`Mission #${m.id} ran — ${m.status}.`);
      await refresh();
    } catch (e: any) { setMsg(String(e.message)); }
    setRunning(false);
  }

  async function runReport(missionId: number) {
    setRunning(true); setMsg("");
    try {
      const r = await api("POST", "/agents/runs", { mission_id: missionId });
      setReport(r.report); setMsg(`Agent run ${r.id} — ${r.status} (${r.llm_calls} LLM calls, $${r.cost_usd}).`);
    } catch (e: any) { setMsg(String(e.message)); }
    setRunning(false);
  }

  async function addToShortlist(playerId: number) {
    if (!shortlists.length) {
      setMsg("Create a shortlist first.");
      return;
    }
    try { await api("POST", `/shortlists/${shortlists[0].id}/players/${playerId}`); setMsg("Added to shortlist."); }
    catch (e: any) { setMsg(String(e.message)); }
  }

  return (
    <div className="flex">
      <SideNav active="/missions" />
      <main className="flex-1 p-8">
        <h1 className="mb-4 text-3xl font-bold">Scouting Missions</h1>

        {authed === false && (
          <div className="mb-6 max-w-md rounded-xl border border-[#1f2c44] bg-[#0e1626] p-5">
            <div className="mb-3 text-sm text-[#8fa0bd]">Sign in to run missions (demo cookie auth — registers if new).</div>
            <input className="mb-2 w-full rounded bg-[#1f2c44] p-2 text-white" placeholder="email" value={authForm.email}
              onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })} />
            <input className="mb-2 w-full rounded bg-[#1f2c44] p-2 text-white" placeholder="password" type="password" value={authForm.password}
              onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })} />
            <input className="mb-3 w-full rounded bg-[#1f2c44] p-2 text-white" placeholder="display name" value={authForm.display_name}
              onChange={(e) => setAuthForm({ ...authForm, display_name: e.target.value })} />
            <div className="flex gap-2">
              <button onClick={() => doAuth(true)} className="rounded bg-[#8cbfff] px-4 py-2 text-sm font-semibold text-[#0e1626]">Register</button>
              <button onClick={() => doAuth(false)} className="rounded border border-[#1f2c44] px-4 py-2 text-sm text-white">Login</button>
            </div>
          </div>
        )}

        {authed && (
          <div className="mb-6 flex max-w-2xl gap-3 rounded-xl border border-[#1f2c44] bg-[#0e1626] p-5">
            <input className="flex-1 rounded bg-[#1f2c44] p-2 text-white" value={draft.title}
              onChange={(e) => setDraft({ ...draft, title: e.target.value })} placeholder="Mission title" />
            <select className="rounded bg-[#1f2c44] p-2 text-white" value={draft.position}
              onChange={(e) => setDraft({ ...draft, position: e.target.value })}>
              {POSITIONS.map((p) => <option key={p}>{p}</option>)}
            </select>
            <button onClick={createMission} disabled={running} className="rounded bg-[#8cbfff] px-4 py-2 font-semibold text-[#0e1626]">
              {running ? "…" : "Run mission"}
            </button>
          </div>
        )}
        {msg && <p className="mb-4 text-sm text-[#8cbfff]">{msg}</p>}

        {authed && missions.length > 0 && (
          <div className="max-w-3xl space-y-3">
            {missions.map((m) => (
              <div key={m.id} className="rounded-xl border border-[#1f2c44] bg-[#0e1626] p-5">
                <div className="mb-1 flex items-center gap-3">
                  <span className="font-semibold">#{m.id} · {m.title}</span>
                  <span className="rounded-full bg-[#1f2c44] px-2 py-0.5 text-xs text-[#8fa0bd]">{m.constraints?.position}</span>
                  <span className="text-xs text-[#8fa0bd]">{m.status}</span>
                </div>
                <div className="mt-2 grid grid-cols-1 gap-1 text-sm">
                  {(m.candidates ?? []).map((c) => (
                    <div key={c.player_id} className="flex items-center gap-3 border-t border-[#1f2c44] py-1.5">
                      <span className="w-6 text-[#8fa0bd]">#{c.rank}</span>
                      <span className="w-24 font-semibold text-[#8cbfff]">{c.score}</span>
                      <span className="flex-1 text-[#8fa0bd]">player {c.player_id}</span>
                      <span className="text-xs text-[#8fa0bd]">{(c.evidence?.minutes ?? 0).toLocaleString()} min</span>
                      <button onClick={() => addToShortlist(c.player_id)}
                        className="rounded border border-[#1f2c44] px-2 py-1 text-xs text-white hover:border-[#8cbfff]">Shortlist</button>
                    </div>
                  ))}
                </div>
                <button onClick={() => runReport(m.id)} disabled={running}
                  className="mt-3 rounded bg-[#1f2c44] px-3 py-1.5 text-sm text-white hover:bg-[#24344f]">Run agent report</button>
              </div>
            ))}
          </div>
        )}

        {report && (
          <div className="mt-6 max-w-2xl rounded-xl border border-[#1f2c44] bg-[#0e1626] p-5">
            <h2 className="mb-2 text-xl font-bold">{report.title}</h2>
            <p className="mb-3 text-sm text-[#8fa0bd]">{report.verdict} · {report.doctrine_total_flags} doctrine flags</p>
            {(report.candidates ?? []).slice(0, 5).map((c: any) => (
              <div key={c.player_id} className="flex items-center gap-3 border-t border-[#1f2c44] py-2 text-sm">
                <span className="w-6 text-[#8fa0bd]">#{c.rank}</span>
                <span className="flex-1 font-semibold">{c.name}</span>
                <span className="text-[#8cbfff]">{c.moneyball_score}</span>
                <span className="text-xs text-[#8fa0bd]">{(c.flags ?? []).join(", ") || "ok"}</span>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}