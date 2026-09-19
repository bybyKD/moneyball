"""Phase 1 smoke tests (spec §26 auth + §38 observability).

Run:  make api-test   (= pytest apps/api/tests using TEST_DATABASE_URL/54321)
"""

import httpx
import pytest

BASE = "http://127.0.0.1:8008/api"


@pytest.fixture(scope="module")
def server():
    """Boot the app for the duration of this module. Production impl spins a
    dedicated ASGI process against the test DB; the lightweight path below
    starts uvicorn on the test port for smoke coverage."""
    import subprocess
    import time

    proc = subprocess.Popen(
        ["./.venv/bin/uvicorn", "apps.api.app.main:app", "--host", "127.0.0.1", "--port", "8008"],
        cwd="/Users/Derio/Documents/moneyball",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={"DATABASE_URL": "postgresql+psycopg://moneyball:moneyball@localhost:54321/moneyball_test"},
    )
    for _ in range(60):
        try:
            httpx.get(f"{BASE}/health", timeout=2)
            break
        except httpx.ConnectError:
            time.sleep(0.5)
    yield proc
    proc.terminate()


def test_health(server):
    r = httpx.get(f"{BASE}/health", timeout=5)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_touches_db(server):
    r = httpx.get(f"{BASE}/health/ready", timeout=5)
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


def test_register_login_me_flow(server):
    import uuid

    email = f"smoke-{uuid.uuid4().hex[:10]}@example.com"
    register = httpx.post(
        f"{BASE}/auth/register",
        json={"email": email, "display_name": "Smoke Tester", "password": "supersecret123"},
        timeout=8,
    )
    assert register.status_code == 201, register.text
    cookies = register.cookies

    me = httpx.get(f"{BASE}/users/me", cookies=cookies, timeout=5)
    assert me.status_code == 200, me.text
    assert me.json()["email"] == email


def test_login_sets_cookie(server):
    import uuid

    email = f"smoke2-{uuid.uuid4().hex[:10]}@example.com"
    httpx.post(f"{BASE}/auth/register", json={"email": email, "display_name": "Smoke 2", "password": "supersecret123"}, timeout=8)
    logged = httpx.post(f"{BASE}/auth/login", json={"email": email, "password": "supersecret123"}, timeout=8)
    assert logged.status_code == 200, logged.text
    assert logged.json()["access_token"]


def test_unauthenticated_me_returns_401(server):
    r = httpx.get(f"{BASE}/users/me", timeout=5)
    assert r.status_code == 401

def test_player_analytics(server):
    r = httpx.get(f"{BASE}/players?limit=1", timeout=5)
    assert r.status_code == 200, r.text
    pid = r.json()[0]["id"]
    a = httpx.get(f"{BASE}/players/{pid}/analytics", timeout=6)
    assert a.status_code == 200, a.text
    body = a.json()["result"]
    assert body["score"] is not None
    assert body["market_value_eur"] is not None
    assert isinstance(body["percentiles"], dict)


def test_scouting_mission_shortlist_flow(server):
    import uuid
    email = f"scout.t.{uuid.uuid4().hex[:8]}@test.io"
    s = httpx.post(f"{BASE}/auth/register", json={"email": email, "password": "demo12345", "display_name": "T Scout"}, timeout=5)
    assert s.status_code == 201, s.text
    cookie = s.headers.get("set-cookie", "").split(";")[0]
    h = {"Cookie": cookie}
    m = httpx.post(f"{BASE}/missions", json={"title": "ST targets", "position": "ST", "top_n": 5}, headers=h, timeout=30)
    assert m.status_code == 201, m.text
    mid = m.json()["id"]
    g = httpx.get(f"{BASE}/missions/{mid}", headers=h, timeout=10)
    assert g.status_code == 200
    cands = g.json()["candidates"]
    assert cands, "mission should produce candidates"
    first = cands[0]
    assert first["score"] > 0 and first["rank"] == 1
    sl = httpx.post(f"{BASE}/shortlists", json={"name": "targets"}, headers=h, timeout=10)
    assert sl.status_code == 201
    sid = sl.json()["id"]
    add = httpx.post(f"{BASE}/shortlists/{sid}/players/{first['player_id']}", headers=h, timeout=10)
    assert add.status_code == 201
    view = httpx.get(f"{BASE}/shortlists/{sid}", headers=h, timeout=10)
    assert len(view.json()["players"]) == 1


def test_agent_run_pipeline(server):
    import uuid
    email = f"agent.t.{uuid.uuid4().hex[:8]}@test.io"
    s = httpx.post(f"{BASE}/auth/register", json={"email": email, "password": "demo12345", "display_name": "A Scout"}, timeout=5)
    assert s.status_code == 201
    h = {"Cookie": s.headers.get("set-cookie", "").split(";")[0]}
    m = httpx.post(f"{BASE}/missions", json={"title": "LB targets", "position": "FB", "top_n": 3}, headers=h, timeout=30)
    mid = m.json()["id"]
    r = httpx.post(f"{BASE}/agents/runs", json={"mission_id": mid}, headers=h, timeout=30)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "complete"
    assert body["llm_calls"] == 0 and body["cost_usd"] == 0
    assert body["report"]["candidates"] and body["report"]["candidates"][0]["moneyball_score"] > 0
    g = httpx.get(f"{BASE}/agents/runs/{body['id']}", headers=h, timeout=10)
    assert g.json()["tasks"] and len(g.json()["events"]) >= 4


def test_similar_players_embedding(server):
    p = httpx.get(f"{BASE}/players?limit=1", timeout=5)
    pid = p.json()[0]["id"]
    r = httpx.get(f"{BASE}/players/{pid}/similar?k=4", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["model"] == "moneyball_demo_v1"
    assert len(body["neighbors"]) == 4
    assert all(0 <= n["similarity"] <= 1.0 for n in body["neighbors"])


def test_market_value_picks(server):
    r = httpx.get(f"{BASE}/market/value-picks?position=W&min_minutes=600&k=5", timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["picks"]) == 5
    assert all(p["score"] > 0 and p["market_value_eur"] > 0 for p in body["picks"])
    ratios = [p["value_ratio"] for p in body["picks"]]
    assert ratios == sorted(ratios, reverse=True)


def test_market_position_summary(server):
    r = httpx.get(f"{BASE}/market/position-summary", timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "ST" in body and "GK" in body
    assert all(0 <= v["median_score"] <= 100 for v in body.values())


def test_compare_players(server):
    p = httpx.get(f"{BASE}/players?limit=2", timeout=5).json()
    ia, ib = p[0]["id"], p[1]["id"]
    r = httpx.get(f"{BASE}/compare?player_a={ia}&player_b={ib}", timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["players"]) == 2
    assert body["winner"]["player_id"] in (ia, ib)
    # auth-required persistence
    import uuid
    h = {"Cookie": httpx.post(f"{BASE}/auth/register",
        json={"email": f"cmp.t.{uuid.uuid4().hex[:6]}@test.io", "password": "demo12345", "display_name": "C"},
        timeout=5).headers.get("set-cookie", "").split(";")[0]}
    s = httpx.post(f"{BASE}/compare", json={"player_ids": [ia, ib], "name": "A/B"}, headers=h, timeout=15)
    assert s.status_code == 201, s.text
    assert s.json()["result"]["winner"]["player_id"] in (ia, ib)
