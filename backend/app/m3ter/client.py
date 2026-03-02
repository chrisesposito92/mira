"""m3ter API client with token caching, retry logic, and per-entity CRUD."""

import asyncio
import base64
import logging
import time
from datetime import UTC, datetime
from typing import Any, ClassVar
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# Token cache TTL: 4h50m (17100s) — 10min buffer on m3ter's 5hr token lifetime
_TOKEN_TTL = 17100

# Retry configuration
_MAX_RETRIES = 3
_BACKOFF_SECONDS = [1, 2, 5]
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class M3terClient:
    """OAuth2 client-credentials client for the m3ter Config and Ingest APIs."""

    _token_cache: ClassVar[dict[tuple[str, str], tuple[str, float]]] = {}

    def __init__(
        self,
        org_id: str,
        api_url: str,
        client_id: str,
        client_secret: str,
    ):
        self.org_id = org_id
        self.api_url = api_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._client: httpx.AsyncClient | None = None
        self._token: str | None = None

        # Pre-derive ingest URL from api_url
        parsed = urlparse(self.api_url)
        ingest_host = parsed.hostname or ""
        if ingest_host.startswith("api."):
            ingest_host = "ingest." + ingest_host[4:]
        else:
            ingest_host = "ingest.m3ter.com"
        self._ingest_base_url = f"{parsed.scheme}://{ingest_host}"

    def _get_client(self) -> httpx.AsyncClient:
        """Lazy-init persistent HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Close the persistent HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def authenticate(self) -> str:
        """Obtain an OAuth2 access token via client credentials grant.

        Uses class-level cache with 4h50m TTL to avoid unnecessary auth calls.
        """
        cache_key = (self.client_id, self.client_secret)

        # Check cache first
        if cache_key in self._token_cache:
            token, expires_at = self._token_cache[cache_key]
            if time.monotonic() < expires_at:
                self._token = token
                return token

        # Fetch new token — m3ter requires HTTP Basic auth for client credentials
        auth_url = f"{self.api_url}/oauth/token"
        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        client = self._get_client()
        resp = await client.post(
            auth_url,
            data={"grant_type": "client_credentials"},
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]

        # Cache the token
        self._token_cache[cache_key] = (token, time.monotonic() + _TOKEN_TTL)
        self._token = token
        return token

    async def test_connection(self) -> dict:
        """Authenticate and hit a lightweight endpoint to verify credentials."""
        tested_at = datetime.now(UTC)
        try:
            token = await self.authenticate()
            client = self._get_client()
            resp = await client.get(
                f"{self.api_url}/organizations/{self.org_id}/products",
                headers={"Authorization": f"Bearer {token}"},
                params={"pageSize": 1},
            )
            resp.raise_for_status()
            return {
                "success": True,
                "message": "Connected successfully",
                "tested_at": tested_at.isoformat(),
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "message": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                "tested_at": tested_at.isoformat(),
            }
        except httpx.RequestError as e:
            return {
                "success": False,
                "message": f"Connection error: {e}",
                "tested_at": tested_at.isoformat(),
            }

    async def _config_api_request(
        self,
        method: str,
        path: str,
        data: dict[str, Any] | None = None,
    ) -> dict:
        """Make a Config API request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            path: API path (e.g., /organizations/{orgId}/products)
            data: Optional JSON body

        Returns:
            Parsed JSON response body.

        Raises:
            httpx.HTTPStatusError: After all retries exhausted for retryable errors,
                or immediately for non-retryable errors.
        """
        token = await self.authenticate()
        client = self._get_client()
        url = f"{self.api_url}{path}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        last_exc: httpx.HTTPStatusError | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                resp = await client.request(method, url, json=data, headers=headers)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                last_exc = e
                if e.response.status_code not in _RETRYABLE_STATUS_CODES:
                    raise
                if attempt < _MAX_RETRIES - 1:
                    wait = _BACKOFF_SECONDS[attempt]
                    logger.warning(
                        "m3ter API %s %s returned %d, retrying in %ds (attempt %d/%d)",
                        method,
                        path,
                        e.response.status_code,
                        wait,
                        attempt + 1,
                        _MAX_RETRIES,
                    )
                    await asyncio.sleep(wait)

        # All retries exhausted
        raise last_exc  # type: ignore[misc]

    async def _ingest_api_post(self, data: list[dict[str, Any]]) -> dict:
        """Submit measurements to the m3ter Ingest API.

        The Ingest API uses a different base URL (ingest.m3ter.com).
        Uses the same retry logic as Config API requests.
        """
        token = await self.authenticate()
        client = self._get_client()
        url = f"{self._ingest_base_url}/organizations/{self.org_id}/measurements"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        last_exc: httpx.HTTPStatusError | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                resp = await client.post(url, json={"measurements": data}, headers=headers)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                last_exc = e
                if e.response.status_code not in _RETRYABLE_STATUS_CODES:
                    raise
                if attempt < _MAX_RETRIES - 1:
                    wait = _BACKOFF_SECONDS[attempt]
                    logger.warning(
                        "m3ter Ingest API returned %d, retrying in %ds (attempt %d/%d)",
                        e.response.status_code,
                        wait,
                        attempt + 1,
                        _MAX_RETRIES,
                    )
                    await asyncio.sleep(wait)

        raise last_exc  # type: ignore[misc]

    # ── Per-entity create methods ──────────────────────────────────────

    async def create_product(self, data: dict[str, Any]) -> dict:
        """Create a product via the Config API."""
        return await self._config_api_request(
            "POST", f"/organizations/{self.org_id}/products", data
        )

    async def create_meter(self, data: dict[str, Any]) -> dict:
        """Create a meter via the Config API."""
        return await self._config_api_request("POST", f"/organizations/{self.org_id}/meters", data)

    async def create_aggregation(self, data: dict[str, Any]) -> dict:
        """Create an aggregation via the Config API."""
        return await self._config_api_request(
            "POST", f"/organizations/{self.org_id}/aggregations", data
        )

    async def create_plan_template(self, data: dict[str, Any]) -> dict:
        """Create a plan template via the Config API."""
        return await self._config_api_request(
            "POST", f"/organizations/{self.org_id}/plantemplates", data
        )

    async def create_plan(self, data: dict[str, Any]) -> dict:
        """Create a plan via the Config API."""
        return await self._config_api_request("POST", f"/organizations/{self.org_id}/plans", data)

    async def create_pricing(self, plan_m3ter_id: str, data: dict[str, Any]) -> dict:
        """Create pricing under a plan via the Config API.

        m3ter nests Pricing under Plan, so the plan's m3ter ID is in the URL path.
        """
        return await self._config_api_request(
            "POST",
            f"/organizations/{self.org_id}/plans/{plan_m3ter_id}/pricing",
            data,
        )

    async def create_account(self, data: dict[str, Any]) -> dict:
        """Create an account via the Config API."""
        return await self._config_api_request(
            "POST", f"/organizations/{self.org_id}/accounts", data
        )

    async def create_account_plan(self, data: dict[str, Any]) -> dict:
        """Create an account plan via the Config API."""
        return await self._config_api_request(
            "POST", f"/organizations/{self.org_id}/accountplans", data
        )

    async def submit_measurements(self, data_list: list[dict[str, Any]]) -> dict:
        """Submit measurements via the Ingest API."""
        return await self._ingest_api_post(data_list)
