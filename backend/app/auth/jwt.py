"""Supabase JWT verification for FastAPI."""

import jwt as pyjwt

from app.config import settings

# JWKS client for ES256 token verification (lazy-initialized)
_jwks_client: pyjwt.PyJWKClient | None = None


def _get_jwks_client() -> pyjwt.PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        _jwks_client = pyjwt.PyJWKClient(jwks_url)
    return _jwks_client


class AuthError(Exception):
    """Authentication/authorization error with HTTP status code."""

    def __init__(self, detail: str, status_code: int = 401):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def verify_token(token: str) -> dict:
    """Decode and verify a Supabase JWT.

    Supports both HS256 (shared secret) and ES256 (JWKS public key).
    Returns the decoded payload dict.
    Raises AuthError if the token is invalid or expired.
    """
    try:
        header = pyjwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")

        if alg == "ES256":
            signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
            payload = pyjwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256"],
                audience="authenticated",
            )
        else:
            payload = pyjwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
    except pyjwt.ExpiredSignatureError as e:
        raise AuthError(f"Invalid token: {e}") from e
    except pyjwt.InvalidTokenError as e:
        raise AuthError(f"Invalid token: {e}") from e

    if "sub" not in payload:
        raise AuthError("Token missing 'sub' claim")

    return payload
