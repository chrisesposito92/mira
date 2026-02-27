"""FastAPI dependency injection — auth, DB, m3ter client."""

from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client

from app.auth.jwt import verify_token
from app.db.client import get_supabase_client

_bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> UUID:
    """Extract and verify user_id from Bearer token."""
    payload = verify_token(credentials.credentials)
    return UUID(payload["sub"])


def get_supabase() -> Client:
    """Return the service-role Supabase client (for DI override in tests)."""
    return get_supabase_client()
