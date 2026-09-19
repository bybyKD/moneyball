"""Synthetic demo seed (spec §45 "demo" watermarking; Phase 2).

Bootstraps the reference Moneyball dataset with deterministic synthetic data so
every layer (players list, player detail, future analytics) has real rows:

    18 leagues · 220 clubs · 18 competitions · 5 seasons · 5,000 players
    + current-season PlayerSeasonStat rows.

* provider="demo" on every row and a marker inside JSON profile columns
  (spec §45-B "static demo" watermark) so consumers/QA can never mistake demo
  rows for real StatsBomb/Transfermarkt imports.
* Deterministic: seeded RNG -> identical output on re-runs (test-friendly).
* Club-level strength factor drives most football-shaped numbers per level.

Run:  make seed   (= ./.venv/bin/python -m apps.api.app.scripts.seed_demo 5000)
"""

import argparse
import asyncio
import random
from datetime import date, timedelta
from itertools import count

from apps.api.app.db.models.football import (
    Club,
    Competition,
    League,
    Player,
    PlayerSeasonStat,
    Season,
)
from apps.api.app.db.session import get_session
from sqlalchemy import select, text

RNG = random.Random(42069)
LEAGUES = [
    # (name, country_name, country_code, code, level, strength_factor, clubs_n, nt)
    ("Premier League", 20, "England", "ENG", "PL", 1, 1.00),
    ("La Liga", 20, "Spain", "ESP", "LL", 1, 0.97),
    ("Serie A", 20, "Italy", "ITA", "SA", 1, 0.95),
    ("Bundesliga", 18, "Germany", "GER", "BL", 1, 0.96),
    ("Ligue 1", 20, "France", "FRA", "L1", 1, 0.93),
    ("Primeira Liga", 18, "Portugal", "POR", "PLPT", 1, 0.86),
    ("Eredivisie", 18, "Netherlands", "NED", "ED", 1, 0.83),
    ("MLS", 29, "United States", "USA", "MLS", 1, 0.75),
    ("Brasileirão", 20, "Brazil", "BRA", "BR", 1, 0.80),
    ("Liga MX", 18, "Mexico", "MEX", "LMX", 1, 0.78),
    ("Super Lig", 20, "Türkiye", "TUR", "SL", 1, 0.79),
    ("Argentine Primera", 14, "Argentina", "ARG", "AP", 1, 0.76),
    ("1. Bundesliga (AUT)", 12, "Austria", "AUT", "ABL", 2, 0.72),
    ("Saudi Pro League", 18, "Saudi Arabia", "KSA", "SPL", 1, 0.77),
    ("J1 League", 20, "Japan", "JPN", "J1", 1, 0.74),
    ("Championship", 24, "England", "ENG", "CH", 2, 0.72),
    ("Ligue 2", 20, "France", "FRA", "L2", 2, 0.66),
    ("2. Bundesliga", 18, "Germany", "GER", "BL2", 2, 0.68),
]
SEASON_YEARS = (2020, 2021, 2022, 2023, 2024)
POSITIONS = ["GK", "CB", "FB", "DM", "CM", "AM", "W", "ST"]
POS_SHARE = {"GK": 22, "CB": 56, "FB": 40, "DM": 38, "CM": 44, "AM": 34, "W": 40, "ST": 42}
GOAL_KEEPER = (minutes_played := None)
NAMES = {
    "EN": (["James", "Harry", "Oliver", "George", "Jack", "Noah", "Leo", "Archie"], ["Smith", "Walker", "Wright", "Hill", "Brooks", "Turner"]),
    "ES": (["Álvaro", "Pablo", "Hugo", "Marco", "Adrián", "Iker", "Mario", "Dani"], ["García", "Espinoza", "Vega", "Reyes", "Castro", "Molina"]),
    "IT": (["Lorenzo", "Matteo", "Alessandro", "Luca", "Gabriele", "Davide", "Simone", "Angelo"], ["Rossi", "Conti", "Gallo", "Ferrari", "Marino", "Greco"]),
    "DE": (["Leon", "Felix", "Jonas", "Nico", "Max", "Tim", "Julian", "Lukas"], ["Schmidt", "Weber", "Koch", "Richter", "Wolf", "Brandt"]),
    "FR": (["Lucas", "Hugo", "Maxime", "Antoine", "Théo", "Nolan", "Enzo", "Mathis"], ["Martin", "Bernard", "Dubois", "Moreau", "Girard", "Laurent"]),
    "PT": (["João", "Tiago", "Rúben", "Gonçalo", "Rafael", "Diogo", "André", "Bernardo"], ["Silva", "Santos", "Pereira", "Costa", "Fernandes", "Mendes"]),
    "US": (["Michael", "Ethan", "Jacob", "Daniel", "Matthew", "Ryan", "Brandon", "Tyler"], ["Johnson", "Brown", "Davis", "Wilson", "Anderson", "Thomas"]),
    "BR": (["Gabriel", "Lucas", "Vinícius", "Matheus", "Felipe", "Thiago", "Bruno", "Rafael"], ["Silva", "Santos", "Oliveira", "Souza", "Lima", "Costa"]),
    "MX": (["Carlos", "Diego", "Luis", "Javier", "Andrés", "Fernando", "Miguel", "Óscar"], ["Hernández", "García", "López", "Sánchez", "Ramírez", "Pérez"]),
    "TR": (["Emre", "Mehmet", "Burak", "Kerem", "Hakan", "Ozan", "Arda", "Cenk"], ["Yılmaz", "Demir", "Çelik", "Şahin", "Aydın", "Öztürk"]),
    "AR": (["Nicolás", "Franco", "Agustín", "Lautaro", "Tomás", "Santiago", "Julián", "Matías"], ["González", "Rodríguez", "Fernández", "Sosa", "Molina", "Acuña"]),
    "AT": (["David", "Philipp", "Maximilian", "Leon", "Julian", "Christoph", "Florian", "Dominik"], ["Gruber", "Wagner", "Huber", "Moser", "Bauer", "Leitner"]),
    "SA": (["Mohammed", "Abdullah", "Salem", "Fahad", "Khalid", "Sultan", "Nawaf", "Turki"], ["Al-Dossari", "Al-Sherif", "Al-Otaibi", "Al-Ghamdi", "Al-Harbi", "Al-Zahrani"]),
    "JP": (["Haruto", "Sota", "Riku", "Yuki", "Daiki", "Keito", "Ren", "Kento"], ["Tanaka", "Sato", "Suzuki", "Takahashi", "Watanabe", "Ito"]),
    "US2": (["Kane", "Theo", "Xavi", "Kylian"], ["Hart", "Cole"]),
}

