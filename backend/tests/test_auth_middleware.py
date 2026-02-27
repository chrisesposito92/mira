"""Tests for JWT verification and auth dependency."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from jose import jwt

from app.auth.jwt import AuthError, verify_token

# Use a fixed test secret
TEST_SECRET = "test-jwt-secret-for-unit-tests-only"


@pytest.fixture(autouse=True)
def _patch_jwt_secret(monkeypatch):
    """Patch the JWT secret for all tests in this module."""
    monkeypatch.setattr("app.auth.jwt.settings.supabase_jwt_secret", TEST_SECRET)


def _make_token(
    sub: str | None = None,
    exp_delta: timedelta | None = None,
    aud: str = "authenticated",
    secret: str = TEST_SECRET,
) -> str:
    payload = {}
    if sub is not None:
        payload["sub"] = sub
    if aud is not None:
        payload["aud"] = aud
    if exp_delta is not None:
        payload["exp"] = datetime.now(UTC) + exp_delta
    else:
        payload["exp"] = datetime.now(UTC) + timedelta(hours=1)
    return jwt.encode(payload, secret, algorithm="HS256")


class TestVerifyToken:
    def test_valid_token(self):
        user_id = str(uuid4())
        token = _make_token(sub=user_id)
        payload = verify_token(token)
        assert payload["sub"] == user_id

    def test_expired_token(self):
        token = _make_token(sub=str(uuid4()), exp_delta=timedelta(hours=-1))
        with pytest.raises(AuthError, match="Invalid token"):
            verify_token(token)

    def test_invalid_signature(self):
        token = _make_token(sub=str(uuid4()), secret="wrong-secret")
        with pytest.raises(AuthError, match="Invalid token"):
            verify_token(token)

    def test_missing_sub_claim(self):
        token = _make_token()  # no sub
        with pytest.raises(AuthError, match="missing 'sub'"):
            verify_token(token)

    def test_wrong_audience(self):
        token = _make_token(sub=str(uuid4()), aud="wrong-audience")
        with pytest.raises(AuthError, match="Invalid token"):
            verify_token(token)

    def test_garbage_token(self):
        with pytest.raises(AuthError, match="Invalid token"):
            verify_token("not.a.jwt")


class TestAuthEndpoint:
    """Test that missing/invalid auth returns proper HTTP errors via the app."""

    def test_no_auth_header(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/projects")
        assert resp.status_code in (401, 403)

    def test_invalid_bearer_token(self, monkeypatch):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/projects", headers={"Authorization": "Bearer garbage"})
        assert resp.status_code == 401
