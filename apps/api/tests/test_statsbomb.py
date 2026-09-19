"""StatsBomb loader unit tests — synthetic mini open-data repo on disk.

Validates the adapter end-to-end against the TEST database (54321) without
touching real data: competitions -> leagues/competitions/seasons, matches ->
clubs, lineups -> players, events -> the 55 player_season_stats columns.
Provider 'test_fixture' is wiped before and after so the shared test DB stays
clean for the smoke suite.
"""

import json

import pytest
from apps.api.app.db.models.football import (
    Club,
    Competition,
    League,
    Player,
    PlayerSeasonStat,
    Season,
)
from apps.api.app.services.statsbomb import StatsBombLoader
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

TEST_URL = "postgresql+psycopg://moneyball:moneyball@localhost:54321/moneyball_test"
FIXTURE_PROVIDER = "test_fixture"


def _event(**kw):
    base = {
        "id": 0, "index": 0, "period": 1, "timestamp": "00:00:01.000",
        "minute": 0, "second": 1, "possession": 100, "play_pattern": {"name": "Regular Play"},
    }
    base.update(kw)
    return base


def _team(tid, name):
    return {"id": tid, "name": name}


def build_fixture(tmp_path):
    root = tmp_path / "open-data"
    root.mkdir(parents=True, exist_ok=True)
    (root / "competitions.json").write_text(json.dumps([
        {
            "competition_id": 9001, "competition_name": "Test League",
            "competition_gender": "male", "competition_youth": False,
            "competition_international": False, "country_name": "England",
            "country_code": "ENG", "season_id": 1, "season_name": "2023/2024",
            "season_start_year": 2023, "season_end_year": 2024,
        }
    ]))

    mdir = root / "matches" / "9001"
    mdir.mkdir(parents=True)
    (mdir / "1.json").write_text(json.dumps([
        {
            "match_id": 7001, "match_date": "2023-10-01",
            "home_team": {"home_team_id": 100, "home_team_name": "Alpha FC"},
            "away_team": {"away_team_id": 101, "away_team_name": "Beta FC"},
        }
    ]))

    ldir = root / "lineups"
    ldir.mkdir()
    alpha_lineup = [
        {"player_id": 10000, "player_name": "Alex Alpha", "country": {"id": 1, "name": "England"},
         "positions": [{"from": 0, "to": 90, "start_reason": "Starts", "end_reason": "Full Time",
                        "position": {"id": 4, "name": "Striker"}}]},
        {"player_id": 10001, "player_name": "Greg Alpha", "country": {"id": 2, "name": "Wales"},
         "positions": [{"from": 0, "to": 90, "start_reason": "Starts", "end_reason": "Full Time",
                        "position": {"id": 0, "name": "Goalkeeper"}}]},
    ]
    beta_lineup = [
        {"player_id": 10100, "player_name": "Boris Beta", "country": {"id": 3, "name": "Scotland"},
         "positions": [{"from": 0, "to": 90, "start_reason": "Starts", "end_reason": "Full Time",
                        "position": {"id": 4, "name": "Striker"}}]},
        {"player_id": 10101, "player_name": "Cara Beta", "country": {"id": 4, "name": "Ireland"},
         "positions": [{"from": 0, "to": 90, "start_reason": "Starts", "end_reason": "Full Time",
                        "position": {"id": 3, "name": "Center Back"}}]},
    ]
    (ldir / "7001.json").write_text(json.dumps([
        {"team_id": 100, "team_name": "Alpha FC", "lineup": alpha_lineup},
        {"team_id": 101, "team_name": "Beta FC", "lineup": beta_lineup},
    ]))

    a = _team(100, "Alpha FC")
    b = _team(101, "Beta FC")
    p10000 = _team(100, "Alpha FC")
    p10001 = _team(100, "Alpha FC")
    p10100 = _team(101, "Beta FC")
    p10000["player"] = {"id": 10000, "name": "Alex Alpha"}
    p10001["player"] = {"id": 10001, "name": "Greg Alpha"}
    p10100["player"] = {"id": 10100, "name": "Boris Beta"}
    ev = [
        _event(id=1, index=1, timestamp="00:00:01.000", type={"name": "Shot"}, team=a, player=p10000.get("player"),
               location=[113, 40], shot={"outcome": {"name": "Goal"}, "statsbomb_xg": 0.5, "type": {"name": "Open Play"}}),
        _event(id=2, index=2, timestamp="00:00:02.000", type={"name": "Shot"}, team=a, player=p10000.get("player"),
               location=[108, 35], shot={"outcome": {"name": "Saved"}, "statsbomb_xg": 0.2, "type": {"name": "Open Play"}}),
        _event(id=3, index=3, timestamp="00:00:03.000", type={"name": "Pass"}, team=a, player=p10000.get("player"),
               location=[100, 35]),
        _event(id=4, index=4, timestamp="00:00:04.000", type={"name": "Pass"}, team=a, player=p10000.get("player"),
               location=[40, 40]),
        _event(id=5, index=5, timestamp="00:00:05.000", type={"name": "Carries"}, team=a, player=p10000.get("player"),
               location=[50, 40], carry={"end_location": [72, 45]}),
        _event(id=6, index=6, timestamp="00:00:06.000", type={"name": "Dribbles"}, team=a, player=p10000.get("player"),
               location=[60, 45], dribble={"outcome": {"name": "Complete"}}),
        _event(id=7, index=7, timestamp="00:00:07.000", type={"name": "Interception"}, team=a, player=p10000.get("player"),
               location=[30, 50]),
        _event(id=8, index=8, timestamp="00:00:08.000", type={"name": "Pressure"}, team=a, player=p10000.get("player"),
               location=[70, 45]),
        _event(id=9, index=9, timestamp="00:00:09.500", type={"name": "Ball Recovery"}, team=a, player=p10000.get("player"),
               location=[72, 46]),
        _event(id=10, index=10, timestamp="00:01:00.000", type={"name": "Pass"}, team=a, player=p10001.get("player"),
               location=[12, 40]),
        _event(id=11, index=11, timestamp="00:01:01.000", type={"name": "Clearance"}, team=a, player=p10001.get("player"),
               location=[10, 35]),
        _event(id=12, index=12, timestamp="00:01:02.000", type={"name": "Duel"}, team=a, player=p10001.get("player"),
               location=[25, 50], duel={"type": {"name": "Tackle"}, "outcome": {"name": "Won"}}),
        _event(id=13, index=13, timestamp="00:01:03.000", type={"name": "Duel"}, team=a, player=p10001.get("player"),
               location=[20, 45], duel={"type": {"name": "Aerial Lost"}, "outcome": {"name": "Lost"}}),
        _event(id=14, index=14, timestamp="00:02:00.000", type={"name": "Shot"}, team=b, player={"id": 10100, "name": "Boris Beta"},
               location=[114, 42], shot={"outcome": {"name": "Saved"}, "statsbomb_xg": 0.3, "type": {"name": "Open Play"}}),
    ]
    ev[2]["pass"] = {"length": 12.0, "end_location": [112, 42], "recipient": {"id": 10001},
                     "shot_assist": True, "goal_assist": True, "assisted_shot_id": 1,
                     "technique": {"name": "Through Ball"}}
    ev[3]["pass"] = {"length": 40.0, "end_location": [60, 45], "recipient": {"id": 10001}}
    ev[9]["pass"] = {"length": 25.0, "end_location": [30, 50], "recipient": {"id": 10000}}
    edir = root / "events"
    edir.mkdir()
    (edir / "7001.json").write_text(json.dumps(ev))
    return root


