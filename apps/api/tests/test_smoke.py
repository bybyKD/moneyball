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