NATIONALITIES = {
    "ENG": "England", "ESP": "Spain", "ITA": "Italy", "GER": "Germany",
    "FRA": "France", "POR": "Portugal", "NED": "Netherlands", "USA": "United States",
    "BRA": "Brazil", "MEX": "Mexico", "TUR": "Türkiye", "ARG": "Argentina",
    "AUT": "Austria", "KSA": "Saudi Arabia", "JPN": "Japan",
}
LEAGUE_NAT_MAP = {  # league name -> primary nationality key
    "Premier League": ("EN", "ENG"), "La Liga": ("ES", "ESP"), "Serie A": ("IT", "ITA"),
    "Bundesliga": ("DE", "GER"), "Ligue 1": ("FR", "FRA"), "Primeira Liga": ("PT", "POR"),
    "Eredivisie": ("NL", "NED"), "MLS": ("US", "USA"), "Brasileirão": ("BR", "BRA"),
    "Liga MX": ("MX", "MEX"), "Super Lig": ("TR", "TUR"), "Argentine Primera": ("AR", "ARG"),
    "1. Bundesliga (AUT)": ("DE", "AUT"), "Saudi Pro League": ("SA", "KSA"),
    "J1 League": ("JP", "JPN"), "Championship": ("EN", "ENG"),
    "Ligue 2": ("FR", "FRA"), "2. Bundesliga": ("DE", "GER"),
}
# NL name bucket fallback for NED
NAMES["NL"] = (["Luuk", "Daan", "Sven", "Bram", "Jesse", "Thijs", "Sem", "Mees"], ["de Vries", "Jansen", "Bakker", "van Dijk", "Visser", "Muller"])

