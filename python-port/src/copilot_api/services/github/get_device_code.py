"""GitHub device code flow implementation."""

import httpx
from typing import Dict, Any

from ...lib.api_config import GITHUB_BASE_URL, GITHUB_CLIENT_ID, GITHUB_APP_SCOPES
from ...lib.error import HTTPError


async def get_device_code() -> Dict[str, Any]:
    """Get device code for GitHub OAuth flow."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GITHUB_BASE_URL}/login/device/code",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "scope": GITHUB_APP_SCOPES,
            },
            headers={"Accept": "application/json"},
        )
        
        if not response.is_success:
            raise HTTPError("Failed to get device code", response)
        
        return response.json()