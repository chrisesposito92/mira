"""Seed logo images for component library entries.

Fetches logos from Logo.dev for all component_library rows where logo_base64 IS NULL.
Falls back to monogram marker when Logo.dev returns no result (per D-08).

Design decisions addressing review feedback:
- Idempotent: Only processes rows where logo_base64 IS NULL (safe to re-run)
- Partial failure tolerant: Each logo fetch is individually try/excepted
- Never blocks setup: Runs independently from migrations; generates monograms if no token
- Rate-limited: 0.3s between requests to avoid Logo.dev throttling
- Uses slug for logging (stable identifier, not auto-generated UUID)

Usage:
    cd backend && source .venv/bin/activate
    python -m scripts.seed_logos

Requires LOGO_DEV_TOKEN in backend/.env (optional -- falls back to monograms)
"""

import asyncio
import base64
import hashlib
import logging

import httpx

from app.config import settings
from app.db.client import get_supabase_client

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Monogram color palette (deterministic by name hash, per D-08)
MONOGRAM_COLORS = [
    "#4A90D9",
    "#50C878",
    "#E67E22",
    "#9B59B6",
    "#E74C3C",
    "#1ABC9C",
    "#F39C12",
    "#3498DB",
]

# Max response size: 2MB (matches logo proxy guard)
MAX_LOGO_BYTES = 2 * 1024 * 1024


def _monogram_for(name: str) -> str:
    """Generate a monogram marker string.

    Format: 'monogram:<INITIALS>:<COLOR>'
    e.g., 'monogram:SF:#4A90D9' for Salesforce
    """
    words = name.split()
    if len(words) >= 2:
        initials = (words[0][0] + words[1][0]).upper()
    else:
        initials = name[:2].upper()
    color_idx = int(hashlib.md5(name.encode()).hexdigest(), 16) % len(MONOGRAM_COLORS)
    color = MONOGRAM_COLORS[color_idx]
    return f"monogram:{initials}:{color}"


async def fetch_logo(client: httpx.AsyncClient, domain: str, token: str) -> str | None:
    """Fetch a logo from Logo.dev, return base64 data URL or None.

    Handles partial failures gracefully per review feedback:
    - Timeout: returns None (monogram fallback)
    - HTTP error: returns None
    - Oversized response: returns None
    - Non-image content type: returns None
    """
    url = f"https://img.logo.dev/{domain}?token={token}&size=128&format=png"
    try:
        resp = await client.get(url, follow_redirects=True, timeout=10.0)
        if resp.status_code != 200:
            logger.warning("  HTTP %d for %s", resp.status_code, domain)
            return None
        if len(resp.content) > MAX_LOGO_BYTES:
            logger.warning("  Oversized response for %s (%d bytes)", domain, len(resp.content))
            return None
        content_type = resp.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            logger.warning("  Non-image content-type for %s: %s", domain, content_type)
            return None
        if len(resp.content) < 100:
            logger.warning(
                "  Suspiciously small response for %s (%d bytes)", domain, len(resp.content)
            )
            return None
        b64 = base64.b64encode(resp.content).decode()
        return f"data:{content_type};base64,{b64}"
    except httpx.TimeoutException:
        logger.warning("  Timeout fetching logo for %s", domain)
        return None
    except httpx.RequestError as e:
        logger.warning("  Request error for %s: %s", domain, e)
        return None


async def main():
    token = settings.logo_dev_token
    if not token:
        logger.warning(
            "LOGO_DEV_TOKEN not configured in backend/.env. "
            "Generating monograms only (logos can be added later by re-running with token)."
        )

    supabase = get_supabase_client()

    # Fetch all rows where logo_base64 is null (idempotent -- re-runs skip populated rows)
    result = (
        supabase.table("component_library")
        .select("id, slug, name, domain, logo_base64")
        .is_("logo_base64", "null")
        .order("display_order")
        .execute()
    )
    rows = result.data

    if not rows:
        logger.info("All component library entries already have logos. Nothing to do.")
        return

    logger.info("Found %d entries without logos.", len(rows))

    fetched = 0
    monogrammed = 0
    errors = 0

    async with httpx.AsyncClient() as client:
        for row in rows:
            logo_b64 = None

            try:
                if token and row["domain"]:
                    logo_b64 = await fetch_logo(client, row["domain"], token)
                    if logo_b64:
                        fetched += 1

                if not logo_b64:
                    logo_b64 = _monogram_for(row["name"])
                    monogrammed += 1

                supabase.table("component_library").update({"logo_base64": logo_b64}).eq(
                    "id", row["id"]
                ).execute()

                status_label = "fetched" if not logo_b64.startswith("monogram:") else "monogram"
                logger.info("  %s (%s): %s", row["name"], row.get("slug", "?"), status_label)
            except Exception as e:
                errors += 1
                logger.error("  FAILED %s: %s", row["name"], e)
                # Continue to next row -- partial failures don't block the rest

            # Rate limit: Logo.dev recommends modest pace
            if token:
                await asyncio.sleep(0.3)

    logger.info(
        "Done: %d logos fetched, %d monograms generated, %d errors.",
        fetched,
        monogrammed,
        errors,
    )
    if errors:
        logger.warning("Re-run `python -m scripts.seed_logos` to retry failed entries.")


if __name__ == "__main__":
    asyncio.run(main())