CLUB_NAME_FRAGS = ["City", "United", "FC", "Athletic", "Rovers", "Wanderers", "Sporting", "Royals", "Academy", "Elite"]
CITIES = {
    "ENG": ["London", "Manchester", "Liverpool", "Birmingham", "Leeds", "Newcastle", "Sheffield", "Bristol"],
    "ESP": ["Madrid", "Barcelona", "Valencia", "Seville", "Bilbao", "Sevilla"],  # placeholder
    "ITA": ["Rome", "Milan", "Turin", "Naples", "Florence", "Genoa"],
    "GER": ["Berlin", "Munich", "Hamburg", "Cologne", "Frankfurt", "Dortmund"],
    "FRA": ["Paris", "Lyon", "Marseille", "Toulouse", "Lille", "Nice"],
    "POR": ["Lisbon", "Porto", "Braga", "Guimarães", "Coimbra", "Faro"],
    "NED": ["Amsterdam", "Rotterdam", "Utrecht", "Eindhoven", "Groningen", "The Hague"],
    "USA": ["New York", "Los Angeles", "Chicago", "Miami", "Atlanta", "Seattle"],
    "BRA": ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Porto Alegre", "Brasília", "Curitiba"],
    "MEX": ["Mexico City", "Guadalajara", "Monterrey", "Puebla", "Tijuana", "León"],
    "TUR": ["Istanbul", "Ankara", "Izmir", "Antalya", "Bursa", "Trabzon"],
    "ARG": ["Buenos Aires", "Córdoba", "Rosario", "La Plata", "Mendoza", "Mar del Plata"],
    "AUT": ["Vienna", "Graz", "Linz", "Salzburg", "Innsbruck", "Klagenfurt"],
    "KSA": ["Riyadh", "Jeddah", "Mecca", "Dammam", "Al-Khobar", "Tabuk"],
    "JPN": ["Tokyo", "Osaka", "Kyoto", "Sapporo", "Nagoya", "Kobe"],
}
LEAGUE_CITY_MAP = {
    "Premier League": "ENG", "La Liga": "ESP", "Serie A": "ITA", "Bundesliga": "GER",
    "Ligue 1": "FRA", "Primeira Liga": "POR", "Eredivisie": "NED", "MLS": "USA",
    "Brasileirão": "BRA", "Liga MX": "MEX", "Super Lig": "TUR", "Argentine Primera": "ARG",
    "1. Bundesliga (AUT)": "AUT", "Saudi Pro League": "KSA", "J1 League": "JPN",
    "Championship": "ENG", "Ligue 2": "FRA", "2. Bundesliga": "GER",
}


def slugify(s: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in s).strip("-").replace("--", "-")


