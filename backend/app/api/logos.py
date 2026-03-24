"""API routes for logo proxy.

Security: This endpoint proxies external logo fetches. It includes strict
SSRF protection per review feedback (Gemini + Codex both flagged HIGH risk):
- Domain must match FQDN regex (letters, digits, dots, hyphens only)
- IP addresses rejected (no 192.168.x.x, 10.x.x.x, 127.x.x.x, etc.)
- Private/reserved hostnames rejected (localhost, .local, .internal)
- Content-type must be image/* (reject HTML, JSON, etc.)
- Response size capped at 2MB (reject oversized payloads)
- Timeout of 10s (prevent hanging connections)
"""

import base64
import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from app.config import settings
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/logos", tags=["logos"])

# Strict FQDN regex: letters, digits, dots, hyphens. Min 2 labels.
# Rejects: IPs, single-label names, special chars.
_FQDN_RE = re.compile(
    r"^(?!-)[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*"
    r"\.[a-zA-Z]{2,}$"
)

# Blocked hostname patterns (private/reserved)
_BLOCKED_PATTERNS = [
    "localhost",
    ".local",
    ".internal",
    ".example",
    ".test",
    ".invalid",
    ".onion",
]

# Max response size: 2MB
_MAX_RESPONSE_BYTES = 2 * 1024 * 1024

# Allowed content type prefix
_ALLOWED_CONTENT_TYPE = "image/"


def _validate_domain(domain: str) -> str:
    """Validate and normalize domain to prevent SSRF attacks.

    Raises HTTPException(400) if domain is invalid, an IP address,
    or resolves to a private/reserved hostname.
    """
    domain = domain.strip().lower()

    # Reject obvious IP addresses (v4 and v6)
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain):
        raise HTTPException(status_code=400, detail="IP addresses not allowed")
    if domain.startswith("[") or "::" in domain:
        raise HTTPException(status_code=400, detail="IPv6 addresses not allowed")

    # Reject private/reserved hostnames
    for pattern in _BLOCKED_PATTERNS:
        if domain == pattern.lstrip(".") or domain.endswith(pattern):
            raise HTTPException(status_code=400, detail=f"Domain '{domain}' is not allowed")

    # Validate FQDN format
    if not _FQDN_RE.match(domain):
        raise HTTPException(
            status_code=400,
            detail="Invalid domain format. Must be a valid FQDN (e.g., stripe.com)",
        )

    return domain


@router.get("/proxy")
async def proxy_logo(
    domain: str = Query(..., min_length=3, description="Domain to fetch logo for"),
    _user_id=Depends(get_current_user),
) -> dict:
    """Fetch logo from Logo.dev and return as base64.

    Per D-05: Logo.dev is the primary source.
    Per D-08: Returns 404 when logo not found (frontend renders monogram fallback).
    SSRF protection per review feedback: validates domain before fetching.
    """
    if not settings.logo_dev_token:
        raise HTTPException(status_code=503, detail="Logo service not configured")

    # Validate domain -- raises 400 on invalid input
    domain = _validate_domain(domain)

    # Construct Logo.dev URL from validated domain (never pass raw user input)
    url = f"https://img.logo.dev/{domain}?token={settings.logo_dev_token}&size=128&format=png"

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, follow_redirects=True, timeout=10.0)
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Logo service timeout")
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Logo service unavailable")

    if resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Logo not found")

    # Validate content type -- reject non-image responses
    content_type = resp.headers.get("content-type", "")
    if not content_type.startswith(_ALLOWED_CONTENT_TYPE):
        raise HTTPException(
            status_code=502,
            detail="Logo service returned non-image content",
        )

    # Validate response size -- reject oversized payloads
    if len(resp.content) > _MAX_RESPONSE_BYTES:
        raise HTTPException(
            status_code=502,
            detail="Logo response exceeds size limit",
        )

    b64 = base64.b64encode(resp.content).decode()
    return {
        "logo_base64": f"data:{content_type};base64,{b64}",
        "domain": domain,
    }
