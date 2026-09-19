"""StatsBomb Open Data adapter — real, licensed event-level football data.

Loads the Hudl ``statsbomb/open-data`` repository into the Moneyball schema:

    competitions.json           -> leagues, competitions, seasons
    matches/{comp}/{season}.json -> clubs (teams)
    lineups/{match}.json        -> players (id, name, minutes, positions)
    events/{match}.json         -> per-player seasonal aggregates (55 stat cols)

* **Deterministic & idempotent** — reseeding wipes only ``provider=statsbomb``
  rows in FK order, then re-inserts.
* **Honest bios** — open data has no DOB/nationality/height/foot, so those stay
  ``NULL`` and ``profile.bios_known`` is ``false``; nothing is fabricated.
* **Attribution** — a ``sources`` row records the explicit StatsBomb
  requirement (state source + logo when publishing; see docs/attribution.md).
* **Documented approximations** — open data has no ready SCA/GCA, pressure-
  success, or progressive metrics, so those are derived here with standard,
  reproducible rules instead of invented values.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
from datetime import date
from pathlib import Path

from apps.api.app.db.models.football import (
    Club,
    Competition,
    League,
    Player,
    PlayerSeasonStat,
    Season,
)
from apps.api.app.db.models.market import Source
from apps.api.app.db.session import get_session
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

PROVIDER = "statsbomb"
REPO_URL = "https://github.com/statsbomb/open-data.git"
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RAW_DIR = REPO_ROOT / "data" / "raw" / "statsbomb"


def _data_root(raw: Path | str) -> Path:
    """The repo nests everything under ``data/``; unwrap it when needed."""
    raw = Path(raw)
    nested = raw / "data"
    if (nested / "competitions.json").exists():
        return nested
    return raw

ATTRIBUTION_TEXT = (
    "State the data source as StatsBomb and use the StatsBomb logo (Media Pack) "
    "when publishing research based on this data."
)

REGION_BOX = (102.0, 18.0, 120.0, 62.0)  # attacking box (attacking direction = +x)
FINAL_THIRD_X = 80.0
LONG_PASS_MIN_LEN = 30.0  # metres
PRESSURE_WIN_SECONDS = 6.0

POSITION_MAP = {
    "Goalkeeper": "GK",
    "Center Back": "CB", "Right Center Back": "CB", "Left Center Back": "CB",
    "Right Back": "FB", "Left Back": "FB",
    "Wing Back": "FB", "Right Wing Back": "FB", "Left Wing Back": "FB",
    "Defensive Midfield": "DM", "Holding Midfield": "DM",
    "Central Midfield": "CM", "Center Midfield": "CM",
    "Left Midfield": "AM", "Right Midfield": "AM", "Attacking Midfield": "AM",
    "Left Attack Midfield": "AM", "Right Attack Midfield": "AM", "Attacking Midfielder": "AM",
    "Left Wing": "W", "Right Wing": "W", "Center Wing": "W", "Winger": "W",
    "Striker": "ST", "Centre Forward": "ST", "Center Forward": "ST", "Second Striker": "ST",
}

SHOT_ON_TARGET_OUTCOMES = {"Goal", "Saved"}
DUEL_TYPES = {"Tackle", "Ground Loose Ball"}
AERIAL_TYPES = {"Aerial Lost", "Aerial Won"}
DRIBBLE_COMPLETE = {"Complete", "Complete (Player)", "Complete (Team)"}

PSS_INT_KEYS = [
    "goals", "assists", "penalty_goals", "shots", "shots_on_target", "touches_in_box",
    "shot_creating_actions", "goal_creating_actions", "passes_attempted", "passes_completed",
    "progressive_passes", "key_passes", "final_third_passes", "passes_into_box",
    "through_balls", "long_passes_attempted", "long_passes_completed",
    "progressive_passing_distance", "carries", "progressive_carries", "carries_into_box",
    "carries_into_final_third", "carry_distance", "progressive_carry_distance",
    "successful_dribbles", "dribbles_attempted", "miscontrols", "dispossessions",
    "touches", "tackles", "interceptions", "blocks", "clearances",
    "defensive_duels_won", "defensive_duels_total", "aerial_duels_won", "aerial_duels_total",
    "pressures", "pressures_successful", "ball_recoveries", "yellow_cards", "red_cards",
]
PSS_FLOAT_KEYS = ["xg", "npxg", "xa"]
PSS_ALL_KEYS = PSS_INT_KEYS + PSS_FLOAT_KEYS
PSS_INSERT_KEYS = PSS_ALL_KEYS + ["minutes_played", "appearances", "starts", "subs"]


def slugify(s: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in s).strip("-").replace("--", "-")


def _mapped_position(name: str) -> str | None:
    return POSITION_MAP.get(name)


def _progressive_gain(start: list | None, end: list | None) -> float:
    """Net forward metres (attacking direction = +x); 0 if not progressive."""
    if not start or not end or len(start) < 2 or len(end) < 2:
        return 0.0
    dx = float(end[0]) - float(start[0])
    dy = float(end[1]) - float(start[1])
    if dx <= 0:
        return 0.0
    dist = math.hypot(dx, dy)
    if dx >= 10.0:
        return dx
    if dist > 0 and dx / dist >= 0.3 and dx >= 5.0:
        return dx
    return 0.0


def _in_box(x: float, y: float) -> bool:
    return REGION_BOX[0] <= x <= REGION_BOX[2] and REGION_BOX[1] <= y <= REGION_BOX[3]


def _in_final_third(x: float) -> bool:
    return x >= FINAL_THIRD_X


def _secs_from_timestamp(ts: str) -> float:
    try:
        h, m, s = ts.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception:
        return 0.0


def _lineup_minutes(v, default: int) -> int:
    """Lineup ``from``/``to`` are 'MM:SS' clock strings or plain minute ints."""
    if v is None:
        return default
    s = str(v).strip()
    if not s:
        return default
    try:
        if ":" in s:
            return int(float(s.split(":")[0]))
        return int(float(s))
    except Exception:
        return default


def _split_name(full: str) -> tuple[str, str]:
    parts = full.strip().split()
    if len(parts) <= 1:
        return full.strip(), full.strip()
    return parts[0], " ".join(parts[1:])


def _inc(acc: dict, k: str, step: int = 1) -> None:
    acc[k] = acc.get(k, 0) + step


def _add(acc: dict, k: str, v: float) -> None:
    acc[k] = acc.get(k, 0.0) + float(v)


async def _run(cmd: list[str]) -> None:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
    )
    _, err = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({cmd[0]}): {err.decode(errors='replace')}")


async def ensure_raw(raw_dir: Path | None = None) -> Path:
    """Shallow-clone the open-data repo once (large; ~17 GB working tree)."""
    root = raw_dir or DEFAULT_RAW_DIR
    if (root / "competitions.json").exists() or (root / "data" / "competitions.json").exists():
        return root
    root.parent.mkdir(parents=True, exist_ok=True)
    await _run(["git", "clone", "--depth", "1", REPO_URL, str(root)])
    if not ((root / "competitions.json").exists() or (root / "data" / "competitions.json").exists()):
        raise RuntimeError(f"clone produced no competitions.json in {root}")
    return root


class StatsBombLoader:
    """Loads a StatsBomb open-data checkout into the schemata for one provider."""

    def __init__(self, session: AsyncSession, raw_dir: Path | None = None, provider: str = PROVIDER) -> None:
        self.session = session
        self.raw_dir = _data_root(raw_dir or DEFAULT_RAW_DIR)
        self.provider = provider
        self._leagues: dict[str, League] = {}
        self._competitions: dict[str, Competition] = {}
        self._seasons: dict[str, Season] = {}
        self._clubs: dict[str, Club] = {}
        self._players: dict[str, Player] = {}
        self._pss: dict[tuple[int, int, int], dict] = {}
        self._player_season_pos: dict[tuple[int, int], dict[str, int]] = {}
        self._player_primary_pos: dict[int, dict[str, int]] = {}
        self.stats = {
            "leagues": 0, "competitions": 0, "seasons": 0,
            "clubs": 0, "players": 0, "matches": 0, "pss": 0,
        }

    # ------------------------------------------------------------------ wipe
    async def wipe_provider(self) -> None:
        s = self.session
        sq = "(SELECT id FROM players WHERE provider = :p)"
        for stmt in (
            "DELETE FROM player_season_stats WHERE provider = :p",
            "DELETE FROM player_match_stats WHERE player_id IN " + sq,
            "DELETE FROM mission_candidates WHERE player_id IN " + sq,
            "DELETE FROM shortlist_players WHERE player_id IN " + sq,
            "DELETE FROM player_positions WHERE player_id IN " + sq,
            "DELETE FROM player_roles WHERE player_id IN " + sq,
            "DELETE FROM player_embeddings WHERE provider = :p",
            "DELETE FROM market_values WHERE player_id IN " + sq,
            "DELETE FROM contracts WHERE player_id IN " + sq,
            "DELETE FROM injuries WHERE player_id IN " + sq,
            "DELETE FROM transfers WHERE player_id IN " + sq,
            "DELETE FROM players WHERE provider = :p",
            "DELETE FROM clubs WHERE provider = :p",
            "DELETE FROM competitions WHERE provider = :p",
            "DELETE FROM seasons WHERE provider = :p",
            "DELETE FROM leagues WHERE provider = :p",
            "DELETE FROM sources WHERE provider = :p",
        ):
            await s.execute(text(stmt).bindparams(p=self.provider))
        await s.commit()

    # ----------------------------------------------------------- competitions
    async def load_competitions(self, competition_ids: set[int] | None = None) -> None:
        comps = json.loads((self.raw_dir / "competitions.json").read_text(encoding="utf-8"))
        for rec in comps:
            cid = int(rec["competition_id"])
            if competition_ids is not None and cid not in competition_ids:
                continue
            ckey = str(cid)
            sid = int(rec["season_id"])
            if ckey not in self._leagues:
                country_code = (rec.get("country_code") or "").strip()[:3] or "INT"
                country_name = (rec.get("country_name") or "").strip() or "International"
                cname = rec.get("competition_name") or f"Comp {cid}"
                ccode = rec.get("competition_code") or f"SB{cid}"
                league = League(
                    name=cname,
                    country_code=country_code,
                    country_name=country_name,
                    code=ccode,
                    level=1,
                    provider=self.provider,
                )
                self.session.add(league)
                await self.session.flush()  # league.id needed for competitions.league_id
                comp = Competition(
                    league_id=league.id,
                    name=cname,
                    kind="international" if bool(rec.get("competition_international")) else "league",
                    gender="female" if rec.get("competition_gender") == "female" else "male",
                    provider=self.provider,
                    provider_id=str(cid),
                )
                self.session.add(comp)
                self._leagues[ckey] = league
                self._competitions[ckey] = comp
                self.stats["leagues"] += 1
                self.stats["competitions"] += 1
            skey = f"{ckey}:{sid}"
            if skey not in self._seasons:
                end_year = int(rec.get("season_end_year") or 0)
                season = Season(
                    name=rec.get("season_name") or str(sid),
                    start_year=int(rec.get("season_start_year") or 0),
                    end_year=end_year,
                    is_current=end_year >= 2025,
                    provider=self.provider,
                    provider_id=f"{cid}:{sid}",
                )
                self.session.add(season)
                self._seasons[skey] = season
                self.stats["seasons"] += 1
        await self.session.flush()
        await self.session.commit()

    # ------------------------------------------------------------ clubs/lineups
    async def load_competition_season(self, competition_id: int, season_id: int) -> None:
        ckey = str(competition_id)
        skey = f"{ckey}:{season_id}"
        comp = self._competitions.get(ckey)
        season = self._seasons.get(skey)
        if comp is None or season is None:
            return
        mpath = self.raw_dir / "matches" / ckey / f"{season_id}.json"
        if not mpath.exists():
            return
        matches = json.loads(mpath.read_text(encoding="utf-8"))
        for m in matches:
            await self._load_match(m, comp, season)
        await self._flush_batches()

    async def _load_match(self, m: dict, comp: Competition, season: Season) -> None:
        s = self.session
        mid = int(m["match_id"])
        league = self._leagues.get(str(comp.provider_id))

        new_clubs: list[Club] = []
        for side in ("home_team", "away_team"):
            team = m[side]
            base = side.split("_")[0]  # home|away
            tid = str(team.get(f"{base}_team_id") or team.get("team_id"))
            name = team.get(f"{base}_team_name") or team.get("team_name")
            if tid not in self._clubs:
                club = Club(
                    slug=slugify(f"{name}-{tid}"),
                    name=name,
                    country_code=league.country_code if league else "INT",
                    country_name=league.country_name if league else "International",
                    league_id=comp.league_id,
                    provider=self.provider,
                    provider_id=tid,
                )
                s.add(club)
                self._clubs[tid] = club
                new_clubs.append(club)
                self.stats["clubs"] += 1
        if new_clubs:
            await s.flush()

        lineup_path = self.raw_dir / "lineups" / f"{mid}.json"
        if not lineup_path.exists():
            return
        lineups = json.loads(lineup_path.read_text(encoding="utf-8"))
        match_stats: dict[int, dict] = {}
        new_players = False

        for team_lineup in lineups:
            team_id = str(team_lineup["team_id"])
            club = self._clubs[team_id]
            for entry in team_lineup["lineup"]:
                pid = str(entry["player_id"])
                player = self._players.get(pid)
                if player is None:
                    full = entry.get("player_name") or entry.get("player_nickname") or f"Player {pid}"
                    first, last = _split_name(full)
                    player = Player(
                        slug=slugify(f"{full}-{pid}"),
                        full_name=full,
                        first_name=first,
                        last_name=last,
                        primary_position="ST",
                        current_club_id=club.id,
                        provider=self.provider,
                        provider_id=pid,
                        profile={
                            "provider": self.provider,
                            "bios_known": False,
                            "statsbomb_player_id": pid,
                        },
                    )
                    s.add(player)
                    self._players[pid] = player
                    self.stats["players"] += 1
                    new_players = True
                else:
                    player.current_club_id = club.id

                minutes = 0
                pos_minutes: dict[str, int] = {}
                started = False
                for p in entry.get("positions", []):
                    frm = _lineup_minutes(p.get("from"), 0)
                    to = _lineup_minutes(p.get("to"), 90)
                    mm = max(0, to - frm)
                    minutes += mm
                    if frm == 0 and (p.get("from_period") in (None, 1)):
                        started = True
                    pos_raw = p.get("position")
                    if isinstance(pos_raw, dict):
                        pos_raw = pos_raw.get("name") or ""
                    pos = _mapped_position(pos_raw or "")
                    if pos:
                        pos_minutes[pos] = pos_minutes.get(pos, 0) + mm
                nat = (entry.get("country") or {}).get("name")
                if nat and not player.nationality_name:
                    player.nationality_name = nat

                acc = match_stats.setdefault(int(pid), {
                    "minutes": 0, "starts": 0, "appearances": 0, "pos_minutes": {},
                })
                acc["club"] = club
                if minutes > 0:
                    acc["appearances"] = 1
                acc["minutes"] += minutes
                if started:
                    acc["starts"] = 1
                for pos, mm in pos_minutes.items():
                    acc["pos_minutes"][pos] = acc["pos_minutes"].get(pos, 0) + mm

        if new_players:
            await s.flush()

        if not match_stats:
            return

        events_path = self.raw_dir / "events" / f"{mid}.json"
        if not events_path.exists():
            self.stats["matches"] += 1
            return
        events = json.loads(events_path.read_text(encoding="utf-8"))
        self._aggregate_events(events, comp, season, match_stats)
        self.stats["matches"] += 1

    # ---------------------------------------------------------------- events
    def _aggregate_events(
        self, events: list[dict], comp: Competition, season: Season, match_stats: dict[int, dict]
    ) -> None:
        shot_xg: dict[str, float] = {}
        by_team: dict[int, list[dict]] = {}
        for ev in events:
            if ev.get("type", {}).get("name") == "Shot":
                shot_xg[str(ev.get("id"))] = float(ev.get("shot", {}).get("statsbomb_xg") or 0.0)
            tid = ev.get("team", {}).get("id")
            if tid is not None:
                by_team.setdefault(int(tid), []).append(ev)

        def pressure_success(team_id: int, idx: int) -> bool:
            team_events = by_team[team_id]
            anchor_t = _secs_from_timestamp(team_events[idx].get("timestamp") or "")
            for j in range(idx + 1, min(idx + 12, len(team_events))):
                nxt = team_events[j]
                if _secs_from_timestamp(nxt.get("timestamp") or "") - anchor_t > PRESSURE_WIN_SECONDS:
                    break
                typ = nxt.get("type", {}).get("name")
                if typ in ("Ball Recovery", "Interception"):
                    return True
                if typ == "Duel" and (nxt.get("duel", {}).get("outcome", {}).get("name") == "Won"):
                    return True
            return False

        for team_id, team_events in by_team.items():
            for idx, ev in enumerate(team_events):
                pid = int(ev.get("player", {}).get("id") or 0)
                if pid == 0 or pid not in match_stats:
                    continue
                typ = ev.get("type", {}).get("name")
                loc = ev.get("location") or []
                x = float(loc[0]) if len(loc) > 0 else 0.0
                y = float(loc[1]) if len(loc) > 1 else 0.0
                acc = match_stats.setdefault(pid, {"touches": 0})
                acc["touches"] = acc.get("touches", 0) + 1

                if typ == "Shot":
                    shot = ev.get("shot", {})
                    _inc(acc, "shots")
                    if (shot.get("outcome") or {}).get("name") in SHOT_ON_TARGET_OUTCOMES:
                        _inc(acc, "shots_on_target")
                    xg = float(shot.get("statsbomb_xg") or 0.0)
                    _add(acc, "xg", xg)
                    if (shot.get("type") or {}).get("name") != "Penalty":
                        _add(acc, "npxg", xg)
                    if (shot.get("outcome") or {}).get("name") == "Goal":
                        _inc(acc, "goals")
                        if (shot.get("type") or {}).get("name") == "Penalty":
                            _inc(acc, "penalty_goals")
                elif typ == "Pass":
                    p = ev.get("pass", {})
                    _inc(acc, "passes_attempted")
                    complete = not p.get("outcome")
                    if complete:
                        _inc(acc, "passes_completed")
                    end = p.get("end_location")
                    ex, ey = (end[0], end[1]) if end and len(end) > 1 else (x, y)
                    if _in_final_third(ex):
                        _inc(acc, "final_third_passes")
                    if _in_box(ex, ey):
                        _inc(acc, "passes_into_box")
                    gain = _progressive_gain(loc, end)
                    if gain > 0:
                        _inc(acc, "progressive_passes")
                        _add(acc, "progressive_passing_distance", gain)
                    if float(p.get("length") or 0.0) >= LONG_PASS_MIN_LEN:
                        _inc(acc, "long_passes_attempted")
                        if complete:
                            _inc(acc, "long_passes_completed")
                    if (p.get("technique") or {}).get("name") == "Through Ball":
                        _inc(acc, "through_balls")
                    if p.get("goal_assist"):
                        _inc(acc, "assists")
                        _inc(acc, "goal_creating_actions")
                    if p.get("shot_assist"):
                        _inc(acc, "key_passes")
                        _inc(acc, "shot_creating_actions")
                        shot_id = p.get("assisted_shot_id")
                        if shot_id is not None and str(shot_id) in shot_xg:
                            _add(acc, "xa", shot_xg[str(shot_id)])
                elif typ == "Carries":
                    carry = ev.get("carry", {})
                    end = carry.get("end_location")
                    _inc(acc, "carries")
                    gain = _progressive_gain(loc, end)
                    if gain > 0:
                        _inc(acc, "progressive_carries")
                        _add(acc, "progressive_carry_distance", gain)
                    ex, ey = (end[0], end[1]) if end and len(end) > 1 else (x, y)
                    if _in_box(ex, ey):
                        _inc(acc, "carries_into_box")
                    if _in_final_third(ex):
                        _inc(acc, "carries_into_final_third")
                    dist = math.hypot(ex - x, ey - y)
                    _add(acc, "carry_distance", dist)
                elif typ == "Dribbles":
                    _inc(acc, "dribbles_attempted")
                    if (ev.get("dribble", {}).get("outcome") or {}).get("name") in DRIBBLE_COMPLETE:
                        _inc(acc, "successful_dribbles")
                elif typ == "Miscontrol":
                    _inc(acc, "miscontrols")
                elif typ == "Dispossessed":
                    _inc(acc, "dispossessions")
                elif typ == "Interception":
                    _inc(acc, "interceptions")
                elif typ == "Clearance":
                    _inc(acc, "clearances")
                elif typ == "Block":
                    _inc(acc, "blocks")
                elif typ == "Ball Recovery":
                    _inc(acc, "ball_recoveries")
                elif typ == "Pressure":
                    _inc(acc, "pressures")
                    if pressure_success(team_id, idx):
                        _inc(acc, "pressures_successful")
                elif typ == "Duel":
                    duel = ev.get("duel", {})
                    dtype = (duel.get("type") or {}).get("name")
                    won = (duel.get("outcome") or {}).get("name") == "Won"
                    if dtype in DUEL_TYPES:
                        _inc(acc, "defensive_duels_total")
                        if won:
                            _inc(acc, "defensive_duels_won")
                        if dtype == "Tackle":
                            _inc(acc, "tackles")
                    elif dtype in AERIAL_TYPES:
                        _inc(acc, "aerial_duels_total")
                        if dtype == "Aerial Won" or won:
                            _inc(acc, "aerial_duels_won")
                elif typ == "Card":
                    card = (ev.get("card") or {}).get("name")
                    if card == "Yellow Card":
                        _inc(acc, "yellow_cards")
                    elif card in ("Red Card", "Second Yellow"):
                        _inc(acc, "red_cards")
                if _in_box(x, y):
                    _inc(acc, "touches_in_box")

        for pid, acc in match_stats.items():
            if acc.get("appearances", 0) == 0 and acc.get("touches", 0) == 0:
                continue
            player = self._players.get(str(pid))
            if player is None:
                continue
            pos_min = acc.get("pos_minutes", {})
            pos = max(pos_min.items(), key=lambda kv: kv[1])[0] if pos_min else player.primary_position
            key = (player.id, comp.id, season.id)
            row = self._pss.get(key)
            if row is None:
                row = {k: 0 for k in PSS_ALL_KEYS}
                row.update({"minutes_played": 0, "appearances": 0, "starts": 0, "subs": 0})
                row["club"] = acc.get("club")
                self._pss[key] = row
            for k in PSS_INT_KEYS:
                row[k] += acc.get(k, 0)
            for k in PSS_FLOAT_KEYS:
                row[k] += acc.get(k, 0.0)
            row["minutes_played"] += acc.get("minutes", 0)
            row["appearances"] += acc.get("appearances", 0)
            row["starts"] += acc.get("starts", 0)
            row["subs"] = row["appearances"] - row["starts"]
            psc = self._player_season_pos.setdefault((player.id, comp.id, season.id), {})
            psc[pos] = psc.get(pos, 0) + acc.get("minutes", 0)
            agg = self._player_primary_pos.setdefault(player.id, {})
            agg[pos] = agg.get(pos, 0) + acc.get("minutes", 0)

    async def _flush_batches(self) -> None:
        s = self.session
        for (pid, cid, sid), row in self._pss.items():
            player = self._players.get(str(pid))
            posc = self._player_season_pos.get((pid, cid, sid), {})
            position = (max(posc.items(), key=lambda kv: kv[1])[0] if posc else None) or (
                player.primary_position if player else "ST"
            )
            club = row.get("club")
            club_id = club.id if club else (player.current_club_id if player else 0)
            s.add(
                PlayerSeasonStat(
                    player_id=pid,
                    season_id=sid,
                    competition_id=cid,
                    club_id=club_id,
                    position=position,
                    provider=self.provider,
                    **{k: row[k] for k in PSS_INSERT_KEYS},
                )
            )
            self.stats["pss"] += 1
        for pid, pos_map in self._player_primary_pos.items():
            player = self._players.get(str(pid))
            if player and pos_map:
                player.primary_position = max(pos_map.items(), key=lambda kv: kv[1])[0]
        self._pss.clear()
        self._player_season_pos.clear()
        await s.flush()
        await s.commit()

    # ----------------------------------------------------------------- source
    async def add_source_row(self) -> None:
        exists = await self.session.scalar(
            text("SELECT id FROM sources WHERE provider = :p").bindparams(p=self.provider)
        )
        if exists:
            return
        self.session.add(
            Source(
                name="StatsBomb Open Data",
                provider=self.provider,
                kind="dataset",
                url="https://github.com/statsbomb/open-data",
                attribution_required=ATTRIBUTION_TEXT,
                last_updated=date.today(),
            )
        )
        await self.session.commit()


async def load_all(
    raw_dir: Path | None = None,
    competition_ids: set[int] | None = None,
    provider: str = PROVIDER,
    wipe: bool = True,
) -> dict:
    """Entry point used by scripts and tests."""
    raw_dir = raw_dir or await ensure_raw(raw_dir)
    data_dir = _data_root(raw_dir)
    async for session in get_session():
        loader = StatsBombLoader(session, raw_dir=data_dir, provider=provider)
        if wipe:
            await loader.wipe_provider()
        comps = json.loads((data_dir / "competitions.json").read_text(encoding="utf-8"))
        wanted: dict[int, set[int]] = {}
        for r in comps:
            cid = int(r["competition_id"])
            if competition_ids is None or cid in competition_ids:
                wanted.setdefault(cid, set()).add(int(r["season_id"]))
        await loader.load_competitions(competition_ids or None)
        for cid in sorted(wanted):
            for sid in sorted(wanted[cid]):
                await loader.load_competition_season(cid, sid)
        await loader.add_source_row()
        return loader.stats


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(description="Load StatsBomb Open Data into Moneyball")
    parser.add_argument("--repo", type=Path, default=DEFAULT_RAW_DIR, help="path to the open-data checkout")
    parser.add_argument("--comps", type=str, default=None, help="comma-separated competition ids (default: all)")
    parser.add_argument("--provider", type=str, default=PROVIDER)
    parser.add_argument("--no-clone", action="store_true", help="fail instead of cloning when data is missing")
    args = parser.parse_args()

    async def _main() -> None:
        if args.no_clone and not (args.repo / "competitions.json").exists():
            raise SystemExit(f"no data at {args.repo} (--no-clone); clone once first")
        comps = {int(c.strip()) for c in args.comps.split(",") if c.strip()} if args.comps else None
        stats = await load_all(raw_dir=args.repo, competition_ids=comps, provider=args.provider)
        print("Loaded StatsBomb dataset: " + ", ".join(f"{k}={v}" for k, v in stats.items()))

    asyncio.run(_main())