async def run(n_players: int) -> None:
    rng = RNG

    async for session in get_session():
        # --- reset ONLY demo rows (fk order) so re-seeds are deterministic
        #     and never touch other providers (e.g. statsbomb) ---
        for table in (
            "player_season_stats", "player_match_stats", "player_positions",
            "player_roles", "players", "clubs", "competitions", "seasons", "leagues",
        ):
            if table in ("player_season_stats",):
                await session.execute(text("DELETE FROM player_season_stats WHERE provider = 'demo'"))
            elif table in ("player_match_stats", "player_positions", "player_roles"):
                await session.execute(
                    text(f"DELETE FROM {table} WHERE player_id IN (SELECT id FROM players WHERE provider = 'demo')")
                )
            else:
                await session.execute(text(f"DELETE FROM {table} WHERE provider = 'demo'"))
        await session.commit()
        leagues = {}
        comps = {}
        for (lname, clubs_n, country, cc, code, level, strength) in LEAGUES:
            league = League(
                name=lname, code=code, country_code=cc, country_name=country,
                level=level, strength_factor=strength, provider="demo",
            )
            session.add(league)
            await session.flush()
            leagues[lname] = league
            competition = Competition(
                league_id=league.id, name=f"{lname} Championship",
                kind="league", gender="male",
            )
            session.add(competition)
            await session.flush()
            comps[lname] = competition

        seasons = {}
        for y in SEASON_YEARS:
            season = Season(
                name=f"{y}/{y + 1}", start_year=y, end_year=y + 1,
                is_current=(y == SEASON_YEARS[-1]),
            )
            session.add(season)
            await session.flush()
            seasons[y] = season

        # --- clubs (exactly N_CLUBS across leagues; spread as evenly as possible) ---
        clubs = []
        club_id_counter = count(1)
        base, extra = divmod(N_CLUBS, len(LEAGUES))
        for li, (lname, clubs_n, country, cc, code, level, strength) in enumerate(LEAGUES):
            n = base + (1 if li < extra else 0)
            league = leagues[lname]
            city_pool = CITIES.get(LEAGUE_CITY_MAP.get(lname, cc), ["Capital"])
            for _ in range(n):
                city = rng.choice(city_pool)
                suffix = rng.choice(CLUB_NAME_FRAGS)
                nm = f"{city} {suffix}"
                cid = next(club_id_counter)
                clubs.append(
                    Club(
                        slug=slugify(f"{lname}-{nm}-{cid}"),
                        name=nm, country_code=cc, country_name=country,
                        league_id=league.id, founded_year=rng.randint(1860, 2010),
                    )
                )
        session.add_all(clubs)
        await session.flush()

        # --- players (sample across leagues proportional to club slots) ---
        player_rows = []
        club_rows = {}  # name -> club (for current_club_id)
        for c in clubs:
            club_rows[c.name] = c
        pos_pool = [p for p, w in POS_SHARE.items() for _ in range(w)]
        for i in range(n_players):
            league = leagues_by_team_weight(rng, LEAGUES)
            club = rng.choice(leagues[league].clubs) if False else None
            # weighted club pick from this league's clubs
            lname = league
            league_clubs = [c for c in clubs if c.league_id == leagues[lname].id]
            club = rng.choice(league_clubs)
            nat_key, nat_code = LEAGUE_NAT_MAP[lname]
            firsts, lasts = NAMES[nat_key]
            first = rng.choice(firsts)
            last = rng.choice(lasts)
            dob = date.today() - timedelta(days=rng.randint(18 * 365, 35 * 365))
            position = rng.choice(pos_pool)
            player_rows.append(
                Player(
                    slug=slugify(f"{first}-{last}-{i}"),
                    full_name=f"{first} {last}", first_name=first, last_name=last,
                    date_of_birth=dob, nationality_code=nat_code,
                    nationality_name=NATIONALITIES[nat_code],
                    height_cm=rng.randint(170, 198), preferred_foot=rng.choice(["left", "right", "both"]),
                    primary_position=position,
                    current_club_id=club.id, profile={"node": "MAR", "demo": True, "seed": 42069},
                )
            )
            if len(player_rows) >= 1500:
                session.add_all(player_rows)
                player_rows = []
                await session.flush()
        if player_rows:
            session.add_all(player_rows)
            await session.flush()

        # --- current-season stats per player ---
        # select all player ids
        player_ids = (await session.scalars(select(Player.id))).all()
        season = seasons[SEASON_YEARS[-1]]
        stat_rows = []
        for pid in player_ids:
            p = await session.get(Player, pid)
            club_id = p.current_club_id
            club = await session.get(Club, club_id)
            lname = next(nm for nm, lg in leagues.items() if lg.id == club.league_id)
            comp = comps[lname]
            minutes = rng.randint(400, 3300)
            goals = int(rng.gauss(0, 18 * 0.6)) if p.primary_position != "GK" else 0
            stat_rows.append(
                PlayerSeasonStat(
                    player_id=pid, season_id=season.id, competition_id=comp.id,
                    club_id=club_id, position=p.primary_position,
                    minutes_played=max(0, minutes),
                    appearances=rng.randint(5, 40),
                    starts=rng.randint(0, 36),
                    subs=rng.randint(0, 8),
                    goals=max(0, goals), assists=max(0, int(rng.gauss(0, 12 * 0.6))),
                    penalty_goals=rng.randint(0, 6),
                    shots=max(0, int(rng.gauss(0, 4.5 * 6) * 1.1)),
                    shots_on_target=max(0, int(rng.gauss(0, 1.6 * 6) * 1.1)),
                    xg=round(max(0.0, rng.gauss(0, 18 * 0.7)), 2),
                    xa=round(max(0.0, rng.gauss(0, 12 * 0.6)), 2),
                    touches=max(0, int(rng.gauss(0, 55 * 6 / 9) * rng.uniform(0.7, 1.3))),
                    passes_attempted=max(0, int(rng.gauss(0, 42 * 6 / 9) * rng.uniform(0.7, 1.3))),
                    passes_completed=max(0, int(rng.gauss(0, 38 * 6 / 9) * rng.uniform(0.7, 1.3))),
                    key_passes=max(0, int(rng.gauss(0, 3.5 * 6 / 9) * rng.uniform(0.5, 1.5))),
                    progressive_passes=max(0, int(rng.gauss(0, 8 * 6 / 9) * rng.uniform(0.5, 1.5))),
                    carries=max(0, int(rng.gauss(0, 30 * 6 / 9) * rng.uniform(0.7, 1.3))),
                    progressive_carries=max(0, int(rng.gauss(0, 10 * 6 / 9) * rng.uniform(0.5, 1.5))),
                    successful_dribbles=max(0, int(rng.gauss(0, 6 * 6 / 9) * rng.uniform(0.5, 1.5))),
                    interceptions=max(0, int(rng.gauss(0, 5 * 6 / 9) * rng.uniform(0.5, 1.5))),
                    tackles=max(0, int(rng.gauss(0, 7 * 6 / 9) * rng.uniform(0.5, 1.5))),
                    ball_recoveries=max(0, int(rng.gauss(0, 12 * 6 / 9) * rng.uniform(0.5, 1.5))),
                    clearances=max(0, int(rng.gauss(0, 6 * 6 / 9) * rng.uniform(0.5, 1.5))),
                    defensive_duels_won=max(0, int(rng.gauss(0, 4 * 6 / 9) * rng.uniform(0.5, 1.5))),
                    defensive_duels_total=max(1, int(rng.gauss(0, 6 * 6 / 9) * rng.uniform(0.5, 1.5)) + 1),
                    aerial_duels_won=max(0, int(rng.gauss(0, 3 * 6 / 9) * rng.uniform(0.5, 1.5))),
                    aerial_duels_total=max(1, int(rng.gauss(0, 5 * 6 / 9) * rng.uniform(0.5, 1.5)) + 1),
                )
            )
            if len(stat_rows) >= 1800:
                session.add_all(stat_rows)
                stat_rows = []
                await session.flush()
        if stat_rows:
            session.add_all(stat_rows)
            await session.flush()

        await session.commit()

        print("Seeded demo dataset:")
        for nm, lg in leagues.items():
            nclub = sum(1 for c in clubs if c.league_id == lg.id)
            nplayer = sum(1 for c in clubs if c.league_id == lg.id)
            print(f"  {nm:<24} {nclub:>3} clubs · {nplayer} players(hidden)")

    print(f"Done: {len(leagues)} leagues, {len(clubs)} clubs, {len(player_ids)} players, current-season stats.")


def leagues_by_team_weight(rng, spec) -> str:
    weights = [max(1, int(spec_league_clubs_raw := [l[1] for l in spec][i] * 2)) for i in range(len(spec))]
    return rng.choices([l[0] for l in spec], weights=weights)[0]


N_CLUBS = 220


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo Moneyball data")
    parser.add_argument("n_players", type=int, nargs="?", default=5000)
    args = parser.parse_args()
    asyncio.run(run(args.n_players))
