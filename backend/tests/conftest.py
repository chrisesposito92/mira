"""Shared test fixtures for Phase 2 database tests."""

import json
import os
import ssl as _ssl_module
import subprocess

import asyncpg
import httpx
import pytest
import pytest_asyncio

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
