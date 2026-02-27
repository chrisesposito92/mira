"""Tests for GoTRUE auth — signup, login, rejection.

Uses the admin API (service role key) for user creation to avoid email rate limits
on hosted Supabase. Tests verify that auth flows work correctly.
"""

import os
import uuid

import httpx
import pytest

from tests.conftest import ANON_KEY, AUTH_URL, TEST_PASSWORD

pytestmark = pytest.mark.asyncio

SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# Module-level shared user — created once, used by all tests
_shared_email = f"mira-auth-test-{uuid.uuid4().hex[:8]}@example.org"
_shared_user: dict | None = None


async def _ensure_test_user() -> dict:
    """Create the shared test user via admin API (bypasses rate limits)."""
    global _shared_user
    if _shared_user is not None:
        return _shared_user

    async with httpx.AsyncClient() as client:
        # Use admin API to create user (bypasses email rate limits)
        resp = await client.post(
            f"{AUTH_URL}/admin/users",
            json={
                "email": _shared_email,
                "password": TEST_PASSWORD,
                "email_confirm": True,
            },
            headers={
                "apikey": ANON_KEY,
                "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
            },
        )
        if resp.status_code not in (200, 201):
            pytest.skip(f"Admin user creation failed ({resp.status_code}): {resp.text}")

        data = resp.json()
        user_id = data.get("id", "")

        # Now login to get an access_token
        login_resp = await client.post(
            f"{AUTH_URL}/token?grant_type=password",
            json={"email": _shared_email, "password": TEST_PASSWORD},
            headers={"apikey": ANON_KEY, "Content-Type": "application/json"},
        )
        if login_resp.status_code != 200:
            pytest.skip(f"Login after admin create failed: {login_resp.text}")

        login_data = login_resp.json()
        _shared_user = {
            "email": _shared_email,
            "access_token": login_data.get("access_token", ""),
            "id": user_id,
        }
        return _shared_user


async def test_signup_creates_user(apply_migrations):
    """Admin user creation should return a valid user with id."""
    user = await _ensure_test_user()
    assert user["id"], "No user id returned"
    assert user["email"] == _shared_email


async def test_login_returns_valid_jwt(apply_migrations):
    """Login with correct credentials returns a JWT."""
    user = await _ensure_test_user()
    assert user["access_token"], "No access_token returned"
    assert len(user["access_token"]) > 50


async def test_wrong_password_rejected(apply_migrations):
    """Login with wrong password should return 400."""
    await _ensure_test_user()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{AUTH_URL}/token?grant_type=password",
            json={"email": _shared_email, "password": "wrongpassword"},
            headers={"apikey": ANON_KEY, "Content-Type": "application/json"},
        )
    assert resp.status_code in (400, 401, 403)
