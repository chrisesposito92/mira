"""Minimal m3ter API client for connection testing."""

from datetime import UTC, datetime

import httpx


class M3terClient:
    """OAuth2 client-credentials client for the m3ter Config API."""

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
        self._token: str | None = None

    async def authenticate(self) -> str:
        """Obtain an OAuth2 access token via client credentials grant."""
        auth_url = f"{self.api_url}/oauth/token"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                auth_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            self._token = resp.json()["access_token"]
            return self._token

    async def test_connection(self) -> dict:
        """Authenticate and hit a lightweight endpoint to verify credentials."""
        tested_at = datetime.now(UTC)
        try:
            token = await self.authenticate()
            async with httpx.AsyncClient() as client:
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
