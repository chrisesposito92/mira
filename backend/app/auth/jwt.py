"""Supabase JWT verification for FastAPI."""

from jose import JWTError, jwt

from app.config import settings


class AuthError(Exception):
    """Authentication/authorization error with HTTP status code."""

    def __init__(self, detail: str, status_code: int = 401):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def verify_token(token: str) -> dict:
    """Decode and verify a Supabase JWT.

    Returns the decoded payload dict.
    Raises AuthError if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError as e:
        raise AuthError(f"Invalid token: {e}") from e

    if "sub" not in payload:
        raise AuthError("Token missing 'sub' claim")

    return payload