@pytest.fixture
async def engine():
    eng = create_async_engine(TEST_URL, poolclass=None)
    yield eng
    await eng.dispose()


async def _wipe(session):
    loader = StatsBombLoader(session, raw_dir="/tmp/nonexistent", provider=FIXTURE_PROVIDER)
    await loader.wipe_provider()


MODELS = [League, Competition, Season, Club, Player, PlayerSeasonStat]


@pytest.mark.asyncio
async def test_loader_end_to_end(tmp_path, engine):
    raw = build_fixture(tmp_path)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        await _wipe(session)
        baseline = {
            model.__tablename__: await session.scalar(select(func.count()).select_from(model))
            for model in MODELS
        }
        loader = StatsBombLoader(session, raw_dir=raw, provider=FIXTURE_PROVIDER)
        await loader.load_competitions({9001})
        await loader.load_competition_season(9001, 1)

        assert (await session.scalar(select(func.count()).select_from(League))) == baseline["leagues"] + 1
        assert (await session.scalar(select(func.count()).select_from(Competition))) == baseline["competitions"] + 1
        assert (await session.scalar(select(func.count()).select_from(Season))) == baseline["seasons"] + 1
        assert (await session.scalar(select(func.count()).select_from(Club))) == baseline["clubs"] + 2
        assert (await session.scalar(select(func.count()).select_from(Player))) == baseline["players"] + 4
        assert (await session.scalar(select(func.count()).select_from(PlayerSeasonStat))) == baseline["player_season_stats"] + 4

        alex = (
            await session.scalars(select(Player).where(Player.provider_id == "10000"))
        ).one()
        assert alex.full_name == "Alex Alpha"
        assert alex.date_of_birth is None
        assert alex.nationality_code is None
        assert alex.nationality_name == "England"
        assert alex.profile["bios_known"] is False
        assert alex.primary_position == "ST"

        stat = (
            await session.scalars(
                select(PlayerSeasonStat).where(
                    PlayerSeasonStat.player_id == alex.id,
                    PlayerSeasonStat.provider == FIXTURE_PROVIDER,
                )
            )
        ).one()
        assert stat.position == "ST"
        assert stat.minutes_played == 90
        assert stat.appearances == 1 and stat.starts == 1 and stat.subs == 0
        assert stat.goals == 1
        assert stat.assists == 1
        assert stat.shots == 2
        assert stat.shots_on_target == 2
        assert stat.xg == pytest.approx(0.7)
        assert stat.npxg == pytest.approx(0.7)
        assert stat.xa == pytest.approx(0.5)
        assert stat.key_passes == 1
        assert stat.shot_creating_actions == 1
        assert stat.goal_creating_actions == 1
        assert stat.through_balls == 1
        assert stat.passes_attempted == 2
        assert stat.passes_completed == 2
        assert stat.progressive_passes == 2
        assert stat.long_passes_attempted == 1
        assert stat.long_passes_completed == 1
        assert stat.final_third_passes == 1
        assert stat.passes_into_box == 1
        assert stat.carries == 1
        assert stat.progressive_carries == 1
        assert stat.successful_dribbles == 1
        assert stat.dribbles_attempted == 1
        assert stat.interceptions == 1
        assert stat.ball_recoveries == 1
        assert stat.pressures == 1
        assert stat.pressures_successful == 1
        assert stat.touches == 9
        assert stat.touches_in_box == 2
        assert stat.carry_distance == 23

        greg = (await session.scalars(select(Player).where(Player.provider_id == "10001"))).one()
        gstat = (
            await session.scalars(
                select(PlayerSeasonStat).where(PlayerSeasonStat.player_id == greg.id)
            )
        ).one()
        assert gstat.position == "GK"
        assert gstat.tackles == 1
        assert gstat.defensive_duels_won == 1
        assert gstat.defensive_duels_total == 1
        assert gstat.aerial_duels_total == 1
        assert gstat.clearances == 1
        assert gstat.touches == 4  # pass, clearance, duel, duel

        boris = (await session.scalars(select(Player).where(Player.provider_id == "10100"))).one()
        bstat = (await session.scalars(
            select(PlayerSeasonStat).where(PlayerSeasonStat.player_id == boris.id)
        )).one()
        assert bstat.shots == 1 and bstat.xg == pytest.approx(0.3)
        assert bstat.shots_on_target == 1

        # wipe only touches fixture provider rows, leaves unrelated rows intact
        await _wipe(session)
        for model in MODELS:
            assert (
                await session.scalar(select(func.count()).select_from(model))
                == baseline[model.__tablename__]
            )
