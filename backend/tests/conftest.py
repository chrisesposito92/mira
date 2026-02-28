"""Shared test fixtures for database integration tests and Phase 4 API unit tests."""

import json
import os
import ssl as _ssl_module
import subprocess
from collections.abc import Generator
from unittest.mock import MagicMock
from uuid import UUID

import asyncpg
import httpx
import pytest
import pytest_asyncio
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

# Load .env from backend directory
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:54322/postgres"
)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "http://localhost:54321")
AUTH_URL = f"{SUPABASE_URL}/auth/v1"
ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")

TEST_PASSWORD = "testpassword123!"

# Detect if connecting to remote Supabase (needs SSL)
_IS_REMOTE = "supabase.co" in DATABASE_URL or "supabase.com" in DATABASE_URL


def _get_ssl_context():
    """Return SSL context for remote Supabase, None for local."""
    if _IS_REMOTE:
        ctx = _ssl_module.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl_module.CERT_NONE
        return ctx
    return None


# Track if migrations have been applied this session
_migrations_applied = False


@pytest.fixture(scope="session")
def apply_migrations():
    """Run all migrations once before the test session."""
    global _migrations_applied
    if _migrations_applied:
        return "already applied"
    script = os.path.join(os.path.dirname(__file__), "..", "scripts", "run_migrations.sh")
    env = {**os.environ, "DATABASE_URL": DATABASE_URL}
    result = subprocess.run(["bash", script], capture_output=True, text=True, env=env)
    if result.returncode != 0:
        pytest.fail(f"Migration failed:\n{result.stderr}\n{result.stdout}")
    _migrations_applied = True
    return result.stdout


@pytest_asyncio.fixture
async def db_conn(apply_migrations):
    """Per-test connection with transaction rollback for isolation."""
    conn = await asyncpg.connect(DATABASE_URL, ssl=_get_ssl_context())
    tx = conn.transaction()
    await tx.start()
    try:
        yield conn
    finally:
        await tx.rollback()
        await conn.close()


async def create_test_user(email: str, password: str = TEST_PASSWORD) -> dict:
    """Create a user via GoTRUE signup endpoint. Returns {id, access_token, email}."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{AUTH_URL}/signup",
            json={"email": email, "password": password},
            headers={
                "apikey": ANON_KEY,
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "id": data["id"],
            "access_token": data["access_token"],
            "email": email,
        }


async def get_user_jwt(email: str, password: str = TEST_PASSWORD) -> str:
    """Login and return access_token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{AUTH_URL}/token?grant_type=password",
            json={"email": email, "password": password},
            headers={
                "apikey": ANON_KEY,
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def set_auth_context(conn: asyncpg.Connection, user_id: str) -> None:
    """Set RLS context for a connection to simulate an authenticated user."""
    claims = json.dumps({"sub": user_id, "role": "authenticated"})
    await conn.execute("SET LOCAL role TO authenticated")
    await conn.execute(f"SET LOCAL request.jwt.claims TO '{claims}'")


# ---------------------------------------------------------------------------
# Phase 4: Unit test fixtures (no Supabase required)
# ---------------------------------------------------------------------------

MOCK_USER_ID = UUID("00000000-1111-2222-3333-444444444444")
TEST_FERNET_KEY = Fernet.generate_key().decode()


@pytest.fixture
def mock_user_id() -> UUID:
    return MOCK_USER_ID


@pytest.fixture
def fernet_key(monkeypatch) -> str:
    """Set a test Fernet key in settings."""
    monkeypatch.setenv("ENCRYPTION_KEY", TEST_FERNET_KEY)
    from app.config import Settings

    test_settings = Settings()
    monkeypatch.setattr("app.m3ter.encryption.settings", test_settings)
    return TEST_FERNET_KEY


class MockPostgrestResponse:
    """Mimics the PostgREST response from Supabase SDK."""

    def __init__(self, data: list[dict] | None = None):
        self.data = data or []


class MockPostgrestBuilder:
    """Chainable mock that supports .table().select().eq()...execute() pattern."""

    def __init__(self, data: list[dict] | None = None) -> None:
        self._data = data or []

    def select(self, *args: object, **kwargs: object) -> "MockPostgrestBuilder":
        return self

    def insert(self, row: dict, **kwargs: object) -> "MockPostgrestBuilder":
        # Keep pre-configured mock data (simulates DB returning full row with defaults)
        return self

    def update(self, values: dict, **kwargs: object) -> "MockPostgrestBuilder":
        if self._data:
            for row in self._data:
                row.update(values)
        return self

    def delete(self, **kwargs: object) -> "MockPostgrestBuilder":
        return self

    def eq(self, column: str, value: str) -> "MockPostgrestBuilder":
        return self

    def in_(self, column: str, values: list[str]) -> "MockPostgrestBuilder":
        return self

    def order(self, column: str, **kwargs: object) -> "MockPostgrestBuilder":
        return self

    def limit(self, count: int) -> "MockPostgrestBuilder":
        return self

    def execute(self) -> MockPostgrestResponse:
        return MockPostgrestResponse(self._data)


@pytest.fixture
def mock_supabase() -> MagicMock:
    """Return a mock Supabase client with configurable table data.

    Usage:
        def test_something(mock_supabase):
            mock_supabase._table_data["projects"] = [{"id": "...", ...}]
            # Now supabase.table("projects").select("*").execute() returns that data
    """
    client = MagicMock()
    client._table_data = {}

    def _table(name: str) -> MockPostgrestBuilder:
        data = client._table_data.get(name, [])
        return MockPostgrestBuilder(data)

    client.table = _table
    return client


@pytest.fixture
def authed_client(mock_supabase: MagicMock) -> Generator[TestClient, None, None]:
    """TestClient with get_current_user overridden to return MOCK_USER_ID.

    Does NOT use context manager to avoid triggering lifespan (get_db_pool),
    which would require a real Postgres connection.
    """
    from app.dependencies import get_current_user, get_supabase
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: MOCK_USER_ID
    app.dependency_overrides[get_supabase] = lambda: mock_supabase
    try:
        yield TestClient(app, raise_server_exceptions=False)
    finally:
        app.dependency_overrides.clear()
